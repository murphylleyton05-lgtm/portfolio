# Decisiones

Registro de decisiones tomadas sin consultar, eligiendo siempre la opción más
simple que resuelve el problema. Si alguna no te sirve, cada punto dice dónde
cambiarla.

## Proyecto

- **Carpeta propia dentro del monorepo `portfolio`** (`ecommerce-argentina/`). En
  Vercel hay que poner *Root Directory = `ecommerce-argentina`*.
- **Next.js 16.4 con Cache Components** (lo que trae `create-next-app` por
  defecto). El catálogo se cachea con `"use cache"` + `cacheTag("catalog")` y se
  invalida cuando el admin guarda cambios o entra un pago. Lo que depende del
  request (carrito, pedido, admin) va dentro de `<Suspense>`.
- **`site.config.ts` en la raíz** con alias `@site-config`. Ahí está todo lo
  que no es secreto: marca, colores, contacto, redes, envíos, retiro y cuotas.
  Los secretos van en `.env.local`.
- **Colores por variables CSS**: el layout raíz inyecta `--brand-*` desde
  `site.config.ts` y Tailwind los usa como `bg-primary`, `text-accent`, etc.
  No hay modo oscuro (la marca define su paleta).
- **Favicon y apple-icon generados** con la inicial de `shortName` y el color
  primario, así cambian solos al cambiar la config. El logo del header es
  `public/logo.svg` (reemplazalo o poné `logo: null`).
- **Modo demo**: si faltan las variables de Supabase, la tienda muestra el
  catálogo de ejemplo desde `src/data/demo-catalog.ts` (los mismos 12 productos
  del seed). El checkout y el admin muestran un aviso pidiendo configurar
  Supabase. Así `npm run dev` funciona desde el minuto uno.
- **`NEXT_PUBLIC_SITE_URL` opcional en Vercel**: si no está, se usa
  `VERCEL_PROJECT_PRODUCTION_URL`.
- **Headers de seguridad básicos** en `next.config.ts` (nosniff, referrer,
  frame-options, permissions-policy). No se agregó CSP estricta para no romper
  el checkout de Mercado Pago ni scripts de terceros que quieras sumar.
- **`npm audit`** reporta 5 vulnerabilidades *high* en `braces`/`micromatch`,
  dependencias de desarrollo de `eslint-config-next`. No llegan al bundle de
  producción y la única "solución" automática es bajar a Next 14, así que se
  dejaron.

## Base de datos

- **Variantes "planas"**: cada variante tiene un nombre libre ("M", "Negro / L",
  "Único") en vez de un sistema de opciones × valores. Todo producto tiene al
  menos una variante; el stock vive en la variante.
- **Precios en `numeric(12,2)` en pesos**. La variante puede pisar el precio del
  producto (`price` null = usa el del producto).
- **Imágenes como `text[]` en `products`** (la primera es la portada), sin tabla
  aparte. Guardan URLs públicas de Supabase Storage o rutas de `/public`.
- **Compra como invitado**: no hay cuentas de cliente. `customers` se hace
  *upsert* por email y cada pedido guarda una copia de los datos del cliente.
- **El cliente ve su pedido con un token secreto** (`/pedido/<id>?token=<uuid>`)
  que va en el link de vuelta de Mercado Pago y en el email.
- **Stock**: se valida al crear el pedido y se descuenta recién cuando el pago
  se aprueba (no se reserva). Puede haber sobreventa si dos personas pagan la
  última unidad al mismo tiempo: el stock queda en 0 (nunca negativo) y el
  admin lo ve. Para una tienda chica es preferible a reservar stock de carritos
  abandonados.
- **Estados del pedido**: `pending_payment → paid → preparing → shipped /
  ready_for_pickup → delivered`, o `cancelled`. Cambiar a cancelado (o volver a
  pendiente) repone stock; pasar a cualquier estado "pagado" lo descuenta si no
  estaba descontado (sirve para cobros por transferencia).
- **Un pago aprobado sobre un pedido cancelado no lo reactiva**: queda
  registrado el pago para que el admin decida.
- **Admins en tabla `admin_users`** + función `is_admin()` usada en las políticas
  RLS y en Storage. Defensa en profundidad: aunque el código del panel tuviera
  un error, la base no deja escribir a quien no es admin.
- **Funciones internas en el esquema `private`** (no expuesto por la API).
- **Tests SQL con un "shim" de Supabase** (`supabase/tests/00_supabase_shim.sql`)
  para poder correr migraciones y pruebas en cualquier Postgres 15+.

## Tienda pública

- **Filtros y búsqueda en memoria** sobre el catálogo cacheado (sin acentos,
  por nombre, descripción, categoría y SKU). Es más simple y rápido que una
  consulta por combinación de filtros para tiendas de hasta ~2000 productos.
  Si crecés más, mover `queryCatalog` a SQL (full text search).
- **Los filtros son formularios GET** (`next/form`): funcionan sin JavaScript y
  las URLs se pueden compartir. Las búsquedas y rangos de precio llevan
  `noindex`; las categorías sí se indexan.
- **Categorías como filtro** (`/productos?categoria=remeras`) en vez de rutas
  propias, para no duplicar páginas.
- **Orden por defecto**: con stock primero, después destacados, después nuevos.
- **Carrito en `localStorage`** (Zustand con `persist`), sincronizado entre
  pestañas. Al abrir carrito o checkout se refrescan precio y stock con el
  servidor y se avisa qué cambió. El servidor nunca confía en precios del
  navegador: recalcula todo al crear el pedido.
- **Sin cuentas de cliente ni favoritos** (fuera del MVP).
- **Placeholders SVG** livianos generados por script (no dependen de servicios
  externos). Las fotos reales que subas desde el admin se optimizan con
  `next/image`.
- **404 "suave" para humanos**: con streaming, un producto inexistente responde
  200 con `noindex` y la página de "no encontrado"; los bots reciben 404 real.

## Pagos (Mercado Pago Checkout Pro)

- **Flujo**: el checkout crea el pedido (`pending_payment`), crea la preferencia
  y redirige a Mercado Pago. Las `back_urls` vuelven a `/pedido/<id>?token=…`.
- **El estado del pago nunca se toma de la URL ni del cuerpo del webhook**: se
  consulta siempre `GET /v1/payments/:id` con el access token. Además se exige
  que el monto pagado cubra el total y que la moneda sea ARS.
- **Doble confirmación**: el webhook (`/api/webhooks/mercadopago`) y la página
  de vuelta sincronizan el pago. Ambos llaman a `confirm_order_payment`, que es
  idempotente. Así funciona aunque el webhook se demore (o en local, donde MP no
  puede llegar).
- **Firma del webhook** (`x-signature`) validada con el validador oficial del
  SDK cuando está `MERCADOPAGO_WEBHOOK_SECRET`. Sin ventana de tiempo: un
  reenvío es inofensivo porque el pago se vuelve a consultar.
- **`notification_url` y `auto_return` solo con sitio https** (Mercado Pago los
  rechaza con `http://localhost`). En local el pago se confirma al volver.
- **Envío como un ítem más** de la preferencia ("Envío"), no con `shipments`.
- **Sin `binary_mode`**: se aceptan pagos en efectivo (Rapipago/Pago Fácil) que
  quedan pendientes hasta acreditarse.
- **Si Mercado Pago falla al crear la preferencia**, el pedido queda creado y el
  cliente va a su página, donde tiene un botón para reintentar el pago.
- **Sin Mercado Pago configurado** (pero con Supabase), los pedidos se crean
  igual como "pendiente de pago" para cobrar por otro medio (transferencia).
- **Credenciales `TEST-…`** usan `sandbox_init_point`; las de producción (o de
  usuarios de prueba `APP_USR-…`) usan `init_point`.

## Panel admin

- **Login con Supabase Auth (email + contraseña)**. No hay registro público: los
  admins se crean con `npm run admin:create -- email "contraseña"` (o con el SQL
  del README). Quien inicia sesión sin estar en `admin_users` es rechazado.
- **Tres capas de protección**: `src/proxy.ts` manda al login a quien no tiene
  sesión (chequeo optimista), cada página y server action vuelve a verificar
  `is_admin()` (`requireAdmin`), y RLS en la base solo deja escribir a admins.
- **Las imágenes se suben directo del navegador a Supabase Storage** (bucket
  `product-images`, máx. 5 MB, JPG/PNG/WebP/AVIF/GIF) con la sesión del admin.
  Así no pasan por las funciones de Vercel (límite de 4,5 MB). Al quitar una
  imagen y guardar, se borra del bucket.
- **Guardar producto no es transaccional** (producto + variantes son varias
  llamadas). Si falla a mitad, se muestra el error y se puede volver a guardar.
- **Borrar producto es definitivo**; para ocultarlo está "Pausar". Los pedidos
  viejos conservan nombre y precio (copia en `order_items`).
- **El stock se edita** en el producto o en la pantalla "Stock" (con filtro de
  stock bajo). Cambiar el estado de un pedido repone o descuenta stock solo.
- **Pedidos sin borrar**: solo se cambian de estado (historial completo).
- **Miniaturas del admin sin optimizar** (`unoptimized`) para no gastar cuota
  de optimización de imágenes de Vercel en pantallas internas.

## Emails (Resend)

- **Qué se manda**: confirmación al cliente cuando el pago se aprueba (o cuando
  el admin marca el pedido como pagado a mano), aviso de "nueva venta" al email
  de `site.config.ts → contact.email`, y aviso al cliente cuando el pedido pasa
  a "Enviado" o "Listo para retirar".
- **Una sola confirmación por pedido**: se reserva con
  `orders.confirmation_email_sent_at` antes de enviar (si el envío falla se
  libera para reintentar) y además se usa la `Idempotency-Key` de Resend. El
  webhook y la página de vuelta pueden llegar juntos sin duplicar emails.
- **Se envían después de responder** (`after()`), así el webhook contesta
  rápido a Mercado Pago aunque Resend demore.
- **HTML hecho a mano con estilos inline** (sin React Email) para no sumar
  dependencias; todo dato del cliente se escapa. Incluye versión texto plano.
- **Sin `RESEND_API_KEY` los emails se imprimen en la consola** del servidor.
- **Remitente en `EMAIL_FROM`** (tiene que ser de un dominio verificado en
  Resend). Las respuestas van a `contact.email` (`replyTo`).
- **No se mandan emails al crear el pedido** (antes de pagar): la página del
  pedido ya muestra todo y evita spam por carritos abandonados.
