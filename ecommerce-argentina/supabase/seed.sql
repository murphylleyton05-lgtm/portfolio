-- ════════════════════════════════════════════════════════════════════════
-- Datos de ejemplo: 4 categorías y 12 productos con variantes y stock.
-- ARCHIVO GENERADO por `npm run demo:generate` desde src/data/demo-catalog.ts
-- Se puede correr varias veces (no duplica). Borrá los productos desde el
-- admin cuando cargues los tuyos.
-- ════════════════════════════════════════════════════════════════════════

insert into public.categories (id, name, slug, description, position) values
  ('10000000-0000-4000-8000-000000000001', 'Remeras', 'remeras', 'Remeras y musculosas de algodón.', 1),
  ('10000000-0000-4000-8000-000000000002', 'Buzos y camperas', 'buzos-y-camperas', 'Abrigo para todos los días.', 2),
  ('10000000-0000-4000-8000-000000000003', 'Pantalones', 'pantalones', 'Joggers y jeans de calce cómodo.', 3),
  ('10000000-0000-4000-8000-000000000004', 'Accesorios', 'accesorios', 'Gorras, bolsos, medias y más.', 4)
on conflict (id) do nothing;

insert into public.products (id, category_id, name, slug, description, price, compare_at_price, images, active, featured, created_at) values
  ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'Remera Básica Algodón', 'remera-basica-algodon', 'La remera que vas a usar todos los días. Jersey de algodón peinado 24/1, cuello redondo con ribb y costuras reforzadas. Calce regular, no se deforma con los lavados.', 24990.00, null, array['/placeholders/remera-basica-algodon-1.svg', '/placeholders/remera-basica-algodon-2.svg']::text[], true, true, '2026-10-01T12:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000001', 'Remera Oversize Estampada', 'remera-oversize-estampada', 'Corte oversize con hombro caído y estampa frontal en serigrafía al agua. Algodón 100% de 180 g, suave y con buena caída.', 29990.00, 34990.00, array['/placeholders/remera-oversize-estampada-1.svg', '/placeholders/remera-oversize-estampada-2.svg']::text[], true, false, '2026-10-01T13:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000003', '10000000-0000-4000-8000-000000000001', 'Musculosa Deportiva Dry-Fit', 'musculosa-deportiva-dry-fit', 'Tela técnica liviana que seca rápido y no se pega al cuerpo. Ideal para entrenar o salir a correr en verano.', 19990.00, null, array['/placeholders/musculosa-deportiva-dry-fit-1.svg', '/placeholders/musculosa-deportiva-dry-fit-2.svg']::text[], true, false, '2026-10-01T14:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000004', '10000000-0000-4000-8000-000000000002', 'Buzo Canguro Frisa', 'buzo-canguro-frisa', 'Buzo con capucha y bolsillo canguro en frisa invisible de algodón. Puños y cintura con elastano para que mantenga la forma.', 54990.00, null, array['/placeholders/buzo-canguro-frisa-1.svg', '/placeholders/buzo-canguro-frisa-2.svg']::text[], true, true, '2026-10-01T15:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000005', '10000000-0000-4000-8000-000000000002', 'Buzo Cuello Redondo Liso', 'buzo-cuello-redondo-liso', 'Clásico buzo de frisa sin capucha. Va con todo: jeans, joggers o arriba de una camisa.', 47990.00, null, array['/placeholders/buzo-cuello-redondo-liso-1.svg', '/placeholders/buzo-cuello-redondo-liso-2.svg']::text[], true, false, '2026-10-01T16:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000006', '10000000-0000-4000-8000-000000000002', 'Campera Rompeviento', 'campera-rompeviento', 'Campera liviana repelente al agua, con capucha guardable en el cuello y bolsillos con cierre. Se pliega en su propio bolsillo.', 69990.00, 79990.00, array['/placeholders/campera-rompeviento-1.svg', '/placeholders/campera-rompeviento-2.svg']::text[], true, true, '2026-10-01T17:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000007', '10000000-0000-4000-8000-000000000003', 'Jogger Frisa', 'jogger-frisa', 'Jogger de frisa con cintura elástica y cordón, bolsillos laterales y puño en el tobillo.', 44990.00, null, array['/placeholders/jogger-frisa-1.svg', '/placeholders/jogger-frisa-2.svg']::text[], true, false, '2026-10-01T18:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000008', '10000000-0000-4000-8000-000000000003', 'Jean Recto Clásico', 'jean-recto-clasico', 'Denim rígido 12 oz de corte recto y tiro medio. Cinco bolsillos y botón metálico.', 64990.00, null, array['/placeholders/jean-recto-clasico-1.svg', '/placeholders/jean-recto-clasico-2.svg']::text[], true, false, '2026-10-01T19:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000009', '10000000-0000-4000-8000-000000000004', 'Gorra Trucker', 'gorra-trucker', 'Gorra con frente de gabardina, red trasera y cierre regulable a presión. Talle único.', 18990.00, null, array['/placeholders/gorra-trucker-1.svg', '/placeholders/gorra-trucker-2.svg']::text[], true, false, '2026-10-01T20:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000010', '10000000-0000-4000-8000-000000000004', 'Tote Bag de Lona', 'tote-bag-de-lona', 'Bolso de lona natural reforzada con manijas largas y bolsillo interno. Entra la notebook.', 15990.00, null, array['/placeholders/tote-bag-de-lona-1.svg', '/placeholders/tote-bag-de-lona-2.svg']::text[], true, true, '2026-10-01T21:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000011', '10000000-0000-4000-8000-000000000004', 'Pack x3 Medias de Algodón', 'pack-x3-medias-de-algodon', 'Tres pares de medias de caña media con puño suave y talón reforzado. Colores surtidos.', 9990.00, null, array['/placeholders/pack-x3-medias-de-algodon-1.svg', '/placeholders/pack-x3-medias-de-algodon-2.svg']::text[], true, false, '2026-10-01T22:00:00.000Z'::timestamptz),
  ('20000000-0000-4000-8000-000000000012', '10000000-0000-4000-8000-000000000004', 'Mate de Calabaza con Bombilla', 'mate-de-calabaza-con-bombilla', 'Mate de calabaza forrado en cuero con virola de alpaca y bombilla de acero inoxidable. Viene curado y listo para usar.', 27990.00, null, array['/placeholders/mate-de-calabaza-con-bombilla-1.svg', '/placeholders/mate-de-calabaza-con-bombilla-2.svg']::text[], true, true, '2026-10-01T23:00:00.000Z'::timestamptz)
on conflict (id) do nothing;

insert into public.product_variants (id, product_id, name, sku, price, stock, position) values
  ('30000000-0000-4000-8000-000000000101', '20000000-0000-4000-8000-000000000001', 'S', 'REM-BAS-S', null, 10, 0),
  ('30000000-0000-4000-8000-000000000102', '20000000-0000-4000-8000-000000000001', 'M', 'REM-BAS-M', null, 15, 1),
  ('30000000-0000-4000-8000-000000000103', '20000000-0000-4000-8000-000000000001', 'L', 'REM-BAS-L', null, 12, 2),
  ('30000000-0000-4000-8000-000000000104', '20000000-0000-4000-8000-000000000001', 'XL', 'REM-BAS-XL', null, 6, 3),
  ('30000000-0000-4000-8000-000000000201', '20000000-0000-4000-8000-000000000002', 'S', 'REM-OVS-S', null, 4, 0),
  ('30000000-0000-4000-8000-000000000202', '20000000-0000-4000-8000-000000000002', 'M', 'REM-OVS-M', null, 8, 1),
  ('30000000-0000-4000-8000-000000000203', '20000000-0000-4000-8000-000000000002', 'L', 'REM-OVS-L', null, 7, 2),
  ('30000000-0000-4000-8000-000000000204', '20000000-0000-4000-8000-000000000002', 'XL', 'REM-OVS-XL', null, 2, 3),
  ('30000000-0000-4000-8000-000000000301', '20000000-0000-4000-8000-000000000003', 'S', 'MUS-DRY-S', null, 9, 0),
  ('30000000-0000-4000-8000-000000000302', '20000000-0000-4000-8000-000000000003', 'M', 'MUS-DRY-M', null, 11, 1),
  ('30000000-0000-4000-8000-000000000303', '20000000-0000-4000-8000-000000000003', 'L', 'MUS-DRY-L', null, 5, 2),
  ('30000000-0000-4000-8000-000000000401', '20000000-0000-4000-8000-000000000004', 'S', 'BUZ-CAN-S', null, 5, 0),
  ('30000000-0000-4000-8000-000000000402', '20000000-0000-4000-8000-000000000004', 'M', 'BUZ-CAN-M', null, 9, 1),
  ('30000000-0000-4000-8000-000000000403', '20000000-0000-4000-8000-000000000004', 'L', 'BUZ-CAN-L', null, 8, 2),
  ('30000000-0000-4000-8000-000000000404', '20000000-0000-4000-8000-000000000004', 'XL', 'BUZ-CAN-XL', null, 3, 3),
  ('30000000-0000-4000-8000-000000000501', '20000000-0000-4000-8000-000000000005', 'S', 'BUZ-RED-S', null, 6, 0),
  ('30000000-0000-4000-8000-000000000502', '20000000-0000-4000-8000-000000000005', 'M', 'BUZ-RED-M', null, 7, 1),
  ('30000000-0000-4000-8000-000000000503', '20000000-0000-4000-8000-000000000005', 'L', 'BUZ-RED-L', null, 6, 2),
  ('30000000-0000-4000-8000-000000000504', '20000000-0000-4000-8000-000000000005', 'XL', 'BUZ-RED-XL', null, 4, 3),
  ('30000000-0000-4000-8000-000000000601', '20000000-0000-4000-8000-000000000006', 'M', 'CAM-ROM-M', null, 4, 0),
  ('30000000-0000-4000-8000-000000000602', '20000000-0000-4000-8000-000000000006', 'L', 'CAM-ROM-L', null, 5, 1),
  ('30000000-0000-4000-8000-000000000603', '20000000-0000-4000-8000-000000000006', 'XL', 'CAM-ROM-XL', null, 2, 2),
  ('30000000-0000-4000-8000-000000000701', '20000000-0000-4000-8000-000000000007', 'S', 'JOG-FRI-S', null, 7, 0),
  ('30000000-0000-4000-8000-000000000702', '20000000-0000-4000-8000-000000000007', 'M', 'JOG-FRI-M', null, 10, 1),
  ('30000000-0000-4000-8000-000000000703', '20000000-0000-4000-8000-000000000007', 'L', 'JOG-FRI-L', null, 8, 2),
  ('30000000-0000-4000-8000-000000000704', '20000000-0000-4000-8000-000000000007', 'XL', 'JOG-FRI-XL', null, 4, 3),
  ('30000000-0000-4000-8000-000000000801', '20000000-0000-4000-8000-000000000008', '38', 'JEA-REC-38', null, 3, 0),
  ('30000000-0000-4000-8000-000000000802', '20000000-0000-4000-8000-000000000008', '40', 'JEA-REC-40', null, 6, 1),
  ('30000000-0000-4000-8000-000000000803', '20000000-0000-4000-8000-000000000008', '42', 'JEA-REC-42', null, 6, 2),
  ('30000000-0000-4000-8000-000000000804', '20000000-0000-4000-8000-000000000008', '44', 'JEA-REC-44', null, 4, 3),
  ('30000000-0000-4000-8000-000000000805', '20000000-0000-4000-8000-000000000008', '46', 'JEA-REC-46', null, 2, 4),
  ('30000000-0000-4000-8000-000000000901', '20000000-0000-4000-8000-000000000009', 'Único', 'GOR-TRU', null, 20, 0),
  ('30000000-0000-4000-8000-000000001001', '20000000-0000-4000-8000-000000000010', 'Único', 'TOT-LON', null, 25, 0),
  ('30000000-0000-4000-8000-000000001101', '20000000-0000-4000-8000-000000000011', '35 a 39', 'MED-PK3-35A39', null, 18, 0),
  ('30000000-0000-4000-8000-000000001102', '20000000-0000-4000-8000-000000000011', '40 a 44', 'MED-PK3-40A44', null, 2, 1),
  ('30000000-0000-4000-8000-000000001201', '20000000-0000-4000-8000-000000000012', 'Único', 'MAT-CAL', null, 0, 0)
on conflict (id) do nothing;
