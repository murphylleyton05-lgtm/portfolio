"""
Datos de fractura (completacion) y normalizacion de la productividad.

POR QUE ESTE MODULO ES EL MAS IMPORTANTE DEL PROYECTO
-----------------------------------------------------
Sin el, cualquier ranking de pozos esta CONFUNDIDO.

Un pozo horizontal de 3.000 m de rama lateral produce mas que uno de 1.500 m
aunque la roca sea exactamente igual de buena: simplemente atraviesa el doble
de reservorio. Comparar el EUR crudo de dos pozos, o de dos bloques, y concluir
"aca la roca es mejor" es un error: puede ser que sus pozos sean mas largos.

La industria resuelve esto normalizando: en vez de comparar EUR, se compara
EUR POR METRO DE RAMA LATERAL (y por etapa de fractura). Eso es lo que hace
este modulo, y es la diferencia entre un analisis anecdotico y uno defendible.

EL PROBLEMA DE LOS NOMBRES DE COLUMNA
-------------------------------------
El portal renombra columnas cada tanto y no todos los CSV usan la misma
convencion. En vez de un mapeo fijo que se rompe, aca buscamos cada columna
por PATRON: "la que contenga 'rama' y 'horizontal'", "la que hable de
'fractura' y 'cantidad'". Es mas robusto y sobrevive a los renombres.

Si un patron no encuentra nada, se avisa con el listado de columnas que si
vinieron, en vez de fallar con un KeyError incomprensible.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Cada campo del esquema normalizado, con los patrones que lo identifican.
# Se prueba en orden: el primero que matchee gana. Todos los patrones se
# evaluan sobre el nombre de columna en minusculas y sin acentos.
PATRONES: dict[str, list[str]] = {
    "id_pozo":       [r"^idpozo$", r"^id_pozo$", r"\bidpozo\b"],
    "sigla":         [r"^sigla$", r"nombre.*pozo"],
    "empresa":       [r"^empresa", r"operador"],
    "area":          [r"areayacimiento", r"^area", r"yacimiento"],
    "formacion":     [r"formacion", r"^formprod$"],
    "tipo_recurso":  [r"sub.?tipo.?recurso", r"tipo.?de.?recurso", r"reservorio"],
    # Los tres que realmente importan para normalizar:
    "rama_m":        [r"longitud.*rama", r"rama.*horizontal", r"longitud.*horizontal",
                      r"\blateral\b.*\b(m|metros|longitud)\b"],
    "etapas":        [r"cantidad.*fractura", r"etapas.*fractura", r"^etapas?$",
                      r"cantidad.*etapas", r"n.?fracturas"],
    "arena_tn":      [r"arena.*total", r"arena.*bombeada", r"^arena", r"agente.*sosten"],
    "agua_m3":       [r"agua.*inyectada", r"agua.*total", r"^agua"],
    "fecha_fractura": [r"fecha.*fin.*fractura", r"fecha.*fractura", r"fecha_data"],
}

# Columnas de arena que suelen venir partidas (nacional / importada) y hay que sumar.
PATRON_ARENA_PARTIDA = r"arena.*(nacional|importada|origen)"

# Filtros de cordura. Un pozo con 50 m de rama o con 20.000 m no es un pozo:
# es un dato mal cargado, y si no se filtra arruina todos los promedios.
RAMA_MINIMA_M = 300.0
RAMA_MAXIMA_M = 8000.0
ETAPAS_MINIMAS = 3
ETAPAS_MAXIMAS = 120


def _normalizar_texto(s: str) -> str:
    """Pasa a minusculas y saca acentos, para que los patrones matcheen igual."""
    s = str(s).strip().lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        s = s.replace(a, b)
    return s


def detectar_columnas(columnas: list[str]) -> dict[str, str]:
    """
    Mapea cada campo del esquema al nombre real de columna que le corresponde.

    Devuelve solo los campos que encontro. Es una funcion pura y sin efectos,
    asi que es facil de testear con nombres de columna inventados.
    """
    normalizadas = {c: _normalizar_texto(c) for c in columnas}
    hallados: dict[str, str] = {}

    for campo, patrones in PATRONES.items():
        for patron in patrones:
            for original, norm in normalizadas.items():
                if re.search(patron, norm) and original not in hallados.values():
                    hallados[campo] = original
                    break
            if campo in hallados:
                break

    return hallados


def normalizar(df_crudo: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte el CSV de fractura al esquema del proyecto.

    Devuelve una fila por pozo con: id_pozo, rama_m, etapas, arena_tn, agua_m3
    y los atributos que haya. Si un pozo aparece varias veces (refractura,
    varias etapas cargadas por separado) se consolida: la rama se toma como el
    maximo declarado y las etapas/arena/agua se suman.
    """
    df = df_crudo.copy()
    df.columns = [str(c).strip() for c in df.columns]

    mapa = detectar_columnas(list(df.columns))

    if "id_pozo" not in mapa:
        raise ValueError(
            "No encontre la columna de id de pozo en el archivo de fractura.\n"
            f"Columnas recibidas: {sorted(df.columns)[:30]}\n"
            "Agrega el patron que corresponda en PATRONES, en fractura.py."
        )
    if "rama_m" not in mapa and "etapas" not in mapa:
        raise ValueError(
            "El archivo no trae ni longitud de rama ni cantidad de etapas: sin "
            "alguna de las dos no se puede normalizar la productividad.\n"
            f"Columnas recibidas: {sorted(df.columns)[:30]}"
        )

    salida = pd.DataFrame({"id_pozo": df[mapa["id_pozo"]].astype("string")})

    for campo in ("rama_m", "etapas", "arena_tn", "agua_m3"):
        if campo in mapa:
            salida[campo] = pd.to_numeric(df[mapa[campo]], errors="coerce")
        else:
            salida[campo] = np.nan

    # La arena suele venir partida en nacional e importada. Cuando estan las
    # partes, MANDAN sobre cualquier columna unica que hayamos detectado: la
    # deteccion por patron puede haber agarrado una de las partes creyendo que
    # era el total, y quedarse con esa seria subestimar la arena del pozo.
    partidas = [c for c in df.columns
                if re.search(PATRON_ARENA_PARTIDA, _normalizar_texto(c))]
    if partidas:
        suma = sum(pd.to_numeric(df[c], errors="coerce").fillna(0) for c in partidas)
        salida["arena_tn"] = suma.replace(0, np.nan)

    for campo in ("sigla", "empresa", "area", "formacion", "tipo_recurso"):
        if campo in mapa:
            salida[campo] = df[mapa[campo]].astype("string").str.strip()

    # --- filtros de cordura ---
    fuera_de_rango = (
        salida["rama_m"].notna()
        & ((salida["rama_m"] < RAMA_MINIMA_M) | (salida["rama_m"] > RAMA_MAXIMA_M))
    )
    salida.loc[fuera_de_rango, "rama_m"] = np.nan

    etapas_absurdas = (
        salida["etapas"].notna()
        & ((salida["etapas"] < ETAPAS_MINIMAS) | (salida["etapas"] > ETAPAS_MAXIMAS))
    )
    salida.loc[etapas_absurdas, "etapas"] = np.nan

    # --- consolidar a una fila por pozo ---
    agregaciones = {
        "rama_m": "max",        # la rama del pozo es una sola: el maximo declarado
        "etapas": "sum",        # las etapas pueden venir cargadas por tandas
        "arena_tn": "sum",
        "agua_m3": "sum",
    }
    for campo in ("sigla", "empresa", "area", "formacion", "tipo_recurso"):
        if campo in salida.columns:
            agregaciones[campo] = "first"

    consolidado = salida.groupby("id_pozo", as_index=False).agg(agregaciones)

    # Un sum() sobre puros NaN devuelve 0, que aca significaria "cero etapas".
    # No es cierto: significa "no declarado". Lo devolvemos a nulo.
    for campo in ("etapas", "arena_tn", "agua_m3"):
        consolidado.loc[consolidado[campo] == 0, campo] = np.nan

    return consolidado


def unir_con_ajustes(ajustes: pd.DataFrame, fractura: pd.DataFrame) -> pd.DataFrame:
    """
    Pega los datos de completacion a los resultados del ajuste de declinacion
    y calcula las metricas normalizadas.

    Metricas que agrega:
        eur_por_metro   EUR dividido por la longitud de rama lateral
        eur_por_etapa   EUR dividido por la cantidad de etapas de fractura
        arena_por_metro intensidad de completacion (toneladas por metro)
        agua_por_metro  intensidad de completacion (m3 por metro)

    `eur_por_metro` es LA metrica: es la que permite decir si un bloque es
    mejor por la roca o solo porque ahi se perforan pozos mas largos.
    """
    df = ajustes.merge(
        fractura.drop(columns=[c for c in ("empresa", "area", "formacion",
                                           "tipo_recurso", "sigla")
                               if c in fractura.columns]),
        on="id_pozo",
        how="left",
    )

    with np.errstate(divide="ignore", invalid="ignore"):
        df["eur_por_metro"] = df["eur"] / df["rama_m"]
        df["eur_por_etapa"] = df["eur"] / df["etapas"]
        df["arena_por_metro"] = df["arena_tn"] / df["rama_m"]
        df["agua_por_metro"] = df["agua_m3"] / df["rama_m"]

    df["tiene_fractura"] = df["rama_m"].notna()
    return df


def cuanto_explica_la_rama(df: pd.DataFrame) -> dict:
    """
    Cuantifica el problema que este modulo resuelve.

    Devuelve, para los pozos con datos de fractura:
      - correlacion entre longitud de rama y EUR
      - que fraccion de la varianza del EUR explica la rama sola (r²)
      - cuantos puestos se mueve el ranking al normalizar

    Este es el numero para el titular del analisis: si la rama explica, por
    decir, el 40% de la diferencia de EUR entre pozos, entonces cualquier
    ranking sin normalizar esta diciendo mas sobre ingenieria de perforacion
    que sobre calidad de roca.
    """
    d = df[df["rama_m"].notna() & df["eur"].notna()].copy()

    if len(d) < 10:
        return {"pozos": len(d), "suficientes_datos": False}

    correlacion = float(d["rama_m"].corr(d["eur"]))

    d["puesto_crudo"] = d["eur"].rank(ascending=False, method="min")
    d["puesto_normalizado"] = d["eur_por_metro"].rank(ascending=False, method="min")
    d["cambio_de_puesto"] = (d["puesto_crudo"] - d["puesto_normalizado"]).abs()

    # Cuantos pozos del top 10 crudo siguen en el top 10 normalizado.
    top_crudo = set(d.nsmallest(10, "puesto_crudo")["id_pozo"])
    top_norm = set(d.nsmallest(10, "puesto_normalizado")["id_pozo"])

    return {
        "pozos": int(len(d)),
        "suficientes_datos": True,
        "correlacion_rama_eur": round(correlacion, 3),
        "varianza_explicada": round(correlacion ** 2, 3),
        "rama_mediana_m": round(float(d["rama_m"].median())),
        "cambio_de_puesto_mediano": int(d["cambio_de_puesto"].median()),
        "cambio_de_puesto_maximo": int(d["cambio_de_puesto"].max()),
        "top10_que_sobrevive": len(top_crudo & top_norm),
    }
