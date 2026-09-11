# Validación estadística del proyecto — RetailPro (Módulo 10)

**Checkpoint:** M10 · Pre-entrega — Validación estadística (y Dashboards en Power BI Service)
**Alumno:** Murphy, Lleyton
**Entregable:** [`Murphy_Lleyton_Validacion_Estadistica_RetailPro.docx`](./Murphy_Lleyton_Validacion_Estadistica_RetailPro.docx)

Validación estadística que confirma que los KPIs del dashboard de RetailPro son
confiables. El proyecto RetailPro se materializa en este portafolio con el dataset
**TechStore** (`Fact_Ventas`), por eso los cálculos de la Parte 2 se corren sobre
[`../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx`](../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx)
(hoja `ventas`, columna `total_venta`, n = 50).

## Contenido

```
validacion-estadistica-retailpro/
├─ README.md                                            ← este archivo
├─ Murphy_Lleyton_Validacion_Estadistica_RetailPro.docx ← ENTREGABLE (Parte 1 + Parte 2 + ajustes)
├─ analisis_estadistico.sql                             ← consultas SQL del paso guiado + Parte 2
└─ verificar_stats.py                                   ← recálculo reproducible de la Parte 2
```

## Resumen de resultados

### Parte 1 — Caso guiado (dos sucursales, s muestral n−1)

| Medida            | Norte  | Sur      |
|-------------------|:------:|:--------:|
| Media             | 500,00 | 500,00   |
| Rango             | 20,00  | 1.150,00 |
| Desv. estándar (s)| 7,91   | 518,41   |

Misma media, dispersión opuesta → **Norte** es la sucursal estable y preferible de gestionar.

### Parte 2 — Datos reales de RetailPro (`total_venta`, n = 50)

| Métrica          | Valor    |
|------------------|:--------:|
| Media            | 528,46   |
| Mediana          | 370,02   |
| Q1 / Q3          | 179,61 / 739,80 |
| IQR              | 560,19   |
| Límite sup. (IQR)| 1.580,08 |
| Outliers         | 4 (1.596 · 1.700 · 1.748,95 · 3.682) |

- **Media ≫ mediana (+43%)** → distribución sesgada a la derecha: el KPI *Ticket
  Promedio* está inflado por ventas extremas.
- **4 outliers legítimos** (notebooks y un smartphone comprados en volumen); cada
  total reconcilia con `precio_unitario × cantidad − descuento`. No son errores de carga.

### Ajuste al dashboard (boceto M7)

Se agrega el KPI **Ticket Mediano (≈ 370 USD)** junto al promedio y se cambia el
título narrativo a *"Venta típica ≈ 370 USD; el promedio 528 USD sube por ventas
mayoristas"*, con nota aclaratoria sobre las ventas B2B de alto valor.

## Reproducir

```bash
cd validacion-estadistica-retailpro
python verificar_stats.py         # requiere openpyxl
```

Salida esperada: media 528,46 · mediana 370,01 · Q1 179,61 · Q3 739,80 · IQR 560,19
· límites −660,67 / 1.580,08 · 4 outliers. Las mismas cifras se obtienen en SQL con
`analisis_estadistico.sql` (`AVG`, `PERCENTILE_CONT`, criterio IQR 1,5×).
