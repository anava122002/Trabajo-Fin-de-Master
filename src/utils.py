import numpy as np
import pandas as pd
import json
import re
import os 
from pathlib import Path

# abrir json (lectura)
def leer_json(ruta:str, df:bool= False):
    if Path(ruta).is_file():
        if df:
            arch = pd.read_json(Path(ruta).absolute())
        else:
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    arch = json.load(f)

        return arch

def leer_df(ruta, formato_csv=True):
    ruta_real = Path(ruta).resolve()
    ruta_real.parent.mkdir(parents=True, exist_ok=True)
    
    if Path(ruta).is_file():
        if formato_csv:
            arch = pd.read_csv(ruta)
        else:
           arch = pd.read_parquet(ruta, engine="pyarrow")

    return arch

# guardar parquet/csv
def guardar_df(df:pd.DataFrame, ruta: str, formato_csv=True):
    ruta_real = Path(ruta).resolve()
    ruta_real.parent.mkdir(parents=True, exist_ok=True)

    if formato_csv:
        df.to_csv(ruta_real, index=False)
    else:
        df.to_parquet(ruta_real, engine="pyarrow", index=False)

