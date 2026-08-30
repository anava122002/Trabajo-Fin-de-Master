import json
import pandas as pd 
import numpy as np 
import sys
from pathlib import Path
import os
import json

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils import leer_json, guardar_df

dict_editoriales = leer_json("data/json/editoriales.json")

SPI_A_ED = {
    nombre_spi: editorial
    for editorial, datos in dict_editoriales.items()
    for nombre_spi in (
        datos["nombre_spi"]
        if isinstance(datos["nombre_spi"], list)
        else [datos["nombre_spi"]]
    )
    if nombre_spi is not None
}

def merge_spi(ruta_spi="data/bronze/spi", spi_a_ed = SPI_A_ED):
    print("="*50,"\nCreando DataFrame con todos los rankings de prestigio\n","="*50)
    print("Leyendo rutas...")
    rutas = sorted(Path(ruta_spi).glob("*.csv"))
    dfs = []
    print("Importando resultados...")
    for ruta in rutas:
        df = pd.read_csv(ruta)

        if "Editorial" not in df.columns:
            raise ValueError(f"{ruta.name} no contiene la columna 'Editorial'.")

        nombre = ruta.stem.lower().replace("clasificacion_", "")

        df = df.rename(columns={
            c: f"{c}_{nombre}"
            for c in df.columns
            if c != "Editorial"
        })
        df["Editorial"] = df["Editorial"].map(spi_a_ed)
        df = (
            df
            .groupby("Editorial", as_index=False)
            .first()
        )
        df = df.set_index("Editorial")
        dfs.append(df)

    print("Resultados importados. Concatenando DataFrames...")
    df = pd.concat(dfs, axis=1, join="outer").reset_index()

    df_selection = df[df['Editorial'].isin(spi_a_ed.values())].copy()
    print("DataFrame creado con éxito.")
    
    return df_selection

def crear_silver_spi(df):
    print("="*50, "\nCREACIÓN DE silver_spi.csv\n", "="*50)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    df_prestigio = pd.DataFrame({})
    df_prestigio["editorial"] = df["Editorial"]

    print("Calculando prestigios...")
    for i in range(1, len(df.columns) - 1, 2):
        col_pos = df.columns[i]
        col_icee = df.columns[i + 1]

        nombre_col = f"prestigio{str(col_pos).replace('Posición', '').strip()}"

        # Extraer como Series unimodales e iloc para evitar ambigüedades
        s_pos = df.iloc[:, i]
        s_icee = df.iloc[:, i + 1]

        mask = s_pos.notna() & s_icee.notna()

        icee = s_icee
        icee_min = icee.min()
        icee_max = icee.max()
        
        if icee_max != icee_min:
            icee_norm = (icee - icee_min) / (icee_max - icee_min)
        else:
            icee_norm = pd.Series(0.0, index=df.index)

        n = s_pos.max()
        percentil = 1 - (s_pos - 1) / (n - 1) if (pd.notna(n) and n > 1) else pd.Series(1.0, index=df.index)

        df_prestigio[nombre_col] = 0.0
        
        # Asignación segura con valores indexados por la máscara
        val_calculado = 0.1 + 0.9 * (0.8 * icee_norm[mask] + 0.2 * percentil[mask])
        df_prestigio.loc[mask, nombre_col] = val_calculado

    df_prestigio = df_prestigio.fillna(0.0)

    # Se incluyen las editoriales que no están en el SPI
    print("Incluyendo editoriales faltantes...")
    nuevas_filas = {}
    for col in df_prestigio.columns:
        nuevas_filas[col] = []

    for ed_dict in dict_editoriales.items():
        ed = ed_dict[0]
        spi = ed_dict[1]['nombre_spi']

        if spi is False:
            for col in nuevas_filas.keys():
                if col == 'editorial':
                    nuevas_filas[col].append(ed)
                else: 
                    nuevas_filas[col].append(0)

    nuevas_filas = pd.DataFrame(nuevas_filas)
    df_prestigio = pd.concat([df_prestigio, nuevas_filas], ignore_index=True)

    print("Guardando resultados...")
    guardar_df(df_prestigio,"data/silver/silver_spi.csv")
    print("silver_spi.csv guardado.")

    return df_prestigio
