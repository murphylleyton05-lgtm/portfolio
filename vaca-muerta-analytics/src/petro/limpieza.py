"""
Limpieza y normalizacion de los datos crudos de la Secretaria de Energia.

El objetivo de este modulo es UNO SOLO: convertir el CSV oficial (que tiene
40+ columnas con nombres cripticos) en un DataFrame con un esquema propio,
estable y en unidades utiles. Todo el resto del proyecto (analisis, dashboard)
trabaja contra ese esquema y no contra el CSV oficial.

Por que importa: si la Secretaria renombra una columna, solo se rompe este
archivo. Es la frontera entre "el mundo exterior" y "mi proyecto".

ESQUEMA NORMALIZADO (lo que devuelve `normalizar()`):
    id_pozo               identificador unico del pozo
    sigla                 nombre/sigla del pozo
    fecha                 primer dia del mes (datetime)
    empresa               operadora
    area                  area o yacimiento
    cuenca                cuenca (Neuquina, Golfo San Jorge, etc.)
    provincia             provincia
    formacion             formacion productiva (VMUT = Vaca Muerta)
    tipo_recurso          SHALE / TIGHT
    tipo_pozo             Petrolifero / Gasifero / etc.
    dias_produccion       dias efectivos de produccion en el mes (tef)
    prod_petroleo_m3      volumen mensual de petroleo, m3
    prod_gas_mm3          volumen mensual de gas, miles de m3
    prod_agua_m3          volumen mensual de agua, m3
    caudal_petroleo_m3d   caudal diario de petroleo, m3/dia   <- para el DCA
    caudal_petroleo_bbld  caudal diario de petroleo, barriles/dia
    caudal_gas_mm3d       caudal diario de gas, miles de m3/dia
"""

from __future__ import annotations

import pandas as pd

# 1 metro cubico = 6.28981 barriles de petroleo.
BARRILES_POR_M3 = 6.28981

# Mapeo: nombre en el CSV oficial -> nombre en nuestro esquema.
# Si el portal cambia un nombre de columna, se corrige ACA y nada mas.
COLUMNAS_OFICIALES = {
    "idpozo": "id_pozo",
    "sigla": "sigla",
    "empresa": "empresa",
    "areayacimiento": "area",
    "areapermisoconcesion": "area_concesion",
    "cuenca": "cuenca",
    "provincia": "provincia",
    "formprod": "formacion",
    "sub_tipo_recurso": "tipo_recurso",
    "tipo_de_recurso": "tipo_recurso_general",
    "tipopozo": "tipo_pozo",
    "tipoextraccion": "tipo_extraccion",
    "tipoestado": "estado",
    "prod_pet": "prod_petroleo_m3",
    "prod_gas": "prod_gas_mm3",
    "prod_agua": "prod_agua_m3",
    "tef": "dias_produccion",
    "anio": "anio",
    "mes": "mes",
}

# Columnas que el resto del proyecto asume que existen.
COLUMNAS_MINIMAS = [
    "id_pozo", "fecha", "empresa", "area", "cuenca", "provincia",
    "formacion", "tipo_recurso", "tipo_pozo",
    "prod_petroleo_m3", "prod_gas_mm3", "dias_produccion",
    "caudal_petroleo_m3d", "caudal_gas_mm3d",
]


# Las operadoras cambian de razon social, se fusionan y se renombran. En una
# serie de 15 años la misma empresa aparece escrita de varias formas, y sin
# unificarla los rankings la cuentan como si fueran companias distintas.
# La clave es un patron; el valor, el nombre con el que la mostramos.
NOMBRES_OPERADORAS = [
    (r"^vista", "VISTA ENERGY"),
    (r"^ypf", "YPF"),
    (r"^shell", "SHELL"),
    (r"exxon", "EXXONMOBIL"),
    (r"^chevron", "CHEVRON"),
    (r"^tecpetrol", "TECPETROL"),
    (r"pan american", "PAN AMERICAN ENERGY"),
    (r"^pluspetrol", "PLUSPETROL"),
    (r"total austral|^totalenergies", "TOTAL AUSTRAL"),
    (r"^pampa", "PAMPA ENERGIA"),
    (r"^pae\b", "PAN AMERICAN ENERGY"),
    (r"^wintershall", "WINTERSHALL"),
    (r"^capex", "CAPEX"),
    (r"^phoenix", "PHOENIX GLOBAL"),
    (r"^gas y petroleo del neuquen|^gypn", "GAS Y PETROLEO DEL NEUQUEN"),
    (r"^petronas", "PETRONAS"),
    (r"^gente de la patagonia", "GENTE DE LA PATAGONIA"),
]


def unificar_operadoras(serie: pd.Series) -> pd.Series:
    """
    Lleva las variantes de razon social de cada operadora a un nombre unico.

    "VISTA ENERGY ARGENTINA SAU", "VISTA OIL & GAS ARGENTINA SAU" y
    "Vista Oil & Gas Argentina SA" son la misma empresa en distintos momentos.
    Sin unificarlas, un ranking por operadora las cuenta como tres companias
    con un tercio de los pozos cada una.
    """
    normalizada = serie.astype("string").str.strip()
    minusculas = normalizada.str.lower()

    salida = normalizada.copy()
    for patron, nombre in NOMBRES_OPERADORAS:
        salida = salida.mask(minusculas.str.contains(patron, regex=True, na=False), nombre)
    return salida


def a_id(serie: pd.Series) -> pd.Series:
    """
    Convierte una columna de identificadores a texto, sin ".0" al final.

    Parece un detalle cosmetico y no lo es. Los id de pozo son numeros enteros,
    pero apenas una columna tiene un nulo pandas la pasa a float, y al
    convertirla a texto queda "100147.0" en vez de "100147". Despues el cruce
    con el dataset de fractura (que trae "100147") no matchea NINGUNA fila, y
    el analisis de normalizacion queda vacio SIN DAR ERROR: el peor tipo de bug.

    Por eso todos los id del proyecto pasan por esta funcion.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return serie.round().astype("Int64").astype("string")
    return (serie.astype("string").str.strip()
            .str.replace(r"\.0$", "", regex=True))


def _unificar_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Colapsa columnas con el mismo nombre en una sola.

    Para cada grupo de columnas homonimas se toma, fila por fila, el primer
    valor no nulo. Es lo correcto cuando la duplicacion viene de concatenar
    archivos donde cada uno traia la columna escrita distinto: cada fila tiene
    dato en una sola de las dos.
    """
    if not df.columns.duplicated().any():
        return df

    repetidas = sorted(set(df.columns[df.columns.duplicated()]))
    print(f"   [aviso] columnas duplicadas unificadas: {repetidas}")

    salida = {}
    for nombre in dict.fromkeys(df.columns):
        bloque = df.loc[:, df.columns == nombre]
        if bloque.shape[1] == 1:
            salida[nombre] = bloque.iloc[:, 0]
        else:
            # bfill sobre el eje de columnas deja el primer no nulo en la 1ra.
            salida[nombre] = bloque.bfill(axis=1).iloc[:, 0]

    return pd.DataFrame(salida, index=df.index)


def normalizar(df_crudo: pd.DataFrame, dias_minimos: float = 1.0,
               mostrar_columnas: bool = False) -> pd.DataFrame:
    """
    Convierte el CSV oficial al esquema normalizado.

    Pasos:
      1. Renombra columnas segun COLUMNAS_OFICIALES.
      2. Construye la columna `fecha` a partir de anio + mes.
      3. Convierte a numerico las columnas de volumen (vienen como texto a veces).
      4. Calcula CAUDALES DIARIOS dividiendo por `dias_produccion` (tef).
         Este es el paso conceptualmente mas importante del modulo: la
         declinacion se modela sobre caudal diario, no sobre volumen mensual.
         Un mes de 28 dias no significa que el pozo declino un 10%.
      5. Ordena por pozo y fecha.
    """
    df = df_crudo.copy()

    # Los CSV oficiales a veces vienen con nombres en mayusculas o con espacios.
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Al concatenar archivos de distintos años aparecen columnas que solo
    # difieren en la capitalizacion ("IDPOZO" y "idpozo"). Despues de pasar
    # todo a minusculas quedan DUPLICADAS, y entonces df["idpozo"] devuelve un
    # DataFrame en vez de una Serie y todo lo que sigue explota.
    # Las unificamos quedandonos, para cada fila, con el primer valor no nulo.
    df = _unificar_duplicadas(df)

    presentes = {k: v for k, v in COLUMNAS_OFICIALES.items() if k in df.columns}
    df = df.rename(columns=presentes)

    # El renombrado tambien puede generar duplicados: si el CSV trae la columna
    # `formprod` Y una `formacion`, ambas terminan llamandose `formacion`.
    # Con un solo archivo de entrada este fue el caso real que rompio el
    # pipeline, asi que unificamos de nuevo despues de renombrar.
    df = _unificar_duplicadas(df)

    if mostrar_columnas:
        print(f"   columnas del archivo ({len(df.columns)}): "
              f"{', '.join(sorted(df.columns))}")

    faltantes = {"id_pozo", "prod_petroleo_m3"} - set(df.columns)
    if faltantes:
        raise ValueError(
            f"El CSV no trae las columnas esperadas: {faltantes}. "
            f"Columnas encontradas: {sorted(df.columns)[:25]}... "
            "Revisa COLUMNAS_OFICIALES en limpieza.py: el portal pudo renombrarlas."
        )

    # --- fecha ---
    if "anio" in df.columns and "mes" in df.columns:
        df["fecha"] = pd.to_datetime(
            dict(
                year=pd.to_numeric(df["anio"], errors="coerce"),
                month=pd.to_numeric(df["mes"], errors="coerce"),
                day=1,
            ),
            errors="coerce",
        )
    elif "fecha_data" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha_data"], errors="coerce")
    else:
        raise ValueError("No pude construir la columna `fecha` (faltan anio/mes).")

    # --- numericos ---
    for col in ["prod_petroleo_m3", "prod_gas_mm3", "prod_agua_m3", "dias_produccion"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = pd.NA

    # --- caudales diarios ---
    # Solo dividimos donde dias_produccion es razonable. Si el pozo produjo 0
    # dias, el caudal no esta definido (no es cero: es "no produjo").
    dias = df["dias_produccion"]
    dias_validos = dias.notna() & (dias >= dias_minimos)

    df["caudal_petroleo_m3d"] = pd.NA
    df["caudal_gas_mm3d"] = pd.NA
    df.loc[dias_validos, "caudal_petroleo_m3d"] = (
        df.loc[dias_validos, "prod_petroleo_m3"] / dias[dias_validos]
    )
    df.loc[dias_validos, "caudal_gas_mm3d"] = (
        df.loc[dias_validos, "prod_gas_mm3"] / dias[dias_validos]
    )

    df["caudal_petroleo_m3d"] = pd.to_numeric(df["caudal_petroleo_m3d"], errors="coerce")
    df["caudal_gas_mm3d"] = pd.to_numeric(df["caudal_gas_mm3d"], errors="coerce")
    df["caudal_petroleo_bbld"] = df["caudal_petroleo_m3d"] * BARRILES_POR_M3

    # --- texto prolijo ---
    for col in ["empresa", "area", "cuenca", "provincia", "formacion",
                "tipo_recurso", "tipo_pozo"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
        else:
            df[col] = pd.NA

    df["id_pozo"] = a_id(df["id_pozo"])
    df["empresa"] = unificar_operadoras(df["empresa"])

    df = df.dropna(subset=["fecha"]).sort_values(["id_pozo", "fecha"])
    return df.reset_index(drop=True)


def filtrar_vaca_muerta(df: pd.DataFrame) -> pd.DataFrame:
    """
    Se queda solo con pozos de Vaca Muerta.

    En el dataset oficial la formacion productiva de Vaca Muerta aparece con la
    sigla `VMUT` (a veces escrita distinto), asi que filtramos por texto que
    contenga "vmut" o "vaca muerta", sin distinguir mayusculas.
    """
    formacion = df["formacion"].fillna("").str.lower()
    es_vm = formacion.str.contains("vmut") | formacion.str.contains("vaca muerta")
    return df[es_vm].copy()


def pozos_con_historia_suficiente(
    df: pd.DataFrame,
    meses_minimos: int = 12,
    caudal_minimo: float = 1.0,
) -> pd.DataFrame:
    """
    Descarta pozos con pocos meses de produccion util.

    Ajustar una curva de declinacion con 3 puntos da un numero, pero no da
    informacion: el ajuste es basura. Filtrar temprano evita llenar el
    dashboard de resultados sin sentido.
    """
    utiles = df[df["caudal_petroleo_m3d"] > caudal_minimo]
    conteo = utiles.groupby("id_pozo")["fecha"].count()
    validos = conteo[conteo >= meses_minimos].index
    return df[df["id_pozo"].isin(validos)].copy()


def resumen_por_pozo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Una fila por pozo con sus atributos y su produccion acumulada historica.
    Es la tabla que se cruza con los resultados del ajuste de declinacion.
    """
    agrupado = df.groupby("id_pozo").agg(
        sigla=("sigla", "first") if "sigla" in df.columns else ("id_pozo", "first"),
        empresa=("empresa", "first"),
        area=("area", "first"),
        cuenca=("cuenca", "first"),
        provincia=("provincia", "first"),
        formacion=("formacion", "first"),
        tipo_recurso=("tipo_recurso", "first"),
        tipo_pozo=("tipo_pozo", "first"),
        primer_mes=("fecha", "min"),
        ultimo_mes=("fecha", "max"),
        meses_produccion=("fecha", "count"),
        acum_petroleo_m3=("prod_petroleo_m3", "sum"),
        acum_gas_mm3=("prod_gas_mm3", "sum"),
        pico_petroleo_m3d=("caudal_petroleo_m3d", "max"),
    )
    agrupado["acum_petroleo_bbl"] = agrupado["acum_petroleo_m3"] * BARRILES_POR_M3
    return agrupado.reset_index()
