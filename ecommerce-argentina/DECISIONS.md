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
