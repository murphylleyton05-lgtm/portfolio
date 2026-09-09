# RetailPro — Análisis de ventas (SQL + IA en el flujo de trabajo)

**Proyecto:** RetailPro · Análisis de ventas sobre modelo estrella
**Alumno:** Murphy, Lleyton
**Pre-entrega:** IA en el flujo del proyecto — *Usando IA para documentar y optimizar el análisis*

Análisis de las ventas de RetailPro a partir de un **modelo estrella de 4 tablas**
(3 dimensiones + 1 tabla de hechos) consultado con SQL sobre SQLite. Este módulo
integra herramientas de IA como **co-piloto** para optimizar el código SQL,
generar insights y documentar el proyecto, manteniendo el **criterio analítico
propio como filtro de calidad**: ningún número de este repo aparece sin poder
rastrearse hasta su consulta de origen.

## Modelo de datos

| Tabla | Rol | Filas | PK |
|-------|-----|:---:|----|
| `dim_clientes`   | Dimensión | 11 | `id_cliente` |
| `dim_productos`  | Dimensión | 12 | `id_producto` |
| `dim_categorias` | Dimensión | 4  | `id_categoria` |
| `fact_ventas`    | Hechos    | 50 | `id_venta` |

`fact_ventas` se relaciona con las dimensiones por `id_cliente` e `id_producto`;
la categoría de cada producto vive en `dim_productos.categoria`.

## Estructura del repo

```
pre-entrega-ia-retailpro/
├─ README.md                          ← este archivo (Tarea 3, editado sobre el borrador de IA)
├─ Pre-entrega_IA_Murphy_Lleyton.docx ← entregable: las 4 tareas documentadas
└─ sql/
   ├─ consulta_base_m5.sql            ← JOIN de 4 tablas original (INNER JOIN)
   ├─ consulta_optimizada.sql         ← versión mejorada tras la revisión con IA
   └─ insights_m4.sql                 ← agregaciones que alimentan los insights
```

## Herramientas usadas

- **SQLite** — motor de consultas del proyecto.
- **SQL** — modelado en estrella, `JOIN`, agregaciones (`GROUP BY`, `SUM`, `AVG`).
- **IA (Claude.ai, versión gratuita)** — revisión del SQL, generación de insights
  y borrador de esta documentación. Todo lo generado con IA fue revisado y
  validado contra los datos reales antes de incorporarse.

## Cómo ejecutar los scripts SQL

Los scripts asumen las 4 tablas ya cargadas en una base SQLite
(`retailpro.db`). Para correrlos:

```bash
# Ejecutar la consulta base del modelo (detalle de ventas)
sqlite3 retailpro.db < sql/consulta_base_m5.sql

# Ejecutar la versión optimizada (no pierde ventas de categoría nula)
sqlite3 retailpro.db < sql/consulta_optimizada.sql

# Ejecutar las agregaciones de análisis (insights comerciales)
sqlite3 retailpro.db < sql/insights_m4.sql
```

## Nota de calidad de dato (criterio analítico)

El dataset trae problemas intencionales de las etapas de limpieza previas. Uno
impacta directamente en las consultas: **un producto quedó con la categoría nula**
(`"Sin Categoria"`). Por eso `consulta_base_m5.sql`, al usar `INNER JOIN` contra
`dim_categorias`, **descarta 2 de las 50 ventas** (USD 471,94; el 1,8 % del
ingreso). `consulta_optimizada.sql` lo corrige con `LEFT JOIN` + `COALESCE` para
preservar las 50 ventas. Es un recordatorio de que un `JOIN` mal elegido puede
sesgar un reporte sin lanzar ningún error.
