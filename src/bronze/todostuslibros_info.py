# ======================================================================================
# OBTENCIÓN DE DATOS (VERSIÓN FINAL Y CORREGIDA)
# ======================================================================================

import os
import json
import csv
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# ======================================================================================
# DRIVER
# ======================================================================================

def crear_driver():
    """Crea y devuelve una instancia de Chrome en modo headless."""

    opciones = Options()
    opciones.add_argument("--headless")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opciones)


# Variable global del driver, se inicializa en control_flujo()
driver = None


# ======================================================================================
# BÚSQUEDA DE CATÁLOGO: EDITORIAL NORMAL (por páginas)
# ======================================================================================

def buscar_editorial(id_editorial, nombre_editorial, pag_inicio, pag_fin):
    """
    Recorre el catálogo de una editorial normal (hasta 200 páginas) iterando de pag_inicio a pag_fin.
    Devuelve los diccionarios con título, autor, precio y URL de cada libro.

    Parámetros:
    * **id_editorial:** el id asignado a la editorial
    * **nombre_editorial:** el nombre de la editorial
    * **pag_inicio:** página del catálogo web donde empezar a hacer scraping
    * **pag_final:** última página del catálogo donde hacer scraping

    Outputs: 
    * Lista de diccionarios con los resultados del scraping
    """
    libros = []
    num_pagina = pag_inicio

    while num_pagina <= pag_fin:
        url = f"https://www.todostuslibros.com/editoriales/{id_editorial}/catalogo?page={num_pagina}"

        # Mostrar progreso solo hasta la página 10 para no llenar la consola
        if num_pagina < 10:
            print(f"Página {num_pagina}...")
        elif num_pagina == 10:
            print("Página 10 y más...")

        driver.get(url)
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        elementos = soup.select("h2 a")

        # Si no hay libros en la página, se acabó el catálogo
        if not elementos:
            print("Sin más resultados.")
            break

        for h2 in soup.select("h2"):
            a = h2.find("a")
            if not a:
                continue

            titulo = a.get_text(strip=True)

            # El autor está en el h3 inmediatamente después del h2
            h3 = h2.find_next_sibling("h3")
            autor = h3.get_text(strip=True) if h3 else ""

            # El precio está en el primer <strong> después del h2
            etiqueta_precio = h2.find_next("strong")
            precio = etiqueta_precio.get_text(strip=True) if etiqueta_precio else ""

            url_libro = a["href"] if a.get("href") else ""

            libros.append({
                "editorial": nombre_editorial,
                "titulo": titulo,
                "autor": autor,
                "precio": precio,
                "url": url_libro,
            })

        num_pagina += 1
        time.sleep(0.5)

    return libros


# ======================================================================================
# BÚSQUEDA DE CATÁLOGO: EDITORIAL GRANDE (por años, para superar el límite de 200 págs)
# ======================================================================================

def buscar_editorial_grande(id_editorial, nombre_editorial, anio_inicio, anio_fin):
    """
    Recorre el catálogo de una editorial grande filtrando por año, lo que permite superar el límite de 200 páginas por búsqueda.
    Para cada año itera todas las páginas disponibles hasta que no haya resultados.
    Devuelve los diccionarios con título, autor, precio y URL de cada libro.

    Parámetros:
    * **id_editorial:** el id asignado a la editorial
    * **nombre_editorial:** el nombre de la editorial
    * **anio_inicio:** página (del año) del catálogo web donde empezar a hacer scraping
    * **anio_final:** última página (del año) del catálogo donde hacer scraping

    Outputs: 
    * Lista de diccionario con los resultados del scraping
    """
    libros = []

    for anio in range(anio_inicio, anio_fin + 1):
        print(f"Año {anio}...")
        num_pagina = 1

        while True:
            url = f"https://www.todostuslibros.com/editoriales/{id_editorial}/catalogo?anios={anio}&page={num_pagina}"
            driver.get(url)
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            elementos = soup.select("h2 a")
            
            # Si no hay libros, este año ya no tiene más páginas
            if not elementos:
                print(f"Sin más resultados en {anio}, página {num_pagina}.")
                break

            for h2 in soup.select("h2"):
                a = h2.find("a")
                if not a:
                    continue

                titulo = a.get_text(strip=True)

                h3 = h2.find_next_sibling("h3")
                autor = h3.get_text(strip=True) if h3 else ""

                etiqueta_precio = h2.find_next("strong")
                precio = etiqueta_precio.get_text(strip=True) if etiqueta_precio else ""

                url_libro = a["href"] if a.get("href") else ""

                libros.append({
                    "editorial": nombre_editorial,
                    "titulo": titulo,
                    "autor": autor,
                    "precio": precio,
                    "url": url_libro,
                })

            num_pagina += 1
            time.sleep(0.5)

    return libros


# ======================================================================================
# EXTRACCIÓN DE FICHA TÉCNICA Y SINOPSIS
# ======================================================================================

def extraer_datos(url):
    """
    Accede a la ficha de un libro y extrae todos los datos técnicos (ISBN, páginas, formato, etc.) y la sinopsis completa.
    Devuelve un diccionario con todos los campos encontrados.

    Parámetros:
    * **url:** link de la página de la ficha técnica

    Outputs: 
    * Diccionario con los resultados del scraping
    """
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # La ficha técnica está dentro de elementos <dl class="datos-tecnicos">
    secciones = soup.find_all("dl", class_="datos-tecnicos")

    nombres = []  # nombres de los campos (dt)
    datos = []    # valores de los campos (dd)

    for seccion in secciones:
        etiquetas_nombre = seccion.find_all("dt")
        etiquetas_dato = seccion.find_all("dd")

        # Extraer nombres de los campos técnicos
        for nombre in etiquetas_nombre:
            nombres.append(nombre.get_text(strip=True).replace(":", "").strip())

        # Extraer valores de los campos técnicos
        # Hay tres posibles estructuras dentro de cada <dd>:
        for dato in etiquetas_dato:

            # Caso 1: el valor está en uno o varios <a> (ej: categorías, editorial)
            enlaces = dato.find_all("a")
            if enlaces:
                lista_valores = [enlace.get_text(strip=True) for enlace in enlaces]
                # Si hay un solo valor lo guardamos como string, si hay varios como lista
                datos.append(lista_valores[0] if len(lista_valores) == 1 else lista_valores)
                continue

            # Caso 2: el valor está en un <span> (ej: idioma)
            span = dato.find("span")
            if span:
                datos.append(span.get_text(strip=True))
                continue

            # Caso 3: el valor está directamente en el <dd> (ej: dimensiones, páginas)
            # Usamos split/join para limpiar espacios y saltos de línea extra
            texto = dato.get_text()
            datos.append(" ".join(texto.split()))

    # Sinopsis completa: está en un div separado fuera de la ficha técnica
    sinopsis = soup.find("div", id="collapseSynopsis")
    nombres.append("Sinopsis")
    if sinopsis:
        # Extraemos párrafo a párrafo y los unimos con " | "
        parrafos = [p.get_text(strip=True) for p in sinopsis.find_all("p")]
        datos.append(" | ".join(parrafos))
    else:
        datos.append("Sin sinopsis")

    # Construir diccionario emparejando cada nombre con su dato
    ficha_tecnica = {}
    for nombre, dato in zip(nombres, datos):
        ficha_tecnica[nombre] = dato

    return ficha_tecnica


# ======================================================================================
# NUEVO SCRAPING
# ======================================================================================

def buscar_editorial_ii(id_editorial, nombre_editorial, pag_inicio, pag_fin):
    """
    Recorre el catálogo de una editorial normal (hasta 200 páginas) iterando de pag_inicio a pag_fin.
    Devuelve los diccionarios con título, autor, precio y URL de cada libro.

    Parámetros:
    * **id_editorial:** el id asignado a la editorial
    * **nombre_editorial:** el nombre de la editorial
    * **pag_inicio:** página del catálogo web donde empezar a hacer scraping
    * **pag_final:** última página del catálogo donde hacer scraping

    Outputs: 
    * Lista de diccionarios con los resultados del scraping
    """
    libros = []
    num_pagina = pag_inicio

    while num_pagina <= pag_fin:
        url = f"https://www.todostuslibros.com/editoriales/{id_editorial}/catalogo?page={num_pagina}"

        # Mostrar progreso solo hasta la página 10 para no llenar la consola
        if num_pagina < 10:
            print(f"Página {num_pagina}...")
        elif num_pagina == 10:
            print("Página 10 y más...")

        driver.get(url)
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        elementos = soup.find_all("article", class_="book-col")

        for el in elementos:
            titulo = el.select_one("p.title").get_text(strip=True)
            autor = el.select_one("p.author").get_text(strip=True)
            precio = el.select_one("div.prices").get_text(strip=True)
            url_libro = el.select_one("p.title a")['href']
        

            libros.append({
                "editorial": nombre_editorial,
                "titulo": titulo,
                "autor": autor,
                "precio": precio,
                "url": url_libro,
            })

        num_pagina += 1
        time.sleep(0.5)

    return libros


# ======================================================================================
# EDITORIAL GRANDE NUEVO
# ======================================================================================

def buscar_editorial_grande_ii(id_editorial, nombre_editorial, anio_inicio, anio_fin):
    """
    Recorre el catálogo de una editorial grande filtrando por año, lo que permite superar el límite de 200 páginas por búsqueda.
    Para cada año itera todas las páginas disponibles hasta que no haya resultados.
    Devuelve los diccionarios con título, autor, precio y URL de cada libro.

    Parámetros:
    * **id_editorial:** el id asignado a la editorial
    * **nombre_editorial:** el nombre de la editorial
    * **anio_inicio:** página (del año) del catálogo web donde empezar a hacer scraping
    * **anio_final:** última página (del año) del catálogo donde hacer scraping

    Outputs: 
    * Lista de diccionario con los resultados del scraping
    """
    libros = []

    for anio in range(anio_inicio, anio_fin + 1):
        print(f"Año {anio}...")
        num_pagina = 1

        while True:
            url = f"https://www.todostuslibros.com/editoriales/{id_editorial}/catalogo?anios={anio}&page={num_pagina}"
            driver.get(url)
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            elementos = soup.find_all("article", class_="book-col")
    
            for el in elementos:
                titulo = el.select_one("p.title").get_text(strip=True)
                autor = el.select_one("p.author").get_text(strip=True)
                precio = el.select_one("div.prices").get_text(strip=True)
                url_libro = el.select_one("p.title a")['href']
        
    
                libros.append({
                    "editorial": nombre_editorial,
                    "titulo": titulo,
                    "autor": autor,
                    "precio": precio,
                    "url": url_libro,
                })

            num_pagina += 1
            time.sleep(0.5)

    return libros



# ======================================================================================
# SCRAPING COMPLETO DE UNA EDITORIAL (búsqueda + fichas + guardado CSV)
# ======================================================================================

def scrapear_editorial(id_editorial, nombre_editorial, inicio, fin, es_grande, nuevo_codigo=True):
    """
    Orquesta el proceso completo para una editorial:
    1. Busca todos los libros del catálogo en el intervalo indicado.
    2. Entra en cada ficha técnica y extrae los datos.
    3. Guarda el resultado en un CSV en la carpeta 'data/'.

    Parámetros:
    * **id_editorial:** identificador de la URL (ej: "debolsillo_179709")
    * **nombre_editorial:** nombre legible (ej: "DEBOLSILLO")
    * **inicio:** página o año de inicio
    * **fin:** página o año de fin
    * **es_grande:** True si es editorial grande (búsqueda por años)

    Output:
    * Archivo .csv con las fichas técnicas de los libros
    """
    print(f"\n{'='*60}")
    print(f"Editorial: {nombre_editorial}")
    print(f"{'='*60}")

    # Fase 1: recoger listado de libros
    print("Leyendo catálogo...")
    if es_grande:
        if nuevo_codigo:
            libros = buscar_editorial_grande_ii(id_editorial, nombre_editorial, inicio, fin)
        else:
            libros = buscar_editorial_grande(id_editorial, nombre_editorial, inicio, fin)
    else:
        if nuevo_codigo:
            libros = buscar_editorial_ii(id_editorial, nombre_editorial, inicio, fin)
        else:
            libros = buscar_editorial(id_editorial, nombre_editorial, inicio, fin)

    print(f"✓ {len(libros)} libros encontrados.")

    if not libros:
        print("No hay libros que procesar.")
        return

    # Fase 2: extraer fichas técnicas
    print("Extrayendo fichas técnicas...")
    lista_libros = []

    for i, libro in enumerate(libros):
        print(f"  [{i+1}/{len(libros)}] {libro['titulo'][:50]}...")

        ficha = extraer_datos(libro["url"] + "#fichaTecnica")

        # Añadir campo traducción si no existe
        if "Traducción" not in ficha:
            ficha["Traducción"] = "Sin traducción"

        # Añadir datos del catálogo a la ficha
        ficha["Título"] = libro["titulo"]
        ficha["Precio"] = libro["precio"]
        ficha["URL"] = libro["url"]

        lista_libros.append(ficha)

    # Fase 3: guardar JSON
    os.makedirs("data", exist_ok=True)
    ruta_json = f"data/bronze/catalogos/catalogo_{nombre_editorial.lower()}.json"
    campos = lista_libros[0].keys()

    # Revisión del catálogo
    if os.path.exists(ruta_json):
        with open(ruta_json, "r", encoding="utf-8") as f:
            libros_existentes = json.load(f)
    else:
        libros_existentes = []

    # Añadir nuevos libros al final
    libros_existentes.extend(lista_libros)

    # Guardar el resultado completo
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(libros_existentes, f, ensure_ascii=False, indent=2)

    print(f"✓ {len(lista_libros)} fichas guardadas en {ruta_json}.")


# ======================================================================================
# CONTROL DE FLUJO INTERACTIVO
# ======================================================================================

def control_flujo(ruta_editoriales="data/json/editoriales.json", ruta_estado="data/json/estado.json"):
    """
    Función principal que gestiona el flujo interactivo del scraping.

    Lee el fichero de editoriales (editoriales.json) con la información de cada una,
    consulta el estado guardado (estado.json) para saber cuáles ya están procesadas,
    y pregunta al usuario qué hacer con cada una.

    Estructura esperada de editoriales.json:
    {
        "debolsillo": {
            "id": "debolsillo_179709",
            "grande": false,
            "intervalo_max": [1, 200]   <- páginas si normal, años si grande
        },
        "espasa": {
            "id": "espasa_76490",
            "grande": true,
            "intervalo_max": [1990, 2024]
        }
    }

    Estructura de estado.json (se genera automáticamente):
    {
        "debolsillo": {
            "ultimo": 200    <- última página/año procesada
        }
    }
    """
    global driver

    # Cargar información de editoriales
    if not os.path.exists(ruta_editoriales):
        print(f"Error: no se encuentra '{ruta_editoriales}'.")
        return

    with open(ruta_editoriales, "r", encoding="utf-8") as f:
        info_editoriales = json.load(f)

    # Cargar estado previo si existe, o empezar desde cero
    if os.path.exists(ruta_estado):
        with open(ruta_estado, "r", encoding="utf-8") as f:
            estado = json.load(f)
    else:
        estado = {}

    # Iniciar el driver una sola vez para toda la sesión
    print("Iniciando navegador...")
    driver = crear_driver()
    print("✓ Navegador listo.\n")

    try:
        for nombre, info in info_editoriales.items():
            maximo = info["intervalo"][1]
            es_grande = info["grande"]
            id_editorial = info["id"]

            # Comprobar si ya está completamente procesada
            if nombre in estado and estado[nombre]["ultimo"] >= maximo:
                print(f"{nombre}: ya procesada completamente, saltando...")
                continue

            # Determinar punto de inicio (desde el principio o desde donde se dejó)
            if nombre in estado:
                ultimo_guardado = estado[nombre]["ultimo"]
                inicio_sugerido = ultimo_guardado+1 # retomamos desde el último guardado
                msg = f"{nombre}: proceso iniciado. Último guardado en {ultimo_guardado}. ¿Continuar? [Y/N]: "
            else:
                inicio_sugerido = info["intervalo"][0]
                msg = f"{nombre}: aún no procesada. ¿Comenzar? [Y/N]: "

            respuesta = input(msg).strip().upper()

            if respuesta == "N":
                print(f"Saltando {nombre}.\n")
                continue

            elif respuesta == "Y":
                # Pedir intervalo al usuario
                tipo = "año" if es_grande else "página"
                print(f"Inicio sugerido: {inicio_sugerido} | Máximo disponible: {maximo}")

                entrada_inicio = input(f"Introduce {tipo} de inicio [{inicio_sugerido}]: ").strip()
                entrada_fin = input(f"Introduce {tipo} de fin (máx. {maximo}): ").strip()

                # Usar valores sugeridos si el usuario no introduce nada
                inicio = int(entrada_inicio) if entrada_inicio else inicio_sugerido
                fin = min(int(entrada_fin), maximo)  # nunca superar el máximo

                # Ejecutar el scraping
                scrapear_editorial(id_editorial, nombre, inicio, fin, es_grande)

                # Actualizar y guardar estado
                if nombre not in estado:
                    estado[nombre] = {}
                estado[nombre]["ultimo"] = fin

                with open(ruta_estado, "w", encoding="utf-8") as f:
                    json.dump(estado, f, ensure_ascii=False, indent=2)

                print(f"Estado guardado: {nombre} → hasta {tipo} {fin}.\n")

            else:
                print("Respuesta no válida, saltando.\n")

    finally:
        # Cerrar el navegador siempre, aunque haya errores
        driver.quit()
        print("\nNavegador cerrado.")

        