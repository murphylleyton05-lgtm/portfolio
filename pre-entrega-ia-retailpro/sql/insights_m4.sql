-- ============================================================================
--  RetailPro — Consultas de análisis (Módulo 4)
--  Agregaciones que alimentan los insights comerciales de la pre-entrega de IA.
--  Todas las cifras del documento salen de estas consultas (fuente trazable).
-- ============================================================================

-- 1) KPIs generales -----------------------------------------------------------
SELECT ROUND(SUM(total_venta), 2) AS ingreso_total,
       COUNT(*)                   AS n_ventas,
       ROUND(AVG(total_venta), 2) AS ticket_promedio,
       SUM(cantidad)              AS unidades
FROM fact_ventas;

-- 2) Ingreso por categoría ----------------------------------------------------
SELECT p.categoria,
       COUNT(*)                     AS ventas,
       SUM(v.cantidad)              AS unidades,
       ROUND(SUM(v.total_venta), 2) AS ingreso,
       ROUND(100.0 * SUM(v.total_venta) /
             (SELECT SUM(total_venta) FROM fact_ventas), 1) AS pct
FROM fact_ventas v
JOIN dim_productos p ON v.id_producto = p.id_producto
GROUP BY p.categoria
ORDER BY ingreso DESC;

-- 3) Ingreso por canal --------------------------------------------------------
SELECT canal,
       COUNT(*)                     AS ventas,
       ROUND(SUM(total_venta), 2)   AS ingreso,
       ROUND(AVG(total_venta), 2)   AS ticket_promedio
FROM fact_ventas
GROUP BY canal
ORDER BY ingreso DESC;

-- 4) Top 5 productos por ingreso ---------------------------------------------
SELECT p.nombre_producto, p.categoria,
       SUM(v.cantidad)              AS unidades,
       ROUND(SUM(v.total_venta), 2) AS ingreso
FROM fact_ventas v
JOIN dim_productos p ON v.id_producto = p.id_producto
GROUP BY p.id_producto
ORDER BY ingreso DESC
LIMIT 5;

-- 5) Top 5 clientes por ingreso ----------------------------------------------
SELECT c.nombre_cliente, c.ciudad,
       COUNT(*)                     AS compras,
       ROUND(SUM(v.total_venta), 2) AS gastado
FROM fact_ventas v
JOIN dim_clientes c ON v.id_cliente = c.id_cliente
GROUP BY c.id_cliente
ORDER BY gastado DESC
LIMIT 5;

-- 6) Ingreso por año ----------------------------------------------------------
SELECT substr(fecha_venta, 1, 4)  AS anio,
       COUNT(*)                    AS ventas,
       ROUND(SUM(total_venta), 2)  AS ingreso
FROM fact_ventas
GROUP BY anio
ORDER BY anio;
