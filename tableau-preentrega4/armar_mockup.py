"""Genera mockup.html (referencia visual del dashboard de Tableau) con los datos reales del CSV."""
import csv
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
filas = list(csv.DictReader((RAIZ / "data" / "vaca_muerta_operadores_mensual.csv").open(encoding="utf-8")))

AZUL, AMBAR, GRIS = "#1F3A5F", "#E8A33D", "#9AA5B1"
META = 500_000

total, gas, pozos = defaultdict(float), defaultdict(float), defaultdict(float)
for f in filas:
    total[f["Mes"]] += float(f["Petroleo_bbl_d"])
    gas[f["Mes"]] += float(f["Gas_miles_m3_d"])
    pozos[f["Mes"]] += float(f["Pozos_activos"])
meses = sorted(total)
ult = meses[-1]
pico_mes = max(meses, key=total.get)
caida = total[ult] / total[pico_mes] - 1

# Línea central
W, H, PX, PY = 700, 260, 50, 20
ymax = 650_000
def x(i): return PX + i * (W - PX - 10) / (len(meses) - 1)
def y(v): return PY + (H - 2 * PY) * (1 - v / ymax)
segs = []
for i in range(1, len(meses)):
    c = AZUL if total[meses[i]] >= META else AMBAR
    segs.append(f'<line x1="{x(i-1):.1f}" y1="{y(total[meses[i-1]]):.1f}" x2="{x(i):.1f}" y2="{y(total[meses[i]]):.1f}" stroke="{c}" stroke-width="3" stroke-linecap="round"/>')
ip = meses.index(pico_mes)
ejes = "".join(f'<text x="{x(i):.1f}" y="{H-2}" font-size="11" fill="#6B7684" text-anchor="{"end" if i == len(meses) - 1 else "middle"}">{m[:7]}</text>'
               for i, m in enumerate(meses) if i % 6 == 0 or i == len(meses) - 1)
grilla = "".join(f'<line x1="{PX}" x2="{W-10}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#EEF0F3"/><text x="{PX-6}" y="{y(v)+4:.1f}" font-size="11" fill="#6B7684" text-anchor="end">{v//1000}k</text>'
                 for v in range(0, ymax + 1, 200_000))
linea = f'''<svg viewBox="0 0 {W} {H}" width="100%">{grilla}
<line x1="{PX}" x2="{W-10}" y1="{y(META):.1f}" y2="{y(META):.1f}" stroke="{GRIS}" stroke-dasharray="6 4" stroke-width="1.5"/>
<text x="{PX+6}" y="{y(META)-6:.1f}" font-size="11" fill="#6B7684">Meta 500k (parámetro)</text>
{''.join(segs)}
<circle cx="{x(ip):.1f}" cy="{y(total[pico_mes]):.1f}" r="5" fill="{AZUL}"/>
<text x="{x(ip)-8:.1f}" y="{y(total[pico_mes])-10:.1f}" font-size="12" font-weight="600" fill="{AZUL}" text-anchor="end">Récord {pico_mes[:7]}: {total[pico_mes]/1000:.0f} mil bbl/d</text>
<circle cx="{x(len(meses)-1):.1f}" cy="{y(total[ult]):.1f}" r="5" fill="{AMBAR}"/>
{ejes}</svg>'''

# Ranking Top 5
ops = sorted(((f["Operador"], float(f["Petroleo_bbl_d"])) for f in filas if f["Mes"] == ult and f["Operador"] != "Otras"),
             key=lambda t: -t[1])[:5]
mx = ops[0][1]
barras = "".join(f'''<div class="bar"><span class="lab">{n}</span><div class="track"><div style="width:{v/mx*100:.0f}%;background:{AMBAR if n=="YPF" else GRIS}"></div></div><span class="val">{v/1000:.0f}k</span></div>''' for n, v in ops)

# Detalle últimos 6 meses
ult6 = meses[-6:]
por = defaultdict(dict)
for f in filas:
    if f["Mes"] in ult6:
        por[f["Operador"]][f["Mes"]] = float(f["Petroleo_bbl_d"])
orden = sorted(por, key=lambda o: -por[o][ult])[:6]
vmax = max(max(por[o].values()) for o in orden)
def celda(v):
    a = 0.12 + 0.88 * (v / vmax) ** 0.5
    return f'<td style="background:rgba(31,58,95,{a:.2f});color:{"#fff" if a > .5 else "#1F2933"}">{v/1000:.0f}k</td>'
tabla = "<tr><th>Operador</th>" + "".join(f"<th>{m[:7]}</th>" for m in ult6) + "</tr>" + "".join(
    f"<tr><td class='op'>{o}</td>{''.join(celda(por[o][m]) for m in ult6)}</tr>" for o in orden)

ypf = [f for f in filas if f["Operador"] == "YPF"]
ypf_d = {f["Mes"]: float(f["Petroleo_bbl_d"]) for f in ypf}
share = (ypf_d[pico_mes] - ypf_d[ult]) / (total[pico_mes] - total[ult])

def n(v): return f"{v:,.0f}".replace(",", ".")

html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Mockup Vaca Muerta</title>
<style>
body{{margin:0;background:#F7F8FA;font-family:"Segoe UI",Arial,sans-serif;color:#1F2933}}
.dash{{width:1200px;padding:16px;box-sizing:border-box}}
.hdr{{display:flex;align-items:center;gap:14px;margin-bottom:12px}}
.hdr svg{{flex:none}}
h1{{font-size:24px;margin:0;color:{AZUL}}} .sub{{font-size:13px;color:#6B7684;margin-top:2px}}
.card{{background:#fff;border-radius:8px;padding:12px 16px;box-shadow:0 1px 2px rgba(0,0,0,.06)}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px}}
.kl{{font-size:12px;color:#6B7684;text-transform:uppercase;letter-spacing:.04em}}
.kv{{font-size:30px;font-weight:700;color:{AZUL}}} .kv.alerta{{color:{AMBAR}}}
.params{{display:flex;gap:12px;margin-bottom:12px;font-size:12px}}
.params .card{{padding:8px 12px;flex:1}} .params b{{color:{AZUL}}}
.mid{{display:grid;grid-template-columns:1.6fr 1fr;gap:12px;margin-bottom:12px}}
h2{{font-size:14px;margin:0 0 8px;color:#1F2933}}
.ins{{font-size:13px;margin-top:6px}} .ins b{{color:{AMBAR}}}
.bar{{display:flex;align-items:center;gap:8px;margin:12px 0;font-size:12px}}
.lab{{width:130px;text-align:right}} .track{{flex:1;height:18px}} .track div{{height:100%;border-radius:3px}} .val{{width:40px}}
table{{border-collapse:collapse;width:100%;font-size:12px}} th{{text-align:center;color:#6B7684;font-weight:600;padding:4px}}
td{{text-align:center;padding:6px;border:2px solid #fff}} td.op{{text-align:left;background:none}}
.foot{{font-size:11px;color:#6B7684;margin-top:8px}}
.tag{{display:inline-block;font-size:10px;color:#fff;border-radius:3px;padding:1px 6px;margin-left:6px;vertical-align:middle}}
</style></head><body><div class="dash">
<div class="hdr">
<svg width="44" height="44" viewBox="0 0 64 64" fill="none" stroke="{AZUL}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" aria-label="ícono (reemplazar por el de Flaticon)">
<path d="M8 20 L40 10 L44 18 L12 28 Z"/><path d="M26 22 L20 54 M26 22 L34 54 M16 54 H40"/><circle cx="26" cy="21" r="3"/><path d="M42 16 V44 M38 44 H50 V54 H38 Z"/></svg>
<div><h1>Vaca Muerta: del récord a la caída — la producción bajó {abs(caida)*100:.0f} % desde {pico_mes[:7]}</h1>
<div class="sub">Producción no convencional por operador · Secretaría de Energía · {meses[0][:7]} a {ult[:7]}</div></div></div>
<div class="kpis">
<div class="card"><div class="kl">Petróleo · bbl/d</div><div class="kv">{n(total[ult])}</div></div>
<div class="card"><div class="kl">Gas · miles m³/d</div><div class="kv">{n(gas[ult])}</div></div>
<div class="card"><div class="kl">Pozos activos</div><div class="kv">{n(pozos[ult])}</div></div>
<div class="card"><div class="kl">Caída desde el pico</div><div class="kv alerta">{caida*100:.0f} %</div></div></div>
<div class="params">
<div class="card">P · Métrica: <b>Petróleo (bbl/d) ▾</b></div>
<div class="card">P · Meta de producción: <b>500.000</b> ——●——</div>
<div class="card">P · Top N operadores: <b>5</b> ——●——</div>
<div class="card">P · Meses a mostrar: <b>6</b> ——●——</div></div>
<div class="mid">
<div class="card"><h2>Producción mensual de Petróleo (bbl/d) <span class="tag" style="background:{AZUL}">sobre meta</span><span class="tag" style="background:{AMBAR}">bajo meta</span></h2>{linea}
<div class="ins"><b>YPF explica el {share*100:.0f} % de la caída:</b> pasó de {ypf_d[pico_mes]/1000:.0f} a {ypf_d[ult]/1000:.0f} mil bbl/d.</div></div>
<div class="card"><h2>Top 5 operadores · {ult[:7]}</h2>{barras}</div></div>
<div class="card"><h2>Detalle: petróleo por operador (bbl/d), últimos 6 meses</h2><table>{tabla}</table></div>
<div class="foot">Mockup de referencia para el dashboard en Tableau Public · Ícono: Flaticon (reemplazar el placeholder) · Paleta: azul {AZUL} principal · ámbar {AMBAR} alerta · gris {GRIS} contexto</div>
</div></body></html>'''
(RAIZ / "mockup.html").write_text(html, encoding="utf-8")
print("mockup.html OK", pico_mes, f"{caida:.3f}", f"share YPF {share:.3f}")
