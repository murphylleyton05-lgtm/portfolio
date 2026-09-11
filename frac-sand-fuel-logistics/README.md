# 🏗️ Frac Sand & Fuel Logistics — Vaca Muerta

Cadena de suministro de **arena de fractura** hacia las locaciones de Vaca Muerta.

> **Consumo real · logística modelada.** El consumo —arena, agua y etapas por pozo— sale de los datos
> **oficiales de fractura** de la Secretaría de Energía (los mismos parquets que procesa
> [`vaca-muerta-analytics`](../vaca-muerta-analytics)). La capa logística (proveedores, entregas, stock,
> transporte, costo) se **modela** sobre ese consumo real, porque ninguna operadora publica su logística interna.

**🔗 Dashboard en vivo:** https://murphylleyton05-lgtm.github.io/portfolio/logistica/

---

## Qué es real y qué es modelo

| Real (dataset oficial) | Modelado (sobre lo real) |
|---|---|
| Arena bombeada por pozo (`arena_tn`) | Proveedores y su confiabilidad |
| Agua por pozo (`agua_m3`) | Entregas, lead time y demoras |
| Etapas por pozo (`etapas`) | Stock diario y política de reposición (s, S) |
| Mes de completación de cada pozo | Costo logístico (flete, demoras, standby) |
|  | Gasoil (estimado de las etapas reales) |

## Por qué importa

Un set de fractura consume **cientos de toneladas de arena por etapa**. Si la arena no llega, el equipo
se detiene y cada día parado cuesta más que semanas de logística. El cuello de botella de Vaca Muerta
muchas veces no es geológico: es **poner la arena en la locación a tiempo y a buen costo**.

## Cómo funciona

`scripts/construir_datos.py` lee `../vaca-muerta-analytics/data/procesado/ajustes_declinacion.parquet`,
arma la **demanda mensual real** de arena/agua/etapas y corre sobre ella una **política de reposición
(s, S)**: cuando el inventario cae por debajo del punto de reorden, se emite una orden que llega tras su
lead time (con demoras por proveedor), así que un envío demorado puede perforar el stock de seguridad o
quebrar. Después `scripts/armar_web.py` arma el dashboard.

En CI, el workflow **Actualizar Vaca Muerta** regenera este tablero con los datos oficiales.

```bash
cd frac-sand-fuel-logistics
python3 scripts/construir_datos.py   # consumo real + logística modelada -> datos.json
python3 scripts/armar_web.py
```

Dependencias: **pandas** (+ pyarrow) y la librería estándar.

## Lo que **no** hace

- La logística (proveedores, entregas, stock, costo) es un **modelo**, no datos de un ERP real: esa
  información no es pública. El consumo sí es real.
- El gasoil se **estima** a partir de las etapas reales (no está en el dataset).
- Modela un único yard consolidado, no transferencias entre depósitos.

---

_Proyecto de portfolio · Lleyton Murphy · consumo real (Secretaría de Energía) + logística modelada._
