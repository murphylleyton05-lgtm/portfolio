"""
Escribe un resumen en Markdown de la ultima corrida del pipeline.

Se usa en GitHub Actions para que el resultado se lea en la pantalla del
workflow, sin tener que abrir los logs. Fuera de CI imprime lo mismo por
pantalla, asi que sirve igual para revisar a mano como quedaron los datos.

Uso:
    python scripts/resumen_ci.py
    python scripts/resumen_ci.py >> $GITHUB_STEP_SUMMARY
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config  # noqa: E402
from petro.limpieza import BARRILES_POR_M3  # noqa: E402


def main() -> None:
    if not config.AJUSTES.exists():
        print("No hay datos procesados.")
        raise SystemExit(1)

    aj = pd.read_parquet(config.AJUSTES)
    meta = json.loads(config.METADATOS.read_text())
    aj["eur_mbbl"] = aj["eur"] * BARRILES_POR_M3 / 1000.0

    fuente = "⚠️ Datos de DEMOSTRACIÓN (sintéticos)" if meta["es_demo"] else "✅ Datos OFICIALES"

    print(f"## {fuente}\n")
    print("| | |")
    print("|---|---|")
    print(f"| Período | {meta['primer_mes']} a {meta['ultimo_mes']} |")
    print(f"| Pozos analizados | {meta['pozos']:,} |")
    print(f"| Curvas ajustadas | {meta['pozos_ajustados']:,} |")
    print(f"| Ajustes confiables (R² ≥ {config.R2_MINIMO_CONFIABLE}) | "
          f"{meta['pozos_ajuste_confiable']:,} "
          f"({meta['pozos_ajuste_confiable'] / max(meta['pozos_ajustados'], 1):.0%}) |")
    print(f"| R² mediano | {aj['r2'].median():.3f} |")
    print(f"| b mediano | {aj['b'].median():.2f} |")
    print(f"| EUR mediano | {aj['eur_mbbl'].median():,.0f} Mbbl |")

    # Cuantos pozos quedaron pegados al tope de b: ahi el EUR queda inflado.
    en_tope = int((aj["b"] >= 1.98).sum())
    if en_tope:
        print(f"| Pozos con b en el tope del modelo | {en_tope:,} "
              f"({en_tope / len(aj):.0%}) — su EUR está sobreestimado |")

    # --- validacion: lo que hace creible al EUR ---
    bt = meta.get("backtest", {})
    if bt.get("suficientes_datos"):
        print("\n### Validación del modelo (backtest)\n")
        print("Ajustado con los primeros 24 meses de cada pozo, prediciendo el resto. "
              "El pozo ya produjo ese período; el modelo no lo vio.\n")
        print("| Horizonte | Error típico | Sesgo | Dentro de ±20% | Pozos |")
        print("|---|---:|---:|---:|---:|")
        for h in (12, 24, 36):
            d = bt.get(f"h{h}")
            if d:
                print(f"| {h} meses | {d['error_absoluto']:.1f}% | "
                      f"{d['error_mediano']:+.1f}% | {d['dentro_20']:.0f}% | "
                      f"{d['pozos']:,} |")

    # --- normalizacion por rama lateral ---
    rama = meta.get("normalizacion_rama", {})
    if rama.get("suficientes_datos"):
        print("\n### Normalización por longitud de rama lateral\n")
        print(f"- La rama explica el **{rama['varianza_explicada']:.0%}** de la "
              f"diferencia de EUR entre pozos ({rama['pozos']:,} con dato declarado)")
        print(f"- Rama mediana: **{rama['rama_mediana_m']:,} m**")
        print(f"- Al normalizar, el ranking se mueve **{rama['cambio_de_puesto_mediano']} "
              f"puestos** (mediana), hasta {rama['cambio_de_puesto_maximo']:,}")
        print(f"- Del top 10 por EUR crudo sobreviven **{rama['top10_que_sobrevive']} "
              "pozos** al pasar a EUR por metro")

    if "empresa" in aj.columns and aj["empresa"].notna().any():
        print("\n### Operadoras con más pozos analizados\n")
        print("| Operadora | Pozos | EUR mediano (Mbbl) |")
        print("|---|---:|---:|")
        top = (aj.groupby("empresa")
                 .agg(pozos=("id_pozo", "count"), eur=("eur_mbbl", "median"))
                 .sort_values("pozos", ascending=False).head(10))
        for empresa, fila in top.iterrows():
            print(f"| {empresa} | {int(fila['pozos']):,} | {fila['eur']:,.0f} |")

    print(f"\n_Metodología: Arps hiperbólica modificada · horizonte "
          f"{meta['horizonte_eur_meses']} meses · declinación terminal "
          f"{meta['d_terminal_anual'] * 100:.0f}% anual._")


if __name__ == "__main__":
    main()
