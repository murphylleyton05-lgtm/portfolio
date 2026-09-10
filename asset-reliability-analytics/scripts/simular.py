#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simula una flota de equipos rotativos (bombas y compresores) de una operacion
de Vaca Muerta y su historial de fallas / reparaciones, para un tablero de
CONFIABILIDAD DE ACTIVOS (Asset Reliability).

Genera datos SINTETICOS con logica realista:
  - una flota de activos con sus caracteristicas (horas, edad, vibracion, etc.);
  - un historial de eventos de falla (modo, downtime, costo) durante 24 meses;
  - una etiqueta "fallo en los proximos 30 dias" que depende de las variables
    del activo, para que el modelo predictivo (modelo.py) tenga senal real que
    aprender.

Deja:
  data/*.csv     -> esquema estrella (dim_/fact_) + features.csv para el modelo
  web/datos.json -> KPIs y series descriptivas (el modelo se agrega en modelo.py)

Determinista (semilla fija). Usa solo numpy + libreria estandar.
"""
import csv
import json
import numpy as np
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"; WEB = RAIZ / "web"
DATA.mkdir(exist_ok=True); WEB.mkdir(exist_ok=True)

rng = np.random.default_rng(7)

HOY = date(2026, 9, 1)
MESES = 24
INICIO = date(2024, 9, 1)
DIAS_PERIODO = (HOY - INICIO).days
HORAS_PERIODO = DIAS_PERIODO * 24

def clave_mes(d): return f"{d.year:04d}-{d.month:02d}"
def meses_lista():
    y, m, out = 2024, 9, []
    for _ in range(MESES):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13: m = 1; y += 1
    return out
MESES_K = meses_lista()

# ----------------------------------------------------------------------------
# Tipos de activo (duty distinto -> confiabilidad distinta)
# ----------------------------------------------------------------------------
TIPOS = [
    # tipo, n, tasa_falla_rel, horas_mes, costo_falla_base, criticidad_base
    ("Bomba de fractura",   48, 1.7,  360, 42000, "Alta"),
    ("Bomba de inyeccion",  34, 0.9,  620, 18000, "Media"),
    ("Compresor de gas",    30, 1.1,  700, 65000, "Alta"),
    ("Bomba booster",       30, 0.7,  540, 12000, "Baja"),
]
UBIC = ["Loma Campana", "Bandurria Sur", "Fortin de Piedra", "El Trapial",
        "Aguada Pichana", "Rincon La Ceniza", "Bajada del Palo"]
MARCAS = {
    "Bomba de fractura": ["SPM", "Gardner Denver", "FMC"],
    "Bomba de inyeccion": ["Grundfos", "Flowserve", "Sulzer"],
    "Compresor de gas": ["Ariel", "Caterpillar", "Waukesha"],
    "Bomba booster": ["Goulds", "KSB", "Weir"],
}
MODOS = ["Sello mecanico", "Rodamiento", "Sobrecalentamiento", "Vibracion excesiva",
         "Falla electrica", "Fuga hidraulica", "Valvula", "Lubricacion"]
MODO_W = [0.20, 0.17, 0.14, 0.13, 0.11, 0.10, 0.08, 0.07]

# ----------------------------------------------------------------------------
# Generacion de la flota (features actuales de cada activo)
# ----------------------------------------------------------------------------
activos = []
aid = 0
for tipo, n, tasa, horas_mes, costo_base, crit_base in TIPOS:
    for _ in range(n):
        aid += 1
        edad_meses = int(rng.integers(6, 84))
        horas_op = round(edad_meses * horas_mes * rng.uniform(0.75, 1.05))
        ciclos = int(horas_op / rng.uniform(6, 24))
        # vibracion y temperatura crecen con horas/edad + ruido (senal para el modelo)
        vibracion = round(1.8 + horas_op / 9000 + rng.normal(0, 0.8), 2)
        vibracion = float(np.clip(vibracion, 0.8, 12))
        temp = round(58 + horas_op / 3000 + rng.normal(0, 6), 1)
        temp = float(np.clip(temp, 45, 115))
        dias_mant = int(np.clip(rng.exponential(38), 1, 210))
        carga = round(float(np.clip(rng.normal(72, 14), 30, 100)), 0)
        criticidad = crit_base if rng.random() < 0.8 else rng.choice(["Alta", "Media", "Baja"])
        activos.append({
            "activo_id": f"EQ-{aid:03d}", "tipo": tipo,
            "marca": str(rng.choice(MARCAS[tipo])),
            "ubicacion": str(rng.choice(UBIC)),
            "edad_meses": edad_meses, "horas_operacion": horas_op,
            "ciclos_arranque": ciclos, "vibracion_mm_s": vibracion,
            "temp_prom_c": temp, "dias_desde_mant": dias_mant,
            "carga_prom_pct": carga, "criticidad": criticidad,
            "tasa": tasa, "horas_mes": horas_mes, "costo_base": costo_base,
        })

# ----------------------------------------------------------------------------
# Historial de fallas durante el periodo (fact_eventos)
# ----------------------------------------------------------------------------
eventos = []
fid = 0
for a in activos:
    # numero esperado de fallas ~ tasa del tipo * factor de condicion
    cond = 1.0 + 0.6 * (a["vibracion_mm_s"] - 4) / 4 + 0.4 * (a["temp_prom_c"] - 75) / 20
    lam = max(0.4, a["tasa"] * (MESES / 12.0) * 1.9 * max(0.3, cond))
    n_fallas = int(rng.poisson(lam))
    a["fallas_previas"] = n_fallas
    for _ in range(n_fallas):
        fid += 1
        dia = int(rng.integers(0, DIAS_PERIODO))
        fecha = INICIO + timedelta(days=dia)
        modo = str(rng.choice(MODOS, p=MODO_W))
        # downtime segun modo. En una cuenca remota, muchas reparaciones esperan
        # repuestos: el tiempo de reparacion incluye esa logistica (por eso son largas).
        base_dt = {"Sello mecanico": 70, "Rodamiento": 120, "Sobrecalentamiento": 90,
                   "Vibracion excesiva": 100, "Falla electrica": 55, "Fuga hidraulica": 40,
                   "Valvula": 60, "Lubricacion": 22}[modo]
        downtime_h = round(float(np.clip(rng.gamma(2.2, base_dt / 2.2), 4, 420)), 1)
        costo = round(a["costo_base"] * rng.uniform(0.5, 1.8) + downtime_h * 400, 0)
        eventos.append({
            "evento_id": f"FL-{fid:04d}", "activo_id": a["activo_id"], "tipo": a["tipo"],
            "ubicacion": a["ubicacion"], "fecha": fecha.isoformat(), "mes": clave_mes(fecha),
            "modo_falla": modo, "downtime_h": downtime_h, "costo_usd": costo,
            "criticidad": a["criticidad"],
        })

# ----------------------------------------------------------------------------
# Etiqueta de entrenamiento: "fallo en los proximos 30 dias"
# Depende de las variables del activo -> el modelo puede aprenderla.
# ----------------------------------------------------------------------------
FEATS = ["horas_operacion", "edad_meses", "ciclos_arranque", "vibracion_mm_s",
         "temp_prom_c", "dias_desde_mant", "carga_prom_pct", "fallas_previas"]
X = np.array([[a[f] for f in FEATS] for a in activos], dtype=float)
mu, sd = X.mean(0), X.std(0) + 1e-9
Z = (X - mu) / sd
# pesos "verdaderos" (positivo = mas riesgo)
w_true = np.array([0.5, 0.3, 0.25, 1.15, 0.7, 0.9, 0.4, 0.8])
b_true = -1.25
logit = b_true + Z @ w_true + rng.normal(0, 0.45, len(activos))
p_true = 1 / (1 + np.exp(-logit))
y = (rng.random(len(activos)) < p_true).astype(int)
for i, a in enumerate(activos):
    a["fallo_30d"] = int(y[i])

# ----------------------------------------------------------------------------
# KPIs de confiabilidad
# ----------------------------------------------------------------------------
n_fallas = len(eventos)
downtime_total = sum(e["downtime_h"] for e in eventos)
costo_total = sum(e["costo_usd"] for e in eventos)
# La disponibilidad se mide contra las HORAS PROGRAMADAS de operacion de cada
# activo (su duty), no contra el calendario 24/7.
horas_flota = sum(a["horas_mes"] * MESES for a in activos)
uptime = horas_flota - downtime_total
disponibilidad = 100 * uptime / horas_flota
mtbf = uptime / n_fallas if n_fallas else 0     # h de operacion entre fallas
mttr = downtime_total / n_fallas if n_fallas else 0                     # h por reparacion

def por(campo, fn):
    d = {}
    for e in eventos:
        d.setdefault(e[campo], []).append(e)
    return {k: fn(v) for k, v in d.items()}

# Disponibilidad por mes
dt_mes = {m: 0.0 for m in MESES_K}
fallas_mes = {m: 0 for m in MESES_K}
for e in eventos:
    dt_mes[e["mes"]] += e["downtime_h"]; fallas_mes[e["mes"]] += 1
horas_flota_mes = sum(a["horas_mes"] for a in activos)
disp_mes = [round(100 * (horas_flota_mes - dt_mes[m]) / horas_flota_mes, 1) for m in MESES_K]

# Pareto de modos de falla
modo_ct = {}
for e in eventos:
    modo_ct[e["modo_falla"]] = modo_ct.get(e["modo_falla"], 0) + 1
pareto = sorted(modo_ct.items(), key=lambda kv: kv[1], reverse=True)
tot_m = sum(v for _, v in pareto); acc = 0; pareto_rows = []
for modo, c in pareto:
    acc += c
    pareto_rows.append({"modo": modo, "n": c, "acum_pct": round(100 * acc / tot_m, 1)})

# MTBF / MTTR / disponibilidad por tipo
tipo_rows = []
for tipo, n, tasa, hm, cb, crit in TIPOS:
    act_t = [a for a in activos if a["tipo"] == tipo]
    ev_t = [e for e in eventos if e["tipo"] == tipo]
    dt_t = sum(e["downtime_h"] for e in ev_t)
    horas_t = sum(a["horas_mes"] * MESES for a in act_t)
    tipo_rows.append({
        "tipo": tipo, "activos": len(act_t), "fallas": len(ev_t),
        "mtbf_h": round((horas_t - dt_t) / len(ev_t)) if ev_t else 0,
        "mttr_h": round(dt_t / len(ev_t), 1) if ev_t else 0,
        "disponibilidad": round(100 * (horas_t - dt_t) / horas_t, 1),
        "costo_usd": round(sum(e["costo_usd"] for e in ev_t), 0),
    })

datos = {
    "meta": {"generado": HOY.isoformat(), "periodo": f"{MESES_K[0]} a {MESES_K[-1]}",
             "activos": len(activos), "eventos": n_fallas, "meses": MESES},
    "kpis": {
        "disponibilidad": round(disponibilidad, 1),
        "mtbf_h": round(mtbf), "mttr_h": round(mttr, 1),
        "downtime_h": round(downtime_total), "fallas": n_fallas,
        "costo_mantenimiento_usd": round(costo_total, 0),
        "costo_downtime_prom": round(costo_total / n_fallas) if n_fallas else 0,
    },
    "serie": {"meses": MESES_K, "disponibilidad": disp_mes,
              "fallas": [fallas_mes[m] for m in MESES_K]},
    "pareto": pareto_rows,
    "tipos": tipo_rows,
    # el bloque "modelo" lo agrega modelo.py
}

# ----------------------------------------------------------------------------
# Escritura de CSVs + features + JSON base
# ----------------------------------------------------------------------------
def escribir_csv(nombre, filas, cols):
    with open(DATA / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for x in filas: w.writerow({c: x.get(c, "") for c in cols})

cols_act = ["activo_id", "tipo", "marca", "ubicacion", "edad_meses", "horas_operacion",
            "ciclos_arranque", "vibracion_mm_s", "temp_prom_c", "dias_desde_mant",
            "carga_prom_pct", "fallas_previas", "criticidad", "fallo_30d"]
escribir_csv("dim_activo.csv", activos, cols_act)
escribir_csv("fact_eventos.csv", eventos,
             ["evento_id", "activo_id", "tipo", "ubicacion", "fecha", "mes",
              "modo_falla", "downtime_h", "costo_usd", "criticidad"])
# features para el modelo (variables + etiqueta)
escribir_csv("features.csv", activos, ["activo_id", "tipo", "criticidad"] + FEATS + ["fallo_30d"])

with open(WEB / "datos.json", "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))

print("OK simulacion")
print(f"  activos: {len(activos)}  eventos: {n_fallas}")
print(f"  disponibilidad: {disponibilidad:.1f}%  MTBF: {mtbf:.0f} h  MTTR: {mttr:.1f} h")
print(f"  downtime: {downtime_total:.0f} h  costo: US$ {costo_total:,.0f}")
print(f"  tasa base de falla-30d: {y.mean()*100:.0f}%  ({y.sum()} de {len(y)})")
