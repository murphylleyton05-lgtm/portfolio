# Evaluación Final — Proyecto Integrador RetailPro

**Instancia:** Evaluación Final del programa de Data Analytics
**Alumno:** Murphy, Lleyton
**Entregable:** [`Murphy_Lleyton_Evaluacion_Final_RetailPro.docx`](./Murphy_Lleyton_Evaluacion_Final_RetailPro.docx)

Reporte de análisis autocontenido que integra **SQL · Estadística · Power BI** sobre
el caso RetailPro (dataset TechStore). El documento se comprende sin abrir las
herramientas: incluye las consultas, sus resultados reales, el modelo, las
transformaciones y las visualizaciones.

## Estructura del entregable (.docx)

1. **Sección 1 — Preguntas Teóricas** (datos vs. información · sublenguajes SQL · IA · storytelling).
2. **Sección 2 — Ejercicios Prácticos**
   - Ej. 1 — Consulta SQL (últimos 30 días, cliente/fecha/total, orden desc) — *ejecutada de verdad*.
   - Ej. 2 — Modelo de datos (diagrama ER en estrella).
   - Ej. 3 — Visualización y storytelling.
3. **Reporte integrador RetailPro** — Contexto · Dataset · EDA · Modelo+SQL ·
   Transformación (Power Query) · Dashboard · Conclusiones e insights.

## Datos y fuente

Las tablas provienen de
[`../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx`](../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx)
(ventas 50 · clientes 11 · productos 12 · categorías 4, tras limpiar). Período
2023-01-10 → 2024-11-08.

## Hallazgos clave

- **Facturación total:** $26.423 · **Online 56% / Tienda 44%**.
- **Ticket promedio $528 vs. mediana $370** → distribución sesgada; se recomienda mostrar ambos.
- **4 outliers legítimos** por IQR (ventas mayoristas de notebooks/smartphone), no errores.
- **Notebooks + Smartphones = ~73%** de la facturación.
- El **−24% interanual** está distorsionado (2024 sin diciembre) → medir por YTD.

## Reproducibilidad

Los gráficos y la ejecución SQL se generan desde el dataset real:

```bash
cd evaluacion-final-retailpro
pip install openpyxl matplotlib pillow
python prep.py     # carga en SQLite y corre la consulta del Ejercicio 1
python agg.py      # calcula los agregados del dashboard -> agg.json
python charts.py   # genera los gráficos en assets/
python sql_er.py   # genera la captura SQL y el diagrama ER
```

- [`ejercicio1_ultimos30dias.sql`](./ejercicio1_ultimos30dias.sql) — consulta del Ejercicio 1 (SQL Server + SQLite).
- `assets/` — visuales embebidos en el `.docx`.

> **Nota:** las capturas de SQL muestran la ejecución real sobre las tablas del
> proyecto; los gráficos representan la página de Power BI y pueden sustituirse por
> capturas nativas de Power BI Desktop si el evaluador lo requiere.
