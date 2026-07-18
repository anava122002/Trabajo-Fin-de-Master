# Modelo de Datos

## 1. Resumen

La idea seleccionada es un modelo de recomendación que, en base a una serie de necesidades referidas por el usuario, recomiende la edición de entre las registradas en la base de datos que más se ajuste a lo pedido. Estas necesidades pueden ser características físicas del libro como el tamaño, peso o tipo de cubierta, del contenido en el caso de estudios introductorios o anotaciones, o editoriales, de modo que se combinarán los propios metadatos de cada edición con información sobre la calidad de su editorial, sello, autor y traductor en caso de tenerlo. El modelo se presentará como una web con un chatbot que actuará como una interfaz conversacional que recogerá y transformará las necesidades del usuario para seleccionar una recomendación. Esta será devuelta al usuario mostrándole su título, autor, editorial y un breve resumen de cómo encaja con lo que ha pedido.

Los datos se van a obtener mediante scraping y búsuqueda en APIs públicas. Concretamente: 

* [Todos tus Libros](https://www.todostuslibros.com/) para obtener el catálogo de cada editorial. De aquí se obtendrá la ficha técnica de cada libro: ISBN, EAN, título, autor, editorial, sinopsis, traductor, nº páginas, dimensiones y peso.

* [OpenLibrary](https://openlibrary.org/) para complementar los metadatos de los libros. En un principio se pretendía obtener portadas, editores literarios, temáticas y valoraciones de los lectores. Sin embargo, la cobertura de OpenLibrary para el catálogo editorial español ha resultado ser muy limitada: la mayoría de ediciones no tienen entrada registrada por ISBN, lo que ha reducido significativamente la cantidad de datos recuperables por esta vía. Como consecuencia, tanto las portadas como las valoraciones y editores literarios se descartan como fuente al no tener cobertura suficiente para ser representativos del catálogo trabajado. 

* [SPI (Scholarly Publishers Indicators)](https://spi.csic.es/) para la información sobre editoriales. Se recogerá la puntuación de cada editorial, la especialización temática y los criterios de selección de originales.


## 2. Formato de Almacenamiento 

Los datos se van a almacenar de la siguiente forma:

* **Datos sobre las ediciones:** los resultados del scraping se guardarán en archivos json, uno por editorial. La información proporcionada en las diferentes fichas técnicas de Todos tus libros es inconsistente: los datos principales (autor, editorial...) siempre aparecen pero otros como las dimensiones, el peso o el precio suelen no recogerse, especialmente si son antiguas. Guardar los datos en archivos tipo json aporta flexibilidad y facilita la posterior unión y transformación en una tabla estructurada que reuna toda la información y será guardada en formato parquet (mejor que csv para archivos pesados).

* **Datos sobre las editoriales:** la web del SPI permite descargar los datos en varios formatos como png, pdf, tds o csv. La intención principal es descargar como csv los datos y, en caso de no ser posible, extraer la información útil de los otros formatos y guardarla en csv.


## 3. Estructura de Capas de Datos

Los datos se organizarán según la siguiente estructura:

``` 
data/
├── bronze/
|   ├── catalogos/
|   |   └── catalogo_editorial.json     (uno por editorial)
|   └── spi/
|       ├── clasificacion_general.csv
|       ├── clasificacion_tematica.csv      (uno por temática)
|       └── seleccion_originales.csv
├── silver/
|   ├── silver_libros.parquet
|   └── silver_editoriales.csv
├── gold/
|   └── gold_libros.parquet
└── control/        (archivos necesarios para el pipeline de scraping)
    ├── editoriales.json
    └── estado.json
```

## 4. Definición de la Capa Gold

El resultado final de la limpieza y transformación de datos será un único archivo llamado `gold_libros.parquet` que contendrá, fila a fila, la información necesaria de cada libro para construir el posterior modelo de recomendación. Deberá contener, como mínimo, las columnas: 

* **ean:** equivalente al código de barras asignado al ISBN. Será el identificador de cada libro. 
* **titulo:** título del libro.
* **autor:** autor del libro. 
* **anio_publicacion:** año de publicación. 
* **temas:** lista de los temas principales relacionados con el libro. Los temas serán extraídos de OpenLibrary y se pasarán por un LLM que agrupe aquellos que son similares para obtener categorías más robustas, descriptivas y fáciles de normalizar.
* **editorial:** nombre de la editorial codificado.
* **ICEE:** posición de la editorial en la clasificación general del SPI.
* **formato:** formato de edición (rústica o cartoné) codificados. 
* **dimensiones:** altura, ancho y peso. 
* **valoracion:** puntuación (de 1 a 5) dada por los usuarios en OpenLibrary (debería complementarse con el número de personas que han puntuado o el número de votos que tiene cada estrella).


## 5. Relaciones entre los Datos

### 5.1 Obtención de datos: 

Para la obtención de datos se usan tres fuentes diferentes: una web y una API para los libros,y una serie de archivos csv de otra web para las editoriales. Para el último caso simplemente se le asignará un ID a cada editorial (puesto que en los archivos originales no tienen) para poder unir toda la información posteriormente de modo que quede en una única tabla con una fila por editorial.

Para los libros se tomará el EAN (ISBN en formato código de barras) como ID por ser un identificador único y universal (relación 1:1), lo que lo hace compatible también con los criterios de búsqueda de la API. El único problema que puede surgir conectando la información de ambas fuentes de esta forma es que la API no contenga algún libro de los recogidos de la web, en cuyo caso (poco común con libros de menos de 30 años) el libro se descartará.

### 5.2 Capa Silver:

Una vez transformados los catálogos de cada editorial en una tabla, ésta estará relacionada a la de editoriales mediante su ID, que ya fue recogido para poder hacer el scraping editorial a editorial en una relación 1:N. En principio, esta relación no debería ocasionar ningún problema.


## 6. Diccionario de Datos Inicial

|   Campo         |              Descripción                 | Tipo de Dato |                     Fuente                                  | Obligatorio | Observaciones |
|   :---          |                 :---:                    |    :---:     |                     :---:                                   |    :---:    |   :---:       |
|   **titulo**    |                                          |     str      | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
|    **autor**    |                                          |     str      | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
| **editorial**   |                                          |     int      | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
|   **formato**   |                                          |     str      | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
|**dimensiones**  |                                          |    float     | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |Viene dado como 'a x b x c'. Será transformado en tres columnas', una por medida|
|   **peso**      |                                          |    float     | [Todos tus Libros](https://www.todostuslibros.com/)         | No          |
| **rating_avg**  |                                          |    float     | [OpenLibrary](https://openlibrary.org/)                     | Sí          |Como depende de OL, en caso de no obtenerse se descarta o se busca una alternativa|
|**rating_count** |                                          |     int      | [OpenLibrary](https://openlibrary.org/)                     | No          |Como depende de OL, en caso de no obtenerse se descarta o se busca una alternativa|  
| **icee_general**|                                          |     int      |[SPI (Scholarly Publishers Indicators)](https://spi.csic.es/)| Sí          |
|   **icee_cat**  |                                          |     int      |[SPI (Scholarly Publishers Indicators)](https://spi.csic.es/)| No          | 
|   **precio**    |                                          |    float     | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
|**cat_principal**|                                          |     list      |[SPI (Scholarly Publishers Indicators)](https://spi.csic.es/)| Sí          |  
|   **subcat**    |                                          |     list      | [OpenLibrary](https://openlibrary.org/)                     | No          |Como depende de OL, en caso de no obtenerse se descarta o se busca una alternativa|  
|   **portada**   |                                          |     str      | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |Será el link de búsqueda de la portada|    


## 7. Problemas de Calidad Esperados

* **Valores nulos**: el problema más extendido en el dataset es la ausencia de datos físicos de las ediciones. Los campos de dimensiones, peso y precio están frecuentemente vacíos, especialmente en ediciones anteriores a los años 2000, donde la ficha técnica de Todos tus Libros es mucho más escueta. Se estima que más del 50% de los registros tendrán al menos uno de estos tres campos vacío. El traductor también es un campo con alta tasa de nulos, ya que solo aplica a obras traducidas y no siempre se registra aunque la traducción exista. Las valoraciones de OpenLibrary, al tener cobertura muy limitada para el catálogo español, serán nulas en la gran mayoría de registros y se tratarán como campo opcional.

* **Inconsistencia en nombres y categorías**: los nombres de los autores no siguen un formato homogéneo: algunos aparecen como "Nombre Apellido", otros como "Apellido, Nombre" y en algunos casos se incluyen títulos honoríficos o iniciales. Lo mismo ocurre con los nombres de las editoriales, que pueden variar entre registros ("Editorial Planeta", "PLANETA", "Planeta") dificultando el cruce con los datos del SPI. Las categorías temáticas son el campo más heterogéneo del dataset: combinan entradas en español e inglés, distintos niveles de especificidad, términos redundantes y etiquetas que no son categorías temáticas sino descriptores de colección o de formato.

* **Sesgos de cobertura**: el catálogo de Todos tus Libros está orientado al mercado español actual, lo que implica una sobrerrepresentación de ediciones recientes y de los sellos de las grandes editoriales (Planeta, Penguin Random House, Anaya) frente a editoriales independientes o especializadas. Las ediciones antiguas o descatalogadas tienen una presencia muy reducida. OpenLibrary tiene el sesgo opuesto: mejor cobertura de obras clásicas y del catálogo anglosajón, y cobertura muy limitada de ediciones españolas contemporáneas.

* **Datos extremos u outliers**: se esperan outliers en el campo de número de páginas (libros de una sola página por error de registro, o enciclopedias con miles), en el peso (estuches o ediciones especiales con pesos muy elevados) y en el precio (ediciones de lujo o coleccionista con precios muy por encima de la media). Estos casos son reales y no necesariamente errores, por lo que requieren análisis caso a caso antes de decidir si se descartan o se mantienen.

* **Problemas al cruzar fuentes**: el cruce entre Todos tus Libros y el SPI se hace por nombre de editorial, que como se ha señalado es inconsistente.

* **Campos relevantes no disponibles**
Las portadas, inicialmente previstas como campo de la capa gold, no han podido obtenerse de forma sistemática por la limitada cobertura de OpenLibrary para el catálogo español. Las valoraciones de lectores tienen el mismo problema. El editor literario, relevante para ediciones críticas o académicas, tampoco está disponible en caso de no tener registro en OpenLibrary.


## 8. Decisiones de Limpieza y Transformación Previstas

* **Tratamiento de valores nulos**: los registros sin título, autor o EAN se eliminarán por ser datos imprescindibles. Para el resto de campos nulos la estrategia varía según el campo: dimensiones, peso y precio se intentarán imputar usando la mediana o el valor más frecuente dentro del mismo grupo editorial y colección, ya que libros de una misma colección suelen tener características físicas homogéneas. Los campos que no puedan imputarse de forma razonable se mantendrán como nulos y se excluirán de los criterios de filtrado activos cuando el usuario no los mencione explícitamente.

* **Normalización de texto**: los nombres de autores y editoriales se normalizarán a formato "Nombre Apellido" en minúsculas con la primera letra en mayúscula. Los nombres de editoriales se mapearán a un nombre canónico mediante un diccionario de equivalencias construido manualmente para los casos más frecuentes, necesario para el cruce con el SPI.

* **Normalización de fechas**: se convertirán todas las fechas al formato datetime de pandas, usando `errors='coerce'` para convertir en nulo las fechas que no puedan parsearse. De la fecha completa se extraerá únicamente el año de publicación como variable numérica.

* **Normalización de unidades**: las dimensiones se convertirán a milímetros y se almacenarán cada una en una columna.. El peso se almacenará en gramos como valor numérico. El precio se convertirá a float usando punto decimal. Los registros con valor "Más información" en el campo precio se tratarán como nulos.

* **Normalización de categorías**: as categorías temáticas se procesarán en dos niveles. Para la categoría principal se usará la taxonomía del SPI como vocabulario controlado, asignando a cada libro la categoría de su editorial. Las subcategorías se tomarán las categorías de Todos tus Libros y se transformarán a lista en el caso de ser `str`.

* **Variables derivadas**: se construirán las siguientes variables derivadas: año de publicación extraído de la fecha completa, superficie de la edición calculada como ancho × alto para facilitar comparaciones de tamaño, y URL de portada construida a partir de las URLs usadas para el scraping.

* **Criterios de validez de un registro**: se considerará válido un registro que tenga al menos título, autor, EAN y editorial. Los registros sin estos cuatro campos se eliminarán. El resto de campos ausentes no invalidan el registro pero pueden reducir su relevancia en el recomendador si el usuario filtra por esos criterios.


## 9. Riesgos del Modelo de Datos

La estructura de la capa bronze está bien definida y el pipeline de scraping funciona de forma estable. El esquema de la capa gold es claro en cuanto a qué campos se necesitan y de dónde vienen. La relación entre libros y editoriales mediante ID es sencilla y no genera ambigüedad. La mayor incertidumbre del modelo reside en la alta tasa de valores nulos en campos relevantes. La limitada cobertura de OpenLibrary para el catálogo editorial español ha dejado sin datos de portadas y valoraciones a la gran mayoría de registros, campos que estaban previstos como parte de la capa gold. A esto se suma que los campos físicos (dimensiones, peso, precio) tienen una tasa de ausencia elevada en ediciones antiguas, lo que puede comprometer la capacidad del recomendador para filtrar por criterios físicos en una parte significativa del catálogo.

De las fuentes, OpenLibrary ha sido la fuente más problemática: la cobertura del catálogo editorial español es muy inferior a la esperada, lo que ha obligado a descartar campos que estaban previstos como obligatorios en el diseño inicial (portadas, valoraciones, editor literario). El SPI puede dar problemas en el cruce por nombres de editoriales si las equivalencias no están bien mapeadas. Si OpenLibrary no puede aportar datos suficientes, el recomendador perdería los campos de valoraciones de usuarios y parte de la información sobre las ediciones. En ese caso, la evaluación de calidad de una edición recaería principalmente en los indicadores del SPI, que aportan información sobre el prestigio y la especialización temática de cada editorial. El sistema seguiría siendo funcional para el caso de uso principal, pero la recomendación se basaría más en criterios editoriales objetivos que en la valoración directa de los lectores.

Si fuera necesario simplificar el modelo, la alternativa más viable sería construir el recomendador únicamente sobre los datos obtenidos de Todos tus Libros y el SPI, prescindiendo de OpenLibrary por completo (en caso de no encontrar una fuente alternativa fiable). Todos tus Libros aporta los metadatos físicos y editoriales de cada edición (autor, formato, dimensiones, peso, precio, traductor y categorías temáticas propias), mientras que el SPI aporta los indicadores de calidad editorial. Esta combinación es suficiente para el caso de uso principal del proyecto y tiene la ventaja de que ambas fuentes han demostrado ser fiables y con buena cobertura del catálogo español, a diferencia de OpenLibrary.