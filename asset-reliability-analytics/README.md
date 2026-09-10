# ⚙️ Asset Reliability Analytics — Vaca Muerta

Tablero de **confiabilidad de activos rotativos** (bombas y compresores) de una operación de Vaca Muerta,
con un **modelo predictivo** que estima qué equipo va a fallar en los próximos 30 días.

> **Data Analytics aplicado a Asset Reliability.** No es un análisis RCM/FMEA de ingeniería de confiabilidad:
> es analítica de datos sobre el problema. Los datos son **simulados** con Python (numpy, semilla fija).

**🔗 Dashboard en vivo:** https://murphylleyton05-lgtm.github.io/portfolio/confiabilidad/

---

## Qué mide

| Indicador | Qué responde |
|---|---|
| **Disponibilidad** | ¿Qué % de las horas programadas el equipo estuvo disponible? |
| **MTBF** | Horas de operación promedio entre fallas. |
| **MTTR** | Horas promedio para reparar (incluye espera de repuestos). |
| **Downtime / Fallas / Costo** | Tiempo perdido, cantidad de eventos y costo de mantenimiento. |
| **Pareto de modos de falla** | Qué pocos modos explican la mayoría de las fallas. |
| **Probabilidad de falla** | Modelo: qué activo intervenir primero. |

## El modelo predictivo

`scripts/modelo.py` entrena una **regresión logística implementada a mano con numpy** (sin sklearn) para
estimar la probabilidad de falla en 30 días a partir de las variables de condición de cada activo
(horas, edad, vibración, temperatura, días desde el último mantenimiento, fallas previas, etc.).

Flujo honesto de data science:

1. separa **train/test (70/30)**;
2. estandariza con la media/desvío del *train*;
3. entrena por descenso de gradiente con regularización L2;
4. **evalúa en el test que el modelo no vio** — AUC, accuracy, precision, recall, matriz de confusión;
5. scorea toda la flota y arma una **watchlist** ordenada por riesgo.

En la última corrida: **AUC ≈ 0,92**, accuracy ≈ 91%. La variable que más pesa es la **vibración**, seguida de
la temperatura y los días desde el último mantenimiento — lo esperable en equipos rotativos.

## Cómo funciona

```bash
cd asset-reliability-analytics
python3 scripts/simular.py    # flota + eventos + features (CSVs + datos.json)
python3 scripts/modelo.py     # entrena el modelo y agrega su resultado al JSON
python3 scripts/armar_web.py  # arma el dashboard
```

Dependencias: **numpy** y la librería estándar. Sin sklearn (la regresión está escrita a mano, y se ve).

## Modelo de datos (esquema estrella)

```
dim_activo  ─< fact_eventos   (una falla por fila: modo, downtime, costo, criticidad)
features.csv                  (variables de condición + etiqueta fallo_30d, para el modelo)
```

## Lo que **no** hace

- Es Data Analytics aplicado a confiabilidad, **no** ingeniería de confiabilidad (RCM/FMEA).
- Los datos son simulados; la etiqueta de falla se construyó a partir de las variables (señal real, sintética).
- El modelo es simple y transparente a propósito (interpretable > potente), no series de sensores en alta frecuencia.
- Predice riesgo, no la causa raíz: dice qué activo mirar primero.

---

_Proyecto de portfolio · Lleyton Murphy · datos simulados._
