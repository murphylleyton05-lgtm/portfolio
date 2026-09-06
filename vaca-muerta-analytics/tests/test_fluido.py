"""
Tests de la clasificacion por ventana de fluido.

Lo que se protege: que el GOR se calcule bien (unidades correctas, division por
cero manejada) y que los cortes de ventana caigan donde deben. Un error de
unidades aca clasificaria pozos de petroleo como gas y arruinaria toda la
separacion.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import fluido  # noqa: E402


# --- calculo del GOR ------------------------------------------------------

def test_gor_convierte_bien_las_unidades():
    """
    El gas viene en Mm3 (miles de m3). Un pozo con 100.000 m3 de petroleo y
    50 Mm3 de gas tiene GOR = 50.000 m3 gas / 100.000 m3 petroleo = 0.5... no.
    50 Mm3 = 50.000 m3. GOR = 50.000 / 100.000 = 0.5 m3/m3. Verifiquemos que
    la conversion Mm3->m3 se aplica.
    """
    # 200 Mm3 = 200.000 m3 de gas; 1.000 m3 de petroleo -> GOR 200 m3/m3
    gor = fluido.gor_m3m3(1000.0, 200.0)
    assert gor == pytest.approx(200.0)


def test_gor_sin_petroleo_es_nan_no_cero():
    gor = fluido.gor_m3m3(0.0, 100.0)
    assert np.isnan(gor)


def test_gor_vectorizado():
    pet = np.array([1000.0, 2000.0, 0.0])
    gas = np.array([100.0, 100.0, 100.0])  # Mm3
    gor = fluido.gor_m3m3(pet, gas)
    assert gor[0] == pytest.approx(100.0)   # 100.000/1000
    assert gor[1] == pytest.approx(50.0)    # 100.000/2000
    assert np.isnan(gor[2])


# --- clasificacion --------------------------------------------------------

def test_los_cortes_de_ventana():
    assert fluido.clasificar(50) == "Petroleo negro"
    assert fluido.clasificar(199.9) == "Petroleo negro"
    assert fluido.clasificar(200) == "Petroleo volatil"
    assert fluido.clasificar(999) == "Petroleo volatil"
    assert fluido.clasificar(1000) == "Gas y condensado"
    assert fluido.clasificar(5000) == "Gas y condensado"


def test_sin_dato_no_rompe():
    assert fluido.clasificar(np.nan) == "Sin dato"
    assert fluido.clasificar(None) == "Sin dato"


# --- integracion con la tabla de pozos -----------------------------------

def _pozos():
    return pd.DataFrame({
        "id_pozo": ["negro", "volatil", "gas", "sin_pet"],
        # petroleo m3, gas Mm3 -> GOR: 100, 500, 2000, indefinido
        "acum_petroleo_m3": [100000.0, 100000.0, 100000.0, 0.0],
        "acum_gas_mm3":     [10000.0,  50000.0,  200000.0, 5000.0],
    })


def test_agregar_ventana_clasifica_cada_pozo():
    r = fluido.agregar_ventana(_pozos())
    ventanas = dict(zip(r["id_pozo"], r["ventana_fluido"]))
    assert ventanas["negro"] == "Petroleo negro"
    assert ventanas["volatil"] == "Petroleo volatil"
    assert ventanas["gas"] == "Gas y condensado"
    assert ventanas["sin_pet"] == "Sin dato"


def test_agregar_ventana_sin_columnas_no_rompe():
    r = fluido.agregar_ventana(pd.DataFrame({"id_pozo": ["a"]}))
    assert r["ventana_fluido"].iloc[0] == "Sin dato"


def test_resumen_cuenta_por_ventana():
    r = fluido.agregar_ventana(_pozos())
    res = fluido.resumen(r)
    assert res["suficientes_datos"]
    assert res["pozos_clasificados"] == 3   # el sin_pet no cuenta
    assert res["sin_dato"] == 1
    assert res["por_ventana"]["Petroleo negro"]["pozos"] == 1
    assert res["por_ventana"]["Gas y condensado"]["pozos"] == 1


def test_resumen_vacio_no_rompe():
    assert fluido.resumen(pd.DataFrame())["suficientes_datos"] is False
