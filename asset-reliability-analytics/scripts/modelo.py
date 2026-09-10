#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo predictivo de falla para el tablero de confiabilidad.

Entrena una REGRESION LOGISTICA (implementada a mano con numpy, sin sklearn)
para estimar la probabilidad de que cada activo falle en los proximos 30 dias,
a partir de sus variables de condicion (horas, vibracion, temperatura, dias
desde el ultimo mantenimiento, fallas previas, etc.).

Flujo honesto de data science:
  1. separa train/test (70/30);
  2. estandariza con la media/desvio del TRAIN;
  3. entrena por descenso de gradiente con regularizacion L2;
  4. evalua en el test que el modelo no vio (AUC, accuracy, matriz de confusion);
  5. con el modelo entrenado, scorea TODA la flota y arma una watchlist.

Agrega el bloque "modelo" a web/datos.json (que ya trae la parte descriptiva).
"""
import csv
import json
import numpy as np
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"; WEB = RAIZ / "web"

FEATS = ["horas_operacion", "edad_meses", "ciclos_arranque", "vibracion_mm_s",
         "temp_prom_c", "dias_desde_mant", "carga_prom_pct", "fallas_previas"]
ETIQ = {"horas_operacion": "Horas de operación", "edad_meses": "Edad (meses)",
        "ciclos_arranque": "Ciclos de arranque", "vibracion_mm_s": "Vibración (mm/s)",
        "temp_prom_c": "Temperatura (°C)", "dias_desde_mant": "Días desde mantenimiento",
        "carga_prom_pct": "Carga promedio (%)", "fallas_previas": "Fallas previas"}

# ----------------------------------------------------------------------------
# Carga
# ----------------------------------------------------------------------------
filas = list(csv.DictReader(open(DATA / "features.csv", encoding="utf-8")))
X = np.array([[float(r[f]) for f in FEATS] for r in filas])
y = np.array([int(r["fallo_30d"]) for r in filas])
n = len(filas)

rng = np.random.default_rng(3)
idx = rng.permutation(n)
corte = int(n * 0.7)
tr, te = idx[:corte], idx[corte:]

mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
Ztr, Zte, Zall = (X[tr] - mu) / sd, (X[te] - mu) / sd, (X - mu) / sd

# ----------------------------------------------------------------------------
# Regresion logistica por descenso de gradiente (con L2)
# ----------------------------------------------------------------------------
def sigmoid(z): return 1 / (1 + np.exp(-z))

def entrenar(Z, yv, lr=0.15, epocas=4000, l2=0.5):
    w = np.zeros(Z.shape[1]); b = 0.0
    m = len(yv)
    for _ in range(epocas):
        p = sigmoid(Z @ w + b)
        err = p - yv
        gw = Z.T @ err / m + l2 * w / m
        gb = err.mean()
        w -= lr * gw; b -= lr * gb
    return w, b

w, b = entrenar(Ztr, y[tr])

# ----------------------------------------------------------------------------
# Evaluacion en el test
# ----------------------------------------------------------------------------
p_te = sigmoid(Zte @ w + b)
pred_te = (p_te >= 0.5).astype(int)
yte = y[te]

def auc(y_true, scores):
    pos = scores[y_true == 1]; neg = scores[y_true == 0]
    if len(pos) == 0 or len(neg) == 0: return float("nan")
    # Mann-Whitney U (con empates a 0.5)
    ganes = 0.0
    for s in pos:
        ganes += (neg < s).sum() + 0.5 * (neg == s).sum()
    return ganes / (len(pos) * len(neg))

tp = int(((pred_te == 1) & (yte == 1)).sum())
tn = int(((pred_te == 0) & (yte == 0)).sum())
fp = int(((pred_te == 1) & (yte == 0)).sum())
fn = int(((pred_te == 0) & (yte == 1)).sum())
acc = (tp + tn) / len(yte)
prec = tp / (tp + fp) if (tp + fp) else 0
rec = tp / (tp + fn) if (tp + fn) else 0
auc_te = auc(yte, p_te)

# ----------------------------------------------------------------------------
# Importancia de variables (coeficientes estandarizados) y scoring de la flota
# ----------------------------------------------------------------------------
pesos = sorted([{"feature": f, "etiqueta": ETIQ[f], "peso": round(float(w[i]), 3)}
                for i, f in enumerate(FEATS)], key=lambda d: abs(d["peso"]), reverse=True)

p_all = sigmoid(Zall @ w + b)
riesgo = []
for i, r in enumerate(filas):
    riesgo.append({
        "activo_id": r["activo_id"], "tipo": r["tipo"], "criticidad": r["criticidad"],
        "prob": round(float(p_all[i]), 3),
        "vibracion": float(r["vibracion_mm_s"]), "temp": float(r["temp_prom_c"]),
        "horas": int(float(r["horas_operacion"])), "dias_mant": int(float(r["dias_desde_mant"])),
        "fallas_previas": int(float(r["fallas_previas"])),
    })
riesgo.sort(key=lambda d: d["prob"], reverse=True)
watchlist = riesgo[:12]
# puntos para el scatter (vibracion vs horas, color = prob)
scatter = [{"x": d["horas"], "y": d["vibracion"], "p": d["prob"], "crit": d["criticidad"]} for d in riesgo]

modelo = {
    "modelo": "Regresión logística (numpy, sin sklearn)",
    "n_train": len(tr), "n_test": len(te),
    "base_rate": round(float(y.mean()), 3),
    "auc": round(float(auc_te), 3), "accuracy": round(float(acc), 3),
    "precision": round(float(prec), 3), "recall": round(float(rec), 3),
    "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    "pesos": pesos, "watchlist": watchlist, "scatter": scatter,
    "en_riesgo_alto": int((p_all >= 0.5).sum()),
}

datos = json.load(open(WEB / "datos.json", encoding="utf-8"))
datos["modelo"] = modelo
json.dump(datos, open(WEB / "datos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

print("OK modelo")
print(f"  train/test: {len(tr)}/{len(te)}  base rate: {y.mean()*100:.0f}%")
print(f"  AUC: {auc_te:.3f}  accuracy: {acc:.3f}  precision: {prec:.3f}  recall: {rec:.3f}")
print(f"  confusion  TP {tp} TN {tn} FP {fp} FN {fn}")
print(f"  top variable: {pesos[0]['etiqueta']} (peso {pesos[0]['peso']})")
print(f"  activos con prob>=0.5: {modelo['en_riesgo_alto']}")
