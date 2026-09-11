#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arma el dashboard: toma web/plantilla.html, le inyecta web/datos.json en el
lugar del marcador /*__DATOS__*/{} y escribe web/index.html (envuelto en su
<!doctype html>) y web/artifact.html (el mismo cuerpo sin <html>/<head>, para
publicar como Artifact).
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"

plantilla = (WEB / "plantilla.html").read_text(encoding="utf-8")
datos = (WEB / "datos.json").read_text(encoding="utf-8")

marcador = "/*__DATOS__*/{}"
if marcador not in plantilla:
    raise SystemExit("No encontre el marcador /*__DATOS__*/{} en la plantilla")
cuerpo = plantilla.replace(marcador, "/*__DATOS__*/" + datos)

# Separar <head> (title/meta/link/style) del resto del cuerpo.
BASE = "https://murphylleyton05-lgtm.github.io/portfolio/logistica/"
OG = (
    '<meta property="og:title" content="Frac Sand & Fuel Logistics — Vaca Muerta">\n'
    '<meta property="og:description" content="Dashboard de cadena de suministro de arena de fractura y gasoil: '
    'OTIF, lead time, stock, quiebres y costo logístico. Consumo real (Secretaría de Energía) + logística modelada.">\n'
    '<meta property="og:type" content="website">\n'
    f'<meta property="og:url" content="{BASE}">\n'
    '<meta name="twitter:card" content="summary_large_image">\n'
)

envoltorio = (
    "<!doctype html>\n<html lang=\"es\" data-theme=\"dark\">\n<head>\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    + OG + "{cabeza}\n</head>\n<body>\n{resto}\n</body>\n</html>\n"
)

# La plantilla arranca con <title>...</title> y termina con </script>. La cabeza
# es todo hasta el cierre de </style>; el resto es el markup + script.
corte = cuerpo.index("</style>") + len("</style>")
cabeza = cuerpo[:corte]
resto = cuerpo[corte:]

(WEB / "index.html").write_text(envoltorio.format(cabeza=cabeza, resto=resto), encoding="utf-8")
(WEB / "artifact.html").write_text(resto, encoding="utf-8")

print("OK web")
print(f"  index.html    {(WEB/'index.html').stat().st_size/1024:.0f} KB")
print(f"  artifact.html {(WEB/'artifact.html').stat().st_size/1024:.0f} KB")
