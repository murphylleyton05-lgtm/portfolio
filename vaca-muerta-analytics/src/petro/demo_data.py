"""
Generador de datos de DEMOSTRACION.

Por que existe este archivo: para que la app funcione end-to-end sin depender
de la descarga (que son cientos de MB y puede fallar por red, por cambios en
el portal, o porque estas mostrando el proyecto en una entrevista sin wifi).

Los datos que genera NO son reales. Son sinteticos, pero construidos con la
misma fisica que los reales: cada pozo se simula con una curva de Arps con
parametros sorteados de rangos plausibles para shale de Vaca Muerta, mas ruido
operativo y meses de parada. Eso hace que el ajuste de declinacion tenga algo
real que encontrar, y que los graficos se parezcan a los de verdad.

IMPORTANTE: el generador emite el esquema CRUDO OFICIAL (idpozo, prod_pet, tef,
anio, mes, ...), no el normalizado. Asi los datos demo pasan exactamente por el
mismo pipeline de limpieza que los reales, y no hay dos caminos que mantener.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .declinacion import caudal_arps

# Operadoras reales del sector, usadas solo como etiquetas verosimiles.
# Los numeros asociados son inventados.
OPERADORAS = [
    "YPF S.A.",
    "VISTA ENERGY ARGENTINA",
    "PAN AMERICAN ENERGY",
    "SHELL ARGENTINA",
    "TECPETROL",
    "PLUSPETROL",
    "CHEVRON ARGENTINA",
    "PAMPA ENERGIA",
]

# Bloques de Vaca Muerta. Cada uno con un "factor de calidad" que multiplica el
# caudal inicial: asi el dataset tiene bloques mejores y peores, que es
# exactamente lo que despues detecta el analisis.
BLOQUES = {
    "LOMA CAMPANA": 1.00,
    "BAJADA DEL PALO OESTE": 1.25,
    "FORTIN DE PIEDRA": 0.85,
    "LA AMARGA CHICA": 1.10,
    "AGUADA PICHANA ESTE": 0.80,
    "EL OREJANO": 0.70,
    "BANDURRIA SUR": 1.30,
    "CORONEL CORNEJO": 0.65,
}


def generar_pozos(
    n_pozos: int = 120,
    mes_inicio: str = "2018-01",
    mes_fin: str = "2026-08",
    semilla: int = 42,
) -> pd.DataFrame:
    """
    Genera un dataset sintetico en el esquema crudo oficial.

    Parametros
    ----------
    n_pozos  : cuantos pozos simular
    semilla  : fija el generador aleatorio. Misma semilla = mismos datos.
               Esto es importante para que el proyecto sea REPRODUCIBLE: si
               alguien corre tu codigo, tiene que ver exactamente tus numeros.

    Devuelve DOS DataFrames:
      - produccion: una fila por pozo-mes (esquema del Capitulo IV)
      - fractura:   una fila por pozo (esquema del Anexo IV de fractura)
    """
    rng = np.random.default_rng(semilla)

    inicio = pd.Timestamp(mes_inicio)
    fin = pd.Timestamp(mes_fin)
    meses_totales = (fin.year - inicio.year) * 12 + (fin.month - inicio.month)

    filas: list[dict] = []
    geometrias: list[dict] = []

    for i in range(n_pozos):
        id_pozo = 100000 + i
        operadora = OPERADORAS[rng.integers(len(OPERADORAS))]
        bloque = list(BLOQUES)[rng.integers(len(BLOQUES))]
        calidad = BLOQUES[bloque]

        # Cada pozo entra en produccion en un mes distinto, con mas pozos
        # nuevos en los ultimos años (el boom de Vaca Muerta es reciente).
        # rng.beta(2, 1) sesga el sorteo hacia el final del periodo.
        mes_puesta = int(rng.beta(2.0, 1.0) * (meses_totales - 12))
        fecha_puesta = inicio + pd.DateOffset(months=mes_puesta)

        # --- Geometria del pozo ---
        # Longitud de rama lateral, en metros. En Vaca Muerta el rango tipico
        # va de 1.500 a 3.500 m, y viene creciendo con los años: los pozos mas
        # nuevos son mas largos. Eso se simula con el termino de `mes_puesta`.
        rama_m = float(rng.normal(1800 + 0.006 * mes_puesta * 1000, 400))
        rama_m = float(np.clip(rama_m, 900, 4200))
        # Etapas de fractura: aproximadamente una cada 55-70 m de rama.
        etapas = int(round(rama_m / rng.uniform(55, 70)))

        # --- Parametros de la curva del pozo ---
        # qi: caudal inicial en m3/d. Depende de DOS cosas: la calidad de la
        # roca del bloque y CUANTO RESERVORIO ATRAVIESA el pozo.
        #
        # Esa segunda dependencia es el punto de todo el analisis: un pozo mas
        # largo produce mas aunque la roca sea igual. Aca la metemos a
        # proposito, escalando con la rama respecto de una de referencia de
        # 2.500 m, para que el analisis tenga el efecto real que debe corregir.
        factor_rama = (rama_m / 2500.0) ** 0.85
        qi = float(rng.lognormal(mean=np.log(140 * calidad * factor_rama), sigma=0.35))
        # Di: declinacion nominal mensual. 0.10-0.22 /mes es tipico de shale.
        di = float(rng.uniform(0.10, 0.22))
        # b: exponente. En shale suele estar entre 0.8 y 1.6.
        b = float(rng.uniform(0.8, 1.6))

        # Relacion gas-petroleo (GOR): cuantos m3 de gas por m3 de petroleo.
        gor = float(rng.uniform(80, 260))
        # Corte de agua inicial y su crecimiento con el tiempo.
        agua_base = float(rng.uniform(0.15, 0.6))

        geometrias.append({
            "idpozo": id_pozo,
            "sigla": f"{bloque[:3]}.x-{id_pozo}",
            "empresa": operadora,
            "areayacimiento": bloque,
            "formacion_productiva": "VMUT",
            "tipo_reservorio": "SHALE",
            "longitud_rama_horizontal_m": round(rama_m, 1),
            "cantidad_fracturas": etapas,
            # Intensidad de completacion: toneladas de arena y m3 de agua por
            # metro de rama, con dispersion entre operadoras.
            "arena_bombeada_nacional_tn": round(rama_m * rng.uniform(0.9, 1.6), 1),
            "arena_bombeada_importada_tn": round(rama_m * rng.uniform(0.05, 0.3), 1),
            "agua_inyectada_m3": round(rama_m * rng.uniform(18, 32), 1),
            "fecha_fin_fractura": fecha_puesta.strftime("%Y-%m-%d"),
        })

        meses_vida = meses_totales - mes_puesta

        for m in range(meses_vida):
            fecha = fecha_puesta + pd.DateOffset(months=m)
            if fecha > fin:
                break

            # Rampa de puesta en marcha: los primeros 1-2 meses el pozo todavia
            # no llego a su pico (limpieza, ajuste de instalaciones).
            factor_rampa = 1.0 if m >= 2 else (0.55 if m == 0 else 0.9)

            caudal_teorico = float(caudal_arps(m, qi, di, b)) * factor_rampa

            # Ruido operativo multiplicativo (+-12%): mediciones, ajustes,
            # variabilidad normal de la operacion.
            caudal_real = caudal_teorico * float(rng.normal(1.0, 0.12))
            caudal_real = max(caudal_real, 0.0)

            # Dias efectivos de produccion en el mes (tef).
            # Casi siempre el mes completo, pero un 6% de los meses hay una
            # parada parcial (mantenimiento, falla, restriccion de evacuacion)
            # y un 2% el pozo esta parado todo el mes.
            sorteo = rng.random()
            if sorteo < 0.02:
                dias = 0.0
            elif sorteo < 0.08:
                dias = float(rng.uniform(5, 25))
            else:
                dias = float(rng.uniform(28, 31))

            volumen_petroleo = caudal_real * dias
            volumen_gas = volumen_petroleo * gor / 1000.0  # a Mm3 (miles de m3)
            # El corte de agua crece con el tiempo, como en la realidad.
            volumen_agua = volumen_petroleo * (agua_base + 0.012 * m)

            filas.append({
                "idpozo": id_pozo,
                "sigla": f"{bloque[:3]}.x-{id_pozo}",
                "anio": fecha.year,
                "mes": fecha.month,
                "empresa": operadora,
                "areayacimiento": bloque,
                "cuenca": "NEUQUINA",
                "provincia": "NEUQUEN",
                "formprod": "VMUT",
                "sub_tipo_recurso": "SHALE",
                "tipo_de_recurso": "NO CONVENCIONAL",
                "tipopozo": "Petrolifero",
                "tipoextraccion": "Bombeo Mecanico" if rng.random() < 0.4 else "Surgente",
                "tipoestado": "Produciendo",
                "prod_pet": round(volumen_petroleo, 2),
                "prod_gas": round(volumen_gas, 2),
                "prod_agua": round(volumen_agua, 2),
                "tef": round(dias, 1),
            })

    return pd.DataFrame(filas), pd.DataFrame(geometrias)


def generar_precios(
    mes_inicio: str = "2018-01",
    mes_fin: str = "2026-08",
    semilla: int = 42,
) -> pd.DataFrame:
    """
    Serie sintetica de precio del crudo (USD/bbl), para la seccion de contexto
    macro del dashboard mientras no tengas la API key de la EIA.

    Se construye como una caminata aleatoria con reversion a la media, mas un
    desplome en 2020 que imita el shock de la pandemia. No es un pronostico ni
    un dato real: es relleno visual honesto y etiquetado como tal.
    """
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range(mes_inicio, mes_fin, freq="MS")

    precios = []
    precio = 65.0
    for fecha in fechas:
        # Reversion a la media hacia 70 USD/bbl, con volatilidad mensual.
        precio += 0.15 * (70.0 - precio) + rng.normal(0, 5.5)
        if fecha.year == 2020 and fecha.month in (3, 4, 5):
            precio *= 0.55  # shock COVID
        precios.append(max(precio, 15.0))

    return pd.DataFrame({"fecha": fechas, "precio_usd_bbl": np.round(precios, 2)})
