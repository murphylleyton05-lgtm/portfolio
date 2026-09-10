# 🛢️ Vaca Muerta Operations Intelligence (+ Power BI)

Tablero de **operaciones** de una cartera de pozos de Vaca Muerta: producción de petróleo y gas,
actividad de perforación y completación, acumulado y ranking de operadores — con el **modelo de datos
en esquema estrella y las medidas DAX** listas para reconstruirlo en **Power BI**.

> Datos **simulados** con Python (numpy, semilla fija). El proyecto hermano
> [`vaca-muerta-analytics`](../vaca-muerta-analytics) usa los **datos oficiales reales** de la
> Secretaría de Energía; este se enfoca en la vista de management y la capa Power BI.

**🔗 Dashboard en vivo:** https://murphylleyton05-lgtm.github.io/portfolio/operaciones/

---

## Qué muestra

- **Producción** de petróleo (bbl/d) y gas (Mm³/d) mes a mes, creciendo a medida que se conectan pozos.
- **Producción acumulada** de la cartera.
- **Actividad**: pozos iniciados (spuds) vs. completados por mes.
- **Ranking de operadores** por producción, share, pozos e inversión.
- **Mix por ventana de fluido** y **top pozos** por acumulado.
- Indicadores de período con variación mes contra mes.

## La capa Power BI

Lo importante de este proyecto no es solo el dashboard web, sino que los datos quedan **modelados para BI**:

- `data/` tiene el **esquema estrella**: una tabla de hechos (`fact_produccion`) rodeada de dimensiones
  (`dim_pozo`, `dim_operador`, `dim_area`, `dim_fecha`), más `fact_actividad`.
- `powerbi/medidas-dax.md` trae las **medidas DAX** listas para pegar: producción bbl/d, acumulado con
  running total, variación MoM, pozos activos con `DISTINCTCOUNT`, share de operador, etc.

Con eso, en Power BI Desktop: importás los CSV, marcás las relaciones, marcás `dim_fecha` como tabla de
fechas y armás las visuales en minutos.

> El archivo binario `.pbix` no se incluye (se autoría en Power BI Desktop), pero se entrega **todo lo
> necesario para reconstruirlo**: el modelo y las medidas.

## Cómo funciona

```bash
cd vaca-muerta-ops-intelligence
python3 scripts/simular.py    # cartera + producción (Arps) + actividad -> CSVs + datos.json
python3 scripts/armar_web.py  # arma el dashboard web
```

Dependencias: **numpy** y la librería estándar.

## Modelo de datos (esquema estrella)

```
dim_operador ─┐
dim_area ─────┤
dim_pozo ─────┼─< fact_produccion   (pozo × mes: petróleo, gas, agua)
dim_fecha ────┤
              └─< fact_actividad     (mes: spuds, completions)
```

## Lo que **no** hace

- Datos simulados, no oficiales (para datos reales, ver `vaca-muerta-analytics`).
- Es una vista de producción y actividad, no de reservas (EUR) ni validación de curvas.
- El costo por pozo es un estimado por longitud de rama y etapas, no un costo contable.
- No incluye el `.pbix`: entrega el modelo estrella + las medidas DAX para reconstruirlo.

---

_Proyecto de portfolio · Lleyton Murphy · datos simulados._
