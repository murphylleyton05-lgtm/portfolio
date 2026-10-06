"""
Genera los 4 iconos de los KPIs con un mismo estilo: trazo lineal, mismo
grosor y el color primario de la paleta. Se dibujan a 4x y se reducen para que
los bordes queden suaves.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
COLOR = (31, 78, 121, 255)  # #1F4E79, color primario del tablero
LADO, ESCALA = 96, 4
G = 7 * ESCALA  # grosor del trazo


def lienzo():
    img = Image.new("RGBA", (LADO * ESCALA, LADO * ESCALA), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def p(x, y):
    return (x * ESCALA, y * ESCALA)


def gota(d):
    # Gota de petroleo: punta arriba + circulo abajo.
    cx, cy, r = 48, 58, 24
    d.arc([p(cx - r, cy - r), p(cx + r, cy + r)], start=-35, end=215, fill=COLOR, width=G)
    a1, a2 = math.radians(-35), math.radians(215)
    d.line([p(cx + r * math.cos(a1), cy + r * math.sin(a1)), p(48, 10)], fill=COLOR, width=G)
    d.line([p(cx + r * math.cos(a2), cy + r * math.sin(a2)), p(48, 10)], fill=COLOR, width=G)
    d.arc([p(36, 50), p(56, 70)], start=110, end=180, fill=COLOR, width=G // 2)


def llama(d):
    pts = [(48, 8), (66, 34), (72, 56), (66, 76), (48, 88), (30, 76), (24, 56), (32, 38), (40, 50), (48, 8)]
    d.line([p(x, y) for x, y in pts], fill=COLOR, width=G, joint="curve")
    d.line([p(x, y) for x, y in [(48, 50), (58, 68), (48, 80), (38, 68), (48, 50)]], fill=COLOR, width=G // 2, joint="curve")


def pozo(d):
    # Torre de perforacion: triangulo con travesanos y base.
    d.line([p(30, 88), p(48, 10), p(66, 88)], fill=COLOR, width=G, joint="curve")
    d.line([p(39, 50), p(57, 50)], fill=COLOR, width=G)
    d.line([p(35, 68), p(61, 68)], fill=COLOR, width=G)
    d.line([p(16, 88), p(80, 88)], fill=COLOR, width=G)


def velocimetro(d):
    d.arc([p(10, 22), p(86, 98)], start=180, end=360, fill=COLOR, width=G)
    for ang in (200, 240, 300, 340):
        a = math.radians(ang)
        d.line([p(48 + 30 * math.cos(a), 60 + 30 * math.sin(a)), p(48 + 38 * math.cos(a), 60 + 38 * math.sin(a))], fill=COLOR, width=G // 2)
    a = math.radians(305)
    d.line([p(48, 60), p(48 + 28 * math.cos(a), 60 + 28 * math.sin(a))], fill=COLOR, width=G)
    d.ellipse([p(43, 55), p(53, 65)], fill=COLOR)


def main() -> None:
    for nombre, dibujo in [("petroleo", gota), ("gas", llama), ("pozos", pozo), ("productividad", velocimetro)]:
        img, d = lienzo()
        dibujo(d)
        img.resize((LADO, LADO), Image.LANCZOS).save(RAIZ / "img" / f"icono_{nombre}.png")
        print("img/icono_" + nombre + ".png")


if __name__ == "__main__":
    main()
