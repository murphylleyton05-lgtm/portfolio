"""
Tests del modulo de fractura y de la normalizacion por rama lateral.

La parte interesante de estos tests es la primera: probamos la deteccion de
columnas contra VARIAS convenciones de nombres plausibles. La idea es que el
codigo sobreviva a que el portal renombre una columna, que es algo que pasa.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import fractura  # noqa: E402


# --- deteccion de columnas por patron ------------------------------------

@pytest.mark.parametrize("nombre", [
    "longitud_rama_horizontal_m",
    "longitud_rama_horizontal",
    "LONGITUD_RAMA_HORIZONTAL_M",
    "longitud rama horizontal (m)",
    "Longitud de Rama Horizontal",
])
def test_detecta_la_rama_lateral_se_llame_como_se_llame(nombre):
    mapa = fractura.detectar_columnas(["idpozo", nombre, "cantidad_fracturas"])
    assert mapa.get("rama_m") == nombre


@pytest.mark.parametrize("nombre", [
    "cantidad_fracturas",
    "CANTIDAD_FRACTURAS",
    "cantidad_etapas",
    "etapas",
])
def test_detecta_las_etapas_de_fractura(nombre):
    mapa = fractura.detectar_columnas(["idpozo", "longitud_rama_horizontal_m", nombre])
    assert mapa.get("etapas") == nombre


def test_detecta_id_de_pozo():
    for nombre in ("idpozo", "IDPOZO", "id_pozo"):
        mapa = fractura.detectar_columnas([nombre, "otra_cosa"])
        assert mapa.get("id_pozo") == nombre


def test_no_inventa_columnas_que_no_estan():
    mapa = fractura.detectar_columnas(["idpozo", "empresa"])
    assert "rama_m" not in mapa
    assert "etapas" not in mapa


def test_una_columna_no_se_asigna_a_dos_campos():
    mapa = fractura.detectar_columnas(
        ["idpozo", "longitud_rama_horizontal_m", "cantidad_fracturas", "arena_total_tn"]
    )
    assert len(set(mapa.values())) == len(mapa)


# --- normalizacion --------------------------------------------------------

def _crudo(**cambios):
    base = pd.DataFrame({
        "idpozo": [1, 2, 3],
        "sigla": ["A-1", "B-2", "C-3"],
        "empresa": ["YPF", "VISTA", "YPF"],
        "longitud_rama_horizontal_m": [2500.0, 1500.0, 3000.0],
        "cantidad_fracturas": [40, 25, 50],
        "agua_inyectada_m3": [60000.0, 35000.0, 75000.0],
    })
    return base.assign(**cambios)


def test_normalizar_devuelve_una_fila_por_pozo():
    r = fractura.normalizar(_crudo())
    assert len(r) == 3
    assert set(r["id_pozo"]) == {"1", "2", "3"}
    assert r.loc[r["id_pozo"] == "1", "rama_m"].iloc[0] == 2500.0


def test_descarta_ramas_absurdas():
    """80 m o 15.000 m de rama no son pozos: son datos mal cargados."""
    r = fractura.normalizar(_crudo(longitud_rama_horizontal_m=[80.0, 15000.0, 3000.0]))
    assert r["rama_m"].isna().sum() == 2
    assert r["rama_m"].notna().sum() == 1


def test_descarta_etapas_absurdas():
    r = fractura.normalizar(_crudo(cantidad_fracturas=[1, 500, 50]))
    assert r["etapas"].isna().sum() == 2


def test_suma_la_arena_cuando_viene_partida():
    """El portal a veces separa arena nacional e importada: hay que sumarlas."""
    crudo = _crudo()
    crudo["arena_bombeada_nacional_tn"] = [3000.0, 1000.0, 4000.0]
    crudo["arena_bombeada_importada_tn"] = [500.0, 200.0, 600.0]
    r = fractura.normalizar(crudo)
    assert r.loc[r["id_pozo"] == "1", "arena_tn"].iloc[0] == pytest.approx(3500.0)


def test_consolida_pozos_repetidos():
    """
    Un pozo puede aparecer varias veces (etapas cargadas por tandas).
    La rama es una sola (maximo); las etapas se suman.
    """
    crudo = pd.DataFrame({
        "idpozo": [1, 1],
        "longitud_rama_horizontal_m": [2500.0, 2500.0],
        "cantidad_fracturas": [20, 20],
    })
    r = fractura.normalizar(crudo)
    assert len(r) == 1
    assert r["rama_m"].iloc[0] == 2500.0
    assert r["etapas"].iloc[0] == 40


def test_sin_id_de_pozo_da_error_claro():
    with pytest.raises(ValueError, match="id de pozo"):
        fractura.normalizar(pd.DataFrame({"empresa": ["YPF"]}))


def test_sin_rama_ni_etapas_da_error_claro():
    with pytest.raises(ValueError, match="ni longitud de rama ni cantidad de etapas"):
        fractura.normalizar(pd.DataFrame({"idpozo": [1], "empresa": ["YPF"]}))


# --- la metrica que da sentido al modulo ---------------------------------

def test_eur_por_metro_neutraliza_la_ventaja_del_pozo_mas_largo():
    """
    El test central. Dos pozos en roca IDENTICA, uno el doble de largo que el
    otro. El EUR crudo dice que el largo es el doble de bueno; el EUR por
    metro tiene que decir que son iguales.
    """
    ajustes = pd.DataFrame({
        "id_pozo": ["1", "2"],
        "eur": [200_000.0, 100_000.0],   # el largo produce el doble
    })
    frac = pd.DataFrame({
        "id_pozo": ["1", "2"],
        "rama_m": [3000.0, 1500.0],      # ...porque mide el doble
        "etapas": [50.0, 25.0],
        "arena_tn": [np.nan, np.nan],
        "agua_m3": [np.nan, np.nan],
    })
    r = fractura.unir_con_ajustes(ajustes, frac)

    assert r["eur_por_metro"].iloc[0] == pytest.approx(r["eur_por_metro"].iloc[1])
    assert r["eur_por_etapa"].iloc[0] == pytest.approx(r["eur_por_etapa"].iloc[1])


def test_pozos_sin_datos_de_fractura_quedan_marcados_no_borrados():
    ajustes = pd.DataFrame({"id_pozo": ["1", "2"], "eur": [200_000.0, 100_000.0]})
    frac = pd.DataFrame({"id_pozo": ["1"], "rama_m": [3000.0],
                         "etapas": [50.0], "arena_tn": [np.nan], "agua_m3": [np.nan]})
    r = fractura.unir_con_ajustes(ajustes, frac)

    assert len(r) == 2                      # no se pierde ningun pozo
    assert r["tiene_fractura"].tolist() == [True, False]
    assert pd.isna(r.loc[r["id_pozo"] == "2", "eur_por_metro"].iloc[0])


def test_cuanto_explica_la_rama_detecta_la_confusion():
    """
    Construimos un caso donde el EUR depende SOLO de la longitud de rama.
    La funcion tiene que reportar correlacion muy alta: es exactamente la
    situacion en la que un ranking sin normalizar engana.
    """
    rng = np.random.default_rng(0)
    ramas = rng.uniform(1500, 3500, 60)
    ajustes = pd.DataFrame({
        "id_pozo": [str(i) for i in range(60)],
        "eur": ramas * 50.0,                 # EUR proporcional a la rama
    })
    frac = pd.DataFrame({
        "id_pozo": [str(i) for i in range(60)],
        "rama_m": ramas,
        "etapas": np.round(ramas / 60),
        "arena_tn": np.nan, "agua_m3": np.nan,
    })
    unido = fractura.unir_con_ajustes(ajustes, frac)
    dx = fractura.cuanto_explica_la_rama(unido)

    assert dx["suficientes_datos"]
    assert dx["correlacion_rama_eur"] > 0.99
    assert dx["varianza_explicada"] > 0.98


def test_cuanto_explica_la_rama_avisa_si_hay_pocos_datos():
    ajustes = pd.DataFrame({"id_pozo": ["1"], "eur": [100.0]})
    frac = pd.DataFrame({"id_pozo": ["1"], "rama_m": [2000.0],
                         "etapas": [30.0], "arena_tn": [np.nan], "agua_m3": [np.nan]})
    dx = fractura.cuanto_explica_la_rama(fractura.unir_con_ajustes(ajustes, frac))
    assert dx["suficientes_datos"] is False
