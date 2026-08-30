import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime
import re
import os 
import json

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.constants import TRADUCTOR_EDITOR, OTROS_CONTRIBUIDORES, ILUSTRACIONES, ESCOLARES, CATEGORIAS, COLUMNAS_FINALES, CATEGORIAS, SUBCATEGORIAS, ENCUADERNACION
from src.utils import leer_json, guardar_df

# ======================================================================================
# CREACIÓN DEL DATAFRAME BASE
# ======================================================================================

def crear_df(ruta_catalogos="data/bronze/catalogos"):

    """
    Carga todos los archivos en `ruta_catalogos` como `pd.DataFrame` y los concatena en un único DataFrame.
    Elimina filas con columnas claves repetidas y normaliza los nombres de todas las columnas.

    Parámetros:
    * `ruta_catalogos`: `str` con ruta relativa a la carpeta. Por defecto `data/bronze/catalogos`

    Output:
    * DataFrame con la información de los archivos de `ruta_catalogos` concatenada.
    """

    path = Path(ruta_catalogos)
    df = pd.DataFrame({})
    jsons = []

    print("="*50,"\nCreando DataFrame con todos los libros\n","="*50)
    for archivo in path.iterdir():
        print(f"Añadiendo {archivo.name}")
        editorial = leer_json(archivo, df=True)
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

    """ 
    Extrae valor numérico de una `str`.
    """

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

    """
    Usa `normalizar_lista` para convertir el tipo de todos los elementos de un conjunto de columnas a `list`.
    """

    df = df.copy()

    for col in columnas_listas:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_lista)

    return df


# Limpieza básica del DF (eliminar filas son datos obligatorios, duplicados, relleno de columnas nulas y mapeo)
def limpieza_basica(df,dict_editoriales=None,dict_encuadernacion=ENCUADERNACION):

    """
    Limpieza básica de un DataFrame:
    * Eliminación de duplicados en columnas identificativas ("ean")
    * Eliminación de nulos en columnas seleccionadas
    * Limpieza de fechas (formato d-m-Y)
    * Relleno de nulos simples ("sinopsis")
    * Mapeo de valores con diccionarios para nomalizar valores iniciales ("editorial" y "encuadernacion")

    Parámetros: 
    * `df`: DataFrame a limpiar
    * `dict_editoriales`: diccionario para corregir valores por defecto de "editorial"
    * `dict_encuadernacion`: diccionario para corregir valores por defecto de "encuadernacion"

    Output:
    DataFrame limpio
    """

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

    """
    Intercambia la posición de los artículos cuando aparecen tras una coma. 
    
    Por ejemplo:
    **Celestina, La -> La Celestina**
    """

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

    """ 
    
    """

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

def crear_silver_ttl(data, ruta_editoriales="data/json/editoriales.json", dict_encuadernacion=ENCUADERNACION):

    print('='*50, "\nCREACIÓN DE silver_ttl.parquet\n", "="*50)
    df = data.copy()

    print("Carga de diccionarios...\n")
    dict_editoriales = leer_json(ruta_editoriales)
    # if os.path.exists(ruta_editoriales):
    #     with open(ruta_editoriales, "r", encoding="utf-8") as f:
    #         dict_editoriales = json.load(f)
    
    TTL_A_ED = {
        nombre_ttl: editorial
        for editorial, datos in dict_editoriales.items()
        for nombre_ttl in datos["nombre_ttl"]
    }

    # Cambio de nombres de columnas
    print("--- Inicio de limpieza básica\n","[1/3] Convirtiendo tipos a `list`...")
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
    print("[2/3] Eliminación de duplicados y nulos no útiles...")
    df = limpieza_basica(df, TTL_A_ED, dict_encuadernacion)
    print("[3/3] Normalización de títulos de libros...\n")
    df['titulo'] = df['titulo'].apply(normalizar_titulos)

    # Merge colaboradores
    print("--- Inicio de Feature Engineering\n", "[1/7] Merge de columnas...")
    df = merge_columnas(df, "traductor_y_editor", TRADUCTOR_EDITOR)
    df = merge_columnas(df,"otros_contribuidores", OTROS_CONTRIBUIDORES)
    df = merge_columnas(df, "subcategorias", CATEGORIAS)

    # Feature engineering
    print("[2/7] Extracción de valores numéricos...")
    df = extraer_numeros(df)
    print("[3/7] Definiendo métricas del aparato crítico...")
    df = definir_aparato_critico(df, OTROS_CONTRIBUIDORES)
    print("[4/7] Creación de columnas marcadores...")
    df = crear_marcadores(df, ESCOLARES, ILUSTRACIONES)
    print("[5/7] Creación de urls a portadas")
    df = crear_portada(df)

    # Relleno
    print("[6/7] Imputación de valores faltantes...")
    df = rellenar_columnas(df)
    print("[7/7] Definiendo categoría principal según el SPI...\n")
    df = inferencia_categoria(df)

    # Limpieza final
    borrar = (
        TRADUCTOR_EDITOR
        + OTROS_CONTRIBUIDORES
        + ILUSTRACIONES
        + ['isbn']
    )
    print("Eliminando columnas sobrantes")
    df = limpiar_columnas(df, borrar)

    df = df[[c for c in COLUMNAS_FINALES if c in df.columns]]
    
    print("Guardando resultado...")
    guardar_df(df, "data/silver/silver_ttl.parquet", False)
    print("silver_ttl.parquet guardado.")

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

