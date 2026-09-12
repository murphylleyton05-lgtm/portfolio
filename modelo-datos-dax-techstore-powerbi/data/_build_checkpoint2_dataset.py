"""
Genera Checkpoint2_TechStore.xlsx: 4 tablas YA LIMPIAS, listas para importar
en Power BI con una carga simple (sin merges ni transformaciones).

Decisiones para evitar el error de "referencia cíclica" / relaciones automaticas:
  - Fact_Ventas NO lleva nombre_producto ni categoria (evita que Power BI
    invente una relacion Fact->Dim_Categorias y arme un bucle).
  - Dim_Clientes NO lleva canal (evita una segunda relacion Fact->Dim_Clientes).
"""
import random
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

HEADER = Font(bold=True)

def add_sheet(wb, name, headers, rows):
    ws = wb.create_sheet(title=name)
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        ws.cell(row=1, column=c).font = HEADER
    for r in rows:
        ws.append(r)
    for i, h in enumerate(headers, start=1):
        width = max([len(str(h))] + [len(str(r[i-1])) for r in rows if r[i-1] is not None])
        ws.column_dimensions[get_column_letter(i)].width = min(width + 3, 34)
    ws.freeze_panes = "A2"
    return ws

wb = Workbook()
wb.remove(wb.active)

# ------------------------------------------------------------ Dim_Categorias
categorias = [
    (1, "Notebooks"), (2, "Perifericos"), (3, "Componentes"), (4, "Smartphones"),
]
add_sheet(wb, "Dim_Categorias", ["id_categoria", "nombre_categoria"],
          [list(c) for c in categorias])

# ------------------------------------------------------------ Dim_Clientes (11 limpios)
clientes = [
    (1,  "Martin Gomez",    "mgomez@mail.com",     "Buenos Aires", "Argentina", date(2023,1,15)),
    (2,  "Lucia Fernandez", "lfernandez@mail.com", "Cordoba",      "Argentina", date(2023,2,3)),
    (3,  "Carlos Rojas",    "Sin dato",            "Santiago",     "Chile",     date(2023,2,20)),
    (4,  "Ana Torres",      "atorres@mail.com",    "Sin dato",     "Mexico",    date(2023,3,11)),
    (5,  "Diego Morales",   "dmorales@mail.com",   "Lima",         "Peru",      date(2023,4,5)),
    (6,  "Sofia Castro",    "scastro@mail.com",    "Bogota",       "Colombia",  date(2023,5,19)),
    (7,  "Javier Nunez",    "jnunez@mail.com",     "Montevideo",   "Uruguay",   date(2023,6,22)),
    (8,  "Valentina Ruiz",  "vruiz@mail.com",      "Guadalajara",  "Mexico",    date(2023,7,30)),
    (9,  "Mateo Silva",     "msilva@mail.com",     "Rosario",      "Argentina", date(2023,8,14)),
    (10, "Camila Vargas",   "cvargas@mail.com",    "Quito",        "Ecuador",   date(2023,9,25)),
    (11, "Nicolas Herrera", "nherrera@mail.com",   "Asuncion",     "Paraguay",  date(2023,10,8)),
]
add_sheet(wb, "Dim_Clientes",
          ["id_cliente", "nombre_cliente", "email", "ciudad", "pais", "fecha_registro"],
          [list(c) for c in clientes])

# ------------------------------------------------------------ Dim_Productos (12 limpios)
productos = [
    (101, "Notebook Lenovo IdeaPad",  "Notebooks",     850.00, 620.00, 15, 1),
    (102, "Notebook HP Pavilion",     "Notebooks",     920.50, 680.00, 10, 1),
    (103, "Mouse Logitech M170",      "Perifericos",    12.99,   6.50, 120, 1),
    (104, "Teclado Redragon K552",    "Perifericos",    45.00,  25.00,  60, 1),
    (105, "Monitor Samsung 24",       "Perifericos",   189.99, 140.00,  25, 1),
    (106, "SSD Kingston 480GB",       "Componentes",    39.90,  22.00,  80, 1),
    (107, "RAM Corsair 8GB",          "Componentes",     0.00,  30.00,  40, 1),
    (108, "Motherboard ASUS B450",    "Componentes",   110.00,  78.00,  18, 1),
    (109, "Samsung Galaxy A54",       "Smartphones",   399.00, 300.00,  22, 1),
    (110, "Xiaomi Redmi Note 12",     "Smartphones",   249.00, 180.00,  30, 1),
    (111, "Auriculares HyperX Cloud", "Sin Categoria",  79.99,  45.00,  35, 1),
    (112, "Webcam Logitech C920",     "Perifericos",    89.90,  55.00,  12, 1),
]
add_sheet(wb, "Dim_Productos",
          ["id_producto", "nombre_producto", "categoria", "precio", "costo", "stock", "activo"],
          [list(p) for p in productos])

# ------------------------------------------------------------ Fact_Ventas (50, misma semilla que M6)
random.seed(2024)
precio_por_prod = {101:850.00,102:920.50,103:12.99,104:45.00,105:189.99,106:39.90,
                   107:95.00,108:110.00,109:399.00,110:249.00,111:79.99,112:89.90}
prod_ids = list(precio_por_prod.keys())
canales = ["Online", "Tienda"]
start = date(2023, 1, 10)
ventas = []
for i in range(1, 51):
    fecha  = start + timedelta(days=random.randint(0, 700))
    id_cli = random.randint(1, 11)
    id_pro = random.choice(prod_ids)
    cant   = random.randint(1, 5)
    punit  = precio_por_prod[id_pro]
    desc   = round(random.choice([0, 0, 0, 0.05, 0.10]) * punit * cant, 2)
    total  = round(punit * cant - desc, 2)
    ventas.append([i, fecha, id_cli, id_pro, cant, punit, desc, total,
                   random.choice(canales)])

add_sheet(wb, "Fact_Ventas",
          ["id_venta", "fecha_venta", "id_cliente", "id_producto", "cantidad",
           "precio_unitario", "descuento", "total_venta", "canal"],
          ventas)

# orden de hojas: dimensiones primero, hechos al final
orden = ["Dim_Categorias", "Dim_Clientes", "Dim_Productos", "Fact_Ventas"]
wb._sheets.sort(key=lambda s: orden.index(s.title))

out = "/home/user/portfolio/modelo-datos-dax-techstore-powerbi/data/Checkpoint2_TechStore.xlsx"
wb.save(out)

fechas = [v[1] for v in ventas]
print("OK ->", out)
print("Dim_Categorias:", len(categorias), "| Dim_Clientes:", len(clientes),
      "| Dim_Productos:", len(productos), "| Fact_Ventas:", len(ventas))
print("rango fechas:", min(fechas), "->", max(fechas))
print("total_venta:", round(sum(v[7] for v in ventas), 2))
print("anios:", sorted({f.year for f in fechas}))
