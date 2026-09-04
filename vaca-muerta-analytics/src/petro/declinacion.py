"""
Curvas de declinacion de pozos (analisis DCA - Decline Curve Analysis).

Este es el corazon tecnico del proyecto. Un pozo no convencional (shale) arranca
produciendo mucho y cae muy rapido los primeros meses: puede perder 60-70% de su
caudal en el primer año. Modelar esa caida sirve para:

  - Estimar cuanto va a producir el pozo en toda su vida (EUR).
  - Comparar la calidad de pozos entre operadoras, bloques y formaciones.
  - Proyectar produccion futura de un area.

El modelo estandar de la industria son las ecuaciones de Arps (1945), que
describen el caudal q en funcion del tiempo t con tres parametros:

    qi : caudal inicial (al inicio de la declinacion)
    Di : tasa de declinacion nominal inicial (1/mes en este modulo)
    b  : exponente de declinacion (adimensional)

Segun el valor de b:
    b = 0        -> declinacion exponencial   q = qi * exp(-Di*t)
    0 < b < 1    -> declinacion hiperbolica   q = qi / (1 + b*Di*t)^(1/b)
    b = 1        -> declinacion armonica      q = qi / (1 + Di*t)

En shale es tipico encontrar b > 1 en los primeros años. El problema es que con
b >= 1 la integral de la curva diverge: el modelo predice reservas infinitas.
Por eso la practica aceptada es la "hiperbolica modificada": se usa Arps
hiperbolica hasta que la declinacion instantanea baja a un valor terminal
(tipicamente 5-10% anual) y a partir de ahi se continua con exponencial.
Eso es lo que implementa este modulo.

NOTA DE UNIDADES: en todo el modulo el tiempo esta en MESES y Di en 1/mes.
El caudal q puede estar en cualquier unidad de volumen/dia (m3/d, bbl/d, Mm3/d),
y el EUR sale en esa misma unidad de volumen multiplicada por dias.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Dias promedio por mes: se usa para convertir un caudal diario a volumen mensual.
DIAS_POR_MES = 30.4375

# Declinacion terminal por defecto: 6% nominal anual, convertida a 1/mes.
# Es un valor conservador y habitual en evaluaciones de shale.
D_TERMINAL_ANUAL_DEFECTO = 0.06


# ---------------------------------------------------------------------------
# 1. Las ecuaciones de Arps
# ---------------------------------------------------------------------------

def caudal_arps(t, qi: float, di: float, b: float) -> np.ndarray:
    """
    Caudal en el tiempo t segun Arps.

    Parametros
    ----------
    t  : tiempo en meses desde el inicio de la declinacion (array o escalar)
    qi : caudal inicial (misma unidad que devuelve la funcion)
    di : declinacion nominal inicial, en 1/mes
    b  : exponente de declinacion

    Devuelve el caudal en las mismas unidades que qi.
    """
    t = np.asarray(t, dtype=float)

    # Caso exponencial: b practicamente cero. Se trata aparte porque la formula
    # hiperbolica se indefine (division por b).
    if b < 1e-6:
        return qi * np.exp(-di * t)

    # Caso hiperbolico / armonico.
    # np.maximum(..., 1e-9) evita que la base se vuelva <= 0 y rompa la potencia
    # si el optimizador prueba parametros absurdos durante el ajuste.
    base = np.maximum(1.0 + b * di * t, 1e-9)
    return qi / base ** (1.0 / b)


def acumulada_arps(t, qi: float, di: float, b: float) -> np.ndarray:
    """
    Produccion acumulada entre 0 y t, integrando la curva de Arps.

    Ojo: devuelve el acumulado en unidades de (caudal * MESES). Para pasarlo a
    volumen real hay que multiplicar por DIAS_POR_MES si el caudal es diario.
    La funcion `eur()` de mas abajo ya se encarga de eso.
    """
    t = np.asarray(t, dtype=float)

    if b < 1e-6:
        # Exponencial: Np = qi/Di * (1 - e^(-Di*t))
        return (qi / di) * (1.0 - np.exp(-di * t))

    if abs(b - 1.0) < 1e-6:
        # Armonica: Np = qi/Di * ln(1 + Di*t)
        return (qi / di) * np.log1p(di * t)

    # Hiperbolica general: Np = qi / (Di*(1-b)) * (1 - (1 + b*Di*t)^(1 - 1/b))
    base = np.maximum(1.0 + b * di * t, 1e-9)
    return (qi / (di * (1.0 - b))) * (1.0 - base ** (1.0 - 1.0 / b))


def _mes_de_cambio_a_exponencial(di: float, b: float, d_terminal_mensual: float) -> float:
    """
    Mes en el que la declinacion instantanea de la hiperbolica cae hasta el
    valor terminal. A partir de ese punto seguimos con exponencial.

    La declinacion instantanea de Arps es D(t) = Di / (1 + b*Di*t).
    Igualando a D_term y despejando t:  t_sw = (Di/D_term - 1) / (b*Di)
    """
    if b < 1e-6 or di <= d_terminal_mensual:
        # Ya es exponencial, o arranca declinando mas lento que el terminal:
        # nunca hay cambio de regimen.
        return np.inf
    return (di / d_terminal_mensual - 1.0) / (b * di)


def caudal_hiperbolica_modificada(
    t,
    qi: float,
    di: float,
    b: float,
    d_terminal_anual: float = D_TERMINAL_ANUAL_DEFECTO,
) -> np.ndarray:
    """
    Caudal con el modelo hiperbolico modificado (Arps hasta el mes de cambio,
    exponencial de ahi en adelante). Es el modelo que se usa para pronosticos
    largos porque no diverge.
    """
    t = np.atleast_1d(np.asarray(t, dtype=float))
    d_term = d_terminal_anual / 12.0
    t_sw = _mes_de_cambio_a_exponencial(di, b, d_term)

    q = caudal_arps(t, qi, di, b)

    # Para los meses posteriores al cambio, reemplazamos por la exponencial que
    # arranca en el caudal del mes de cambio.
    if np.isfinite(t_sw):
        posterior = t > t_sw
        if posterior.any():
            q_sw = float(caudal_arps(t_sw, qi, di, b))
            q[posterior] = q_sw * np.exp(-d_term * (t[posterior] - t_sw))

    return q


# ---------------------------------------------------------------------------
# 2. El resultado de un ajuste
# ---------------------------------------------------------------------------

@dataclass
class AjusteDeclinacion:
    """Resultado del ajuste de una curva de declinacion a un pozo."""

    id_pozo: str
    qi: float               # caudal inicial ajustado (misma unidad que los datos)
    di_mensual: float       # declinacion nominal inicial, 1/mes
    di_anual: float         # la misma declinacion expresada como % nominal anual
    b: float                # exponente de Arps
    r2: float               # bondad de ajuste (1 = perfecto)
    rmse: float             # error cuadratico medio, en unidades de caudal
    n_meses: int            # cuantos puntos se usaron para ajustar
    eur: float              # produccion estimada total (volumen)
    eur_unidad: str         # etiqueta de la unidad del EUR
    convergio: bool         # False si el optimizador fallo y se usaron defaults

    def como_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 3. Ajuste sobre datos reales
# ---------------------------------------------------------------------------

def preparar_serie(
    df_pozo: pd.DataFrame,
    col_caudal: str = "caudal_petroleo_m3d",
    col_fecha: str = "fecha",
    desde_el_pico: bool = True,
    caudal_minimo: float = 0.1,
) -> pd.DataFrame:
    """
    Deja la serie de un pozo lista para ajustar.

    Tres cosas importantes que hace:

    1. Ordena por fecha y descarta meses sin produccion (ceros, nulos, paradas).
       Un mes en cero no significa que el pozo declino: significa que estuvo
       parado. Si no los sacamos, el ajuste se rompe.

    2. Arranca desde el PICO de produccion. Los pozos de shale suelen tardar
       1-3 meses en alcanzar su maximo (limpieza del pozo, rampa de puesta en
       marcha). La declinacion se modela desde el pico en adelante, no desde
       el primer mes.

    3. Agrega la columna `t_meses`: meses transcurridos desde el pico. Es la
       variable independiente del ajuste.
    """
    df = df_pozo.copy()
    df = df.sort_values(col_fecha)
    df = df[df[col_caudal].notna() & (df[col_caudal] > caudal_minimo)]

    if df.empty:
        return df

    if desde_el_pico:
        # idxmax devuelve el indice del maximo; nos quedamos desde ahi.
        pos_pico = df[col_caudal].values.argmax()
        df = df.iloc[pos_pico:]

    # Meses transcurridos desde el primer punto (el pico).
    fecha0 = df[col_fecha].iloc[0]
    df = df.assign(
        t_meses=(df[col_fecha] - fecha0).dt.days / DIAS_POR_MES
    )
    return df


def ajustar_pozo(
    df_pozo: pd.DataFrame,
    id_pozo: str = "s/d",
    col_caudal: str = "caudal_petroleo_m3d",
    col_fecha: str = "fecha",
    b_maximo: float = 2.0,
    meses_minimos: int = 6,
    horizonte_meses: int = 360,
    d_terminal_anual: float = D_TERMINAL_ANUAL_DEFECTO,
    unidad: str = "m3",
) -> AjusteDeclinacion | None:
    """
    Ajusta una curva de Arps a la historia de produccion de UN pozo y estima
    su EUR (Estimated Ultimate Recovery = produccion total esperada en su vida).

    Devuelve None si el pozo no tiene suficientes meses utiles para ajustar.

    Parametros clave
    ----------------
    meses_minimos    : abajo de esto el ajuste no es confiable, se descarta.
    horizonte_meses  : vida util asumida para el EUR (360 meses = 30 años).
    b_maximo         : cota superior de b. En shale es normal b > 1.
    """
    serie = preparar_serie(df_pozo, col_caudal=col_caudal, col_fecha=col_fecha)

    if len(serie) < meses_minimos:
        return None

    t = serie["t_meses"].to_numpy(dtype=float)
    q = serie[col_caudal].to_numpy(dtype=float)

    # --- Semilla inicial (p0) ---
    # Un buen punto de partida ayuda muchisimo a que el optimizador converja.
    qi_0 = float(q[0])
    # Estimacion cruda de Di: cuanto cayo entre el primer y el ultimo punto.
    if len(t) > 1 and q[-1] > 0 and t[-1] > 0:
        di_0 = float(np.log(q[0] / q[-1]) / t[-1])
        di_0 = float(np.clip(di_0, 0.005, 0.5))
    else:
        di_0 = 0.05
    b_0 = 1.0

    # --- Cotas ---
    # qi no puede ser negativo ni absurdamente mayor al maximo observado.
    # Di entre 0.1%/mes y 60%/mes. b entre casi-exponencial y b_maximo.
    cotas = (
        [1e-6, 1e-4, 1e-3],
        [qi_0 * 5.0 + 1.0, 0.6, b_maximo],
    )

    convergio = True
    try:
        parametros, _ = curve_fit(
            caudal_arps,
            t,
            q,
            p0=[qi_0, di_0, b_0],
            bounds=cotas,
            maxfev=20000,
        )
        qi, di, b = (float(x) for x in parametros)
    except Exception:
        # Si no converge no rompemos el pipeline: marcamos el pozo y seguimos
        # con la semilla. Despues se puede filtrar por `convergio` o por r2.
        qi, di, b = qi_0, di_0, b_0
        convergio = False

    # --- Bondad de ajuste ---
    q_modelo = caudal_arps(t, qi, di, b)
    residuos = q - q_modelo
    ss_res = float(np.sum(residuos ** 2))
    ss_tot = float(np.sum((q - q.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    rmse = float(np.sqrt(np.mean(residuos ** 2)))

    # --- EUR ---
    eur_valor = eur(
        qi, di, b,
        horizonte_meses=horizonte_meses,
        d_terminal_anual=d_terminal_anual,
    )

    return AjusteDeclinacion(
        id_pozo=str(id_pozo),
        qi=qi,
        di_mensual=di,
        di_anual=di * 12.0,
        b=b,
        r2=r2,
        rmse=rmse,
        n_meses=len(serie),
        eur=eur_valor,
        eur_unidad=unidad,
        convergio=convergio,
    )


def eur(
    qi: float,
    di: float,
    b: float,
    horizonte_meses: int = 360,
    d_terminal_anual: float = D_TERMINAL_ANUAL_DEFECTO,
) -> float:
    """
    EUR (Estimated Ultimate Recovery): volumen total que se espera producir en
    `horizonte_meses`, usando el modelo hiperbolico modificado.

    Se calcula integrando numericamente la curva mes a mes. Podria hacerse con
    la formula analitica, pero la integracion numerica es mas facil de auditar
    y el costo computacional es despreciable.

    Devuelve volumen (caudal diario * dias), es decir m3 si el caudal era m3/d.
    """
    meses = np.arange(0, horizonte_meses, 1.0)
    caudales = caudal_hiperbolica_modificada(
        meses, qi, di, b, d_terminal_anual=d_terminal_anual
    )
    return float(np.sum(caudales) * DIAS_POR_MES)


def pronostico(
    ajuste: AjusteDeclinacion,
    horizonte_meses: int = 120,
    d_terminal_anual: float = D_TERMINAL_ANUAL_DEFECTO,
) -> pd.DataFrame:
    """
    Genera la curva pronosticada a futuro para graficar sobre los datos reales.
    Devuelve un DataFrame con columnas `t_meses` y `caudal_modelo`.
    """
    meses = np.arange(0, horizonte_meses, 1.0)
    caudales = caudal_hiperbolica_modificada(
        meses, ajuste.qi, ajuste.di_mensual, ajuste.b,
        d_terminal_anual=d_terminal_anual,
    )
    return pd.DataFrame({"t_meses": meses, "caudal_modelo": caudales})


def ajustar_muchos_pozos(
    df: pd.DataFrame,
    col_id: str = "id_pozo",
    col_caudal: str = "caudal_petroleo_m3d",
    col_fecha: str = "fecha",
    mostrar_progreso: bool = False,
    **kwargs,
) -> pd.DataFrame:
    """
    Aplica `ajustar_pozo` a todos los pozos de un DataFrame y devuelve una
    tabla con un renglon por pozo. Esta es la tabla que alimenta los rankings
    del dashboard (mejores pozos, comparacion entre operadoras, etc.).

    Con los datos oficiales esto son miles de ajustes no lineales y puede
    tardar varios minutos, asi que `mostrar_progreso=True` imprime avance para
    que no parezca que el programa se colgo.
    """
    resultados = []
    grupos = df.groupby(col_id)
    total = len(grupos)

    for i, (id_pozo, grupo) in enumerate(grupos, start=1):
        if mostrar_progreso and (i % 250 == 0 or i == total):
            print(f"      {i:,}/{total:,} pozos ({i / total:.0%})", flush=True)
        ajuste = ajustar_pozo(
            grupo,
            id_pozo=id_pozo,
            col_caudal=col_caudal,
            col_fecha=col_fecha,
            **kwargs,
        )
        if ajuste is not None:
            resultados.append(ajuste.como_dict())

    if not resultados:
        return pd.DataFrame()

    return pd.DataFrame(resultados).sort_values("eur", ascending=False)


def curva_tipo(
    df: pd.DataFrame,
    col_id: str = "id_pozo",
    col_caudal: str = "caudal_petroleo_m3d",
    col_fecha: str = "fecha",
    percentiles: tuple[float, ...] = (0.1, 0.5, 0.9),
) -> pd.DataFrame:
    """
    Curva tipo ("type curve") de un conjunto de pozos: para cada mes de vida,
    los percentiles del caudal de todos los pozos del grupo.

    Es la forma en que la industria compara bloques y operadoras: en lugar de
    mirar pozo por pozo, se mira el comportamiento tipico del conjunto,
    alineando todos los pozos por su mes de vida (no por fecha calendario).

    P10 / P50 / P90 aca son percentiles estadisticos: P90 es el mejor caso de
    caudal (el 90% de los pozos produce menos que eso).
    """
    series = []
    for id_pozo, grupo in df.groupby(col_id):
        s = preparar_serie(grupo, col_caudal=col_caudal, col_fecha=col_fecha)
        if s.empty:
            continue
        # Redondeamos el mes de vida a entero para poder agrupar entre pozos.
        s = s.assign(mes_vida=s["t_meses"].round().astype(int), id_pozo=id_pozo)
        series.append(s[["id_pozo", "mes_vida", col_caudal]])

    if not series:
        return pd.DataFrame()

    todos = pd.concat(series, ignore_index=True)
    agregado = todos.groupby("mes_vida")[col_caudal].quantile(list(percentiles)).unstack()
    agregado.columns = [f"p{int(p * 100)}" for p in percentiles]
    agregado["n_pozos"] = todos.groupby("mes_vida")[col_caudal].count()
    return agregado.reset_index()
