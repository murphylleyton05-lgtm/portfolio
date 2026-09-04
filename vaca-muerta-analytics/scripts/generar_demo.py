"""
Genera el dataset de demostracion (sintetico) en data/crudo/.

Uso:
    python scripts/generar_demo.py
    python scripts/generar_demo.py --pozos 300 --semilla 7

Correlo cuando no quieras (o no puedas) descargar los datos reales.
El archivo que produce tiene el mismo esquema que el CSV oficial, asi que el
resto del pipeline no se entera de la diferencia.
"""

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script desde cualquier carpeta sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config, demo_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos sinteticos de demo.")
    parser.add_argument("--pozos", type=int, default=150, help="cantidad de pozos")
    parser.add_argument("--semilla", type=int, default=42, help="semilla aleatoria")
    args = parser.parse_args()

    config.asegurar_carpetas()

    print(f"Generando {args.pozos} pozos sinteticos (semilla={args.semilla})...")
    df = demo_data.generar_pozos(n_pozos=args.pozos, semilla=args.semilla)

    salida = config.DIR_CRUDO / "DEMO__no_convencional.csv"
    df.to_csv(salida, index=False)
    print(f"  {len(df):,} filas pozo-mes -> {salida}")

    precios = demo_data.generar_precios(semilla=args.semilla)
    salida_precios = config.DIR_CRUDO / "DEMO__precios_crudo.csv"
    precios.to_csv(salida_precios, index=False)
    print(f"  {len(precios):,} meses de precio -> {salida_precios}")

    print("\nListo. Ahora corre:  python scripts/preparar_datos.py")


if __name__ == "__main__":
    main()
