# 🛢️ Vaca Muerta Operations Intelligence (+ Power BI)

Tablero de **operaciones** de los pozos no convencionales de Vaca Muerta: producción de petróleo y gas,
actividad (pozos nuevos en producción), acumulado y ranking de operadores — con el **modelo de datos**
y las **medidas DAX** listas para reconstruirlo en **Power BI**.

> **Datos oficiales de la Secretaría de Energía** (los mismos que
> [`vaca-muerta-analytics`](../vaca-muerta-analytics)). El tablero se **regenera automáticamente por CI**
> con la producción real. Localmente, sin correr el pipeline, usa la versión demo (mismo esquema).

**🔗 Dashboard en vivo:** https://murphylleyton05-lgtm.github.io/portfolio/operaciones/

---

## De dónde salen los datos

Este proyecto **no baja datos por su cuenta**: reutiliza los parquets procesados por el pipeline de
`vaca-muerta-analytics`, que descarga y limpia la producción oficial de pozos no convencionales.

- `scripts/construir_datos.py` lee `../vaca-muerta-analytics/data/procesado/{produccion,pozos}.parquet`
  y arma `web/datos.json` con las series y agregados.
- `scripts/armar_web.py` inyecta ese JSON en la plantilla y arma el dashboard.

En CI, el workflow **Actualizar Vaca Muerta** procesa los datos reales y, en el mismo job, regenera este
tablero — así queda siempre con los últimos datos oficiales.

```bash
# Local (usa la versión demo de los parquets si no corriste el pipeline):
cd vaca-muerta-ops-intelligence
python3 scripts/construir_datos.py
python3 scripts/armar_web.py
```

Dependencias: **pandas** (+ pyarrow) y la librería estándar.

## Qué muestra

- **Producción** de petróleo (bbl/d) y gas (Mm³/d) mes a mes.
- **Producción acumulada** (histórica).
- **Actividad**: pozos que entran en producción cada mes.
- **Ranking de operadores** por producción, share, pozos y acumulado.
- **Mix por ventana de fluido** y **top pozos** por acumulado.
- Indicadores con variación mes contra mes.

## La capa Power BI

`powerbi/medidas-dax.md` trae las medidas DAX sobre el esquema real
(`produccion.parquet` como tabla de hechos, `pozos.parquet` como dimensión). Power BI importa parquet
directo; se marcan las relaciones y se pegan las medidas.

> El `.pbix` binario se autorea en Power BI Desktop; acá se entrega el modelo (parquet) y las medidas.

## Lo que **no** hace

- Muestra producción y actividad, **no** reservas (EUR) ni validación de curvas — eso está en `vaca-muerta-analytics`.
- El dataset no trae fecha de spud: la "actividad" se mide por el mes de primera producción de cada pozo.
- No incluye el `.pbix`.

---

_Proyecto de portfolio · Lleyton Murphy · datos oficiales de la Secretaría de Energía._
