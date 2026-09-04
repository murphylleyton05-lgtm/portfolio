"""
Tests del modulo de declinacion.

Por que hay tests en un proyecto de portfolio: porque es la diferencia entre
"hice un notebook" y "escribi software". Un reclutador tecnico mira si hay
tests antes de mirar los graficos.

La estrategia de estos tests es la que se usa para validar cualquier modelo
matematico: generar datos SINTETICOS con parametros conocidos, ajustar, y
verificar que el ajuste recupera esos parametros. Si el ajuste no puede
recuperar parametros que vos mismo pusiste, no va a servir con datos reales.

Correr con:   pytest -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import declinacion  # noqa: E402


# --- Las ecuaciones ------------------------------------------------------

def test_caudal_en_t0_es_qi():
    """En t=0 la curva vale exactamente qi, para cualquier b."""
    for b in (0.0, 0.5, 1.0, 1.5):
        assert declinacion.caudal_arps(0, qi=100.0, di=0.1, b=b) == pytest.approx(100.0)


def test_la_curva_siempre_declina():
    """El caudal nunca puede subir con el tiempo."""
    t = np.arange(0, 60)
    for b in (0.0, 0.5, 1.0, 1.8):
        q = declinacion.caudal_arps(t, qi=100.0, di=0.15, b=b)
        assert np.all(np.diff(q) <= 0)


def test_caso_exponencial_coincide_con_la_formula_cerrada():
    """Con b=0, Arps tiene que dar exactamente qi*exp(-Di*t)."""
    t = np.arange(0, 24)
    q = declinacion.caudal_arps(t, qi=200.0, di=0.08, b=0.0)
    esperado = 200.0 * np.exp(-0.08 * t)
    np.testing.assert_allclose(q, esperado, rtol=1e-9)


def test_caso_armonico_coincide_con_la_formula_cerrada():
    """Con b=1, Arps tiene que dar qi/(1+Di*t)."""
    t = np.arange(0, 24)
    q = declinacion.caudal_arps(t, qi=200.0, di=0.08, b=1.0)
    esperado = 200.0 / (1.0 + 0.08 * t)
    np.testing.assert_allclose(q, esperado, rtol=1e-9)


def test_b_mas_alto_significa_cola_mas_larga():
    """
    A los 5 años, un pozo con b alto tiene que estar produciendo mas que uno
    con b bajo (misma qi y Di). Es la propiedad que hace que b importe tanto
    en la evaluacion economica de un pozo de shale.
    """
    q_bajo = declinacion.caudal_arps(60, qi=100.0, di=0.15, b=0.3)
    q_alto = declinacion.caudal_arps(60, qi=100.0, di=0.15, b=1.5)
    assert q_alto > q_bajo


# --- El corte terminal ---------------------------------------------------

def test_hiperbolica_modificada_cae_por_debajo_de_la_pura():
    """
    Despues del mes de cambio, la hiperbolica modificada tiene que declinar
    MAS que la hiperbolica pura (por eso existe: para no sobreestimar reservas).
    """
    t = np.array([300.0])
    pura = declinacion.caudal_arps(t, qi=100.0, di=0.2, b=1.4)[0]
    modificada = declinacion.caudal_hiperbolica_modificada(
        t, qi=100.0, di=0.2, b=1.4, d_terminal_anual=0.06
    )[0]
    assert modificada < pura


def test_el_corte_terminal_acota_el_eur():
    """
    Con b >= 1 la integral de Arps pura diverge. Con el corte terminal el EUR
    tiene que ser finito y razonable.
    """
    valor = declinacion.eur(qi=150.0, di=0.18, b=1.5, horizonte_meses=360)
    assert np.isfinite(valor)
    assert 0 < valor < 1e7


def test_eur_crece_con_el_horizonte():
    """Mas años de vida util => mas volumen acumulado. Trivial pero protege
    contra errores de signo en la integracion."""
    corto = declinacion.eur(qi=100.0, di=0.15, b=1.0, horizonte_meses=60)
    largo = declinacion.eur(qi=100.0, di=0.15, b=1.0, horizonte_meses=360)
    assert largo > corto


# --- El ajuste sobre datos ------------------------------------------------

def _pozo_sintetico(qi, di, b, meses=36, ruido=0.0, semilla=0):
    """Arma un DataFrame de un pozo con parametros conocidos."""
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2021-01-01", periods=meses, freq="MS")
    t = np.arange(meses, dtype=float)
    q = declinacion.caudal_arps(t, qi, di, b)
    if ruido:
        q = q * rng.normal(1.0, ruido, size=meses)
    return pd.DataFrame({
        "id_pozo": "TEST-1",
        "fecha": fechas,
        "caudal_petroleo_m3d": np.maximum(q, 0.01),
    })


def test_el_ajuste_recupera_los_parametros_sin_ruido():
    """Con datos limpios el ajuste tiene que recuperar qi, Di y b casi exactos."""
    df = _pozo_sintetico(qi=120.0, di=0.14, b=1.1, meses=48)
    ajuste = declinacion.ajustar_pozo(df, id_pozo="TEST-1")

    assert ajuste is not None
    assert ajuste.convergio
    assert ajuste.qi == pytest.approx(120.0, rel=0.02)
    assert ajuste.di_mensual == pytest.approx(0.14, rel=0.05)
    assert ajuste.b == pytest.approx(1.1, rel=0.10)
    assert ajuste.r2 > 0.999


def test_el_ajuste_tolera_ruido_realista():
    """Con 12% de ruido (como en la operacion real) el ajuste sigue siendo bueno."""
    df = _pozo_sintetico(qi=120.0, di=0.14, b=1.1, meses=48, ruido=0.12, semilla=7)
    ajuste = declinacion.ajustar_pozo(df, id_pozo="TEST-1")

    assert ajuste is not None
    assert ajuste.r2 > 0.85
    assert ajuste.qi == pytest.approx(120.0, rel=0.25)


def test_pozo_con_pocos_meses_se_descarta():
    """Menos de `meses_minimos` puntos utiles => None, no un ajuste basura."""
    df = _pozo_sintetico(qi=100.0, di=0.15, b=1.0, meses=4)
    assert declinacion.ajustar_pozo(df, meses_minimos=9) is None


def test_los_meses_parados_no_se_usan_para_ajustar():
    """
    Un mes en cero significa "pozo parado", no "produccion cero". Tiene que
    quedar afuera de la serie, si no arrastra la curva hacia abajo.
    """
    df = _pozo_sintetico(qi=100.0, di=0.15, b=1.0, meses=24)
    df.loc[10, "caudal_petroleo_m3d"] = 0.0
    serie = declinacion.preparar_serie(df)
    assert len(serie) == 23
    assert (serie["caudal_petroleo_m3d"] > 0).all()


def test_la_serie_arranca_en_el_pico():
    """
    Si el pozo tiene rampa de puesta en marcha (los primeros meses por debajo
    del pico), la serie de ajuste tiene que empezar en el maximo.
    """
    df = _pozo_sintetico(qi=100.0, di=0.15, b=1.0, meses=24)
    # Simulamos una rampa: los dos primeros meses producen menos.
    df.loc[0, "caudal_petroleo_m3d"] = 40.0
    df.loc[1, "caudal_petroleo_m3d"] = 80.0
    serie = declinacion.preparar_serie(df)
    assert serie["caudal_petroleo_m3d"].iloc[0] == serie["caudal_petroleo_m3d"].max()
    assert serie["t_meses"].iloc[0] == 0.0


# --- Agregados ------------------------------------------------------------

def test_ajustar_muchos_pozos_devuelve_una_fila_por_pozo():
    a = _pozo_sintetico(qi=100.0, di=0.15, b=1.0, meses=30)
    b = _pozo_sintetico(qi=200.0, di=0.10, b=1.2, meses=30)
    b["id_pozo"] = "TEST-2"
    df = pd.concat([a, b], ignore_index=True)

    resultado = declinacion.ajustar_muchos_pozos(df)
    assert len(resultado) == 2
    # Viene ordenado por EUR descendente: el pozo mas productivo primero.
    assert resultado.iloc[0]["id_pozo"] == "TEST-2"


def test_curva_tipo_agrega_percentiles_por_mes_de_vida():
    pozos = []
    for i, qi in enumerate([80.0, 120.0, 160.0]):
        p = _pozo_sintetico(qi=qi, di=0.15, b=1.0, meses=24)
        p["id_pozo"] = f"TEST-{i}"
        pozos.append(p)
    df = pd.concat(pozos, ignore_index=True)

    ct = declinacion.curva_tipo(df)
    assert {"mes_vida", "p10", "p50", "p90", "n_pozos"} <= set(ct.columns)
    assert ct["n_pozos"].max() == 3
    # El P90 siempre por encima del P10.
    assert (ct["p90"] >= ct["p10"]).all()


# --- calidad del ajuste: el filtro que evita rankings absurdos -------------

def test_un_pozo_erratico_da_r2_bajo():
    """
    Con datos oficiales aparecieron pozos cuya serie no sigue ninguna
    declinacion (paradas, intervenciones, datos mal declarados). El ajuste
    tiene que reportar R2 bajo para que el filtro de calidad los descarte,
    en vez de darles un EUR gigante y ponerlos primeros en el ranking.
    """
    rng = np.random.default_rng(3)
    fechas = pd.date_range("2021-01-01", periods=30, freq="MS")
    # Ruido puro alrededor de una media: no hay declinacion que encontrar.
    caudal = rng.uniform(40, 160, 30)
    df = pd.DataFrame({
        "id_pozo": "ERRATICO",
        "fecha": fechas,
        "caudal_petroleo_m3d": caudal,
    })
    ajuste = declinacion.ajustar_pozo(df, id_pozo="ERRATICO")

    assert ajuste is not None
    assert ajuste.r2 < 0.7, "un pozo sin tendencia no puede dar un ajuste confiable"


def test_b_en_el_tope_dispara_el_eur():
    """
    Documenta POR QUE hay que filtrar por b: con b pegado al tope el EUR se
    multiplica varias veces respecto de un b normal, con el mismo qi y Di.
    Es la razon por la que los ajustes fallidos encabezaban el ranking.
    """
    normal = declinacion.eur(qi=100.0, di=0.15, b=1.0, horizonte_meses=360)
    en_tope = declinacion.eur(qi=100.0, di=0.15, b=2.0, horizonte_meses=360)
    assert en_tope > normal * 1.5
