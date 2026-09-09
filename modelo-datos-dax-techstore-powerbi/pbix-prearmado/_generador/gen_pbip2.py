"""Parte 2: Dim_Fechas, _Medidas, model, relaciones, .platform, .pbip, report."""
import os, uuid, json

BASE = "/home/user/portfolio/modelo-datos-dax-techstore-powerbi/pbix-prearmado"
NAME = "Murphy_Lleyton_Checkpoint2"
SM = f"{BASE}/{NAME}.SemanticModel"
RP = f"{BASE}/{NAME}.Report"
os.makedirs(f"{SM}/definition/tables", exist_ok=True)
os.makedirs(RP, exist_ok=True)

def w(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ---------------------------------------------------------------- Dim_Fechas (calculada)
dim_fechas = """table Dim_Fechas
\tdataCategory: Time

\tcolumn Date
\t\tdataType: dateTime
\t\tisKey
\t\tsourceColumn: [Date]
\t\tsummarizeBy: none

\tcolumn 'Año' = YEAR(Dim_Fechas[Date])
\t\tdataType: int64
\t\tsummarizeBy: none

\tcolumn 'Mes Número' = MONTH(Dim_Fechas[Date])
\t\tdataType: int64
\t\tsummarizeBy: none

\tcolumn 'Mes Nombre' = FORMAT(Dim_Fechas[Date], "MMMM")
\t\tdataType: string
\t\tsortByColumn: 'Mes Número'
\t\tsummarizeBy: none

\tcolumn 'Trimestre' = "T" & QUARTER(Dim_Fechas[Date])
\t\tdataType: string
\t\tsummarizeBy: none

\tcolumn 'Semana' = WEEKNUM(Dim_Fechas[Date])
\t\tdataType: int64
\t\tsummarizeBy: none

\tpartition Dim_Fechas = calculated
\t\tmode: import
\t\tsource = CALENDAR(MIN(Fact_Ventas[fecha_venta]), MAX(Fact_Ventas[fecha_venta]))
"""
w(f"{SM}/definition/tables/Dim_Fechas.tmdl", dim_fechas)

# ---------------------------------------------------------------- _Medidas (medidas)
medidas = r'''table '_Medidas'

	column Col
		dataType: int64
		isHidden
		sourceColumn: [Col]
		summarizeBy: none

	measure 'Total Ventas' = SUM(Fact_Ventas[total_venta])
		formatString: #,##0.00

	measure 'Ventas Online' = CALCULATE([Total Ventas], Fact_Ventas[canal] = "Online")
		formatString: #,##0.00

	measure 'Ventas YTD' = TOTALYTD([Total Ventas], Dim_Fechas[Date])
		formatString: #,##0.00

	measure 'Ventas LY' = CALCULATE([Total Ventas], SAMEPERIODLASTYEAR(Dim_Fechas[Date]))
		formatString: #,##0.00

	measure '% Crecimiento Anual' = ```
			VAR VentasActual = [Total Ventas]
			VAR VentasAnterior = [Ventas LY]
			RETURN
			    DIVIDE(VentasActual - VentasAnterior, VentasAnterior)
			```
		formatString: 0.00%;-0.00%;0.00%

	partition '_Medidas' = calculated
		mode: import
		source = ROW("Col", 1)
'''
w(f"{SM}/definition/tables/_Medidas.tmdl", medidas)

# ---------------------------------------------------------------- relationships
def rel():
    return str(uuid.uuid4())
relationships = f"""relationship {rel()}
\tfromColumn: Fact_Ventas.id_cliente
\ttoColumn: Dim_Clientes.id_cliente

relationship {rel()}
\tfromColumn: Fact_Ventas.id_producto
\ttoColumn: Dim_Productos.id_producto

relationship {rel()}
\tfromColumn: Fact_Ventas.fecha_venta
\ttoColumn: Dim_Fechas.Date

relationship {rel()}
\tfromColumn: Dim_Productos.categoria
\ttoColumn: Dim_Categorias.nombre_categoria
"""
w(f"{SM}/definition/relationships.tmdl", relationships)

# ---------------------------------------------------------------- model / database
model = """model Model
\tculture: es-ES
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tdiscourageImplicitMeasures
\tsourceQueryCulture: es-ES

ref table Dim_Categorias
ref table Dim_Clientes
ref table Dim_Productos
ref table Fact_Ventas
ref table Dim_Fechas
ref table '_Medidas'
"""
w(f"{SM}/definition/model.tmdl", model)
w(f"{SM}/definition/database.tmdl", "database\n\tcompatibilityLevel: 1567\n")

# ---------------------------------------------------------------- pbism / platform
w(f"{SM}/definition.pbism", json.dumps({"version": "4.2", "settings": {}}, indent=2))

def platform(kind, name):
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": name},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
    }, indent=2)
w(f"{SM}/.platform", platform("SemanticModel", NAME))
w(f"{RP}/.platform", platform("Report", NAME))

# ---------------------------------------------------------------- report
w(f"{RP}/definition.pbir", json.dumps({
    "version": "4.0",
    "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}, "byConnection": None},
}, indent=2))

section_name = str(uuid.uuid4())
report_json = {
    "config": json.dumps({"version": "5.43", "activeSectionIndex": 0, "layoutOptimization": 0}),
    "layoutOptimization": 0,
    "publicCustomVisuals": [],
    "resourcePackages": [],
    "sections": [{
        "config": "{}",
        "displayName": "Validación",
        "displayOption": 1,
        "filters": "[]",
        "height": 720.0,
        "name": section_name,
        "visualContainers": [],
        "width": 1280.0,
    }],
    "filters": "[]",
}
w(f"{RP}/report.json", json.dumps(report_json, indent=2))

# ---------------------------------------------------------------- .pbip
w(f"{BASE}/{NAME}.pbip", json.dumps({
    "version": "1.0",
    "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
    "settings": {"enableAutoRecovery": True},
}, indent=2))

print("PBIP generado en", BASE)
for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        print(os.path.relpath(os.path.join(root, f), BASE))
