import pandas as pd
import numpy as np
import ast
from sklearn.preprocessing import MinMaxScaler
from src.constants import SUBCATEGORIAS

def merge_dataframes(ttl: pd.DataFrame, spi: pd.DataFrame):
    return ttl.merge(spi, how="left", on="editorial", validate="many_to_one")

def portabilidad(df):
    columnas = ["alto_mm", "ancho_mm", "grueso", "peso"]
    scaler = MinMaxScaler()

    escaladas = pd.DataFrame(
        scaler.fit_transform(df[columnas]),
        columns=columnas,
        index=df.index
    )

    # Invertir: 1 = pequeño/ligero = más portátil
    # .clip(lower=0.01) evita que un valor máximo ponga a 0 toda la media geométrica
    escaladas = (1 - escaladas).clip(lower=0.01)

    df["indice_portabilidad"] = escaladas.prod(axis=1) ** (1 / len(columnas))
    return df

def compacidad(df):
    df['indice_compacidad'] = df['n_paginas'] / (df['alto_mm'] * df['ancho_mm'] * df['grueso'])
    return df

def prestancia(df):
    variables = ["alto_mm", "ancho_mm", "grueso", "peso"]
    scaler = MinMaxScaler()

    normalizadas = pd.DataFrame(
        scaler.fit_transform(df[variables]),
        columns=variables,
        index=df.index
    )

    pesos_encuadernacion = {
        "rústica": 0.4,
        "rústica con solapas": 0.5,
        "tapa blanda": 0.4,
        "cartoné": 0.7,
        "tapa dura": 0.8,
        "tela": 0.9,
        "piel": 1.0,
    }

    encuadernacion = (
        df["encuadernacion"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
        .map(pesos_encuadernacion)
        .fillna(0.5)
    )

    df["indice_prestancia"] = (
        0.20 * (normalizadas["alto_mm"] + normalizadas["ancho_mm"]) / 2
        + 0.15 * normalizadas["grueso"]
        + 0.20 * normalizadas["peso"]
        + 0.45 * encuadernacion
    )
    return df

def ap_critico(df, pesos=None):
    # Claves normalizadas SIN tildes para coincidir con tipo_aparato_critico
    if pesos is None:
        pesos = {
            "introduccion": 1.0,
            "prologo": 1.0,
            "epilogo": 1.0,
            "notas": 1.5,
            "anotaciones": 1.5,
            "estudio": 2.0,
            "comentarios": 1.5,
            "bibliografia": 1.0,
            "cronologia": 0.5,
            "trabajo_preliminar": 1.0
        }

    def calcular_score(textos):
        if isinstance(textos, str):
            try:
                textos = ast.literal_eval(textos)
            except (ValueError, SyntaxError):
                textos = []

        if not isinstance(textos, (list, tuple, set)):
            return 0.0

        return sum(pesos.get(str(texto).lower().strip(), 0) for texto in textos)

    df["score_critico"] = df["tipo_aparato_critico"].apply(calcular_score)
    return df

def colaboradores(df):
    def parse_lista(val):
        if isinstance(val, str):
            try:
                return ast.literal_eval(val)
            except (ValueError, SyntaxError):
                return []
        return val if isinstance(val, list) else []

    colabs_series = df["otros_contribuidores"].apply(parse_lista)
    frecuencia = colabs_series.explode().dropna().value_counts()

    def calcular_score(lista):
        if not isinstance(lista, (list, tuple, set)) or len(lista) == 0:
            return 0.0

        valores = [frecuencia.get(colaborador, 0) for colaborador in lista]
        if not valores:
            return 0.0

        return np.mean(np.log1p(valores))

    df["score_colaboradores"] = colabs_series.apply(calcular_score)
    return df

def prestigio(df):
    def parse_lista(val):
        if isinstance(val, str):
            try:
                return ast.literal_eval(val)
            except (ValueError, SyntaxError):
                return []
        return val if isinstance(val, list) else []

    def calcular_prestigio(fila):
        subcategorias = parse_lista(fila["subcategorias"])
        categorias = parse_lista(fila["categorias"])

        if not subcategorias or not categorias:
            return np.nan

        conteo = {}
        for subcategoria in subcategorias:
            for categoria in categorias:
                if categoria in SUBCATEGORIAS and subcategoria in SUBCATEGORIAS[categoria]:
                    conteo[categoria] = conteo.get(categoria, 0) + 1
                    break

        if not conteo:
            return np.nan

        total = sum(conteo.values())
        pesos = {cat: cant / total for cat, cant in conteo.items()}

        valores = []
        for categoria, peso in pesos.items():
            # Formato exacto de la columna en SPI/Gold
            columna = f"prestigio_{categoria.lower().replace(' ', '_').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}"

            if columna not in df.columns:
                continue

            valor = fila[columna]
            if pd.notna(valor):
                valores.append((valor, peso))

        if not valores:
            return np.nan

        suma_pesos = sum(peso for _, peso in valores)
        return sum(valor * (peso / suma_pesos) for valor, peso in valores)

    df["prestigio_cat"] = df.apply(calcular_prestigio, axis=1)
    return df 

def crear_gold(ttl: pd.DataFrame, spi: pd.DataFrame):

    df = merge_dataframes(ttl, spi)
    df.dropna(subset=['alto_mm', 'ancho_mm', 'peso', 'grueso', 'n_paginas', 'precio'], inplace=True)
    df.drop(columns=['sinopsis'], inplace=True)

    columnas = ["alto_mm", "ancho_mm", "peso"]
    mask = pd.Series(True, index=df.index)

    for col in columnas:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1

        limite_inferior = max(0.0, q1 - 1.5 * iqr)
        limite_superior = q3 + 1.5 * iqr

        mask &= (df[col] >= limite_inferior) & (df[col] <= limite_superior)

    df = df[mask]
    

    df = portabilidad(df)
    df = compacidad(df)
    df = prestancia(df)

    df = colaboradores(df)
    df = ap_critico(df)
    df = prestigio(df)

    return df