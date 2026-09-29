"""Arma el CSV para Tableau (formato largo: mes x operador) desde datos.json de vaca-muerta-ops-intelligence."""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ORIGEN = RAIZ.parent / "vaca-muerta-ops-intelligence" / "web" / "datos.json"
DESTINO = RAIZ / "data" / "vaca_muerta_operadores_mensual.csv"

datos = json.loads(ORIGEN.read_text(encoding="utf-8"))
meses = datos["serie"]["meses"]

with DESTINO.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Mes", "Operador", "Petroleo_bbl_d", "Gas_miles_m3_d", "Pozos_activos"])
    for op in datos["operadores_serie"]:
        for i, mes in enumerate(meses):
            w.writerow([f"{mes}-01", op["operador"].title() if op["operador"] != "YPF" else "YPF",
                        round(op["oil_bbl_d"][i]), round(op["gas_mm3_d"][i]), int(op["activos"][i])])

print(f"{DESTINO.name}: {len(meses) * len(datos['operadores_serie'])} filas ({meses[0]} a {meses[-1]})")
