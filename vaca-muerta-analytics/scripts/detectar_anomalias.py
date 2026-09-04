"""
Detecta pozos que se desviaron de su curva de declinacion esperada.

Esta es la pieza que convierte el proyecto de "un dashboard" en "un sistema que
corre solo". La idea es simple y es la misma que usa cualquier monitoreo:

    1. Cada pozo tiene una curva ajustada -> el modelo sabe cuanto DEBERIA
       producir cada mes.
    2. Se compara la produccion real del ultimo mes contra esa prediccion.
    3. Los pozos que se desvian mas que un umbral se reportan.

Un desvio NEGATIVO grande sugiere un problema: falla de equipo, restriccion de
evacuacion, pozo intervenido, o un dato mal declarado.
Un desvio POSITIVO grande sugiere una intervencion exitosa (o tambien un dato
mal cargado, que en la practica es igual de comun).

IMPORTANTE - lo que esto NO es: no es un diagnostico. Es un DETECTOR. Dice
"mira este pozo", no "este pozo tiene tal problema". Vender lo segundo cuando
solo tenes lo primero es la forma mas rapida de perder credibilidad.

Uso:
    python scripts/detectar_anomalias.py
    python scripts/detectar_anomalias.py --umbral 30 --json
    python scripts/detectar_anomalias.py --meses 3 --salida reporte.json

La opcion --json imprime SOLO json por stdout, para que n8n (o cualquier
orquestador) lo pueda parsear directamente. Ver docs/05-automatizacion-n8n.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config, declinacion  # noqa: E402
from petro.limpieza import BARRILES_POR_M3  # noqa: E402


def detectar(
    produccion: pd.DataFrame,
    ajustes: pd.DataFrame,
    umbral_pct: float = 25.0,
    meses_a_revisar: int = 1,
    r2_minimo: float = 0.7,
) -> pd.DataFrame:
    """
    Compara produccion real contra la curva ajustada de cada pozo.

    Parametros
    ----------
    umbral_pct       : desvio minimo (en %) para reportar un pozo.
    meses_a_revisar  : cuantos meses finales de cada pozo mirar.
    r2_minimo        : solo se revisan pozos cuyo ajuste es confiable. Si el
                       modelo no describe bien al pozo, un "desvio" contra ese
                       modelo no significa nada.

    Devuelve un DataFrame con un renglon por pozo-mes anomalo.
    """
    confiables = ajustes[ajustes["r2"] >= r2_minimo]
    hallazgos = []

    for fila in confiables.itertuples():
        serie_pozo = produccion[produccion["id_pozo"] == fila.id_pozo]
        serie = declinacion.preparar_serie(serie_pozo, col_caudal="caudal_petroleo_m3d")

        if len(serie) <= meses_a_revisar:
            continue

        ultimos = serie.tail(meses_a_revisar)

        for punto in ultimos.itertuples():
            esperado = float(declinacion.caudal_hiperbolica_modificada(
                punto.t_meses, fila.qi, fila.di_mensual, fila.b,
                d_terminal_anual=config.D_TERMINAL_ANUAL,
            )[0])

            if esperado <= 0.01:
                continue

            real = float(punto.caudal_petroleo_m3d)
            desvio_pct = (real - esperado) / esperado * 100.0

            if abs(desvio_pct) >= umbral_pct:
                hallazgos.append({
                    "id_pozo": fila.id_pozo,
                    "sigla": getattr(fila, "sigla", ""),
                    "empresa": getattr(fila, "empresa", ""),
                    "area": getattr(fila, "area", ""),
                    "mes": punto.fecha.strftime("%Y-%m"),
                    "mes_de_vida": int(round(punto.t_meses)),
                    "caudal_real_bbld": round(real * BARRILES_POR_M3, 1),
                    "caudal_esperado_bbld": round(esperado * BARRILES_POR_M3, 1),
                    "desvio_pct": round(desvio_pct, 1),
                    "tipo": "bajo_rendimiento" if desvio_pct < 0 else "sobre_rendimiento",
                    "r2_del_ajuste": round(float(fila.r2), 3),
                })

    if not hallazgos:
        return pd.DataFrame(columns=[
            "id_pozo", "sigla", "empresa", "area", "mes", "mes_de_vida",
            "caudal_real_bbld", "caudal_esperado_bbld", "desvio_pct", "tipo",
            "r2_del_ajuste",
        ])

    df = pd.DataFrame(hallazgos)
    # Ordenamos por magnitud del desvio: lo mas raro primero.
    return df.reindex(df["desvio_pct"].abs().sort_values(ascending=False).index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detecta pozos fuera de su curva esperada.")
    parser.add_argument("--umbral", type=float, default=25.0,
                        help="desvio minimo en %% para reportar (default: 25)")
    parser.add_argument("--meses", type=int, default=1,
                        help="cuantos meses finales revisar (default: 1)")
    parser.add_argument("--r2-minimo", type=float, default=config.R2_MINIMO_CONFIABLE,
                        help="solo revisar pozos con ajuste confiable")
    parser.add_argument("--json", action="store_true",
                        help="imprimir solo JSON (para n8n u otro orquestador)")
    parser.add_argument("--salida", type=Path, help="ademas, guardar el JSON en un archivo")
    args = parser.parse_args()

    if not config.AJUSTES.exists():
        print("No hay datos procesados. Corre primero: python scripts/preparar_datos.py",
              file=sys.stderr)
        raise SystemExit(1)

    produccion = pd.read_parquet(config.PRODUCCION)
    ajustes = pd.read_parquet(config.AJUSTES)

    anomalias = detectar(
        produccion, ajustes,
        umbral_pct=args.umbral,
        meses_a_revisar=args.meses,
        r2_minimo=args.r2_minimo,
    )

    reporte = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "umbral_pct": args.umbral,
        "meses_revisados": args.meses,
        "pozos_evaluados": int((ajustes["r2"] >= args.r2_minimo).sum()),
        "anomalias_encontradas": int(len(anomalias)),
        "bajo_rendimiento": int((anomalias["tipo"] == "bajo_rendimiento").sum()),
        "sobre_rendimiento": int((anomalias["tipo"] == "sobre_rendimiento").sum()),
        "detalle": anomalias.to_dict(orient="records"),
    }

    if args.salida:
        args.salida.write_text(json.dumps(reporte, indent=2, ensure_ascii=False))

    if args.json:
        # Solo JSON por stdout: n8n lo parsea directo.
        print(json.dumps(reporte, ensure_ascii=False))
        return

    # Salida legible para una persona.
    print(f"Pozos evaluados (R2 >= {args.r2_minimo}): {reporte['pozos_evaluados']:,}")
    print(f"Umbral de desvio: +/- {args.umbral}%")
    print(f"Anomalias: {reporte['anomalias_encontradas']:,} "
          f"({reporte['bajo_rendimiento']} por debajo, "
          f"{reporte['sobre_rendimiento']} por encima)\n")

    if anomalias.empty:
        print("Ningun pozo se desvio mas alla del umbral.")
        return

    print(anomalias.head(20).to_string(index=False))
    if len(anomalias) > 20:
        print(f"\n... y {len(anomalias) - 20} mas.")


if __name__ == "__main__":
    main()
