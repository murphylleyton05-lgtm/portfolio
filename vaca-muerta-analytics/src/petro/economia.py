"""
Economia de pozo: ¿a que precio del barril cierra?

DE QUE SIRVE
------------
Hasta aca el proyecto dice cuanto va a producir un pozo. Eso todavia no es la
pregunta del negocio. La pregunta del negocio es si conviene perforarlo, y eso
depende de tres cosas: cuanto cuesta el pozo, cuanto produce, y a que precio se
vende lo que produce.

El indicador que usa la industria para resumir todo eso es el PRECIO DE
EQUILIBRIO (breakeven): el precio del barril al cual el pozo apenas devuelve la
inversion, ni gana ni pierde. Cuando se lee "Vaca Muerta cierra a 40 dolares",
se habla de esto.

COMO SE CALCULA ACA
-------------------
El valor presente de un pozo, a un precio P, es:

    VAN = (P - opex) * (1 - regalias) * Vd  -  costo_del_pozo

donde `Vd` es el VOLUMEN DESCONTADO: los barriles que produce el pozo, cada uno
traido a valor de hoy segun cuando se produce. Un barril dentro de diez años
vale menos que uno de este mes, y en shale eso pesa muchisimo porque la mayor
parte del volumen sale en los primeros años.

Igualando VAN = 0 y despejando el precio:

    precio_equilibrio = costo_del_pozo / ((1 - regalias) * Vd) + opex

Es analitico: no hace falta iterar. Y esa formula deja ver de una que el
precio de equilibrio baja si el pozo produce mas (Vd sube) o si el pozo cuesta
menos, que es exactamente la intuicion del negocio.

LO QUE ESTE MODELO **NO** HACE
------------------------------
Es un modelo simple y hay que decirlo, porque presentarlo como algo mas seria
deshonesto:

  - No tiene impuesto a las ganancias ni retenciones a la exportacion.
  - Asume precio constante en el tiempo. En la realidad no lo es.
  - No tiene inflacion ni costos de abandono del pozo.
  - Usa el costo de pozo como un unico numero, cuando en la realidad varia
    muchisimo entre operadoras, bloques y años.
  - El volumen sale del modelo de declinacion, que ya tiene su propio error
    (ver validacion.py: subestima de forma sistematica, asi que estos precios
    de equilibrio probablemente sean algo PESIMISTAS).

Sirve para comparar pozos y bloques entre si con reglas iguales, no para
tomar una decision de inversion.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .declinacion import DIAS_POR_MES, caudal_hiperbolica_modificada
from .limpieza import BARRILES_POR_M3


@dataclass(frozen=True)
class Supuestos:
    """
    Los supuestos economicos, juntos y explicitos.

    Estan en un solo objeto a proposito: asi cualquiera que lea un resultado
    puede ver con que numeros se hizo, y cambiarlos es cambiar un solo lugar.

    Los valores por defecto son ordenes de magnitud publicos y discutibles para
    un pozo horizontal de shale en Vaca Muerta. NO son datos medidos: son
    supuestos, y cambiarlos cambia el resultado.
    """

    costo_pozo_musd: float = 12.0      # millones de USD, pozo perforado y terminado
    opex_usd_bbl: float = 12.0         # costo operativo por barril producido
    regalias_pct: float = 12.0         # regalias provinciales, % del valor boca de pozo
    descuento_anual_pct: float = 10.0  # tasa de descuento anual
    horizonte_meses: int = 240         # 20 años de vida economica

    def como_dict(self) -> dict:
        return {
            "costo_pozo_musd": self.costo_pozo_musd,
            "opex_usd_bbl": self.opex_usd_bbl,
            "regalias_pct": self.regalias_pct,
            "descuento_anual_pct": self.descuento_anual_pct,
            "horizonte_meses": self.horizonte_meses,
        }


def volumen_descontado_bbl(
    qi_m3d: float,
    di_mensual: float,
    b: float,
    supuestos: Supuestos = Supuestos(),
    d_terminal_anual: float = 0.06,
) -> float:
    """
    Barriles que produce el pozo, cada uno traido a valor presente.

    Es la pieza central: un barril del mes 1 vale mas que uno del mes 120.
    Sin descontar, un pozo que produce lento parece igual de bueno que uno que
    produce rapido, y en shale eso es justamente lo que los diferencia.
    """
    meses = np.arange(supuestos.horizonte_meses, dtype=float)
    caudal = caudal_hiperbolica_modificada(
        meses, qi_m3d, di_mensual, b, d_terminal_anual=d_terminal_anual
    )
    volumen_mensual_bbl = caudal * DIAS_POR_MES * BARRILES_POR_M3

    # Tasa mensual equivalente a la anual (composicion, no division).
    tasa_mensual = (1 + supuestos.descuento_anual_pct / 100) ** (1 / 12) - 1
    factor = 1 / (1 + tasa_mensual) ** meses

    return float(np.sum(volumen_mensual_bbl * factor))


def precio_de_equilibrio(
    qi_m3d: float,
    di_mensual: float,
    b: float,
    supuestos: Supuestos = Supuestos(),
    d_terminal_anual: float = 0.06,
) -> float:
    """
    Precio del barril al que el pozo devuelve exactamente la inversion.

    Por debajo de ese precio el pozo destruye valor; por encima, lo crea.
    """
    vd = volumen_descontado_bbl(qi_m3d, di_mensual, b, supuestos, d_terminal_anual)
    if vd <= 0:
        return float("inf")

    neto = (1 - supuestos.regalias_pct / 100) * vd
    return supuestos.costo_pozo_musd * 1e6 / neto + supuestos.opex_usd_bbl


def van_musd(
    qi_m3d: float,
    di_mensual: float,
    b: float,
    precio_usd_bbl: float,
    supuestos: Supuestos = Supuestos(),
    d_terminal_anual: float = 0.06,
) -> float:
    """Valor presente neto del pozo, en millones de USD, a un precio dado."""
    vd = volumen_descontado_bbl(qi_m3d, di_mensual, b, supuestos, d_terminal_anual)
    margen = (precio_usd_bbl - supuestos.opex_usd_bbl) * (1 - supuestos.regalias_pct / 100)
    return (margen * vd - supuestos.costo_pozo_musd * 1e6) / 1e6


def meses_de_repago(
    qi_m3d: float,
    di_mensual: float,
    b: float,
    precio_usd_bbl: float,
    supuestos: Supuestos = Supuestos(),
    d_terminal_anual: float = 0.06,
) -> float | None:
    """
    Cuantos meses tarda el pozo en devolver lo que costo, sin descontar.

    Se calcula sin descuento a proposito: el repago es una medida de caja, no
    de valor. Devuelve None si nunca llega a repagarse dentro del horizonte.
    """
    meses = np.arange(supuestos.horizonte_meses, dtype=float)
    caudal = caudal_hiperbolica_modificada(
        meses, qi_m3d, di_mensual, b, d_terminal_anual=d_terminal_anual
    )
    bbl = caudal * DIAS_POR_MES * BARRILES_POR_M3
    margen = (precio_usd_bbl - supuestos.opex_usd_bbl) * (1 - supuestos.regalias_pct / 100)

    if margen <= 0:
        return None

    acumulado = np.cumsum(bbl * margen)
    llegada = np.argmax(acumulado >= supuestos.costo_pozo_musd * 1e6)

    if acumulado[llegada] < supuestos.costo_pozo_musd * 1e6:
        return None
    return float(llegada + 1)


def evaluar(
    ajustes: pd.DataFrame,
    precio_usd_bbl: float = 65.0,
    supuestos: Supuestos = Supuestos(),
    d_terminal_anual: float = 0.06,
) -> pd.DataFrame:
    """
    Calcula la economia de cada pozo de la tabla de ajustes.

    Agrega las columnas:
        volumen_descontado_bbl
        precio_equilibrio_usd    el numero que resume todo
        van_musd                 al `precio_usd_bbl` dado
        repago_meses
    """
    df = ajustes.copy()

    vd, be, van, repago = [], [], [], []
    for f in df.itertuples():
        v = volumen_descontado_bbl(f.qi, f.di_mensual, f.b, supuestos, d_terminal_anual)
        vd.append(v)
        be.append(precio_de_equilibrio(f.qi, f.di_mensual, f.b, supuestos, d_terminal_anual))
        van.append(van_musd(f.qi, f.di_mensual, f.b, precio_usd_bbl, supuestos, d_terminal_anual))
        repago.append(meses_de_repago(f.qi, f.di_mensual, f.b, precio_usd_bbl,
                                      supuestos, d_terminal_anual))

    df["volumen_descontado_bbl"] = vd
    df["precio_equilibrio_usd"] = be
    df["van_musd"] = van
    df["repago_meses"] = repago
    df["rentable"] = df["precio_equilibrio_usd"] <= precio_usd_bbl
    return df


def resumen(evaluados: pd.DataFrame, precio_usd_bbl: float,
            supuestos: Supuestos = Supuestos()) -> dict:
    """Los numeros del conjunto, para el titular y el README."""
    be = evaluados["precio_equilibrio_usd"].replace([np.inf, -np.inf], np.nan).dropna()
    if be.empty:
        return {"suficientes_datos": False}

    return {
        "suficientes_datos": True,
        "pozos": int(len(be)),
        "precio_evaluado": precio_usd_bbl,
        "equilibrio_mediano": round(float(be.median()), 1),
        "equilibrio_p10": round(float(be.quantile(0.10)), 1),
        "equilibrio_p90": round(float(be.quantile(0.90)), 1),
        "rentables_pct": round(float((be <= precio_usd_bbl).mean() * 100), 1),
        "van_mediano_musd": round(float(evaluados["van_musd"].median()), 1),
        "repago_mediano_meses": (
            None if evaluados["repago_meses"].isna().all()
            else int(evaluados["repago_meses"].median())
        ),
        "supuestos": supuestos.como_dict(),
    }
