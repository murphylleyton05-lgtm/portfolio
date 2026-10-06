"""Imagen de referencia: como tiene que quedar el dashboard (con los datos reales)."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.image import imread  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
AZUL, NARANJA, GRIS, TEXTO, FONDO = "#1f4e79", "#e8833a", "#a6b1bb", "#333f48", "#f4f6f8"
TINTES = {"YPF": NARANJA, "Vista": "#1f4e79", "Pluspetrol": "#3d6a94", "Shell": "#5b86ae",
          "PAE": "#7fa3c4", "Resto": GRIS}


def caja(fig, rect):
    ax = fig.add_axes(rect)
    ax.set_facecolor("white")
    for s in ax.spines.values():
        s.set_color("#d9dee3")
    return ax


def main() -> None:
    d = pd.read_excel(RAIZ / "data" / "VacaMuerta_Tableau.xlsx")
    u = d[d.Ultimo_mes == "Si"]
    oil, ant = u.Petroleo_bbl_d.sum(), u.Petroleo_anio_anterior_bbl_d.sum()

    fig = plt.figure(figsize=(12, 8.2), dpi=110, facecolor=FONDO)
    fig.text(0.02, 0.955, "El petróleo de Vaca Muerta creció 32% en un año y YPF aporta más de la mitad",
             fontsize=17, weight="bold", color=AZUL)
    fig.text(0.02, 0.925, "Producción no convencional, dic-2025: 602 mil bbl/d vs 456 mil en dic-2024. "
             "YPF explica 56% del total; Chevron y Pampa son los más productivos por pozo.",
             fontsize=9.5, color=TEXTO)

    kpis = [("icono_petroleo", "PETRÓLEO · DIC-2025", f"{oil/1000:.0f} mil bbl/d",
             f"▲ +{(oil/ant-1)*100:.1f}% vs dic-2024"),
            ("icono_gas", "GAS · DIC-2025", f"{u.Gas_Mm3_d.sum()/1000:.1f} MMm³/d", ""),
            ("icono_pozos", "POZOS EN PRODUCCIÓN", f"{u.Pozos_activos.sum():,} pozos".replace(",", "."), ""),
            ("icono_productividad", "PETRÓLEO POR POZO", f"{oil/u.Pozos_activos.sum():.0f} bbl/d", "")]
    for i, (ico, et, val, sub) in enumerate(kpis):
        x = 0.02 + i * 0.2425
        ax = caja(fig, [x, 0.78, 0.23, 0.12])
        ax.set_xticks([]); ax.set_yticks([])
        ia = fig.add_axes([x + 0.008, 0.795, 0.05, 0.09]); ia.axis("off")
        ia.imshow(imread(RAIZ / "img" / f"{ico}.png"))
        fig.text(x + 0.068, 0.868, et, fontsize=7.5, weight="bold", color="#6b7680")
        fig.text(x + 0.068, 0.83, val, fontsize=15, weight="bold", color=AZUL)
        if sub:
            fig.text(x + 0.068, 0.8, sub, fontsize=8.5, weight="bold", color=NARANJA)

    # Eje doble
    e = d[d.Petroleo_anio_anterior_bbl_d.notna()].groupby("Mes")[
        ["Petroleo_bbl_d", "Petroleo_anio_anterior_bbl_d"]].sum()
    ax = caja(fig, [0.06, 0.37, 0.53, 0.33])
    ax.bar(e.index, e.Petroleo_bbl_d, width=20, color=AZUL, label="Mes actual")
    ax.plot(e.index, e.Petroleo_anio_anterior_bbl_d, color=GRIS, lw=2.5, marker="o", ms=3,
            label="Mismo mes año anterior")
    ax.set_ylim(0, 650000)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f} mil")
    ax.tick_params(labelsize=7.5)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    fig.text(0.02, 0.72, "¿Cuánto creció el petróleo frente al mismo mes del año anterior?",
             fontsize=10, weight="bold", color=TEXTO)
    fig.text(0.02, 0.705, "EJE DOBLE · barras = mes · línea = año anterior · ejes sincronizados",
             fontsize=7.5, color="#6b7680")

    # Dona
    g = u.groupby("Grupo_Dona").Petroleo_bbl_d.sum().reindex(list(TINTES))
    ax = caja(fig, [0.62, 0.37, 0.36, 0.33]); ax.axis("off")
    ax.pie(g, colors=[TINTES[k] for k in g.index], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.38, edgecolor="white"),
           labels=[f"{k}\n{v/oil*100:.0f}%" for k, v in g.items()], textprops=dict(fontsize=8))
    ax.text(0, 0.05, f"{oil/1000:.0f} mil", ha="center", fontsize=14, weight="bold", color=AZUL)
    ax.text(0, -0.17, "bbl/d · dic-2025", ha="center", fontsize=7.5, color="#6b7680")
    fig.text(0.62, 0.72, "¿Quién produce el petróleo? (dic-2025)", fontsize=10, weight="bold", color=TEXTO)
    fig.text(0.62, 0.705, "DONA · 6 segmentos · total en el centro", fontsize=7.5, color="#6b7680")

    # Treemap (rebanado simple en filas, alcanza como referencia)
    t = u.assign(p=u.Petroleo_bbl_d / u.Pozos_activos).sort_values("Petroleo_bbl_d", ascending=False)
    ax = caja(fig, [0.02, 0.05, 0.96, 0.24]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("c", [GRIS, AZUL])
    norm = matplotlib.colors.Normalize(t.p.min(), t.p.max())
    tot, x = t.Petroleo_bbl_d.sum(), 0
    for _, r in t.iterrows():
        w = r.Petroleo_bbl_d / tot
        ax.add_patch(plt.Rectangle((x, 0), w, 1, color=cmap(norm(r.p)), ec="white", lw=2))
        if w > 0.06:
            ax.text(x + 0.006, 0.9, f"{r.Operador.title()}\n{r.Petroleo_bbl_d:,.0f} bbl/d\n{r.p:.0f} por pozo"
                    .replace(",", "."), va="top", fontsize=7.5 if w > 0.08 else 6, color="white", weight="bold")
        x += w
    fig.text(0.02, 0.31, "¿Cómo se distribuye la producción entre operadores? (dic-2025)",
             fontsize=10, weight="bold", color=TEXTO)
    fig.text(0.02, 0.295, "TREEMAP · tamaño = petróleo · color = bbl/d por pozo · "
             "clic en un operador = filtra KPIs y eje doble; clic de nuevo = vuelve todo",
             fontsize=7.5, color="#6b7680")
    fig.text(0.02, 0.015, "Fuente: Secretaría de Energía (datos abiertos). Ventana sep-2023 a dic-2025. "
             "Elaboración: Lleyton Murphy.", fontsize=7, color="#6b7680")
    fig.savefig(RAIZ / "img" / "referencia_dashboard.png", facecolor=FONDO)
    print("img/referencia_dashboard.png")


if __name__ == "__main__":
    main()
