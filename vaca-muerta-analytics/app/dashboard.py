"""
Dashboard de analisis de pozos no convencionales - Vaca Muerta.

Se levanta con:
    streamlit run app/dashboard.py

Lee UNICAMENTE los archivos de data/procesado/. No descarga ni recalcula nada:
todo el trabajo pesado lo hizo scripts/preparar_datos.py. Esa separacion es
deliberada -- un dashboard que recalcula en cada click es un dashboard lento, y
la lentitud es lo primero que se nota cuando lo mostras en una entrevista.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import config, declinacion  # noqa: E402
from petro.limpieza import BARRILES_POR_M3  # noqa: E402

st.set_page_config(
    page_title="Vaca Muerta Analytics",
    page_icon="🛢️",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Carga de datos (cacheada)
# ---------------------------------------------------------------------------

@st.cache_data
def cargar():
    """
    Lee los parquet procesados.

    @st.cache_data hace que Streamlit lea los archivos UNA sola vez y reuse el
    resultado en cada interaccion. Sin esto, cada movimiento de un filtro
    volveria a leer el disco.
    """
    if not config.AJUSTES.exists():
        return None

    produccion = pd.read_parquet(config.PRODUCCION)
    ajustes = pd.read_parquet(config.AJUSTES)
    precios = pd.read_parquet(config.PRECIOS) if config.PRECIOS.exists() else pd.DataFrame()
    metadatos = json.loads(config.METADATOS.read_text()) if config.METADATOS.exists() else {}
    return produccion, ajustes, precios, metadatos


datos = cargar()

if datos is None:
    st.title("🛢️ Vaca Muerta Analytics")
    st.error("No hay datos procesados todavia.")
    st.markdown(
        """
        Corre estos dos comandos en la raiz del proyecto y volve a cargar la pagina:

        ```bash
        python scripts/generar_demo.py       # o: python scripts/descargar_datos.py
        python scripts/preparar_datos.py
        ```
        """
    )
    st.stop()

produccion, ajustes, precios, metadatos = datos


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------

st.title("🛢️ Vaca Muerta Analytics")
st.caption(
    "Analisis de curvas de declinacion y productividad de pozos no convencionales · "
    "Datos: Secretaria de Energia de la Nacion (datos.energia.gob.ar)"
)

if metadatos.get("es_demo"):
    st.warning(
        "**Datos de DEMOSTRACION (sinteticos).** Estos pozos no existen: se generaron "
        "con curvas de Arps y ruido para que la app sea navegable sin descargar los "
        "datasets oficiales. Para usar datos reales: `python scripts/descargar_datos.py` "
        "y despues `python scripts/preparar_datos.py`.",
        icon="⚠️",
    )


# ---------------------------------------------------------------------------
# Filtros (barra lateral)
# ---------------------------------------------------------------------------

st.sidebar.header("Filtros")

empresas = sorted(ajustes["empresa"].dropna().unique())
empresas_sel = st.sidebar.multiselect("Operadora", empresas, default=empresas)

areas = sorted(ajustes["area"].dropna().unique())
areas_sel = st.sidebar.multiselect("Area / bloque", areas, default=areas)

r2_minimo = st.sidebar.slider(
    "R² minimo del ajuste",
    0.0, 1.0, float(config.R2_MINIMO_CONFIABLE), 0.05,
    help=(
        "Descarta pozos cuyo ajuste de declinacion es malo. Un R² bajo suele "
        "indicar un pozo con historia irregular (paradas largas, intervenciones, "
        "cambios de sistema de extraccion) que Arps no describe bien."
    ),
)

solo_convergidos = st.sidebar.checkbox(
    "Solo ajustes convergidos", value=True,
    help="Excluye pozos donde el optimizador no encontro solucion.",
)

st.sidebar.divider()
st.sidebar.caption(
    f"Ultimo procesamiento: {metadatos.get('generado_en', 's/d')[:16].replace('T', ' ')}  \n"
    f"Periodo: {metadatos.get('primer_mes', '?')} a {metadatos.get('ultimo_mes', '?')}  \n"
    f"Horizonte EUR: {metadatos.get('horizonte_eur_meses', '?')} meses  \n"
    f"Declinacion terminal: {metadatos.get('d_terminal_anual', 0) * 100:.0f}% anual"
)

# Aplicamos los filtros.
mask = (
    ajustes["empresa"].isin(empresas_sel)
    & ajustes["area"].isin(areas_sel)
    & (ajustes["r2"] >= r2_minimo)
)
if solo_convergidos:
    mask &= ajustes["convergio"]

aj = ajustes[mask].copy()
prod = produccion[produccion["id_pozo"].isin(aj["id_pozo"])].copy()

if aj.empty:
    st.warning("Ningun pozo cumple los filtros. Aflojá el R² minimo o sumá operadoras.")
    st.stop()

# Columnas derivadas en unidades de la industria (barriles).
aj["eur_mbbl"] = aj["eur"] * BARRILES_POR_M3 / 1000.0
aj["qi_bbld"] = aj["qi"] * BARRILES_POR_M3


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Pozos analizados", f"{len(aj):,}")
k2.metric("Operadoras", f"{aj['empresa'].nunique()}")
k3.metric(
    "Acumulado historico",
    f"{aj['acum_petroleo_m3'].sum() * BARRILES_POR_M3 / 1e6:,.1f} MMbbl",
    help="Suma de la produccion historica de petroleo de los pozos filtrados.",
)
k4.metric(
    "EUR mediano / pozo",
    f"{aj['eur_mbbl'].median():,.0f} Mbbl",
    help="Produccion total estimada de un pozo tipico, en miles de barriles.",
)
k5.metric(
    "Declinacion inicial mediana",
    f"{aj['di_anual'].median() * 100:,.0f} % /año",
    help="Tasa de declinacion nominal en el primer mes, anualizada.",
)


# ---------------------------------------------------------------------------
# Pestañas
# ---------------------------------------------------------------------------

tab_pozo, tab_bench, tab_rank, tab_panorama, tab_macro = st.tabs([
    "📉 Curva de declinacion",
    "📊 Curvas tipo (benchmark)",
    "🏆 Ranking de pozos",
    "🗺️ Panorama",
    "💵 Contexto macro",
])


# --- 1. Curva de declinacion de un pozo ------------------------------------

with tab_pozo:
    st.subheader("Ajuste de Arps pozo por pozo")
    st.markdown(
        "Cada punto es la produccion real de un mes; la linea es el modelo ajustado "
        "y su extrapolacion. El modelo es **hiperbolico modificado**: sigue Arps "
        "hasta que la declinacion cae al valor terminal y despues continua "
        "exponencial, para que el EUR no diverja."
    )

    col_izq, col_der = st.columns([1, 3])

    with col_izq:
        orden = st.radio(
            "Ordenar pozos por", ["EUR (mayor primero)", "R² (mejor ajuste)", "ID"],
            index=0,
        )
        if orden.startswith("EUR"):
            aj_ordenado = aj.sort_values("eur", ascending=False)
        elif orden.startswith("R²"):
            aj_ordenado = aj.sort_values("r2", ascending=False)
        else:
            aj_ordenado = aj.sort_values("id_pozo")

        etiquetas = {
            f"{fila.sigla} · {fila.empresa[:18]} · EUR {fila.eur_mbbl:,.0f} Mbbl": fila.id_pozo
            for fila in aj_ordenado.itertuples()
        }
        elegido = st.selectbox("Pozo", list(etiquetas))
        id_elegido = etiquetas[elegido]

        horizonte = st.slider("Horizonte del pronostico (meses)", 24, 360, 120, 12)

    fila = aj[aj["id_pozo"] == id_elegido].iloc[0]
    serie_pozo = prod[prod["id_pozo"] == id_elegido]
    serie = declinacion.preparar_serie(serie_pozo, col_caudal="caudal_petroleo_m3d")

    ajuste = declinacion.AjusteDeclinacion(
        id_pozo=fila["id_pozo"], qi=fila["qi"], di_mensual=fila["di_mensual"],
        di_anual=fila["di_anual"], b=fila["b"], r2=fila["r2"], rmse=fila["rmse"],
        n_meses=int(fila["n_meses"]), eur=fila["eur"], eur_unidad="m3",
        convergio=bool(fila["convergio"]),
    )
    curva = declinacion.pronostico(
        ajuste, horizonte_meses=horizonte, d_terminal_anual=config.D_TERMINAL_ANUAL
    )

    with col_der:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=serie["t_meses"], y=serie["caudal_petroleo_m3d"] * BARRILES_POR_M3,
            mode="markers", name="Produccion real",
            marker=dict(size=7, color="#1f77b4"),
        ))
        fig.add_trace(go.Scatter(
            x=curva["t_meses"], y=curva["caudal_modelo"] * BARRILES_POR_M3,
            mode="lines", name="Arps ajustada + pronostico",
            line=dict(width=3, color="#d62728"),
        ))
        # Marca visual de donde termina la historia y empieza la extrapolacion.
        if not serie.empty:
            fig.add_vline(
                x=float(serie["t_meses"].max()), line_dash="dot", line_color="grey",
                annotation_text="fin de la historia", annotation_position="top",
            )
        fig.update_layout(
            height=460,
            xaxis_title="Meses desde el pico de produccion",
            yaxis_title="Caudal de petroleo (bbl/d)",
            legend=dict(orientation="h", y=1.1),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig, width="stretch")

        escala_log = st.checkbox("Escala logaritmica en Y", value=False,
                                 help="En log, una declinacion exponencial se ve como una recta.")
        if escala_log:
            fig.update_yaxes(type="log")
            st.plotly_chart(fig, width="stretch")

    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("qi (caudal inicial)", f"{fila['qi_bbld']:,.0f} bbl/d")
    p2.metric("Di (declinacion inicial)", f"{fila['di_anual'] * 100:,.0f} %/año")
    p3.metric("b (exponente Arps)", f"{fila['b']:.2f}")
    p4.metric("R² del ajuste", f"{fila['r2']:.3f}")
    p5.metric("EUR estimado", f"{fila['eur_mbbl']:,.0f} Mbbl")

    with st.expander("Como leer estos parametros"):
        st.markdown(
            """
            - **qi**: el caudal del pozo al inicio de la declinacion (su pico). Es la
              medida mas directa de "que tan bueno salio" el pozo.
            - **Di**: que tan rapido cae. En shale de Vaca Muerta es normal ver
              declinaciones nominales iniciales muy altas.
            - **b**: la "curvatura" de la caida. b alto significa que el pozo cae
              fuerte al principio pero despues se aplana y produce mucho tiempo a
              caudal bajo. Valores de b mayores a 1 son comunes en shale y son la
              razon por la que hace falta el corte terminal.
            - **R²**: que tan bien el modelo describe los datos. Abajo de 0.7 conviene
              mirar el pozo a mano antes de sacar conclusiones.
            - **EUR**: el volumen total que se espera producir. Es el numero que
              termina alimentando cualquier evaluacion economica del pozo.
            """
        )


# --- 2. Curvas tipo --------------------------------------------------------

with tab_bench:
    st.subheader("Curvas tipo: comparar grupos de pozos")
    st.markdown(
        "Una **curva tipo** alinea todos los pozos de un grupo por su *mes de vida* "
        "(no por fecha calendario) y muestra el comportamiento tipico del conjunto. "
        "Es la forma en que la industria compara bloques y operadoras sin que el "
        "resultado dependa de cuando se perforo cada pozo."
    )

    agrupar_por = st.selectbox("Comparar por", ["empresa", "area"], index=0)
    grupos_disponibles = (
        aj.groupby(agrupar_por)["id_pozo"].count().sort_values(ascending=False)
    )
    grupos_sel = st.multiselect(
        "Grupos a comparar",
        list(grupos_disponibles.index),
        default=list(grupos_disponibles.index[:4]),
    )

    if grupos_sel:
        fig = go.Figure()
        resumen_filas = []
        colores = px.colors.qualitative.Plotly

        for i, grupo in enumerate(grupos_sel):
            ids = aj[aj[agrupar_por] == grupo]["id_pozo"]
            sub = prod[prod["id_pozo"].isin(ids)]
            ct = declinacion.curva_tipo(sub, col_caudal="caudal_petroleo_m3d")
            if ct.empty:
                continue
            # Solo mostramos meses con al menos 3 pozos: con menos, la mediana
            # es ruido y la curva se dispara al final.
            ct = ct[ct["n_pozos"] >= 3]
            color = colores[i % len(colores)]

            fig.add_trace(go.Scatter(
                x=ct["mes_vida"], y=ct["p50"] * BARRILES_POR_M3,
                mode="lines", name=f"{grupo} (n={len(ids)})",
                line=dict(width=3, color=color),
            ))
            resumen_filas.append({
                agrupar_por: grupo,
                "pozos": len(ids),
                "qi mediano (bbl/d)": aj[aj[agrupar_por] == grupo]["qi_bbld"].median(),
                "b mediano": aj[aj[agrupar_por] == grupo]["b"].median(),
                "Di mediano (%/año)": aj[aj[agrupar_por] == grupo]["di_anual"].median() * 100,
                "EUR mediano (Mbbl)": aj[aj[agrupar_por] == grupo]["eur_mbbl"].median(),
            })

        fig.update_layout(
            height=470,
            xaxis_title="Mes de vida del pozo",
            yaxis_title="Caudal mediano P50 (bbl/d)",
            legend=dict(orientation="h", y=1.12),
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, width="stretch")

        st.dataframe(
            pd.DataFrame(resumen_filas).round(1).sort_values(
                "EUR mediano (Mbbl)", ascending=False
            ),
            width="stretch", hide_index=True,
        )


# --- 3. Ranking ------------------------------------------------------------

with tab_rank:
    st.subheader("Ranking de pozos por EUR estimado")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        tabla = aj[[
            "sigla", "empresa", "area", "primer_mes", "meses_produccion",
            "qi_bbld", "di_anual", "b", "r2", "eur_mbbl",
        ]].copy()
        tabla["di_anual"] = tabla["di_anual"] * 100
        tabla["primer_mes"] = pd.to_datetime(tabla["primer_mes"]).dt.strftime("%Y-%m")
        tabla = tabla.rename(columns={
            "sigla": "Pozo", "empresa": "Operadora", "area": "Area",
            "primer_mes": "Puesta en marcha", "meses_produccion": "Meses",
            "qi_bbld": "qi (bbl/d)", "di_anual": "Di (%/año)", "b": "b",
            "r2": "R²", "eur_mbbl": "EUR (Mbbl)",
        })
        st.dataframe(
            tabla.sort_values("EUR (Mbbl)", ascending=False).round(2),
            width="stretch", hide_index=True, height=430,
        )
        st.download_button(
            "⬇️ Descargar ranking (CSV)",
            tabla.to_csv(index=False).encode("utf-8"),
            file_name="ranking_pozos_eur.csv",
            mime="text/csv",
        )

    with col_b:
        fig = px.histogram(
            aj, x="eur_mbbl", nbins=30,
            labels={"eur_mbbl": "EUR (Mbbl)"},
            title="Distribucion del EUR",
        )
        fig.update_layout(height=250, showlegend=False, margin=dict(t=45, b=30))
        st.plotly_chart(fig, width="stretch")

        fig2 = px.scatter(
            aj, x="qi_bbld", y="eur_mbbl", color="empresa",
            labels={"qi_bbld": "qi (bbl/d)", "eur_mbbl": "EUR (Mbbl)"},
            title="qi vs EUR",
        )
        fig2.update_layout(height=280, showlegend=False, margin=dict(t=45, b=30))
        st.plotly_chart(fig2, width="stretch")
        st.caption(
            "La relacion entre caudal inicial y EUR es fuerte pero no perfecta: "
            "dos pozos con el mismo pico pueden terminar muy distinto segun como declinen."
        )


# --- 4. Panorama -----------------------------------------------------------

with tab_panorama:
    st.subheader("Produccion agregada")

    mensual = (
        prod.groupby("fecha")
        .agg(
            petroleo_m3=("prod_petroleo_m3", "sum"),
            gas_mm3=("prod_gas_mm3", "sum"),
            pozos_activos=("id_pozo", "nunique"),
        )
        .reset_index()
    )
    mensual["petroleo_kbbld"] = (
        mensual["petroleo_m3"] * BARRILES_POR_M3 / 30.4375 / 1000.0
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mensual["fecha"], y=mensual["petroleo_kbbld"],
        mode="lines", name="Petroleo (kbbl/d)", line=dict(width=3),
    ))
    fig.add_trace(go.Scatter(
        x=mensual["fecha"], y=mensual["pozos_activos"],
        mode="lines", name="Pozos activos", yaxis="y2",
        line=dict(width=2, dash="dot"),
    ))
    fig.update_layout(
        height=400,
        xaxis_title="Mes",
        yaxis=dict(title="Produccion (kbbl/d)"),
        yaxis2=dict(title="Pozos activos", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.12),
        margin=dict(t=50, b=40),
    )
    st.plotly_chart(fig, width="stretch")

    col_a, col_b = st.columns(2)

    with col_a:
        por_empresa = (
            aj.groupby("empresa")
            .agg(pozos=("id_pozo", "count"),
                 acum_mmbbl=("acum_petroleo_bbl", lambda s: s.sum() / 1e6))
            .reset_index()
            .sort_values("acum_mmbbl", ascending=True)
        )
        fig = px.bar(
            por_empresa, x="acum_mmbbl", y="empresa", orientation="h",
            labels={"acum_mmbbl": "Acumulado (MMbbl)", "empresa": ""},
            title="Produccion acumulada por operadora",
        )
        fig.update_layout(height=380, margin=dict(t=45, b=30))
        st.plotly_chart(fig, width="stretch")

    with col_b:
        por_area = (
            aj.groupby("area")
            .agg(pozos=("id_pozo", "count"), eur_mediano=("eur_mbbl", "median"))
            .reset_index()
            .sort_values("eur_mediano", ascending=True)
        )
        fig = px.bar(
            por_area, x="eur_mediano", y="area", orientation="h",
            labels={"eur_mediano": "EUR mediano (Mbbl)", "area": ""},
            title="Calidad de roca por bloque (EUR mediano)",
        )
        fig.update_layout(height=380, margin=dict(t=45, b=30))
        st.plotly_chart(fig, width="stretch")


# --- 5. Contexto macro -----------------------------------------------------

with tab_macro:
    st.subheader("Precio del crudo vs actividad")

    if precios.empty:
        st.info(
            "No hay serie de precios cargada. Opciones:\n\n"
            "- `python scripts/generar_demo.py` genera una serie sintetica de relleno.\n"
            "- Para datos reales, saca una API key gratuita de la EIA "
            "(https://www.eia.gov/opendata/register.php), exportala como `EIA_API_KEY` "
            "y usa `petro.ingesta.precios_crudo_eia()`."
        )
    else:
        mensual = (
            prod.groupby("fecha")
            .agg(petroleo_m3=("prod_petroleo_m3", "sum"),
                 pozos_activos=("id_pozo", "nunique"))
            .reset_index()
        )
        mensual["petroleo_kbbld"] = (
            mensual["petroleo_m3"] * BARRILES_POR_M3 / 30.4375 / 1000.0
        )
        combinado = mensual.merge(precios, on="fecha", how="inner")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=combinado["fecha"], y=combinado["precio_usd_bbl"],
            name="Precio crudo (USD/bbl)", line=dict(width=3),
        ))
        fig.add_trace(go.Scatter(
            x=combinado["fecha"], y=combinado["pozos_activos"],
            name="Pozos activos", yaxis="y2", line=dict(width=2, dash="dot"),
        ))
        fig.update_layout(
            height=400,
            yaxis=dict(title="USD/bbl"),
            yaxis2=dict(title="Pozos activos", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.12),
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, width="stretch")

        if metadatos.get("es_demo"):
            st.caption(
                "⚠️ Serie de precios sintetica: cualquier correlacion que veas aca es "
                "artificial. Con datos reales de la EIA este grafico si tiene sentido."
            )

        st.markdown("**Correlacion con rezago**")
        st.markdown(
            "La actividad de perforacion no reacciona al precio en el mismo mes: las "
            "decisiones de inversion tardan. Por eso se mira la correlacion con "
            "*rezago* (lag), corriendo la serie de precios N meses hacia atras."
        )
        filas = []
        for lag in range(0, 13):
            corr = combinado["precio_usd_bbl"].shift(lag).corr(combinado["pozos_activos"])
            filas.append({"Rezago (meses)": lag, "Correlacion": round(float(corr), 3)})
        corr_df = pd.DataFrame(filas)
        fig = px.bar(corr_df, x="Rezago (meses)", y="Correlacion")
        fig.update_layout(height=280, margin=dict(t=20, b=30))
        st.plotly_chart(fig, width="stretch")


st.divider()
st.caption(
    "Proyecto de portfolio · Lleyton Murphy · "
    "Codigo y metodologia en el README del repositorio."
)
