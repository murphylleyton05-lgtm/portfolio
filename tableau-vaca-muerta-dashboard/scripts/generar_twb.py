"""
Genera el libro de Tableau (.twb y .twbx empaquetado) del dashboard de
Vaca Muerta: KPIs + eje doble + dona + treemap, con una accion de filtro.

    python3 scripts/generar_twb.py            # arma tableau/*.twb y *.twbx
    python3 scripts/generar_twb.py --xsd RUTA # ademas valida contra el XSD oficial

El XSD oficial esta en https://github.com/tableau/tableau-document-schemas
(version 2026.1). La validacion es sintactica: la prueba final es abrirlo en
Tableau Public Desktop.
"""

import argparse
import sys
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "vaca_muerta_operadores_mensual.csv"
NOMBRE = "VacaMuerta_Dashboard_Murphy_Lleyton"
DASH = "Dashboard Vaca Muerta"
DS = "federated.0vacamuerta2025"
CONN = "textscan.0vacamuertacsv"
TABLA = "[vaca_muerta_operadores_mensual#csv]"
ULTIMO, ANTERIOR = "dic-2025", "dic-2024"

# Paleta: 3 colores con rol fijo (+ tintes del primario para categorias).
PRIMARIO = "#1f4e79"   # medida principal: petroleo actual
ACENTO = "#e8833a"     # foco: YPF, variacion, lo que hay que mirar
CONTEXTO = "#a6b1bb"   # comparacion / resto: año anterior, "Resto"
TEXTO = "#333f48"
TINTES = ["#1f4e79", "#3d6a94", "#5b86ae", "#7fa3c4"]

W, H = 1200, 820  # tamaño fijo del dashboard en px


def uid() -> str:
    return "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, NOMBRE + str(uid.n))).upper() + "}"


uid.n = 0


def nuevo_uid() -> str:
    uid.n += 1
    return uid()


def a(v) -> str:
    """Valor de atributo XML con comillas."""
    return quoteattr(str(v))


# --------------------------------------------------------------------------
# Campos
# --------------------------------------------------------------------------

COLUMNAS = [
    # nombre, tipo tableau, remote-type, rol, tipo
    ("Mes", "date", 133, "dimension", "ordinal"),
    ("Operador", "string", 129, "dimension", "nominal"),
    ("Petroleo_bbl_d", "integer", 20, "measure", "quantitative"),
    ("Petroleo_bbl_d_anio_anterior", "integer", 20, "measure", "quantitative"),
    ("Gas_Mm3_d", "real", 5, "measure", "quantitative"),
    ("Pozos_activos", "integer", 20, "measure", "quantitative"),
]

ULT = "[Mes] = {FIXED : MAX([Mes])}"

# id, caption, datatype, rol, tipo, formula
CALCULOS = [
    ("Calc_UltOil", "Petróleo último mes (bbl/d)", "integer", "measure", "quantitative",
     f"IF {ULT} THEN [Petroleo_bbl_d] END"),
    ("Calc_UltOilAnt", "Petróleo mismo mes año anterior (bbl/d)", "integer", "measure", "quantitative",
     f"IF {ULT} THEN [Petroleo_bbl_d_anio_anterior] END"),
    ("Calc_UltGas", "Gas último mes (Mm3/d)", "real", "measure", "quantitative",
     f"IF {ULT} THEN [Gas_Mm3_d] END"),
    ("Calc_UltPozos", "Pozos activos último mes", "integer", "measure", "quantitative",
     f"IF {ULT} THEN [Pozos_activos] END"),
    ("Calc_Var", "Var % interanual petróleo", "real", "measure", "quantitative",
     "(SUM([Calc_UltOil]) - SUM([Calc_UltOilAnt])) / SUM([Calc_UltOilAnt])"),
    ("Calc_Prod", "Productividad (bbl/d por pozo)", "real", "measure", "quantitative",
     "SUM([Calc_UltOil]) / SUM([Calc_UltPozos])"),
    ("Calc_Share", "Participación % petróleo", "real", "measure", "quantitative",
     "SUM([Calc_UltOil]) / MIN({FIXED : SUM([Calc_UltOil])})"),
    ("Calc_Grupo", "Grupo operador (dona)", "string", "dimension", "nominal",
     "CASE [Operador]\n"
     "WHEN 'YPF' THEN 'YPF'\n"
     "WHEN 'VISTA ENERGY' THEN 'Vista'\n"
     "WHEN 'PLUSPETROL' THEN 'Pluspetrol'\n"
     "WHEN 'SHELL' THEN 'Shell'\n"
     "WHEN 'PAN AMERICAN ENERGY' THEN 'PAE'\n"
     "ELSE 'Resto'\nEND"),
    ("Calc_ConComp", "Tiene comparación interanual", "boolean", "dimension", "nominal",
     "NOT ISNULL([Petroleo_bbl_d_anio_anterior])"),
    ("Calc_DonaBase", "Dona base", "integer", "measure", "quantitative", "MIN(0)"),
    ("Calc_DonaHueco", "Dona hueco", "integer", "measure", "quantitative", "MIN(0)"),
    ("Calc_TxtOil", "KPI petróleo (texto)", "string", "measure", "nominal",
     'STR(INT(ROUND(SUM([Calc_UltOil]) / 1000, 0))) + " mil bbl/d"'),
    ("Calc_TxtVar", "KPI variación (texto)", "string", "measure", "nominal",
     'IF [Calc_Var] >= 0 THEN "▲ +" ELSE "▼ " END + STR(ROUND([Calc_Var] * 100, 1)) + '
     f'"% vs {ANTERIOR}"'),
    ("Calc_TxtGas", "KPI gas (texto)", "string", "measure", "nominal",
     'STR(ROUND(SUM([Calc_UltGas]) / 1000, 1)) + " MMm³/d"'),
    ("Calc_TxtPozos", "KPI pozos (texto)", "string", "measure", "nominal",
     'STR(INT(SUM([Calc_UltPozos]))) + " pozos"'),
    ("Calc_TxtProd", "KPI productividad (texto)", "string", "measure", "nominal",
     'STR(INT(ROUND([Calc_Prod], 0))) + " bbl/d"'),
]
CALC = {c[0]: c for c in CALCULOS}
# Formatos por defecto (codigo Tableau: n = numero, p = porcentaje).
FORMATOS = {
    "Petroleo_bbl_d": "n#,##0", "Petroleo_bbl_d_anio_anterior": "n#,##0",
    "Pozos_activos": "n#,##0", "Gas_Mm3_d": "n#,##0",
    "Calc_UltOil": "n#,##0", "Calc_UltOilAnt": "n#,##0", "Calc_UltPozos": "n#,##0",
    "Calc_Prod": "n#,##0", "Calc_Var": "p0.0%", "Calc_Share": "p0%",
}
AGREGADOS = {"Calc_Var", "Calc_Prod", "Calc_Share", "Calc_DonaBase", "Calc_DonaHueco",
             "Calc_TxtOil", "Calc_TxtVar", "Calc_TxtGas", "Calc_TxtPozos", "Calc_TxtProd"}
GRUPOS = [("YPF", ACENTO), ("Vista", TINTES[0]), ("Pluspetrol", TINTES[1]),
          ("Shell", TINTES[2]), ("PAE", TINTES[3]), ("Resto", CONTEXTO)]


def ref(inst: str) -> str:
    return f"[{DS}].[{inst}]"


def inst_name(campo: str, deriv: str) -> str:
    """Nombre de column-instance al estilo Tableau."""
    if campo in AGREGADOS:
        tipo = CALC[campo][4]
        return f"usr:{campo}:{'nk' if tipo == 'nominal' else 'qk'}"
    pref = {"Sum": "sum", "None": "none", "Month-Trunc": "tmn"}[deriv]
    if deriv == "None":
        return f"none:{campo}:nk"
    return f"{pref}:{campo}:qk"


def columna_def(campo: str) -> str:
    f = f" default-format={a(FORMATOS[campo])}" if campo in FORMATOS else ""
    for n, dt, _, rol, tipo in COLUMNAS:
        if n == campo:
            return f"<column datatype={a(dt)}{f} name={a('[' + n + ']')} role={a(rol)} type={a(tipo)} />"
    _, cap, dt, rol, tipo, formula = CALC[campo]
    return (f"<column caption={a(cap)} datatype={a(dt)}{f} name={a('[' + campo + ']')} role={a(rol)} type={a(tipo)}>"
            f"<calculation class='tableau' formula={a(formula)} /></column>")


def instancia(campo: str, deriv: str) -> str:
    n = inst_name(campo, deriv)
    d = "User" if campo in AGREGADOS else deriv
    tipo = {"nk": "nominal", "qk": "quantitative", "ok": "ordinal"}[n.rsplit(":", 1)[1]]
    return f"<column-instance column={a('[' + campo + ']')} derivation={a(d)} name={a('[' + n + ']')} pivot='key' type={a(tipo)} />"


def dependencias(usos) -> str:
    """usos: lista de (campo, derivacion). Incluye las dependencias de los calculos."""
    campos, insts = [], []
    pend = [c for c, _ in usos]
    while pend:
        c = pend.pop()
        if c in campos:
            continue
        campos.append(c)
        if c in CALC:
            formula = CALC[c][5]
            pend += [n for n, *_ in COLUMNAS if f"[{n}]" in formula]
            pend += [k for k in CALC if f"[{k}]" in formula]
    for c, d in usos:
        x = instancia(c, d)
        if x not in insts:
            insts.append(x)
    orden = [n for n, *_ in COLUMNAS] + [k for k, *_ in CALCULOS]
    cols = [columna_def(c) for c in sorted(campos, key=orden.index)]
    return (f"<datasource-dependencies datasource={a(DS)}>" + "".join(cols) + "".join(sorted(insts))
            + "</datasource-dependencies>")


# --------------------------------------------------------------------------
# Texto con formato
# --------------------------------------------------------------------------

def run(texto, size=None, color=None, bold=False, campo=None):
    attrs = ""
    if bold:
        attrs += " bold='true'"
    if color:
        attrs += f" fontcolor={a(color)}"
    attrs += " fontname='Tableau Book'" if not bold else " fontname='Tableau Bold'"
    if size:
        attrs += f" fontsize={a(size)}"
    if campo:
        texto = f"<{ref(campo)}>"
    return f"<run{attrs}>{escape(texto)}</run>"


def br():
    return "<run>Æ&#10;</run>"


def formatted(*runs) -> str:
    return "<formatted-text>" + "".join(runs) + "</formatted-text>"


# --------------------------------------------------------------------------
# Datasource
# --------------------------------------------------------------------------

def datasource() -> str:
    cols_csv = "".join(
        f"<column datatype={a(dt)} name={a(n)} ordinal={a(i)} />"
        for i, (n, dt, *_r) in enumerate(COLUMNAS))
    meta = "".join(
        "<metadata-record class='column'>"
        f"<remote-name>{n}</remote-name><remote-type>{rt}</remote-type>"
        f"<local-name>[{n}]</local-name><parent-name>[vaca_muerta_operadores_mensual.csv]</parent-name>"
        f"<remote-alias>{n}</remote-alias><ordinal>{i}</ordinal><local-type>{dt}</local-type>"
        f"<aggregation>{'Year' if dt == 'date' else ('Count' if dt == 'string' else 'Sum')}</aggregation>"
        "<contains-null>true</contains-null></metadata-record>"
        for i, (n, dt, rt, *_r) in enumerate(COLUMNAS))
    campos = "".join(columna_def(n) for n, *_ in COLUMNAS) + "".join(
        columna_def(k) for k, *_ in CALCULOS)
    mapa = "".join(f"<map to={a(col)}><bucket>&quot;{g}&quot;</bucket></map>" for g, col in GRUPOS)
    return (
        f"<datasources><datasource caption='Vaca Muerta · producción oficial' inline='true' name={a(DS)} version='26.1'>"
        "<connection class='federated'><named-connections>"
        f"<named-connection caption='vaca_muerta_operadores_mensual' name={a(CONN)}>"
        "<connection class='textscan' directory='Data/data' filename='vaca_muerta_operadores_mensual.csv' password='' server='' />"
        "</named-connection></named-connections>"
        f"<relation connection={a(CONN)} name='vaca_muerta_operadores_mensual.csv' table={a(TABLA)} type='table'>"
        "<columns character-set='UTF-8' header='yes' locale='en_US' separator=','>"
        f"{cols_csv}</columns></relation>"
        f"<metadata-records>{meta}</metadata-records></connection>"
        "<aliases enabled='yes' />"
        f"{campos}"
        "<layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />"
        "<style><style-rule element='mark'>"
        f"<encoding attr='color' field={a(ref('none:Calc_Grupo:nk'))} type='palette'>{mapa}</encoding>"
        "</style-rule></style>"
        "</datasource></datasources>"
    )


# --------------------------------------------------------------------------
# Hojas
# --------------------------------------------------------------------------

def titulo(texto, sub=None) -> str:
    runs = [run(texto, 13, TEXTO, bold=True)]
    if sub:
        runs += [br(), run(sub, 9, "#6b7680")]
    return f"<layout-options><title>{formatted(*runs)}</title></layout-options>"


def hoja(nombre, usos, panes, rows="", cols="", filtros="", estilo="", tit="") -> str:
    return (
        f"<worksheet name={a(nombre)}>{tit}<table><view>"
        f"<datasources><datasource caption='Vaca Muerta · producción oficial' name={a(DS)} /></datasources>"
        f"{dependencias(usos)}{filtros}<aggregation value='true' /></view>"
        f"<style>{estilo}</style><panes>{panes}</panes>"
        f"<rows>{rows}</rows><cols>{cols}</cols></table>"
        f"<simple-id uuid={a(nuevo_uid())} /></worksheet>"
    )


def pane(mark, encodings="", label="", estilo="", pid=None, eje=None) -> str:
    extra = f" id={a(pid)}" if pid is not None else ""
    if eje:
        extra += f" y-axis-name={a(ref(eje))}"
    enc = f"<encodings>{encodings}</encodings>" if encodings else ""
    lab = f"<customized-label>{label}</customized-label>" if label else ""
    est = f"<style><style-rule element='mark'>{estilo}</style-rule></style>" if estilo else ""
    return (f"<pane selection-relaxation-option='selection-relaxation-allow'{extra}>"
            f"<view><breakdown value='auto' /></view><mark class={a(mark)} />{enc}{lab}{est}</pane>")


def fmt(attr, valor) -> str:
    return f"<format attr={a(attr)} value={a(valor)} />"


def hoja_kpi(nombre, etiqueta, campo_valor, campo_sub=None) -> str:
    usos = [(campo_valor, "User")] + ([(campo_sub, "User")] if campo_sub else [])
    enc = f"<text column={a(ref(inst_name(campo_valor, 'User')))} />"
    runs = [run(etiqueta, 9, "#6b7680", bold=True), br(),
            run("", 20, PRIMARIO, bold=True, campo=inst_name(campo_valor, "User"))]
    if campo_sub:
        enc += f"<text column={a(ref(inst_name(campo_sub, 'User')))} />"
        runs += [br(), run("", 10, ACENTO, bold=True, campo=inst_name(campo_sub, "User"))]
    p = pane("Text", enc, formatted(*runs),
             fmt("mark-labels-show", "true") + fmt("text-align", "left"))
    estilo = "<style-rule element='table'>" + fmt("background-color", "#ffffff") + "</style-rule>"
    return hoja(nombre, usos, p, estilo=estilo)


def hoja_eje_doble() -> str:
    oil = "sum:Petroleo_bbl_d:qk"
    ant = "sum:Petroleo_bbl_d_anio_anterior:qk"
    mes = "tmn:Mes:qk"
    usos = [("Petroleo_bbl_d", "Sum"), ("Petroleo_bbl_d_anio_anterior", "Sum"),
            ("Mes", "Month-Trunc"), ("Calc_ConComp", "None")]
    filtro = (f"<filter class='categorical' column={a(ref('none:Calc_ConComp:nk'))}>"
              f"<groupfilter function='member' level={a('[none:Calc_ConComp:nk]')} member='true' "
              "user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />"
              "</filter>"
              f"<slices><column>{ref('none:Calc_ConComp:nk')}</column></slices>")
    panes = (pane("Automatic")
             + pane("Bar", pid=1, eje=oil, estilo=fmt("mark-color", PRIMARIO) + fmt("size", "0.6"))
             + pane("Line", pid=2, eje=ant, estilo=fmt("mark-color", CONTEXTO)
                    + fmt("mark-labels-show", "false")))
    estilo = (
        "<style-rule element='axis'>"
        f"<encoding attr='space' class='0' field={a(ref(ant))} field-type='quantitative' fold='true' "
        "scope='rows' synchronized='true' type='space' />"
        f"<format attr='display' class='0' field={a(ref(ant))} scope='rows' value='false' />"
        f"<format attr='title' class='0' field={a(ref(oil))} scope='rows' value='Petróleo (bbl/d)' />"
        f"<format attr='title' class='0' field={a(ref(mes))} scope='cols' value='' />"
        "</style-rule>"
        "<style-rule element='gridline'>" + fmt("line-visibility", "off") + "</style-rule>"
    )
    return hoja(
        "Eje doble · Petróleo vs año anterior", usos, panes,
        rows=f"({ref(oil)} + {ref(ant)})", cols=ref(mes), filtros=filtro, estilo=estilo,
        tit=titulo("¿Cuánto creció el petróleo frente al mismo mes del año anterior?",
                   "Barras: producción del mes (bbl/d) · Línea gris: mismo mes del año anterior · ejes sincronizados"))


def hoja_dona() -> str:
    base, hueco = "usr:Calc_DonaBase:qk", "usr:Calc_DonaHueco:qk"
    oil, share, grupo, txt = ("sum:Calc_UltOil:qk", "usr:Calc_Share:qk",
                             "none:Calc_Grupo:nk", "usr:Calc_TxtOil:nk")
    usos = [("Calc_DonaBase", "User"), ("Calc_DonaHueco", "User"), ("Calc_UltOil", "Sum"),
            ("Calc_Share", "User"), ("Calc_Grupo", "None"), ("Calc_TxtOil", "User")]
    enc1 = (f"<color column={a(ref(grupo))} /><wedge-size column={a(ref(oil))} />"
            f"<text column={a(ref(grupo))} /><text column={a(ref(share))} />")
    lab1 = formatted(run("", 9, TEXTO, bold=True, campo=grupo), br(), run("", 9, TEXTO, campo=share))
    enc2 = f"<text column={a(ref(txt))} />"
    lab2 = formatted(run("", 15, PRIMARIO, bold=True, campo=txt), br(), run(ULTIMO, 9, "#6b7680"))
    panes = (pane("Pie")
             + pane("Pie", enc1, lab1, fmt("mark-labels-show", "true") + fmt("size", "4.2"),
                    pid=1, eje=base)
             + pane("Pie", enc2, lab2, fmt("mark-labels-show", "true") + fmt("mark-color", "#ffffff")
                    + fmt("size", "2.4"), pid=2, eje=hueco))
    estilo = (
        "<style-rule element='axis'>"
        f"<encoding attr='space' class='0' field={a(ref(hueco))} field-type='quantitative' fold='true' "
        "scope='rows' synchronized='true' type='space' />"
        f"<format attr='display' class='0' field={a(ref(base))} scope='rows' value='false' />"
        f"<format attr='display' class='0' field={a(ref(hueco))} scope='rows' value='false' />"
        "</style-rule>"
        "<style-rule element='gridline'>" + fmt("line-visibility", "off") + "</style-rule>"
        "<style-rule element='zeroline'>" + fmt("line-visibility", "off") + "</style-rule>"
        f"<style-rule element='field-labels'>{fmt('display', 'false')}</style-rule>"
    )
    return hoja("Dona · Participación por operador", usos, panes,
                rows=f"({ref(base)} + {ref(hueco)})", estilo=estilo,
                tit=titulo(f"¿Quién produce el petróleo? ({ULTIMO})",
                           "Participación en bbl/d · top 5 operadores + resto"))


def hoja_treemap() -> str:
    oil, prod, op = "sum:Calc_UltOil:qk", "usr:Calc_Prod:qk", "none:Operador:nk"
    usos = [("Calc_UltOil", "Sum"), ("Calc_Prod", "User"), ("Operador", "None")]
    enc = (f"<color column={a(ref(prod))} /><size column={a(ref(oil))} />"
           f"<text column={a(ref(op))} /><text column={a(ref(oil))} /><text column={a(ref(prod))} />")
    lab = formatted(run("", 10, "#ffffff", bold=True, campo=op), br(),
                    run("", 9, "#ffffff", campo=oil), run(" bbl/d", 9, "#ffffff"), br(),
                    run("", 9, "#ffffff", campo=prod), run(" bbl/d por pozo", 9, "#ffffff"))
    p = pane("Square", enc, lab, fmt("mark-labels-show", "true"))
    estilo = (
        "<style-rule element='mark'>"
        f"<encoding attr='color' field={a(ref(prod))} type='interpolated'>"
        "<color-palette custom='true' name='' type='ordered-sequential'>"
        f"<color>{CONTEXTO}</color><color>{PRIMARIO}</color></color-palette></encoding>"
        "</style-rule>"
    )
    return hoja(
        "Treemap · Operadores", usos, p, estilo=estilo,
        tit=titulo(f"¿Cómo se distribuye la producción entre operadores? ({ULTIMO})",
                   "Tamaño: petróleo (bbl/d) · Color: productividad por pozo · "
                   "Hacé clic en un operador para filtrar el tablero; clic de nuevo para volver"))


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------

class Zonas:
    def __init__(self):
        self.n = 0

    def id(self):
        self.n += 1
        return self.n


Z = Zonas()


def coords(x, y, w, h) -> str:
    """px -> unidades de Tableau (100000 = ancho/alto completo)."""
    return (f"x={a(round(x * 100000 / W))} y={a(round(y * 100000 / H))} "
            f"w={a(round(w * 100000 / W))} h={a(round(h * 100000 / H))}")


def zona_estilo(fondo=None, borde=None, padding=None) -> str:
    f = ""
    if fondo:
        f += fmt("background-color", fondo)
    if borde:
        f += fmt("border-color", borde) + fmt("border-style", "solid") + fmt("border-width", "1")
    if padding is not None:
        f += fmt("margin", str(padding))
    return f"<zone-style>{f}</zone-style>" if f else ""


def z_hoja(nombre, x, y, w, h, show_title=True, **est) -> str:
    st = "" if show_title else " show-title='false'"
    return f"<zone {coords(x, y, w, h)} id={a(Z.id())} name={a(nombre)}{st}>{zona_estilo(**est)}</zone>"


def z_texto(texto_xml, x, y, w, h, **est) -> str:
    return (f"<zone {coords(x, y, w, h)} id={a(Z.id())} type-v2='text'>{texto_xml}"
            f"{zona_estilo(**est)}</zone>")


def z_imagen(archivo, x, y, w, h) -> str:
    return (f"<zone {coords(x, y, w, h)} id={a(Z.id())} is-centered='1' is-scaled='1' "
            f"param={a('Image/' + archivo)} type-v2='bitmap'>{zona_estilo(padding=10)}</zone>")


def z_cont(direccion, hijos, x, y, w, h, **est) -> str:
    return (f"<zone {coords(x, y, w, h)} id={a(Z.id())} param={a(direccion)} type-v2='layout-flow'>"
            + "".join(hijos) + zona_estilo(**est) + "</zone>")


KPIS = [
    ("KPI Petróleo", "icono_petroleo.png"),
    ("KPI Gas", "icono_gas.png"),
    ("KPI Pozos", "icono_pozos.png"),
    ("KPI Productividad", "icono_productividad.png"),
]


def dashboard() -> str:
    M = 16                      # margen externo
    ancho = W - 2 * M
    y0 = M
    h_tit, h_kpi, h_mid, h_bot, h_pie = 78, 100, 330, 250, 30
    gap = 10

    titulo_xml = formatted(
        run("El petróleo de Vaca Muerta creció 32% en un año y YPF aporta más de la mitad", 20, PRIMARIO, bold=True),
        br(),
        run(f"Producción no convencional, {ULTIMO}: 602 mil bbl/d vs 456 mil en {ANTERIOR}. "
            "YPF explica 56% del total; Chevron y Pampa son los más productivos por pozo.", 11, TEXTO))
    zt = z_texto(titulo_xml, M, y0, ancho, h_tit)

    # Fila de KPIs: 4 tarjetas (icono + hoja), cada una en su contenedor horizontal.
    y1 = y0 + h_tit + gap
    wk = (ancho - 3 * gap) / 4
    tarjetas = []
    for i, (hoja_kpi_nombre, icono) in enumerate(KPIS):
        x = M + i * (wk + gap)
        tarjetas.append(z_cont("horz", [
            z_imagen(icono, x, y1, 64, h_kpi),
            z_hoja(hoja_kpi_nombre, x + 64, y1, wk - 64, h_kpi, show_title=False),
        ], x, y1, wk, h_kpi, fondo="#ffffff", borde="#d9dee3"))
    zk = z_cont("horz", tarjetas, M, y1, ancho, h_kpi)

    # Centro: eje doble (macro) + dona.
    y2 = y1 + h_kpi + gap
    w_eje = round(ancho * 0.62)
    zm = z_cont("horz", [
        z_hoja("Eje doble · Petróleo vs año anterior", M, y2, w_eje, h_mid, fondo="#ffffff", borde="#d9dee3"),
        z_hoja("Dona · Participación por operador", M + w_eje + gap, y2, ancho - w_eje - gap, h_mid,
               fondo="#ffffff", borde="#d9dee3"),
    ], M, y2, ancho, h_mid)

    # Abajo: detalle por operador (origen de la accion de filtro).
    y3 = y2 + h_mid + gap
    zb = z_hoja("Treemap · Operadores", M, y3, ancho, h_bot, fondo="#ffffff", borde="#d9dee3")

    y4 = y3 + h_bot + gap / 2
    pie = z_texto(formatted(run(
        "Fuente: Secretaría de Energía (datos abiertos, producción de pozos no convencionales). "
        "Ventana: sep-2023 a dic-2025. Elaboración: Lleyton Murphy.", 8, "#6b7680")),
        M, y4, ancho, h_pie)

    vertical = z_cont("vert", [zt, zk, zm, zb, pie], M, y0, ancho, H - 2 * M)
    raiz = (f"<zone h='100000' id={a(Z.id())} type-v2='layout-basic' w='100000' x='0' y='0'>"
            f"{vertical}{zona_estilo(fondo='#f4f6f8')}</zone>")
    return (
        f"<dashboards><dashboard name={a(DASH)}>"
        "<style><style-rule element='table'>" + fmt("background-color", "#f4f6f8") + "</style-rule></style>"
        f"<size maxheight={a(H)} maxwidth={a(W)} minheight={a(H)} minwidth={a(W)} sizing-mode='fixed' />"
        f"<zones>{raiz}</zones>"
        f"<simple-id uuid={a(nuevo_uid())} /></dashboard></dashboards>"
    )


def acciones() -> str:
    return (
        "<actions>"
        "<action caption='Filtrar tablero por operador' name='[Action_FiltroOperador]'>"
        "<activation auto-clear='true' type='on-select' />"
        f"<source dashboard={a(DASH)} type='sheet' worksheet='Treemap · Operadores' />"
        "<command command='tsc:tsl-filter'>"
        "<param name='exclude' value='Dona · Participación por operador' />"
        "<param name='special-fields' value='all' />"
        f"<param name='target' value={a(DASH)} />"
        "</command></action></actions>"
    )


def ventanas() -> str:
    hojas = ["KPI Petróleo", "KPI Gas", "KPI Pozos", "KPI Productividad",
             "Eje doble · Petróleo vs año anterior", "Dona · Participación por operador",
             "Treemap · Operadores"]
    w = "".join(
        f"<window class='worksheet' name={a(h)}><cards><edge name='left'><strip size='160'>"
        "<card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
        "<edge name='top'><strip size='31'><card type='columns' /></strip>"
        "<strip size='31'><card type='rows' /></strip><strip size='31'><card type='title' /></strip>"
        f"</edge></cards><simple-id uuid={a(nuevo_uid())} /></window>"
        for h in hojas)
    d = (f"<window class='dashboard' maximized='true' name={a(DASH)}>"
         "<viewpoints /><active id='-1' />"
         f"<simple-id uuid={a(nuevo_uid())} /></window>")
    return f"<windows source-height='30'>{w}{d}</windows>"


def workbook() -> str:
    hojas = (
        hoja_kpi("KPI Petróleo", f"PETRÓLEO · {ULTIMO.upper()}", "Calc_TxtOil", "Calc_TxtVar")
        + hoja_kpi("KPI Gas", f"GAS · {ULTIMO.upper()}", "Calc_TxtGas")
        + hoja_kpi("KPI Pozos", "POZOS EN PRODUCCIÓN", "Calc_TxtPozos")
        + hoja_kpi("KPI Productividad", "PETRÓLEO POR POZO", "Calc_TxtProd")
        + hoja_eje_doble() + hoja_dona() + hoja_treemap()
    )
    return (
        "<?xml version='1.0' encoding='utf-8' ?>\n"
        "<workbook original-version='26.1' source-build='0.0.0 (0000.0.0.0)' source-platform='win' "
        "version='26.1' xmlns:user='http://www.tableausoftware.com/xml/user'>"
        "<document-format-change-manifest><ManifestByVersion /></document-format-change-manifest>"
        "<preferences><preference name='ui.encoding.shelf.height' value='24' />"
        "<preference name='ui.shelf.height' value='26' /></preferences>"
        f"{datasource()}{acciones()}<worksheets>{hojas}</worksheets>{dashboard()}{ventanas()}"
        "<explain-data enabled-for-viewer='true' extreme-values-enabled-for-all='false'>"
        "<explanation-types /></explain-data>"
        "</workbook>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xsd", help="ruta al twb_2026.1.0.xsd (con sus imports resueltos)")
    args = ap.parse_args()

    xml = workbook()
    salida = RAIZ / "tableau"
    salida.mkdir(exist_ok=True)
    twb = salida / f"{NOMBRE}.twb"
    twb.write_text(xml, encoding="utf-8")

    if args.xsd:
        from lxml import etree
        esquema = etree.XMLSchema(etree.parse(args.xsd))
        doc = etree.fromstring(xml.encode("utf-8"))
        if not esquema.validate(doc):
            for e in esquema.error_log:
                print(f"línea {e.line}: {e.message}")
            sys.exit(1)
        print("XSD: el .twb es válido")

    twbx = salida / f"{NOMBRE}.twbx"
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{NOMBRE}.twb", xml)
        z.write(CSV, "Data/data/" + CSV.name)
        for png in sorted((RAIZ / "img").glob("icono_*.png")):
            z.write(png, "Image/" + png.name)
    print(f"-> {twb.relative_to(RAIZ)}\n-> {twbx.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
