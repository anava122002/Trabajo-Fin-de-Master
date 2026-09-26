import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from modelo import recomendar_ediciones


load_dotenv()
# API_KEY = os.getenv("GEMINI_API_TOKEN")
# MODEL = "gemini-2.5-flash-lite"

# llm = ChatGoogleGenerativeAI(
#     model=MODEL,
#     temperature=0.7,
#     google_api_key=API_KEY
# )

from langchain_ollama import ChatOllama
llm = ChatOllama(model="qwen2.5:3b", temperature=0.2)

# =======================================================================================================
# NODOS
# =======================================================================================================

# --- Estructura de los datos

# 1. Sub-sección de búsqueda
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


# 2. Sub-sección de restricciones físicas y económicas
class RestriccionesFiltros(BaseModel):
    precio: Tuple[float, float] = Field(
        default=(0.0, 100.0),
        description="Rango de precio [min, max] en euros",
    )


# 3. Sub-sección de flags adicionales
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


# 4. Sub-sección de perfil
class PerfilFiltros(BaseModel):
    arquetipo: str = Field(
        default="lectura_general",
        description="Uno de: estudio_investigacion, lectura_general, coleccion_regalo, escolar_juvenil",
    )
    flags_adicionales: FlagsAdicionales = Field(
        default_factory=FlagsAdicionales
    )


# 5. Esquema global completo (info_busqueda)
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
    datos_completos: bool  
    top_libros: list  
    respuesta_final: str

class ExtraerInfoBusqueda(BaseModel):
    """Estructura de extracción y respuesta para el Subagente Recolector."""

    info_busqueda: InfoBusqueda
    datos_completos: bool = Field(
        description=(
            "True UNICAMENTE si le has mostrado el resumen al usuario y este ha confirmado "
            "que los datos son correctos. False si todavía estás indagando o pidiendo confirmación."
        )
    )
    mensaje_conversacional: str = Field(
        description=(
            "El mensaje de texto que le dirás al usuario en este turno. Si faltan datos, "
            "hazle preguntas amables. Si ya tienes bastante info, muestra el resumen de lo "
            "recopilado y pregúntale si es correcto."
        )
    )


# --- Nodos
def nodo_recolector(state: EstadoAgente) -> dict:
    """Subagente 1: Conversa con el usuario para extraer preferencias y estructurar 'info_busqueda'."""

    prompt_recolector = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un bibliotecario experto. Tu objetivo es ayudar al usuario a encontrar la edición perfecta de un libro.\n"
                "Revisa la conversación y actualiza la información de búsqueda.\n"
                "Genera siempre un 'mensaje_conversacional' adecuado: responde amable, indaga los datos que falten o "
                "pide confirmación si ya tienes lo principal.",
            ),
            MessagesPlaceholder(variable_name="preguntas"),
        ]
    )

    cadena_recolectora = prompt_recolector | llm.with_structured_output(
        ExtraerInfoBusqueda
    )

    resultado: ExtraerInfoBusqueda = cadena_recolectora.invoke(
        {"preguntas": state["preguntas"]}
    )

    dict_busqueda = resultado.info_busqueda.model_dump()

    # Creamos la respuesta que generó la IA para el usuario
    mensaje_ia = AIMessage(content=resultado.mensaje_conversacional)

    return {
        "info_busqueda": dict_busqueda,
        "datos_completos": resultado.datos_completos,
        # Al pasar mensaje_ia en 'preguntas', LangGraph (vía add_messages) lo añade al historial
        "preguntas": [mensaje_ia],
    }


def nodo_modelo(state: EstadoAgente) -> dict:
    """Nodo determinista: Ejecuta el pipeline TOPSIS-AHP."""
    
    criterios = state["info_busqueda"]

    top_libros = recomendar_ediciones(criterios).to_dict(orient="records")

    return {"top_libros": top_libros}


def nodo_explicacion(state: EstadoAgente) -> dict:
    """Subagente 2: Interpreta los resultados del modelo TOPSIS y redacta la justificación para el usuario."""
    top_libros = state["top_libros"]
    criterios_usuario = state["info_busqueda"]

    prompt_explicador = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un recomendador literario experto. Has recibido una lista de las mejores ediciones calculadas por un sistema multicriterio (TOPSIS). "
                "Tu tarea es presentar al usuario las opciones y justificar de forma natural y convincente por qué se han escogido esas concretamente para su perfil, destacando los aspectos más relevantes según su arquetipo.",
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

# --- Transición 
def evaluar_completitud(state: EstadoAgente) -> str:
    """Si 'datos_completos' es True, avanza AUTOMÁTICAMENTE al modelo sin esperar input del usuario."""
    if state.get("datos_completos"):
        return "ejecutar_modelo"
    return END

# --- Construcción grafo
builder = StateGraph(EstadoAgente)

builder.add_node("recolector", nodo_recolector)
builder.add_node("ejecutar_modelo", nodo_modelo)
builder.add_node("explicador", nodo_explicacion)

# Punto de entrada directo al recolector
builder.set_entry_point("recolector")

# Borde condicional desde el recolector
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
# BLOQUE DE EJECUCIÓN PRINCIPAL (Para pruebas en consola)
# ======================================================================================

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    print("--- INICIANDO AGENTE RECOMENDADOR LITERARIO ---")
    print("Escribe 'salir' o 'exit' para terminar.\n")

    # Inicializamos el estado local de prueba
    estado_actual = {
        "preguntas": [],
        "info_busqueda": {},
        "datos_completos": False,
        "top_libros": [],
        "respuesta_final": "",
    }

    while True:
        # 1. Capturar entrada por terminal
        user_input = input("\nUsuario > ")
        if user_input.lower() in ["salir", "exit"]:
            print("¡Hasta luego!")
            break

        # 2. Agregar el mensaje del usuario al historial
        estado_actual["preguntas"].append(HumanMessage(content=user_input))

        # 3. Invocar al agente LangGraph
        print("\n[Pensando...]")
        estado_actual = agente_app.invoke(estado_actual)

        # 4. Mostrar la respuesta según la fase del agente
        if estado_actual.get("respuesta_final"):
            # Fase final: TOPSIS ejecutado y explicación lista
            print(f"\nAgente (Explicador) > {estado_actual['respuesta_final']}")
            print("\n--- TOPSIS RESULTADOS ---")
            print(estado_actual["top_libros"])
            break
        else:
            # Fase recolectora: El agente sigue preguntando o confirmando
            ultimo_mensaje = estado_actual["preguntas"][-1]
            print(f"\nAgente (Recolector) > {ultimo_mensaje.content}")

        # [Opcional] Para depurar: muestra el estado del diccionario de búsqueda actual
        # print(f"\n[DEBUG - info_busqueda]: {estado_actual.get('info_busqueda')}")
        # print(f"[DEBUG - datos_completos]: {estado_actual.get('datos_completos')}")
