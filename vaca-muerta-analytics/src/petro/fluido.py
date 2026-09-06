"""
Ventana de fluido de cada pozo, a partir del GOR de produccion.

POR QUE IMPORTA
---------------
Hasta aca el proyecto trata a todos los pozos como si produjeran lo mismo. No es
cierto: en Vaca Muerta conviven ventanas geologicas distintas. Un pozo de la
ventana de petroleo negro (poco gas asociado) y uno de la ventana de gas y
condensado son animales distintos, y compararles el EUR de petroleo sin
distinguirlos mezcla peras con manzanas.

La forma mas directa y honesta de separarlos con datos publicos es el GOR
(gas-oil ratio): cuantos m3 de gas produce el pozo por cada m3 de petroleo.

    GOR = volumen de gas / volumen de petroleo   [m3/m3]

QUE ES Y QUE NO ES ESTA CLASIFICACION
-------------------------------------
ES: una clasificacion por GOR DE PRODUCCION. Rapida, reproducible, y suficiente
    para no mezclar ventanas al comparar o rankear.

NO ES: una tipificacion PVT de fluido. La ventana "real" de un reservorio se
    determina con analisis PVT de laboratorio (composicion, punto de burbuja,
    etc.), que no esta en los datos publicos. Un pozo puede tener GOR de
    produccion alto por depletacion aunque su fluido original sea petroleo.

Presentarla como lo primero y no como lo segundo es lo correcto: es un proxy
util, con sus limites declarados.

LOS UMBRALES
------------
Los cortes son aproximados y estan en la literatura de ingenieria de
reservorios. En m3/m3 (unidad metrica, que es la del dato oficial):

    GOR < 200          Petroleo negro     (black oil)
    200 <= GOR < 1000  Petroleo volatil   (volatile oil)
    GOR >= 1000        Gas y condensado / humedo

Para referencia, 1 m3/m3 = 5.615 scf/bbl (la unidad de campo).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# m3 de gas por m3 de petroleo. El dato oficial trae el gas en Mm3 (miles de
# m3), asi que al calcular hay que multiplicar el gas por 1000 para volver a m3.
M3_POR_MM3 = 1000.0

# 1 m3/m3 = 5.615 scf/bbl. Solo para mostrar en la unidad de campo si hace falta.
SCF_BBL_POR_M3M3 = 5.615

# Cortes de ventana, en m3/m3. Aproximados y declarados como tales.
GOR_PETROLEO_NEGRO = 200.0
GOR_PETROLEO_VOLATIL = 1000.0

# Etiquetas ordenadas de menos a mas gas.
VENTANAS = ["Petroleo negro", "Petroleo volatil", "Gas y condensado", "Sin dato"]


def gor_m3m3(acum_petroleo_m3, acum_gas_mm3):
    """
    GOR de produccion, en m3 de gas por m3 de petroleo.

    Se calcula sobre ACUMULADOS, no sobre un mes: un mes suelto puede tener un
    corte de gas atipico por una parada o un dato mal cargado. El acumulado de
    toda la vida del pozo es mucho mas estable.

    Devuelve NaN cuando no hay petroleo acumulado (division indefinida): un pozo
    sin petroleo no tiene GOR de petroleo, no tiene GOR cero.
    """
    pet = np.asarray(acum_petroleo_m3, dtype=float)
    gas = np.asarray(acum_gas_mm3, dtype=float) * M3_POR_MM3
    with np.errstate(divide="ignore", invalid="ignore"):
        gor = np.where(pet > 0, gas / pet, np.nan)
    return gor


def clasificar(gor) -> str:
    """Devuelve la ventana de fluido para un GOR (en m3/m3)."""
    if gor is None or (isinstance(gor, float) and np.isnan(gor)):
        return "Sin dato"
    if gor < GOR_PETROLEO_NEGRO:
        return "Petroleo negro"
    if gor < GOR_PETROLEO_VOLATIL:
        return "Petroleo volatil"
    return "Gas y condensado"


def agregar_ventana(pozos: pd.DataFrame,
                    col_petroleo: str = "acum_petroleo_m3",
                    col_gas: str = "acum_gas_mm3") -> pd.DataFrame:
    """
    Agrega a la tabla de pozos las columnas `gor_m3m3` y `ventana_fluido`.

    Espera acumulados de petroleo (m3) y gas (Mm3), que es lo que produce
    `limpieza.resumen_por_pozo`.
    """
    df = pozos.copy()

    if col_petroleo not in df.columns or col_gas not in df.columns:
        # Sin columnas de acumulado no se puede clasificar: se marca todo como
        # sin dato en vez de fallar, para que el pipeline no se corte.
        df["gor_m3m3"] = np.nan
        df["ventana_fluido"] = "Sin dato"
        return df

    df["gor_m3m3"] = gor_m3m3(df[col_petroleo], df[col_gas])
    df["ventana_fluido"] = [clasificar(g) for g in df["gor_m3m3"]]
    return df


def resumen(pozos: pd.DataFrame) -> dict:
    """
    Cuenta cuantos pozos hay en cada ventana y su GOR mediano.

    Es el numero para el titular: dice cuan mezclado estaba el dataset antes de
    separar por ventana, que es justamente lo que justifica hacerlo.
    """
    if "ventana_fluido" not in pozos.columns:
        return {"suficientes_datos": False}

    con_dato = pozos[pozos["ventana_fluido"] != "Sin dato"]
    if con_dato.empty:
        return {"suficientes_datos": False}

    conteo = {}
    for ventana in VENTANAS[:-1]:  # sin "Sin dato"
        sub = con_dato[con_dato["ventana_fluido"] == ventana]
        if not sub.empty:
            conteo[ventana] = {
                "pozos": int(len(sub)),
                "pct": round(len(sub) / len(con_dato) * 100, 1),
                "gor_mediano": round(float(sub["gor_m3m3"].median()), 1),
            }

    return {
        "suficientes_datos": True,
        "pozos_clasificados": int(len(con_dato)),
        "sin_dato": int((pozos["ventana_fluido"] == "Sin dato").sum()),
        "gor_mediano_global": round(float(con_dato["gor_m3m3"].median()), 1),
        "por_ventana": conteo,
    }
