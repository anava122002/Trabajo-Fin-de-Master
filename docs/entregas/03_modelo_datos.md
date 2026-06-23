# Modelo de Datos

## 1. Resumen

La idea seleccionada es un modelo de recomendación que, en base a una serie de necesidades referidas por el usuario, recomiende la edición de entre las registradas en la base de datos que más se ajuste a lo pedido. Estas necesidades pueden ser características físicas del libro como el tamaño, peso o tipo de cubierta, del contenido en el caso de estudios introductorios o anotaciones, o editoriales, de modo que se combinarán los propios metadatos de cada edición con información sobre la calidad de su editorial, sello, autor y traductor en caso de tenerlo. El modelo se presentará como una web con un chatbot que actuará como una interfaz conversacional que recogerá y transformará las necesidades del usuario para seleccionar una recomendación. Esta será devuelta al usuario mostrándole su título, autor, editorial y un breve resumen de cómo encaja con lo que ha pedido.

Los datos se van a obtener mediante scraping y búsuqueda en APIs públicas. Concretamente: 

* [Todos tus Libros](https://www.todostuslibros.com/) para obtener el catálogo de cada editorial. De aquí se obtendrá la ficha técnica de cada libro: ISBN, EAN, título, autor, editorial, sinopsis, traductor, nº páginas, dimensiones y peso.

* [OpenLibrary](https://openlibrary.org/) para complementar los metadatos de los libros, principalmente las portadas, editores, temáticas y las valoraciones de los lectores. 

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
|   **formato**   |                                          |     int      | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
|**dimensiones**  |                                          |    float     | [OpenLibrary](https://openlibrary.org/)                     | Sí          |
|   **peso**      |                                          |    float     | [OpenLibrary](https://openlibrary.org/)                     | No          |
| **rating_avg**  |                                          |    float     | [OpenLibrary](https://openlibrary.org/)                     | Sí          |
|**rating_count** |                                          |     int      | [OpenLibrary](https://openlibrary.org/)                     | No          |  
| **icee_general**|                                          |     int      |[SPI (Scholarly Publishers Indicators)](https://spi.csic.es/)| Sí          |
|   **icee_cat**  |                                          |     int      |[SPI (Scholarly Publishers Indicators)](https://spi.csic.es/)| No          | 
|   **precio**    |                                          |    float     | [Todos tus Libros](https://www.todostuslibros.com/)         | Sí          |
|**cat_principal**|                                          |     int      |[SPI (Scholarly Publishers Indicators)](https://spi.csic.es/)| Sí          |  
|   **subcat**    |                                          |     int      | [OpenLibrary](https://openlibrary.org/)                     | No          |        