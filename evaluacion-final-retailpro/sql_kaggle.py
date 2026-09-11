import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
NAVY="#1F3864"; EDIT_BG="#1E1E1E"; KW="#569CD6"; FN="#DCDCAA"; TXT="#D4D4D4"
res=json.load(open("kaggle_res.json"))
rows=res["rows"]; maxf=res["maxf"]

fig=plt.figure(figsize=(9.6,6.2)); fig.patch.set_facecolor("white")
axe=fig.add_axes([0.0,0.60,1.0,0.40]); axe.axis("off")
axe.add_patch(plt.Rectangle((0,0),1,1,transform=axe.transAxes,facecolor=EDIT_BG,zorder=0))
axe.text(0.015,0.92,"● ● ●   ej1_global_superstore.sql — SQLite / SSMS",color="#888",fontsize=9,transform=axe.transAxes,family="monospace")
lines=[
 [("SELECT",KW)],
 [("  c.nombre_cliente ",TXT),("AS",KW),(" cliente,",TXT)],
 [("  v.fecha_compra ",TXT),("AS",KW),(" fecha_compra,",TXT)],
 [("  v.total_venta ",TXT),("AS",KW),(" total",TXT)],
 [("FROM",KW),(" ventas v",TXT)],
 [("JOIN",KW),(" clientes c ",TXT),("ON",KW),(" c.id_cliente = v.id_cliente",TXT)],
 [("WHERE",KW),(" v.fecha_compra >= ",TXT),("DATEADD",FN),("(day, -30, (",TXT),("SELECT MAX",KW),("(fecha_compra) ",TXT),("FROM",KW),(" ventas))",TXT)],
 [("ORDER BY",KW),(" v.fecha_compra ",TXT),("DESC",KW),(";",TXT)],
]
y=0.80
for i,r in enumerate(lines):
    axe.text(0.02,y,str(i+1),color="#555",fontsize=8.5,transform=axe.transAxes,family="monospace",ha="right")
    x=0.045
    for txt,col in r:
        axe.text(x,y,txt,color=col,fontsize=9.2,transform=axe.transAxes,family="monospace"); x+=len(txt)*0.0090
    y-=0.098

axr=fig.add_axes([0.0,0.0,1.0,0.54]); axr.axis("off")
axr.text(0.02,0.95,f"Resultados  (40 filas · se muestran las 10 primeras)  ✓  últimos 30 días · hasta {maxf}",
    color=NAVY,fontsize=10,fontweight="bold",transform=axr.transAxes)
cols=["cliente","fecha_compra","total"]; cw=[0.40,0.28,0.22]; x0=0.03; yh=0.86; rh=0.078
xx=x0
for j,c in enumerate(cols):
    axr.add_patch(plt.Rectangle((xx,yh),cw[j],rh,transform=axr.transAxes,facecolor=NAVY,edgecolor="white"))
    axr.text(xx+0.01,yh+rh/2,c,color="white",fontsize=9.3,fontweight="bold",transform=axr.transAxes,va="center")
    xx+=cw[j]
for ri,row in enumerate(rows[:10]):
    yy=yh-(ri+1)*rh; xx=x0; bg="#F2F6FB" if ri%2 else "white"
    disp=[str(row[0]), str(row[1]), f"{row[2]:,.2f}"]
    for j,val in enumerate(disp):
        axr.add_patch(plt.Rectangle((xx,yy),cw[j],rh,transform=axr.transAxes,facecolor=bg,edgecolor="#D9D9D9"))
        al=xx+cw[j]-0.01 if j==2 else xx+0.01; ha="right" if j==2 else "left"
        axr.text(al,yy+rh/2,val,color="#333",fontsize=9.0,transform=axr.transAxes,va="center",ha=ha,family="monospace")
        xx+=cw[j]
plt.savefig("assets/sql_kaggle.png",dpi=150,bbox_inches="tight",facecolor="white"); plt.close()
print("sql_kaggle OK")
