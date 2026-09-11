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
   - Ej. 1 — Consulta SQL sobre un **dataset real de Kaggle («Global Superstore»)**, separado en `ventas` + `clientes` (últimos 30 días, cliente/fecha/total, orden desc) — *ejecutada de verdad*.
   - Ej. 2 — Modelo de datos (diagrama ER en estrella).
   - Ej. 3 — Visualización y storytelling.
3. **Reporte integrador RetailPro** — Contexto · Dataset · EDA · Modelo+SQL ·
   Transformación (Power Query) · Dashboard · Conclusiones e insights.

## Datos y fuentes

- **Ejercicio 1 (SQL):** dataset público de Kaggle **Global Superstore**
  (`global_superstore.csv`, 1.000 pedidos), separado en `ventas` + `clientes`.
- **Ejercicios 2–3 y reporte integrador:** tablas de RetailPro desde
  [`../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx`](../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx)
  (ventas 50 · clientes 11 · productos 12 · categorías 4, tras limpiar; período
  2023-01-10 → 2024-11-08).

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
python kaggle_ej1.py  # Ejercicio 1: separa Global Superstore y corre la consulta (Kaggle)
python sql_kaggle.py  # captura del resultado del Ejercicio 1
python agg.py         # agregados del dashboard RetailPro -> agg.json
python charts.py      # gráficos del dashboard/EDA en assets/
python sql_er.py      # diagrama ER de RetailPro
```

- [`ejercicio1_ultimos30dias.sql`](./ejercicio1_ultimos30dias.sql) — consulta del Ejercicio 1 (SQL Server + SQLite).
- `global_superstore.csv` — dataset de Kaggle usado en el Ejercicio 1.
- `assets/` — visuales embebidos en el `.docx`.

> **Nota:** las capturas de SQL muestran la ejecución real sobre las tablas del
> proyecto; los gráficos representan la página de Power BI y pueden sustituirse por
> capturas nativas de Power BI Desktop si el evaluador lo requiere.
