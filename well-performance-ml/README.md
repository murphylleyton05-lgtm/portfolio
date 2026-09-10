# 📈 Well Performance ML — ¿qué diseño de pozo rinde más?

Modelo de **machine learning** con datos **oficiales** de Vaca Muerta que predice el **EUR** de un pozo
(sus reservas estimadas) a partir del **diseño de fractura** — y, sobre todo, cuantifica cuánto del
rendimiento explica el diseño frente a la **geología**.

> **Datos oficiales de la Secretaría de Energía** (los parquets que procesa
> [`vaca-muerta-analytics`](../vaca-muerta-analytics)). El modelo se **regenera por CI** con los datos reales.

**🔗 Dashboard en vivo:** https://murphylleyton05-lgtm.github.io/portfolio/performance/

---

## La pregunta

En Vaca Muerta se discute cuánto rinde un pozo por su **completación** (rama, etapas, arena) vs. por **dónde
está** (la roca). Este proyecto lo pone en números:

- **Modelo A — solo diseño:** predice log(EUR) con rama, etapas, arena, agua e intensidad.
- **Modelo B — diseño + área:** agrega el área como proxy de la geología.

La diferencia de R² entre A y B es **el peso de la ubicación**. El hallazgo típico: el diseño explica una
parte, pero sumar la geología sube bastante el R² — *el diseño ayuda, pero la ubicación manda*.

## Cómo funciona

`scripts/construir_datos.py` lee `ajustes_declinacion.parquet`, se queda con los pozos de **ajuste
confiable**, entrena una **regresión lineal (ridge) sobre log(EUR)** implementada con numpy, separa
**train/test 70/30**, evalúa en el test (R² en espacio de EUR y MAPE), calcula la importancia de las
variables y arma el `datos.json`. `scripts/armar_web.py` arma el dashboard.

```bash
cd well-performance-ml
python3 scripts/construir_datos.py
python3 scripts/armar_web.py
```

Dependencias: **numpy**, **pandas** (+ pyarrow).

## Lo que **no** hace

- Las variables de diseño y producción son reales; el **EUR es una estimación** del ajuste de declinación, no un dato medido.
- El diseño explica solo una parte del EUR — y ese es el punto, no un defecto: el modelo lo cuantifica.
- **Correlación, no causalidad:** que la arena suba con el EUR no prueba que la cause (los buenos pozos se completan más agresivo).
- Modelo lineal, elegido por interpretable.

---

_Proyecto de portfolio · Lleyton Murphy · datos oficiales de la Secretaría de Energía._
