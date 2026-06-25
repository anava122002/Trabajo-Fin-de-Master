# ======================================================================================
# ACCESO A API DE OPENLIBRARY
# ======================================================================================

import requests
import json
import pandas as pd
from pathlib import Path
import re


# ======================================================================================
# LECTURA DE DATOS
# ======================================================================================

# --- Contribuidores (editor, traductor...)
def leer_brief(isbn):   

    # Llamada para contribuidores
    url = f"http://openlibrary.org/api/volumes/brief/isbn/{isbn}"

    response = requests.get(url)

    if response.status_code == 200:
        api1 = response.json()

        if api1 == []:
            # No encuentra el libro
            return True
        
        contenido = api1["records"]

        # clave tipo /books/OL9130631M
        clave = list(contenido.keys())[0]
        
        # Edición exacta
        edicion = contenido[clave]["details"]["details"]["edition_name"]

        # Editores
        contribuidores = contenido[clave]["details"]["details"]["contributors"]
        editores = []
        if contribuidores != "":
            for contr in contribuidores:
                if contr['role'] == 'Editor':
                    editores.append(contr["name"])

        # Peso
        peso = contenido[clave]["details"]["details"]['weight']

        # Dimensiones
        dim = contenido[clave]["details"]["details"]['physical_dimensions']

        # Formato
        formato = contenido[clave]["details"]["details"]['physical_format']

        # Categorías
        total_cats = contenido[clave]["data"]["subjects"]
        categorias = []
        for cat_dict in total_cats:
            categorias.append(cat_dict["name"])
        categorias += contenido[clave]["details"]["details"]['subjects']
        categorias.apply(lambda x: x.translate(str.maketrans({"-":"", "/": "", "&": "and"})).strip())
        

    else: 
        raise Exception(f"Conexión denegada. Status {response.status_code}")
    
    return {'edicion': edicion, 'editores': editores, 'peso': peso, 'dim': dim, 'formato': formato, 'categorias': categorias}

# --- Ratings
def leer_ratings(isbn):

    # Llamada para ratings
    url = f"https://openlibrary.org/search.json?isbn={isbn}&fields=rating*"

    response = requests.get(url)

    if response.status_code == 200:
        api2 = response.json()
        ratings = api2["docs"][0]

    else: 
        raise Exception(f"Conexión denegada. Status {response.status_code}")
    
    return ratings

# --- Sinopsis (ver como conseguirla de otro sitio)


# ======================================================================================
# CONTROL DE FLUJO INTERACTIVO
# ======================================================================================

def control_flujo_api(ruta_catalogos="data/catalogos"): # cambiarlo para que te permita elegir cuántos libros hay que 

    print("Iniciando búsqueda en API...")
    catalogos = [f for f in Path(ruta_catalogos).iterdir() if f.is_file()]

    for ruta_cat in catalogos:
        print(f"\nLeyendo {ruta_cat.name}...")

        with open(ruta_cat, "r", encoding="utf-8") as f:
            catalogo = json.load(f)

        if 'openl' in catalogo[0].keys():
            print("Catálogo completo.")
            continue 
        
        key = input("Continuar [Y/N]?")    

        if key=='N':
            continue

        print(f"Comenzando con {ruta_cat.name}. Total de libros a buscar: {len(catalogo)+1}...")
        for libro in range(len(catalogo)):
            print(f"[{libro+1}/{len(catalogo)+1}]")
            ean = catalogo[libro]['ean']

            brief = leer_brief(ean)
            ratings = leer_ratings(ean)

            catalogo[libro].update({
                **brief, 
                **ratings,
                'openl': True
            })
        print("Catálogo terminado.")

        with open(ruta_cat, "w", encoding="utf-8") as f:
                    json.dump(catalogo, f, ensure_ascii=False, indent=2)