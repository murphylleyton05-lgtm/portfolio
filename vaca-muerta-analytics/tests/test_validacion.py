"""
Tests del backtest.

Estos tests protegen la afirmacion mas fuerte del proyecto: "el modelo predice
la produccion futura con un error de X%". Si el backtest esta mal, ese numero
es mentira, y es exactamente el numero que alguien va a querer discutir.

La estrategia es la de siempre: datos sinteticos con respuesta conocida.
Si el pozo sigue EXACTAMENTE una curva de Arps, el modelo entrenado con los
primeros 24 meses tiene que predecir los siguientes casi sin error.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import declinacion, validacion  # noqa: E402


def _pozo(qi=120.0, di=0.14, b=1.1, meses=72, ruido=0.0, semilla=0, id_pozo="T-1"):
    rng = np.random.default_rng(semilla)
    t = np.arange(meses, dtype=float)
    q = declinacion.caudal_arps(t, qi, di, b)
    if ruido:
        q = q * rng.normal(1.0, ruido, size=meses)
    return pd.DataFrame({
        "id_pozo": id_pozo,
        "fecha": pd.date_range("2019-01-01", periods=meses, freq="MS"),
        "caudal_petroleo_m3d": np.maximum(q, 0.01),
    })


# --- el test central ------------------------------------------------------

def test_sin_ruido_el_modelo_predice_casi_exacto():
    """
    Si el pozo sigue una curva de Arps perfecta, entrenar con 24 meses y
    predecir los 36 siguientes tiene que dar un error despreciable.
    Si este test falla, el backtest esta midiendo cualquier cosa.
    """
    r = validacion.backtest_pozo(_pozo(meses=72))

    assert r is not None
    assert abs(r["error_pct_36"]) < 2.0, f"error {r['error_pct_36']}% con datos perfectos"


def test_con_ruido_realista_el_error_sigue_siendo_chico():
    """Con 12% de ruido operativo, el error acumulado debe seguir siendo moderado."""
    r = validacion.backtest_pozo(_pozo(meses=72, ruido=0.12, semilla=5))

    assert r is not None
    assert abs(r["error_pct_36"]) < 25.0


def test_el_modelo_no_ve_los_meses_que_predice():
    """
    El test que valida la honestidad del backtest: si cambiamos SOLO los meses
    posteriores al entrenamiento, la prediccion no puede cambiar. Si cambia,
    el modelo esta viendo datos que no deberia y todo el ejercicio es falso.
    """
    base = _pozo(meses=72)
    alterado = base.copy()
    # Duplicamos la produccion de todo lo que viene despues del entrenamiento.
    alterado.loc[30:, "caudal_petroleo_m3d"] *= 2.0

    r1 = validacion.backtest_pozo(base)
    r2 = validacion.backtest_pozo(alterado)

    assert r1 is not None and r2 is not None
    # La prediccion (pred_36) sale solo del ajuste: tiene que ser identica.
    assert r1["pred_36"] == pytest.approx(r2["pred_36"], rel=1e-9)
    # Lo real cambio, asi que el error tiene que haber cambiado.
    assert r1["error_pct_36"] != pytest.approx(r2["error_pct_36"])


def test_pozo_corto_no_se_evalua():
    """Sin meses suficientes para entrenar y evaluar, el pozo se descarta."""
    assert validacion.backtest_pozo(_pozo(meses=20)) is None
    assert validacion.backtest_pozo(_pozo(meses=30), horizontes=(36,)) is None


def test_horizontes_mas_largos_no_siempre_estan():
    """
    Un pozo con 40 meses alcanza para evaluar 12 meses pero no 36.
    El resultado tiene que traer el horizonte corto y omitir el largo.
    """
    r = validacion.backtest_pozo(_pozo(meses=40), horizontes=(12, 36))
    assert r is not None
    assert "error_pct_12" in r
    assert "error_pct_36" not in r


# --- agregacion -----------------------------------------------------------

def test_resumen_reporta_sesgo_y_precision():
    pozos = []
    for i in range(30):
        p = _pozo(meses=72, ruido=0.10, semilla=i, id_pozo=f"T-{i}")
        pozos.append(p)
    df = pd.concat(pozos, ignore_index=True)

    bt = validacion.backtest_muchos(df)
    assert len(bt) == 30

    res = validacion.resumen(bt)
    assert res["suficientes_datos"]
    assert res["h36"]["pozos"] == 30
    # Con ruido simetrico el sesgo tiene que ser chico...
    assert abs(res["h36"]["error_mediano"]) < 20
    # ...y el error absoluto tiene que ser >= al sesgo en valor absoluto.
    assert res["h36"]["error_absoluto"] >= abs(res["h36"]["error_mediano"]) - 1e-9
    assert 0 <= res["h36"]["dentro_20"] <= 100
    assert res["h36"]["p10"] <= res["h36"]["p90"]


def test_resumen_vacio_no_rompe():
    res = validacion.resumen(pd.DataFrame())
    assert res["suficientes_datos"] is False


def test_la_frase_dice_si_sobreestima_o_subestima():
    bt = validacion.backtest_muchos(pd.concat(
        [_pozo(meses=72, ruido=0.10, semilla=i, id_pozo=f"T-{i}") for i in range(25)],
        ignore_index=True))
    res = validacion.resumen(bt)
    frase = validacion.frase_del_resultado(res, horizonte=36)

    assert "error absoluto mediano" in frase
    assert ("sobreestima" in frase) or ("subestima" in frase)
    assert "%" in frase


def test_la_frase_avisa_cuando_no_hay_datos():
    frase = validacion.frase_del_resultado({"suficientes_datos": False})
    assert "No hay pozos suficientes" in frase


def test_un_pozo_no_entra_en_un_horizonte_que_no_vivio():
    """
    El pozo tiene 40 meses: 24 de entrenamiento y 16 posteriores. Puede validar
    el horizonte de 12 meses, pero NO el de 36 — nunca llego a producir 36
    meses despues del corte.

    Sin esta regla, el error "a 36 meses" se calcularia mezclando pozos que
    solo vivieron 16, y el numero que el proyecto presenta como su validacion
    principal seria falso.
    """
    r = validacion.backtest_pozo(_pozo(meses=40), horizontes=(12, 36))
    assert r is not None
    assert "error_pct_12" in r
    assert "error_pct_36" not in r


def test_los_meses_evaluados_se_corresponden_con_el_horizonte():
    """El conteo reportado tiene que ser coherente con el horizonte."""
    r = validacion.backtest_pozo(_pozo(meses=72), horizontes=(12, 36))
    assert r["meses_evaluados_12"] <= 12
    assert 30 <= r["meses_evaluados_36"] <= 36


def test_el_error_agregado_es_distinto_del_mediano():
    """
    El error agregado responde otra pregunta que el error por pozo: cuanto se
    equivoca el modelo en el TOTAL de un conjunto, no en cada pozo. Cuando los
    errores individuales tienen signos opuestos, se compensan y el agregado es
    mucho menor. Es la diferencia entre pronosticar un pozo y pronosticar un
    programa de perforacion.
    """
    bt = pd.DataFrame({
        "id_pozo": ["A", "B"],
        # Uno sobreestima 50%, el otro subestima 50%: en el total se cancelan.
        "real_36": [100.0, 100.0],
        "pred_36": [150.0, 50.0],
        "error_pct_36": [50.0, -50.0],
    })
    # resumen() exige al menos 10 pozos por horizonte; replicamos el patron.
    bt = pd.concat([bt] * 6, ignore_index=True)

    res = validacion.resumen(bt, horizontes=(36,))
    d = res["h36"]

    assert d["error_absoluto"] == pytest.approx(50.0)   # cada pozo se equivoca 50%
    assert d["error_agregado"] == pytest.approx(0.0)    # el total, nada


def test_la_frase_menciona_el_agregado_cuando_esta():
    bt = pd.DataFrame({
        "id_pozo": [str(i) for i in range(12)],
        "real_36": [100.0] * 12,
        "pred_36": [90.0] * 12,
        "error_pct_36": [-10.0] * 12,
    })
    frase = validacion.frase_del_resultado(validacion.resumen(bt, horizontes=(36,)), 36)
    assert "error del total" in frase
