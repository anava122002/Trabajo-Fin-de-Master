# Pruebas de la Primera versión del Modelo AHP + TOPSIS

## 0. Introducción

### 0.1 Descripción

### 0.2 Ejemplo de input

```info_busqueda = {
    "busqueda": {
        "titulo_aprox": 'Werther',
        "autor": "Goethe",
        "categorias": ['Literatura'],
        "subcategorias": ['Poesía']
    },
    "restricciones": {
        "precio": [0, 50]  # Rango de precio
    },
    'perfil': {
        "arquetipo": "lectura_general", # estudio_investigacion, lectura_general, coleccion_regalo, escolar_juvenil
        "flags_adicionales": {
        "es_para_regalo": True,
        "prefiere_ilustrado": False,
        "ed_preferida": 'Cátedra',
        "col_preferida": None,
        "enc_preferida": None
        }
    }
}
```

* **busqueda:** filtros blandos del modelo. Usados para búsquedas aproximadas (`rapidfuzz`).

* **restricciones:** filtros duros. Se busca que los valores estén en el intervalo.

* **perfil:** *arquetipo* hace referencia a la matriz de pesos usada en AHP. Las *flags_adicionales* son preferencias del usuario; suman a la score final entre un 0.1 y 0.15.


## 1. Pruebas

### Título y autor completos (sin flags adicionales)

```
info_busqueda = {
    "busqueda": {
        "titulo_aprox": 'Rebelión en la Granja',
        "autor": "George Orwell",
        "categorias": ['Literatura'],
        "subcategorias": []
    },
    "restricciones": {
        "precio": [0, 50]  # Rango de precio
    },
    'perfil': {
        "arquetipo": "lectura_general",
        "flags_adicionales": {
        "es_para_regalo": False,
        "prefiere_ilustrado": False,
        "ed_preferida": None,
        "col_preferida": None,
        "enc_preferida": None
        }
    }
}
```

#### Resultado para lectura_general:
|  |Título| Editorial|  Precio|  TOPSIS|
| :---: |:---| :---|  :---|  :---:|
54593|         Rebelión En La Granja |   Espasa |   7.00  |    **1.000000**|
33106 | Rebelión En La Granja....Ccc | Destino  |  6.68   |   **0.982000**|
33359 |  Rebelión En La Granja....Dl |  Destino |  40.01  |    **0.957046**|

### Resultado para estudio_investigacion (y escolar_juvenil):

|  |Título| Editorial|  Precio|  TOPSIS|
| :---: |:---| :---|  :---|  :---:|
35343 |     Rebelión En La Granja |Ediciones Akal |   12.00  |    **0.948591**|
54593      | Rebelión En La Granja | Espasa  |  7.00   |   **0.053174**|
33106 |  Rebelión En La Granja....Ccc |  Destino |  6.68  |    **0.050247**|

### Resultado para coleccion_regalo:

|  |Título| Editorial|  Precio|  TOPSIS|
| :---: |:---| :---|  :---|  :---:|
35343|  Rebelión En La Granja|  Ediciones Akal|   12.00 |  **0.807264**  |
24811| Rebelión En La Granja (La Novela Gráfica)| Debolsillo| 22.90 |  **0.216709**  |
74109|  Rebelión En La Granja (Anulado)|         Planeta|   12.95  | **0.149557**|


### Título y/o autor incompletos

#### Ejemplo 1 (ambas incompletas): 

```
info_busqueda = {
    "busqueda": {
        "titulo_aprox": 'Quijote',
        "autor": "Cervantes",
        "categorias": ['Literatura'],
        "subcategorias": []
    },
    "restricciones": {
        "precio": [0, 50]  # Rango de precio
    },
    'perfil': {
        "arquetipo": "lectura_general", 
        "flags_adicionales": {
        "es_para_regalo": False,
        "prefiere_ilustrado": False,
        "ed_preferida": None,
        "col_preferida": None,
        "enc_preferida": None
        }
    }
}
```
|  |Título| Editorial|  Precio|  TOPSIS|
| :---: |:---| :---|  :---|  :---:|
14810 |  Don Quijote De La Mancha|Alianza Editorial |   13.5|**1.000000**|  
44137 | Don Quijote De La Mancha I y Ii | Ediciones Cátedra |   6.075| **1.000000**|
22461 |El Ingenioso Hidalgo Don Quijote De La Mancha|Castalia Ediciones|11.5| **0.943455**|

#### Ejemplo 2 (ambas incompletas + flags adicionales):

```
'perfil': {
        "arquetipo": "lectura_general", 
        "flags_adicionales": {
        "es_para_regalo": False,
        "prefiere_ilustrado": 'True',
        "ed_preferida": 'Castalia',
        "col_preferida": None,
        "enc_preferida": None
        }
    }
```

|  |Título| Editorial|  Precio|  TOPSIS|
| :---: |:---| :---|  :---|  :---:|
22461 |El Ingenioso Hidalgo Don Quijote De La Mancha|Castalia Ediciones|11.5| **1.000000**|
14810 |  Don Quijote De La Mancha|Alianza Editorial |   13.5|**1.000000**|  
44137 | Don Quijote De La Mancha I y Ii | Ediciones Cátedra |   6.075| **1.000000**|


### Valores sin especificar (Antologías, colecciones...)

#### Solo autor:

```
info_busqueda = {
    "busqueda": {
        "titulo_aprox": None,
        "autor": "Elvira Sastre",
        "categorias": ['Literatura'],
        "subcategorias": []
    },
    "restricciones": {
        "precio": [0, 50]  # Rango de precio
    },
    'perfil': {
        "arquetipo": "lectura_general", # estudio_investigacion, lectura_general, coleccion_regalo, escolar_juvenil
        "flags_adicionales": {
        "es_para_regalo": False,
        "prefiere_ilustrado": False,
        "ed_preferida": None,
        "col_preferida": None,
        "enc_preferida": None
        }
    }
}
```

|  |Título| Editorial|  Precio|  TOPSIS|
| :---: |:---| :---|  :---|  :---:|
19226|  Las Vulnerabilidades|       Booket|   10.95|      1.000000|
78999|           Días Sin Ti|  Seix Barral|   18.00|      0.699353|
78714|  Las Vulnerabilidades|  Seix Barral|   20.90|      0.628137|



### Libros que no están en los registros