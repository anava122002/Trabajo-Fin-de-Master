# Idea para el TFM. Datos Necesarios

## 1. Idea Seleccionada

La idea seleccionada para el TFM es un recomendador  de  ediciones  según  necesidades  del  lector. Cuando se lee en formato físico, la edición elegida 
condiciona la experiencia de lectura tanto para bien si se adapta a nuestras necesidades como para mal si el formato es demasiado grande o pesado, carece de suficientes elementos paratextuales (en caso de necesitarlos) para su correcta compresión o si es, en general, una mala edición desde el punto de vista técnico.

El objetivo es crear un modelo de recomendación que, en base a una serie de necesidades referidas por el usuario, recomiende la edición de entre las registradas en la base de datos que más se ajuste a lo pedido. Estas necesidades pueden ser características físicas del libro como el tamaño, peso o tipo de cubierta, del contenido en el caso de estudios introductorios o anotaciones, o editoriales, de modo que se combinarán los propios metadatos de cada edición con información sobre la calidad de su editorial, sello, autor y traductor en caso de tenerlo.

El modelo se presentará como una web con un chatbot que actuará como una interfaz conversacional que recogerá y transformará las necesidades del usuario para seleccionar una recomendación. Esta será devuelta al usuario mostrándole su título, autor, editorial y un breve resumen de cómo encaja con lo que ha pedido. La inspiración viene de [Gnooks](https://www.gnooks.com/faves.php) (y otras páginas del mismo autor).


## 2. Datos Necesarios

Para una primera versión del proyecto, lo ideal sería contar con la mayor parte de la oferta actual de los diferentes sellos de las editoriales más grandes de España, como pueden ser Planeta, Peguin Random House o Anaya. De cada edición en particular se buscará como mínimo:

* **Metadatos básicos de la obra:** título, idioma, autor, fecha de publicación...
* **Específicos de la edición:** nº páginas, dimensiones, tapas, precio...
* **Valoración de consumidores**
* **Información sobre su sello:** ICEE general y especialización temática (también podría incluirse la selección de originales como validación de calidad)


## 3. Fuentes de Datos Previstas

Los datos se van a obtener mediante scraping y búsuqueda en APIs públicas. Concretamente: 

* [Todos tus Libros](https://www.todostuslibros.com/) para obtener el catálogo de cada editorial. La mayor ventaja es que es mucho más fácil de scrapear que las webs oficiales de las editoriales e incluye igualmente la mayor parte de sus publicaciones. Es bastante limitado en cuestión de valoraciones de usuarios, especialmente para libros más antiguos.
* [OpenLibrary](https://openlibrary.org/) para complementar los metadatos de las ediciones y añadir las valoraciones de consumidores. Cada item de OpenLibrary tiene su propia API y cada API una documentación bastante extensa, de modo que es una fuente esencial para completar el dataset que se va a usar en el modelo.
* [SPI (Scholarly Publishers Indicators)](https://spi.csic.es/) para la información sobre editoriales. El SPI es un sistema que aporta información de apoyo en los procesos de evaluación de la actividad científica y realiza estudios sobre la edición académica española que integra a sellos editoriales pequeños, medianos y grandes, universitarios, comerciales/privados e institucionales.


## 4. Privacidad y Protección de Datos

Los datos que se van a usar no contienen información sensible ni con copyright. Los metadatos bibliográficos en sí  los genera la editorial, están registrados en bases de datos bibliográficas internacionales, y son por naturaleza información factual y pública. Los datos de las APIs y del SPI son también de libre uso y la valoración de los clientes se recogerá en forma de métricas, de modo que tampoco habría problemas. 

El único inconveniente puede venir por esta claúsula de los términos y condiciones de *Todos tus Libros*: los textos, imágenes, sonidos, animaciones, software y el resto de contenidos incluidos en este website son propiedad exclusiva de CEGAL o sus licenciantes. Cualquier acto de transmisión, distribución, cesión, reproducción, almacenamiento o comunicación pública total o parcial, deberá contar con el consentimiento expreso de CEGAL. Por otra parte, La legislación española (Ley de Propiedad Intelectual, art. 67) y el Reglamento europeo de IA y datos permiten el uso de datos públicamente accesibles con fines de investigación sin ánimo de lucro, además de que *CEGAL* es un proyecto financiado con dinero público del Ministerio de Cultura cuyo objetivo declarado es precisamente la difusión del libro. Usar sus datos para un proyecto académico sobre recomendación de ediciones está alineado con su misión institucional, no en contra.


## 5. Viabilidad Inicial del Proyecto

Puesto que ya se ha empezado el proceso de obtención de datos y se han superado todas las dificultades que han ido surgiendo, los pricipales problemas que pueden poner en riesgo la viabilidad del proyecto son: 
* **Cambios en la estructura HTML de [Todos tus Libros](https://www.todostuslibros.com/)**: habría que rehacer todo el código que obtiene la información principal del proyecto. Este, por su estructura actual, está adaptado por necesidad para que distinga entre editoriales grandes (+20.000 ediciones) y pequeñas mediante un JSON, leyendo el HTML de forma diferente en cada caso y almancenando los avances en un JSON para que el scraping pueda ser intermitente (si no serían horas de espera).

* **Posibles problemas con los ISBN como identificador:** puede darse el caso de que algún ISBN esté mal registrado en *Todos tus Libros* y por tanto no se pueda encontrar en la API de *OpenLibrary*. Sería necesario buscar un backup para estos casos y alguna forma de validad la corrección del ISBN.

* **Viabilidad del modelo en sí:** trabajar sin conocer información previa del usuario resta sofisticación al modelo y la identificación de necesidades recaerá entera sobre el chatbot y la información que el usuario crea conveniente aporte. 

* **Volumen de datos:** si no se delimita la cantidad de datos suficientes para hacer una demostración el proyecto tiene el riesgo de crecer demasiado, por eso se toman únicamente las editoriales más grandes.