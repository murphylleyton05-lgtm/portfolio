# Pipeline ETL — TechStore (Power BI · Power Query · M)

**Checkpoint:** Pipeline ETL desde datos crudos a modelo confiable
**Alumno:** Murphy, Lleyton
**Entregable final:** `Pipeline_ETL_Murphy_Lleyton.pbix`

Pipeline ETL que conecta Power BI al dataset de ventas de **TechStore**, perfila la
calidad de los datos, resuelve los problemas intencionales (duplicados, nulos y
tipos), aplica nomenclatura profesional `Dim_ / Fact_`, enriquece la tabla de
hechos con un **Merge** y documenta la lógica en **lenguaje M**.

> ⚠️ **Sobre el `.pbix`:** el `.pbix` es un binario que **solo genera Power BI
> Desktop** (Windows). Este repo entrega todo lo que el checkpoint evalúa —el
> dataset con los problemas, el **código M completo** de las 4 consultas y esta
> documentación— para que reproducir el `.pbix` sea pegar y aplicar. La guía
> paso a paso está en [Cómo reproducir el `.pbix`](#cómo-reproducir-el-pbix).

---

## Contenido del repo

```
pipeline-etl-techstore-powerbi/
├─ README.md                      ← este archivo (incluye justificaciones)
├─ data/
│  ├─ Pipeline_ETL_Dataset.xlsx   ← dataset con los problemas intencionales (celdas en amarillo)
│  └─ _build_dataset.py           ← script reproducible que genera el .xlsx
└─ power-query/                   ← código M de cada consulta (pegar en el Editor Avanzado)
   ├─ Dim_Clientes.m
   ├─ Dim_Productos.m
   ├─ Dim_Categorias.m
   └─ Fact_Ventas.m
```

## El dataset y sus problemas

| Hoja | Filas crudas | Problema intencional | Filas tras limpiar |
|------|:---:|------|:---:|
| `clientes`  | 12 | 1 duplicado (`id_cliente=3`) + 2 nulos (`email`, `ciudad`) | **11** |
| `productos` | 13 | 1 duplicado (`id_producto=103`) + 2 nulos (`precio`, `categoria`) | **12** |
| `ventas`    | 50 | limpia | **50** |
| `categorias`| 4  | limpia | **4** |

Las celdas problemáticas están **resaltadas en amarillo** dentro del `.xlsx`.

---

## Decisiones de limpieza (justificación técnica)

### `Dim_Clientes`
- **Duplicado** → `Table.Distinct` por **`id_cliente`** únicamente. Es una
  dimensión: su PK debe ser única o la relación 1:N con `Fact_Ventas` genera
  filas fantasma e infla los importes en el modelo.
- **`email` nulo (id 3) y `ciudad` nula (id 4)** → se **reemplazan por `"Sin dato"`**,
  no se eliminan. Ninguno de los dos campos participa de un cálculo de negocio, y
  borrar el cliente nos haría perder sus ventas asociadas por integridad
  referencial. Conservar la fila con un marcador explícito es lo correcto.

### `Dim_Productos`
- **Duplicado (`id_producto=103`)** → `Table.Distinct` por **`id_producto`**, por la
  PK y no por todas las columnas (no dependemos de que el resto de campos sean
  idénticos byte a byte).
- **`precio` nulo (id 107) — CRÍTICO** → se **imputa `0`**, no se elimina la fila.
  Razón: `Fact_Ventas` referencia ese `id_producto`; borrarlo rompería el Merge y
  la integridad referencial. Se usa `0` como **marcador visible**: deja el ingreso
  de ese producto en 0 (evidentemente incorrecto → se detecta en revisión) en
  lugar de inventar un importe plausible que contaminaría los KPIs. Queda marcado
  para corregir con el dueño del dato.
- **`categoria` nula (id 111)** → se etiqueta **`"Sin Categoria"`**. Así el producto
  sigue apareciendo en los cortes por categoría de forma explícita y auditable, en
  vez de desaparecer o quedar asignado a una categoría adivinada.

### `Fact_Ventas`
- **Tipado de `fecha_venta` como `Date`** → crítico para armar la línea de tiempo y
  relacionar con la tabla calendario del modelo (M8).
- **Merge (`LeftOuter`) contra `Dim_Productos` por `id_producto`** → se conservan
  **todas** las ventas aunque un producto faltara en la dimensión. Se expanden solo
  `nombre_producto` y `categoria`; el resto de columnas de la dimensión no se
  materializan para no duplicar datos que ya viven en `Dim_Productos`.

## Tipos de dato aplicados

| Columnas | Tipo |
|----------|------|
| IDs (`id_*`), `cantidad`, `stock`, `activo` | Whole Number (`Int64.Type`) |
| `fecha_venta`, `fecha_registro` | Date |
| `precio`, `costo`, `total_venta`, `descuento`, `precio_unitario` | Decimal Number (`type number`) |
| Nombres, `categoria`, `canal`, `email`, `ciudad`, `pais` | Text |

## Nomenclatura

| Hoja origen | Consulta final |
|-------------|----------------|
| `clientes`  | `Dim_Clientes` |
| `productos` | `Dim_Productos` |
| `categorias`| `Dim_Categorias` |
| `ventas`    | `Fact_Ventas` |

---

## Cómo reproducir el `.pbix`

1. **Conectar** — Power BI Desktop → *Inicio → Obtener datos → Excel* → elegí
   `data/Pipeline_ETL_Dataset.xlsx` → en el Navegador tildá las 4 hojas y hacé clic
   en **Transformar datos** (NO en *Cargar*).
2. **Perfilar** — *Vista* → activá *Calidad de columnas*, *Distribución de columnas*
   y *Perfil de columna* → cambiá a **“Todo el conjunto de datos”**. Confirmá los
   duplicados/nulos marcados en amarillo.
3. **Aplicar el M** — para cada consulta: *Inicio → Editor avanzado* → reemplazá el
   contenido por el `.m` correspondiente de `power-query/`. Renombrá las consultas a
   `Dim_Clientes`, `Dim_Productos`, `Dim_Categorias`, `Fact_Ventas`.
   - Los `.m` usan un parámetro **`RutaArchivo`** en vez de una ruta hardcodeada.
     Creá el parámetro: *Administrar parámetros → Nuevo → RutaArchivo (Texto)* con la
     ruta a tu `.xlsx`. (Alternativa: reemplazá `File.Contents(RutaArchivo)` por la
     ruta que Power BI genera al conectar.)
   - Cargá primero `Dim_Productos` (Fact_Ventas hace Merge contra ella).
4. **Validar** — sin íconos de error (triángulo amarillo). Conteo esperado:
   **Dim_Clientes 11 · Dim_Productos 12 · Fact_Ventas 50 · Dim_Categorias 4**.
5. **Cerrar y aplicar** — verificá que no aparezcan errores de carga.
6. **Guardar** como `Pipeline_ETL_Murphy_Lleyton.pbix` en esta misma carpeta y
   subilo al repo.

## Regenerar el dataset (opcional)

```bash
pip install openpyxl
python3 data/_build_dataset.py
```
Semilla fija → el `.xlsx` (mismos problemas y conteos) es 100 % reproducible.
