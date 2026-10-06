"""
Arma el dataset para Tableau a partir de los datos oficiales ya procesados.

Fuente: ../vaca-muerta-ops-intelligence/web/datos.json (produccion oficial de
pozos no convencionales, Secretaria de Energia), serie por operador.

Salida: data/vaca_muerta_operadores_mensual.csv, una fila por mes x operador.

Se corta en 2025-12 a proposito: desde 2026-01 el padron de pozos del dataset
no registra pozos nuevos (pozos nuevos = 0 ocho meses seguidos), asi que la
produccion de 2026 solo refleja la declinacion de los pozos viejos y daria una
caida que no es real.
"""

import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ.parent / "vaca-muerta-ops-intelligence" / "web" / "datos.json"
DESTINO = RAIZ / "data" / "vaca_muerta_operadores_mensual.csv"
ULTIMO_MES = "2025-12"


def main() -> None:
    datos = json.loads(ORIGEN.read_text(encoding="utf-8"))
    meses = datos["serie"]["meses"]
    fin = meses.index(ULTIMO_MES)

    filas = []
    for op in datos["operadores_serie"]:
        if not any(op["oil_bbl_d"][: fin + 1]):
            continue  # operador sin produccion en la ventana analizada
        nombre = "OTRAS (resto)" if op["operador"] == "Otras" else op["operador"]
        for i in range(fin + 1):
            ant = i - 12
            filas.append({
                "Mes": f"{meses[i]}-01",
                "Operador": nombre,
                "Petroleo_bbl_d": round(op["oil_bbl_d"][i]),
                "Petroleo_bbl_d_anio_anterior": round(op["oil_bbl_d"][ant]) if ant >= 0 else "",
                "Gas_Mm3_d": round(op["gas_mm3_d"][i], 2),
                "Pozos_activos": op["activos"][i],
            })

    # Control: la suma por operador tiene que dar el total oficial de cada mes.
    for i in range(fin + 1):
        suma = sum(f["Petroleo_bbl_d"] for f in filas if f["Mes"] == f"{meses[i]}-01")
        assert abs(suma - datos["serie"]["oil_bbl_d"][i]) <= 11, (meses[i], suma)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} filas -> {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
