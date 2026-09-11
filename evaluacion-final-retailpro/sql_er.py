import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY="#1F3864"; BLUE="#2E74B5"; EDIT_BG="#1E1E1E"; KW="#569CD6"; STR="#CE9178"; FN="#DCDCAA"; COM="#6A9955"; TXT="#D4D4D4"

# ---------------- SQL "screenshot": editor panel + result grid ----------------
sql_lines=[
 ("SELECT",KW,0),("  c.nombre_cliente AS cliente,",TXT,0),
 ("  v.fecha_venta       AS fecha_compra,",TXT,0),
 ("  v.total_venta       AS total",TXT,0),
 ("FROM ventas v",[("FROM",KW),(" ventas v",TXT)],0),
 ("JOIN clientes c ON c.id_cliente = v.id_cliente",[("JOIN",KW),(" clientes c ",TXT),("ON",KW),(" c.id_cliente = v.id_cliente",TXT)],0),
 ("WHERE v.fecha_venta >= DATEADD(day,-30,(SELECT MAX(fecha_venta) FROM ventas))",[("WHERE",KW),(" v.fecha_venta >= ",TXT),("DATEADD",FN),("(day,-30,(",TXT),("SELECT MAX",KW),("(fecha_venta) ",TXT),("FROM",KW),(" ventas))",TXT)],0),
 ("ORDER BY v.fecha_venta DESC;",[("ORDER BY",KW),(" v.fecha_venta ",TXT),("DESC",KW),(";",TXT)],0),
]
fig=plt.figure(figsize=(9.4,4.9)); fig.patch.set_facecolor("white")
# editor
axe=fig.add_axes([0.0,0.52,1.0,0.48]); axe.axis("off"); axe.set_facecolor(EDIT_BG)
axe.add_patch(plt.Rectangle((0,0),1,1,transform=axe.transAxes,facecolor=EDIT_BG,zorder=0))
axe.text(0.015,0.92,"● ● ●   consulta_ej1.sql — SQLite / SSMS",color="#888",fontsize=9,transform=axe.transAxes,family="monospace")
rows=[
 [("SELECT",KW)],
 [("  c.nombre_cliente ",TXT),("AS",KW),(" cliente,",TXT)],
 [("  v.fecha_venta ",TXT),("AS",KW),(" fecha_compra,",TXT)],
 [("  v.total_venta ",TXT),("AS",KW),(" total",TXT)],
 [("FROM",KW),(" ventas v",TXT)],
 [("JOIN",KW),(" clientes c ",TXT),("ON",KW),(" c.id_cliente = v.id_cliente",TXT)],
 [("WHERE",KW),(" v.fecha_venta >= ",TXT),("DATEADD",FN),("(day, -30, (",TXT),("SELECT MAX",KW),("(fecha_venta) ",TXT),("FROM",KW),(" ventas))",TXT)],
 [("ORDER BY",KW),(" v.fecha_venta ",TXT),("DESC",KW),(";",TXT)],
]
y=0.80
for i,r in enumerate(rows):
    axe.text(0.02,y,str(i+1),color="#555",fontsize=8.5,transform=axe.transAxes,family="monospace",ha="right")
    x=0.045
    for txt,col in r:
        axe.text(x,y,txt,color=col,fontsize=9.3,transform=axe.transAxes,family="monospace")
        x+=len(txt)*0.0092
    y-=0.098
# result grid
axr=fig.add_axes([0.0,0.0,1.0,0.46]); axr.axis("off")
axr.text(0.02,0.93,"Resultados  (3 filas)  ✓  últimos 30 días · hasta 2024-11-08",color=NAVY,fontsize=10,fontweight="bold",transform=axr.transAxes)
cols=["cliente","fecha_compra","total"]
data=[["Carlos Rojas","2024-11-08","758.10"],["Ana Torres","2024-10-31","209.00"],["Carlos Rojas","2024-10-22","399.00"]]
cw=[0.34,0.30,0.24]; x0=0.03; yh=0.72
xx=x0
for j,cname in enumerate(cols):
    axr.add_patch(plt.Rectangle((xx,yh),cw[j],0.16,transform=axr.transAxes,facecolor=NAVY,edgecolor="white"))
    axr.text(xx+0.01,yh+0.08,cname,color="white",fontsize=9.5,fontweight="bold",transform=axr.transAxes,va="center")
    xx+=cw[j]
for ri,row in enumerate(data):
    yy=yh-(ri+1)*0.16; xx=x0
    bg="#F2F6FB" if ri%2 else "white"
    for j,val in enumerate(row):
        axr.add_patch(plt.Rectangle((xx,yy),cw[j],0.16,transform=axr.transAxes,facecolor=bg,edgecolor="#D9D9D9"))
        al = xx+cw[j]-0.01 if j==2 else xx+0.01
        ha = "right" if j==2 else "left"
        axr.text(al,yy+0.08,val,color="#333",fontsize=9.3,transform=axr.transAxes,va="center",ha=ha,family="monospace")
        xx+=cw[j]
plt.savefig("assets/sql.png",dpi=150,bbox_inches="tight",facecolor="white"); plt.close()

# ---------------- ER diagram (star schema) ----------------
fig,ax=plt.subplots(figsize=(9.2,5.3)); ax.axis("off"); ax.set_xlim(0,10); ax.set_ylim(0,10)
def entity(x,y,title,fields,pk=None,fk=(),color=BLUE,w=2.5):
    h=0.5+0.42*len(fields)
    ax.add_patch(FancyBboxPatch((x,y-h),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",
        facecolor="white",edgecolor=color,linewidth=2,zorder=3))
    ax.add_patch(plt.Rectangle((x,y-0.5),w,0.5,facecolor=color,edgecolor=color,zorder=4))
    ax.text(x+w/2,y-0.25,title,ha="center",va="center",color="white",fontweight="bold",fontsize=11,zorder=5)
    for i,f in enumerate(fields):
        fy=y-0.5-0.42*(i+0.5)
        style="italic" if f in fk else "normal"
        weight="bold" if f==pk else "normal"
        tag=" (PK)" if f==pk else (" (FK)" if f in fk else "")
        col = NAVY if f==pk else ("#1F6F6D" if f in fk else "#333")
        ax.text(x+0.14,fy,f+tag,ha="left",va="center",fontsize=8.7,style=style,fontweight=weight,color=col,zorder=5)
    return (x,y,w,h)

fact=entity(3.75,7.2,"Ventas (hechos)",
    ["id_venta","fecha_venta","id_cliente","id_producto","cantidad","precio_unitario","descuento","total_venta","canal"],
    pk="id_venta",fk=("id_cliente","id_producto","fecha_venta"),color=NAVY,w=2.9)
cli=entity(0.4,9.6,"Clientes",["id_cliente","nombre_cliente","email","ciudad","pais","canal"],pk="id_cliente",color=BLUE)
prod=entity(7.1,9.6,"Productos",["id_producto","nombre_producto","categoria","precio","costo","stock"],pk="id_producto",fk=("categoria",),color=BLUE)
cat=entity(7.4,3.0,"Categorias",["id_categoria","nombre_categoria"],pk="id_categoria",color="#8064A2",w=2.2)
fec=entity(0.5,4.3,"Fechas (calendario)",["Date","Año","Mes","Trimestre","Semana"],pk="Date",color="#2CA6A4",w=2.6)

def rel(p1,p2,l1off,lNoff):
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-",color="#999",linewidth=1.6,zorder=1))
    ax.text(p1[0]+l1off[0],p1[1]+l1off[1],"1",fontsize=11,color=NAVY,fontweight="bold",zorder=6)
    ax.text(p2[0]+lNoff[0],p2[1]+lNoff[1],"N",fontsize=11,color=NAVY,fontweight="bold",zorder=6)
rel((2.9,7.7),(4.05,7.15),(0.05,0.12),(-0.28,0.02))    # clientes -> ventas
rel((7.1,7.7),(6.62,7.15),(-0.15,0.12),(0.12,0.02))    # productos -> ventas
rel((3.1,4.55),(3.78,5.15),(0.05,0.14),(-0.34,-0.02))   # fechas -> ventas
rel((7.7,3.0),(7.35,7.85),(0.12,0.05),(-0.30,0.02))    # categorias -> productos
ax.text(5,0.35,"Esquema en estrella (con rama snowflake Categorías → Productos)  ·  (PK) clave primaria   (FK) clave foránea  ·  relaciones 1:N de dirección única",
    ha="center",fontsize=8.6,color="#555")
plt.savefig("assets/er.png",dpi=150,bbox_inches="tight",facecolor="white"); plt.close()
print("sql + er OK")
