"""
Inyecta los resultados de la ultima corrida en el README.

Un README con numeros escritos a mano queda viejo en la segunda corrida, y un
README con numeros viejos es peor que uno sin numeros: dice que el proyecto
esta abandonado. Este script reescribe un bloque delimitado del README con los
resultados actuales, y el workflow lo commitea junto con la app.

Los marcadores en el README son:
    <!-- RESULTADOS:INICIO -->  ... contenido generado ...  <!-- RESULTADOS:FIN -->

Uso:
    python scripts/actualizar_readme.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config, validacion  # noqa: E402

INICIO = "<!-- RESULTADOS:INICIO -->"
FIN = "<!-- RESULTADOS:FIN -->"


def bloque(meta: dict) -> str:
    """Arma el markdown que va entre los marcadores."""
    lineas: list[str] = []

    fuente = ("datos de demostración (sintéticos)" if meta.get("es_demo")
              else "datos oficiales de la Secretaría de Energía")
    lineas.append(
        f"> Última actualización: **{datetime.now(timezone.utc):%Y-%m-%d}** · "
        f"{fuente} · período **{meta['primer_mes']} a {meta['ultimo_mes']}** · "
        f"**{meta['pozos']:,} pozos**, {meta['pozos_ajustados']:,} con curva ajustada."
    )

    bt = meta.get("backtest", {})
    if bt.get("suficientes_datos"):
        lineas.append("")
        lineas.append("| Horizonte | Error en **un pozo** | Sesgo | Dentro de ±20% "
                      "| Error en el **total** | Pozos |")
        lineas.append("|---|---:|---:|---:|---:|---:|")
        for h in validacion.HORIZONTES:
            d = bt.get(f"h{h}")
            if not d:
                continue
            agregado = d.get("error_agregado")
            lineas.append(
                f"| {h} meses | {d['error_absoluto']:.1f}% | {d['error_mediano']:+.1f}% "
                f"| {d['dentro_20']:.0f}% "
                f"| {'—' if agregado is None else f'{agregado:+.1f}%'} "
                f"| {d['pozos']:,} |"
            )

        largo = bt.get(f"h{validacion.HORIZONTES[-1]}")
        if largo and largo.get("error_agregado") is not None:
            lineas.append("")
            lineas.append(
                f"**En una línea:** a {validacion.HORIZONTES[-1]} meses el modelo se "
                f"equivoca **{largo['error_absoluto']:.0f}% en un pozo individual** pero "
                f"solo **{abs(largo['error_agregado']):.0f}% en el total** de "
                f"{largo['pozos']:,} pozos — los errores se compensan. Y "
                f"{'sobreestima' if largo['error_mediano'] > 0 else 'subestima'} de forma "
                f"sistemática, lo que es corregible."
            )

    rama = meta.get("normalizacion_rama", {})
    if rama.get("suficientes_datos"):
        lineas.append("")
        lineas.append(
            f"**Normalización por rama lateral** ({rama['pozos']:,} pozos con longitud "
            f"declarada, mediana {rama['rama_mediana_m']:,} m): la longitud explica el "
            f"**{rama['varianza_explicada']:.0%}** de la diferencia de EUR entre pozos, "
            f"pero al normalizar el ranking se mueve **{rama['cambio_de_puesto_mediano']} "
            f"puestos** en la mediana y del top 10 por EUR crudo sobreviven solo "
            f"**{rama['top10_que_sobrevive']}**."
        )

    return "\n".join(lineas)


def main() -> None:
    if not config.METADATOS.exists():
        raise SystemExit("No hay metadatos. Corre antes: python scripts/preparar_datos.py")

    readme = config.RAIZ / "README.md"
    texto = readme.read_text()

    if INICIO not in texto or FIN not in texto:
        raise SystemExit(
            f"El README no tiene los marcadores {INICIO} / {FIN}. "
            "Sin ellos no sé dónde escribir."
        )

    meta = json.loads(config.METADATOS.read_text())
    antes = texto[: texto.index(INICIO) + len(INICIO)]
    despues = texto[texto.index(FIN):]

    readme.write_text(f"{antes}\n{bloque(meta)}\n{despues}")
    print(f"README actualizado con los resultados de {meta['primer_mes']} "
          f"a {meta['ultimo_mes']}")


if __name__ == "__main__":
    main()
