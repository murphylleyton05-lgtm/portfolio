-- ============================================================================
--  RetailPro — Consulta base del modelo (Módulo 5)
--  Une la tabla de hechos de ventas con sus 3 dimensiones.
--  Motor: SQLite. Devuelve el detalle de cada venta enriquecido.
--  NOTA: esta es la versión ORIGINAL con INNER JOIN. Ver el análisis de la
--  pre-entrega de IA: el INNER JOIN sobre categoría descarta silenciosamente
--  las ventas cuyo producto tiene la categoría nula (2 de 50 en el dataset).
-- ============================================================================
SELECT
    v.id_venta,
    v.fecha_venta,
    c.nombre_cliente,
    c.ciudad,
    c.pais,
    p.nombre_producto,
    cat.nombre_categoria,
    v.cantidad,
    v.precio_unitario,
    v.descuento,
    v.total_venta,
    v.canal
FROM fact_ventas       AS v
INNER JOIN dim_clientes   AS c   ON v.id_cliente  = c.id_cliente
INNER JOIN dim_productos  AS p   ON v.id_producto = p.id_producto
INNER JOIN dim_categorias AS cat ON p.categoria   = cat.nombre_categoria
ORDER BY v.fecha_venta;
