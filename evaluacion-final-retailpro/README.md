# Evaluación Final — Proyecto Integrador RetailPro

Entrega que cierra el programa de Data Analytics. Integra SQL, estadística y
Power BI sobre el dataset real del proyecto (TechStore / RetailPro).

**Alumno:** Murphy, Lleyton

## Entregable

- [`entrega/Evaluacion_Final_RetailPro_Murphy_Lleyton.docx`](entrega/Evaluacion_Final_RetailPro_Murphy_Lleyton.docx)

Documento único con:

- **Reporte de análisis:** contexto/pregunta de negocio, dataset y fuentes, EDA
  (validación estadística: media vs. mediana, IQR, outliers), conclusiones.
- **Sección 1 — Teoría:** datos vs. información, sublenguajes SQL, IA en el
  análisis, principios de storytelling.
- **Sección 2 — Práctica:** Ej.1 consulta SQL (últimos 30 días, ordenada) con
  resultado real; Ej.2 diagrama ER (esquema en estrella); Ej.3
  visualización + storytelling con boceto de dashboard.

## Datos

Se usan los datos reales del proyecto en
[`../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx`](../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx)
(tabla `ventas` = 50 operaciones depuradas). Esto mantiene el "hilo conductor"
con el resto del proyecto integrador (ETL, modelo DAX, dashboard y la
pre-entrega de validación estadística).

## Consulta SQL del Ejercicio 1

```sql
SELECT c.nombre_cliente, v.fecha_venta, v.total_venta
FROM ventas AS v
JOIN clientes AS c ON v.id_cliente = c.id_cliente
WHERE v.fecha_venta > (SELECT MAX(fecha_venta) FROM ventas) - INTERVAL '30 days'
ORDER BY v.fecha_venta DESC;
```

Ventana de 30 días desde la última venta (2024-11-08) → 3 registros.

## Antes de entregar

El evaluador pide capturas reales de las herramientas. Reemplazá en el `.docx`:

- **Ejercicio 1:** la consulta y su tabla, por una captura de tu editor
  (pgAdmin / SSMS / DBeaver) ejecutando la query sobre tu base.
- **Figura 2 (dashboard):** por una captura de tu Power BI real.

Verificá también que el documento (si lo pasás a Google Docs) tenga acceso
público/de revisión y que no incluya enlaces externos.

## Reproducir

```bash
pip install openpyxl matplotlib
python3 scripts/er_diagram.py      # regenera img/er_diagram.png
python3 scripts/dashboard.py       # regenera img/dashboard.png
npm install docx && node scripts/build_final.js entrega/Evaluacion_Final_RetailPro_Murphy_Lleyton.docx
```
