import sys
import json
from typing import TypedDict, Annotated, List, Optional, Tuple
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from langchain_ollama import ChatOllama
llm = ChatOllama(
    model="qwen2.5:3b", 
    temperature=0.2, # Reducción de temperatura para mayor control temático
    base_url="http://127.0.0.1:11434"
)

from modelo import recomendar_ediciones
from constants import CATEGORIAS_SPI, SUBCATEGORIAS

# Schemas
class BusquedaFiltros(BaseModel):
    titulo_aprox: Optional[str] = Field(default=None)
    autor: Optional[str] = Field(default=None)
    categorias: List[str] = Field(default_factory=list)
    subcategorias: List[str] = Field(default_factory=list)

class RestriccionesFiltros(BaseModel):
    precio: Tuple[float, float] = Field(default=(0.0, 100.0))

class FlagsAdicionales(BaseModel):
    es_para_regalo: bool = Field(default=False)
    prefiere_ilustrado: bool = Field(default=False)
    ed_preferida: Optional[str] = Field(default=None)
    col_preferida: Optional[str] = Field(default=None)
    enc_preferida: Optional[str] = Field(default=None)

class PerfilFiltros(BaseModel):
    arquetipo: str = Field(default="lectura_general")
    flags_adicionales: FlagsAdicionales = Field(default_factory=FlagsAdicionales)

class InfoBusqueda(BaseModel):
    busqueda: BusquedaFiltros = Field(default_factory=BusquedaFiltros)
    restricciones: RestriccionesFiltros = Field(default_factory=RestriccionesFiltros)
    perfil: PerfilFiltros = Field(default_factory=PerfilFiltros)

class EstadoAgente(TypedDict):
    preguntas: Annotated[list[BaseMessage], add_messages]
    info_busqueda: dict  
    datos_completos: bool  
    top_libros: list
    pesos_ahp: dict
    cr_ahp: float
    respuesta_final: str

class ExtraerInfoFluida(BaseModel):
    info_busqueda: InfoBusqueda
    datos_completos: bool = Field(description="True si se identifica título, autor o tema clave.")
    mensaje_conversacional: str = Field(description="Mensaje breve confirmando los datos tomados.")

# Nodos
def nodo_recolector(state: EstadoAgente) -> dict:
    str_categorias = ", ".join(CATEGORIAS_SPI)
    json_subcategorias = json.dumps(SUBCATEGORIAS, ensure_ascii=False, indent=2)
    str_subcategorias_escapado = json_subcategorias.replace("{", "{{").replace("}", "}}")

    prompt_recolector = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un agente recepcionista de librería. Rellena la estructura 'info_busqueda'.\n"
            "Marca `datos_completos: True` cuando haya título, autor o temática claros.\n"
            "CATEGORÍAS:\n{categorias}\n\nSUBCATEGORÍAS:\n{subcategorias}"
        ),
        MessagesPlaceholder(variable_name="preguntas"),
    ])

    cadena = prompt_recolector | llm.with_structured_output(ExtraerInfoFluida)
    resultado = cadena.invoke({
        "preguntas": state["preguntas"],
        "categorias": str_categorias,
        "subcategorias": str_subcategorias_escapado
    })

    return {
        "info_busqueda": resultado.info_busqueda.model_dump(),
        "datos_completos": resultado.datos_completos,
        "preguntas": [AIMessage(content=resultado.mensaje_conversacional)],
    }

def nodo_modelo(state: EstadoAgente) -> dict:
    criterios = state["info_busqueda"]
    
    # Desempaquetado correcto de la tupla devuelta por el modelo
    top_libros_df, pesos_dict, cr = recomendar_ediciones(criterios)
    
    if not top_libros_df.empty:
        top_libros = top_libros_df.to_dict(orient="records")
    else:
        top_libros = []

    return {
        "top_libros": top_libros,
        "pesos_ahp": pesos_dict,
        "cr_ahp": cr
    }

def nodo_explicacion(state: EstadoAgente) -> dict:
    top_libros = state["top_libros"]
    criterios_usuario = state["info_busqueda"]
    pesos = state.get("pesos_ahp", {})

    # Manejo del estado "No encuentro esa obra"
    if not top_libros:
        return {
            "respuesta_final": "Lo siento, no he encontrado ninguna edición en nuestro catálogo que coincida con tus criterios de búsqueda. Prueba a ampliar los filtros de precio o revisar el título."
        }

    prompt_explicador = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un recomendador literario riguroso. Explica la selección de ediciones devuelta por TOPSIS.\n"
            "REGLA DE ORO: Solo puedes justificar la recomendación basándote estrictamente en las variables que han intervenido en el cálculo:\n"
            "- Pesos AHP aplicados: {pesos}\n"
            "- Variables físicas y editoriales reales del libro (páginas, encuadernación, precio, aparato crítico, prestigio SPI).\n"
            "NO te inventes datos ni menciones atributos que no estén explícitamente en el objeto del libro."
        ),
        (
            "human",
            "Criterios del usuario:\n{criterios}\n\nEdiciones ordenadas por TOPSIS:\n{libros}\n\n"
            "Redacta una justificación concisa:"
        ),
    ])

    cadena = prompt_explicador | llm
    respuesta = cadena.invoke({
        "criterios": criterios_usuario,
        "libros": top_libros,
        "pesos": pesos
    })

    return {"respuesta_final": respuesta.content}

def evaluar_completitud(state: EstadoAgente) -> str:
    return "ejecutar_modelo" if state.get("datos_completos") else END

# Grafo
builder = StateGraph(EstadoAgente)
builder.add_node("recolector", nodo_recolector)
builder.add_node("ejecutar_modelo", nodo_modelo)
builder.add_node("explicador", nodo_explicacion)

builder.set_entry_point("recolector")
builder.add_conditional_edges("recolector", evaluar_completitud, {"ejecutar_modelo": "ejecutar_modelo", END: END})
builder.add_edge("ejecutar_modelo", "explicador")
builder.add_edge("explicador", END)

agente_app = builder.compile()