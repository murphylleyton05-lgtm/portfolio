"""
Genera la app web a partir de los datos ya procesados.

La app de web/ es un solo archivo HTML con los datos adentro: no consulta ningun
servidor, no necesita Python instalado y funciona con doble clic. Este script es
el que mete los datos en la plantilla.

Corrrelo cada vez que actualices los datos. Si no lo corres, la app sigue
mostrando los datos de la ultima vez.

Uso:
    python scripts/generar_web.py
    python scripts/generar_web.py --max-pozos 400

Salidas:
    web/index.html      pagina completa, para abrir con doble clic o publicar
    web/artifact.html   el mismo contenido sin <html>/<head>, para publicar
                        como artifact de Claude
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config, declinacion  # noqa: E402
from petro.limpieza import BARRILES_POR_M3  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
PLANTILLA = RAIZ / "web" / "plantilla.html"

# Envoltorio para la version que se abre sola en el navegador.
ENVOLTORIO = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{margin:0;font:14px system-ui}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{cabeza}</head>
<body>
{cuerpo}</body>
</html>
"""


def seleccionar_confiables(ajustes: pd.DataFrame) -> pd.DataFrame:
    """
    Los ajustes en los que se puede confiar: R2 suficiente, convergidos, y con
    `b` por debajo del tope del optimizador.

    Es una funcion aparte y pura para poder testearla: el criterio de "confiable"
    decide que pozos entran al ranking y a la economia, asi que un cambio
    silencioso aca cambia todos los numeros del proyecto.
    """
    return ajustes[
        (ajustes["r2"] >= config.R2_MINIMO_CONFIABLE)
        & ajustes["convergio"]
        & (ajustes["b"] < config.B_EN_EL_TOPE)
    ]


def armar_datos(max_pozos: int, meses_minimos: int) -> dict:
    """
    Arma el JSON que se incrusta en la app.

    Con datos reales pueden ser miles de pozos. Meterlos todos haria un HTML de
    decenas de MB que tarda en abrir, asi que nos quedamos con los `max_pozos`
    de mayor EUR: son los que interesa mirar, y el ranking sigue siendo util.
    El dashboard de Streamlit si trabaja con el conjunto completo.
    """
    if not config.AJUSTES.exists():
        raise SystemExit(
            "No hay datos procesados.\n"
            "Corre primero:  python scripts/preparar_datos.py"
        )

    produccion = pd.read_parquet(config.PRODUCCION)
    ajustes = pd.read_parquet(config.AJUSTES)
    metadatos = json.loads(config.METADATOS.read_text())

    # Backtest: predicho vs real para los pozos que se pudieron validar.
    ruta_bt = config.DIR_PROCESADO / "backtest.parquet"
    backtest = pd.read_parquet(ruta_bt) if ruta_bt.exists() else pd.DataFrame()

    total = len(ajustes)

    # ---------------------------------------------------------------
    # FILTRO DE CALIDAD. Sin esto el ranking queda encabezado por los
    # ajustes que FALLARON, no por los mejores pozos.
    #
    # Por que: cuando la curva no ajusta, el optimizador clava b en su tope
    # y la integral del EUR se dispara. Un pozo con R2 = 0 y b = 2.00 puede
    # dar un EUR de 7 millones de barriles, diez veces lo que produce un
    # buen pozo real de Vaca Muerta. Ordenar por EUR sin filtrar pone
    # justamente esos arriba de todo.
    #
    # Con datos sinteticos esto no se veia porque todos los pozos ajustaban
    # bien. Aparecio recien con los datos oficiales.
    # ---------------------------------------------------------------
    antes = len(ajustes)
    confiables = seleccionar_confiables(ajustes)

    if len(confiables) < 20:
        # Si casi nada pasa el filtro, algo mas grande esta mal. Avisamos en
        # vez de mostrar un puñado de pozos como si fuera el panorama.
        print(f"   [!] solo {len(confiables)} de {antes} ajustes son confiables. "
              "Revisa los datos de entrada antes de creerle a este ranking.")
    else:
        descartados = antes - len(confiables)
        print(f"   descartados {descartados:,} de {antes:,} ajustes por baja "
              f"calidad ({descartados / antes:.0%}): R2 < "
              f"{config.R2_MINIMO_CONFIABLE}, sin converger, o b en el tope")
        ajustes = confiables

    # Poblacion para la economia: SIEMPRE los ajustes confiables, aunque sean
    # pocos, y nunca los que no pasaron el filtro.
    #
    # Ojo con la rama de arriba: cuando casi nada pasa el filtro dejamos
    # `ajustes` sin filtrar para que los graficos muestren algo, pero meter esos
    # ajustes rotos en la economia daria precios de equilibrio absurdamente
    # bajos (b en el tope -> volumen descontado enorme -> el pozo "cierra" a
    # cualquier precio). Preferimos una seccion vacia a un numero mentiroso.
    confiables_para_poblacion = confiables.copy()

    ajustes = ajustes.sort_values("eur", ascending=False).head(max_pozos)

    pozos, series = [], {}
    for f in ajustes.itertuples():
        serie = declinacion.preparar_serie(
            produccion[produccion["id_pozo"] == f.id_pozo],
            col_caudal="caudal_petroleo_m3d",
        )
        if len(serie) < meses_minimos:
            continue
        pozos.append({
            "id": str(f.id_pozo),
            "sigla": str(f.sigla) if pd.notna(f.sigla) else str(f.id_pozo),
            "op": str(f.empresa) if pd.notna(f.empresa) else "S/D",
            "area": str(f.area) if pd.notna(f.area) else "S/D",
            "qi": round(f.qi * BARRILES_POR_M3, 1),
            "di": round(f.di_mensual, 5),
            "b": round(f.b, 3),
            "r2": round(f.r2, 3),
            "eur": round(f.eur * BARRILES_POR_M3 / 1000, 1),
            "n": int(f.n_meses),
            "acum": round(f.acum_petroleo_bbl / 1000, 1),
            "inicio": pd.Timestamp(f.primer_mes).strftime("%Y-%m"),
            # Geometria del pozo. Puede no estar: no todos los pozos declaran
            # fractura, y sin estos datos la app oculta la seccion de
            # normalizacion en vez de mostrar graficos vacios.
            "rama": (round(float(f.rama_m)) if getattr(f, "rama_m", None) is not None
                     and pd.notna(getattr(f, "rama_m", None)) else None),
            "etapas": (int(f.etapas) if getattr(f, "etapas", None) is not None
                       and pd.notna(getattr(f, "etapas", None)) else None),
        })
        series[str(f.id_pozo)] = [
            round(v * BARRILES_POR_M3, 1) for v in serie["caudal_petroleo_m3d"]
        ]

    if not pozos:
        raise SystemExit("Ningun pozo quedo con historia suficiente para la app.")

    # --- backtest para el grafico de predicho vs real ---
    puntos_bt = []
    if not backtest.empty:
        siglas = dict(zip(ajustes["id_pozo"].astype(str), ajustes["sigla"].astype(str)))
        for f in backtest.itertuples():
            fila = {"id": str(f.id_pozo),
                    "sigla": siglas.get(str(f.id_pozo), str(f.id_pozo))}
            hay = False
            for h in (12, 24, 36):
                real = getattr(f, f"real_{h}", None)
                pred = getattr(f, f"pred_{h}", None)
                if real is not None and pd.notna(real) and pd.notna(pred):
                    # A miles de barriles, que es como se habla de estos volumenes.
                    fila[f"r{h}"] = round(float(real) * BARRILES_POR_M3 / 1000, 1)
                    fila[f"p{h}"] = round(float(pred) * BARRILES_POR_M3 / 1000, 1)
                    hay = True
            if hay:
                puntos_bt.append(fila)

    # --- poblacion completa para la economia ---
    #
    # La app incrusta solo los `max_pozos` de mayor EUR, y eso esta bien para los
    # graficos de curvas: son los que interesa mirar. Pero para la economia es un
    # SESGO grave: si solo mostras los mejores pozos, el 100% cierra a cualquier
    # precio razonable y el resultado miente sobre el conjunto.
    #
    # Por eso va aparte la poblacion completa de ajustes confiables, con lo
    # minimo para recalcular el precio de equilibrio: qi, Di, b y la operadora.
    # Son tres numeros por pozo, asi que entran miles sin engordar el archivo.
    poblacion = [
        {
            "qi": round(f.qi * BARRILES_POR_M3, 1),
            "di": round(f.di_mensual, 5),
            "b": round(f.b, 3),
            "op": str(f.empresa) if pd.notna(f.empresa) else "S/D",
        }
        for f in confiables_para_poblacion.itertuples()
    ]

    return {
        "wells": pozos,
        "series": series,
        "backtest": puntos_bt,
        "poblacion": poblacion,
        "meta": {
            "periodo": f"{metadatos['primer_mes']} a {metadatos['ultimo_mes']}",
            "es_demo": metadatos["es_demo"],
            "pozos_totales": total,
            "pozos_confiables": int(len(ajustes)),
            "d_term": metadatos["d_terminal_anual"],
            "horizonte": metadatos["horizonte_eur_meses"],
            # Diagnostico de cuanto de la diferencia de EUR explica la rama.
            "rama": metadatos.get("normalizacion_rama", {}),
            "backtest": metadatos.get("backtest", {}),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera la app web con los datos actuales.")
    parser.add_argument("--max-pozos", type=int, default=400,
                        help="cuantos pozos incrustar, los de mayor EUR (default: 400)")
    parser.add_argument("--meses-minimos", type=int, default=6,
                        help="meses minimos de historia para incluir un pozo")
    args = parser.parse_args()

    if not PLANTILLA.exists():
        raise SystemExit(f"Falta la plantilla: {PLANTILLA}")

    datos = armar_datos(args.max_pozos, args.meses_minimos)
    plantilla = PLANTILLA.read_text()

    if "__DATOS__" not in plantilla:
        raise SystemExit("La plantilla perdio el marcador __DATOS__.")

    cuerpo = plantilla.replace(
        "__DATOS__", json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    )

    # La version standalone necesita <head>: le pasamos el <title> y los <link>/<style>
    # que la plantilla trae arriba de todo, y dejamos el resto en el <body>.
    corte = cuerpo.index('<div class="wrap">')
    cabeza, resto = cuerpo[:corte], cuerpo[corte:]

    (RAIZ / "web" / "artifact.html").write_text(cuerpo)
    (RAIZ / "web" / "index.html").write_text(
        ENVOLTORIO.format(cabeza=cabeza, cuerpo=resto)
    )

    fuente = "DEMOSTRACION (sinteticos)" if datos["meta"]["es_demo"] else "OFICIALES"
    tam = (RAIZ / "web" / "index.html").stat().st_size / 1_000_000
    print(f"App generada con datos {fuente}")
    print(f"  {len(datos['wells']):,} pozos incrustados "
          f"(de {datos['meta']['pozos_totales']:,} ajustados)")
    print(f"  periodo: {datos['meta']['periodo']}")
    con_rama = sum(1 for w in datos["wells"] if w.get("rama"))
    print(f"  {con_rama:,} con longitud de rama declarada")
    print(f"  {len(datos['backtest']):,} pozos validados con backtest")
    print(f"  {len(datos['poblacion']):,} pozos en la población para economía")
    print(f"  web/index.html  ({tam:.1f} MB)  <- abrilo con doble clic")


if __name__ == "__main__":
    main()
