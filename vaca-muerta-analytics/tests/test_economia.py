"""
Tests de la economia de pozo.

El mas importante es el de consistencia interna: si el precio de equilibrio
esta bien calculado, valuar el pozo a ESE precio tiene que dar un VAN de cero.
Es la definicion de precio de equilibrio, y si no se cumple, todo el numero es
inventado.

Los demas tests verifican que el modelo se mueva en la direccion correcta ante
cambios que tienen una respuesta obvia: un pozo mas caro cierra a un precio mas
alto, un pozo mejor cierra a un precio mas bajo, etc. Son simples a proposito:
si un modelo economico falla estas, no sirve.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import economia  # noqa: E402

# Un pozo tipico: 140 m3/d iniciales, declinacion 15%/mes, b hiperbolico.
POZO = dict(qi_m3d=140.0, di_mensual=0.15, b=1.2)


# --- consistencia interna: la prueba de fuego --------------------------

def test_al_precio_de_equilibrio_el_van_es_cero():
    """
    Definicion de precio de equilibrio: al venderse a ese precio, el pozo no
    gana ni pierde. Si este test falla, el numero no significa nada.
    """
    be = economia.precio_de_equilibrio(**POZO)
    van = economia.van_musd(**POZO, precio_usd_bbl=be)
    assert van == pytest.approx(0.0, abs=1e-6)


def test_arriba_del_equilibrio_gana_y_abajo_pierde():
    be = economia.precio_de_equilibrio(**POZO)
    assert economia.van_musd(**POZO, precio_usd_bbl=be + 10) > 0
    assert economia.van_musd(**POZO, precio_usd_bbl=be - 10) < 0


# --- direccion de los efectos -------------------------------------------

def test_un_pozo_mas_caro_necesita_mas_precio():
    barato = economia.precio_de_equilibrio(
        **POZO, supuestos=economia.Supuestos(costo_pozo_musd=8.0))
    caro = economia.precio_de_equilibrio(
        **POZO, supuestos=economia.Supuestos(costo_pozo_musd=16.0))
    assert caro > barato


def test_un_pozo_mejor_cierra_a_menos_precio():
    flojo = economia.precio_de_equilibrio(qi_m3d=70.0, di_mensual=0.15, b=1.2)
    bueno = economia.precio_de_equilibrio(qi_m3d=200.0, di_mensual=0.15, b=1.2)
    assert bueno < flojo


def test_mas_regalias_suben_el_equilibrio():
    sin = economia.precio_de_equilibrio(**POZO, supuestos=economia.Supuestos(regalias_pct=0.0))
    con = economia.precio_de_equilibrio(**POZO, supuestos=economia.Supuestos(regalias_pct=25.0))
    assert con > sin


def test_el_opex_se_traslada_uno_a_uno_al_equilibrio():
    """
    El opex es un costo por barril: sumarle 5 USD/bbl tiene que subir el precio
    de equilibrio exactamente 5 USD/bbl, ni mas ni menos.
    """
    a = economia.precio_de_equilibrio(**POZO, supuestos=economia.Supuestos(opex_usd_bbl=10.0))
    b = economia.precio_de_equilibrio(**POZO, supuestos=economia.Supuestos(opex_usd_bbl=15.0))
    assert b - a == pytest.approx(5.0, abs=1e-9)


# --- el descuento, que es lo que hace no trivial al calculo -------------

def test_el_pozo_que_produce_antes_conserva_mas_valor_al_descontar():
    """
    La razon por la que hay que descontar y no solo sumar barriles.

    Comparar dos pozos distintos no aisla el efecto del tiempo, porque tambien
    cambia cuanto producen en total. Lo que si lo aisla es la FRACCION de
    volumen que sobrevive al descuento: para cada pozo, cuanto vale su
    produccion descontada respecto de la misma produccion sin descontar.

    Un pozo que declina rapido cobra antes, asi que conserva una fraccion
    mayor. Uno que produce despacio durante veinte años pierde mucho mas.
    """
    sin_descuento = economia.Supuestos(descuento_anual_pct=0.0)

    def fraccion_que_sobrevive(qi, di):
        con = economia.volumen_descontado_bbl(qi, di, 1.2)
        sin = economia.volumen_descontado_bbl(qi, di, 1.2, supuestos=sin_descuento)
        return con / sin

    rapido = fraccion_que_sobrevive(200.0, 0.25)
    lento = fraccion_que_sobrevive(95.0, 0.06)

    assert rapido > lento, (
        f"el pozo rapido deberia conservar mas valor: {rapido:.3f} vs {lento:.3f}"
    )


def test_a_igual_forma_de_curva_el_pozo_mas_grande_cierra_a_menos_precio():
    """
    Con la misma declinacion, duplicar el caudal inicial duplica el volumen y
    por lo tanto baja el precio de equilibrio. Es el chequeo de que el modelo
    escala como corresponde.
    """
    chico = economia.precio_de_equilibrio(qi_m3d=100.0, di_mensual=0.15, b=1.2)
    grande = economia.precio_de_equilibrio(qi_m3d=200.0, di_mensual=0.15, b=1.2)

    supuestos = economia.Supuestos()
    # Solo el componente de capex escala con el volumen; opex y diferencial son
    # costos por barril, fijos respecto del tamano del pozo. Los restamos para
    # aislar el capex, que debe dividirse por dos al duplicar el caudal.
    fijos = supuestos.opex_usd_bbl + supuestos.diferencial_usd_bbl
    capex_chico = chico - fijos
    capex_grande = grande - fijos
    assert capex_grande == pytest.approx(capex_chico / 2, rel=1e-6)


def test_una_tasa_de_descuento_mayor_sube_el_equilibrio():
    baja = economia.precio_de_equilibrio(
        **POZO, supuestos=economia.Supuestos(descuento_anual_pct=5.0))
    alta = economia.precio_de_equilibrio(
        **POZO, supuestos=economia.Supuestos(descuento_anual_pct=20.0))
    assert alta > baja


def test_sin_descuento_el_volumen_es_mayor():
    con = economia.volumen_descontado_bbl(
        **{"qi_m3d": 140.0, "di_mensual": 0.15, "b": 1.2},
        supuestos=economia.Supuestos(descuento_anual_pct=10.0))
    sin = economia.volumen_descontado_bbl(
        **{"qi_m3d": 140.0, "di_mensual": 0.15, "b": 1.2},
        supuestos=economia.Supuestos(descuento_anual_pct=0.0))
    assert sin > con


# --- repago ---------------------------------------------------------------

def test_a_mejor_precio_el_repago_es_mas_rapido():
    lento = economia.meses_de_repago(**POZO, precio_usd_bbl=45.0)
    rapido = economia.meses_de_repago(**POZO, precio_usd_bbl=90.0)
    assert lento is not None and rapido is not None
    assert rapido < lento


def test_si_el_precio_no_cubre_el_opex_nunca_repaga():
    assert economia.meses_de_repago(
        **POZO, precio_usd_bbl=5.0,
        supuestos=economia.Supuestos(opex_usd_bbl=12.0)) is None


# --- sobre la tabla completa ---------------------------------------------

def test_evaluar_agrega_las_columnas_y_marca_los_rentables():
    ajustes = pd.DataFrame({
        "id_pozo": ["A", "B"],
        "qi": [200.0, 40.0],
        "di_mensual": [0.15, 0.15],
        "b": [1.2, 1.2],
    })
    r = economia.evaluar(ajustes, precio_usd_bbl=65.0)

    for col in ("precio_equilibrio_usd", "van_musd", "repago_meses", "rentable"):
        assert col in r.columns

    # El pozo bueno cierra a menos precio que el flojo.
    assert r.loc[0, "precio_equilibrio_usd"] < r.loc[1, "precio_equilibrio_usd"]
    # `rentable` tiene que ser coherente con el precio evaluado.
    assert bool(r.loc[0, "rentable"]) == (r.loc[0, "precio_equilibrio_usd"] <= 65.0)


def test_resumen_devuelve_los_percentiles_y_los_supuestos():
    ajustes = pd.DataFrame({
        "id_pozo": [str(i) for i in range(20)],
        "qi": [60.0 + i * 12 for i in range(20)],
        "di_mensual": [0.15] * 20,
        "b": [1.2] * 20,
    })
    ev = economia.evaluar(ajustes, precio_usd_bbl=65.0)
    res = economia.resumen(ev, 65.0)

    assert res["suficientes_datos"]
    assert res["pozos"] == 20
    assert res["equilibrio_p10"] <= res["equilibrio_mediano"] <= res["equilibrio_p90"]
    assert 0 <= res["rentables_pct"] <= 100
    # Los supuestos viajan con el resultado: sin ellos el numero no se puede leer.
    assert res["supuestos"]["costo_pozo_musd"] == 12.0


def test_los_ajustes_rotos_darian_precios_de_equilibrio_absurdos():
    """
    Documenta por que la economia se calcula SOLO sobre ajustes confiables.

    Un ajuste fallido lleva b a su tope, y con b alto la curva tiene una cola
    larguisima: el volumen descontado se dispara y el pozo parece cerrar a
    cualquier precio. Si esos pozos entraran en el calculo, la conclusion seria
    que casi todo Vaca Muerta es rentable a 20 dolares, que es falso.
    """
    sano = economia.precio_de_equilibrio(qi_m3d=140.0, di_mensual=0.15, b=1.2)
    roto = economia.precio_de_equilibrio(qi_m3d=140.0, di_mensual=0.15, b=2.0)

    assert roto < sano, "b en el tope infla el volumen y abarata el equilibrio"
    # La distorsion no es menor: justifica filtrar antes de calcular.
    assert roto < sano * 0.9
