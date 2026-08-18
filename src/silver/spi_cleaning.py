import json
import pandas as pd 
import numpy as np 
from pathlib import Path
from src.constants import EDITORIALES

SPI_A_ED = {
    nombre_spi: editorial
    for editorial, datos in EDITORIALES.items()
    for nombre_spi in (
        datos["spi"]
        if isinstance(datos["spi"], list)
        else [datos["spi"]]
    )
    if nombre_spi is not None
}

def merge_spi(ruta_spi="data/bronze/spi", spi_a_ed = SPI_A_ED):
    rutas = sorted(Path(ruta_spi).glob("*.csv"))
    dfs = []
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
    
    df = pd.concat(dfs, axis=1, join="outer").reset_index()

    df_selection = df[df['Editorial'].isin(spi_a_ed.values())].copy()

    return df_selection

def prestigio_editorial(df):
    df = df.loc[:, ~df.columns.duplicated()].copy()

    df_prestigio = pd.DataFrame({})
    df_prestigio["editorial"] = df["Editorial"]

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
    nuevas_filas = {}
    for col in df_prestigio.columns:
        nuevas_filas[col] = []

    for ed_dict in EDITORIALES.items():
        ed = ed_dict[0]
        spi = ed_dict[1]['spi']

        if spi is None:
            for col in nuevas_filas.keys():
                if col == 'editorial':
                    nuevas_filas[col].append(ed)
                else: 
                    nuevas_filas[col].append(0)

    nuevas_filas = pd.DataFrame(nuevas_filas)
    df_prestigio = pd.concat([df_prestigio, nuevas_filas], ignore_index=True)

        # df_prestig.to_parquet("data/silver/prestigio_spi.parquet", engine="pyarrow")

        # añadir filas de editoriales que no están en el spi con todo cero

    return df_prestigio
