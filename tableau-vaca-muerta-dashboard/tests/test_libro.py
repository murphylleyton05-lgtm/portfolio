"""Controles del dataset y del libro de Tableau (sin Tableau ni red)."""

import csv
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import generar_twb  # noqa: E402

CSV = RAIZ / "data" / "vaca_muerta_operadores_mensual.csv"


def filas():
    with CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_csv_cuadra_con_el_titular():
    ult = [f for f in filas() if f["Mes"] == "2025-12-01"]
    oil = sum(int(f["Petroleo_bbl_d"]) for f in ult)
    ant = sum(int(f["Petroleo_bbl_d_anio_anterior"]) for f in ult)
    ypf = sum(int(f["Petroleo_bbl_d"]) for f in ult if f["Operador"] == "YPF")
    assert round(oil / 1000) == 602
    assert round((oil / ant - 1) * 100) == 32          # "creció 32%"
    assert ypf / oil > 0.5                              # "más de la mitad"


def test_dona_tiene_seis_segmentos_como_maximo():
    formula = generar_twb.CALC["Calc_Grupo"][5]
    grupos = set(re.findall(r"THEN '([^']+)'", formula)) | set(re.findall(r"ELSE '([^']+)'", formula))
    assert len(grupos) <= 6


def test_libro_consistente():
    root = ET.fromstring(generar_twb.workbook().encode("utf-8"))
    hojas = {w.get("name") for w in root.iter("worksheet")}
    zonas = {z.get("name") for z in root.iter("zone") if z.get("name")}
    assert zonas == hojas
    accion = root.find("actions/action")
    assert accion.find("activation").get("type") == "on-select"
    assert accion.find("source").get("worksheet") in hojas
    # Eje doble con ejes sincronizados.
    eje = next(w for w in root.iter("worksheet") if w.get("name").startswith("Eje doble"))
    enc = eje.find("table/style/style-rule/encoding")
    assert enc.get("fold") == "true" and enc.get("synchronized") == "true"


def test_twbx_empaquetado():
    twbx = RAIZ / "tableau" / f"{generar_twb.NOMBRE}.twbx"
    nombres = zipfile.ZipFile(twbx).namelist()
    assert f"{generar_twb.NOMBRE}.twb" in nombres
    assert "Data/data/vaca_muerta_operadores_mensual.csv" in nombres
    assert sum(n.startswith("Image/icono_") for n in nombres) == 4
