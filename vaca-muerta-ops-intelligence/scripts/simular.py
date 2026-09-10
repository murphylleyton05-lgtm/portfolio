#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vaca Muerta Operations Intelligence — motor de datos.

Simula la ACTIVIDAD Y PRODUCCION de una cartera de pozos no convencionales de
Vaca Muerta a lo largo del tiempo: pozos que se van perforando y completando,
su produccion mensual de petroleo y gas (con curva de declinacion tipo Arps),
por operador y area. Es el tipo de dato que alimenta un tablero de Power BI de
management: producción, actividad, acumulado, ranking de operadores.

Deja:
  data/*.csv     -> esquema estrella (dim_/fact_), listo para modelar en Power BI
  web/datos.json -> agregados para el dashboard web

Datos SIMULADOS (semilla fija). El proyecto hermano `vaca-muerta-analytics` usa
los datos oficiales reales de la Secretaría de Energía; este se enfoca en el
modelo de datos y el tablero de operaciones, con datos sintéticos realistas.
"""
import csv
import json
import numpy as np
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"; WEB = RAIZ / "web"
DATA.mkdir(exist_ok=True); WEB.mkdir(exist_ok=True)
rng = np.random.default_rng(11)

MESES = 36
def meses_lista():
    y, mo, out = 2023, 9, []
    for _ in range(MESES):
        out.append(f"{y:04d}-{mo:02d}"); mo += 1
        if mo == 13: mo = 1; y += 1
    return out
MK = meses_lista()

OPERADORES = [
    # nombre, peso (share de actividad), calidad (multiplica productividad)
    ("YPF", 0.26, 1.06), ("Vista Energy", 0.12, 1.12), ("Shell", 0.10, 1.04),
    ("Tecpetrol", 0.10, 1.02), ("Pan American Energy", 0.09, 1.00),
    ("Pluspetrol", 0.08, 0.98), ("Chevron", 0.07, 1.03), ("ExxonMobil", 0.06, 1.05),
    ("Pampa Energia", 0.06, 0.97), ("Total Austral", 0.06, 1.01),
]
AREAS = [
    ("Loma Campana", "Petroleo negro"), ("Bandurria Sur", "Petroleo negro"),
    ("La Amarga Chica", "Petroleo negro"), ("Fortin de Piedra", "Gas y condensado"),
    ("Aguada Pichana", "Gas y condensado"), ("Rincon La Ceniza", "Petroleo volatil"),
    ("Bajada del Palo", "Petroleo negro"), ("El Trapial", "Petroleo volatil"),
    ("Los Toldos", "Petroleo volatil"), ("Aguada Federal", "Gas y condensado"),
]
VENT_QI = {  # qi de petroleo (bbl/d) y factor gas segun ventana
    "Petroleo negro":    (1150, 0.9),
    "Petroleo volatil":  (950, 1.9),
    "Gas y condensado":  (280, 7.0),
}

# ----------------------------------------------------------------------------
# Generar pozos: se perforan escalonados en el tiempo (actividad creciente)
# ----------------------------------------------------------------------------
N_POZOS = 90
pozos = []
op_names = [o[0] for o in OPERADORES]
op_w = np.array([o[1] for o in OPERADORES]); op_w = op_w / op_w.sum()
op_q = {o[0]: o[2] for o in OPERADORES}
for i in range(N_POZOS):
    op = str(rng.choice(op_names, p=op_w))
    area, ventana = AREAS[int(rng.integers(len(AREAS)))]
    # mes de spud: distribuido en los primeros ~30 meses (actividad sostenida)
    spud_idx = int(np.clip(rng.integers(0, MESES - 4), 0, MESES - 4))
    # completado 2-4 meses despues; primera produccion 1 mes despues
    comp_idx = min(MESES - 1, spud_idx + int(rng.integers(2, 5)))
    fp_idx = min(MESES - 1, comp_idx + 1)
    rama = int(np.clip(rng.normal(2600, 550), 1200, 3800))
    etapas = int(rama / rng.uniform(50, 75))
    qi_base, gas_factor = VENT_QI[ventana]
    qi = qi_base * op_q[op] * (rama / 2600) ** 0.6 * rng.uniform(0.7, 1.3)
    b = float(np.clip(rng.normal(1.1, 0.25), 0.6, 1.7))
    Di = rng.uniform(0.10, 0.16)  # declinacion nominal mensual inicial
    costo = round((9.0 + rama / 1000 * 1.6 + etapas * 0.05) * rng.uniform(0.9, 1.12), 1)  # US$ MM
    pozos.append({
        "pozo_id": f"VM-{i+1:03d}", "operador": op, "area": area, "ventana": ventana,
        "rama_m": rama, "etapas": etapas, "qi_bbl_d": round(qi, 0), "b": round(b, 2),
        "Di": round(Di, 4), "gas_factor": gas_factor, "costo_musd": costo,
        "spud": MK[spud_idx], "completado": MK[comp_idx], "primera_prod": MK[fp_idx],
        "fp_idx": fp_idx, "spud_idx": spud_idx, "comp_idx": comp_idx,
    })

# ----------------------------------------------------------------------------
# Produccion mensual por pozo (Arps hiperbolica) -> fact_produccion
# ----------------------------------------------------------------------------
DIAS_MES = 30.4
def arps(qi, Di, b, t):  # t en meses desde primera produccion
    return qi / (1.0 + b * Di * t) ** (1.0 / b)

fact_prod = []
for p in pozos:
    for idx in range(p["fp_idx"], MESES):
        t = idx - p["fp_idx"]
        q_oil = arps(p["qi_bbl_d"], p["Di"], p["b"], t) * rng.uniform(0.93, 1.07)
        oil_bbl = q_oil * DIAS_MES
        gas_mm3 = q_oil * p["gas_factor"] * 0.159 / 1000 * DIAS_MES  # bbl->m3 aprox, a Mm3
        agua = oil_bbl * rng.uniform(0.2, 0.8)
        fact_prod.append({
            "pozo_id": p["pozo_id"], "operador": p["operador"], "area": p["area"],
            "ventana": p["ventana"], "mes": MK[idx],
            "petroleo_bbl": round(oil_bbl, 0), "gas_mm3": round(gas_mm3, 3),
            "agua_bbl": round(agua, 0), "petroleo_bbl_d": round(q_oil, 1),
        })

# ----------------------------------------------------------------------------
# Actividad: spuds y completions por mes -> fact_actividad
# ----------------------------------------------------------------------------
spuds = {m: 0 for m in MK}; comps = {m: 0 for m in MK}
for p in pozos:
    spuds[p["spud"]] += 1; comps[p["completado"]] += 1
fact_act = [{"mes": m, "spuds": spuds[m], "completions": comps[m]} for m in MK]

# ----------------------------------------------------------------------------
# Agregados para el dashboard
# ----------------------------------------------------------------------------
oil_mes = {m: 0.0 for m in MK}; gas_mes = {m: 0.0 for m in MK}; pozos_activos = {m: set() for m in MK}
for r in fact_prod:
    oil_mes[r["mes"]] += r["petroleo_bbl"]; gas_mes[r["mes"]] += r["gas_mm3"]
    pozos_activos[r["mes"]].add(r["pozo_id"])

oil_bbl_d = [round(oil_mes[m] / DIAS_MES, 0) for m in MK]
gas_mm3_d = [round(gas_mes[m] / DIAS_MES, 2) for m in MK]
activos = [len(pozos_activos[m]) for m in MK]
acum_oil = np.cumsum([oil_mes[m] for m in MK]) / 1e6  # MMbbl
acum = [round(x, 2) for x in acum_oil]

# Ranking de operadores (acumulado y ultimo mes)
op_rows = []
ult = MK[-1]
for op in op_names:
    p_op = [p for p in pozos if p["operador"] == op]
    prod_op = [r for r in fact_prod if r["operador"] == op]
    acum_op = sum(r["petroleo_bbl"] for r in prod_op) / 1e6
    ult_op = sum(r["petroleo_bbl_d"] for r in prod_op if r["mes"] == ult)
    if not p_op: continue
    op_rows.append({
        "operador": op, "pozos": len(p_op),
        "acum_mmbbl": round(acum_op, 2),
        "oil_bbl_d": round(ult_op, 0),
        "prod_por_pozo": round(ult_op / len(p_op), 0) if p_op else 0,
        "inversion_musd": round(sum(x["costo_musd"] for x in p_op), 0),
    })
op_rows.sort(key=lambda r: r["oil_bbl_d"], reverse=True)

# Mix por ventana (produccion actual)
vent_mix = {}
for r in fact_prod:
    if r["mes"] == ult:
        vent_mix[r["ventana"]] = vent_mix.get(r["ventana"], 0) + r["petroleo_bbl_d"]
vent_rows = [{"ventana": k, "oil_bbl_d": round(v, 0)} for k, v in
             sorted(vent_mix.items(), key=lambda kv: kv[1], reverse=True)]

# Performance por pozo (top por acumulado)
pozo_acum = {}
for r in fact_prod:
    pozo_acum[r["pozo_id"]] = pozo_acum.get(r["pozo_id"], 0) + r["petroleo_bbl"]
peak = {}
for r in fact_prod:
    peak[r["pozo_id"]] = max(peak.get(r["pozo_id"], 0), r["petroleo_bbl_d"])
pozo_rows = []
for p in pozos:
    pozo_rows.append({
        "pozo_id": p["pozo_id"], "operador": p["operador"], "area": p["area"],
        "ventana": p["ventana"], "primera_prod": p["primera_prod"], "rama_m": p["rama_m"],
        "peak_bbl_d": round(peak.get(p["pozo_id"], 0), 0),
        "acum_mbbl": round(pozo_acum.get(p["pozo_id"], 0) / 1000, 0),
        "costo_musd": p["costo_musd"],
    })
pozo_rows.sort(key=lambda r: r["acum_mbbl"], reverse=True)

# Indicadores del periodo (mes actual vs anterior)
def var(a, b): return round(100 * (a - b) / b, 1) if b else 0
kpis = {
    "oil_bbl_d": oil_bbl_d[-1], "oil_var_mom": var(oil_bbl_d[-1], oil_bbl_d[-2]),
    "gas_mm3_d": gas_mm3_d[-1], "gas_var_mom": var(gas_mm3_d[-1], gas_mm3_d[-2]),
    "pozos_activos": activos[-1], "pozos_total": len(pozos),
    "acum_mmbbl": acum[-1],
    "pozos_perforados": sum(spuds.values()), "completions": sum(comps.values()),
    "inversion_musd": round(sum(p["costo_musd"] for p in pozos), 0),
}

datos = {
    "meta": {"generado": date(2026, 9, 1).isoformat(), "periodo": f"{MK[0]} a {MK[-1]}",
             "meses": MESES, "pozos": len(pozos), "operadores": len(op_rows)},
    "kpis": kpis,
    "serie": {"meses": MK, "oil_bbl_d": oil_bbl_d, "gas_mm3_d": gas_mm3_d,
              "activos": activos, "acum_mmbbl": acum,
              "spuds": [spuds[m] for m in MK], "completions": [comps[m] for m in MK]},
    "operadores": op_rows, "ventanas": vent_rows, "pozos_top": pozo_rows[:14],
}

# ----------------------------------------------------------------------------
# Escritura CSV (estrella) + JSON
# ----------------------------------------------------------------------------
def escribir_csv(nombre, filas, cols):
    with open(DATA / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for x in filas: w.writerow({c: x.get(c, "") for c in cols})

escribir_csv("dim_pozo.csv", pozos,
             ["pozo_id", "operador", "area", "ventana", "rama_m", "etapas", "qi_bbl_d",
              "b", "Di", "costo_musd", "spud", "completado", "primera_prod"])
escribir_csv("dim_operador.csv", [{"operador": o[0], "share_actividad": o[1]} for o in OPERADORES],
             ["operador", "share_actividad"])
escribir_csv("dim_area.csv", [{"area": a[0], "ventana": a[1]} for a in AREAS], ["area", "ventana"])
escribir_csv("dim_fecha.csv", [{"mes": m, "anio": int(m[:4]), "mes_num": int(m[5:])} for m in MK],
             ["mes", "anio", "mes_num"])
escribir_csv("fact_produccion.csv", fact_prod,
             ["pozo_id", "operador", "area", "ventana", "mes", "petroleo_bbl", "gas_mm3",
              "agua_bbl", "petroleo_bbl_d"])
escribir_csv("fact_actividad.csv", fact_act, ["mes", "spuds", "completions"])

json.dump(datos, open(WEB / "datos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

print("OK simulacion")
print(f"  pozos: {len(pozos)}  filas de produccion: {len(fact_prod)}")
print(f"  oil actual: {oil_bbl_d[-1]:,.0f} bbl/d  gas: {gas_mm3_d[-1]:.1f} Mm3/d  activos: {activos[-1]}")
print(f"  acumulado: {acum[-1]:.1f} MMbbl  inversion: US$ {kpis['inversion_musd']:,.0f} MM")
