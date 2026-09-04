"""
Backtest del modelo de declinacion: ¿se le puede creer al EUR?

LA PREGUNTA QUE ESTE MODULO RESPONDE
------------------------------------
Un EUR es una PREDICCION a 30 años. Cualquiera puede ajustar una curva y tirar
un numero grande; lo dificil es mostrar que ese numero significa algo.

La forma honesta de mostrarlo es la misma que se usa para validar cualquier
modelo predictivo: esconderle datos y ver si acierta.

    1. Se toman los primeros N meses de cada pozo (por defecto 24).
    2. Se ajusta la curva usando SOLO esos meses.
    3. Se le pide al modelo que prediga los meses siguientes.
    4. Se compara con lo que el pozo produjo de verdad.

El pozo ya produjo esos meses, pero el modelo no los vio. Es una prediccion
real, no un ajuste sobre datos conocidos.

QUE SIGNIFICA EL RESULTADO
--------------------------
El error se mide sobre el volumen ACUMULADO del periodo predicho, no sobre el
caudal mes a mes. Es lo correcto: al EUR le importa el volumen total, y un mes
individual puede desviarse por una parada sin que la prediccion sea mala.

Tambien se reporta el SESGO: si el modelo se equivoca, ¿lo hace siempre para
el mismo lado? Un modelo que sobreestima sistematicamente un 15% es mas util
que uno que se equivoca 15% al azar, porque el sesgo se puede corregir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .declinacion import (
    DIAS_POR_MES,
    D_TERMINAL_ANUAL_DEFECTO,
    ajustar_pozo,
    caudal_hiperbolica_modificada,
    preparar_serie,
)

# Meses de historia que ve el modelo antes de tener que predecir.
MESES_ENTRENAMIENTO = 24

# Horizontes de prediccion a evaluar, en meses despues del entrenamiento.
HORIZONTES = (12, 24, 36)


def backtest_pozo(
    df_pozo: pd.DataFrame,
    id_pozo: str = "s/d",
    col_caudal: str = "caudal_petroleo_m3d",
    col_fecha: str = "fecha",
    meses_entrenamiento: int = MESES_ENTRENAMIENTO,
    horizontes: tuple[int, ...] = HORIZONTES,
    d_terminal_anual: float = D_TERMINAL_ANUAL_DEFECTO,
) -> dict | None:
    """
    Ajusta con los primeros meses y mide el error contra lo que realmente paso.

    Devuelve None si el pozo no tiene historia suficiente para entrenar y
    ademas evaluar al menos el horizonte mas corto.

    El diccionario que devuelve trae, por cada horizonte h:
        real_h        volumen realmente producido en esos h meses
        pred_h        volumen que el modelo predijo
        error_pct_h   (pred - real) / real * 100   (positivo = sobreestimo)
    """
    serie = preparar_serie(df_pozo, col_caudal=col_caudal, col_fecha=col_fecha)

    minimo_necesario = meses_entrenamiento + min(horizontes)
    if len(serie) < minimo_necesario:
        return None

    entrenamiento = serie.iloc[:meses_entrenamiento]

    # Ajustamos SOLO con la ventana de entrenamiento. `desde_el_pico=False`
    # porque `serie` ya arranca en el pico: recortarla otra vez seria un error.
    ajuste = ajustar_pozo(
        entrenamiento.assign(**{col_fecha: entrenamiento[col_fecha]}),
        id_pozo=id_pozo,
        col_caudal=col_caudal,
        col_fecha=col_fecha,
        meses_minimos=min(meses_entrenamiento, 9),
        d_terminal_anual=d_terminal_anual,
    )
    if ajuste is None or not ajuste.convergio:
        return None

    resultado: dict = {
        "id_pozo": str(id_pozo),
        "meses_entrenamiento": meses_entrenamiento,
        "meses_disponibles": len(serie),
        "r2_entrenamiento": round(ajuste.r2, 3),
        "b_entrenamiento": round(ajuste.b, 3),
    }

    futuro = serie.iloc[meses_entrenamiento:]
    t_futuro = futuro["t_meses"].to_numpy(dtype=float)
    q_futuro = futuro[col_caudal].to_numpy(dtype=float)

    t_corte = float(serie["t_meses"].iloc[meses_entrenamiento - 1])

    for h in horizontes:
        dentro = t_futuro < (t_corte + h)

        # Un pozo entra en el bucket de h meses SOLO si realmente vivio esos h
        # meses. Sin esta condicion, un pozo con 16 meses de historia posterior
        # al entrenamiento se contaria como si validara el horizonte de 36, y
        # el error a 36 meses quedaria calculado sobre pozos que nunca llegaron
        # ahi: el numero titular del proyecto seria falso.
        #
        # Se piden dos cosas:
        #   - que la serie llegue hasta (casi) el final del horizonte
        #   - que haya suficientes meses con produccion adentro, tolerando las
        #     paradas, que en un pozo real son normales
        llega_al_final = t_futuro.size and t_futuro.max() >= (t_corte + h - 3)
        meses_suficientes = dentro.sum() >= h * 0.6

        if not (llega_al_final and meses_suficientes):
            continue

        real = float(np.sum(q_futuro[dentro]) * DIAS_POR_MES)
        predicho = float(np.sum(
            caudal_hiperbolica_modificada(
                t_futuro[dentro], ajuste.qi, ajuste.di_mensual, ajuste.b,
                d_terminal_anual=d_terminal_anual,
            )
        ) * DIAS_POR_MES)

        if real <= 0:
            continue

        resultado[f"real_{h}"] = real
        resultado[f"pred_{h}"] = predicho
        resultado[f"error_pct_{h}"] = round((predicho - real) / real * 100.0, 2)
        resultado[f"meses_evaluados_{h}"] = int(dentro.sum())

    # Si no se pudo evaluar ningun horizonte, el pozo no aporta nada.
    if not any(k.startswith("error_pct_") for k in resultado):
        return None

    return resultado


def backtest_muchos(
    df: pd.DataFrame,
    col_id: str = "id_pozo",
    col_caudal: str = "caudal_petroleo_m3d",
    col_fecha: str = "fecha",
    mostrar_progreso: bool = False,
    **kwargs,
) -> pd.DataFrame:
    """Corre el backtest sobre todos los pozos. Una fila por pozo evaluado."""
    filas = []
    grupos = df.groupby(col_id)
    total = len(grupos)

    for i, (id_pozo, grupo) in enumerate(grupos, start=1):
        if mostrar_progreso and (i % 250 == 0 or i == total):
            print(f"      {i:,}/{total:,} pozos ({i / total:.0%})", flush=True)
        r = backtest_pozo(grupo, id_pozo=id_pozo, col_caudal=col_caudal,
                          col_fecha=col_fecha, **kwargs)
        if r is not None:
            filas.append(r)

    return pd.DataFrame(filas)


def resumen(backtest: pd.DataFrame, horizontes: tuple[int, ...] = HORIZONTES) -> dict:
    """
    Convierte el backtest en los numeros que se muestran y se defienden.

    Por cada horizonte:
        pozos            cuantos pozos se pudieron evaluar
        error_mediano    mediana del error porcentual con signo (el SESGO:
                         positivo = el modelo sobreestima)
        error_absoluto   mediana del |error| (la PRECISION tipica)
        dentro_20        % de pozos con error dentro de +/- 20%
        p10 / p90        los extremos del error, para no esconder la cola
    """
    if backtest.empty:
        return {"suficientes_datos": False, "pozos": 0}

    salida: dict = {"suficientes_datos": True, "pozos_totales": int(len(backtest))}

    for h in horizontes:
        col = f"error_pct_{h}"
        if col not in backtest.columns:
            continue
        errores = backtest[col].dropna()
        if len(errores) < 10:
            continue

        salida[f"h{h}"] = {
            "pozos": int(len(errores)),
            "error_mediano": round(float(errores.median()), 1),
            "error_absoluto": round(float(errores.abs().median()), 1),
            "dentro_20": round(float((errores.abs() <= 20).mean() * 100), 1),
            "p10": round(float(errores.quantile(0.10)), 1),
            "p90": round(float(errores.quantile(0.90)), 1),
        }

    return salida


def frase_del_resultado(res: dict, horizonte: int = 36) -> str:
    """
    Traduce el resumen a una frase que se pueda decir en voz alta.

    Sirve para el README y para una entrevista: el numero solo no comunica,
    la frase si.
    """
    clave = f"h{horizonte}"
    if not res.get("suficientes_datos") or clave not in res:
        return "No hay pozos suficientes para validar el modelo a ese horizonte."

    d = res[clave]
    sentido = "sobreestima" if d["error_mediano"] > 0 else "subestima"
    return (
        f"Entrenado con {MESES_ENTRENAMIENTO} meses, el modelo predice la produccion "
        f"de los {horizonte} meses siguientes con un error absoluto mediano del "
        f"{d['error_absoluto']:.0f}%, evaluado sobre {d['pozos']:,} pozos que ya "
        f"produjeron ese periodo. {d['dentro_20']:.0f}% de los pozos caen dentro de "
        f"+/-20%. El modelo {sentido} de forma sistematica: el error mediano con "
        f"signo es {d['error_mediano']:+.0f}%."
    )
