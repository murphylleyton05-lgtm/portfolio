-- Evaluación Final — Ejercicio 1 (Consulta SQL)
-- Alumno: Murphy, Lleyton  ·  Proyecto RetailPro / TechStore
-- Extrae cliente, fecha y total de las ventas de los últimos 30 días
-- (contados desde la última venta del dataset) ordenadas por fecha desc.

-- ---- Variante SQL Server / estándar ----
SELECT
    c.nombre_cliente AS cliente,
    v.fecha_venta    AS fecha_compra,
    v.total_venta    AS total
FROM ventas v
JOIN clientes c ON c.id_cliente = v.id_cliente
WHERE v.fecha_venta >= DATEADD(day, -30, (SELECT MAX(fecha_venta) FROM ventas))
ORDER BY v.fecha_venta DESC;

-- ---- Variante SQLite (usada para ejecutar y capturar el resultado) ----
-- SELECT c.nombre_cliente AS cliente,
--        date(v.fecha_venta) AS fecha_compra,
--        v.total_venta AS total
-- FROM ventas v
-- JOIN clientes c ON c.id_cliente = v.id_cliente
-- WHERE date(v.fecha_venta) >= date((SELECT MAX(fecha_venta) FROM ventas), '-30 day')
-- ORDER BY v.fecha_venta DESC;

-- Resultado real (ventana 2024-10-09 → 2024-11-08):
--   Carlos Rojas | 2024-11-08 | 758.10
--   Ana Torres   | 2024-10-31 | 209.00
--   Carlos Rojas | 2024-10-22 | 399.00
