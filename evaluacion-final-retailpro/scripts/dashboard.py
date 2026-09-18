import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json

SC = "/tmp/claude-0/-home-user-portfolio/4c309c01-0fb3-591e-b34d-06bb0c3dc912/scratchpad/"
d = json.load(open(SC + "agg.json"))

NAVY="#1F3864"; ACCENT="#2E74B5"; LIGHT="#8FB4DD"; GREY="#595959"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#CCCCCC"})

fig = plt.figure(figsize=(11, 6.6), dpi=140)
fig.patch.set_facecolor("#F4F6FA")
gs = GridSpec(3, 3, figure=fig, height_ratios=[0.5, 1, 1], hspace=0.55, wspace=0.3,
              left=0.06, right=0.97, top=0.9, bottom=0.08)

fig.text(0.06, 0.955, "RetailPro — Panel de Ventas (TechStore)", fontsize=15,
         fontweight="bold", color=NAVY)
fig.text(0.06, 0.925, "Fuente: Fact_Ventas (50 operaciones depuradas) · 2023–2024", fontsize=8.5, color=GREY)

# ---- KPI row ----
kpis = [
    ("Total Ventas", f"${d['total']:,.0f}"),
    ("Ticket típico (mediana)", "$370"),
    ("Ticket promedio", "$528"),
    ("N.º de ventas", str(d["n"])),
]
# manual KPI cards
ax0 = fig.add_axes([0.06, 0.74, 0.91, 0.13]); ax0.axis("off")
for i,(lab,val) in enumerate(kpis):
    x = i/4
    ax0.add_patch(plt.Rectangle((x+0.005, 0.05), 0.24-0.01, 0.9, transform=ax0.transAxes,
                  facecolor="white", edgecolor="#D6E0F0", linewidth=1.2))
    ax0.text(x+0.12, 0.66, val, transform=ax0.transAxes, ha="center", va="center",
             fontsize=16, fontweight="bold", color=NAVY)
    ax0.text(x+0.12, 0.26, lab, transform=ax0.transAxes, ha="center", va="center",
             fontsize=8.5, color=GREY)

# ---- Ventas por categoria (barh) ----
ax1 = fig.add_subplot(gs[1, 0])
cat = {k:v for k,v in d["por_cat"].items() if k!="Sin categoria"}
cats = sorted(cat, key=cat.get)
ax1.barh(cats, [cat[c] for c in cats], color=ACCENT)
ax1.set_title("Ventas por categoría", fontsize=10, fontweight="bold", color=NAVY, loc="left")
ax1.tick_params(labelsize=7.5)
for s in ["top","right"]: ax1.spines[s].set_visible(False)

# ---- Tendencia mensual (line) ----
ax2 = fig.add_subplot(gs[1, 1:])
mes = d["por_mes"]
xs = list(mes.keys()); ys = list(mes.values())
ax2.plot(range(len(xs)), ys, color=NAVY, linewidth=2, marker="o", markersize=3)
ax2.fill_between(range(len(xs)), ys, color=LIGHT, alpha=0.3)
ax2.set_title("Tendencia mensual de ventas", fontsize=10, fontweight="bold", color=NAVY, loc="left")
step=max(1,len(xs)//7)
ax2.set_xticks(range(0,len(xs),step)); ax2.set_xticklabels([xs[i] for i in range(0,len(xs),step)], rotation=45, fontsize=7, ha="right")
ax2.tick_params(labelsize=7.5)
for s in ["top","right"]: ax2.spines[s].set_visible(False)

# ---- Ventas por canal (donut) ----
ax3 = fig.add_subplot(gs[2, 0])
canal=d["por_canal"]
w,_,_=ax3.pie(list(canal.values()), labels=list(canal.keys()), autopct="%1.0f%%",
        colors=[ACCENT, LIGHT], startangle=90, textprops={"fontsize":8},
        wedgeprops={"width":0.42})
ax3.set_title("Ventas por canal", fontsize=10, fontweight="bold", color=NAVY, loc="left")

# ---- Distribucion / outliers note (hist) ----
ax4 = fig.add_subplot(gs[2, 1:])
import openpyxl
wb=openpyxl.load_workbook("/home/user/portfolio/pipeline-etl-techstore-powerbi/data/Pipeline_ETL_Dataset.xlsx", data_only=True)
vh=[c.value for c in wb["ventas"][1]]; idx=vh.index("total_venta")
vals=[float(r[idx]) for r in wb["ventas"].iter_rows(min_row=2, values_only=True) if r[idx] is not None]
ax4.hist(vals, bins=15, color=ACCENT, edgecolor="white")
ax4.axvline(528.46, color="#C00000", linestyle="--", linewidth=1.5, label="Media 528")
ax4.axvline(370.01, color="#1F7A1F", linestyle="--", linewidth=1.5, label="Mediana 370")
ax4.axvline(1580.08, color="#888888", linestyle=":", linewidth=1.2, label="Límite outlier 1.580")
ax4.set_title("Distribución del ticket (media vs. mediana)", fontsize=10, fontweight="bold", color=NAVY, loc="left")
ax4.legend(fontsize=7, loc="upper right"); ax4.tick_params(labelsize=7.5)
for s in ["top","right"]: ax4.spines[s].set_visible(False)

out = SC + "dashboard.png"
plt.savefig(out, dpi=140, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("WROTE", out)
