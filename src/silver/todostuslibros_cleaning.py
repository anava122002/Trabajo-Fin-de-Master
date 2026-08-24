import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
import os 
import json
from src.constants import TRADUCTOR_EDITOR, OTROS_CONTRIBUIDORES, ILUSTRACIONES, ESCOLARES, CATEGORIAS, COLUMNAS_FINALES, CATEGORIAS, SUBCATEGORIAS, ENCUADERNACION, CATEGORIAS_SPI

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
        valor = valor.strip().title()
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

            x = str(x).strip().title()

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
def limpieza_basica(df,dict_editoriales=None,dict_encuadernacion=ENCUADERNACION):

    # quitar duplicados por EAN
    df.drop_duplicates(subset="ean", inplace=True)

    # eliminar libros sin autor y sin categoría
    df = df.dropna(
        subset=["ean", "titulo", "autoria", "categorias"],
        how="any",
    )
    df['ean'] = df['ean'].astype(str)

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
        df["editorial"] = df["editorial"].map(dict_editoriales)

    # encuadernación
    if dict_encuadernacion is not None:
        df["encuadernacion"] = df["encuadernacion"].map(dict_encuadernacion)

    return df

def normalizar_titulos(nombre:str):
    articulos = {"El", "La", "Los", "Las", "Un", "Una", "Unos", "Unas"}

    if "," in nombre:
        titulo, articulo = map(str.strip, nombre.rsplit(",", 1))
        if articulo in articulos:
            nombre = f"{articulo} {titulo}"

    nombre = nombre.strip().title()

    return nombre 

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

def crear_marcadores(df, ilustraciones, escolares):
    # Escolares
    escolar = (
        df[escolares]
        .apply(lambda col: col.str.len())
        .sum(axis=1)
        > 0
    )
    df['es_escolar'] = escolar 

    # Ilustrada
    ilustrada = (
        df[ilustraciones]
        .apply(lambda col: col.str.len())
        .sum(axis=1)
        > 0
    )
    df['es_ilustrada'] = ilustrada

    # Impresión bajo demanda
    ibd = (
        df["ibd"]
        .str.len()
        > 0
    )
    df['es_ibd'] = ibd

    return df


def crear_portada(df:pd.DataFrame):
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


def definir_aparato_critico(df, cols_ap):

    def tiene_contenido(valor):
        if valor is None:
            return False
        if isinstance(valor, float) and pd.isna(valor):
            return False
        if isinstance(valor, (list, np.ndarray)) and len(valor) == 0:
            return False
        return True

    # Creamos la máscara booleana
    mask = df[cols_ap].map(tiene_contenido).any(axis=1)
    df["aparato_critico"] = mask

    # Generamos los valores directamente en el apply sin necesidad de .loc
    def extraer_tipos(fila):
        presentes = [col for col in cols_ap if tiene_contenido(fila[col])]
        return presentes if presentes else np.nan

    df["tipo_aparato_critico"] = df[cols_ap].apply(extraer_tipos, axis=1)

    return df

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
    peso_estimado = df['peso'].fillna((df["alto_mm"]/1000) * (df["ancho_mm"]/1000) * (df["n_paginas"]/2) * 80 + 120)

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


# inferencia categorías
def inferencia_categoria(df, categorias=SUBCATEGORIAS):

    def obtener_categorias(subcategorias_libro):
        if not isinstance(subcategorias_libro, (list, tuple, set)):
            return []

        return list({
            categoria
            for subcategoria in subcategorias_libro
            for categoria, subcategorias in categorias.items()
            if subcategoria in subcategorias
        })

    df["categorias"] = df["subcategorias"].apply(obtener_categorias)

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

def limpiar_df_completa(data, ruta_editoriales="data/json/editoriales.json", dict_encuadernacion=ENCUADERNACION):

    df = data.copy()
    if os.path.exists(ruta_editoriales):
        with open(ruta_editoriales, "r", encoding="utf-8") as f:
            dict_editoriales = json.load(f)

    TTL_A_ED = {
        nombre_ttl: editorial
        for editorial, datos in dict_editoriales.items()
        for nombre_ttl in datos["nombre_ttl"]
    }

    # Cambio de nombres de columnas
    columnas_lista = list(set(
        TRADUCTOR_EDITOR
        + OTROS_CONTRIBUIDORES
        + ILUSTRACIONES
        + ESCOLARES
        + CATEGORIAS
        + ["autoria"]
    ))
    df = normalizar_columnas_lista(df, columnas_lista)

    # Limpieza
    df = limpieza_basica(df, TTL_A_ED, dict_encuadernacion)
    df['titulo'] = df['titulo'].apply(normalizar_titulos)

    # Merge colaboradores
    df = merge_columnas(df, "traductor_y_editor", TRADUCTOR_EDITOR)
    df = merge_columnas(df,"otros_contribuidores", OTROS_CONTRIBUIDORES)
    df = merge_columnas(df, "subcategorias", CATEGORIAS)

    # Feature engineering
    df = extraer_numeros(df)
    df = definir_aparato_critico(df, OTROS_CONTRIBUIDORES)
    df = crear_marcadores(df, ESCOLARES, ILUSTRACIONES)
    df = crear_portada(df)

    # Relleno
    df = rellenar_columnas(df)
    df = inferencia_categoria(df)

    # Limpieza final
    borrar = (
        TRADUCTOR_EDITOR
        + OTROS_CONTRIBUIDORES
        + ILUSTRACIONES
        + ['isbn']
    )
    df = limpiar_columnas(df, borrar)

    df = df[[c for c in COLUMNAS_FINALES if c in df.columns]]

    return df


def validar_catalogo(df):
    # EAN únicos
    if df['ean'].nunique().count() < len(df['ean']):
        print('Existen números EAN repetidos.') 
    
    # sin nulos en columnas obligatorial
    cols_nulos = ["ean", "titulo", "autoria", "categorias"]
    for col in cols_nulos:
        if df[col].isna().sum() > 0:
            print(f'Existen nulos en la columna {col}.') 

    # fechas válidas
    formato = '%d/%m/%Y'
    for fecha in df['fecha_publicacion']:
        try:
            fecha_valida = datetime.strptime(fecha, formato)
            print("Fecha correcta")
        except ValueError:
            print("Fecha inválida")

    # dimensiones positivas
    cols_numericas = ["n_paginas","precio","alto_mm","ancho_mm","grueso","peso"]
    for col in cols_numericas:
        if any(x<=0 for x in df[col]):
            print(f"La columna {col} tiene núemeros no positivos.")
