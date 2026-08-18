import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from constants import SUBCATEGORIAS

def merge_dataframes(ttl:pd.DataFrame, spi:pd.DataFrame):
    return ttl.merge(spi, how="left", on="editorial", validate="many_to_one")

def portabilidad(df):
    columnas = ["alto_mm", "ancho_mm", "grueso", "peso"]
    scaler = MinMaxScaler()
    
    # Escalamos entre 0 y 1
    escaladas = pd.DataFrame(
        scaler.fit_transform(df[columnas]),
        columns=columnas,
        index=df.index
    )
    
    # Invertimos para que 1 = pequeño/ligero (portátil)
    # clip(0.01, 1) evita ceros absolutos que anulen la media geométrica
    escaladas = (1 - escaladas).clip(lower=0.01)
    
    df["indice_portabilidad"] = escaladas.prod(axis=1) ** (1 / len(columnas))
    return df


def compacidad(df):

    df['indice_compacidad'] = df['n_paginas'] / (df['alto_mm'] * df['ancho_mm'] * df['grueso'])

    return df



def prestancia(df):

    variables = [
        "alto_mm",
        "ancho_mm",
        "grueso",
        "peso"
    ]

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
        .str.lower()
        .str.strip()
        .map(pesos_encuadernacion)
        .fillna(0.5)
    )

    df["indice_prestancia"] = (
        0.20 * (
            normalizadas["alto_mm"] +
            normalizadas["ancho_mm"]
        ) / 2
        +
        0.15 * normalizadas["grueso"]
        +
        0.20 * normalizadas["peso"]
        +
        0.45 * encuadernacion
    )

    return df


def ap_critico(df, pesos=None):
    """
    Calcula el score del aparato crítico a partir de los tipos
    de textos complementarios ya identificados en Silver.
    """

    if pesos is None:
        pesos = {
            "introducción": 1.0,
            "prólogo": 1.0,
            "epílogo": 1.0,
            "notas": 1.5,
            "anotaciones": 1.5,
            "estudio": 2.0,
            "comentarios": 1.5,
            "bibliografía": 1.0,
            "cronología": 0.5,
        }

    def calcular_score(textos):
        if not isinstance(textos, (list, tuple, set)):
            return 0.0

        return sum(
            pesos.get(texto.lower().strip(), 0)
            for texto in textos
        )

    df["score_critico"] = df["tipo_aparato_critico"].apply(calcular_score)

    return df


def colaboradores(df):
    """
    Calcula la relevancia de los colaboradores según su frecuencia
    de aparición en el catálogo y genera un score por edición.
    """

    # Contar apariciones de cada colaborador
    frecuencia = (
        df["otros_contribuidores"]
        .explode()
        .dropna()
        .value_counts()
    )

    # Función para obtener el score de una lista de colaboradores
    def calcular_score(lista):
        if not isinstance(lista, (list, tuple, set)):
            return 0.0

        valores = [
            frecuencia.get(colaborador, 0)
            for colaborador in lista
        ]

        if not valores:
            return 0.0

        # Evita que una frecuencia muy alta domine el resultado
        return np.mean(np.log1p(valores))

    df["score_colaboradores"] = (
        df["otros_contribuidores"]
        .apply(calcular_score)
    )

    return df

def prestigio(df):

    def calcular_prestigio(fila):

        subcategorias = fila["subcategorias"]
        categorias = fila["categorias"]

        # No hay subcategorías o categorías identificadas
        if not isinstance(subcategorias, (list, tuple, set)):
            return np.nan

        if not categorias:
            return np.nan

        # Contar cuántas subcategorías pertenecen a cada categoría
        conteo = {}

        for subcategoria in subcategorias:
            for categoria in categorias:
                if subcategoria in SUBCATEGORIAS[categoria]:
                    conteo[categoria] = conteo.get(categoria, 0) + 1
                    break

        # No se ha podido asignar ninguna subcategoría
        if not conteo:
            return np.nan

        # Calcular los pesos
        total = sum(conteo.values())

        pesos = {
            categoria: cantidad / total
            for categoria, cantidad in conteo.items()
        }

        # Obtener los prestigios disponibles
        valores = []

        for categoria, peso in pesos.items():

            columna = f"prestigio_{categoria}"

            if columna not in df.columns:
                continue

            valor = fila[columna]

            if pd.notna(valor):
                valores.append((valor, peso))

        # Ningún prestigio disponible
        if not valores:
            return np.nan

        # Reajustar pesos si alguna categoría no tiene prestigio
        suma_pesos = sum(peso for _, peso in valores)

        prestigio_final = sum(
            valor * (peso / suma_pesos)
            for valor, peso in valores
        )

        return prestigio_final

    df["prestigio_cat"] = df.apply(calcular_prestigio, axis=1)

    return df 


def crear_gold(ttl: pd.DataFrame, spi: pd.DataFrame):

    # 1. Unir TTL y SPI
    df = merge_dataframes(ttl, spi)
    df.dropna(subset=['alto_mm', 'ancho_mm', 'peso', 'grueso', 'n_paginas', 'precio'], inplace=True)

    # 2. Calcular características físicas
    df = portabilidad(df)
    df = compacidad(df)
    df = prestancia(df)

    # 3. Calcular relevancia de colaboradores
    df = colaboradores(df)
    df = ap_critico(df)

    # 4. Calcular prestigio según composición temática
    df = prestigio(df)

    return df