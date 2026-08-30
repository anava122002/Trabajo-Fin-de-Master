# ===================================================================================
# MODELO
# ===================================================================================

import re
import numpy as np 
import pandas as pd
from rapidfuzz import fuzz
from constants import MATRICES_ARQUETIPO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "gold" / "gold_metadata.parquet"

STOPWORDS = {"la", "el", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o", "a", "en"}

def limpiar_texto(texto: str) -> str:
    """Elimina caracteres especiales, tildes simples y stopwords."""
    if not isinstance(texto, str):
        return ""
    # Minusculas y quitar caracteres no alfanumericos
    texto = texto.lower().strip()
    palabras = re.findall(r'\b\w+\b', texto)
    # Filtrar palabras vacias
    palabras_filtradas = [p for p in palabras if p not in STOPWORDS]
    return " ".join(palabras_filtradas) if palabras_filtradas else texto

# PASO 1: FILTRO
def filtro(info_usuario: dict, umbral_similitud: float = 75):
    df = pd.read_parquet(DATA_PATH)
    busqueda = info_usuario['busqueda']
    restricciones = info_usuario['restricciones']

    df_filtrado = df.copy()

    titulo_query = busqueda.get("titulo_aprox")
    autor_query = busqueda.get("autor")
    
    # 1. Filtro estricto de Título
    if titulo_query:
        query_limpia = limpiar_texto(titulo_query) # ej: "quijote"
        
        def evaluar_coincidencia(titulo_libro):
            titulo_limpio = limpiar_texto(str(titulo_libro)) # ej: "don quijote de la mancha"
            
            palabras_query = set(query_limpia.split())
            palabras_titulo = set(titulo_limpio.split())
            
            # REGLA 1: Si todas las palabras clave buscadas están presentes en el título -> Pasa (Score 100)
            if palabras_query and palabras_query.issubset(palabras_titulo):
                return 100.0
            
            # REGLA 2: Si la cadena buscada está contenida como subcadena -> Pasa (Score 100)
            if query_limpia in titulo_limpio:
                return 100.0

            # REGLA 3: Si no es contención exacta, evaluar por similitud difusa (typos)
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

    # 3. Filtros duros
    for col, rest in restricciones.items():
        if col in df_filtrado.columns and rest:
            df_filtrado = df_filtrado[df_filtrado[col].between(rest[0], rest[1])]

    return df_filtrado

# PASO 2: CÁLCULO DE PESOS
CRITERIOS = [
    "indice_portabilidad",
    "indice_compacidad",
    "indice_prestancia",
    "aparato_critico",
    "prestigio_cat"
]
def calcular_vector_ahp(matriz: np.ndarray, columnas: list = CRITERIOS):
    """
    Calcula el vector de pesos normalizado y el Ratio de Consistencia (CR).
    """
    n = matriz.shape[0]
    
    # 1. Autovalores y autovectores
    autovalores, autovectores = np.linalg.eig(matriz)
    max_idx = np.argmax(np.real(autovalores))
    lambda_max = np.real(autovalores[max_idx])
    
    # 2. Vector propio principal normalizado (Pesos w_j)
    weights = np.real(autovectores[:, max_idx])
    weights = weights / np.sum(weights)
    
    # 3. Ratio de Consistencia (CR de Saaty)
    ci = (lambda_max - n) / (n - 1)
    ri_5 = 1.12  # Valor aleatorio de Saaty para n = 5
    cr = ci / ri_5
    
    dict_pesos = dict(zip(columnas, np.round(weights, 4)))
    
    return dict_pesos, cr

# PASO 3: MODELO TOPSIS
def ejecutar_topsis(df: pd.DataFrame, pesos_dict: dict) -> pd.DataFrame:
    df_res = df.copy()
    cols = list(pesos_dict.keys())
    
    # 1. Matriz de decisión
    X = df_res[cols].astype(float).values
    
    # 2. Normalización Vectorial
    normas = np.sqrt((X**2).sum(axis=0))
    normas[normas == 0.0] = 1.0
    X_norm = X / normas
    
    # 3. Ponderación con los pesos AHP
    weights = np.array([pesos_dict[c] for c in cols])
    X_weighted = X_norm * weights
    
    # 4. Solución Ideal Positiva (A+) e Ideal Negativa (A-)
    # 'precio' es costo (minimizar); los demás son beneficios (maximizar)
    ideal_pos = []
    ideal_neg = []
    
    for i, col in enumerate(cols):
        if col == "precio":
            ideal_pos.append(X_weighted[:, i].min())
            ideal_neg.append(X_weighted[:, i].max())
        else:
            ideal_pos.append(X_weighted[:, i].max())
            ideal_neg.append(X_weighted[:, i].min())
            
    ideal_pos = np.array(ideal_pos)
    ideal_neg = np.array(ideal_neg)
    
    # 5. Distancias Euclídeas
    d_pos = np.sqrt(((X_weighted - ideal_pos)**2).sum(axis=1))
    d_neg = np.sqrt(((X_weighted - ideal_neg)**2).sum(axis=1))
    
    # 6. Cercanía Relativa (Score TOPSIS de 0 a 1)
    df_res["score_topsis"] = d_neg / (d_pos + d_neg)
    
    return df_res.sort_values(by="score_topsis", ascending=False)

def aplicar_bonificaciones_usuario(df_ranking: pd.DataFrame, busqueda: dict) -> pd.DataFrame:
    if df_ranking.empty:
        return df_ranking

    df_res = df_ranking.copy()
    bonus = np.ones(len(df_res))

    # Acceso directo a claves del diccionario
    ed_pref = busqueda["ed_preferida"] if "ed_preferida" in busqueda else busqueda.get("editorial", "")
    enc_pref = busqueda["enc_preferida"] if "enc_preferida" in busqueda else busqueda.get("encuadernacion", "")

    # Aplicar Bonus de Editorial (+15%)
    if ed_pref:
        term_ed = str(ed_pref).lower().strip()
        mask_ed = df_res['editorial'].fillna("").astype(str).str.lower().str.contains(term_ed, regex=False)
        bonus += np.where(mask_ed, 0.15, 0.0)

    # Aplicar Bonus de Encuadernación (+10%)
    if enc_pref:
        term_enc = str(enc_pref).lower().strip()
        mask_enc = df_res['encuadernacion'].fillna("").astype(str).str.lower().str.contains(term_enc, regex=False)
        bonus += np.where(mask_enc, 0.10, 0.0)

    # Calcular Score Final
    df_res["score_topsis_base"] = df_res["score_topsis"]
    df_res["score_topsis"] = (df_res["score_topsis"] * bonus).clip(upper=1.0)
    
    return df_res.sort_values(by="score_topsis", ascending=False)



def recomendar_ediciones(
    info_usuario: dict, 
    matriz_ahp: np.ndarray = None,
) -> tuple[pd.DataFrame, dict, float]:

    arquetipo = info_usuario['perfil']['arquetipo']
    
    # 1. Filtro estricto por texto / restricciones
    df_filtrado = filtro(info_usuario)
    if df_filtrado.empty:
        return pd.DataFrame(), {}, 0.0

    # 2. Selección de matriz y cálculo AHP
    if matriz_ahp is not None:
        matriz = matriz_ahp
    elif arquetipo and arquetipo in MATRICES_ARQUETIPO:
        matriz = MATRICES_ARQUETIPO[arquetipo]
    else:
        matriz = MATRICES_ARQUETIPO["lectura_general"]

    pesos_dict, cr = calcular_vector_ahp(matriz, CRITERIOS)

    # 3. Ranking base con TOPSIS (evalúa solo métricas físicas/calidad)
    df_ranking = ejecutar_topsis(df_filtrado, pesos_dict)

    # 4. Aplicar multiplicador de afinidad (Preferencias del usuario)
    perfil = info_usuario["perfil"]
    df_ranking_final = aplicar_bonificaciones_usuario(df_ranking, perfil['flags_adicionales'])

    return df_ranking_final, pesos_dict, cr


def transformar_ranking(ranking):
    pass