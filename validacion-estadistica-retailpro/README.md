# Validación estadística del proyecto — RetailPro / TechStore (Módulo 10)

**Pre-entrega evaluable del proyecto integrador.** Valida que los KPIs del
dashboard sean estadísticamente confiables aplicando tendencia central y
dispersión sobre un caso guiado (Parte 1) y sobre los datos reales del
proyecto (Parte 2).

**Alumno:** Murphy, Lleyton

## Entregable

- [`entrega/Pre-entrega_Validacion_estadistica_Murphy_Lleyton.docx`](entrega/Pre-entrega_Validacion_estadistica_Murphy_Lleyton.docx)
  — documento con las dos partes, cálculos en tabla y la sección final de
  ajustes al dashboard.

## Dataset validado

Columna `total_venta` de la tabla `ventas` (50 registros ya depurados en el
pipeline ETL), en
[`../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx`](../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx).

## Resultados

### Parte 1 — Caso guiado (dos sucursales, muestra de 5 días)

| Sucursal | Media | Rango | Desv. est. muestral | Lectura |
|----------|------:|------:|--------------------:|---------|
| Norte    | 500,00 |    20 |    7,91 | Muy estable |
| Sur      | 500,00 | 1.150 |  518,41 | Muy volátil |

Misma media, dispersión opuesta → **preferible gestionar Norte** por su
predictibilidad.

### Parte 2 — RetailPro (`total_venta`, n = 50)

**a) Ticket promedio real vs. representativo**

| Medida | Valor (USD) |
|--------|------------:|
| Media (AVG)   | 528,46 |
| Mediana (P50) | 370,01 |

Media 43 % por encima de la mediana → distribución **sesgada a la derecha**;
el KPI de Ticket Promedio está **inflado por ventas extremas**.

**b) Outliers por método IQR**

| Estadístico | Valor (USD) |
|-------------|------------:|
| Q1 | 179,61 |
| Q3 | 739,80 |
| IQR | 560,19 |
| Límite inferior | −660,67 |
| Límite superior | 1.580,08 |

**4 outliers** (ids 9, 22, 37, 45): 1.700 · 1.596 · 3.682 · 1.748,95. Son
**eventos legítimos de negocio** (notebooks y un smartphone comprados en
cantidades de 2–4), no errores de carga. Representan el 8 % de las
operaciones pero el 33 % de la facturación.

**c) Ajuste al dashboard**

Se agrega la **Mediana del Ticket** junto al Ticket Promedio y se cambia el
título narrativo del visual a *"Ticket típico $370 (mediana) — promedio $528
elevado por ventas de alto valor"*, con nota aclaratoria.

## SQL utilizado

```sql
-- a) Media vs. mediana
SELECT
  AVG(total_venta)                                         AS media,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_venta) AS mediana
FROM ventas;

-- b) Cuartiles, IQR y límites
WITH q AS (
  SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_venta) AS q1,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_venta) AS q3
  FROM ventas
)
SELECT q1, q3, (q3 - q1) AS iqr,
       q1 - 1.5*(q3 - q1) AS limite_inferior,
       q3 + 1.5*(q3 - q1) AS limite_superior
FROM q;
```

## Reproducir

```bash
# Verificar los cálculos sobre el dataset real
python3 verificar_estadisticas.py

# Regenerar el .docx (requiere: npm install docx)
node build_docx.js entrega/Pre-entrega_Validacion_estadistica_Murphy_Lleyton.docx
```
