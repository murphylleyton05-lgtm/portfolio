"""
Pipeline principal: crudo -> procesado.

Lee todos los CSV de data/crudo/, los normaliza, filtra Vaca Muerta, ajusta la
curva de declinacion de cada pozo y deja todo listo en data/procesado/ para
que el dashboard solo tenga que leer archivos (rapido) y no recalcular nada.

Uso:
    python scripts/preparar_datos.py
    python scripts/preparar_datos.py --sin-filtro-vm     # todos los pozos, no solo VM
    python scripts/preparar_datos.py --meses-minimos 12

Salidas en data/procesado/:
    produccion.parquet          serie mensual normalizada, pozo por pozo
    pozos.parquet               una fila por pozo (atributos + acumulados)
    ajustes_declinacion.parquet una fila por pozo (qi, Di, b, R2, EUR)
    precios_crudo.parquet       serie de precio del crudo
    metadatos.json              cuando se corrio, cuantas filas, si es demo
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from petro import (config, declinacion, fractura as mod_fractura,  # noqa: E402
                   limpieza, validacion)


def cargar_crudo(patron: str = "*no_convencional*.csv") -> tuple[pd.DataFrame, bool]:
    """
    Lee y concatena todos los CSV de produccion que haya en data/crudo/.

    Devuelve (dataframe, es_demo). `es_demo` es True si los unicos archivos
    encontrados son los sinteticos: lo propagamos hasta el dashboard para que
    muestre el cartel de "datos de demostracion" y nadie confunda las cosas.
    """
    archivos = sorted(config.DIR_CRUDO.glob(patron))
    if not archivos:
        raise SystemExit(
            f"No hay archivos en {config.DIR_CRUDO} que matcheen {patron!r}.\n"
            "Corre primero uno de estos:\n"
            "    python scripts/descargar_datos.py    (datos reales)\n"
            "    python scripts/generar_demo.py       (datos sinteticos)"
        )

    es_demo = all(a.name.startswith("DEMO__") for a in archivos)

    partes = []
    for archivo in archivos:
        print(f"  leyendo {archivo.name} ...", end=" ", flush=True)
        df = pd.read_csv(archivo, low_memory=False)
        print(f"{len(df):,} filas")
        partes.append(df)

    return pd.concat(partes, ignore_index=True), es_demo


def cargar_fractura() -> pd.DataFrame:
    """
    Lee los CSV de fractura si estan. Devuelve vacio si no hay ninguno.

    No es obligatorio: sin fractura el proyecto funciona igual, solo que los
    rankings quedan sin normalizar por longitud de rama. Por eso esto degrada
    en vez de fallar.
    """
    archivos = sorted(config.DIR_CRUDO.glob("*fractura*.csv"))
    if not archivos:
        return pd.DataFrame()

    partes = []
    for archivo in archivos:
        print(f"  leyendo {archivo.name} ...", end=" ", flush=True)
        df = pd.read_csv(archivo, low_memory=False)
        print(f"{len(df):,} filas")
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def cargar_precios() -> pd.DataFrame:
    """Lee la serie de precios si existe; si no, devuelve un DataFrame vacio."""
    archivos = sorted(config.DIR_CRUDO.glob("*precios*.csv"))
    if not archivos:
        return pd.DataFrame(columns=["fecha", "precio_usd_bbl"])
    df = pd.read_csv(archivos[0])
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara los datos para el dashboard.")
    parser.add_argument("--sin-filtro-vm", action="store_true",
                        help="no filtrar por formacion Vaca Muerta")
    parser.add_argument("--meses-minimos", type=int, default=config.MESES_MINIMOS_AJUSTE,
                        help="meses minimos de produccion para ajustar un pozo")
    args = parser.parse_args()

    config.asegurar_carpetas()

    # --- 1. Cargar ---
    print("1) Cargando datos crudos")
    crudo, es_demo = cargar_crudo()
    if es_demo:
        print("   [!] Solo se encontraron datos DEMO (sinteticos).")

    # --- 2. Normalizar ---
    print("\n2) Normalizando esquema y calculando caudales diarios")
    df = limpieza.normalizar(crudo, mostrar_columnas=True)
    print(f"   {len(df):,} filas pozo-mes | {df['id_pozo'].nunique():,} pozos")
    print(f"   periodo: {df['fecha'].min():%Y-%m} a {df['fecha'].max():%Y-%m}")

    # --- 3. Filtrar ---
    if not args.sin_filtro_vm:
        print("\n3) Filtrando pozos de Vaca Muerta")
        df_vm = limpieza.filtrar_vaca_muerta(df)
        if df_vm.empty:
            print("   [!] Ningun pozo de Vaca Muerta. Sigo con todos los pozos.")
        else:
            df = df_vm
        print(f"   {df['id_pozo'].nunique():,} pozos")
    else:
        print("\n3) (filtro de Vaca Muerta desactivado)")

    print(f"\n4) Descartando pozos con menos de {args.meses_minimos} meses utiles")
    df = limpieza.pozos_con_historia_suficiente(df, meses_minimos=args.meses_minimos)
    print(f"   {df['id_pozo'].nunique():,} pozos quedan para analizar")

    if df.empty:
        raise SystemExit("No quedaron pozos despues de filtrar. Baja --meses-minimos.")

    # --- 5. Resumen por pozo ---
    print("\n5) Resumiendo atributos y acumulados por pozo")
    pozos = limpieza.resumen_por_pozo(df)

    # --- 6. Ajuste de declinacion ---
    print(f"\n6) Ajustando curvas de declinacion ({df['id_pozo'].nunique():,} pozos)")
    print("   (esto es lo que mas tarda: son un curve_fit por pozo)")
    ajustes = declinacion.ajustar_muchos_pozos(
        df,
        col_id="id_pozo",
        col_caudal="caudal_petroleo_m3d",
        col_fecha="fecha",
        mostrar_progreso=True,
        meses_minimos=args.meses_minimos,
        horizonte_meses=config.HORIZONTE_EUR_MESES,
        d_terminal_anual=config.D_TERMINAL_ANUAL,
    )

    if ajustes.empty:
        raise SystemExit("Ningun pozo pudo ajustarse. Revisa los datos de entrada.")

    # Pegamos los atributos del pozo (empresa, area, etc.) a los resultados,
    # para que el dashboard pueda filtrar y agrupar sin hacer joins.
    ajustes = ajustes.merge(pozos, on="id_pozo", how="left")
    ajustes["ajuste_confiable"] = ajustes["r2"] >= config.R2_MINIMO_CONFIABLE

    # --- 6b. Normalizacion por longitud de rama lateral ---
    print("\n6b) Cruzando con datos de fractura (longitud de rama, etapas)")
    crudo_fractura = cargar_fractura()
    diagnostico_rama = {}

    if crudo_fractura.empty:
        print("   (no hay archivos de fractura: los rankings quedan sin normalizar)")
        ajustes["rama_m"] = pd.NA
        ajustes["eur_por_metro"] = pd.NA
        ajustes["eur_por_etapa"] = pd.NA
        ajustes["tiene_fractura"] = False
    else:
        try:
            frac = mod_fractura.normalizar(crudo_fractura)
            print(f"   {len(frac):,} pozos con datos de completacion")
            ajustes = mod_fractura.unir_con_ajustes(ajustes, frac)
            con_datos = int(ajustes["tiene_fractura"].sum())
            print(f"   {con_datos:,} de {len(ajustes):,} pozos ajustados "
                  f"tienen rama declarada ({con_datos / len(ajustes):.0%})")

            # OJO: el diagnostico se calcula SOLO sobre ajustes confiables.
            # Incluir los que fallaron mete EUR de millones de barriles que no
            # son reales, y ensucia la correlacion que estamos midiendo.
            solo_buenos = ajustes[
                (ajustes["r2"] >= config.R2_MINIMO_CONFIABLE)
                & ajustes["convergio"]
                & (ajustes["b"] < 1.98)
            ]
            print(f"   diagnostico sobre {len(solo_buenos):,} ajustes confiables "
                  f"(de {len(ajustes):,})")
            diagnostico_rama = mod_fractura.cuanto_explica_la_rama(solo_buenos)
            if diagnostico_rama.get("suficientes_datos"):
                d = diagnostico_rama
                print(f"   rama mediana: {d['rama_mediana_m']:,} m")
                print(f"   correlacion rama-EUR: {d['correlacion_rama_eur']:.3f} "
                      f"-> la longitud explica el {d['varianza_explicada']:.0%} "
                      f"de la diferencia de EUR entre pozos")
                print(f"   al normalizar, el ranking se mueve "
                      f"{d['cambio_de_puesto_mediano']} puestos (mediana), "
                      f"hasta {d['cambio_de_puesto_maximo']}")
                print(f"   del top 10 crudo sobreviven "
                      f"{d['top10_que_sobrevive']} pozos al normalizar")
        except ValueError as e:
            # El esquema de fractura no matcheo. No tiramos todo el pipeline
            # por eso: seguimos sin normalizar y avisamos fuerte.
            print(f"   [!] no pude usar los datos de fractura: {e}")
            ajustes["rama_m"] = pd.NA
            ajustes["eur_por_metro"] = pd.NA
            ajustes["eur_por_etapa"] = pd.NA
            ajustes["tiene_fractura"] = False

    confiables = int(ajustes["ajuste_confiable"].sum())
    print(f"   {len(ajustes):,} pozos ajustados | "
          f"{confiables:,} con R2 >= {config.R2_MINIMO_CONFIABLE}")
    print(f"   R2 mediano: {ajustes['r2'].median():.3f}")
    print(f"   b mediano:  {ajustes['b'].median():.2f}")
    print(f"   EUR mediano: {ajustes['eur'].median():,.0f} m3 "
          f"({ajustes['eur'].median() * limpieza.BARRILES_POR_M3 / 1000:,.0f} Mbbl)")

    # --- 6c. Backtest: validar el modelo contra datos que no vio ---
    print("\n6c) Backtest: ajustando con los primeros "
          f"{validacion.MESES_ENTRENAMIENTO} meses y prediciendo el resto")
    print("   (es la validacion del EUR: el pozo ya produjo, el modelo no lo vio)")

    backtest = validacion.backtest_muchos(
        df,
        col_id="id_pozo",
        col_caudal="caudal_petroleo_m3d",
        col_fecha="fecha",
        mostrar_progreso=True,
    )
    resumen_backtest = validacion.resumen(backtest)

    if resumen_backtest.get("suficientes_datos"):
        print(f"   {resumen_backtest['pozos_totales']:,} pozos con historia "
              "suficiente para validar")
        for h in validacion.HORIZONTES:
            d = resumen_backtest.get(f"h{h}")
            if d:
                print(f"   a {h:>2} meses: error absoluto mediano "
                      f"{d['error_absoluto']:>5.1f}%  |  sesgo {d['error_mediano']:+6.1f}%  "
                      f"|  {d['dentro_20']:.0f}% dentro de +/-20%  ({d['pozos']:,} pozos)")
        print(f"\n   >> {validacion.frase_del_resultado(resumen_backtest)}")
    else:
        print("   (no hay pozos con historia suficiente para validar)")

    # --- 7. Guardar ---
    print("\n7) Guardando en data/procesado/")
    df.to_parquet(config.PRODUCCION, index=False)
    pozos.to_parquet(config.POZOS, index=False)
    ajustes.to_parquet(config.AJUSTES, index=False)
    if not backtest.empty:
        backtest.to_parquet(config.DIR_PROCESADO / "backtest.parquet", index=False)

    precios = cargar_precios()
    if not precios.empty:
        precios.to_parquet(config.PRECIOS, index=False)

    metadatos = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "es_demo": es_demo,
        "filas_produccion": int(len(df)),
        "pozos": int(df["id_pozo"].nunique()),
        "pozos_ajustados": int(len(ajustes)),
        "pozos_ajuste_confiable": confiables,
        "primer_mes": df["fecha"].min().strftime("%Y-%m"),
        "ultimo_mes": df["fecha"].max().strftime("%Y-%m"),
        "meses_minimos_ajuste": args.meses_minimos,
        "horizonte_eur_meses": config.HORIZONTE_EUR_MESES,
        "d_terminal_anual": config.D_TERMINAL_ANUAL,
        "normalizacion_rama": diagnostico_rama,
        "backtest": resumen_backtest,
    }
    config.METADATOS.write_text(json.dumps(metadatos, indent=2, ensure_ascii=False))

    for archivo in (config.PRODUCCION, config.POZOS, config.AJUSTES, config.METADATOS):
        if archivo.exists():
            print(f"   {archivo.name}  ({archivo.stat().st_size / 1_000_000:.1f} MB)")

    print("\nListo. Levanta el dashboard con:  streamlit run app/dashboard.py")


if __name__ == "__main__":
    main()
