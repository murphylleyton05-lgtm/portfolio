"""
petro - libreria de analisis de datos de hidrocarburos (Argentina).

Modulos:
    config       rutas y parametros del proyecto
    ingesta      descarga desde datos.energia.gob.ar y EIA
    limpieza     normalizacion del esquema oficial
    declinacion  curvas de declinacion de Arps, EUR y curvas tipo
    demo_data    generador de datos sinteticos para correr sin descargar
"""

from . import config, declinacion, demo_data, ingesta, limpieza  # noqa: F401

__version__ = "0.1.0"
__all__ = ["config", "ingesta", "limpieza", "declinacion", "demo_data"]
