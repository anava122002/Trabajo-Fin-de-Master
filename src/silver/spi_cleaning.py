# ======================================================================================
# DATOS DE SPI
# ======================================================================================

import json
import pandas as pd 
import numpy as np 
from pathlib import Path

def merge_spi(ruta_spi="data/bronze/spi", ruta_dict = 'data/json/spi_a_ed.json'):
    with open(ruta_dict, "r", encoding="utf-8") as f:
        spi_a_ed = json.load(f)

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
    df_prestigio = pd.DataFrame({})
    df_prestigio["Editorial"] = df["Editorial"]

    for i in range(1, len(df.columns) - 2, 2):
        col_pos = df.columns[i]
        col_icee = df.columns[i + 1]

        nombre_col = f"prestigio_{str(col_pos).replace('Posición', '').strip()}"

        mask = df[[col_pos, col_icee]].notna().all(axis=1)

        icee = df[col_icee]
        icee_norm = (icee - icee.min()) / (icee.max() - icee.min())

        n = df[col_pos].max()
        percentil = 1 - (df[col_pos] - 1) / (n - 1) if n > 1 else pd.Series(1.0, index=df.index)

        df_prestigio[nombre_col] = 0.0
        df_prestigio.loc[mask, nombre_col] = 0.1 + 0.9*(0.8 * icee_norm[mask] + 0.2 * percentil[mask])

        df.to_parquet("data/silver/prestigio_spi.parquet", engine="pyarrow")

    return df_prestigio
