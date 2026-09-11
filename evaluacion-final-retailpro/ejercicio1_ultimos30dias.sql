-- Evaluación Final — Ejercicio 1 (Consulta SQL)
-- Alumno: Murphy, Lleyton
-- Dataset: Kaggle — «Global Superstore» (1.000 pedidos), retail global.
-- Viene en UNA sola tabla; se separa en dos entidades: ventas y clientes.
--   clientes(id_cliente, nombre_cliente, segmento, ciudad, pais)   -- por Customer ID (800 únicos)
--   ventas(order_id, id_cliente, fecha_compra, total_venta)        -- una línea por venta (Sales)
-- Preparación: Order Date -> tipo Date; se conservan cliente, fecha y total; sin nulos críticos.

-- ---- Variante SQL Server / estándar ----
SELECT
    c.nombre_cliente AS cliente,
    v.fecha_compra   AS fecha_compra,
    v.total_venta    AS total
FROM ventas v
JOIN clientes c ON c.id_cliente = v.id_cliente
WHERE v.fecha_compra >= DATEADD(day, -30, (SELECT MAX(fecha_compra) FROM ventas))
ORDER BY v.fecha_compra DESC;

-- ---- Variante SQLite (usada para ejecutar y capturar el resultado) ----
-- SELECT c.nombre_cliente AS cliente,
--        v.fecha_compra   AS fecha_compra,
--        v.total_venta    AS total
-- FROM ventas v
-- JOIN clientes c ON c.id_cliente = v.id_cliente
-- WHERE v.fecha_compra >= date((SELECT MAX(fecha_compra) FROM ventas), '-30 day')
-- ORDER BY v.fecha_compra DESC;

-- Resultado real: 40 filas (ventana 2015-12-01 -> 2015-12-31). Primeras filas:
--   Erica Bern          | 2015-12-31 | 1264.47
--   Marina Lichtenstein | 2015-12-31 | 1091.28
--   Harry Marie         | 2015-12-30 | 1913.40
--   Carlos Daly         | 2015-12-29 | 1461.14
--   Adam Hart           | 2015-12-29 | 1534.87
--
-- La separación en dos tablas y la carga se automatizan en kaggle_ej1.py
-- (fuente: raw.githubusercontent.com/yannie28/Global-Superstore).
