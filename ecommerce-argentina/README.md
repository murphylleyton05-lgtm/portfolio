# Pampa Store — ecommerce listo para vender en Argentina

Tienda online con **Next.js 16 (App Router) + TypeScript + Tailwind**, **Supabase**
(Postgres, Auth y Storage), **Mercado Pago Checkout Pro** en pesos y emails con
**Resend**. Pensada para deployar en **Vercel**.

> Toda la identidad (nombre, colores, logo, contacto, redes, envíos, datos
> fiscales) se cambia en un solo archivo: [`site.config.ts`](./site.config.ts).
> Los secretos van en `.env.local` (ver [`.env.example`](./.env.example)).
> Cada decisión tomada está explicada en [`DECISIONS.md`](./DECISIONS.md).

## Qué incluye

- **Tienda**: home, listado con búsqueda (sin acentos), filtros por categoría,
  precio y stock, orden y paginación; página de producto con galería,
  variantes (talle/color), stock y cotizador de envío; carrito persistente.
- **Checkout**: datos del cliente, envío a domicilio (costo por zona de CP,
  envío gratis desde un mínimo) o retiro en el local; validación con Zod.
- **Pagos**: Mercado Pago Checkout Pro (tarjetas, cuotas, efectivo), webhook
  con firma verificada que confirma el pago y descuenta stock una sola vez.
- **Panel admin** (`/admin`): pedidos y cambio de estado, productos con subida
  de imágenes, variantes y stock, control de stock y categorías.
- **Emails** (Resend): confirmación de compra, aviso de venta a la tienda,
  "enviado" y "listo para retirar".
- **Argentina**: CP/CPA, provincias, WhatsApp (flotante, por producto y por
  pedido), **Botón de arrepentimiento**, link a Defensa del Consumidor y Data
  Fiscal.
- **Calidad**: SEO (metadata, sitemap, robots, Open Graph dinámico, JSON-LD de
  producto), imágenes optimizadas, estados de carga y errores, RLS en la base,
  tests (Vitest + SQL) y CI en GitHub Actions.

## Correrlo en local (2 minutos, sin cuentas)

Requisitos: Node.js 20.9 o superior.

```bash
cd ecommerce-argentina
npm install
npm run dev
```

Abrí <http://localhost:3000>. Sin variables de entorno la tienda arranca en
**modo demo**: muestra los 12 productos de ejemplo y podés usar el carrito,
pero no crea pedidos ni deja entrar al admin hasta que configures Supabase.

## Ponerla en producción

### 1. Supabase (base de datos, login del admin e imágenes)

1. Creá un proyecto en <https://supabase.com/dashboard> (región São Paulo).
2. Abrí **SQL Editor → New query** y ejecutá, en este orden, el contenido de:
   1. [`supabase/migrations/20261013000000_schema.sql`](./supabase/migrations/20261013000000_schema.sql)
   2. [`supabase/migrations/20261013000100_security_and_functions.sql`](./supabase/migrations/20261013000100_security_and_functions.sql)
   3. [`supabase/seed.sql`](./supabase/seed.sql) (opcional: los 12 productos de ejemplo)
3. En **Project Settings → API Keys** copiá la URL del proyecto, la
   _Publishable key_ y la _Secret key_ a `.env.local`
   (`cp .env.example .env.local`).
4. Recomendado: en **Authentication → Sign In / Providers** desactivá
   _Allow new users to sign up_ (los admins se crean a mano).
5. Creá tu usuario del panel:
   ```bash
   npm run admin:create -- vos@tumail.com "una-clave-segura"
   ```

### 2. Mercado Pago

1. En <https://www.mercadopago.com.ar/developers/panel/app> creá una
   aplicación (producto **Checkout Pro**).
2. Copiá el **Access Token** a `MERCADOPAGO_ACCESS_TOKEN` (primero el de
   prueba; cuando todo funcione, el de producción).
3. Una vez deployada la tienda, en la aplicación → **Webhooks** configurá la
   URL `https://TU-DOMINIO/api/webhooks/mercadopago`, marcá el evento
   **Pagos**, guardá y copiá la **clave secreta** a
   `MERCADOPAGO_WEBHOOK_SECRET`.

> Para probar usá las cuentas y tarjetas de prueba de Mercado Pago. En local
> (http://localhost) Mercado Pago no puede llamar al webhook: el pago se
> confirma igual cuando volvés a la tienda desde el checkout.

### 3. Resend (emails) — opcional pero recomendado

1. Creá una API key en <https://resend.com/api-keys> → `RESEND_API_KEY`.
2. Verificá tu dominio en Resend y poné el remitente en `EMAIL_FROM`
   (ej. `Tu Tienda <pedidos@tudominio.com.ar>`).

### 4. Vercel

1. En <https://vercel.com/new> importá este repositorio.
2. **Root Directory: `ecommerce-argentina`** (el framework Next.js se detecta solo).
3. Cargá las variables de `.env.local` en **Environment Variables**
   (`NEXT_PUBLIC_SITE_URL` = tu dominio, ej. `https://tutienda.com.ar`; si no
   la cargás se usa el dominio `.vercel.app`).
4. Deploy. Si después cambiás una variable `NEXT_PUBLIC_*`, hacé _Redeploy_.

## Personalizar

| Qué                                      | Dónde                                     |
| ---------------------------------------- | ----------------------------------------- |
| Nombre, textos, colores, contacto, redes | `site.config.ts`                          |
| Zonas y costos de envío, retiro, cuotas  | `site.config.ts` → `shipping`, `pickup`   |
| Razón social, CUIT, Data Fiscal          | `site.config.ts` → `legal`                |
| Logo                                     | `public/logo.svg` (o `logo: null`)        |
| Productos, stock, categorías, pedidos    | Panel `/admin`                            |
| Favicon / imagen para redes              | Se generan solos con el nombre y el color |

## Variables de entorno

| Variable                               | Obligatoria      | Para qué                                        |
| -------------------------------------- | ---------------- | ----------------------------------------------- |
| `NEXT_PUBLIC_SITE_URL`                 | Recomendada      | URL pública (emails, Mercado Pago, SEO)         |
| `NEXT_PUBLIC_SUPABASE_URL`             | Sí (para vender) | URL del proyecto Supabase                       |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Sí (para vender) | Clave pública (o la _anon key_ legacy)          |
| `SUPABASE_SECRET_KEY`                  | Sí (para vender) | Clave secreta del servidor (o _service_role_)   |
| `MERCADOPAGO_ACCESS_TOKEN`             | Sí (para cobrar) | Crear preferencias y consultar pagos            |
| `MERCADOPAGO_WEBHOOK_SECRET`           | Recomendada      | Verificar la firma de los webhooks              |
| `RESEND_API_KEY`                       | Recomendada      | Enviar emails (sin ella se imprimen en consola) |
| `EMAIL_FROM`                           | Con Resend       | Remitente de un dominio verificado              |

## Cómo funciona un pedido

1. El checkout valida los datos (Zod), **recalcula precios, stock y envío en el
   servidor** y crea el pedido como _Pendiente de pago_.
2. Se crea la preferencia de Mercado Pago y el cliente paga en Checkout Pro.
3. Mercado Pago avisa al webhook (y el cliente vuelve a `/pedido/<id>`). En
   ambos casos se **consulta el pago en la API de Mercado Pago** (nunca se
   confía en la URL) y, si está aprobado y el monto coincide, el pedido pasa a
   _Pagado_ y se descuenta el stock una sola vez.
4. Se envía el email de confirmación al cliente y el aviso a la tienda.
5. Desde el admin lo pasás a _En preparación → Enviado / Listo para retirar →
   Entregado_ (con aviso por email). Cancelar repone el stock.

## Scripts

| Comando                                 | Qué hace                                            |
| --------------------------------------- | --------------------------------------------------- |
| `npm run dev`                           | Servidor de desarrollo                              |
| `npm run build` / `npm start`           | Build y servidor de producción                      |
| `npm run lint`                          | ESLint                                              |
| `npm run typecheck`                     | Genera tipos de rutas y corre TypeScript            |
| `npm run test`                          | Tests unitarios (Vitest)                            |
| `npm run format`                        | Formatea con Prettier                               |
| `npm run check`                         | Formato + lint + tipos + tests + build (como el CI) |
| `npm run admin:create -- email "clave"` | Crea un usuario admin del panel                     |
| `npm run db:test`                       | Tests SQL (migraciones, pagos, stock, RLS)          |
| `npm run demo:generate`                 | Regenera `seed.sql` e imágenes demo                 |

## Estructura

```
site.config.ts        ← marca, colores, contacto, envíos, retiro, legales (editar acá)
.env.example          ← variables secretas (copiar a .env.local)
supabase/
  migrations/         ← esquema, RLS, funciones de pago/stock, bucket de imágenes
  seed.sql            ← 12 productos de ejemplo (generado)
  tests/              ← tests SQL + "shim" de Supabase para correrlos en Postgres
scripts/              ← generar seed/placeholders, crear admin
src/
  app/(store)/        ← tienda: home, productos, carrito, checkout, pedido, arrepentimiento
  app/admin/          ← panel: login, inicio, pedidos, productos, stock, categorías
  app/api/webhooks/   ← webhook de Mercado Pago
  components/         ← UI (store, admin, ui)
  lib/                ← env, supabase, catálogo, carrito, checkout, envíos, pagos, emails
  data/               ← catálogo demo (fuente del seed)
  proxy.ts            ← sesión y protección de /admin
```

## Base de datos (Supabase)

| Tabla              | Para qué                                                  |
| ------------------ | --------------------------------------------------------- |
| `categories`       | Categorías del catálogo                                   |
| `products`         | Productos (precio base, precio tachado, imágenes, activo) |
| `product_variants` | Variantes (talle/color) con **stock** y precio opcional   |
| `customers`        | Clientes (compra como invitado, se identifican por email) |
| `orders`           | Pedidos: estado, entrega, totales y datos de Mercado Pago |
| `order_items`      | Items del pedido (copia de nombre y precio al comprar)    |
| `admin_users`      | Usuarios de Supabase Auth con acceso al panel             |

Seguridad con **RLS**: el público solo lee el catálogo activo; los admins
gestionan todo; los pedidos los crea el servidor con la secret key. El stock se
descuenta una sola vez cuando se aprueba el pago (`confirm_order_payment`) y se
repone si el admin cancela el pedido (`set_order_status`).

Tests de la base (migraciones + seed + pagos/stock/RLS) contra un Postgres vacío:

```bash
DATABASE_URL=postgres://postgres@localhost:5432/postgres npm run db:test
```

Si editás `src/data/demo-catalog.ts`, regenerá seed e imágenes con
`npm run demo:generate`.

## Panel admin

Entrá a `/admin` (te pide login). Desde ahí:

- **Inicio**: pedidos para preparar, esperando pago, ventas de 30 días y stock bajo.
- **Pedidos**: filtros por estado y búsqueda, detalle con datos del cliente
  (con link a WhatsApp), entrega y pago, y cambio de estado.
- **Productos**: alta, edición y borrado; imágenes (subida a Supabase Storage),
  variantes con stock, precio tachado, destacado y pausar.
- **Stock**: todas las variantes con edición rápida y filtro de stock bajo.
- **Categorías**: alta, edición, orden y borrado.

Si preferís crear el admin sin el script: creá el usuario en _Authentication →
Users → Add user_ y ejecutá en el SQL Editor:

```sql
insert into public.admin_users (user_id)
select id from auth.users where email = 'vos@tumail.com';
```

## Emails

| Cuándo                                     | A quién             |
| ------------------------------------------ | ------------------- |
| Se aprueba el pago (o lo marcás pagado)    | Cliente + la tienda |
| Marcás el pedido como "Enviado"            | Cliente             |
| Marcás el pedido como "Listo para retirar" | Cliente             |
| Alguien usa el Botón de arrepentimiento    | Cliente + la tienda |

Sin `RESEND_API_KEY`, los emails se imprimen en la consola del servidor.

## Envíos, retiro y WhatsApp

Todo se configura en [`site.config.ts`](./site.config.ts):

```ts
shipping: {
  enabled: true,
  freeShippingThreshold: 150000, // null = sin envío gratis
  zones: [
    { id: "caba", name: "CABA", postalCodeRanges: [[1000, 1499]], cost: 4500, eta: "24 a 48 hs hábiles" },
    { id: "gba", name: "GBA", postalCodeRanges: [[1600, 1999]], cost: 6500, eta: "48 a 72 hs hábiles" },
  ],
  defaultZone: { id: "interior", name: "Resto del país", cost: 9900, eta: "3 a 7 días hábiles" },
},
pickup: { enabled: true, address: "...", hours: "..." },
contact: { whatsapp: "5491123456789", ... },
```

## Antes de vender (checklist)

- [ ] Completar `site.config.ts` (marca, contacto, WhatsApp, dirección de retiro, CUIT, Data Fiscal).
- [ ] Reemplazar `public/logo.svg` y cargar tus productos (borrar los de ejemplo).
- [ ] Pasar a las credenciales **de producción** de Mercado Pago y configurar el webhook.
- [ ] Verificar el dominio en Resend.
- [ ] Hacer una compra real de bajo monto de punta a punta.
- [ ] Sumar términos y condiciones / política de cambios (dependen de tu negocio).
