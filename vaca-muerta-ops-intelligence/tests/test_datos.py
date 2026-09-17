"""Pruebas del generador de datos de Operations Intelligence.

Corren contra los parquets procesados (demo local o reales en CI): ejecutan
construir_datos.py y validan la estructura y los rangos del datos.json.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PROC = RAIZ.parent / "vaca-muerta-analytics" / "data" / "procesado" / "produccion.parquet"


@pytest.fixture(scope="module")
def datos():
    if not PROC.exists():
        pytest.skip("faltan los parquets procesados (correr el pipeline de vaca-muerta-analytics)")
    subprocess.run([sys.executable, "scripts/construir_datos.py"], cwd=RAIZ, check=True)
    return json.loads((RAIZ / "web" / "datos.json").read_text(encoding="utf-8"))


def test_estructura(datos):
    for clave in ("meta", "kpis", "serie", "operadores", "operadores_serie", "ventanas", "pozos_top"):
        assert clave in datos, f"falta {clave}"


def test_kpis_finitos_y_positivos(datos):
    k = datos["kpis"]
    for campo in ("oil_bbl_d", "gas_mm3_d", "acum_mmbbl"):
        assert math.isfinite(k[campo]) and k[campo] > 0
    assert 0 < k["pozos_activos"] <= k["pozos_total"]


def test_series_alineadas(datos):
    s = datos["serie"]
    n = len(s["meses"])
    for campo in ("oil_bbl_d", "gas_mm3_d", "activos", "acum_mmbbl", "nuevos"):
        assert len(s[campo]) == n, f"{campo} desalineada"


def test_acumulado_no_decrece(datos):
    ac = datos["serie"]["acum_mmbbl"]
    assert all(b >= a - 1e-6 for a, b in zip(ac, ac[1:])), "el acumulado debería ser monótono"


def test_series_por_operadora_suman_al_total(datos):
    """La suma de las operadoras debe reconstruir la serie total (±1%)."""
    s = datos["serie"]
    ops = datos["operadores_serie"]
    for i in range(len(s["meses"])):
        suma = sum(o["oil_bbl_d"][i] for o in ops)
        assert suma == pytest.approx(s["oil_bbl_d"][i], rel=0.01, abs=1.0)
