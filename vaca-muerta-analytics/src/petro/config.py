"""
Configuracion central: rutas y parametros por defecto.

Tener las rutas en un solo lugar evita el clasico problema de scripts que
funcionan solo si los corres parado en la carpeta correcta.
"""

from pathlib import Path

# RAIZ = la carpeta del proyecto (dos niveles arriba de este archivo).
RAIZ = Path(__file__).resolve().parents[2]

DIR_DATOS = RAIZ / "data"
DIR_CRUDO = DIR_DATOS / "crudo"
DIR_PROCESADO = DIR_DATOS / "procesado"

# Archivos que produce el pipeline y consume el dashboard.
PRODUCCION = DIR_PROCESADO / "produccion.parquet"
POZOS = DIR_PROCESADO / "pozos.parquet"
AJUSTES = DIR_PROCESADO / "ajustes_declinacion.parquet"
PRECIOS = DIR_PROCESADO / "precios_crudo.parquet"
METADATOS = DIR_PROCESADO / "metadatos.json"

# Parametros por defecto del analisis.
MESES_MINIMOS_AJUSTE = 9      # pozos con menos meses utiles no se ajustan
HORIZONTE_EUR_MESES = 360     # 30 años de vida util asumida
D_TERMINAL_ANUAL = 0.06       # declinacion terminal 6% anual
R2_MINIMO_CONFIABLE = 0.70    # abajo de esto el ajuste se marca como dudoso


def asegurar_carpetas() -> None:
    """Crea las carpetas de datos si no existen."""
    for carpeta in (DIR_CRUDO, DIR_PROCESADO):
        carpeta.mkdir(parents=True, exist_ok=True)
