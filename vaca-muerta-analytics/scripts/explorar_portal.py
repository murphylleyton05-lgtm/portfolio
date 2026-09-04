"""
Explora el portal de datos abiertos y reporta lo que realmente hay.

Existe porque adivinar nombres de datasets y de columnas es la forma mas rapida
de escribir codigo que no funciona. Este script no asume nada: pregunta.

Imprime, para los temas que nos interesan:
  1. Que datasets existen (slug real, titulo, cuando se actualizo)
  2. Que archivos tiene cada uno (nombre, formato, tamaño, fecha)
  3. Las COLUMNAS REALES del CSV mas reciente, bajando solo los primeros KB

El punto 3 es el importante: con eso se completa el mapeo de columnas en
limpieza.py sin adivinar.

Uso:
    python scripts/explorar_portal.py
    python scripts/explorar_portal.py --buscar "fractura" "no convencional"
"""

import argparse
import io
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import ingesta  # noqa: E402

TERMINOS = [
    "produccion de petroleo y gas por pozo",
    "fractura",
    "no convencional",
    "perforacion de pozos",
]


def columnas_reales(url: str, kb: int = 400) -> tuple[list[str], pd.DataFrame] | None:
    """
    Baja solo los primeros KB de un CSV y devuelve sus columnas y 2 filas.

    Los CSV del portal pesan cientos de MB. Para saber como se llaman las
    columnas no hace falta bajar el archivo entero: alcanza con el encabezado.
    Leemos en streaming y cortamos apenas tenemos suficiente.
    """
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            crudo = b""
            for pedazo in r.iter_content(chunk_size=32 * 1024):
                crudo += pedazo
                if len(crudo) > kb * 1024:
                    break
    except Exception as e:
        print(f"    (no pude leer el archivo: {e})")
        return None

    # La ultima linea casi seguro quedo cortada por la mitad: la descartamos.
    texto = crudo.decode("utf-8", errors="replace")
    texto = texto[: texto.rfind("\n")]

    try:
        df = pd.read_csv(io.StringIO(texto), nrows=3, low_memory=False)
    except Exception as e:
        print(f"    (no pude parsear el CSV: {e})")
        return None

    return list(df.columns), df


def main() -> None:
    parser = argparse.ArgumentParser(description="Reporta que hay realmente en el portal.")
    parser.add_argument("--buscar", nargs="*", default=TERMINOS)
    parser.add_argument("--sin-columnas", action="store_true",
                        help="no bajar encabezados, solo listar datasets")
    args = parser.parse_args()

    vistos: set[str] = set()

    for termino in args.buscar:
        print(f"\n{'=' * 78}")
        print(f"BUSQUEDA: {termino!r}")
        print("=" * 78)

        try:
            encontrados = ingesta.buscar_datasets(termino, filas=8)
        except Exception as e:
            print(f"  fallo la busqueda: {e}")
            continue

        if encontrados.empty:
            print("  (sin resultados)")
            continue
        print(encontrados.to_string(index=False))

        for slug in encontrados["slug"]:
            if slug in vistos:
                continue
            vistos.add(slug)

            print(f"\n  {'-' * 74}")
            print(f"  DATASET: {slug}")
            print(f"  {'-' * 74}")
            try:
                recursos = ingesta.listar_recursos(slug)
            except Exception as e:
                print(f"    no pude listar recursos: {e}")
                continue

            csvs = recursos[recursos["formato"] == "CSV"].copy()
            print(f"    {len(recursos)} recursos ({len(csvs)} CSV)")

            if csvs.empty:
                continue

            csvs = csvs.sort_values("modificado", ascending=False, na_position="last")
            print("\n    Los 5 CSV mas recientes:")
            print(csvs[["nombre", "bytes", "modificado"]].head(5).to_string(index=False))

            if args.sin_columnas:
                continue

            print("\n    COLUMNAS REALES del CSV mas reciente:")
            resultado = columnas_reales(csvs.iloc[0]["url"])
            if resultado:
                cols, muestra = resultado
                for i, c in enumerate(cols):
                    print(f"      {i:2d}. {c}")
                print("\n    Primeras filas:")
                print(muestra.head(2).to_string(max_colwidth=22))


if __name__ == "__main__":
    main()
