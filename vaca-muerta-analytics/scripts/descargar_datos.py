"""
Descarga los datos REALES desde datos.energia.gob.ar.

Uso:
    python scripts/descargar_datos.py                  # descarga no convencional
    python scripts/descargar_datos.py --listar         # solo lista que hay, no baja
    python scripts/descargar_datos.py --dataset perforacion
    python scripts/descargar_datos.py --forzar         # ignora el cache

Los CSV son grandes (cientos de MB). Se guardan en data/crudo/, que esta en
.gitignore: los datos NO se commitean, se regeneran corriendo este script.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config, ingesta  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga datos de la Secretaria de Energia.")
    parser.add_argument(
        "--dataset", default="no_convencional",
        choices=list(ingesta.DATASETS),
        help="que dataset bajar",
    )
    parser.add_argument("--listar", action="store_true", help="listar recursos sin descargar")
    parser.add_argument("--forzar", action="store_true", help="volver a descargar aunque exista")
    parser.add_argument("--buscar", help="buscar datasets por texto en el portal")
    args = parser.parse_args()

    config.asegurar_carpetas()

    if args.buscar:
        print(ingesta.buscar_datasets(args.buscar).to_string(index=False))
        return

    slug = ingesta.DATASETS[args.dataset]
    print(f"Dataset: {args.dataset}  ({slug})\n")

    recursos = ingesta.listar_recursos(slug)
    print(recursos[["nombre", "formato", "bytes", "modificado"]].to_string(index=False))

    if args.listar:
        print("\n(--listar activo: no se descargo nada)")
        return

    print()
    archivos = ingesta.descargar_dataset(
        args.dataset, config.DIR_CRUDO, forzar=args.forzar
    )
    print(f"\n{len(archivos)} archivo(s) en {config.DIR_CRUDO}")
    print("Ahora corre:  python scripts/preparar_datos.py")


if __name__ == "__main__":
    main()
