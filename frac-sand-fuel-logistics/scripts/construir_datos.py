#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frac Sand & Fuel Logistics — CONSUMO REAL + logística modelada.

El consumo sale de los datos OFICIALES de fractura de la Secretaría de Energía
(los mismos parquets que procesa `vaca-muerta-analytics`): arena bombeada,
agua y etapas por pozo, con su mes de completación. Sobre esa demanda real se
modela la capa logística que NO es pública (proveedores, entregas, stock,
transporte, costo), con una política de reposición (s, S).

  Consumo (arena, agua, etapas, pozos): REAL, del dataset oficial.
  Logística (entregas, stock, lead time, OTIF, costo): MODELADA sobre lo real.

Fuente:
  vaca-muerta-analytics/data/procesado/ajustes_declinacion.parquet
Local usa la versión demo (mismo esquema); en CI son los datos reales.
"""
import csv
import json
import random
import statistics
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"; WEB = RAIZ / "web"
DATA.mkdir(exist_ok=True); WEB.mkdir(exist_ok=True)
PROC = RAIZ.parent / "vaca-muerta-analytics" / "data" / "procesado"
random.seed(42)

if not (PROC / "ajustes_declinacion.parquet").exists():
    raise SystemExit(f"No encuentro {PROC}/ajustes_declinacion.parquet (corré antes el pipeline).")

aj = pd.read_parquet(PROC / "ajustes_declinacion.parquet")
meta_src = json.load(open(PROC / "metadatos.json", encoding="utf-8")) if (PROC / "metadatos.json").exists() else {}
es_demo = bool(meta_src.get("es_demo", True))

aj = aj[aj["tiene_fractura"] == True].copy()
aj["mes"] = pd.to_datetime(aj["primer_mes"]).dt.strftime("%Y-%m")

# ----------------------------------------------------------------------------
# Consumo REAL por mes (arena, agua, etapas, pozos completados)
# ----------------------------------------------------------------------------
N_MESES = 36
por_mes = aj.groupby("mes").agg(
    arena_t=("arena_tn", "sum"), agua_m3=("agua_m3", "sum"),
    etapas=("etapas", "sum"), pozos=("sigla", "count"),
).reset_index().sort_values("mes")
por_mes = por_mes.tail(N_MESES).reset_index(drop=True)

# Rango CONTINUO de meses (los meses sin completaciones se rellenan con 0,
# así el timeline diario y los gráficos no tienen huecos).
def rango_meses(a, b):
    y0, m0 = int(a[:4]), int(a[5:]); y1, m1 = int(b[:4]), int(b[5:]); out = []
    while (y0, m0) <= (y1, m1):
        out.append(f"{y0:04d}-{m0:02d}"); m0 += 1
        if m0 == 13: m0 = 1; y0 += 1
    return out
MESES = rango_meses(por_mes["mes"].iloc[0], por_mes["mes"].iloc[-1])

arena_mes = {m: 0.0 for m in MESES}; arena_mes.update(dict(zip(por_mes["mes"], por_mes["arena_t"])))
etapas_mes = {m: 0.0 for m in MESES}; etapas_mes.update(dict(zip(por_mes["mes"], por_mes["etapas"])))
GASOIL_M3_POR_ETAPA = 11.0  # estimado de ingeniería: gasoil por etapa de fractura
gasoil_mes = {m: etapas_mes[m] * GASOIL_M3_POR_ETAPA for m in MESES}

arena_total_real = float(por_mes["arena_t"].sum())
agua_total_real = float(por_mes["agua_m3"].sum())
etapas_total_real = int(por_mes["etapas"].sum())
pozos_total_real = int(por_mes["pozos"].sum())

# Timeline diario del período
INICIO = date(int(MESES[0][:4]), int(MESES[0][5:]), 1)
y, mo = int(MESES[-1][:4]), int(MESES[-1][5:])
FIN = (date(y + (mo == 12), (mo % 12) + 1, 1)) - timedelta(days=1)
DIAS = [INICIO + timedelta(days=i) for i in range((FIN - INICIO).days + 1)]
clave_mes = lambda d: f"{d.year:04d}-{d.month:02d}"
dias_por_mes = {}
for d in DIAS:
    dias_por_mes[clave_mes(d)] = dias_por_mes.get(clave_mes(d), 0) + 1

consumo_diario_prom = arena_total_real / len(DIAS)

# ----------------------------------------------------------------------------
# Capa logística MODELADA (proveedores, política de reposición, costo)
# ----------------------------------------------------------------------------
PROVEEDORES = [
    ("PRV-01", "Arenera del Sur",      "Chelforo (RN)",   420, 0.93, 5),
    ("PRV-02", "Silice Patagonia",     "Dolavon (CH)",    610, 0.86, 7),
    ("PRV-03", "NQN Frac Sand",        "Anelo (NQN)",      95, 0.90, 2),
    ("PRV-04", "Arenas Cuyanas",       "San Rafael (MZA)",780, 0.80, 8),
]
PADS = ["Loma Campana", "Bandurria Sur", "La Amarga Chica", "Fortin de Piedra",
        "Rincon La Ceniza", "Bajada del Palo", "El Trapial", "Los Toldos"]
# niveles de inventario escalados a la demanda real
SEG = round(consumo_diario_prom * 4)
REORDEN = round(consumo_diario_prom * 8)
OBJETIVO = round(consumo_diario_prom * 18)
LOTE = max(500, round(consumo_diario_prom * 2.2))
COSTO_STANDBY_DIA = 145000
DEMORA_USD_DIA = 850
CAMION_T = 30.0

entregas = []
folio = 0
def nueva_entrega(fecha_orden, cantidad):
    global folio
    prov = random.choices(PROVEEDORES, weights=[0.42, 0.24, 0.20, 0.14])[0]
    pid, pnom, origen, dist, confiab, lead_base = prov
    lead_plan = lead_base + random.randint(0, 2)
    fplan = fecha_orden + timedelta(days=lead_plan)
    if random.random() < (1 - confiab):
        retraso = random.choices([1, 2, 3, 5, 8], weights=[38, 26, 18, 12, 6])[0]
        if dist > 500: retraso += random.randint(0, 3)
    else:
        retraso = -1 if random.random() < 0.15 else 0
    freal = fplan + timedelta(days=retraso)
    cant_plan = round(cantidad, 1)
    cant_real = round(cant_plan * (random.uniform(0.80, 0.97) if random.random() < 0.07 else random.uniform(0.99, 1.01)), 1)
    costo_flete = round((cant_real * dist * 0.13 + max(1, round(cant_real / CAMION_T)) * 380) * random.uniform(0.9, 1.12), 0)
    costo_demora = round(max(0, retraso) * DEMORA_USD_DIA * max(1, round(cant_real / CAMION_T)), 0)
    en_tiempo, completo = retraso <= 0, cant_real >= cant_plan * 0.98
    estado = ("OTIF" if en_tiempo and completo else "Demorado" if not en_tiempo and completo
              else "Incompleto" if en_tiempo else "Demorado+Incompleto")
    folio += 1
    e = {"folio": f"ENV-{folio:05d}", "proveedor": pnom, "proveedor_id": pid, "origen": origen,
         "distancia_km": dist, "pad": random.choice(PADS), "mes": clave_mes(fecha_orden),
         "fecha_real": freal.isoformat(), "lead_real_dias": (freal - fecha_orden).days,
         "retraso_dias": retraso, "cant_real": cant_real, "costo_flete_usd": costo_flete,
         "costo_demora_usd": costo_demora, "estado": estado, "en_tiempo": en_tiempo, "material": "Arena"}
    entregas.append(e)
    return freal, cant_real

# consumo diario de arena (real mensual repartido en los días, con variación)
arena_dia = {}
for d in DIAS:
    base = arena_mes[clave_mes(d)] / dias_por_mes[clave_mes(d)]
    arena_dia[d] = base * random.uniform(0.72, 1.28)

onhand = OBJETIVO * 0.85
pipeline, stock_rows, serie_stock = [], [], []
dias_quiebre = dias_bajo = 0
standby_usd = 0.0
for d in DIAS:
    recep = 0.0
    for arr, qty in [p for p in pipeline if p[0] == d]:
        onhand += qty; recep += qty
    pipeline = [p for p in pipeline if p[0] != d]
    dem = arena_dia[d]
    consumido = min(onhand, dem); onhand -= consumido
    quiebre = 0
    if consumido < dem - 1: quiebre = 1; dias_quiebre += 1; standby_usd += COSTO_STANDBY_DIA
    elif onhand < SEG: dias_bajo += 1
    en_transito = sum(q for _, q in pipeline)
    if onhand + en_transito < REORDEN:
        por_pedir = OBJETIVO - (onhand + en_transito)
        while por_pedir > 1:
            lote = min(LOTE, por_pedir)
            arr, rec = nueva_entrega(d, lote)
            if INICIO <= arr <= FIN + timedelta(days=25): pipeline.append((arr, rec))
            por_pedir -= lote
    stock_rows.append({"fecha": d.isoformat(), "stock_arena_t": round(onhand, 0),
                       "stock_seguridad_t": SEG, "quiebre": quiebre})
    serie_stock.append(round(onhand, 0))

# ----------------------------------------------------------------------------
# KPIs y agregados
# ----------------------------------------------------------------------------
pct = lambda a, b: round(100.0 * a / b, 1) if b else 0.0
tot = len(entregas)
otif = sum(1 for e in entregas if e["estado"] == "OTIF")
lead_reales = [e["lead_real_dias"] for e in entregas]
retrasos = [e["retraso_dias"] for e in entregas if e["retraso_dias"] > 0]
costo_flete = sum(e["costo_flete_usd"] for e in entregas)
costo_demora = sum(e["costo_demora_usd"] for e in entregas)
PRECIO_ARENA_T = 83.0  # referencia de mercado (estimado)
costo_material = arena_total_real * PRECIO_ARENA_T
costo_almacen = statistics.mean(serie_stock) * 1.8 * len(MESES)
costo_logistico = costo_flete + costo_demora + costo_almacen + standby_usd

otif_mes = []
for m in MESES:
    envs = [e for e in entregas if e["mes"] == m]
    otif_mes.append(pct(sum(1 for e in envs if e["estado"] == "OTIF"), len(envs)))

ranking = []
for pid, pnom, origen, dist, confiab, lead_base in PROVEEDORES:
    envs = [e for e in entregas if e["proveedor_id"] == pid]
    if not envs: continue
    ranking.append({"proveedor": pnom, "material": "Arena", "origen": origen, "distancia_km": dist,
                    "envios": len(envs), "volumen": round(sum(e["cant_real"] for e in envs), 0), "unidad": "t",
                    "otif": pct(sum(1 for e in envs if e["estado"] == "OTIF"), len(envs)),
                    "lead_dias": round(statistics.mean(e["lead_real_dias"] for e in envs), 1),
                    "retraso_dias": round(statistics.mean(e["retraso_dias"] for e in envs), 2),
                    "costo_log_usd": round(sum(e["costo_flete_usd"] + e["costo_demora_usd"] for e in envs), 0)})
ranking.sort(key=lambda r: r["otif"], reverse=True)

hist = []
lt = [e["lead_real_dias"] for e in entregas]
for lo, hi in [(0, 2), (3, 4), (5, 6), (7, 8), (9, 11), (12, 99)]:
    hist.append({"rango": f"{lo}-{hi}" if hi < 99 else f"{lo}+", "n": sum(1 for x in lt if lo <= x <= hi)})

rutas = {}
for e in entregas:
    k = (e["origen"], e["proveedor"], e["distancia_km"])
    r = rutas.setdefault(k, {"origen": e["origen"], "proveedor": e["proveedor"], "distancia_km": e["distancia_km"],
                             "envios": 0, "costo_flete_usd": 0.0})
    r["envios"] += 1; r["costo_flete_usd"] += e["costo_flete_usd"]
rutas_lista = sorted(rutas.values(), key=lambda r: r["costo_flete_usd"], reverse=True)
for r in rutas_lista:
    r["costo_prom_envio_usd"] = round(r["costo_flete_usd"] / r["envios"], 0)
    r["costo_flete_usd"] = round(r["costo_flete_usd"], 0)

recientes = [{"folio": e["folio"], "fecha_real": e["fecha_real"], "material": "Arena de fractura",
              "proveedor": e["proveedor"], "pad": e["pad"], "cant_real": e["cant_real"], "unidad": "t",
              "retraso_dias": e["retraso_dias"], "estado": e["estado"]}
             for e in sorted(entregas, key=lambda e: e["fecha_real"], reverse=True)[:12]]

datos = {
    "meta": {"generado": meta_src.get("generado_en", "")[:10], "periodo": f"{MESES[0]} a {MESES[-1]}",
             "meses": len(MESES), "envios": tot, "pozos": pozos_total_real, "es_demo": es_demo,
             "proveedores": len(PROVEEDORES), "etapas": etapas_total_real},
    "kpis": {"arena_total_t": round(arena_total_real, 0), "gasoil_total_m3": round(sum(gasoil_mes.values()), 0),
             "agua_total_m3": round(agua_total_real, 0), "etapas": etapas_total_real,
             "otif_pct": pct(otif, tot), "fill_rate_pct": pct(sum(1 for e in entregas if e["estado"] in ("OTIF", "Demorado")), tot),
             "lead_prom_dias": round(statistics.mean(lead_reales), 1) if lead_reales else 0,
             "retraso_prom_dias": round(statistics.mean(retrasos), 1) if retrasos else 0,
             "cobertura_dias": round(serie_stock[-1] / consumo_diario_prom, 1) if consumo_diario_prom else 0,
             "dias_quiebre": dias_quiebre, "dias_bajo_seguridad": dias_bajo,
             "costo_logistico_usd": round(costo_logistico, 0), "standby_usd": round(standby_usd, 0),
             "costo_log_por_t": round(costo_logistico / arena_total_real, 1) if arena_total_real else 0},
    "serie": {"meses": MESES, "arena_t": [round(arena_mes[m], 0) for m in MESES],
              "gasoil_m3": [round(gasoil_mes[m], 0) for m in MESES], "otif_pct": otif_mes},
    "stock": {"fechas": [r["fecha"] for r in stock_rows], "stock_t": [r["stock_arena_t"] for r in stock_rows],
              "seguridad_t": SEG, "quiebres": [i for i, r in enumerate(stock_rows) if r["quiebre"]]},
    "costo_desglose": [
        {"concepto": "Arena (material)", "usd": round(costo_material, 0)},
        {"concepto": "Transporte / flete", "usd": round(costo_flete, 0)},
        {"concepto": "Almacenamiento", "usd": round(costo_almacen, 0)},
        {"concepto": "Demoras (demurrage)", "usd": round(costo_demora, 0)},
        {"concepto": "Standby por quiebre", "usd": round(standby_usd, 0)}],
    "ranking": ranking, "hist_lead": hist, "rutas": rutas_lista, "recientes": recientes,
}
json.dump(datos, open(WEB / "datos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# CSV del consumo real (para Power BI)
with open(DATA / "consumo_real_mensual.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["mes", "arena_t", "agua_m3", "etapas", "pozos"])
    for r in por_mes.itertuples():
        w.writerow([r.mes, round(r.arena_t), round(r.agua_m3), int(r.etapas), int(r.pozos)])

fuente = "DEMO" if es_demo else "oficiales (Secretaría de Energía)"
print("OK logistica")
print(f"  fuente consumo: {fuente}  | pozos: {pozos_total_real}  meses: {len(MESES)}")
print(f"  arena real: {arena_total_real:,.0f} t  agua: {agua_total_real:,.0f} m3  etapas: {etapas_total_real:,}")
print(f"  envios modelados: {tot}  OTIF: {datos['kpis']['otif_pct']}%  quiebre: {dias_quiebre} d")
print(f"  costo logistico: US$ {costo_logistico:,.0f}  ({datos['kpis']['costo_log_por_t']} US$/t)")
