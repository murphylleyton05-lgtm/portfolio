"""
Tests de la seleccion de pozos que alimenta la app.

El criterio de "ajuste confiable" decide que pozos entran al ranking y a la
economia. Es la clase de regla que se puede aflojar sin querer y que nadie nota,
porque los graficos siguen dibujandose igual: solo cambian los numeros.
"""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from petro import config  # noqa: E402

# generar_web.py es un script, no un modulo del paquete: lo cargamos por ruta.
_spec = importlib.util.spec_from_file_location(
    "generar_web", RAIZ / "scripts" / "generar_web.py"
)
generar_web = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generar_web)


def _ajustes():
    """Cuatro pozos: uno bueno y tres que deberian quedar afuera."""
    return pd.DataFrame({
        "id_pozo": ["bueno", "r2_bajo", "no_convergio", "b_en_tope"],
        "r2": [0.95, 0.30, 0.95, 0.95],
        "convergio": [True, True, False, True],
        "b": [1.2, 1.2, 1.2, config.B_EN_EL_TOPE + 0.01],
        "eur": [100.0, 900.0, 800.0, 999.0],
    })


def test_solo_pasa_el_ajuste_confiable():
    r = generar_web.seleccionar_confiables(_ajustes())
    assert list(r["id_pozo"]) == ["bueno"]


def test_descarta_r2_bajo():
    r = generar_web.seleccionar_confiables(_ajustes())
    assert "r2_bajo" not in set(r["id_pozo"])


def test_descarta_los_que_no_convergieron():
    r = generar_web.seleccionar_confiables(_ajustes())
    assert "no_convergio" not in set(r["id_pozo"])


def test_descarta_b_en_el_tope():
    """
    El mas importante de los tres: son los ajustes con el EUR mas alto, asi que
    sin este filtro encabezan el ranking y ademas hunden el precio de equilibrio.
    """
    r = generar_web.seleccionar_confiables(_ajustes())
    assert "b_en_tope" not in set(r["id_pozo"])


def test_los_descartados_son_justo_los_de_mayor_eur():
    """
    Deja constancia de por que el filtro no es un detalle: los tres pozos que
    se descartan tienen EUR mucho mayor que el unico bueno. Sin filtrar, el
    ranking entero seria de ajustes rotos.
    """
    aj = _ajustes()
    confiables = generar_web.seleccionar_confiables(aj)
    descartados = aj[~aj["id_pozo"].isin(confiables["id_pozo"])]
    assert descartados["eur"].min() > confiables["eur"].max()


def test_el_criterio_usa_la_constante_compartida():
    """
    Si alguien cambia el tope en config, el filtro tiene que seguirlo. Es lo que
    evita que la app y el pipeline filtren distinto.
    """
    aj = _ajustes()
    aj.loc[aj["id_pozo"] == "b_en_tope", "b"] = config.B_EN_EL_TOPE - 0.01
    r = generar_web.seleccionar_confiables(aj)
    assert set(r["id_pozo"]) == {"bueno", "b_en_tope"}
