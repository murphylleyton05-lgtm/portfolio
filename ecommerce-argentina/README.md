# Pampa Store — ecommerce listo para vender en Argentina

Tienda online con **Next.js 16 (App Router) + TypeScript + Tailwind**, **Supabase**
(Postgres, Auth y Storage), **Mercado Pago Checkout Pro** en pesos y emails con
**Resend**. Pensada para deployar en **Vercel**.

> Toda la identidad (nombre, colores, logo, contacto, redes, envíos) se cambia
> en un solo archivo: [`site.config.ts`](./site.config.ts).

## Correrlo en local (2 minutos, sin cuentas)

Requisitos: Node.js 20.9 o superior.

```bash
cd ecommerce-argentina
npm install
cp .env.example .env.local   # podés dejarlo vacío para el modo demo
npm run dev
```

Abrí <http://localhost:3000>. Sin variables de entorno la tienda arranca en
**modo demo**: muestra los 12 productos de ejemplo, pero no crea pedidos ni deja
entrar al admin hasta que configures Supabase.

## Scripts

| Comando             | Qué hace                                              |
| ------------------- | ----------------------------------------------------- |
| `npm run dev`       | Servidor de desarrollo                                |
| `npm run build`     | Build de producción                                   |
| `npm run lint`      | ESLint                                                |
| `npm run typecheck` | Genera tipos de rutas y corre TypeScript              |
| `npm run test`      | Tests unitarios (Vitest)                              |
| `npm run check`     | Todo lo anterior junto (lo mismo que corre el CI)     |
| `npm run admin:create -- email "clave"` | Crea un usuario admin del panel |
| `npm run db:test`   | Tests SQL (migraciones, pagos, stock, RLS)            |
| `npm run demo:generate` | Regenera `seed.sql` e imágenes demo               |

## Estructura

```
site.config.ts        ← marca, colores, contacto, envíos, retiro (editar acá)
.env.example          ← variables secretas (copiar a .env.local)
src/
  app/                ← rutas (App Router)
  components/         ← UI
  lib/                ← lógica: env, supabase, catálogo, carrito, envíos, pagos, emails
  data/               ← catálogo demo (fuente del seed)
DECISIONS.md          ← decisiones tomadas y cómo cambiarlas
```

## Base de datos (Supabase)

Las migraciones están en [`supabase/migrations`](./supabase/migrations) y los
datos de ejemplo en [`supabase/seed.sql`](./supabase/seed.sql):

| Tabla              | Para qué                                                     |
| ------------------ | ------------------------------------------------------------ |
| `categories`       | Categorías del catálogo                                      |
| `products`         | Productos (precio base, precio tachado, imágenes, activo)    |
| `product_variants` | Variantes (talle/color) con **stock** y precio opcional      |
| `customers`        | Clientes (compra como invitado, se identifican por email)    |
| `orders`           | Pedidos: estado, entrega, totales y datos de Mercado Pago     |
| `order_items`      | Items del pedido (copia de nombre y precio al comprar)       |
| `admin_users`      | Usuarios de Supabase Auth con acceso al panel                |

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

- **Pedidos**: listado con filtros por estado y búsqueda, detalle con datos del
  cliente, entrega y pago, y cambio de estado (repone/descuenta stock solo).
- **Productos**: alta, edición y borrado; imágenes (subida a Supabase Storage),
  variantes con stock, precio tachado, destacado y pausar.
- **Stock**: todas las variantes con edición rápida y filtro de stock bajo.
- **Categorías**: alta, edición, orden y borrado.

Para crear tu usuario admin (con `.env.local` completo):

```bash
npm run admin:create -- vos@tumail.com "una-clave-segura"
```

O desde el SQL Editor de Supabase, después de crear el usuario en
*Authentication → Users → Add user*:

```sql
insert into public.admin_users (user_id)
select id from auth.users where email = 'vos@tumail.com';
```

## Emails

Con `RESEND_API_KEY` y `EMAIL_FROM` configurados se envían:

| Cuándo                                     | A quién              |
| ------------------------------------------ | -------------------- |
| Se aprueba el pago (o lo marcás pagado)    | Cliente + la tienda  |
| Marcás el pedido como "Enviado"            | Cliente              |
| Marcás el pedido como "Listo para retirar" | Cliente              |

Sin la clave, los emails se imprimen en la consola del servidor.

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
