# 🏗️ Frac Sand & Fuel Logistics — Vaca Muerta

Dashboard de **cadena de suministro** para una operación de fractura hidráulica en Vaca Muerta:
el abastecimiento de **arena de fractura** (frac sand) y **gasoil** hacia las locaciones.

> **Data Analytics aplicado a Supply Chain.** Los datos son **simulados** con Python (semilla fija),
> pero la lógica de negocio es realista: demanda de los sets de fractura, política de reposición de
> inventario, lead time y demoras por proveedor, quiebres de stock y costo logístico.

**🔗 Dashboard en vivo:** https://murphylleyton05-lgtm.github.io/portfolio/logistica/

---

## Por qué importa

Un set de fractura consume **cientos de toneladas de arena por etapa** y no para de quemar gasoil.
Si la arena no llega, el equipo se detiene — y un día de *standby* cuesta más que semanas de logística.
El cuello de botella de Vaca Muerta no siempre es geológico: muchas veces es **poner la arena en la
locación a tiempo y a buen costo**. Este panel mide justamente eso.

## Qué mide

| Indicador | Qué responde |
|---|---|
| **OTIF** | ¿Qué % de envíos llegó a tiempo y completo? |
| **Lead time / retraso** | ¿Cuánto tarda un proveedor y cuánto se desvía? |
| **Stock de arena** | ¿Cuántos días de cobertura hay? ¿Cuándo se perfora el stock de seguridad? |
| **Días de quiebre** | ¿Cuántos días paró el equipo por falta de arena? |
| **Costo logístico** | ¿En qué se va la plata: material, flete, demoras, standby? |
| **Performance por proveedor** | ¿Quién es confiable y quién es caro? |

## Cómo funciona

1. **`scripts/simular.py`** genera los datos:
   - Demanda mensual de arena y gasoil a partir de la actividad de fractura (sets, etapas/día, estacionalidad).
   - El inventario de arena se modela con una **política de reposición (s, S)**: cuando el disponible + en
     tránsito cae por debajo del punto de reorden `s`, se emite una orden para reponer hasta el objetivo `S`.
     Las órdenes llegan tras su lead time (con demoras según el proveedor), así que **un envío demorado puede
     hacer perforar el stock de seguridad e incluso quebrar**. Así el stock, el OTIF y el costo salen de la
     misma realidad, no de números sueltos.
   - Deja los datos en **esquema estrella** (`data/dim_*.csv`, `data/fact_*.csv`) listos para modelar en
     Power BI, y un `web/datos.json` compacto para el dashboard.
2. **`scripts/armar_web.py`** inyecta ese JSON en la plantilla y arma `web/index.html`.

```bash
cd frac-sand-fuel-logistics
python3 scripts/simular.py     # genera CSVs + datos.json
python3 scripts/armar_web.py   # arma el dashboard
```

Sin dependencias: solo la librería estándar de Python.

## Modelo de datos (esquema estrella)

```
dim_proveedor ─┐
dim_pad ───────┤
dim_material ──┼─< fact_entregas   (un envío por fila: plan vs real, costo, estado)
dim_fecha ─────┘
               ├─< fact_stock      (stock diario de arena, consumo, recepción, quiebre)
               └─< fact_consumo    (demanda mensual de arena y gasoil)
```

## Lo que **no** hace

- Los datos son simulados, no salen de un ERP real.
- Modela un único yard consolidado (no transferencias entre depósitos).
- El costo de standby es una tarifa fija aproximada.
- Es diagnóstico, no prescriptivo: muestra el costo de las rutas pero no resuelve el ruteo óptimo.

---

_Proyecto de portfolio · Lleyton Murphy · datos simulados._
