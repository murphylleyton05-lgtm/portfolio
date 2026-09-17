"""Pruebas del generador de Frac Logistics (consumo real + logística modelada)."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PROC = RAIZ.parent / "vaca-muerta-analytics" / "data" / "procesado" / "ajustes_declinacion.parquet"


@pytest.fixture(scope="module")
def datos():
    if not PROC.exists():
        pytest.skip("faltan los parquets procesados")
    subprocess.run([sys.executable, "scripts/construir_datos.py"], cwd=RAIZ, check=True)
    return json.loads((RAIZ / "web" / "datos.json").read_text(encoding="utf-8"))


def test_estructura(datos):
    for clave in ("meta", "kpis", "serie", "stock", "costo_desglose", "ranking", "rutas"):
        assert clave in datos


def test_consumo_real_positivo(datos):
    k = datos["kpis"]
    assert k["arena_total_t"] > 0
    assert k["agua_total_m3"] > 0
    assert k["etapas"] > 0


def test_otif_en_rango(datos):
    otif = datos["kpis"]["otif_pct"]
    assert 0 <= otif <= 100
    assert all(0 <= x <= 100 for x in datos["serie"]["otif_pct"])


def test_stock_alineado_y_no_negativo(datos):
    st = datos["stock"]
    assert len(st["fechas"]) == len(st["stock_t"])
    assert min(st["stock_t"]) >= 0, "el stock no puede ser negativo"
    assert all(0 <= i < len(st["fechas"]) for i in st["quiebres"])


def test_costo_desglose_finito(datos):
    for fila in datos["costo_desglose"]:
        assert math.isfinite(fila["usd"]) and fila["usd"] >= 0


def test_serie_arena_alineada(datos):
    s = datos["serie"]
    assert len(s["meses"]) == len(s["arena_t"]) == len(s["gasoil_m3"])
