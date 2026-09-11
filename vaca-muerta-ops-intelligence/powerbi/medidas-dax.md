# Medidas DAX — Vaca Muerta Operations Intelligence

Fuente: los parquets procesados por el pipeline oficial
(`../vaca-muerta-analytics/data/procesado/`). Power BI Desktop importa **parquet** directo
(Obtener datos → Más → Parquet, o vía carpeta).

- `produccion.parquet` → tabla de hechos (`fact_produccion`), una fila por **pozo × mes**.
- `pozos.parquet` → dimensión de pozos (`dim_pozo`).
- Creá una `dim_fecha` (tabla de fechas) a partir de `produccion[fecha]` con
  `CALENDAR(MIN(fact_produccion[fecha]), MAX(fact_produccion[fecha]))` y marcala como tabla de fechas.

## Relaciones

```
dim_pozo[id_pozo]   1 ─── *  fact_produccion[id_pozo]
dim_fecha[fecha]    1 ─── *  fact_produccion[fecha]
```

> Nota de unidades: la producción viene en **m³** (`prod_petroleo_m3`) y en **Mm³** de gas
> (`prod_gas_mm3`, miles de m³). Para petróleo en barriles se usa **1 m³ = 6,28981 bbl**.

---

## Producción

```DAX
Petroleo m3 = SUM( fact_produccion[prod_petroleo_m3] )

Petroleo bbl = [Petroleo m3] * 6.28981

Petroleo bbl/d = DIVIDE( [Petroleo bbl], 30.4 )

Gas Mm3 = SUM( fact_produccion[prod_gas_mm3] )

Gas Mm3/d = DIVIDE( [Gas Mm3], 30.4 )
```

## Acumulado (running total)

```DAX
Oil acumulado (MMbbl) =
DIVIDE(
    CALCULATE(
        [Petroleo bbl],
        FILTER( ALL( dim_fecha ), dim_fecha[fecha] <= MAX( dim_fecha[fecha] ) )
    ),
    1000000
)
```

## Variación mes contra mes

```DAX
Petroleo bbl/d mes anterior =
CALCULATE( [Petroleo bbl/d], PREVIOUSMONTH( dim_fecha[fecha] ) )

Var MoM % =
VAR ant = [Petroleo bbl/d mes anterior]
RETURN DIVIDE( [Petroleo bbl/d] - ant, ant )
```

## Pozos y productividad

```DAX
Pozos activos = DISTINCTCOUNT( fact_produccion[id_pozo] )

Produccion por pozo (bbl/d) = DIVIDE( [Petroleo bbl/d], [Pozos activos] )
```

## Actividad (pozos nuevos)

```DAX
-- Pozos que registran su PRIMERA producción en el período filtrado.
Pozos nuevos =
CALCULATE(
    DISTINCTCOUNT( fact_produccion[id_pozo] ),
    FILTER(
        VALUES( fact_produccion[id_pozo] ),
        CALCULATE( MIN( fact_produccion[fecha] ) ) IN VALUES( dim_fecha[fecha] )
    )
)
```

## Share de operador

```DAX
Share operador % =
DIVIDE(
    [Petroleo bbl/d],
    CALCULATE( [Petroleo bbl/d], ALL( fact_produccion[empresa] ) )
)
```

---

Con estas medidas armás las visuales: líneas de **Petroleo bbl/d** y **Gas Mm3/d** por
`dim_fecha[fecha]`, un área de **Oil acumulado (MMbbl)**, barras de **Pozos nuevos** por mes, una tabla de
operadores (`empresa`) con **Share operador %**, y tarjetas para los KPIs.
