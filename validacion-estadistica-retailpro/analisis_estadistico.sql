-- Validación estadística de RetailPro — Módulo 10
-- Alumno: Murphy, Lleyton
-- Fuente: Fact_Ventas del proyecto TechStore (columna total_venta, n = 50)
-- Los mismos cálculos del paso guiado, aplicados a los datos reales del proyecto.

-- ================================================================
-- PARTE 1 (caso guiado) — cargar en una tabla ventas_semana
--   columnas: sucursal (text), venta (numeric)
--   Norte: 500, 510, 490, 505, 495
--   Sur  : 100, 900, 50, 1200, 250
-- ================================================================

-- 1) Media y rango por sucursal
SELECT
    sucursal,
    AVG(venta)              AS media,        -- Norte 500 · Sur 500
    MAX(venta) - MIN(venta) AS rango         -- Norte 20  · Sur 1150
FROM ventas_semana
GROUP BY sucursal;

-- 2) Desviación estándar MUESTRAL (n-1)
SELECT
    sucursal,
    STDDEV_SAMP(venta) AS desvio_muestral    -- Norte ≈ 7,91 · Sur ≈ 518,41
FROM ventas_semana                           -- (SQL Server: STDEV(venta))
GROUP BY sucursal;

-- ================================================================
-- PARTE 2 — validación sobre los datos reales de RetailPro
--   Se usa la tabla de hechos del proyecto. Aquí se referencia como
--   ventas(total_venta); en el modelo es Fact_Ventas[total_venta].
-- ================================================================

-- 2a) Ticket promedio: media vs. mediana
SELECT
    AVG(total_venta)                                         AS media,    -- 528,46
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_venta) AS mediana   -- 370,02
FROM ventas;
-- media (528,46) >> mediana (370,02)  => distribución sesgada a la derecha:
-- el KPI "Ticket Promedio" está inflado por ventas extremas.

-- 2b) Outliers por método IQR (Q1, Q3, IQR y límites)
WITH q AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_venta) AS q1,  -- 179,61
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_venta) AS q3   -- 739,80
    FROM ventas
)
SELECT
    q1, q3,
    (q3 - q1)          AS iqr,               -- 560,19
    q1 - 1.5*(q3 - q1) AS limite_inferior,   -- -660,67
    q3 + 1.5*(q3 - q1) AS limite_superior    -- 1580,08
FROM q;

-- Listado de outliers (4 registros, todos por encima del límite superior)
WITH q AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_venta) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_venta) AS q3
    FROM ventas
)
SELECT v.*
FROM ventas v, q
WHERE v.total_venta < q.q1 - 1.5*(q.q3 - q.q1)
   OR v.total_venta > q.q3 + 1.5*(q.q3 - q.q1)
ORDER BY v.total_venta;
-- id 9  (Notebook Lenovo, 2u)  = 1.700,00
-- id 22 (Galaxy A54, 4u)       = 1.596,00
-- id 45 (Notebook HP, 2u -desc)= 1.748,95
-- id 37 (Notebook HP, 4u)      = 3.682,00
-- Todos reconcilian con precio_unitario*cantidad - descuento => eventos legítimos
-- (compras por volumen de alto valor), no errores de carga.
