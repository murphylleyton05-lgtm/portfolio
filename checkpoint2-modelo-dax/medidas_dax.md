# Código DAX — Checkpoint 2

Copiar y pegar en Power BI Desktop. Nombres de tabla/columna según el modelo
del checkpoint anterior (`Fact_Ventas[total_venta]`, `Fact_Ventas[canal]`, etc.).

## Tabla calendario (Inicio → Nueva tabla)

Versión en un solo paso (crea la tabla y todas las columnas de tiempo a la vez):

```DAX
Dim_Fechas =
ADDCOLUMNS(
    CALENDAR(MIN(Fact_Ventas[fecha_venta]), MAX(Fact_Ventas[fecha_venta])),
    "Año", YEAR([Date]),
    "Mes Número", MONTH([Date]),
    "Mes Nombre", FORMAT([Date], "MMMM"),
    "Trimestre", "T" & QUARTER([Date]),
    "Semana", WEEKNUM([Date])
)
```

Luego: clic derecho en `Dim_Fechas` → **Marcar como tabla de fechas** → columna `Date`.

## Medidas (clic derecho en `_Medidas` → Nueva medida)

```DAX
Total Ventas = SUM(Fact_Ventas[total_venta])
```

```DAX
Ventas Online =
CALCULATE(
    [Total Ventas],
    Fact_Ventas[canal] = "Online"
)
```

```DAX
Ventas YTD =
TOTALYTD(
    [Total Ventas],
    Dim_Fechas[Date]
)
```

```DAX
Ventas LY =
CALCULATE(
    [Total Ventas],
    SAMEPERIODLASTYEAR(Dim_Fechas[Date])
)
```

```DAX
% Crecimiento Anual =
VAR VentasActual   = [Total Ventas]
VAR VentasAnterior = [Ventas LY]
RETURN
    DIVIDE(VentasActual - VentasAnterior, VentasAnterior)
```

> Formatear `% Crecimiento Anual` como **porcentaje**:
> Herramientas de medida → Formato → %.
