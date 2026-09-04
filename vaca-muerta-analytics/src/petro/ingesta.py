"""
Ingesta de datos desde las fuentes publicas oficiales.

FUENTE PRINCIPAL: datos.energia.gob.ar
    Es el portal de datos abiertos de la Secretaria de Energia de la Nacion.
    Corre sobre CKAN, que es el software estandar de portales de datos abiertos
    y expone una API REST publica, SIN API KEY y sin registro.

    La API que usamos es `package_show`, que devuelve el metadato de un dataset
    incluyendo la lista de "resources" (los archivos CSV descargables) con su URL.
    Documentacion de CKAN: https://docs.ckan.org/en/latest/api/

FUENTE SECUNDARIA: EIA (U.S. Energy Information Administration)
    Para precios internacionales de crudo (WTI y Brent), que sirven de contexto
    macro. Requiere una API key gratuita: https://www.eia.gov/opendata/register.php

IMPORTANTE - unidades de los datos de la Secretaria:
    prod_pet  -> petroleo, en m3 por mes
    prod_gas  -> gas, en Mm3 (MILES de m3) por mes
    prod_agua -> agua, en m3 por mes
    tef       -> "tiempo efectivo de fluencia": DIAS del mes en que el pozo
                 efectivamente produjo. Es clave: para obtener el caudal diario
                 real hay que dividir por tef, NO por 30. Un pozo que produjo
                 3000 m3 en 10 dias tiene un caudal de 300 m3/d, no de 100.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import pandas as pd
import requests

# --- Endpoints y datasets -------------------------------------------------

CKAN_BASE = "https://datos.energia.gob.ar/api/3/action"

# Identificadores (slugs) de los datasets que nos interesan en el portal.
# Si alguno cambia de nombre, `buscar_datasets()` de abajo te ayuda a encontrarlo.
DATASETS = {
    # Produccion mensual POZO POR POZO de shale y tight. Este es EL dataset
    # del proyecto: sin el no hay curvas de declinacion.
    "no_convencional": "produccion-de-pozos-de-gas-y-petroleo-no-convencional",
    # Produccion convencional, por si queres comparar convencional vs shale.
    "convencional": "produccion-de-pozos-de-gas-y-petroleo-por-concesion-de-explotacion",
    # Datos de perforacion y terminacion (actividad). Sirve para cruzar
    # actividad de perforacion contra precio del crudo.
    "perforacion": "perforacion-de-pozos-de-gas-y-petroleo",
}

TIEMPO_ESPERA = 120  # segundos de timeout para las descargas (los CSV son grandes)


# --- Utilidades de descubrimiento ----------------------------------------

def buscar_datasets(consulta: str, filas: int = 10) -> pd.DataFrame:
    """
    Busca datasets en el portal por texto libre.

    Usala cuando un slug de DATASETS deje de funcionar (el portal a veces
    renombra datasets). Ejemplo:  buscar_datasets("no convencional")
    """
    respuesta = requests.get(
        f"{CKAN_BASE}/package_search",
        params={"q": consulta, "rows": filas},
        timeout=TIEMPO_ESPERA,
    )
    respuesta.raise_for_status()
    resultados = respuesta.json()["result"]["results"]
    return pd.DataFrame([
        {
            "slug": d.get("name"),
            "titulo": d.get("title"),
            "actualizado": d.get("metadata_modified"),
            "recursos": len(d.get("resources", [])),
        }
        for d in resultados
    ])


def listar_recursos(slug: str) -> pd.DataFrame:
    """
    Lista los archivos descargables de un dataset (nombre, formato, URL, tamaño).

    Un dataset del portal suele tener varios CSV: uno por año, o uno historico
    completo mas los del año en curso. Mirar esta tabla antes de descargar
    te ahorra bajar 800 MB al pedo.
    """
    respuesta = requests.get(
        f"{CKAN_BASE}/package_show",
        params={"id": slug},
        timeout=TIEMPO_ESPERA,
    )
    respuesta.raise_for_status()
    recursos = respuesta.json()["result"]["resources"]
    return pd.DataFrame([
        {
            "nombre": r.get("name"),
            "formato": (r.get("format") or "").upper(),
            "url": r.get("url"),
            "bytes": r.get("size"),
            "modificado": r.get("last_modified") or r.get("created"),
        }
        for r in recursos
    ])


# --- Descarga -------------------------------------------------------------

def descargar_recurso(url: str, destino: Path, forzar: bool = False) -> Path:
    """
    Descarga un archivo a disco, con cache: si ya existe no lo vuelve a bajar
    (salvo que pases forzar=True).

    Descarga en streaming (de a pedazos) para no cargar 500 MB en RAM.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and not forzar:
        print(f"[cache] ya existe, no se vuelve a descargar: {destino.name}")
        return destino

    print(f"[descargando] {url}")
    with requests.get(url, stream=True, timeout=TIEMPO_ESPERA) as r:
        r.raise_for_status()
        # Escribimos a un archivo temporal y recien al final renombramos, para
        # que una descarga cortada no deje un CSV corrupto en el cache.
        temporal = destino.with_suffix(destino.suffix + ".parcial")
        with open(temporal, "wb") as f:
            for pedazo in r.iter_content(chunk_size=1024 * 256):
                f.write(pedazo)
        temporal.rename(destino)

    mb = destino.stat().st_size / 1_000_000
    print(f"[ok] {destino.name} ({mb:.1f} MB)")
    return destino


def descargar_dataset(
    clave: str,
    carpeta_destino: Path,
    solo_csv: bool = True,
    forzar: bool = False,
    max_archivos: int | None = None,
    max_mb: float | None = None,
) -> list[Path]:
    """
    Descarga los recursos de un dataset de DATASETS a `carpeta_destino`.

    Ejemplo:
        descargar_dataset("no_convencional", Path("data/crudo"))

    Los limites `max_archivos` y `max_mb` existen para correr esto en un
    servidor de integracion continua, donde el disco es finito: un dataset del
    portal puede traer un CSV por año y sumar varios GB. Cuando hay limite se
    priorizan los recursos MAS RECIENTES, que son los que interesan para
    analizar produccion actual.
    """
    if clave not in DATASETS:
        raise ValueError(
            f"Clave desconocida: {clave!r}. Opciones: {list(DATASETS)}"
        )

    recursos = listar_recursos(DATASETS[clave])
    if solo_csv:
        recursos = recursos[recursos["formato"] == "CSV"]

    if recursos.empty:
        raise RuntimeError(
            f"El dataset {clave!r} no devolvio recursos CSV. "
            "Revisa con listar_recursos() si cambio el formato."
        )

    if max_archivos or max_mb:
        # Mas nuevo primero. `modificado` puede venir vacio: esos van al final.
        recursos = recursos.sort_values("modificado", ascending=False, na_position="last")

        if max_mb:
            bytes_acumulados, quedan = 0, []
            for _, fila in recursos.iterrows():
                tam = float(fila["bytes"]) if pd.notna(fila["bytes"]) else 0.0
                if quedan and (bytes_acumulados + tam) / 1e6 > max_mb:
                    break
                bytes_acumulados += tam
                quedan.append(fila)
            recursos = pd.DataFrame(quedan)

        if max_archivos:
            recursos = recursos.head(max_archivos)

        print(f"[limite] se descargan {len(recursos)} recurso(s) "
              f"(max_archivos={max_archivos}, max_mb={max_mb})")

    archivos = []
    for _, fila in recursos.iterrows():
        # Sanitizamos el nombre para que sea un nombre de archivo valido.
        nombre = "".join(
            c if c.isalnum() or c in "-_." else "_"
            for c in str(fila["nombre"])
        )[:120]
        archivos.append(
            descargar_recurso(
                fila["url"],
                Path(carpeta_destino) / f"{clave}__{nombre}.csv",
                forzar=forzar,
            )
        )
    return archivos


# --- Precios internacionales (EIA) ---------------------------------------

def precios_crudo_eia(
    serie: str = "PET.RWTC.M",
    api_key: str | None = None,
) -> pd.DataFrame:
    """
    Precio mensual del crudo desde la API de la EIA.

    Series utiles:
        PET.RWTC.M  -> WTI Cushing, promedio mensual, USD/bbl
        PET.RBRTE.M -> Brent Europa, promedio mensual, USD/bbl

    La API key gratuita se saca en https://www.eia.gov/opendata/register.php
    Guardala en la variable de entorno EIA_API_KEY, nunca hardcodeada en el
    codigo (si la commiteas al repo, queda publica para siempre).
    """
    api_key = api_key or os.environ.get("EIA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta la API key de EIA. Sacala gratis en "
            "https://www.eia.gov/opendata/register.php y exportala:\n"
            "  export EIA_API_KEY=tu_key_aca"
        )

    respuesta = requests.get(
        "https://api.eia.gov/v2/seriesid/" + serie,
        params={"api_key": api_key},
        timeout=TIEMPO_ESPERA,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()["response"]["data"]

    df = pd.DataFrame(datos)
    df["fecha"] = pd.to_datetime(df["period"])
    df = df.rename(columns={"value": "precio_usd_bbl"})
    return df[["fecha", "precio_usd_bbl"]].sort_values("fecha").reset_index(drop=True)


def leer_csv_local(ruta: Path, **kwargs) -> pd.DataFrame:
    """
    Lee un CSV descargado. Envuelto en una funcion propia porque los CSV del
    portal a veces vienen con encoding raro; asi el arreglo queda en un solo
    lugar en vez de repartido por todo el proyecto.
    """
    ruta = Path(ruta)
    try:
        return pd.read_csv(ruta, low_memory=False, **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(ruta, low_memory=False, encoding="latin-1", **kwargs)
