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
