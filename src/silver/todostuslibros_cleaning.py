# ======================================================================================
# MERGE Y LIMPIEZA DE CATÁLOGOS
# ======================================================================================
import pandas as pd
import numpy as np
import pathlib as Path
import json
import re

# ======================================================================================
# CREACIÓN DEL DATAFRAME BASE
# ======================================================================================

def crear_df(ruta_catalogos="data/bronze/catalogos"):
    path = Path(ruta_catalogos)
    df = pd.DataFrame({})
    jsons = []

    print("="*50,"\nCreando DataFrame con todos los libros\n","="*50)
    for archivo in path.iterdir():
        if archivo.is_file():
            print(f"Añadiendo {archivo.name}")
            editorial = pd.read_json(archivo.absolute())
            jsons.append(editorial)

    df = pd.concat(jsons, axis=0)

    # Borrar filas repetidas
    print("Catálogos convertidos a DataFrame. Eliminando filas duplicadas...")
    df.drop_duplicates(subset=['EAN'], keep='first', inplace=True)

    # Limpiado de nombre de columnas
    df.columns = df.columns.str.strip().str.lower().str.translate(str.maketrans({"á": "a", "é": "e", "í": "i", "ó":"o", "ú": "u", "º": "", " ": "_"}))

    print("DataFrame creado con éxito.")
    return df


# =============================================================================
# FUNCIONES AUXILIARES Y LIMPIEZA BÁSICA
# =============================================================================

# Búsqueda de la moda en una lista de strings
def moda(x):
    """
    Devuelve la moda de una serie.
    """

    x = x.dropna()

    if len(x) == 0:
        return np.nan

    return x.mode().iloc[0]

# Busca los nombres más repetidos en una serie de listas/columnas
def contador_nombres(df, min_apariciones=5):

    df = df.copy()

    todos = pd.concat([
        df["traductor_y_editor"].explode(),
        df["otros_contribuidores"].explode()
    ]).dropna()

    frecuencia = todos.value_counts()

    destacados = frecuencia[frecuencia >= min_apariciones].to_dict()

    def calcular_score(personas):
        return sum(
            destacados.get(p, 0)
            for p in personas
        )

    def colaboradores_destacados(personas):
        return [
            p
            for p in personas
            if p in destacados
        ]

    colaboradores = df["traductor_y_editor"]+ df["otros_contribuidores"]

    df["score_colaboradores"] = colaboradores.apply(calcular_score)

    df["colaboradores_destacados"] = colaboradores.apply(colaboradores_destacados)

    return df

# Extrae el número (precio, medida...) de un string
def extraer_numero(x):

    _NUMERO = re.compile(r"(\d+[.,]?\d*)")

    if pd.isna(x):
        return np.nan

    m = _NUMERO.search(str(x))

    if m is None:
        return np.nan

    return float(m.group(1).replace(",", "."))


# Conversión de los elementos de una lista/columna en listas
def normalizar_lista(valor):
    """
    Convierte cualquier valor en una lista.

    NaN -> []
    str -> [str]
    list -> list limpia
    ndarray -> list
    """

    if valor is None:
        return []

    if isinstance(valor, float) and np.isnan(valor):
        return []

    if isinstance(valor, str):
        valor = valor.strip().capitalize()
        if valor == "":
            return []

        return [valor]

    if isinstance(valor, np.ndarray):
        valor = valor.tolist()

    if isinstance(valor, (list, tuple)):
        salida = []
        for x in valor:
            if pd.isna(x):
                continue

            x = str(x).strip().capitalize()

            if x:
                salida.append(x)

        return list(dict.fromkeys(salida))

    return [str(valor)]


def normalizar_columnas_lista(df, columnas_listas):

    df = df.copy()

    for col in columnas_listas:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_lista)

    return df


# Limpieza básica del DF (eliminar filas son datos obligatorios, duplicados, relleno de columnas nulas y mapeo)
def limpieza_basica(df,dict_editoriales=None,dict_encuadernacion=None,):

    df = df.copy()

    # quitar duplicados por EAN
    df.drop_duplicates(subset="ean", inplace=True)

    # eliminar libros sin autor y sin categoría
    df = df.dropna(
        subset=["autoria", "categorias"],
        how="all",
    )

    # fecha
    df["fecha_publicacion"] = pd.to_datetime(
        df["fecha_publicacion"],
        format="%d-%m-%Y",
        errors="coerce",
    )

    # sinopsis
    df["sinopsis"] = df["sinopsis"].fillna("Sin sinopsis")

    # ids editoriales
    if dict_editoriales is not None:
        df["id_editorial"] = df["editorial"].map(dict_editoriales)

    # encuadernación
    if dict_encuadernacion is not None:
        df["encuadernacion"] = df["encuadernacion"].map(dict_encuadernacion)

    return df


# =============================================================================
# MERGE DE COLUMNAS Y FEATURES
# =============================================================================

# Unión de columnas para crear otra nueva
def merge_columnas(df, nombre, columnas):

    df = df.copy()

    for col in columnas:
        if col not in df.columns:
            df[col] = [[] for _ in range(len(df))]

    df[nombre] = df[columnas].sum(axis=1).apply(lambda x: list(dict.fromkeys(x)))

    return df

# Coversión de columnas numéricas que aparecen como str
def extraer_numeros(df):

    df = df.copy()

    for col in ["precio","peso","grueso","n_paginas"]:
        if col in df.columns:
            df[col] = df[col].apply(extraer_numero)

    # dimensiones (ej: 240 x 170 mm)
    medidas = df["dimensiones"].astype(str).str.extract(r"(\d+[.,]?\d*)\D+(\d+[.,]?\d*)")

    df["alto_mm"] = medidas[0].str.replace(",", ".", regex=False).astype(float)
    df["ancho_mm"] = medidas[1].str.replace(",", ".", regex=False).astype(float)

    return df

# Deetermina a qué grupo pertenece cada libro y crea columna con su portada
def crear_columnas(df, ilustraciones, escolares):

    df = df.copy()

    # Flags
    df["es_ilustrado"] = (
        df[ilustraciones]
        .apply(lambda col: col.str.len())
        .sum(axis=1)
        > 0
    )

    escolar = (
        df[escolares]
        .apply(lambda col: col.str.len())
        .sum(axis=1)
        > 0
    )

    comentada = (
        df["otros_contribuidores"]
        .str.len()
        > 0
    )

    adaptada = (
        df["adaptacion"]
        .str.len()
        > 0
    )

    ibd = (
        df["ibd"]
        .str.len()
        > 0
    )


    # Tipo edición
    df["tipo_edicion"] = 'Edición normal'

    df.loc[escolar, "tipo_edicion"] = "escolar"
    df.loc[comentada & ~escolar,"tipo_edicion"] = "comentada"
    df.loc[titulo.str.contains(r"\banotad\b",regex=True,na=False) & ~escolar,"presentacion"] = "comentada"
    df.loc[adaptada,"tipo_edicion"] = "adaptada"
    df.loc[ibd,"tipo_edicion"] = "ibd"

    # Presentación
    titulo = df["titulo"].fillna("").str.lower()

    df["presentacion"] = "tomo único"
    df.loc[titulo.str.contains(r"\bestuche\b",regex=True,na=False),"presentacion"] = "estuche"
    df.loc[titulo.str.contains(r"obras?\s+completas?",regex=True,na=False),"presentacion"] = "obras completas"
    df.loc[titulo.str.contains(r"\bpack\b",regex=True,na=False),"presentacion"] = "pack"
    df.loc[titulo.str.contains(r"\bvol?\s\b",regex=True,na=False),"presentacion"] = "colección"
    df.loc[titulo.str.contains(r"\btomo?\s\b",regex=True,na=False),"presentacion"] = "colección"

    # URL imagen
    ean = df["ean"].astype(str)
    df["img"] = (
        "https://static.cegal.es/imagenes/marcadas/"
        + ean.str[:8]
        + "/"
        + ean
        + ".gif"
    )

    return df

# Reunir tipo de aparato crítico
def definir_aparato_critico(df, cols_ap):
    mask = df[cols_ap].notna().any(axis=1)

    df["aparato_critico"] = mask

    df["tipo_aparato_critico"] = df[cols_ap].apply(lambda fila: [col for col in cols_ap if pd.notna(fila[col])],axis=1)

    df.loc[~mask, "tipo_aparato_critico"] = np.nan

    return df

# Imputación de columnas en base a otras
def rellenar_columnas(df):

    df = df.copy()

    # Medidas por editorial + colección
    for col in ["alto_mm", "ancho_mm", "precio", "n_paginas"]:
        mediana_col = df.groupby(["editorial", "coleccion"])[col].transform("median")
        mediana_enc = df.groupby(["editorial", "encuadernacion"])[col].transform("median")
        
        df[col] = df[col].fillna(mediana_col).fillna(mediana_enc)


    # Grosor (fórmula estándar)
    df["grueso"] = df["grueso"].fillna(df["n_paginas"] * 0.04)

    # Peso (fórmula estándar)
    peso_estimado = df['peso'].fillna(df["alto_mm"] * df["ancho_mm"] * df["n_paginas"] * 0.08 + 120)

    df["peso"] = df["peso"].fillna(peso_estimado)

    # Idioma original 
    df["autor_principal"] = (
        df["autoria"]
        .apply(
            lambda x:
                x[0]
                if len(x)
                else np.nan
        )
    )

    idioma = (
        df.groupby("autor_principal")[
            "idioma_original"
        ]
        .transform(moda)
    )

    df["idioma_original"] = df["idioma_original"].fillna(idioma)

    df.drop(columns="autor_principal", inplace=True)

    return df


# =============================================================================
# LIMPIEZA FINAL
# =============================================================================

def limpiar_columnas(df, cols_borrar):

    borrar = [c for c in cols_borrar if c in df.columns]

    return df.drop(columns=borrar)

# =============================================================================
# PIPELINE
# =============================================================================

def limpiar_df_completa(data, dict_editoriales=None, dict_encuadernacion=None):

    TRADUCTOR_EDITOR = [
        "traduccion",
        "edicion_literaria",
        "edicion",
        "direccion_de_edicion",
        "edicion_y_traduccion",
    ]

    OTROS_CONTRIBUIDORES = [
        "epilogo",
        "prologo",
        "trabajo_preliminar",
        "contribucion",
        "introduccion",
        "comentarios_a_la_traduccion",
        "introduccion_a_notas",
        "prefacio",
        "notas",
        "compilacion",
    ]

    ILUSTRACIONES = [
        "ilustracion",
        "ilustracion_fotografica",
        "fotografia",
    ]

    ESCOLARES = [
        "material_enseñanza",
        "tipo_material_enseñanza",
        "tipo_enseñanza",
        "asignatura",
        "ciclo",
    ]

    CATEGORIAS = [
        "categorias",
        "pais_de_publicacion",
        "asignatura",
        "tipo_material_enseñanza",
        "ciclo",
    ]

    COLUMNAS_LISTA = list(set(
        TRADUCTOR_EDITOR
        + OTROS_CONTRIBUIDORES
        + ILUSTRACIONES
        + ESCOLARES
        + CATEGORIAS
        + ["autoria"]
    ))

    COLUMNAS_FINALES = [
        "isbn",
        "ean",
        "titulo",
        "editorial",
        "id_editorial",
        "coleccion",
        "autoria",
        "traductor_y_editor",
        "otros_contribuidores",
        "subcategorias",
        "idioma_original",
        "idioma_de_publicacion",
        "fecha_publicacion",
        "n_paginas",
        "precio",
        "alto_mm",
        "ancho_mm",
        "grueso",
        "peso",
        "encuadernacion",
        "tipo_edicion",
        "presentacion",
        "es_ilustrado",
        "score_colaboradores",
        "colaboradores_destacados",
        "sinopsis",
        "url",
        "img",
    ]

    borrar = (
            TRADUCTOR_EDITOR
            + OTROS_CONTRIBUIDORES
            + ILUSTRACIONES
        )

    df = data.copy()

    # Normalización
    df = normalizar_columnas_lista(df, COLUMNAS_LISTA)

    # Limpieza
    df = limpieza_basica(df, dict_editoriales, dict_encuadernacion)

    # Merge colaboradores
    df = merge_columnas(df, "traductor_y_editor", TRADUCTOR_EDITOR)
    df = merge_columnas(df,"otros_contribuidores", OTROS_CONTRIBUIDORES)
    df = merge_columnas(df, "subcategorias", CATEGORIAS)

    # Feature engineering
    df = contador_nombres(df)
    df = extraer_numeros(df)
    df = crear_columnas(df, ILUSTRACIONES, ESCOLARES)
    df = definir_aparato_critico(df, OTROS_CONTRIBUIDORES)

    # Relleno
    df = rellenar_columnas(df)

    # Limpieza final
    df = limpiar_columnas(df, borrar)

    df = df[[c for c in COLUMNAS_FINALES if c in df.columns]]

    df.to_parquet("data/silver/catalogo.parquet", engine="pyarrow")

    return df

