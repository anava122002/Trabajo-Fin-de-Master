# ======================================================================================
# DATOS DE SPI
# ======================================================================================

import pandas as pd
from pathlib import Path
import json
from functools import reduce

def merge_spi(lista_editoriales, ruta_ed="data/json/editoriales.json", ruta_spi="data/bronze/spi"):
    
    with open(ruta_ed, "r", encoding="utf-8") as f:
        editoriales = json.load(f)

    clasificaciones = list(Path(ruta_spi).iterdir())
    dfs = []
    for ruta_cla in clasificaciones:
        print(f"\nIncluyendo {ruta_cla.name}...")
        with open(ruta_cla, "r", encoding="utf-8") as f:
            dfs.append(pd.DataFrame(json.load(f)))

    df = reduce(lambda left, right: left.merge(right, on="Editorial", how='outer'), dfs)

    nombre_spi = {editoriales[ed]["nombre_spi"]: ed for ed in lista_editoriales}
    id_dict = {editoriales[ed]["nombre_spi"]: editoriales[ed]["id"] for ed in lista_editoriales}

    df_selection = df[df['Editorial'].isin(nombre_spi.keys())].copy()
    df_selection['Editorial'] = df_selection["Editorial"].map(nombre_spi)
    df_selection['id'] = df_selection["Editorial"].map(id_dict)

    return df_selection