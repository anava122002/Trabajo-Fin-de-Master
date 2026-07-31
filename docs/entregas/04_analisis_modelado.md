# Análisis de Modelado

## 0. Aclaraciones y Modificaciones de Decisiones Previas

1. **Cuándo una edición se considera mejor que otra:**

La calidad de una edición, según se ha considerado para este proyecto, puede evaluarse de tres formas:

* **Calidad material:** depende de las dimensiones, peso, número de páginas, encuadernación, colección y precio.

* **Calidad editorial:** el aparato crítico (prólogo, introducción, estudio previo, anotaciones...), sus colaboradores y el prestigio de éstos.

 * **Necesidades del usuario:** pueden ser de tamaño, contenido, precio...

Una edición será mejor que otra en tanto que se adapate a las necesidades del usuario manteniendo o mejorando tanto como sea posible la calidad de material y editorial. 

Por ejemplo, supongamos que tenemos dos ediciones de un mismo libro, una de ellas perteneciente a una colección low-cost de una editorial reconocida (materiales de calidad media y precio bajo pero a nivel editorial excelente) y la otra una edición  ilustrada para colección de una editorial pequeña y poco conocida (materiales de buena calidad, precio alto y sin aparato crítico). Para un usuario que busca una edición sobre la que trabajar la obra será mejor la primera opción aunque se prescinda de la calidad, mientras que para otro que busque una edición vistosa o para regalo será mejor la segunda aunque la calidad editorial no sea la mejor.

Si, por otra parte, os ediciones presentan características muy similares para las necesidades del usuario (pertenecen a colecciones de nivel comparable, tienen un formato y un precio parecidos y ambas satisfacen sus requisitos) se elegirá aquella con mejor calidad material y editorial.la calidad editorial y material pasa a convertirse en el criterio de desempate. En estos casos, el recomendador priorizará la edición que ofrezca un mayor prestigio editorial, mejores materiales o ambas cualidades, favoreciendo, por ejemplo, una edición de Cátedra frente a otra de Alianza si el resto de características relevantes son equivalentes.

2. **Contradicciones en la capa gold y alternativas a OpenLibrary:**

Hay variables que en un principio se habían considerado necesarias y que, por no poder usar la API de OpenLibrary, finalmente no van a poder usarse. Este es el caso de las valoraciones. Como ni siquiera se tiene acceso a ellas se van a descartar completamente.

En el caso de dimensiones como el alto, ancho, peso, grosor o precio, el uso de fórmulas estándar y datos de ediciones de la misma colección o medidas han ayudado a recuperar más del 50% de las entradas nulas. Puesto que son medidas esenciales para evaluar la calidad material y, tras el proceso de imputación, están disponibles en más del 90 % de los registros, se ha considerado conveniente conservarlas en la capa Gold.

Finalmente, aunque no se han podido extraer de OpenLibrary todos los colaboradores de cada edición, sí que se tienen registros sobre anotaciones, prólogos y demás proveniente de Todos tus Libros. De aquí se puede obtener información que complemente al SPI, como el número de piezas que forman el aparato crítico de la edición, el total de colaboradores o la frecuencia con la que colaboran.

3. **Replanteamiento del uso del SPI:**

El SPI proporciona información sobre la calidad de la selección y tratamiento de los textos por parte de las diferentes editoriales, ordenándolas en un ranking según su puntuación. Esta información dejará de utilizarse como un indicador directo de la calidad de una edición para, en su lugar, usarla para medir el prestigio de la editorial en las distintas áreas de conocimiento. Las categorías específicas obtenidas de Todos tus Libros se normalizarán en un conjunto de categorías generales (filosofía, derecho, narrativa, historia, etc.) compatibles con las áreas del SPI (las categorías iniciales pasarán a ser subcategorías). De este modo, el prestigio editorial se evaluará en función de la disciplina del libro, evitando asignar automáticamente a todas las obras la especialización de su editorial.

El prestigio en cada categoría se calcula como sigue: 

**prestigio = 0.1 + 0.9 * (0.8 * icee_norm + 0.2 * percentil)**

siendo `icee_norm` la puntuación otorgada por el SPI normalizada (no todas las categorías tienen las mismas escalas) y `percentil` el percentil de la posici´pn de la editorial en el ranking.

## 1. Problema que se Busca Resolver

Actualmente, la amplia oferta editorial disponible tanto en tiendas web como físicas puede abrumar a los lectores y dificultar la elección de una edición adecuada. La idea principal del proyecto es identificar las necesidades específicas del usuario y tomarlas como punto de partida para presentarle a continuación las ediciones del libro que buscan que más se adapten a ellas, empleando la calidad editorial y material como criterio de priorización entre las alternativas más adecuadas. 

El resultado esperado es una recomendación de hasta tres ediciones (si las hay) del libro buscado o, en caso de no buscar un título concreto sino una recopilación de textos o temáticas concretas (como puede ser el caso de una antología, colección de obras, guía...), la identificación de aquellos libros cuyas ediciones se ajusten mejor a sus necesidades.

## 2. Análisis de Datos y Utilidad Esperada

Puesto que vamos a tratar con un modelo de predicción, el objetivo del análisis previo a la construcción del modelo es conocer el catálogo y comprobar que, efectivamente, puede ser usado con dicho fin.

Por una parte, es necesario conocer la distribución de los datos recogidos: de las categorías, formatos y encuadernaciones, precios, dimensiones, idiomas y traducciones, aparato crítico y prestigio editorial. Por otra, es necesario conocer la cobertura actual de cada variable y desarrollar una estrategia que permita tanto + imputar el máximo número de datos faltantes posibles como extraer nueva información útil.

Además, es necesario saber si existen suficientes ediciones distintas de un mismo título como para que el recomendador tenga sentido. Hay casos en los que es evidente que esta condición se cumple, como puede ser para títulos muy populares o clásicos, pero para la gran mayoría de los casos esto no es así. Un caso a parte son aquellos libros cuyo interés reside en su contenido más que en un título concreto, como antologías, manuales, guías o recopilaciones. Para este tipo de búsquedas, la temática y las características de la obra adquieren mayor relevancia que el título, ampliando así el conjunto de alternativas que pueden recomendarse.

### 2.1 Proposición de Datos Complementarios

Como prevención a este problema y para mostrar una dimensión mayor de las posibilidades del modelo propuesto, se ha pensado en hacer una selección de ediciones del dataset final y simular con ellas lo que sería el catálogo de una web de segunda mano como IberLibro, Agapea o Todocolección. No sería un sustituto del dataset principal, sino un complemento que ayudaría a:

* **Aportar un margen mayor de actuación:** decenas de ediciones con cientos de ejemplares de cada una, todas con diferentes estados de conservación, precios y librerías.

* **Evaluar el modelo:** la simulación sería un banco de pruebas que ayudaría a compribar si el modelo filtra correctamente, prioriza la calidad cuando corresponde o tiene elementos ajenos al libro como la valoración de la librería que lo vende o los gastos de envío.

* **Demostrar escalabilidad:** si el modelo sigue funcionando normalmente con un número elevado de ejemplares de cada libro.

## 3. Tipos de Modelos que se van a Plantear

Como los datos incluyen información sobre las ediciones pero no sobre anteriores compras o preferencias de otros clientes, será necesario recurrir a un modelo de recomendación content-based, a un modelo knowledge-based o a un híbrido. La estrategia a seguir es la siguiente:

1. Un agente LLM extrae las necesitades del usuario conversando con él.

2. Se aplican filtros duros (título, autor, presupuesto...).

3. Los datos resultantes pasan por un sistema de puntuación multicriterio que englobe los criterios de calidad mencionados anteriormente.

4. Se muestra al usuario el top 3 del ranking.

Se consideran los siguientes modelos

| Modelo | Descripción | Ventajas | Limitaciones |
| :---:  |   :---      | :---     | :---         |
| **Recomendación basada en contenidos** | Cada elemento se representa como un vector de características y se comparan mediante alguna medida de similitud | Existen varias medidas que pueden usarse, aunque en este caso se daría prioridad a la similitud de Gower por permitir usar datos numéricos, categóricos y booleanos | No contempla la prioridad que el usuario da a unas variables sobre otras |
| **Recomendación híbrida contenido + pesos** | Otorga una peso a cada variable según las necesidades especificadas por el ususario antes de calcular la similitud | Elimina el problema del modelo anterior | Los pesos están predefinidos para cada uso por lo que no se ajustan al usuario completamente. Además, deben decidirse al momento de implementar el modelo por no tener datos de clientes reales |
| **Sistema experto** | Se defienen reglas complejas que ayuden al modelo a "pensar". Por ejemplo, si el usuario busca estudiar y existe aparato crítico aumenta mucho la valoración; si existen dos ediciones similares se elige la de mayor prestigio | Las reglas basadas en conocimiento real ayudan a ajustar los resultdos del modelo a decisiones de usuarios reales, elimiando parcialmente el problema anterior | Exige definir y justificar muchas reglas |


Además, al modelo elegido se le aplicaría una capa de explicabilidad para que el usuario reciba los resultados junto con una justificación de cada uno y una breve comparación. 

## 4. Datos de Entrada en el Análisis y los Modelos

Los datos de entrada tanto para el análisis como para el modelo serán los de la tabla `gold_ediciones`. Cada una de sus filas contiene información integrada de Todos tus Libros y el SPI sobre una edición de un libro, además de las generadas durante el proceso de ETL. El ISBN de cada libro actúa como identificador único, siendo esta la única columna que no puede tener valores repetidos. 

A continuación se describen las variables de la tabla y su función (análisis, filtro y/o modelo):

| Nombre de Variable | Tipo | Uso | Obtención | Descripción General | 
|       :---        | :--- |:--- |   :---    |     :---            |
|**ean**| Numérica (int) | | TTL | Identificador de cada edición
| **titulo** | Texto (str) | Análisis y Filtro | TTL | Nombre de la edición |
| **autor** | lISTA | Análisis y Filtro | TTL | Autor(es) principal(es) de la obra |
| **editorial** | Texto (str) | Análisis | TTL | Editorial que publica la edición |
| **coleccion** | Texto (str) | Análisis | TTL | Colección a la que pertenece la edición |
| **idioma_publicacion** | Texto (str) | Análisis y Filtro | TTL | Idioma |
| **idioma_publicacion** | Texto (str) | Análisis y Filtro | TTL | Idioma original |
| **fecha_publicacion** | Fecha | Análisis y Filtro | TTL | Día en que fue publicada |
| **img** | Texto (str) | | Cálculo Propio | URL de la portada |
| **categoría** | Texto (str) | Análisis y Filtro | Cálculo propio | Inferencia de la categoría principal de las subcategorías extraídas de TTL. Se corresponden con las categorías propuestas por el SPI |
| **subcategorias** | Lista | Análisis y Filtro | TTL | Categorización más específica de la obra |
| **encuadernacion** | Texto (str) | Análisis | TTL | Formato físico de la edición |
| **n_pags** | Numérica (int) | || TTL Total de páginas |
| **alto_mm** | Numérica (float) | Análisis | TTL | Alto del libro físico en milímetros |
| **ancho_mm** | Numérica (float) | Análisis | TTL | Ancho del libro físico en milímetros |
| **grosor_mm** | Numérica (float) | Análisis | Cálculo propio | Grosor del libro físico en milímetros |
| **peso_g** | Numérica (float) | Análisis | TTL | Peso del libro físico en gramos |
| **precio** | Numérica (float) | Análisis | TTL | Precio del libro en euros |
| **indice_portabilidad** | Numérica (float) | Modelo | TTL | Mide cómo de cómodo es tratar con el libro (relación dimensión, peso, grosor) |
| **indice_compacidad** | Numérica (float) | Modelo | TTL | Mide cuánta información/texto ofrece en relación al espacio que ocupa |
| **indice_prestancia** | Numérica (float) | Modelo | TTL | Sensación de importancia o presencia puedetransmite la edición (especialmente pensada para identificar ediciones especiales para regalo, colección...) |
| **aparato_critico** | Booleana | Todas | Cálculo propio | Indica si la edición cuenta con aparato crítico/ textos complementarios |
| **textos_complementarios** | Lista | Análisis | TTL | Textos complementarios que componen el aparato crítico |
| **otros_colaboradores** | Lista | Análisis | TTL | Nombres de los colaboradores (que no son ni autor ni traductor) |
| **score_critico** | Numérica (float) | Modelo | Cálculo propio | Mide la relevancia del aparato crítico |
| **score_colaboradores** | Numérica (float) | Modelo | Cálculo propio | Mide la relevancia del aparato crítico de una edición en base a la de sus colaboradores |
| **prestigio_general** | Numérica (float) | Modelo | Cálculo propio | Mide el prestigio de una editorial según su posición del ranking y la puntuación dada por el SPI |
| **prestigio_cat** | Numérica (float) | Modelo | Cálculo propio | Mide el prestigio de una editorial en una categoría según su posición del ranking y la puntuación dada por el SPI |
| **es_escolar** | Booleana | Análisis y Filtro | Cálculo propio | Indica si una edición está pensada para el ámbito escolar (principalmente libros de texto) |
| **es_adaptada** | Booleana | Análisis y Filtro | Cálculo propio | Indica si el texto de una edición ha sido adaptado a un público concreto |
| **es_ilustrado** | Booleana | Análisis y Filtro | Cálculo propio | Indica si el texto de una edición es ilustrada |
| **formato_fisico** | Texto (str) | Análisis y Modelo | TTL | Indica si es un único tomo, una colección, un estuche... |

## 5. Datos de Salida y Forma de Consumo

Al ser un modelo de recomendación, la salida será un ranking con el identificador (ISBN/EAN) y una score para cada edición según su ajuste a los criterios acompañada de una explicación textual de los resultados. El top 3 será devuelto por el modelo como un diccionario de modo que sirva de contexto para el agente encargado de presentarlo al usuario en la aplicación.

Este diccionario contendrá también otro tipo de información sobre la edición, como título, autor, edición y portada, para que el usuario sea capaz de identificarla fácilmente, comparar las alternativas y tomar una decisión por sí mismo.

## 6. Estrategia para Diseñar y Seleccionar el Modelo

El proceso de modelado partirá de la tabla final de la capa Gold. Antes de aplicar los distintos modelos se eliminarán las variables no necesarias, se normalizarán las variables numéricas cuando sea necesario, y se codificarán las variables categóricas, transformando aquellas compuestas por listas (subcategorías, colaboradores o textos complementarios) a una representación adecuada para el cálculo de similitudes. No será necesario realizar tratamientos adicionales sobre valores nulos, ya que estos habrán sido resueltos durante la construcción de la capa Gold. A diferencia de un problema clásico de clasificación o regresión, el proyecto no dispone de una variable objetivo conocida, sino que pretende generar un ranking de ediciones ordenadas según su adecuación a las preferencias expresadas por el usuario. Cada edición recibirá un score de recomendación, utilizado únicamente para ordenar las alternativas disponibles dentro de una misma consulta.

Como punto de partida se implementará un baseline basado exclusivamente en reglas, en el que, tras aplicar los filtros obligatorios (idioma, categoría, adaptaciones, etc.), las ediciones se ordenarán mediante una combinación fija de variables como el prestigio editorial, la calidad del aparato crítico o la relevancia de los colaboradores. Posteriormente, este sistema se comparará con un recomendador Content-Based, que representará tanto las ediciones como las preferencias del usuario mediante vectores de características para calcular su similitud, y con un modelo híbrido, que tomará como base el recomendador anterior pero modificará dinámicamente la importancia de cada variable en función de las necesidades detectadas durante la conversación con el usuario. Así, búsquedas orientadas al estudio darán mayor peso al aparato crítico y al prestigio editorial, mientras que consultas centradas en el coleccionismo o en la compra para regalo priorizarán aspectos relacionados con la calidad material y la presentación de la edición.

La comparación entre modelos no se realizará únicamente atendiendo a una métrica cuantitativa, sino considerando también la calidad y coherencia de las recomendaciones, su capacidad de adaptación a distintos perfiles de usuario, la interpretabilidad de los resultados, la estabilidad frente a pequeñas variaciones en la consulta, el coste computacional, la complejidad de implementación y su integración con el agente conversacional. 

## 7. Estrategia de Validación y Evaluación

Dado que el proyecto no dispone de un histórico de interacciones reales, la evaluación se llevará a cabo mediante un conjunto de escenarios de prueba representativos de los principales casos de uso del recomendador (estudio, lectura general, coleccionismo, regalo, búsqueda temática, etc.), analizando en cada uno de ellos tanto el orden de las recomendaciones como las explicaciones generadas. El modelo definitivo será aquel que ofrezca el mejor equilibrio entre calidad de las recomendaciones, interpretabilidad, eficiencia e integración dentro del MVP, y no necesariamente el que obtenga la puntuación cuantitativa más elevada.

## 8. Riesgos y Alternativas

El principal riesgo del proyecto es la ausencia de una variable objetivo conocida. El sistema no pretende predecir un valor observado, sino generar recomendaciones a partir de las características de las ediciones y de las preferencias expresadas por el usuario. Por ello, la calidad del sistema dependerá en gran medida de que las variables construidas durante la ingeniería de características (prestigio editorial, puntuación del aparato crítico, relevancia de los colaboradores, índices materiales, etc.) representen adecuadamente los criterios utilizados por un lector para seleccionar una edición.

En cuanto a los datos, el volumen de ediciones recopilado resulta suficiente para construir un recomendador basado en contenido, ya que este tipo de modelos no requiere un histórico de interacciones entre usuarios y productos. Sin embargo, existen ciertas limitaciones derivadas de la cobertura de las fuentes utilizadas. Algunas editoriales no proporcionan la misma cantidad de información bibliográfica, determinados indicadores de prestigio no están disponibles para todas ellas y existen categorías con un número reducido de ediciones o con menor representación en el SPI. Asimismo, determinadas características relacionadas con la calidad material, como el tipo de papel o el acabado de la impresión, no pueden obtenerse de forma sistemática y, por tanto, no podrán formar parte del modelo.

La mayor incertidumbre del proyecto se encuentra en la evaluación objetiva de las recomendaciones, al no existir un conjunto de respuestas correctas con el que comparar los resultados obtenidos. Para reducir este problema se diseñará una batería de escenarios de prueba representativos de los principales casos de uso del sistema y se analizará tanto la coherencia de las recomendaciones como la calidad de las explicaciones generadas. Si los modelos propuestos no consiguieran superar de forma clara al sistema basado en reglas o no pudieran validarse con suficiente rigor, se optaría por mantener este último como solución definitiva del MVP, ya que ofrece recomendaciones completamente interpretables, fácilmente justificables y alineadas con los objetivos del proyecto.


