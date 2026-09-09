# Modelo de datos con relaciones + medidas DAX — TechStore (Power BI)

**Checkpoint:** M8 · Modelo de datos con relaciones activas y tabla de medidas core en DAX
**Alumno:** Murphy, Lleyton
**Entregable final:** `Murphy_Lleyton_Checkpoint2.pbix`

Este checkpoint le da **inteligencia analítica** al `.pbix` que quedó del módulo
anterior ([`../pipeline-etl-techstore-powerbi`](../pipeline-etl-techstore-powerbi)):
crea las **relaciones 1:N** del esquema en estrella, la **tabla calendario**
`Dim_Fechas` y las **5 medidas DAX core** que van a alimentar todos los reportes
del proyecto integrador (M11).

> ⚠️ **Sobre el `.pbix`:** el `.pbix` es un binario que **solo genera Power BI
> Desktop** (Windows). Este repo entrega todo lo que el checkpoint evalúa —el
> **código DAX completo** (calendario, columnas y las 5 medidas), el diagrama del
> modelo y las relaciones documentadas, y la matriz de validación esperada— para
> que armar el `.pbix` sea **pegar y aplicar**. La guía está en
> [Cómo reproducir el `.pbix`](#cómo-reproducir-el-pbix).

---

## Contenido del repo

```
modelo-datos-dax-techstore-powerbi/
├─ README.md                        ← este archivo
├─ Murphy_Lleyton_Checkpoint2.pbix  ← se genera en Power BI Desktop (ver guía)
└─ dax/
   ├─ 01_Dim_Fechas.dax             ← tabla calendario (CALENDAR / CALENDARAUTO)
   ├─ 02_Dim_Fechas_columnas.dax    ← columnas: Año, Mes Número, Mes Nombre, Trimestre, Semana
   └─ 03_Medidas_Core.dax           ← _Medidas + las 5 medidas DAX
```

Punto de partida: `../pipeline-etl-techstore-powerbi/Pipeline_ETL_Murphy_Lleyton.pbix`
(tablas ya limpias con Power Query). El dataset origen es
`../pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx`.

---

## Esquema en estrella

Cuatro dimensiones alrededor de la tabla de hechos `Fact_Ventas`. `Dim_Categorias`
cuelga de `Dim_Productos` (rama snowflake), tal como pide la cadena de relaciones
del checkpoint.

```mermaid
erDiagram
    Dim_Clientes   ||--o{ Fact_Ventas   : "id_cliente (1:N)"
    Dim_Productos  ||--o{ Fact_Ventas   : "id_producto (1:N)"
    Dim_Fechas     ||--o{ Fact_Ventas   : "Date -> fecha_venta (1:N)"
    Dim_Categorias ||--o{ Dim_Productos : "nombre_categoria -> categoria (1:N)"

    Fact_Ventas {
        int    id_venta
        date   fecha_venta
        int    id_cliente
        int    id_producto
        int    cantidad
        number precio_unitario
        number descuento
        number total_venta
        text   canal
        text   nombre_producto
        text   categoria
    }
    Dim_Clientes {
        int  id_cliente PK
        text nombre_cliente
        text email
        text ciudad
        text pais
        date fecha_registro
        text canal
    }
    Dim_Productos {
        int    id_producto PK
        text   nombre_producto
        text   categoria
        number precio
        number costo
        int    stock
        int    activo
    }
    Dim_Categorias {
        int  id_categoria PK
        text nombre_categoria
    }
    Dim_Fechas {
        date Date PK
        int  Año
        int  "Mes Número"
        text "Mes Nombre"
        text Trimestre
        int  Semana
    }
```

### Relaciones a configurar

| Tabla dimensión (lado 1) | Columna            | → | Tabla destino (lado N) | Columna       | Cardinalidad | Dirección | Estado |
|--------------------------|--------------------|---|------------------------|---------------|:------------:|:---------:|:------:|
| `Dim_Clientes`           | `id_cliente`       | → | `Fact_Ventas`          | `id_cliente`  | 1:N          | Única     | Activa |
| `Dim_Productos`          | `id_producto`      | → | `Fact_Ventas`          | `id_producto` | 1:N          | Única     | Activa |
| `Dim_Fechas`             | `Date`             | → | `Fact_Ventas`          | `fecha_venta` | 1:N          | Única     | Activa |
| `Dim_Categorias`         | `nombre_categoria` | → | `Dim_Productos`        | `categoria`   | 1:N          | Única     | Activa |

Todas las relaciones: **cardinalidad 1:N**, **dirección de filtro única**
(de la dimensión hacia los hechos) y **activas** (línea continua). Sin
bidireccionales — generan ambigüedad en las medidas DAX.

> **⚠️ Desviación justificada respecto de la consigna (categorías).**
> La consigna genérica sugiere relacionar `Dim_Categorias[id_categoria]` con una
> supuesta `Dim_Productos[id_categoria]`. En **este** dataset de TechStore
> (el que venís arrastrando desde M3/M6) `Dim_Productos` **no** tiene la FK
> `id_categoria`: tiene el **texto** `categoria`. La relación fiel al dato real
> es entonces `Dim_Categorias[nombre_categoria] (1) → Dim_Productos[categoria] (N)`.
> Sigue siendo una relación 1:N de dirección única y respeta la cadena
> `Categorías → Productos → Ventas`. El producto con `categoria = "Sin Categoria"`
> (imputado en M6 por un nulo) simplemente no matchea ninguna fila de
> `Dim_Categorias`, lo cual es correcto y auditable.
>
> *Alternativa "por el libro":* agregar una columna `id_categoria` a
> `Dim_Productos` con un `LOOKUPVALUE`/merge contra `Dim_Categorias` y relacionar
> por ese entero. Se documenta la opción pero se entrega la relación por
> `nombre_categoria` para no inventar datos que el pipeline de M6 no produjo.

---

## Tabla calendario `Dim_Fechas`

Se crea con DAX (`dax/01_Dim_Fechas.dax`) tomando el rango de `Fact_Ventas[fecha_venta]`:

```dax
Dim_Fechas =
CALENDAR (
    MIN ( Fact_Ventas[fecha_venta] ),
    MAX ( Fact_Ventas[fecha_venta] )
)
```

Columnas calculadas (`dax/02_Dim_Fechas_columnas.dax`): `Año`, `Mes Número`,
`Mes Nombre`, `Trimestre`, `Semana`.

**Paso obligatorio:** clic derecho sobre `Dim_Fechas` → **Marcar como tabla de
fechas** → columna `Date`. Sin esto, `TOTALYTD` y `SAMEPERIODLASTYEAR` no
funcionan aunque la fórmula sea correcta.

---

## Tabla de medidas `_Medidas`

Contenedor **sin columnas de datos** (ícono de calculadora). Se crea con
*Especificar datos* → nombre `_Medidas` → *Cargar*, y luego se **elimina la
"Columna 1"** por defecto. El prefijo `_` la deja primera en el panel.

## Las 5 medidas core (`dax/03_Medidas_Core.dax`)

| # | Medida               | Técnica que demuestra                         |
|---|----------------------|-----------------------------------------------|
| 1 | `Total Ventas`       | Agregación básica (`SUM`)                      |
| 2 | `Ventas Online`      | `CALCULATE` + filtro (`canal = "Online"`)      |
| 3 | `Ventas YTD`         | Inteligencia de tiempo (`TOTALYTD`)            |
| 4 | `Ventas LY`          | Comparativa anual (`SAMEPERIODLASTYEAR`)       |
| 5 | `% Crecimiento Anual`| Optimización con `VAR` + `DIVIDE`              |

```dax
Total Ventas = SUM ( Fact_Ventas[total_venta] )

Ventas Online =
CALCULATE ( [Total Ventas], Fact_Ventas[canal] = "Online" )

Ventas YTD =
TOTALYTD ( [Total Ventas], Dim_Fechas[Date] )

Ventas LY =
CALCULATE ( [Total Ventas], SAMEPERIODLASTYEAR ( Dim_Fechas[Date] ) )

% Crecimiento Anual =
VAR VentasActual   = [Total Ventas]
VAR VentasAnterior = [Ventas LY]
RETURN
    DIVIDE ( VentasActual - VentasAnterior, VentasAnterior )
```

`% Crecimiento Anual` se formatea como **porcentaje** (Herramientas de medida →
Formato → %). La Medida 5 usa `VAR` para calcular `[Ventas LY]` **una sola vez**
y `DIVIDE` para evitar la división por cero (nunca la barra `/`).

---

## Validación con matriz

Página **Validación** con una **Matriz**:

- **Filas:** `Dim_Fechas[Mes Nombre]`
- **Columnas:** `Dim_Fechas[Año]`
- **Valores:** `Total Ventas`, `Ventas YTD`, `Ventas LY`, `% Crecimiento Anual`

| Qué verificar                | Resultado esperado                          |
|------------------------------|---------------------------------------------|
| `Ventas YTD` en enero        | Igual a `Total Ventas` de enero             |
| `Ventas YTD` en febrero      | Acumulado enero + febrero                   |
| `Ventas LY` en 2024          | Muestra los valores de 2023                 |
| `Ventas LY` en 2023          | `BLANK` (no hay año anterior)               |
| `% Crecimiento Anual` en 2024| Positivo o negativo según los datos         |

---

## Cómo reproducir el `.pbix`

1. **Abrir el punto de partida** — abrí en Power BI Desktop el
   `Pipeline_ETL_Murphy_Lleyton.pbix` del módulo anterior. Ya trae
   `Dim_Clientes`, `Dim_Productos`, `Dim_Categorias` y `Fact_Ventas` limpias.
   *(Si no lo tenés, reconstruilo con la guía de `../pipeline-etl-techstore-powerbi/README.md`.)*
2. **Crear el calendario** — *Inicio → Nueva tabla* → pegá el contenido de
   `dax/01_Dim_Fechas.dax`. Luego agregá las 5 columnas de
   `dax/02_Dim_Fechas_columnas.dax` (*Nueva columna*, una por vez).
3. **Marcar como tabla de fechas** — clic derecho en `Dim_Fechas` → *Marcar como
   tabla de fechas* → columna `Date`. **No te saltees este paso.**
4. **Armar las relaciones** — *Vista de Modelo* → arrastrá las columnas según la
   [tabla de relaciones](#relaciones-a-configurar). Para cada una verificá
   **1:N**, **dirección única** y **activa** (doble clic en la línea para revisar).
5. **Crear `_Medidas`** — *Inicio → Especificar datos* → nombre `_Medidas` →
   *Cargar* → eliminá la *Columna 1*. Debe quedar con ícono de calculadora.
6. **Escribir las medidas** — clic derecho en `_Medidas` → *Nueva medida* → pegá
   una por una las 5 de `dax/03_Medidas_Core.dax`. Formateá
   `% Crecimiento Anual` como `%`.
7. **Validar** — creá la página *Validación* con la matriz y comprobá la tabla
   de [validación](#validación-con-matriz).
8. **Guardar** como `Murphy_Lleyton_Checkpoint2.pbix` en esta carpeta y subilo al repo.

---

## ⚠️ Errores comunes a evitar

- **No marcar `Dim_Fechas` como tabla de fechas** → `TOTALYTD` y
  `SAMEPERIODLASTYEAR` devuelven resultados incorrectos o vacíos.
- **Relación bidireccional** → ambigüedad en las medidas. Usar siempre dirección
  única (dimensión → hechos).
- **Dejar la "Columna 1" en `_Medidas`** → la tabla no toma el ícono de
  calculadora y las medidas quedan colgando de una tabla de datos.
- **Usar `/` en vez de `DIVIDE`** → error de división por cero cuando
  `Ventas LY` es `BLANK`.
- **No usar `VAR` en la Medida 5** → recalcularía `[Ventas LY]` dos veces; el
  objetivo del ejercicio es practicar la optimización con variables.
- **`% Crecimiento` sin formato de porcentaje** → aparece `0,15` en lugar de `15 %`.
