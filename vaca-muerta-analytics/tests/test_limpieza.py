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
    produccion, _fractura = demo_data.generar_pozos(n_pozos=5, semilla=1)
    return produccion


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


def test_columnas_duplicadas_se_unifican():
    """
    Caso real que rompio el pipeline con datos oficiales: al concatenar CSV de
    distintos años, uno traia "IDPOZO" y otro "idpozo". Al pasar todo a
    minusculas quedaban dos columnas con el mismo nombre, y entonces
    df["idpozo"] devolvia un DataFrame en vez de una Serie.
    """
    a = pd.DataFrame({
        "IDPOZO": [1], "ANIO": [2024], "MES": [3], "PROD_PET": [3000.0],
        "TEF": [10.0], "EMPRESA": ["X"], "FORMPROD": ["VMUT"],
    })
    b = pd.DataFrame({
        "idpozo": [2], "anio": [2024], "mes": [4], "prod_pet": [1500.0],
        "tef": [10.0], "empresa": ["Y"], "formprod": ["VMUT"],
    })
    crudo = pd.concat([a, b], ignore_index=True)
    assert len(crudo.columns) == 14, "el caso de prueba debe tener columnas duplicadas"

    df = limpieza.normalizar(crudo)

    assert len(df) == 2
    assert list(df["id_pozo"]) == ["1", "2"]
    assert df["caudal_petroleo_m3d"].tolist() == [300.0, 150.0]


def test_unificar_duplicadas_toma_el_primer_valor_no_nulo():
    from petro.limpieza import _unificar_duplicadas
    d = pd.DataFrame([[1.0, None], [None, 2.0]], columns=["idpozo", "idpozo"])
    r = _unificar_duplicadas(d)
    assert list(r.columns) == ["idpozo"]
    assert r["idpozo"].tolist() == [1.0, 2.0]


def test_los_id_de_pozo_no_quedan_con_punto_cero():
    """
    Bug real y silencioso: si una columna de id tiene algun nulo, pandas la
    pasa a float y el id queda como "100147.0". Ese id no matchea con el
    "100147" del dataset de fractura, el cruce da vacio y el analisis de
    normalizacion desaparece sin ningun error.
    """
    assert limpieza.a_id(pd.Series([100147.0, 100148.0])).tolist() == ["100147", "100148"]
    assert limpieza.a_id(pd.Series(["100147.0", " 100148 "])).tolist() == ["100147", "100148"]
    assert limpieza.a_id(pd.Series([1, 2])).tolist() == ["1", "2"]


def test_el_cruce_produccion_fractura_matchea():
    """
    El test que protege el analisis entero: los id que salen de produccion
    tienen que ser iguales a los que salen de fractura, para que el merge una
    las filas de verdad.
    """
    from petro import fractura as mod_fractura

    crudo_prod = pd.concat([
        pd.DataFrame({"IDPOZO": [100147], "ANIO": [2024], "MES": [3],
                      "PROD_PET": [3000.0], "TEF": [10.0], "FORMPROD": ["VMUT"]}),
        pd.DataFrame({"idpozo": [100148], "anio": [2024], "mes": [3],
                      "prod_pet": [1500.0], "tef": [10.0], "formprod": ["VMUT"]}),
    ], ignore_index=True)
    prod = limpieza.normalizar(crudo_prod)

    frac = mod_fractura.normalizar(pd.DataFrame({
        "idpozo": [100147, 100148],
        "longitud_rama_horizontal_m": [2500.0, 1500.0],
        "cantidad_fracturas": [40, 25],
    }))

    assert set(prod["id_pozo"]) == set(frac["id_pozo"]), "los id no matchean"
