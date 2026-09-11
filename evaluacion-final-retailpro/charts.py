import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import matplotlib.font_manager as fm

d = json.load(open("agg.json"))
NAVY="#1F3864"; BLUE="#2E74B5"; TEAL="#2CA6A4"; AMBER="#E4A93C"; RED="#C0504D"; GREY="#666666"
CAT=[BLUE, TEAL, AMBER, "#8064A2", RED, "#9BB7D4"]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.edgecolor":"#CCCCCC",
    "axes.linewidth":0.8,"axes.grid":True,"grid.color":"#EEEEEE","grid.linewidth":0.8})
def money(x): return f"${x:,.0f}".replace(",", ".")
def clean(ax):
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

# ---------- 1. KPI cards ----------
fig,ax=plt.subplots(figsize=(9.2,1.7)); ax.axis("off")
cards=[("Total Ventas",money(d["total_ventas"]),NAVY),
       ("N.º de Ventas",str(d["n_ventas"]),BLUE),
       ("Ticket Promedio",money(d["ticket_prom"]),AMBER),
       ("Ticket Mediano",money(d["ticket_med"]),TEAL),
       ("Crecim. Anual",f'{d["crec"]:.1f}%',RED)]
w=1/len(cards)
for i,(t,v,c) in enumerate(cards):
    x=i*w+0.01
    ax.add_patch(FancyBboxPatch((x,0.08),w-0.02,0.84,boxstyle="round,pad=0.01,rounding_size=0.03",
        transform=ax.transAxes,facecolor="white",edgecolor=c,linewidth=2))
    ax.add_patch(Rectangle((x,0.78),w-0.02,0.14,transform=ax.transAxes,facecolor=c,edgecolor="none"))
    ax.text(x+(w-0.02)/2,0.85,t,transform=ax.transAxes,ha="center",va="center",color="white",fontsize=10,fontweight="bold")
    ax.text(x+(w-0.02)/2,0.42,v,transform=ax.transAxes,ha="center",va="center",color=c,fontsize=17,fontweight="bold")
plt.savefig("assets/kpi.png",dpi=150,bbox_inches="tight",facecolor="white"); plt.close()

# ---------- 2. Ventas por mes ----------
fig,ax=plt.subplots(figsize=(9.2,3.0))
meses=[m for m,_ in d["por_mes"]]; vals=[v for _,v in d["por_mes"]]
cols=[BLUE if m.startswith("2023") else TEAL for m in meses]
ax.bar(range(len(meses)),vals,color=cols)
ax.set_xticks(range(len(meses))); ax.set_xticklabels(meses,rotation=60,ha="right",fontsize=8)
ax.set_ylabel("Ventas (USD)"); ax.yaxis.set_major_formatter(lambda x,_:money(x))
clean(ax)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BLUE,label="2023"),Patch(color=TEAL,label="2024")],frameon=False,loc="upper right")
ax.set_title("Evolución mensual de ventas (2023–2024)",loc="left",fontweight="bold",color=NAVY,fontsize=12)
plt.tight_layout(); plt.savefig("assets/ventas_mes.png",dpi=150,facecolor="white"); plt.close()

# ---------- 3. Por categoria ----------
fig,ax=plt.subplots(figsize=(4.5,2.9))
cat=[c for c,_ in d["por_cat"]][::-1]; cv=[v for _,v in d["por_cat"]][::-1]
ax.barh(cat,cv,color=BLUE); clean(ax); ax.grid(axis="y")
ax.xaxis.set_major_formatter(lambda x,_:money(x))
for i,v in enumerate(cv): ax.text(v,i,f" {money(v)}",va="center",fontsize=8,color=GREY)
ax.set_title("Ventas por categoría",loc="left",fontweight="bold",color=NAVY,fontsize=12)
plt.tight_layout(); plt.savefig("assets/categoria.png",dpi=150,facecolor="white"); plt.close()

# ---------- 4. Canal donut ----------
fig,ax=plt.subplots(figsize=(4.5,2.9))
lab=[c for c,_,_ in d["por_canal"]]; cv=[v for _,v,_ in d["por_canal"]]
w,_,at=ax.pie(cv,labels=lab,autopct=lambda p:f"{p:.0f}%",colors=[BLUE,AMBER],
    wedgeprops=dict(width=0.42,edgecolor="white"),pctdistance=0.78,textprops={"fontsize":10})
ax.text(0,0,f'{money(sum(cv))}\nTotal',ha="center",va="center",fontsize=10,fontweight="bold",color=NAVY)
ax.set_title("Ventas por canal",loc="left",fontweight="bold",color=NAVY,fontsize=12)
plt.tight_layout(); plt.savefig("assets/canal.png",dpi=150,facecolor="white"); plt.close()

# ---------- 5. Por pais ----------
fig,ax=plt.subplots(figsize=(4.5,2.9))
pa=[c for c,_ in d["por_pais"]][::-1]; pv=[v for _,v in d["por_pais"]][::-1]
ax.barh(pa,pv,color=TEAL); clean(ax); ax.grid(axis="y")
ax.xaxis.set_major_formatter(lambda x,_:money(x))
ax.set_title("Ventas por país",loc="left",fontweight="bold",color=NAVY,fontsize=12)
plt.tight_layout(); plt.savefig("assets/pais.png",dpi=150,facecolor="white"); plt.close()

# ---------- 6. Distribucion ticket (EDA + validacion) ----------
fig,ax=plt.subplots(figsize=(9.2,3.0))
ax.hist(d["dist"],bins=18,color=BLUE,alpha=0.85,edgecolor="white")
ax.axvline(d["ticket_prom"],color=RED,linewidth=2,label=f'Media {money(d["ticket_prom"])}')
ax.axvline(d["ticket_med"],color=TEAL,linewidth=2,linestyle="--",label=f'Mediana {money(d["ticket_med"])}')
ax.axvline(1580.08,color=GREY,linewidth=1.5,linestyle=":",label="Límite IQR 1.580")
clean(ax); ax.set_xlabel("total_venta (USD)"); ax.set_ylabel("Frecuencia")
ax.legend(frameon=False,fontsize=9)
ax.set_title("Distribución del ticket: sesgo a la derecha (4 outliers legítimos)",loc="left",fontweight="bold",color=NAVY,fontsize=12)
plt.tight_layout(); plt.savefig("assets/dist.png",dpi=150,facecolor="white"); plt.close()

# ---------- 7. Top clientes ----------
fig,ax=plt.subplots(figsize=(4.5,2.9))
tc=[c for c,_ in d["top_cli"]][::-1]; tv=[v for _,v in d["top_cli"]][::-1]
ax.barh(tc,tv,color=NAVY); clean(ax); ax.grid(axis="y")
ax.xaxis.set_major_formatter(lambda x,_:money(x))
ax.set_title("Top 6 clientes por facturación",loc="left",fontweight="bold",color=NAVY,fontsize=12)
plt.tight_layout(); plt.savefig("assets/topcli.png",dpi=150,facecolor="white"); plt.close()

print("charts OK")
