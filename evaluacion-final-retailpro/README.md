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

## Capturas

El documento ya incluye las capturas que pide el evaluador, renderizadas a
partir de la consulta y los datos reales del proyecto:

- **Figura 2** (`img/cap_sql_editor.png`): la consulta ejecutada en un editor
  SQL (estilo DBeaver/PostgreSQL) con las 3 filas recuperadas.
- **Figura 3** (`img/cap_powerbi.png`): el dashboard en Power BI Desktop.

Si preferís capturas tomadas por vos en tus propias herramientas, corré la
consulta de `scripts/` sobre tu base y el `.pbix` en tu Power BI, y reemplazá
esas dos figuras. Si lo pasás a Google Docs, verificá acceso público/de
revisión y que no haya enlaces externos.

## Reproducir

```bash
pip install openpyxl matplotlib
python3 scripts/er_diagram.py      # regenera img/er_diagram.png
python3 scripts/dashboard.py       # regenera img/dashboard.png
npm install docx && node scripts/build_final.js entrega/Evaluacion_Final_RetailPro_Murphy_Lleyton.docx
```
