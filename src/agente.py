import os
import json
from typing import List, Optional

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser

from google.colab import userdata


API_KEY = userdata.get('HF_API_KEY')

MODEL = "Qwen/Qwen2.5-72B-Instruct"

llm = HuggingFaceEndpoint(
    repo_id=MODEL,
    temperature=0.5,
    huggingfacehub_api_token=API_KEY
)

class ExtraccionFiltros(BaseModel):     # completar cuando el DF esté completo
    titulo: Optional[str] = Field(default=None, description="Título del libro (completo o aproximado). Puede ser que el usuario dé el título completo o sólo lo sugiera (por ejemplo en caso de pedir una antología, una recopilación de obras o tener clara la temática pero no el libro concreto).")
    autor: Optional[str] = Field(default=None, description="Autor del libro")
    formato: Optional[str] = Field(default=None, description="Encuadernación del libro: Rústica, Cartoné. Si el usuario menciona que quiere un libro poco pesado, sugerir Rústica aunque nolo diga.")
    categorias: Optional[list] = Field(default=None, description="Temáticas del libro. Infièrelas del título, autor o contexto si el usuario no las menciona. Dejar vacío solo si no hay ninguna pista en la conversación.")
    peso: Optional[float] = Field(default=999, description="Peso aproximado del libro en gramos. No es necesario rellenar esta categoría si no se dan explícitamente.")
    dimensiones: Optional[list] = Field(default=[999,999,999], description="Dimensiones aproximadas (ancho x alto) en milímetros. No es necesario rellenar esta categoría si no se dan explícitamente.")


def llamada_ia(mensaje):


    system_prompt = """Eres un asistente especializado en ayudar a usuarios a encontrar la edición perfecta de un libro.
    Tu tarea es mantener una conversación natural con el usuario y extraer información estructurada sobre el libro que busca.

    REGLAS DE EXTRACCIÓN:
    - Extrae únicamente información que el usuario haya mencionado explícitamente o que puedas inferir con seguridad del contexto.
    - Para las categorías temáticas, infièrelas del contexto si el usuario no las menciona explícitamente.
    - Si el usuario menciona que quiere un libro ligero o para viajar, infiere formato Rústica aunque no lo diga.
    - No inventes información que el usuario no haya dado ni insinuado.

    MANEJO DE AMBIGÜEDAD:
    - Si el usuario pide una antología, recopilación u obra sin título concreto, deja el campo título vacío y extrae solo el autor y las categorías.
    - Si el usuario menciona un título parcial o aproximado, guárdalo tal como lo dice sin intentar completarlo.
    - Si un dato es ambiguo por la naturaleza de lo que busca (antologías, estuches, recopilaciones), no preguntes por él.

    CUÁNDO PREGUNTAR:
    - Pregunta solo si falta autor o una descripción mínima de la obra, ya que sin eso no es posible buscar.
    - No preguntes por formato, peso o dimensiones a menos que el usuario haya mencionado que le importan.
    - Haz una sola pregunta a la vez y de forma natural, no como un formulario.

    {format_instructions}"""

    parser = PydanticOutputParser(pydantic_object=ExtraccionFiltros)

    template_extraccion = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{texto}")
    ])

    fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)

    cadena_extraccion = template_extraccion | llm | parser

    resultado_raw = cadena_extraccion.invoke({
        "texto": mensaje,
        "format_instructions": parser.get_format_instructions()
    })

    resultado = fixing_parser.parse(resultado_raw.content)

    



# Otros modelos: 
# --- Familia Qwen (Alibaba)
# Qwen/Qwen2.5-72B-Instruct — el más capaz, bueno en español y en seguir instrucciones estructuradas
# Qwen/Qwen2.5-7B-Instruct — más ligero y rápido, suficiente para extracción de filtros simples
# --- Familia Llama (Meta)
# meta-llama/Llama-3.3-70B-Instruct — muy bueno siguiendo instrucciones y con structured outputs, buen español
# meta-llama/Llama-3.1-8B-Instruct — versión ligera, para prototipado rápido