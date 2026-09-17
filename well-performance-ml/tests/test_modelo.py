"""Pruebas del modelo de Well Performance ML.

Ejecuta construir_datos.py (entrena regresión lineal + random forest) y valida
que las métricas sean números finitos y coherentes.
"""
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
    for clave in ("meta", "kpis", "modelo", "scatter_rama", "ventanas", "top"):
        assert clave in datos


def test_split_train_test(datos):
    m = datos["meta"]
    assert m["n_train"] > 0 and m["n_test"] > 0
    assert m["n_train"] + m["n_test"] == m["pozos"]


def test_metricas_finitas(datos):
    """El bug real que rompió CI: R²/MAPE salían NaN. Esto lo blinda."""
    mo = datos["modelo"]
    for campo in ("r2_diseno", "r2_geo", "mape", "rf_r2_diseno", "rf_r2_geo"):
        v = mo[campo]
        assert isinstance(v, (int, float)) and math.isfinite(v), f"{campo} no es finito: {v}"


def test_geologia_aporta(datos):
    """El hallazgo central: sumar la geología explica más que el diseño solo."""
    mo = datos["modelo"]
    assert mo["r2_geo"] >= mo["r2_diseno"] - 1e-9


def test_coeficientes_completos(datos):
    coefs = datos["modelo"]["coefs"]
    assert len(coefs) == 6  # las 6 variables de diseño
    assert all(math.isfinite(c["peso"]) for c in coefs)


def test_pred_vs_real_no_vacio(datos):
    pvr = datos["modelo"]["pred_vs_real"]
    assert len(pvr) == datos["meta"]["n_test"]
    assert all(p["real"] > 0 and math.isfinite(p["pred"]) for p in pvr)
