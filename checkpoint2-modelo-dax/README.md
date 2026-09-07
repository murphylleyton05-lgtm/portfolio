# Checkpoint 2 — Modelo de datos con relaciones y medidas DAX (RetailPro / TechStore)

**Alumno:** Murphy, Lleyton
**Entregable:** `Murphy_Lleyton_Checkpoint2.pbix`
**Base:** continúa sobre `Pipeline_ETL_Murphy_Lleyton.pbix` del módulo anterior.

Transforma el `.pbix` limpio del checkpoint anterior en un **modelo analítico**:
esquema en estrella con relaciones 1:N activas, tabla calendario marcada como
tabla de fechas, y una tabla `_Medidas` con las 5 medidas DAX core.

> El `.pbix` se genera en Power BI Desktop. Este README + `medidas_dax.md`
> contienen todo el código y la configuración para reproducirlo.

## 1. Relaciones (esquema en estrella)

| Dimensión (lado 1) | Columna | → | Hechos (lado N) | Columna |
|---|---|---|---|---|
| Dim_Clientes | `id_cliente` | → | Fact_Ventas | `id_cliente` |
| Dim_Productos | `id_producto` | → | Fact_Ventas | `id_producto` |
| Dim_Categorias | `nombre_categoria` | → | Dim_Productos | `categoria` |
| Dim_Fechas | `Date` | → | Fact_Ventas | `fecha_venta` |

Todas: **cardinalidad 1:N**, **dirección de filtro única**, **activas**.

> ⚠️ Nota sobre `Dim_Categorias`: en este modelo `Dim_Productos` guarda la
> categoría como **texto** (`categoria`), no como `id_categoria`. Por eso la
> relación se hace `Dim_Categorias[nombre_categoria] → Dim_Productos[categoria]`.
> Es una relación 1:N válida y cumple el esquema en estrella igual.

## 2. Tabla calendario `Dim_Fechas`

Creada con DAX (`Nueva tabla`) e incluye las columnas de tiempo. Se marca como
**tabla de fechas** sobre la columna `Date` — obligatorio para que `TOTALYTD` y
`SAMEPERIODLASTYEAR` funcionen. Ver `medidas_dax.md`.

## 3. Tabla `_Medidas`

Tabla vacía (`Especificar datos`) sin columnas → ícono de calculadora 🧮.
Contiene las 5 medidas core.

## 4. Librería de medidas (5)

| Medida | Técnica |
|---|---|
| `Total Ventas` | Agregación básica (SUM) |
| `Ventas Online` | CALCULATE con filtro |
| `Ventas YTD` | Inteligencia de tiempo (TOTALYTD) |
| `Ventas LY` | Inteligencia de tiempo (SAMEPERIODLASTYEAR) |
| `% Crecimiento Anual` | VAR + DIVIDE (optimizada, sin división directa) |

Código completo en [`medidas_dax.md`](./medidas_dax.md).

## 5. Validación

Página `Validación` con una matriz: filas `Mes Nombre`, columnas `Año`, valores
`Total Ventas`, `Ventas YTD`, `Ventas LY`, `% Crecimiento Anual`.
Se verifica que YTD acumule mes a mes, que `Ventas LY` en 2024 muestre 2023 y en
2023 dé BLANK, y que `% Crecimiento` quede formateado como porcentaje.
