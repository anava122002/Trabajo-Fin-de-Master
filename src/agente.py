import sys
from typing import TypedDict, Literal, Annotated, List, Optional, Tuple
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargar variables de entorno si existen (ej. API Keys)
load_dotenv()

# Importaciones de LangChain y LangGraph
from langchain_core.messages import SystemMessage, BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Cargar el LLM según las librerías usadas en agente.py
from langchain_ollama import ChatOllama
llm = ChatOllama(model="qwen2.5:3b", temperature=0.2)

# Importar la función del modelo determinista
from modelo import recomendar_ediciones


# =======================================================================================================
# ESTRUCTURAS DE DATOS (PYDANTIC SCHEMAS)
# =======================================================================================================

class BusquedaFiltros(BaseModel):
    titulo_aprox: Optional[str] = Field(
        default=None, description="Título aproximado o palabras clave del libro"
    )
    autor: Optional[str] = Field(
        default=None, description="Nombre o apellidos del autor/a"
    )
    categorias: List[str] = Field(
        default_factory=list, description="Lista de categorías principales"
    )
    subcategorias: List[str] = Field(
        default_factory=list, description="Lista de subcategorías específicas"
    )


class RestriccionesFiltros(BaseModel):
    precio: Tuple[float, float] = Field(
        default=(0.0, 50.0),
        description="Rango de precio [min, max] en euros",
    )


class FlagsAdicionales(BaseModel):
    es_para_regalo: bool = Field(
        default=False, description="Indica si la compra es para regalo"
    )
    prefiere_ilustrado: bool = Field(
        default=False, description="Indica si prefiere edición ilustrada"
    )
    ed_preferida: Optional[str] = Field(
        default=None, description="Editorial preferida por el usuario"
    )
    col_preferida: Optional[str] = Field(
        default=None, description="Colección preferida por el usuario"
    )
    enc_preferida: Optional[str] = Field(
        default=None, description="Encuadernación preferida (ej. Bolsillo, Tapa dura)"
    )


class PerfilFiltros(BaseModel):
    arquetipo: str = Field(
        default="lectura_general",
        description="Uno de: estudio_investigacion, lectura_general, coleccion_regalo, escolar_juvenil",
    )
    flags_adicionales: FlagsAdicionales = Field(
        default_factory=FlagsAdicionales
    )


class InfoBusqueda(BaseModel):
    busqueda: BusquedaFiltros = Field(default_factory=BusquedaFiltros)
    restricciones: RestriccionesFiltros = Field(
        default_factory=RestriccionesFiltros
    )
    perfil: PerfilFiltros = Field(default_factory=PerfilFiltros)


# --- Estado del agente
class EstadoAgente(TypedDict):
    preguntas: Annotated[list[BaseMessage], add_messages]
    info_busqueda: dict  
    campo_actual: str  # Rastrea qué punto específico se está preguntando
    datos_completos: bool  
    top_libros: list  
    respuesta_final: str


class ExtraerInfoPuntoAPunto(BaseModel):
    """Estructura para la extracción iterativa y secuencial punto por punto."""

    info_busqueda: InfoBusqueda
    campo_siguiente: str = Field(
        description=(
            "Nombre exacto de la clave del diccionario sobre la cual se va a preguntar a continuación, "
            "o 'FIN' si ya se han preguntado y confirmado todos los puntos uno a uno."
        )
    )
    datos_completos: bool = Field(
        description=(
            "True UNICAMENTE si se han preguntado absolutamente TODOS los puntos uno por uno "
            "y el usuario ha confirmado que toda la información recolectada es correcta. False en caso contrario."
        )
    )
    mensaje_conversacional: str = Field(
        description=(
            "Mensaje directo al usuario realizando la pregunta correspondiente ÚNICAMENTE al campo actual, "
            "o solicitando confirmación final de todo el resumen si se llegó al final."
        )
    )


# =======================================================================================================
# NODOS Y GRAFO
# =======================================================================================================

# Secuencia estricta punto por punto para la recolección del diccionario info_busqueda
ORDEN_PREGUNTAS = [
    "busqueda.titulo_aprox",
    "busqueda.autor",
    "busqueda.categorias",
    "busqueda.subcategorias",
    "restricciones.precio",
    "perfil.arquetipo",
    "perfil.flags_adicionales.es_para_regalo",
    "perfil.flags_adicionales.prefiere_ilustrado",
    "perfil.flags_adicionales.ed_preferida",
    "perfil.flags_adicionales.col_preferida",
    "perfil.flags_adicionales.enc_preferida"
]


def nodo_recolector(state: EstadoAgente) -> dict:
    """Subagente 1: Recolecta la información preguntando punto por punto en estricto orden."""

    campo_actual = state.get("campo_actual") or ORDEN_PREGUNTAS[0]

    prompt_recolector = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un asistente bibliotecario metódico y ordenado.\n"
                "Tu tarea es rellenar la estructura 'info_busqueda' realizando preguntas **punto por punto**.\n\n"
                f"El orden estricto de preguntas es:\n{ORDEN_PREGUNTAS}\n\n"
                f"Actualmente te encuentras indagando el campo: '{campo_actual}'.\n\n"
                "Instrucciones clave:\n"
                "1. Extrae la información aportada por el usuario en el historial y actualiza 'info_busqueda'.\n"
                "2. Formula la pregunta del campo actual de manera clara y amable.\n"
                "3. Si el usuario responde sobre el campo actual, avanza 'campo_siguiente' al próximo campo del orden estricto.\n"
                "4. No avances al siguiente punto ni preguntes múltiples temas a la vez; indaga punto por punto.\n"
                "5. Una vez recorridos todos los puntos, muestra el resumen completo de 'info_busqueda' y pide confirmación final al usuario.\n"
                "6. Solo marca 'datos_completos' en True cuando se hayan completado todos los campos y el usuario confirme de forma explícita que la información es correcta.",
            ),
            MessagesPlaceholder(variable_name="preguntas"),
        ]
    )

    cadena_recolectora = prompt_recolector | llm.with_structured_output(
        ExtraerInfoPuntoAPunto
    )

    resultado: ExtraerInfoPuntoAPunto = cadena_recolectora.invoke(
        {"preguntas": state["preguntas"]}
    )

    mensaje_ia = AIMessage(content=resultado.mensaje_conversacional)

    return {
        "info_busqueda": resultado.info_busqueda.model_dump(),
        "campo_actual": resultado.campo_siguiente,
        "datos_completos": resultado.datos_completos,
        "preguntas": [mensaje_ia],
    }


def nodo_modelo(state: EstadoAgente) -> dict:
    """Nodo determinista: Ejecuta la función recomendar_ediciones()."""
    
    criterios = state["info_busqueda"]
    top_libros_df = recomendar_ediciones(criterios)
    
    if not top_libros_df.empty:
        top_libros = top_libros_df.to_dict(orient="records")
    else:
        top_libros = []

    return {"top_libros": top_libros}


def nodo_explicacion(state: EstadoAgente) -> dict:
    """Subagente 2: Redacta la justificación final recomendando las ediciones obtenidas."""
    top_libros = state["top_libros"]
    criterios_usuario = state["info_busqueda"]

    prompt_explicador = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un recomendador literario experto. Has recibido la lista de las mejores ediciones "
                "calculadas por un sistema multicriterio (TOPSIS).\n"
                "Presenta al usuario las opciones obtenidas y justifica de forma natural y clara por qué "
                "se adaptan a las preferencias solicitadas.",
            ),
            (
                "human",
                "Preferencias solicitadas:\n{criterios}\n\nTop ediciones recomendadas por el modelo:\n{libros}\n\n"
                "Por favor, redacta la recomendación final dirigida al usuario:",
            ),
        ]
    )

    cadena_explicacion = prompt_explicador | llm

    respuesta = cadena_explicacion.invoke(
        {"criterios": criterios_usuario, "libros": top_libros}
    )

    return {"respuesta_final": respuesta.content}


# --- Transición condicional
def evaluar_completitud(state: EstadoAgente) -> str:
    if state.get("datos_completos"):
        return "ejecutar_modelo"
    return END


# --- Construcción del grafo de estados
builder = StateGraph(EstadoAgente)

builder.add_node("recolector", nodo_recolector)
builder.add_node("ejecutar_modelo", nodo_modelo)
builder.add_node("explicador", nodo_explicacion)

builder.set_entry_point("recolector")

builder.add_conditional_edges(
    "recolector",
    evaluar_completitud,
    {
        "ejecutar_modelo": "ejecutar_modelo",
        END: END,
    },
)

builder.add_edge("ejecutar_modelo", "explicador")
builder.add_edge("explicador", END)

agente_app = builder.compile()


# ======================================================================================
# BLOQUE DE EJECUCIÓN PRINCIPAL (Consola INTERACTIVA)
# ======================================================================================

if __name__ == "__main__":

    # Diccionario inicial especificado en la consulta
    info_busqueda_inicial = {
        "busqueda": {
            "titulo_aprox": None,
            "autor": "Elvira Sastre",
            "categorias": ['Literatura'],
            "subcategorias": []
        },
        "restricciones": {
            "precio": (0.0, 50.0)
        },
        "perfil": {
            "arquetipo": "lectura_general",
            "flags_adicionales": {
                "es_para_regalo": False,
                "prefiere_ilustrado": False,
                "ed_preferida": None,
                "col_preferida": None,
                "enc_preferida": None
            }
        }
    }

    print("--- INICIANDO AGENTE RECOMENDADOR PUNTO POR PUNTO ---")
    print("Escribe 'salir' o 'exit' para terminar.\n")

    estado_actual = {
        "preguntas": [],
        "info_busqueda": info_busqueda_inicial,
        "campo_actual": ORDEN_PREGUNTAS[0],
        "datos_completos": False,
        "top_libros": [],
        "respuesta_final": "",
    }

    # Primer mensaje de arranque del agente
    estado_actual["preguntas"].append(
        HumanMessage(content="Hola, quisiera buscar una recomendación de libro.")
    )

    print("[Iniciando conversación...]")
    estado_actual = agente_app.invoke(estado_actual)
    
    ultimo_mensaje = estado_actual["preguntas"][-1]
    print(f"\nAgente (Recolector) > {ultimo_mensaje.content}")

    while True:
        user_input = input("\nUsuario > ")
        if user_input.lower() in ["salir", "exit"]:
            print("¡Hasta luego!")
            break

        estado_actual["preguntas"].append(HumanMessage(content=user_input))

        print("\n[Pensando...]")
        estado_actual = agente_app.invoke(estado_actual)

        if estado_actual.get("respuesta_final"):
            print(f"\nAgente (Explicador) > {estado_actual['respuesta_final']}")
            print("\n--- RECOMENDACIONES TOPSIS CALCULADAS ---")
            for idx, libro in enumerate(estado_actual["top_libros"], 1):
                print(f"{idx}. {libro.get('titulo', 'Sin título')} - Editorial: {libro.get('editorial', 'N/A')} - Score: {libro.get('score_topsis', 'N/A')}")
            break
        else:
            ultimo_mensaje = estado_actual["preguntas"][-1]
            print(f"\nAgente (Recolector) > {ultimo_mensaje.content}")