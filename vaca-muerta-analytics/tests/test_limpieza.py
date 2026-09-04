"""
Tests de la normalizacion del esquema oficial.

Estos tests protegen la frontera con el mundo exterior: si la Secretaria
cambia un nombre de columna o el formato de una fecha, estos tests fallan y
te avisan antes de que el dashboard muestre numeros mal.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import demo_data, limpieza  # noqa: E402


@pytest.fixture
def crudo():
    """Un dataset chico en el esquema crudo oficial."""
    return demo_data.generar_pozos(n_pozos=5, semilla=1)


def test_normalizar_produce_las_columnas_minimas(crudo):
    df = limpieza.normalizar(crudo)
    faltantes = set(limpieza.COLUMNAS_MINIMAS) - set(df.columns)
    assert not faltantes, f"faltan columnas: {faltantes}"


def test_el_caudal_diario_divide_por_dias_efectivos():
    """
    El punto conceptual mas importante del modulo: el caudal es el volumen
    dividido por los DIAS QUE EL POZO PRODUJO (tef), no por los dias del mes.
    """
    crudo = pd.DataFrame([{
        "idpozo": 1, "anio": 2024, "mes": 3,
        "prod_pet": 3000.0, "prod_gas": 300.0, "prod_agua": 100.0,
        "tef": 10.0, "empresa": "X", "areayacimiento": "A",
        "cuenca": "NEUQUINA", "provincia": "NEUQUEN", "formprod": "VMUT",
        "sub_tipo_recurso": "SHALE", "tipopozo": "Petrolifero",
    }])
    df = limpieza.normalizar(crudo)
    # 3000 m3 en 10 dias = 300 m3/d (no 3000/31 = 96.8).
    assert df["caudal_petroleo_m3d"].iloc[0] == pytest.approx(300.0)


def test_mes_parado_no_genera_caudal():
    """tef=0 significa que el pozo no produjo: el caudal queda nulo, no cero."""
    crudo = pd.DataFrame([{
        "idpozo": 1, "anio": 2024, "mes": 3,
        "prod_pet": 0.0, "prod_gas": 0.0, "prod_agua": 0.0, "tef": 0.0,
        "empresa": "X", "areayacimiento": "A", "cuenca": "N",
        "provincia": "N", "formprod": "VMUT", "sub_tipo_recurso": "SHALE",
        "tipopozo": "Petrolifero",
    }])
    df = limpieza.normalizar(crudo)
    assert pd.isna(df["caudal_petroleo_m3d"].iloc[0])


def test_conversion_a_barriles(crudo):
    df = limpieza.normalizar(crudo)
    validos = df[df["caudal_petroleo_m3d"].notna()]
    esperado = validos["caudal_petroleo_m3d"] * limpieza.BARRILES_POR_M3
    pd.testing.assert_series_equal(
        validos["caudal_petroleo_bbld"], esperado, check_names=False
    )


def test_falta_una_columna_esencial_da_error_claro():
    """
    Si el CSV no trae idpozo, queremos un mensaje que explique que pasa, no un
    KeyError a 200 lineas de distancia.
    """
    with pytest.raises(ValueError, match="columnas esperadas"):
        limpieza.normalizar(pd.DataFrame({"anio": [2024], "mes": [1]}))


def test_filtro_vaca_muerta(crudo):
    df = limpieza.normalizar(crudo)
    vm = limpieza.filtrar_vaca_muerta(df)
    assert len(vm) == len(df)  # el demo es todo VMUT

    df.loc[df.index[:10], "formacion"] = "QUINTUCO"
    vm = limpieza.filtrar_vaca_muerta(df)
    assert len(vm) == len(df) - 10


def test_pozos_con_historia_suficiente_filtra_por_pozo_entero(crudo):
    df = limpieza.normalizar(crudo)
    filtrado = limpieza.pozos_con_historia_suficiente(df, meses_minimos=1000)
    assert filtrado.empty


def test_resumen_por_pozo_una_fila_por_pozo(crudo):
    df = limpieza.normalizar(crudo)
    resumen = limpieza.resumen_por_pozo(df)
    assert len(resumen) == df["id_pozo"].nunique()
    assert (resumen["acum_petroleo_m3"] > 0).all()
