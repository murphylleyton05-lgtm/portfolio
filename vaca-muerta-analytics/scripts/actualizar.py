"""
Un solo comando: descarga los datos oficiales, los procesa y regenera la app.

    python scripts/actualizar.py            <- datos REALES de la Secretaria
    python scripts/actualizar.py --demo     <- datos sinteticos (para probar)

Es el atajo de todo el pipeline. Equivale a correr, en orden:

    python scripts/descargar_datos.py --dataset no_convencional --forzar
    python scripts/preparar_datos.py
    python scripts/generar_web.py

Cuando termina, `web/index.html` queda actualizado: abrilo con doble clic.

Si algo falla, el script te dice en que paso fue y que comando correr para
mirarlo de cerca. Los errores mas comunes con datos reales son dos:

  - El dataset cambio de nombre en el portal.
        python scripts/descargar_datos.py --buscar "no convencional"
  - El CSV trae una columna con otro nombre.
        Se corrige en COLUMNAS_OFICIALES, en src/petro/limpieza.py
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PY = sys.executable


def paso(numero: int, total: int, titulo: str, comando: list[str],
         opcional: bool = False) -> None:
    """
    Corre un script del pipeline mostrando en que paso vamos.

    Un paso `opcional` que falla avisa pero no corta: sirve para datos que
    mejoran el analisis pero no son imprescindibles.
    """
    print(f"\n{'─' * 62}")
    print(f"PASO {numero}/{total} · {titulo}")
    print("─" * 62, flush=True)

    t0 = time.time()
    resultado = subprocess.run([PY, *comando], cwd=RAIZ)

    if resultado.returncode != 0 and opcional:
        print(f"\n  ! El paso {numero} ({titulo}) fallo, pero es opcional: sigo.")
        return

    if resultado.returncode != 0:
        print(f"\n✗ Fallo el paso {numero} ({titulo}).")
        print(f"  Para verlo en detalle:  python {' '.join(comando)}")
        if "descargar" in comando[0]:
            print("  Si el dataset cambio de nombre en el portal, buscalo con:")
            print('      python scripts/descargar_datos.py --buscar "no convencional"')
        if "preparar" in comando[0]:
            print("  Si se queja de columnas, revisa COLUMNAS_OFICIALES en")
            print("      src/petro/limpieza.py")
        raise SystemExit(resultado.returncode)

    print(f"  ✓ listo en {time.time() - t0:.0f} s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Descarga, procesa y regenera la app en un solo comando."
    )
    parser.add_argument("--demo", action="store_true",
                        help="usar datos sinteticos en vez de descargar los reales")
    parser.add_argument("--max-pozos", type=int, default=400,
                        help="cuantos pozos incrustar en la app web (default: 400)")
    parser.add_argument("--sin-descargar", action="store_true",
                        help="saltear la descarga y usar los CSV que ya tenes en data/crudo/")
    parser.add_argument("--max-mb", type=float, default=None,
                        help="tope de descarga en MB (util en un servidor de CI)")
    args = parser.parse_args()

    pasos = []
    if args.demo:
        pasos.append(("Generando pozos sinteticos", ["scripts/generar_demo.py"]))
    elif not args.sin_descargar:
        tope = ["--max-mb", str(args.max_mb)] if args.max_mb else []
        pasos.append((
            "Descargando produccion de la Secretaria de Energia",
            ["scripts/descargar_datos.py", "--dataset", "no_convencional", "--forzar"] + tope,
        ))
        # La fractura es opcional: sin ella el proyecto anda, solo que los
        # rankings quedan sin normalizar por longitud de rama. Por eso este
        # paso no corta el pipeline si falla.
        pasos.append((
            "Descargando datos de fractura (rama lateral y etapas)",
            ["scripts/descargar_datos.py", "--dataset", "fractura", "--forzar"] + tope,
            True,
        ))

    pasos.append(("Procesando y ajustando curvas de declinacion", ["scripts/preparar_datos.py"]))
    pasos.append(("Generando la app web", ["scripts/generar_web.py",
                                           "--max-pozos", str(args.max_pozos)]))
    pasos.append(("Escribiendo los resultados en el README",
                  ["scripts/actualizar_readme.py"], True))

    print("Actualizando Vaca Muerta Analytics")
    if not args.demo and not args.sin_descargar:
        print("La descarga son cientos de MB y el ajuste de miles de pozos")
        print("puede tardar varios minutos. Se puede cortar con Ctrl+C.")

    for i, entrada in enumerate(pasos, start=1):
        titulo, comando = entrada[0], entrada[1]
        opcional = entrada[2] if len(entrada) > 2 else False
        paso(i, len(pasos), titulo, comando, opcional=opcional)

    print(f"\n{'─' * 62}")
    print("LISTO")
    print("─" * 62)
    print(f"  App:        {RAIZ / 'web' / 'index.html'}   <- abrila con doble clic")
    print("  Dashboard:  streamlit run app/dashboard.py")


if __name__ == "__main__":
    main()
