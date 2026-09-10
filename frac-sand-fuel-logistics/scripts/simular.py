#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simula la cadena de suministro de una operacion de fractura en Vaca Muerta:
arena de fractura (frac sand) y gasoil para los equipos de bombeo.

Genera datos SINTETICOS con logica de negocio realista y los deja en:
  data/*.csv     -> esquema estrella (dim_* y fact_*), listo para Power BI
  web/datos.json -> agregados y series ya calculados para el dashboard web

La arena se modela con una POLITICA DE REPOSICION (s, S): cuando el inventario
disponible + en transito cae por debajo del punto de reorden s, se emite una
orden para reponer hasta el nivel objetivo S. Las ordenes llegan tras su lead
time (con demoras segun el proveedor), asi que un envio demorado puede hacer
que el stock perfore el nivel de seguridad e incluso quiebre (equipo parado).
Asi el stock, el cumplimiento (OTIF) y el costo salen de la misma realidad.

Solo usa la libreria estandar. Es determinista (semilla fija).
"""

import csv
import json
import random
import statistics
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
WEB = RAIZ / "web"
DATA.mkdir(exist_ok=True)
WEB.mkdir(exist_ok=True)

random.seed(42)

HOY = date(2026, 9, 1)
MESES = 24


def primeros_de_mes(fin, n):
    y, m, out = fin.year, fin.month, []
    for _ in range(n):
        out.append(date(y, m, 1))
        m -= 1
        if m == 0:
            y -= 1
            m = 12
    return list(reversed(out))


MESES_LISTA = primeros_de_mes(date(HOY.year, HOY.month, 1), MESES)
INICIO = MESES_LISTA[0]
FIN = HOY - timedelta(days=1)
DIAS = [INICIO + timedelta(days=i) for i in range((FIN - INICIO).days + 1)]
clave_mes = lambda d: f"{d.year:04d}-{d.month:02d}"

# ----------------------------------------------------------------------------
# Dimensiones (datos simulados; nombres genericos / geografia real)
# ----------------------------------------------------------------------------
PROVEEDORES = [
    ("PRV-01", "Arenera del Sur",      "Arena",  "Chelforo (RN)",        420, 0.93, 5),
    ("PRV-02", "Silice Patagonia",     "Arena",  "Dolavon (CH)",         610, 0.86, 7),
    ("PRV-03", "NQN Frac Sand",        "Arena",  "Anelo (NQN)",           95, 0.90, 2),
    ("PRV-04", "Arenas Cuyanas",       "Arena",  "San Rafael (MZA)",     780, 0.80, 8),
    ("PRV-05", "Combustibles del Alto","Gasoil", "Plaza Huincul (NQN)",  110, 0.95, 2),
    ("PRV-06", "Distribuidora Neuquen","Gasoil", "Neuquen (NQN)",        130, 0.91, 2),
    ("PRV-07", "Sur Energia",          "Gasoil", "Bahia Blanca (BA)",    640, 0.84, 6),
]
PADS = [
    ("PAD-01", "Loma Campana", "YPF"), ("PAD-02", "Bandurria Sur", "YPF"),
    ("PAD-03", "La Amarga Chica", "YPF"), ("PAD-04", "Fortin de Piedra", "Tecpetrol"),
    ("PAD-05", "Rincon La Ceniza", "Shell"), ("PAD-06", "Bajada del Palo", "Vista"),
    ("PAD-07", "El Trapial", "Chevron"), ("PAD-08", "Aguada Pichana", "Total"),
    ("PAD-09", "Los Toldos", "ExxonMobil"), ("PAD-10", "Cruz de Lorena", "Shell"),
    ("PAD-11", "Aguada Federal", "Wintershall"), ("PAD-12", "Coiron Amargo", "Pan American"),
]
MATERIALES = [
    ("MAT-01", "Arena fina (100 mesh)", "t",  75.0),
    ("MAT-02", "Arena gruesa (40/70)",  "t",  92.0),
    ("MAT-03", "Gasoil grado 2",        "m3", 950.0),
]

# ----------------------------------------------------------------------------
# Parametros de negocio
# ----------------------------------------------------------------------------
SETS_FRACTURA = 3
ARENA_POR_ETAPA_T = 320
ETAPAS_POR_DIA = 9
DIAS_ACTIVOS_MES = 15
GASOIL_POR_DIA_SET_M3 = 42

# Politica de reposicion de arena (toneladas)
STOCK_SEGURIDAD_T = 12000     # piso de seguridad (linea de referencia)
PUNTO_REORDEN_T = 34000       # s: emitir orden cuando la posicion cae por debajo
NIVEL_OBJETIVO_T = 78000      # S: reponer hasta aca
LOTE_MAX_ENVIO_T = 9000       # una orden grande se parte en envios de este tope

COSTO_STANDBY_USD_DIA = 145000
COSTO_ALMACEN_USD_T_MES = 1.8
DEMORA_USD_DIA = 850
CAMION_ARENA_T = 30.0
ENVIO_GASOIL_M3 = 120.0

prov_arena = [p for p in PROVEEDORES if p[2] == "Arena"]
prov_gasoil = [p for p in PROVEEDORES if p[2] == "Gasoil"]
mat_arena = [m for m in MATERIALES if m[2] == "t"]
mat_gasoil = [m for m in MATERIALES if m[2] == "m3"]


def costo_transporte_usd(distancia_km, toneladas_equiv):
    viajes = max(1, round(toneladas_equiv / CAMION_ARENA_T))
    return (toneladas_equiv * distancia_km * 0.13 + viajes * 380) * random.uniform(0.9, 1.12)


entregas = []
folio = 0


def nueva_entrega(fecha_orden, familia, cantidad, proveedores, materiales, unidad):
    """Crea un envio: elige proveedor/material, calcula lead/retraso/costo."""
    global folio
    prov = random.choices(proveedores, weights=[0.42, 0.24, 0.20, 0.14][: len(proveedores)])[0]
    pid, pnom, pmat, origen, dist, confiab, lead_base = prov
    pad = random.choice(PADS)
    mat = random.choice(materiales)

    lead_plan = lead_base + random.randint(0, 2)
    fecha_plan = fecha_orden + timedelta(days=lead_plan)
    if random.random() < (1 - confiab):
        retraso = random.choices([1, 2, 3, 5, 8], weights=[38, 26, 18, 12, 6])[0]
        if dist > 500:
            retraso += random.randint(0, 3)
    else:
        retraso = -1 if random.random() < 0.15 else 0
    fecha_real = fecha_plan + timedelta(days=retraso)
    lead_real = (fecha_real - fecha_orden).days

    cant_plan = round(cantidad, 1)
    if random.random() < 0.07:
        cant_real = round(cant_plan * random.uniform(0.80, 0.97), 1)
    else:
        cant_real = round(cant_plan * random.uniform(0.99, 1.01), 1)

    t_equiv = cant_real if unidad == "t" else cant_real * 0.84
    costo_material = round(cant_real * mat[3], 0)
    costo_flete = round(costo_transporte_usd(dist, t_equiv), 0)
    costo_demora = round(max(0, retraso) * DEMORA_USD_DIA * max(1, round(t_equiv / CAMION_ARENA_T)), 0)

    en_tiempo, completo = retraso <= 0, cant_real >= cant_plan * 0.98
    estado = ("OTIF" if en_tiempo and completo else
              "Demorado" if not en_tiempo and completo else
              "Incompleto" if en_tiempo else "Demorado+Incompleto")

    folio += 1
    e = {
        "folio": f"ENV-{folio:05d}", "material_id": mat[0], "material": mat[1],
        "familia": familia, "unidad": unidad, "proveedor_id": pid, "proveedor": pnom,
        "origen": origen, "distancia_km": dist, "pad_id": pad[0], "pad": pad[1],
        "operadora": pad[2], "mes": clave_mes(fecha_orden),
        "fecha_orden": fecha_orden.isoformat(), "fecha_plan": fecha_plan.isoformat(),
        "fecha_real": fecha_real.isoformat(), "lead_plan_dias": lead_plan,
        "lead_real_dias": lead_real, "retraso_dias": retraso, "cant_plan": cant_plan,
        "cant_real": cant_real, "costo_material_usd": costo_material,
        "costo_flete_usd": costo_flete, "costo_demora_usd": costo_demora, "estado": estado,
        "en_tiempo": en_tiempo, "completo": completo,
    }
    entregas.append(e)
    return e, fecha_real, cant_real


# ----------------------------------------------------------------------------
# Demanda mensual (arena y gasoil) con tendencia + estacionalidad + ruido
# ----------------------------------------------------------------------------
consumo_rows = []
arena_mes_dda, gasoil_mes_dda = {}, {}
for i, mes in enumerate(MESES_LISTA):
    factor = (1.0 + 0.010 * i) * (1.0 + 0.08 * (1 if mes.month in (3, 4, 5, 9, 10) else -0.4)) * random.uniform(0.92, 1.08)
    arena = SETS_FRACTURA * ETAPAS_POR_DIA * ARENA_POR_ETAPA_T * DIAS_ACTIVOS_MES * factor
    gasoil = SETS_FRACTURA * GASOIL_POR_DIA_SET_M3 * DIAS_ACTIVOS_MES * factor
    arena_mes_dda[clave_mes(mes)] = arena
    gasoil_mes_dda[clave_mes(mes)] = gasoil
    consumo_rows.append({"mes": clave_mes(mes), "arena_consumo_t": round(arena, 0),
                         "gasoil_consumo_m3": round(gasoil, 0), "sets_activos": SETS_FRACTURA,
                         "etapas_estimadas": round(arena / ARENA_POR_ETAPA_T, 0)})

# Consumo diario de arena (reparto del mes en sus dias, con variabilidad)
dias_por_mes = {}
for d in DIAS:
    dias_por_mes[clave_mes(d)] = dias_por_mes.get(clave_mes(d), 0) + 1
arena_dia = {}
for d in DIAS:
    base = arena_mes_dda[clave_mes(d)] / dias_por_mes[clave_mes(d)]
    arena_dia[d] = base * random.uniform(0.72, 1.28)

# ----------------------------------------------------------------------------
# Simulacion de inventario de arena con politica (s, S)
# ----------------------------------------------------------------------------
onhand = NIVEL_OBJETIVO_T * 0.85
pipeline = []          # lista de (fecha_arribo, cantidad)
stock_rows, serie_stock = [], []
dias_quiebre = dias_bajo_seg = 0
standby_usd = 0.0
consumo_real_arena = 0.0

for d in DIAS:
    # 1) recepciones del dia
    recep = 0.0
    llegan = [p for p in pipeline if p[0] == d]
    for arr, qty in llegan:
        onhand += qty
        recep += qty
    pipeline = [p for p in pipeline if p[0] != d]

    # 2) consumo del dia (limitado por lo disponible -> quiebre si falta)
    demanda = arena_dia[d]
    consumido = min(onhand, demanda)
    onhand -= consumido
    consumo_real_arena += consumido
    quiebre = 0
    if consumido < demanda - 1:      # no se pudo abastecer todo: equipo parado
        quiebre = 1
        dias_quiebre += 1
        standby_usd += COSTO_STANDBY_USD_DIA
    elif onhand < STOCK_SEGURIDAD_T:
        dias_bajo_seg += 1

    # 3) reorden: si la posicion (disponible + en transito) < s, reponer hasta S
    en_transito = sum(q for _, q in pipeline)
    posicion = onhand + en_transito
    if posicion < PUNTO_REORDEN_T:
        por_pedir = NIVEL_OBJETIVO_T - posicion
        while por_pedir > 1:
            lote = min(LOTE_MAX_ENVIO_T, por_pedir)
            e, arribo, recibido = nueva_entrega(d, "Arena", lote, prov_arena, mat_arena, "t")
            if INICIO <= arribo <= FIN + timedelta(days=20):
                pipeline.append((arribo, recibido))
            por_pedir -= lote

    stock_rows.append({"fecha": d.isoformat(), "stock_arena_t": round(onhand, 0),
                       "consumo_t": round(consumido, 0), "recepcion_t": round(recep, 0),
                       "stock_seguridad_t": STOCK_SEGURIDAD_T, "quiebre": quiebre})
    serie_stock.append(round(onhand, 0))

# ----------------------------------------------------------------------------
# Gasoil: ordenes mensuales simples (no se modela su stock)
# ----------------------------------------------------------------------------
for mes in MESES_LISTA:
    dda = gasoil_mes_dda[clave_mes(mes)] * 1.02
    n = max(1, round(dda / ENVIO_GASOIL_M3))
    for _ in range(n):
        dia = random.randint(1, 26)
        nueva_entrega(date(mes.year, mes.month, dia), "Gasoil", ENVIO_GASOIL_M3,
                      prov_gasoil, mat_gasoil, "m3")

# ----------------------------------------------------------------------------
# KPIs y agregados
# ----------------------------------------------------------------------------
pct = lambda a, b: round(100.0 * a / b, 1) if b else 0.0
tot = len(entregas)
otif = sum(1 for e in entregas if e["estado"] == "OTIF")
a_tiempo = sum(1 for e in entregas if e["en_tiempo"])
completos = sum(1 for e in entregas if e["completo"])
lead_reales = [e["lead_real_dias"] for e in entregas]
retrasos = [e["retraso_dias"] for e in entregas if e["retraso_dias"] > 0]
arena_total = sum(e["cant_real"] for e in entregas if e["familia"] == "Arena")
gasoil_total = sum(e["cant_real"] for e in entregas if e["familia"] == "Gasoil")

mat_arena_cost = sum(e["costo_material_usd"] for e in entregas if e["familia"] == "Arena")
mat_gasoil_cost = sum(e["costo_material_usd"] for e in entregas if e["familia"] == "Gasoil")
costo_flete = sum(e["costo_flete_usd"] for e in entregas)
costo_demora = sum(e["costo_demora_usd"] for e in entregas)
costo_almacen = statistics.mean(serie_stock) * COSTO_ALMACEN_USD_T_MES * MESES
costo_logistico = costo_flete + costo_demora + costo_almacen + standby_usd
costo_total = mat_arena_cost + mat_gasoil_cost + costo_logistico
consumo_diario_prom = consumo_real_arena / len(DIAS)
cobertura_dias = round(serie_stock[-1] / consumo_diario_prom, 1) if consumo_diario_prom else 0

serie_meses = [r["mes"] for r in consumo_rows]
otif_mes = []
for mm in serie_meses:
    envs = [e for e in entregas if e["mes"] == mm]
    otif_mes.append(pct(sum(1 for e in envs if e["estado"] == "OTIF"), len(envs)))

ranking = []
for pid, pnom, pmat, origen, dist, confiab, lead_base in PROVEEDORES:
    envs = [e for e in entregas if e["proveedor_id"] == pid]
    if not envs:
        continue
    ranking.append({
        "proveedor": pnom, "material": pmat, "origen": origen, "distancia_km": dist,
        "envios": len(envs), "volumen": round(sum(e["cant_real"] for e in envs), 0),
        "unidad": "t" if pmat == "Arena" else "m3",
        "otif": pct(sum(1 for e in envs if e["estado"] == "OTIF"), len(envs)),
        "lead_dias": round(statistics.mean(e["lead_real_dias"] for e in envs), 1),
        "retraso_dias": round(statistics.mean(e["retraso_dias"] for e in envs), 2),
        "costo_log_usd": round(sum(e["costo_flete_usd"] + e["costo_demora_usd"] for e in envs), 0),
    })
ranking.sort(key=lambda r: r["otif"], reverse=True)

hist = []
lt_arena = [e["lead_real_dias"] for e in entregas if e["familia"] == "Arena"]
for lo, hi in [(0, 2), (3, 4), (5, 6), (7, 8), (9, 11), (12, 99)]:
    hist.append({"rango": f"{lo}-{hi}" if hi < 99 else f"{lo}+",
                 "n": sum(1 for x in lt_arena if lo <= x <= hi)})

rutas = {}
for e in entregas:
    k = (e["origen"], e["proveedor"], e["distancia_km"])
    r = rutas.setdefault(k, {"origen": e["origen"], "proveedor": e["proveedor"],
                             "distancia_km": e["distancia_km"], "envios": 0, "costo_flete_usd": 0.0})
    r["envios"] += 1
    r["costo_flete_usd"] += e["costo_flete_usd"]
rutas_lista = sorted(rutas.values(), key=lambda r: r["costo_flete_usd"], reverse=True)
for r in rutas_lista:
    r["costo_prom_envio_usd"] = round(r["costo_flete_usd"] / r["envios"], 0)
    r["costo_flete_usd"] = round(r["costo_flete_usd"], 0)

# Mezcla arena + gasoil para que "ultimos envios" no quede dominado por un solo material.
rec_a = sorted([e for e in entregas if e["familia"] == "Arena"], key=lambda e: e["fecha_real"], reverse=True)[:6]
rec_g = sorted([e for e in entregas if e["familia"] == "Gasoil"], key=lambda e: e["fecha_real"], reverse=True)[:6]
recientes = [{"folio": e["folio"], "fecha_real": e["fecha_real"], "material": e["material"],
              "proveedor": e["proveedor"], "pad": e["pad"], "cant_real": e["cant_real"],
              "unidad": e["unidad"], "retraso_dias": e["retraso_dias"], "estado": e["estado"]}
             for e in sorted(rec_a + rec_g, key=lambda e: e["fecha_real"], reverse=True)]

datos = {
    "meta": {"generado": HOY.isoformat(), "periodo": f"{serie_meses[0]} a {serie_meses[-1]}",
             "meses": MESES, "envios": tot, "pads": len(PADS),
             "proveedores": len(PROVEEDORES), "sets_fractura": SETS_FRACTURA},
    "kpis": {"arena_total_t": round(arena_total, 0), "gasoil_total_m3": round(gasoil_total, 0),
             "otif_pct": pct(otif, tot), "a_tiempo_pct": pct(a_tiempo, tot),
             "fill_rate_pct": pct(completos, tot), "lead_prom_dias": round(statistics.mean(lead_reales), 1),
             "retraso_prom_dias": round(statistics.mean(retrasos), 1) if retrasos else 0,
             "cobertura_dias": cobertura_dias, "dias_quiebre": dias_quiebre,
             "dias_bajo_seguridad": dias_bajo_seg, "costo_logistico_usd": round(costo_logistico, 0),
             "costo_total_usd": round(costo_total, 0), "standby_usd": round(standby_usd, 0),
             "costo_log_por_t": round(costo_logistico / arena_total, 1) if arena_total else 0},
    "serie": {"meses": serie_meses, "arena_t": [r["arena_consumo_t"] for r in consumo_rows],
              "gasoil_m3": [r["gasoil_consumo_m3"] for r in consumo_rows], "otif_pct": otif_mes},
    "stock": {"fechas": [r["fecha"] for r in stock_rows], "stock_t": [r["stock_arena_t"] for r in stock_rows],
              "seguridad_t": STOCK_SEGURIDAD_T, "objetivo_t": NIVEL_OBJETIVO_T,
              "quiebres": [i for i, r in enumerate(stock_rows) if r["quiebre"]]},
    "costo_desglose": [
        {"concepto": "Arena (material)", "usd": round(mat_arena_cost, 0)},
        {"concepto": "Gasoil (material)", "usd": round(mat_gasoil_cost, 0)},
        {"concepto": "Transporte / flete", "usd": round(costo_flete, 0)},
        {"concepto": "Almacenamiento", "usd": round(costo_almacen, 0)},
        {"concepto": "Demoras (demurrage)", "usd": round(costo_demora, 0)},
        {"concepto": "Standby por quiebre", "usd": round(standby_usd, 0)}],
    "ranking": ranking, "hist_lead": hist, "rutas": rutas_lista, "recientes": recientes,
}

# ----------------------------------------------------------------------------
# Escritura CSV (estrella) + JSON
# ----------------------------------------------------------------------------
def escribir_csv(nombre, filas, columnas):
    with open(DATA / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        for fila in filas:
            w.writerow({c: fila.get(c, "") for c in columnas})


escribir_csv("dim_proveedor.csv", [{"proveedor_id": p[0], "proveedor": p[1], "material": p[2],
             "origen": p[3], "distancia_km": p[4], "confiabilidad": p[5], "lead_base_dias": p[6]} for p in PROVEEDORES],
             ["proveedor_id", "proveedor", "material", "origen", "distancia_km", "confiabilidad", "lead_base_dias"])
escribir_csv("dim_pad.csv", [{"pad_id": p[0], "pad": p[1], "operadora": p[2]} for p in PADS],
             ["pad_id", "pad", "operadora"])
escribir_csv("dim_material.csv", [{"material_id": m[0], "material": m[1], "unidad": m[2],
             "precio_unit_usd": m[3]} for m in MATERIALES], ["material_id", "material", "unidad", "precio_unit_usd"])
escribir_csv("dim_fecha.csv", [{"fecha": d.isoformat(), "anio": d.year, "mes": d.month,
             "mes_clave": clave_mes(d), "dia": d.day} for d in DIAS], ["fecha", "anio", "mes", "mes_clave", "dia"])
escribir_csv("fact_entregas.csv", entregas,
             ["folio", "material_id", "material", "familia", "unidad", "proveedor_id", "proveedor", "origen",
              "distancia_km", "pad_id", "pad", "operadora", "mes", "fecha_orden", "fecha_plan", "fecha_real",
              "lead_plan_dias", "lead_real_dias", "retraso_dias", "cant_plan", "cant_real",
              "costo_material_usd", "costo_flete_usd", "costo_demora_usd", "estado"])
escribir_csv("fact_stock.csv", stock_rows,
             ["fecha", "stock_arena_t", "consumo_t", "recepcion_t", "stock_seguridad_t", "quiebre"])
escribir_csv("fact_consumo.csv", consumo_rows,
             ["mes", "arena_consumo_t", "gasoil_consumo_m3", "sets_activos", "etapas_estimadas"])

with open(WEB / "datos.json", "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))

print("OK simulacion")
print(f"  envios: {tot}  |  arena: {arena_total:,.0f} t  |  gasoil: {gasoil_total:,.0f} m3")
print(f"  OTIF: {datos['kpis']['otif_pct']}%  lead: {datos['kpis']['lead_prom_dias']} d  "
      f"quiebre: {dias_quiebre} d  bajo seguridad: {dias_bajo_seg} d")
print(f"  stock min/max: {min(serie_stock):,.0f} / {max(serie_stock):,.0f} t  cobertura: {cobertura_dias} d")
print(f"  costo logistico: US$ {costo_logistico:,.0f}  ({datos['kpis']['costo_log_por_t']} US$/t)")
