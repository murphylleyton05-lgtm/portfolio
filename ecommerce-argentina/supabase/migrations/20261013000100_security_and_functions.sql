-- ════════════════════════════════════════════════════════════════════════════
-- Seguridad (RLS + permisos), funciones de pedidos/stock y bucket de imágenes.
--
-- Modelo:
--   · Público (anon): lee categorías, productos activos y sus variantes.
--   · Admin (usuario en admin_users): lee y escribe todo desde el panel.
--   · Servidor (secret key / service_role): crea pedidos y confirma pagos.
--     Bypassea RLS, por eso esa clave nunca sale del servidor.
-- ════════════════════════════════════════════════════════════════════════════

-- ── ¿El usuario actual es admin? ────────────────────────────────────────────

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.admin_users where user_id = (select auth.uid())
  );
$$;

revoke all on function public.is_admin() from public;
grant execute on function public.is_admin() to anon, authenticated, service_role;

-- ── Row Level Security ──────────────────────────────────────────────────────

alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.product_variants enable row level security;
alter table public.customers enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.admin_users enable row level security;

-- Catálogo
create policy "categories_select_all" on public.categories
  for select to anon, authenticated using (true);
create policy "categories_admin_write" on public.categories
  for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "products_select_active" on public.products
  for select to anon, authenticated using (active or public.is_admin());
create policy "products_admin_write" on public.products
  for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "variants_select_active_product" on public.product_variants
  for select to anon, authenticated using (
    exists (
      select 1 from public.products p
      where p.id = product_id and (p.active or public.is_admin())
    )
  );
create policy "variants_admin_write" on public.product_variants
  for all to authenticated using (public.is_admin()) with check (public.is_admin());

-- Clientes y pedidos: solo admins (el checkout escribe con la secret key).
create policy "customers_admin_all" on public.customers
  for all to authenticated using (public.is_admin()) with check (public.is_admin());
create policy "orders_admin_all" on public.orders
  for all to authenticated using (public.is_admin()) with check (public.is_admin());
create policy "order_items_admin_all" on public.order_items
  for all to authenticated using (public.is_admin()) with check (public.is_admin());

-- Cada usuario puede ver si él mismo es admin.
create policy "admin_users_select_self" on public.admin_users
  for select to authenticated using (user_id = (select auth.uid()));

-- ── Permisos explícitos (RLS filtra filas; esto limita operaciones) ─────────

revoke all on public.categories, public.products, public.product_variants,
  public.customers, public.orders, public.order_items, public.admin_users
  from anon, authenticated;

grant select on public.categories, public.products, public.product_variants to anon;
grant select, insert, update, delete on public.categories, public.products,
  public.product_variants to authenticated;
grant select, update on public.customers, public.orders, public.order_items to authenticated;
grant select on public.admin_users to authenticated;

grant all on public.categories, public.products, public.product_variants,
  public.customers, public.orders, public.order_items, public.admin_users to service_role;
grant usage, select on all sequences in schema public to service_role;

-- ── Stock (funciones internas, no expuestas por la API) ─────────────────────

create or replace function private.apply_order_stock(p_order_id uuid)
returns void
language plpgsql
set search_path = ''
as $$
begin
  update public.product_variants v
     set stock = greatest(v.stock - i.qty, 0)
    from (
      select variant_id, sum(quantity)::integer as qty
        from public.order_items
       where order_id = p_order_id and variant_id is not null
       group by variant_id
    ) i
   where v.id = i.variant_id;

  update public.orders set stock_applied = true where id = p_order_id;
end;
$$;

create or replace function private.restore_order_stock(p_order_id uuid)
returns void
language plpgsql
set search_path = ''
as $$
begin
  update public.product_variants v
     set stock = v.stock + i.qty
    from (
      select variant_id, sum(quantity)::integer as qty
        from public.order_items
       where order_id = p_order_id and variant_id is not null
       group by variant_id
    ) i
   where v.id = i.variant_id;

  update public.orders set stock_applied = false where id = p_order_id;
end;
$$;

revoke all on all functions in schema private from public, anon, authenticated;

-- ── Confirmar pago (lo llama el webhook de Mercado Pago con la secret key) ──
-- Idempotente: si llega dos veces el mismo pago, el stock se descuenta una sola
-- vez. Devuelve true solo en la llamada que pasa el pedido a "paid" (para mandar
-- el email de confirmación una única vez).

create or replace function public.confirm_order_payment(
  p_order_id uuid,
  p_payment_id text,
  p_payment_status text,
  p_payment_status_detail text default null
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_status public.order_status;
  v_stock_applied boolean;
  v_current_payment_id text;
begin
  select status, stock_applied, mp_payment_id
    into v_status, v_stock_applied, v_current_payment_id
    from public.orders
   where id = p_order_id
     for update;

  if not found then
    raise exception 'Pedido % inexistente', p_order_id using errcode = 'P0002';
  end if;

  -- Guardamos el estado del pago mientras el pedido espera pago, o si es una
  -- actualización del mismo pago (ej. un reintegro). Un intento rechazado que
  -- llega tarde no pisa los datos de un pago ya aprobado.
  if v_status = 'pending_payment' or v_current_payment_id is null or v_current_payment_id = p_payment_id then
    update public.orders
       set mp_payment_id = p_payment_id,
           mp_payment_status = p_payment_status,
           mp_payment_status_detail = p_payment_status_detail
     where id = p_order_id;
  end if;

  if p_payment_status <> 'approved' or v_status <> 'pending_payment' then
    return false;
  end if;

  if not v_stock_applied then
    perform private.apply_order_stock(p_order_id);
  end if;

  update public.orders
     set status = 'paid',
         paid_at = coalesce(paid_at, now())
   where id = p_order_id;

  return true;
end;
$$;

revoke all on function public.confirm_order_payment(uuid, text, text, text) from public, anon, authenticated;
grant execute on function public.confirm_order_payment(uuid, text, text, text) to service_role;

-- ── Cambiar estado desde el admin ───────────────────────────────────────────
-- Mantiene el stock consistente:
--   · pending_payment / cancelled → si el stock estaba descontado, se repone.
--   · cualquier otro estado       → si no estaba descontado, se descuenta
--     (sirve para marcar como pagado un pedido cobrado por transferencia).

create or replace function public.set_order_status(
  p_order_id uuid,
  p_status public.order_status
)
returns public.order_status
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_stock_applied boolean;
begin
  if not public.is_admin() then
    raise exception 'No autorizado' using errcode = '42501';
  end if;

  select stock_applied into v_stock_applied
    from public.orders
   where id = p_order_id
     for update;

  if not found then
    raise exception 'Pedido % inexistente', p_order_id using errcode = 'P0002';
  end if;

  if p_status in ('pending_payment', 'cancelled') then
    if v_stock_applied then
      perform private.restore_order_stock(p_order_id);
    end if;
  elsif not v_stock_applied then
    perform private.apply_order_stock(p_order_id);
  end if;

  update public.orders
     set status = p_status,
         paid_at = case
           when p_status in ('pending_payment', 'cancelled') then paid_at
           else coalesce(paid_at, now())
         end
   where id = p_order_id;

  return p_status;
end;
$$;

revoke all on function public.set_order_status(uuid, public.order_status) from public, anon;
grant execute on function public.set_order_status(uuid, public.order_status) to authenticated, service_role;

-- ── Storage: imágenes de productos ──────────────────────────────────────────
-- Bucket público (las imágenes se ven sin login); solo admins suben/borran.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'product-images',
  'product-images',
  true,
  5242880, -- 5 MB
  array['image/jpeg', 'image/png', 'image/webp', 'image/avif', 'image/gif']
)
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

create policy "product_images_admin_select" on storage.objects
  for select to authenticated
  using (bucket_id = 'product-images' and public.is_admin());

create policy "product_images_admin_insert" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'product-images' and public.is_admin());

create policy "product_images_admin_update" on storage.objects
  for update to authenticated
  using (bucket_id = 'product-images' and public.is_admin())
  with check (bucket_id = 'product-images' and public.is_admin());

create policy "product_images_admin_delete" on storage.objects
  for delete to authenticated
  using (bucket_id = 'product-images' and public.is_admin());
