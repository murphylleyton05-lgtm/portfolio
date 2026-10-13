-- ════════════════════════════════════════════════════════════════════════════
-- Esquema de la tienda: categorías, productos, variantes, clientes, pedidos e
-- items de pedido. Los precios están en pesos (ARS) con 2 decimales.
-- ════════════════════════════════════════════════════════════════════════════

create schema if not exists private;

-- ── Tipos ───────────────────────────────────────────────────────────────────

create type public.order_status as enum (
  'pending_payment',  -- creado, esperando el pago en Mercado Pago
  'paid',             -- pago aprobado (se descontó el stock)
  'preparing',        -- en preparación
  'shipped',          -- despachado
  'ready_for_pickup', -- listo para retirar
  'delivered',        -- entregado / retirado
  'cancelled'         -- cancelado (si había descontado stock, se repone)
);

create type public.delivery_method as enum ('shipping', 'pickup');

-- ── updated_at automático ──────────────────────────────────────────────────

create or replace function private.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ── Categorías ──────────────────────────────────────────────────────────────

create table public.categories (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 80),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  description text not null default '',
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger categories_updated_at before update on public.categories
  for each row execute function private.set_updated_at();

-- ── Productos ───────────────────────────────────────────────────────────────

create table public.products (
  id uuid primary key default gen_random_uuid(),
  category_id uuid references public.categories (id) on delete set null,
  name text not null check (char_length(name) between 1 and 120),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  description text not null default '',
  -- Precio base. Una variante puede pisarlo con su propio precio.
  price numeric(12, 2) not null check (price >= 0),
  -- Precio "antes" para mostrar tachado (opcional).
  compare_at_price numeric(12, 2) check (compare_at_price is null or compare_at_price >= 0),
  -- URLs públicas (Supabase Storage o rutas de /public). La primera es la portada.
  images text[] not null default '{}',
  active boolean not null default true,
  featured boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index products_category_id_idx on public.products (category_id);
create index products_active_featured_idx on public.products (active, featured);

create trigger products_updated_at before update on public.products
  for each row execute function private.set_updated_at();

-- ── Variantes (talle, color, etc.) ─────────────────────────────────────────
-- Todo producto tiene al menos una variante; los productos sin opciones usan
-- una sola llamada "Único". El stock vive acá.

create table public.product_variants (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products (id) on delete cascade,
  name text not null default 'Único' check (char_length(name) between 1 and 80),
  sku text unique,
  price numeric(12, 2) check (price is null or price >= 0),
  stock integer not null default 0 check (stock >= 0),
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index product_variants_product_id_idx on public.product_variants (product_id);

create trigger product_variants_updated_at before update on public.product_variants
  for each row execute function private.set_updated_at();

-- ── Clientes ────────────────────────────────────────────────────────────────
-- Compra como invitado: el cliente se identifica por email (guardado en minúscula).

create table public.customers (
  id uuid primary key default gen_random_uuid(),
  email text not null unique check (email = lower(email)),
  name text not null,
  phone text,
  dni text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger customers_updated_at before update on public.customers
  for each row execute function private.set_updated_at();

-- ── Pedidos ─────────────────────────────────────────────────────────────────

create table public.orders (
  id uuid primary key default gen_random_uuid(),
  -- Número legible para el cliente (#1001, #1002...).
  number bigint generated always as identity (start with 1001) unique,
  -- Token secreto para que el cliente vea su pedido sin cuenta (/pedido/:id?token=...).
  access_token uuid not null default gen_random_uuid(),
  customer_id uuid references public.customers (id) on delete set null,
  status public.order_status not null default 'pending_payment',

  -- Copia de los datos del cliente al momento de comprar.
  customer_name text not null,
  customer_email text not null,
  customer_phone text not null,
  customer_dni text,

  delivery_method public.delivery_method not null,
  -- { street, number, apartment, city, province, postal_code } — null si es retiro.
  shipping_address jsonb,
  shipping_zone text,

  subtotal numeric(12, 2) not null check (subtotal >= 0),
  shipping_cost numeric(12, 2) not null default 0 check (shipping_cost >= 0),
  total numeric(12, 2) not null check (total >= 0),
  notes text,

  -- Mercado Pago
  mp_preference_id text,
  mp_init_point text,
  mp_payment_id text,
  mp_payment_status text,
  mp_payment_status_detail text,
  paid_at timestamptz,

  -- true cuando el stock de este pedido ya se descontó (evita descontar dos veces).
  stock_applied boolean not null default false,
  confirmation_email_sent_at timestamptz,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint orders_shipping_address_required
    check (delivery_method = 'pickup' or shipping_address is not null)
);

create index orders_status_created_at_idx on public.orders (status, created_at desc);
create index orders_created_at_idx on public.orders (created_at desc);
create index orders_customer_email_idx on public.orders (lower(customer_email));
create index orders_customer_id_idx on public.orders (customer_id);

create trigger orders_updated_at before update on public.orders
  for each row execute function private.set_updated_at();

-- ── Items de pedido ─────────────────────────────────────────────────────────
-- Guardan una copia de nombre/precio para que el pedido no cambie si después
-- se edita o borra el producto.

create table public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders (id) on delete cascade,
  product_id uuid references public.products (id) on delete set null,
  variant_id uuid references public.product_variants (id) on delete set null,
  product_name text not null,
  variant_name text not null,
  sku text,
  image text,
  unit_price numeric(12, 2) not null check (unit_price >= 0),
  quantity integer not null check (quantity > 0),
  created_at timestamptz not null default now()
);

create index order_items_order_id_idx on public.order_items (order_id);
create index order_items_variant_id_idx on public.order_items (variant_id);
create index order_items_product_id_idx on public.order_items (product_id);

-- ── Administradores ─────────────────────────────────────────────────────────
-- Usuarios de Supabase Auth con acceso al panel. Se agregan con
-- `npm run admin:create` o con el SQL del README.

create table public.admin_users (
  user_id uuid primary key references auth.users (id) on delete cascade,
  created_at timestamptz not null default now()
);
