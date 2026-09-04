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

    total = len(ajustes)
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

    return {
        "wells": pozos,
        "series": series,
        "meta": {
            "periodo": f"{metadatos['primer_mes']} a {metadatos['ultimo_mes']}",
            "es_demo": metadatos["es_demo"],
            "pozos_totales": total,
            "d_term": metadatos["d_terminal_anual"],
            "horizonte": metadatos["horizonte_eur_meses"],
            # Diagnostico de cuanto de la diferencia de EUR explica la rama.
            "rama": metadatos.get("normalizacion_rama", {}),
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
    print(f"  web/index.html  ({tam:.1f} MB)  <- abrilo con doble clic")


if __name__ == "__main__":
    main()
