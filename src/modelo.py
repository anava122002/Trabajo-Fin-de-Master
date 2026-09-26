import re
import numpy as np 
import pandas as pd
from rapidfuzz import fuzz
from constants import MATRICES_ARQUETIPO, CRITERIOS
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "gold" / "gold_metadata.parquet"

STOPWORDS = {"la", "el", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o", "a", "en"}

def limpiar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    palabras = re.findall(r'\b\w+\b', texto)
    palabras_filtradas = [p for p in palabras if p not in STOPWORDS]
    return " ".join(palabras_filtradas) if palabras_filtradas else texto

def filtro(info_usuario: dict, umbral_similitud: float = 75):
    try:
        df = pd.read_parquet(DATA_PATH)
    except Exception:
        # Dummy DataFrame de respaldo si el archivo no existe
        return pd.DataFrame()

    busqueda = info_usuario.get('busqueda', {})
    restricciones = info_usuario.get('restricciones', {})

    df_filtrado = df.copy()

    titulo_query = busqueda.get("titulo_aprox")
    autor_query = busqueda.get("autor")
    categorias_query = busqueda.get("categorias", [])
    
    # 1. Filtro de Título
    if titulo_query:
        query_limpia = limpiar_texto(titulo_query)
        def evaluar_coincidencia(titulo_libro):
            titulo_limpio = limpiar_texto(str(titulo_libro))
            palabras_query = set(query_limpia.split())
            palabras_titulo = set(titulo_limpio.split())
            
            if palabras_query and palabras_query.issubset(palabras_titulo):
                return 100.0
            if query_limpia in titulo_limpio:
                return 100.0
            if not palabras_query.intersection(palabras_titulo):
                score_fuzzy = fuzz.ratio(query_limpia, titulo_limpio)
                return score_fuzzy if score_fuzzy >= 75 else 0.0
            
            return fuzz.token_set_ratio(query_limpia, titulo_limpio)

        scores_titulo = df_filtrado['titulo'].fillna("").apply(evaluar_coincidencia)
        df_filtrado = df_filtrado[scores_titulo >= umbral_similitud]
        
    # 2. Filtro de Autor
    if autor_query and not df_filtrado.empty:
        scores_autor = df_filtrado['autoria'].fillna("").astype(str).apply(
            lambda x: fuzz.partial_ratio(autor_query.lower(), x.lower())
        )
        df_filtrado = df_filtrado[scores_autor >= umbral_similitud]

    # 3. Filtro de Categorías
    if categorias_query and not df_filtrado.empty and 'categorias' in df_filtrado.columns:
        pattern = '|'.join([re.escape(c) for c in categorias_query])
        df_filtrado = df_filtrado[df_filtrado['categorias'].fillna("").astype(str).str.contains(pattern, case=False, regex=True)]

    # 4. Filtros de Restricciones (Precio)
    if 'precio' in restricciones and 'precio' in df_filtrado.columns:
        p_min, p_max = restricciones['precio']
        df_filtrado = df_filtrado[df_filtrado['precio'].between(p_min, p_max)]

    return df_filtrado

def calcular_vector_ahp(matriz: np.ndarray, columnas: list = CRITERIOS):
    n = matriz.shape[0]
    
    # Manejo explícito de Matriz Identidad
    if np.array_equal(matriz, np.eye(n)):
        weights = np.ones(n) / n
        dict_pesos = dict(zip(columnas, np.round(weights, 4)))
        return dict_pesos, 0.0

    autovalores, autovectores = np.linalg.eig(matriz)
    max_idx = np.argmax(np.real(autovalores))
    lambda_max = np.real(autovalores[max_idx])
    
    weights = np.real(autovectores[:, max_idx])
    weights = weights / np.sum(weights)
    
    ci = (lambda_max - n) / (n - 1)
    ri_5 = 1.12
    cr = ci / ri_5
    
    dict_pesos = dict(zip(columnas, np.round(weights, 4)))
    return dict_pesos, float(np.real(cr))

def ejecutar_topsis(df: pd.DataFrame, pesos_dict: dict) -> pd.DataFrame:
    df_res = df.copy()
    cols = list(pesos_dict.keys())
    
    # Verificar disponibilidad de columnas en el DF
    for c in cols:
        if c not in df_res.columns:
            df_res[c] = 0.0

    X = df_res[cols].astype(float).values
    normas = np.sqrt((X**2).sum(axis=0))
    normas[normas == 0.0] = 1.0
    X_norm = X / normas
    
    weights = np.array([pesos_dict[c] for c in cols])
    X_weighted = X_norm * weights
    
    ideal_pos, ideal_neg = [], []
    for i, col in enumerate(cols):
        if col == "precio":
            ideal_pos.append(X_weighted[:, i].min())
            ideal_neg.append(X_weighted[:, i].max())
        else:
            ideal_pos.append(X_weighted[:, i].max())
            ideal_neg.append(X_weighted[:, i].min())
            
    ideal_pos = np.array(ideal_pos)
    ideal_neg = np.array(ideal_neg)
    
    d_pos = np.sqrt(((X_weighted - ideal_pos)**2).sum(axis=1))
    d_neg = np.sqrt(((X_weighted - ideal_neg)**2).sum(axis=1))
    
    denom = d_pos + d_neg
    denom[denom == 0] = 1e-9
    df_res["score_topsis"] = d_neg / denom
    
    return df_res.sort_values(by="score_topsis", ascending=False)

def aplicar_bonificaciones_usuario(df_ranking: pd.DataFrame, flags: dict) -> pd.DataFrame:
    if df_ranking.empty:
        return df_ranking

    df_res = df_ranking.copy()
    bonus = np.ones(len(df_res))

    # Incorporación de TODAS las preferencias recogidas por el agente
    ed_pref = flags.get("ed_preferida")
    enc_pref = flags.get("enc_preferida")
    col_pref = flags.get("col_preferida")
    prefiere_ilustrado = flags.get("prefiere_ilustrado", False)

    if ed_pref:
        mask_ed = df_res['editorial'].fillna("").astype(str).str.lower().str.contains(str(ed_pref).lower().strip(), regex=False)
        bonus += np.where(mask_ed, 0.15, 0.0)

    if enc_pref:
        mask_enc = df_res['encuadernacion'].fillna("").astype(str).str.lower().str.contains(str(enc_pref).lower().strip(), regex=False)
        bonus += np.where(mask_enc, 0.10, 0.0)

    if col_pref and 'coleccion' in df_res.columns:
        mask_col = df_res['coleccion'].fillna("").astype(str).str.lower().str.contains(str(col_pref).lower().strip(), regex=False)
        bonus += np.where(mask_col, 0.10, 0.0)

    if prefiere_ilustrado and 'es_ilustrado' in df_res.columns:
        mask_ilus = df_res['es_ilustrado'] == True
        bonus += np.where(mask_ilus, 0.15, 0.0)

    df_res["score_topsis_base"] = df_res["score_topsis"]
    df_res["score_topsis"] = (df_res["score_topsis"] * bonus).clip(upper=1.0)
    
    return df_res.sort_values(by="score_topsis", ascending=False)

def recomendar_ediciones(info_usuario: dict, matriz_ahp: np.ndarray = None) -> tuple[pd.DataFrame, dict, float]:
    perfil = info_usuario.get('perfil', {})
    arquetipo = perfil.get('arquetipo', 'lectura_general')
    
    df_filtrado = filtro(info_usuario)
    if df_filtrado.empty:
        return pd.DataFrame(), {}, 0.0

    if matriz_ahp is not None:
        matriz = matriz_ahp
    elif arquetipo in MATRICES_ARQUETIPO:
        matriz = MATRICES_ARQUETIPO[arquetipo]
    else:
        matriz = MATRICES_ARQUETIPO["lectura_general"]

    pesos_dict, cr = calcular_vector_ahp(matriz, CRITERIOS)
    df_ranking = ejecutar_topsis(df_filtrado, pesos_dict)

    flags = perfil.get('flags_adicionales', {})
    df_ranking_final = aplicar_bonificaciones_usuario(df_ranking, flags)

    df_top = df_ranking_final.head(3).reset_index(drop=True)
    return df_top, pesos_dict, cr


