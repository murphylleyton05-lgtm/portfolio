-- ============================================================================
--  RetailPro — Consulta base OPTIMIZADA (resultado de la Tarea 1 de IA)
--  Cambio aceptado tras la revisión con IA + criterio propio:
--    * dim_categorias pasa de INNER JOIN a LEFT JOIN, para NO perder las ventas
--      cuyo producto quedó con categoría nula ("Sin Categoria"). Con INNER JOIN
--      se perdían 2 de 50 ventas (USD 471,94; el 1,8 % del ingreso).
--    * Se preservan las 50 ventas de la tabla de hechos.
--  Índices sugeridos por la IA (útiles a mayor volumen; en 50 filas son
--  irrelevantes, se dejan documentados para escalabilidad):
--    CREATE INDEX IF NOT EXISTS ix_ventas_cliente  ON fact_ventas(id_cliente);
--    CREATE INDEX IF NOT EXISTS ix_ventas_producto ON fact_ventas(id_producto);
-- ============================================================================
SELECT
    v.id_venta,
    v.fecha_venta,
    c.nombre_cliente,
    c.ciudad,
    c.pais,
    p.nombre_producto,
    COALESCE(cat.nombre_categoria, 'Sin Categoria') AS categoria,
    v.cantidad,
    v.precio_unitario,
    v.descuento,
    v.total_venta,
    v.canal
FROM fact_ventas       AS v
INNER JOIN dim_clientes  AS c   ON v.id_cliente  = c.id_cliente
INNER JOIN dim_productos AS p   ON v.id_producto = p.id_producto
LEFT  JOIN dim_categorias AS cat ON p.categoria  = cat.nombre_categoria
ORDER BY v.fecha_venta;
