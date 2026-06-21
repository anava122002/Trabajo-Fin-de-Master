# Lista de ideas para el TFM 
 
Estas son las tres ideas que más interesantes me han parecido de todas las que he estado 
considerando: 
 
-  **Automatización  de  procesos  contables:**  la  idea  viene  de  mi  tío,  que  tiene  una 
correduría y emplea mucho tiempo en hacer tareas repetitivas y tediosas como recopilar 
documentación, rellenar documentos, preparar declaraciones de la renta... La idea sería 
automatizar la mayor parte del trabajo con técnicas de scripting para que solo tenga que 
revisar el documento final. El principal problema es la obtención de datos, tanto por 
privacidad como por cómo los guarda (generalmente en formato físico). 
 
-  **Recomendador  de  ediciones  según  necesidades  del  lector:**  esta  idea  viene  de 
varios sitios, pero hay dos focos principales. El primero es que, cuando empecé a leer 
libros más complejos y que en algunos casos necesitaban de una buena traducción o 
contextualización previa (me solía pasar sobre todo con el teatro griego), me di cuenta 
de que había que ser cuidadoso con la edición que compras pues en muchas ocasiones 
tenía que recurrir a internet para entender la historia completa. El otro son mis tías, que 
si bien les gusta leer en formato físico, no pueden leer cierto tipo de libros grandes o 
pesados por problemas en las articulaciones. La idea es un programa que recomiende 
libros según un scoring basado en criterios editoriales y académicos (para asegurar la 
calidad) y las propias necesidades del lector. Los datos pueden ser extraídos de APIs 
públicas  (como  OpenLibrary)  y  scrapping  de  las webs de las principales editoriales 
españolas. 
 
-  **Detector de contradicciones en un texto:** muchas empresas manejan gran cantidad 
de  documentos  que  pueden  contener  cláusulas  contradictorias,  ambigüedades  o 
incoherencias.  Lo  mismo  pasa  con  artículos  de  prensa,  argumentos  usados  en 
programas de tertulias... La idea es un programa de NLP que segmente el texto en 
unidades semánticas relacionadas mediante un grafo dirigido y detecte contradicciones 
analizando la coherencia global del texto mediante el análisis del espectro de su matriz 
de adyacencia (lo cual va en concordancia con el tema de mi TFG, de ahí la idea). Los 
datos para entrenar el modelo pueden ser extraídos de datos públicos (BOEs, Portal de 
Transparencia...).