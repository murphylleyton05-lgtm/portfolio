import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY = "#1F3864"; ACCENT = "#2E74B5"; HEAD = "#1F3864"; BODY = "#EAF1FB"; PK = "#C00000"

fig, ax = plt.subplots(figsize=(11, 6.2), dpi=140)
ax.set_xlim(0, 11); ax.set_ylim(0, 6.2); ax.axis("off")

def entity(x, y, w, title, fields):
    row_h = 0.42
    h = row_h * (len(fields) + 1)
    # header
    ax.add_patch(FancyBboxPatch((x, y+h-row_h), w, row_h,
                 boxstyle="round,pad=0,rounding_size=0.02",
                 linewidth=1.2, edgecolor=NAVY, facecolor=HEAD, mutation_aspect=1))
    ax.text(x+w/2, y+h-row_h/2, title, ha="center", va="center",
            color="white", fontsize=11, fontweight="bold")
    for i, (name, tag) in enumerate(fields):
        ry = y + h - row_h*(i+2)
        ax.add_patch(plt.Rectangle((x, ry), w, row_h, linewidth=0.8,
                     edgecolor="#BBBBBB", facecolor=BODY))
        color = PK if tag in ("PK", "FK") else "#222222"
        weight = "bold" if tag in ("PK", "FK") else "normal"
        label = name + (f"  ({tag})" if tag else "")
        ax.text(x+0.12, ry+row_h/2, label, ha="left", va="center",
                color=color, fontsize=8.6, fontweight=weight)
    return (x, y, w, h)

# Entities
cli = entity(0.4, 3.4, 2.9, "Dim_Clientes", [
    ("id_cliente", "PK"), ("nombre_cliente", ""), ("ciudad", ""),
    ("pais", ""), ("canal", "")])
prod = entity(0.4, 0.2, 2.9, "Dim_Productos", [
    ("id_producto", "PK"), ("nombre_producto", ""), ("categoria", ""),
    ("precio", ""), ("stock", "")])
fact = entity(7.0, 1.7, 3.6, "Fact_Ventas", [
    ("id_venta", "PK"), ("id_cliente", "FK"), ("id_producto", "FK"),
    ("fecha_venta", ""), ("cantidad", ""), ("precio_unitario", ""),
    ("total_venta", "")])

def relate(a, b, txt, ay, by):
    ax_, ay_, aw, ah = a
    bx_, by_, bw, bh = b
    x1 = ax_ + aw; x2 = bx_
    arrow = FancyArrowPatch((x1, ay), (x2, by), arrowstyle="-|>",
        mutation_scale=16, linewidth=1.6, color=ACCENT,
        connectionstyle="arc3,rad=0.0")
    ax.add_patch(arrow)
    ax.text(x1+0.25, ay+0.18, "1", color=NAVY, fontsize=11, fontweight="bold")
    ax.text(x2-0.45, by+0.18, "N", color=NAVY, fontsize=11, fontweight="bold")
    ax.text((x1+x2)/2, (ay+by)/2+0.22, txt, color="#555555", fontsize=8,
            ha="center", style="italic")

relate(cli, fact, "realiza", 4.15, 3.05)
relate(prod, fact, "incluye", 1.05, 2.15)

ax.text(5.5, 6.0, "Modelo entidad-relacion (esquema en estrella) - RetailPro / TechStore",
        ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)
ax.text(5.5, 0.02, "Relaciones 1:N  -  un cliente y un producto pueden aparecer en muchas ventas",
        ha="center", va="bottom", fontsize=8.5, color="#777777")

plt.tight_layout()
out = "/tmp/claude-0/-home-user-portfolio/4c309c01-0fb3-591e-b34d-06bb0c3dc912/scratchpad/er_diagram.png"
plt.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
print("WROTE", out)
