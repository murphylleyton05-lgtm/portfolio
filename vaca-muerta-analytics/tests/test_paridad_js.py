"""
Paridad entre el Python y el JavaScript de la app.

POR QUE EXISTE ESTE TEST
------------------------
La app web calcula el precio de equilibrio en el navegador, en JavaScript, para
que mover un control recalcule al instante. Eso significa que la MISMA
matematica esta escrita dos veces: en `src/petro/economia.py` y adentro de
`web/plantilla.html`.

Dos implementaciones de la misma formula son una bomba de tiempo: se arregla un
signo en una y se olvida la otra, y a partir de ahi la app y el pipeline
reportan numeros distintos sin que nadie se entere. Es un bug silencioso, del
peor tipo.

Este test corre el JavaScript de verdad (con node), le pasa los mismos pozos
que al Python, y verifica que den lo mismo. Si alguien toca una de las dos
implementaciones y no la otra, el test falla.

Si node no esta disponible, el test se saltea en vez de fallar: no tiene sentido
romper la suite de alguien por no tener Node instalado.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from petro import economia  # noqa: E402

PLANTILLA = RAIZ / "web" / "plantilla.html"

# Pozos de prueba: uno bueno, uno mediano, uno flojo, y uno de declinacion lenta.
POZOS = [
    {"qi_bbld": 1200.0, "di": 0.18, "b": 1.4},
    {"qi_bbld": 700.0, "di": 0.14, "b": 1.1},
    {"qi_bbld": 250.0, "di": 0.09, "b": 0.7},
    {"qi_bbld": 400.0, "di": 0.05, "b": 1.8},
]

# Varios juegos de supuestos, para no validar solo el caso por defecto.
SUPUESTOS = [
    economia.Supuestos(),
    economia.Supuestos(costo_pozo_musd=18.0, opex_usd_bbl=8.0),
    economia.Supuestos(regalias_pct=25.0, descuento_anual_pct=15.0),
]


def _extraer(nombre: str, texto: str) -> str:
    """Saca una funcion JS completa de la plantilla, contando llaves."""
    inicio = texto.index(f"function {nombre}(")
    profundidad, i = 0, texto.index("{", inicio)
    for j in range(i, len(texto)):
        if texto[j] == "{":
            profundidad += 1
        elif texto[j] == "}":
            profundidad -= 1
            if profundidad == 0:
                return texto[inicio:j + 1]
    raise AssertionError(f"no pude extraer la función {nombre}")


@pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")
def test_los_percentiles_del_javascript_coinciden_con_pandas():
    """
    La paridad por pozo no alcanza: la app tambien AGREGA (mediana, P10, P90) y
    ahi puede divergir aunque cada pozo coincida.

    Paso de verdad: el JS tomaba `ordenado[floor(n*q)]` y pandas interpola
    linealmente, asi que el P90 daba 100.1 en la app y 98.9 en el README. Dos
    numeros distintos para lo mismo, en la misma pagina.
    """
    import numpy as np
    import pandas as pd

    texto = PLANTILLA.read_text()
    percentil_js = _extraer("percentil", texto)

    rng = np.random.default_rng(0)
    muestras = [
        sorted(rng.uniform(20, 200, n).round(4).tolist())
        for n in (11, 12, 50, 143, 1000)
    ]
    cuantiles = [0.10, 0.25, 0.5, 0.75, 0.90]

    guion = f"""
{percentil_js}
const muestras = {json.dumps(muestras)};
const qs = {json.dumps(cuantiles)};
console.log(JSON.stringify(muestras.map(m => qs.map(q => percentil(m, q)))));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(guion)
        ruta = f.name
    try:
        proc = subprocess.run(["node", ruta], capture_output=True, text=True, timeout=60)
    finally:
        Path(ruta).unlink(missing_ok=True)

    assert proc.returncode == 0, f"el JS falló:\n{proc.stderr}"
    js = json.loads(proc.stdout)

    for muestra, fila in zip(muestras, js):
        serie = pd.Series(muestra)
        for q, valor_js in zip(cuantiles, fila):
            assert valor_js == pytest.approx(float(serie.quantile(q)), rel=1e-9), (
                f"percentil {q} con n={len(muestra)}: JS {valor_js} vs pandas "
                f"{serie.quantile(q)}"
            )


@pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")
def test_el_javascript_de_la_app_da_lo_mismo_que_el_python():
    texto = PLANTILLA.read_text()

    # Las mismas funciones que usa la app, tal cual estan escritas ahi.
    funciones = "\n".join(
        _extraer(n, texto) for n in ("qArps", "mesDeCambio", "qModelo", "volumenDescontado")
    )
    constantes = (
        "const D_TERM = 0.06 / 12;\n"
        "const DIAS_MES = 30.4375;\n"
        "const HORIZONTE_ECO = 240;\n"
    )

    casos = [
        {"pozo": p, "sup": s.como_dict()}
        for p in POZOS for s in SUPUESTOS
    ]

    guion = f"""
{constantes}
{funciones}

const casos = {json.dumps(casos)};
const salida = casos.map(c => {{
  const vd = volumenDescontado(c.pozo.qi_bbld, c.pozo.di, c.pozo.b,
                               c.sup.descuento_anual_pct);
  const be = c.sup.costo_pozo_musd * 1e6 / ((1 - c.sup.regalias_pct / 100) * vd)
             + c.sup.opex_usd_bbl;
  return {{ vd, be }};
}});
console.log(JSON.stringify(salida));
"""

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(guion)
        ruta = f.name

    try:
        proc = subprocess.run(["node", ruta], capture_output=True, text=True, timeout=60)
    finally:
        Path(ruta).unlink(missing_ok=True)

    assert proc.returncode == 0, f"el JS falló:\n{proc.stderr}"
    resultados_js = json.loads(proc.stdout)

    for caso, js in zip(casos, resultados_js):
        pozo, sup = caso["pozo"], economia.Supuestos(**caso["sup"])

        # El Python trabaja en m3/d; la app, en bbl/d. La conversión es lineal,
        # así que el volumen descontado en barriles tiene que coincidir.
        from petro.limpieza import BARRILES_POR_M3
        qi_m3d = pozo["qi_bbld"] / BARRILES_POR_M3

        vd_py = economia.volumen_descontado_bbl(qi_m3d, pozo["di"], pozo["b"], sup)
        be_py = economia.precio_de_equilibrio(qi_m3d, pozo["di"], pozo["b"], sup)

        assert js["vd"] == pytest.approx(vd_py, rel=1e-6), (
            f"volumen descontado distinto para {pozo}: JS {js['vd']:.1f} vs Python {vd_py:.1f}"
        )
        assert js["be"] == pytest.approx(be_py, rel=1e-6), (
            f"precio de equilibrio distinto para {pozo}: "
            f"JS {js['be']:.2f} vs Python {be_py:.2f}"
        )
