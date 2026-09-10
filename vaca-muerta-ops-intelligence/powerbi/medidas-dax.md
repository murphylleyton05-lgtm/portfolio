# Medidas DAX — Vaca Muerta Operations Intelligence

Modelo en **esquema estrella**. Importá los CSV de `../data` a Power BI Desktop y creá estas relaciones:

```
dim_operador[operador]  1 ─── *  fact_produccion[operador]
dim_area[area]          1 ─── *  fact_produccion[area]
dim_pozo[pozo_id]       1 ─── *  fact_produccion[pozo_id]
dim_fecha[mes]          1 ─── *  fact_produccion[mes]
dim_fecha[mes]          1 ─── *  fact_actividad[mes]
```

> Marcá `dim_fecha` como **tabla de fechas** (creá una columna `fecha` real con
> `Fecha = DATE(dim_fecha[anio], dim_fecha[mes_num], 1)`) para que funcionen las
> funciones de time intelligence (`PREVIOUSMONTH`, `DATESYTD`, etc.).

---

## Producción

```DAX
Petroleo bbl = SUM( fact_produccion[petroleo_bbl] )

Petroleo bbl/d =
DIVIDE( [Petroleo bbl], 30.4 )

Gas Mm3 = SUM( fact_produccion[gas_mm3] )

Gas Mm3/d =
DIVIDE( [Gas Mm3], 30.4 )

Agua bbl = SUM( fact_produccion[agua_bbl] )
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
Pozos activos = DISTINCTCOUNT( fact_produccion[pozo_id] )

Pozos en cartera = DISTINCTCOUNT( dim_pozo[pozo_id] )

Produccion por pozo (bbl/d) =
DIVIDE( [Petroleo bbl/d], [Pozos activos] )
```

## Actividad

```DAX
Spuds = SUM( fact_actividad[spuds] )

Completions = SUM( fact_actividad[completions] )

Pozos perforados (acum) =
CALCULATE(
    [Spuds],
    FILTER( ALL( dim_fecha ), dim_fecha[fecha] <= MAX( dim_fecha[fecha] ) )
)
```

## Inversión (desde dim_pozo)

```DAX
Inversion (MM US$) = SUM( dim_pozo[costo_musd] )
```

## Share de operador

```DAX
Share operador % =
DIVIDE(
    [Petroleo bbl/d],
    CALCULATE( [Petroleo bbl/d], ALL( dim_operador ) )
)
```

---

Con estas medidas armás las visuales del tablero: un gráfico de líneas de
**Petroleo bbl/d** y **Gas Mm3/d** por `dim_fecha[fecha]`, un área de
**Oil acumulado (MMbbl)**, barras de **Spuds**/**Completions** por mes, una
tabla de operadores con **Share operador %**, y tarjetas para los KPIs.
