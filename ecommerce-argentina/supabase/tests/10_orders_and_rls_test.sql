-- ════════════════════════════════════════════════════════════════════════════
-- Tests de pedidos, stock y permisos. Corre dentro de una transacción que se
-- descarta al final (no deja datos). Falla con excepción si algo no da.
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- Helpers para simular el usuario de la API.
create function pg_temp.as_role(p_role text, p_user uuid default null) returns void
language plpgsql as $$
begin
  perform set_config('request.jwt.claim.sub', coalesce(p_user::text, ''), true);
  execute format('set local role %I', p_role);
end;
$$;

create function pg_temp.assert(condition boolean, message text) returns void
language plpgsql as $$
begin
  if not coalesce(condition, false) then
    raise exception 'FALLÓ: %', message;
  end if;
end;
$$;

-- Datos: un admin, un usuario común y un pedido de 2 remeras M + 1 gorra.
insert into auth.users (id, email) values
  ('aaaaaaaa-0000-4000-8000-000000000001', 'admin@test.com'),
  ('bbbbbbbb-0000-4000-8000-000000000001', 'cliente@test.com');
insert into public.admin_users (user_id) values ('aaaaaaaa-0000-4000-8000-000000000001');

insert into public.orders (id, customer_name, customer_email, customer_phone, delivery_method, subtotal, shipping_cost, total)
values ('cccccccc-0000-4000-8000-000000000001', 'Ana', 'ana@test.com', '1122334455', 'pickup', 68970, 0, 68970);

insert into public.order_items (order_id, product_id, variant_id, product_name, variant_name, unit_price, quantity) values
  ('cccccccc-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000102', 'Remera Básica Algodón', 'M', 24990, 2),
  ('cccccccc-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000009', '30000000-0000-4000-8000-000000000901', 'Gorra Trucker', 'Único', 18990, 1);

-- El número de pedido arranca en 1001.
select pg_temp.assert(
  (select number from public.orders where id = 'cccccccc-0000-4000-8000-000000000001') = 1001,
  'el primer pedido debería ser el #1001'
);

-- ── Seed ────────────────────────────────────────────────────────────────────
select pg_temp.assert((select count(*) from public.products) = 12, 'seed: 12 productos');
select pg_temp.assert((select count(*) from public.categories) = 4, 'seed: 4 categorías');
select pg_temp.assert(
  not exists (select 1 from public.products p where not exists (select 1 from public.product_variants v where v.product_id = p.id)),
  'seed: todo producto tiene al menos una variante'
);

-- ── Pago aprobado: descuenta stock una sola vez ────────────────────────────
select pg_temp.as_role('service_role');

select pg_temp.assert(
  public.confirm_order_payment('cccccccc-0000-4000-8000-000000000001', 'pay-1', 'approved', 'accredited'),
  'el primer pago aprobado devuelve true'
);
select pg_temp.assert(
  not public.confirm_order_payment('cccccccc-0000-4000-8000-000000000001', 'pay-1', 'approved', 'accredited'),
  'el mismo pago repetido devuelve false (idempotente)'
);

reset role;
select pg_temp.assert((select stock from public.product_variants where id = '30000000-0000-4000-8000-000000000102') = 13, 'remera M: 15 - 2 = 13');
select pg_temp.assert((select stock from public.product_variants where id = '30000000-0000-4000-8000-000000000901') = 19, 'gorra: 20 - 1 = 19');
select pg_temp.assert(
  (select status = 'paid' and stock_applied and paid_at is not null from public.orders where id = 'cccccccc-0000-4000-8000-000000000001'),
  'pedido pagado con stock aplicado'
);

-- Un intento rechazado que llega tarde no pisa el pago aprobado.
select pg_temp.as_role('service_role');
select pg_temp.assert(
  not public.confirm_order_payment('cccccccc-0000-4000-8000-000000000001', 'pay-0', 'rejected', 'cc_rejected_other_reason'),
  'pago rechazado devuelve false'
);
reset role;
select pg_temp.assert(
  (select mp_payment_id = 'pay-1' and mp_payment_status = 'approved' from public.orders where id = 'cccccccc-0000-4000-8000-000000000001'),
  'el rechazo tardío no pisa el pago aprobado'
);

-- ── Permisos de funciones ───────────────────────────────────────────────────
select pg_temp.as_role('anon');
do $$
begin
  perform public.confirm_order_payment('cccccccc-0000-4000-8000-000000000001', 'x', 'approved');
  raise exception 'FALLÓ: anon no debería poder confirmar pagos';
exception when insufficient_privilege then null;
end
$$;
reset role;

select pg_temp.as_role('authenticated', 'bbbbbbbb-0000-4000-8000-000000000001');
do $$
begin
  perform public.set_order_status('cccccccc-0000-4000-8000-000000000001', 'cancelled');
  raise exception 'FALLÓ: un usuario no admin no debería cambiar estados';
exception when insufficient_privilege then null;
end
$$;
reset role;

-- ── Admin cancela: se repone el stock ──────────────────────────────────────
select pg_temp.as_role('authenticated', 'aaaaaaaa-0000-4000-8000-000000000001');
select public.set_order_status('cccccccc-0000-4000-8000-000000000001', 'cancelled');
reset role;
select pg_temp.assert((select stock from public.product_variants where id = '30000000-0000-4000-8000-000000000102') = 15, 'cancelar repone remera M a 15');
select pg_temp.assert(
  (select not stock_applied from public.orders where id = 'cccccccc-0000-4000-8000-000000000001'),
  'pedido cancelado sin stock aplicado'
);

-- Un pago aprobado sobre un pedido cancelado no lo reactiva solo.
select pg_temp.as_role('service_role');
select pg_temp.assert(
  not public.confirm_order_payment('cccccccc-0000-4000-8000-000000000001', 'pay-1', 'approved', 'accredited'),
  'pago sobre pedido cancelado devuelve false'
);
reset role;
select pg_temp.assert((select stock from public.product_variants where id = '30000000-0000-4000-8000-000000000102') = 15, 'no se descuenta stock de un cancelado');

-- Admin lo marca "preparando" (ej. cobró por transferencia): vuelve a descontar.
select pg_temp.as_role('authenticated', 'aaaaaaaa-0000-4000-8000-000000000001');
select public.set_order_status('cccccccc-0000-4000-8000-000000000001', 'preparing');
reset role;
select pg_temp.assert((select stock from public.product_variants where id = '30000000-0000-4000-8000-000000000102') = 13, 'preparar descuenta de nuevo (13)');

-- El stock nunca queda negativo aunque se venda de más.
update public.product_variants set stock = 1 where id = '30000000-0000-4000-8000-000000000102';
insert into public.orders (id, customer_name, customer_email, customer_phone, delivery_method, subtotal, shipping_cost, total)
values ('cccccccc-0000-4000-8000-000000000002', 'Beto', 'beto@test.com', '1122334455', 'pickup', 49980, 0, 49980);
insert into public.order_items (order_id, variant_id, product_name, variant_name, unit_price, quantity) values
  ('cccccccc-0000-4000-8000-000000000002', '30000000-0000-4000-8000-000000000102', 'Remera Básica Algodón', 'M', 24990, 2);
select pg_temp.as_role('service_role');
select public.confirm_order_payment('cccccccc-0000-4000-8000-000000000002', 'pay-2', 'approved');
reset role;
select pg_temp.assert((select stock from public.product_variants where id = '30000000-0000-4000-8000-000000000102') = 0, 'stock se clampa en 0');

-- ── RLS ─────────────────────────────────────────────────────────────────────
update public.products set active = false where slug = 'gorra-trucker';

select pg_temp.as_role('anon');
select pg_temp.assert((select count(*) from public.products) = 11, 'anon no ve productos inactivos');
select pg_temp.assert(
  (select count(*) from public.product_variants where product_id = '20000000-0000-4000-8000-000000000009') = 0,
  'anon no ve variantes de productos inactivos'
);
do $$
begin
  perform 1 from public.orders;
  raise exception 'FALLÓ: anon no debería leer pedidos';
exception when insufficient_privilege then null;
end
$$;
do $$
begin
  insert into public.products (name, slug, price) values ('Hack', 'hack', 1);
  raise exception 'FALLÓ: anon no debería crear productos';
exception when insufficient_privilege then null;
end
$$;
reset role;

select pg_temp.as_role('authenticated', 'bbbbbbbb-0000-4000-8000-000000000001');
select pg_temp.assert((select count(*) from public.orders) = 0, 'usuario común no ve pedidos');
select pg_temp.assert((select count(*) from public.products) = 11, 'usuario común no ve inactivos');
do $$
begin
  update public.products set price = 1 where slug = 'jogger-frisa';
  if found then raise exception 'FALLÓ: usuario común no debería editar productos'; end if;
end
$$;
reset role;

select pg_temp.as_role('authenticated', 'aaaaaaaa-0000-4000-8000-000000000001');
select pg_temp.assert((select count(*) from public.orders) = 2, 'admin ve todos los pedidos');
select pg_temp.assert((select count(*) from public.products) = 12, 'admin ve inactivos');
update public.products set price = 45990 where slug = 'jogger-frisa';
select pg_temp.assert(public.is_admin(), 'is_admin() true para admin');
reset role;
select pg_temp.assert((select price from public.products where slug = 'jogger-frisa') = 45990, 'admin puede editar productos');
select pg_temp.assert(
  (select updated_at = now() from public.products where slug = 'jogger-frisa'),
  'el trigger actualiza updated_at'
);

rollback;

\echo '✓ Tests de pedidos, stock y RLS OK'
