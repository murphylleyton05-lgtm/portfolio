"""
Genera un proyecto Power BI (.pbip) YA ARMADO para el Checkpoint 2:
- 5 tablas con datos embebidos (M inline, sin Excel externo -> no cuelga al refrescar)
- Dim_Fechas como tabla calculada (CALENDAR) + columnas + marcada como tabla de fechas
- _Medidas con las 5 medidas DAX
- 4 relaciones 1:N direccion unica
- 1 pagina de reporte "Validacion" (vacia, para agregar la matriz a mano)

Salida: modelo-datos-dax-techstore-powerbi/pbix-prearmado/
"""
import os, random, uuid, json
from datetime import date, timedelta

BASE = "/home/user/portfolio/modelo-datos-dax-techstore-powerbi/pbix-prearmado"
NAME = "Murphy_Lleyton_Checkpoint2"
SM = f"{BASE}/{NAME}.SemanticModel"
RP = f"{BASE}/{NAME}.Report"

# ---------------------------------------------------------------- datos limpios
categorias = [
    (1, "Notebooks"), (2, "Perifericos"), (3, "Componentes"), (4, "Smartphones"),
]

clientes = [  # 11 limpios (dedup id 3, nulos -> "Sin dato")
    (1,  "Martin Gomez",    "mgomez@mail.com",     "Buenos Aires", "Argentina", date(2023,1,15), "Online"),
    (2,  "Lucia Fernandez", "lfernandez@mail.com", "Cordoba",      "Argentina", date(2023,2,3),  "Tienda"),
    (3,  "Carlos Rojas",    "Sin dato",            "Santiago",     "Chile",     date(2023,2,20), "Online"),
    (4,  "Ana Torres",      "atorres@mail.com",    "Sin dato",     "Mexico",    date(2023,3,11), "Online"),
    (5,  "Diego Morales",   "dmorales@mail.com",   "Lima",         "Peru",      date(2023,4,5),  "Tienda"),
    (6,  "Sofia Castro",    "scastro@mail.com",    "Bogota",       "Colombia",  date(2023,5,19), "Online"),
    (7,  "Javier Nunez",    "jnunez@mail.com",     "Montevideo",   "Uruguay",   date(2023,6,22), "Tienda"),
    (8,  "Valentina Ruiz",  "vruiz@mail.com",      "Guadalajara",  "Mexico",    date(2023,7,30), "Online"),
    (9,  "Mateo Silva",     "msilva@mail.com",     "Rosario",      "Argentina", date(2023,8,14), "Online"),
    (10, "Camila Vargas",   "cvargas@mail.com",    "Quito",        "Ecuador",   date(2023,9,25), "Tienda"),
    (11, "Nicolas Herrera", "nherrera@mail.com",   "Asuncion",     "Paraguay",  date(2023,10,8), "Online"),
]

productos = [  # 12 limpios (dedup id 103, precio nulo->0, categoria nula->"Sin Categoria")
    (101, "Notebook Lenovo IdeaPad",  "Notebooks",     850.00, 620.00, 15, 1),
    (102, "Notebook HP Pavilion",     "Notebooks",     920.50, 680.00, 10, 1),
    (103, "Mouse Logitech M170",      "Perifericos",   12.99,  6.50,  120, 1),
    (104, "Teclado Redragon K552",    "Perifericos",   45.00,  25.00,  60, 1),
    (105, "Monitor Samsung 24",       "Perifericos",   189.99, 140.00, 25, 1),
    (106, "SSD Kingston 480GB",       "Componentes",   39.90,  22.00,  80, 1),
    (107, "RAM Corsair 8GB",          "Componentes",   0.00,   30.00,  40, 1),
    (108, "Motherboard ASUS B450",    "Componentes",   110.00, 78.00,  18, 1),
    (109, "Samsung Galaxy A54",       "Smartphones",   399.00, 300.00, 22, 1),
    (110, "Xiaomi Redmi Note 12",     "Smartphones",   249.00, 180.00, 30, 1),
    (111, "Auriculares HyperX Cloud", "Sin Categoria", 79.99,  45.00,  35, 1),
    (112, "Webcam Logitech C920",     "Perifericos",   89.90,  55.00,  12, 1),
]
prod_nombre = {p[0]: p[1] for p in productos}
prod_categoria = {p[0]: p[2] for p in productos}

# ventas: mismo seed/logica que _build_dataset.py -> 50 filas identicas
random.seed(2024)
precio_por_prod = {101:850.00,102:920.50,103:12.99,104:45.00,105:189.99,106:39.90,
                   107:95.00,108:110.00,109:399.00,110:249.00,111:79.99,112:89.90}
prod_ids = list(precio_por_prod.keys())
canales = ["Online", "Tienda"]
start = date(2023,1,10)
ventas = []
for i in range(1,51):
    fecha = start + timedelta(days=random.randint(0,700))
    id_cli = random.randint(1,11)
    id_prod = random.choice(prod_ids)
    cant = random.randint(1,5)
    punit = precio_por_prod[id_prod]
    desc = round(random.choice([0,0,0,0.05,0.10])*punit*cant, 2)
    total = round(punit*cant - desc, 2)
    ventas.append([i, fecha, id_cli, id_prod, cant, punit, desc, total,
                   random.choice(canales), prod_nombre[id_prod], prod_categoria[id_prod]])

# ---------------------------------------------------------------- helpers M
def mstr(s):  # escapa string para M
    return '"' + str(s).replace('"', '""') + '"'

def mdate(d):
    return f"#date({d.year}, {d.month}, {d.day})"

def m_table(cols_types, rows):
    # cols_types: list of (name, mtype)  ; rows: list of list of M-literals
    hdr = ", ".join(f"{n} = {t}" for n, t in cols_types)
    body = ",\n            ".join(
        "{" + ", ".join(r) + "}" for r in rows
    )
    return (
        "let\n"
        "    Source = #table(\n"
        f"        type table [{hdr}],\n"
        "        {\n"
        f"            {body}\n"
        "        }\n"
        "    )\n"
        "in\n"
        "    Source"
    )

os.makedirs(f"{SM}/definition/tables", exist_ok=True)
os.makedirs(f"{RP}", exist_ok=True)

# ---------------------------------------------------------------- tablas M
def col(name, dtype, fmt=None, cat=None):
    lines = [f"\tcolumn {ident(name)}", f"\t\tdataType: {dtype}",
             f"\t\tsourceColumn: {name}"]
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    if cat:
        lines.append(f"\t\tdataCategory: {cat}")
    lines.append("\t\tsummarizeBy: none" if dtype in ("string","dateTime") else "\t\tsummarizeBy: sum")
    return "\n".join(lines)

def ident(n):
    return f"'{n}'" if (" " in n) else n

def table_tmdl(name, columns, partition_m):
    parts = [f"table {name}", ""]
    for c in columns:
        parts.append(c)
        parts.append("")
    parts.append(f"\tpartition {name} = m")
    parts.append("\t\tmode: import")
    parts.append("\t\tsource =")
    for ln in partition_m.split("\n"):
        parts.append("\t\t\t" + ln if ln else "")
    parts.append("")
    return "\n".join(parts) + "\n"

# Dim_Categorias
cat_cols = [col("id_categoria","int64"), col("nombre_categoria","string")]
cat_m = m_table([("id_categoria","Int64.Type"),("nombre_categoria","text")],
                [[str(c[0]), mstr(c[1])] for c in categorias])
open(f"{SM}/definition/tables/Dim_Categorias.tmdl","w").write(table_tmdl("Dim_Categorias", cat_cols, cat_m))

# Dim_Clientes
cli_cols = [col("id_cliente","int64"), col("nombre_cliente","string"),
            col("email","string"), col("ciudad","string"), col("pais","string"),
            col("fecha_registro","dateTime"), col("canal","string")]
cli_m = m_table([("id_cliente","Int64.Type"),("nombre_cliente","text"),("email","text"),
                 ("ciudad","text"),("pais","text"),("fecha_registro","date"),("canal","text")],
                [[str(c[0]),mstr(c[1]),mstr(c[2]),mstr(c[3]),mstr(c[4]),mdate(c[5]),mstr(c[6])] for c in clientes])
open(f"{SM}/definition/tables/Dim_Clientes.tmdl","w").write(table_tmdl("Dim_Clientes", cli_cols, cli_m))

# Dim_Productos
prod_cols = [col("id_producto","int64"), col("nombre_producto","string"),
             col("categoria","string"), col("precio","double"), col("costo","double"),
             col("stock","int64"), col("activo","int64")]
prod_m = m_table([("id_producto","Int64.Type"),("nombre_producto","text"),("categoria","text"),
                  ("precio","number"),("costo","number"),("stock","Int64.Type"),("activo","Int64.Type")],
                 [[str(p[0]),mstr(p[1]),mstr(p[2]),repr(p[3]),repr(p[4]),str(p[5]),str(p[6])] for p in productos])
open(f"{SM}/definition/tables/Dim_Productos.tmdl","w").write(table_tmdl("Dim_Productos", prod_cols, prod_m))

# Fact_Ventas
fact_cols = [col("id_venta","int64"), col("fecha_venta","dateTime"),
             col("id_cliente","int64"), col("id_producto","int64"), col("cantidad","int64"),
             col("precio_unitario","double"), col("descuento","double"),
             col("total_venta","double"), col("canal","string"),
             col("nombre_producto","string"), col("categoria","string")]
fact_m = m_table([("id_venta","Int64.Type"),("fecha_venta","date"),("id_cliente","Int64.Type"),
                  ("id_producto","Int64.Type"),("cantidad","Int64.Type"),("precio_unitario","number"),
                  ("descuento","number"),("total_venta","number"),("canal","text"),
                  ("nombre_producto","text"),("categoria","text")],
                 [[str(v[0]),mdate(v[1]),str(v[2]),str(v[3]),str(v[4]),repr(v[5]),
                   repr(v[6]),repr(v[7]),mstr(v[8]),mstr(v[9]),mstr(v[10])] for v in ventas])
open(f"{SM}/definition/tables/Fact_Ventas.tmdl","w").write(table_tmdl("Fact_Ventas", fact_cols, fact_m))

print("tablas M OK")
print("ventas[0]:", ventas[0])
print("ventas[49]:", ventas[49])
print("total ventas:", round(sum(v[7] for v in ventas),2))
