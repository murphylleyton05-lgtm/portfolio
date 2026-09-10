#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vaca Muerta Operations Intelligence — datos REALES.

Lee los parquets procesados del pipeline oficial (el mismo que alimenta
`vaca-muerta-analytics`, con datos de la Secretaría de Energía) y arma el
web/datos.json del tablero de operaciones. En CI esos parquets se regeneran
con los datos oficiales completos; localmente son la versión demo (mismo
esquema), así que este script corre igual en los dos casos.

Fuente de los parquets:
  vaca-muerta-analytics/data/procesado/{produccion,pozos}.parquet
"""
import json
import sys
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"; WEB.mkdir(exist_ok=True)
PROC = RAIZ.parent / "vaca-muerta-analytics" / "data" / "procesado"

BBL_M3 = 6.28981
DIAS = 30.4
N_SERIE = 36  # meses a graficar

if not (PROC / "produccion.parquet").exists():
    sys.exit(f"No encuentro los parquets en {PROC}. Corré antes el pipeline de vaca-muerta-analytics.")

prod = pd.read_parquet(PROC / "produccion.parquet")
pozos = pd.read_parquet(PROC / "pozos.parquet")
meta_src = {}
if (PROC / "metadatos.json").exists():
    meta_src = json.load(open(PROC / "metadatos.json", encoding="utf-8"))
es_demo = bool(meta_src.get("es_demo", True))

prod["ym"] = prod["fecha"].dt.strftime("%Y-%m")
prod["oil_bbl"] = prod["prod_petroleo_m3"] * BBL_M3

# --- serie mensual (toda la historia; despues recortamos a los ultimos N) ---
mens = prod.groupby("ym").agg(
    oil_bbl=("oil_bbl", "sum"),
    gas_mm3=("prod_gas_mm3", "sum"),
    activos=("id_pozo", "nunique"),
).reset_index().sort_values("ym")
mens["oil_bbl_d"] = (mens["oil_bbl"] / DIAS).round(0)
mens["gas_mm3_d"] = (mens["gas_mm3"] / DIAS).round(2)
mens["acum_mmbbl"] = (mens["oil_bbl"].cumsum() / 1e6).round(2)

# pozos nuevos por mes (primer mes de produccion)
pozos["primer_ym"] = pd.to_datetime(pozos["primer_mes"]).dt.strftime("%Y-%m")
nuevos_por_mes = pozos.groupby("primer_ym").size()
mens["nuevos"] = mens["ym"].map(nuevos_por_mes).fillna(0).astype(int)

serie = mens.tail(N_SERIE).reset_index(drop=True)
meses = serie["ym"].tolist()

# --- KPIs (ultimo mes vs anterior) ---
ult, ant = mens.iloc[-1], mens.iloc[-2]
def var(a, b): return round(100 * (a - b) / b, 1) if b else 0.0
gas_acum_mmm3 = round(prod["prod_gas_mm3"].sum() / 1000, 1)  # Mm3 -> MMm3 (miles de Mm3)

kpis = {
    "oil_bbl_d": float(ult["oil_bbl_d"]), "oil_var_mom": var(ult["oil_bbl_d"], ant["oil_bbl_d"]),
    "gas_mm3_d": float(ult["gas_mm3_d"]), "gas_var_mom": var(ult["gas_mm3_d"], ant["gas_mm3_d"]),
    "pozos_activos": int(ult["activos"]), "pozos_total": int(pozos["id_pozo"].nunique()),
    "acum_mmbbl": float(mens["acum_mmbbl"].iloc[-1]),
    "gas_acum_mmm3": gas_acum_mmm3,
    "pozos_nuevos": int(serie["nuevos"].sum()),
    "operadores": int(prod["empresa"].nunique()),
}

# --- ranking de operadores (ultimo mes + acumulado) ---
ult_ym = mens["ym"].iloc[-1]
pu = prod[prod["ym"] == ult_ym]
ranking = pu.groupby("empresa").agg(
    oil_bbl_d=("oil_bbl", lambda s: round(s.sum() / DIAS, 0)),
    pozos=("id_pozo", "nunique"),
).reset_index()
acum_op = (pozos.groupby("empresa")["acum_petroleo_bbl"].sum() / 1e6).round(2)
ranking["acum_mmbbl"] = ranking["empresa"].map(acum_op).fillna(0)
ranking["prod_por_pozo"] = (ranking["oil_bbl_d"] / ranking["pozos"]).round(0)
ranking = ranking.sort_values("oil_bbl_d", ascending=False)
op_rows = [{"operador": r.empresa, "oil_bbl_d": float(r.oil_bbl_d), "pozos": int(r.pozos),
            "prod_por_pozo": float(r.prod_por_pozo), "acum_mmbbl": float(r.acum_mmbbl)}
           for r in ranking.itertuples()][:12]

# --- mix por ventana de fluido (produccion actual) ---
vent_map = pozos.set_index("id_pozo")["ventana_fluido"].to_dict()
pu = pu.copy(); pu["ventana"] = pu["id_pozo"].map(vent_map)
vent = (pu.groupby("ventana")["oil_bbl"].sum() / DIAS).round(0).sort_values(ascending=False)
vent_rows = [{"ventana": k, "oil_bbl_d": float(v)} for k, v in vent.items() if pd.notna(k)]

# --- top pozos por acumulado ---
top = pozos.sort_values("acum_petroleo_bbl", ascending=False).head(14)
pozo_rows = [{"pozo_id": r.sigla, "operador": r.empresa, "area": r.area.title(),
              "ventana": r.ventana_fluido, "peak_bbl_d": round(r.pico_petroleo_m3d * BBL_M3, 0),
              "acum_mbbl": round(r.acum_petroleo_bbl / 1000, 0)} for r in top.itertuples()]

datos = {
    "meta": {"generado": meta_src.get("generado_en", "")[:10], "periodo": f"{meses[0]} a {meses[-1]}",
             "meses": len(meses), "pozos": kpis["pozos_total"], "operadores": kpis["operadores"],
             "es_demo": es_demo, "hist_desde": mens["ym"].iloc[0]},
    "kpis": kpis,
    "serie": {"meses": meses, "oil_bbl_d": serie["oil_bbl_d"].tolist(),
              "gas_mm3_d": serie["gas_mm3_d"].tolist(), "activos": serie["activos"].tolist(),
              "acum_mmbbl": serie["acum_mmbbl"].tolist(), "nuevos": serie["nuevos"].tolist()},
    "operadores": op_rows, "ventanas": vent_rows, "pozos_top": pozo_rows,
}

json.dump(datos, open(WEB / "datos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
fuente = "DEMO (sintéticos)" if es_demo else "oficiales (Secretaría de Energía)"
print("OK datos operaciones")
print(f"  fuente: {fuente}")
print(f"  pozos: {kpis['pozos_total']}  operadores: {kpis['operadores']}  historia desde {mens['ym'].iloc[0]}")
print(f"  oil: {kpis['oil_bbl_d']:,.0f} bbl/d  gas: {kpis['gas_mm3_d']:.1f} Mm3/d  activos: {kpis['pozos_activos']}")
print(f"  acumulado: {kpis['acum_mmbbl']:.1f} MMbbl")
