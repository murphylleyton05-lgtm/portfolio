#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Well Performance ML — ¿qué diseño de completación rinde más?

Con datos REALES de la Secretaría de Energía, entrena un modelo que predice el
EUR (reservas estimadas de un pozo) a partir de su DISEÑO DE FRACTURA:
longitud de rama, etapas, arena bombeada, agua e intensidad. La idea es separar
cuánto del rendimiento explica el diseño (lo que una operadora controla) y qué
palanca mueve más la aguja.

Modelo: regresión lineal (ridge) sobre log(EUR), implementada con numpy.
Flujo honesto: train/test 70/30, estandarización con el train, evaluación en el
test que el modelo no vio (R², MAPE), importancia de variables, predicho vs real.

Fuente: vaca-muerta-analytics/data/procesado/ajustes_declinacion.parquet
Local usa la versión demo (mismo esquema); en CI son los datos reales.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"; WEB.mkdir(exist_ok=True)
PROC = RAIZ.parent / "vaca-muerta-analytics" / "data" / "procesado"
BBL_M3 = 6.28981

if not (PROC / "ajustes_declinacion.parquet").exists():
    raise SystemExit(f"No encuentro {PROC}/ajustes_declinacion.parquet (corré el pipeline).")

aj = pd.read_parquet(PROC / "ajustes_declinacion.parquet")
meta_src = json.load(open(PROC / "metadatos.json", encoding="utf-8")) if (PROC / "metadatos.json").exists() else {}
es_demo = bool(meta_src.get("es_demo", True))

# Solo pozos con ajuste confiable (EUR con sentido) y con fractura declarada.
df = aj[(aj["ajuste_confiable"] == True) & (aj["tiene_fractura"] == True)].copy()
df = df[df["eur"] > 0]
df["eur_bbl"] = df["eur"] * BBL_M3
df["es_volatil"] = (df["ventana_fluido"] == "Petroleo volatil").astype(float)

FEATS = ["rama_m", "etapas", "arena_tn", "agua_m3", "arena_por_metro", "es_volatil"]
ETIQ = {"rama_m": "Longitud de rama (m)", "etapas": "Etapas", "arena_tn": "Arena total (t)",
        "agua_m3": "Agua (m³)", "arena_por_metro": "Arena por metro (t/m)", "es_volatil": "Ventana volátil"}

X = df[FEATS].to_numpy(dtype=float)
y = np.log(df["eur_bbl"].to_numpy(dtype=float))   # log para domar la asimetría
n = len(df)

rng = np.random.default_rng(5)
idx = rng.permutation(n)
corte = int(n * 0.7)
tr, te = idx[:corte], idx[corte:]

mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
Ztr, Zte, Zall = (X[tr] - mu) / sd, (X[te] - mu) / sd, (X - mu) / sd

# Ridge por ecuación normal: w = (Z'Z + λI)^-1 Z'y  (con intercepto aparte)
def entrenar(Z, yv, lam=1.0):
    Zi = np.hstack([np.ones((len(Z), 1)), Z])
    R = lam * np.eye(Zi.shape[1]); R[0, 0] = 0.0  # no penalizar el intercepto
    w = np.linalg.solve(Zi.T @ Zi + R, Zi.T @ yv)
    return w  # w[0] = intercepto

def r2_eur(Ztr_, Zte_, lam=1.0):
    """Entrena en train, evalúa R² (espacio EUR) y MAPE en test. Devuelve (r2, mape, pred_te)."""
    ww = entrenar(Ztr_, y[tr], lam)
    pred_log = np.hstack([np.ones((len(Zte_), 1)), Zte_]) @ ww
    real, pred = np.exp(y[te]), np.exp(pred_log)
    r2_ = 1 - np.sum((real - pred) ** 2) / np.sum((real - real.mean()) ** 2)
    mape_ = float(np.mean(np.abs((real - pred) / real)) * 100)
    return float(r2_), mape_, pred

# --- Modelo A: SOLO DISEÑO ---
w = entrenar(Ztr, y[tr])
r2, mape, _ = r2_eur(Ztr, Zte)
pred_te_log = np.hstack([np.ones((len(Zte), 1)), Zte]) @ w
ss_res_l = np.sum((y[te] - pred_te_log) ** 2); ss_tot_l = np.sum((y[te] - y[te].mean()) ** 2)
r2_log = 1 - ss_res_l / ss_tot_l

# --- Modelo B: DISEÑO + ÁREA (proxy de geología) ---
areas = pd.get_dummies(df["area"], prefix="area").to_numpy(dtype=float)
Xb = np.hstack([X, areas])
mub, sdb = Xb[tr].mean(0), Xb[tr].std(0) + 1e-9
Zbtr, Zbte = (Xb[tr] - mub) / sdb, (Xb[te] - mub) / sdb
r2_b, mape_b, pred_te_b = r2_eur(Zbtr, Zbte, lam=2.0)
real_te = np.exp(y[te]); pred_te = pred_te_b   # el mejor modelo para predicho-vs-real
# cuánto del "gap a explicar" agrega la geología
aporte_geo = round(max(0.0, r2_b - r2), 3)

# Importancia = coeficientes estandarizados (sin el intercepto)
coefs = sorted([{"feature": f, "etiqueta": ETIQ[f], "peso": round(float(w[i + 1]), 3)}
                for i, f in enumerate(FEATS)], key=lambda d: abs(d["peso"]), reverse=True)

# Predicho vs real (test) en Mbbl
pvr = [{"real": round(float(r) / 1000, 0), "pred": round(float(p) / 1000, 0)}
       for r, p in zip(real_te, pred_te)]

# Dispersión EUR vs rama y vs arena (todos los pozos, color por ventana)
def scatter(campo):
    return [{"x": round(float(r[campo]), 0), "y": round(float(r["eur_bbl"]) / 1000, 0),
             "vol": int(r["es_volatil"])} for _, r in df.iterrows()]

# EUR por ventana (mediana real)
vent = df.groupby("ventana_fluido")["eur_bbl"].median().sort_values(ascending=False)
vent_rows = [{"ventana": k, "eur_mbbl": round(v / 1000, 0), "n": int((df["ventana_fluido"] == k).sum())}
             for k, v in vent.items()]

# Top pozos por EUR
top = df.sort_values("eur_bbl", ascending=False).head(12)
top_rows = [{"pozo": r.sigla, "operador": r.empresa, "ventana": r.ventana_fluido,
             "rama_m": round(r.rama_m), "etapas": int(r.etapas), "arena_tn": round(r.arena_tn),
             "eur_mbbl": round(r.eur_bbl / 1000, 0)} for r in top.itertuples()]

datos = {
    "meta": {"generado": meta_src.get("generado_en", "")[:10], "es_demo": es_demo,
             "pozos": n, "n_train": len(tr), "n_test": len(te)},
    "kpis": {"pozos": n, "eur_mediano_mbbl": round(float(df["eur_bbl"].median()) / 1000, 0),
             "r2": round(float(r2), 3), "r2_geo": round(float(r2_b), 3), "aporte_geo": aporte_geo,
             "mape": round(mape_b, 1), "top_driver": coefs[0]["etiqueta"]},
    "modelo": {"modelo": "Regresión lineal (ridge) sobre log(EUR), numpy",
               "r2_diseno": round(float(r2), 3), "r2_geo": round(float(r2_b), 3),
               "r2_log": round(float(r2_log), 3), "mape": round(mape_b, 1), "aporte_geo": aporte_geo,
               "coefs": coefs, "pred_vs_real": pvr},
    "scatter_rama": scatter("rama_m"),
    "scatter_arena": scatter("arena_tn"),
    "ventanas": vent_rows,
    "top": top_rows,
}
json.dump(datos, open(WEB / "datos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

fuente = "DEMO" if es_demo else "oficiales (Secretaría de Energía)"
print("OK well-performance-ml")
print(f"  fuente: {fuente}  pozos confiables: {n}  train/test: {len(tr)}/{len(te)}")
print(f"  EUR mediano: {datos['kpis']['eur_mediano_mbbl']:.0f} Mbbl")
print(f"  R² (EUR): {r2:.3f}  R² (log): {r2_log:.3f}  MAPE: {mape:.1f}%")
print(f"  driver principal: {coefs[0]['etiqueta']} (peso {coefs[0]['peso']})")
