import csv, sqlite3, datetime

# ---- Cargar Global Superstore (Kaggle) ----
rows=[]
with open("global_superstore.csv", encoding="utf-8-sig") as f:
    r=csv.DictReader(f)
    for d in r: rows.append(d)
print("filas crudas:", len(rows))

def parse_date(s):
    s=s.strip()
    for fmt in ("%m/%d/%Y","%d/%m/%Y","%Y-%m-%d"):
        try: return datetime.datetime.strptime(s,fmt).date()
        except: pass
    return None

# ---- Limpieza ----
clean=[]
bad=0
for d in rows:
    dt=parse_date(d["Order Date"])
    try: sales=round(float(d["Sales"]),2)
    except: sales=None
    cid=(d["Customer ID"] or "").strip()
    cname=(d["Customer Name"] or "").strip()
    if not dt or sales is None or not cid or not cname:
        bad+=1; continue
    clean.append({"order_id":d["Order ID"].strip(),"id_cliente":cid,"nombre_cliente":cname,
                  "segmento":d["Segment"].strip(),"ciudad":d["City"].strip(),"pais":d["Country"].strip(),
                  "fecha_compra":dt.isoformat(),"total_venta":sales})
print("descartadas (nulos/fechas invalidas):", bad, "| limpias:", len(clean))

# ---- Separar en dos entidades: clientes y ventas ----
clientes={}
for c in clean:
    clientes.setdefault(c["id_cliente"],{"id_cliente":c["id_cliente"],"nombre_cliente":c["nombre_cliente"],
        "segmento":c["segmento"],"ciudad":c["ciudad"],"pais":c["pais"]})
print("clientes unicos:", len(clientes))

con=sqlite3.connect(":memory:"); cur=con.cursor()
cur.execute("CREATE TABLE clientes(id_cliente TEXT PRIMARY KEY, nombre_cliente TEXT, segmento TEXT, ciudad TEXT, pais TEXT)")
cur.executemany("INSERT INTO clientes VALUES(?,?,?,?,?)",[(v["id_cliente"],v["nombre_cliente"],v["segmento"],v["ciudad"],v["pais"]) for v in clientes.values()])
cur.execute("CREATE TABLE ventas(order_id TEXT, id_cliente TEXT, fecha_compra TEXT, total_venta REAL)")
cur.executemany("INSERT INTO ventas VALUES(?,?,?,?)",[(c["order_id"],c["id_cliente"],c["fecha_compra"],c["total_venta"]) for c in clean])
con.commit()

maxf=cur.execute("SELECT MAX(fecha_compra) FROM ventas").fetchone()[0]
minf=cur.execute("SELECT MIN(fecha_compra) FROM ventas").fetchone()[0]
print("rango fechas:", minf, "->", maxf)

q="""
SELECT c.nombre_cliente AS cliente,
       v.fecha_compra    AS fecha_compra,
       v.total_venta     AS total
FROM ventas v
JOIN clientes c ON c.id_cliente = v.id_cliente
WHERE v.fecha_compra >= date((SELECT MAX(fecha_compra) FROM ventas), '-30 day')
ORDER BY v.fecha_compra DESC;
"""
res=cur.execute(q).fetchall()
print("\nEJ1 filas ultimos 30 dias:", len(res))
for row in res[:15]: print(row)
# guardar resultado para el screenshot
import json
json.dump({"rows":res,"maxf":maxf,"minf":minf,"n_clean":len(clean),"n_cli":len(clientes),"bad":bad,"n_raw":len(rows)}, open("kaggle_res.json","w"))
