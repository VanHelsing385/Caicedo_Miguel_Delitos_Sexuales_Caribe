PROYECTO DE MINERÍA DE DATOS
ANÁLISIS DE DELITOS SEXUALES EN LA REGIÓN CARIBE

Asignatura: Minería de Datos
Autores: Miguel Caicedo - Jordy Cardenas

============================================================
1. DESCRIPCIÓN
============================================================

Este proyecto desarrolla un proceso de análisis exploratorio y almacenamiento de datos relacionados con los delitos sexuales reportados por la Policía Nacional de Colombia, con énfasis en los ocho departamentos de la región Caribe.

El proceso comprende la lectura y exploración del conjunto de datos original, la limpieza y transformación de la información, su almacenamiento en PostgreSQL mediante Neon y la preparación de los datos para su análisis y visualización en Power BI.

La aplicación de análisis exploratorio se desarrolla en Python y Streamlit.

============================================================
2. TECNOLOGÍAS UTILIZADAS
============================================================

- Python 3.14.4 (versión utilizada en las pruebas).
- Pandas 3.1.1.
- NumPy 2.5.4.
- Streamlit 1.67.0.
- Plotly 7.1.0.
- PostgreSQL.
- Neon.
- Psycopg 3.3.8.
- Python-dotenv 1.2.4.
- Power BI Desktop.

Las dependencias de Python se encuentran en requirements.txt.

============================================================
3. ESTRUCTURA DEL PROYECTO
============================================================

Caicedo_Miguel_Delitos_Sexuales_Caribe/
|
|-- README.txt
|-- requirements.txt
|
|-- .streamlit/
|   |-- config.toml
|
|-- 00_datos_originales/
|   |-- delitos_sexuales_nacional.csv
|
|-- 01_eda/
|   |-- app.py
|   |-- contexto.py
|   |-- datos.py
|   |-- estilo.py
|   |-- limpieza.py
|   |-- verificar_carga.py
|   |
|   |-- paginas/
|       |-- inicio.py
|       |-- p1_carga.py
|       |-- p2_faltantes.py
|       |-- p3_duplicados.py
|       |-- p4_descriptivas.py
|       |-- p5_atipicos.py
|       |-- p6_relaciones.py
|
|-- 02_base_de_datos/
    |-- 01_crear_tablas.sql
    |-- 02_verificaciones.sql
    |-- guardar_limpios.py
    |-- validar_codigos_dane.py
    |-- verificar_modelo.py
    |
    |-- salida/
        |-- delitos_limpios.csv
        |-- control.json

La carpeta salida contiene los archivos generados durante la preparación de los datos. El archivo control.json permite comprobar la correspondencia entre el archivo original, el archivo preparado y los scripts de limpieza.

============================================================
4. REQUISITOS PREVIOS
============================================================

- Tener Python instalado.
- Disponer de conexión a internet.
- Contar con una base de datos PostgreSQL en Neon para ejecutar la carga.
- Tener acceso a Power BI Desktop para utilizar el proyecto de visualización.

============================================================
5. INSTALACIÓN
============================================================

PASO 1. Abrir una terminal en la carpeta raíz del proyecto.

PASO 2. Crear un entorno virtual.

En Windows:

    python -m venv .venv
    .venv\Scripts\activate

En Linux:

    python3 -m venv .venv
    source .venv/bin/activate

PASO 3. Instalar las dependencias:

    python -m pip install -r requirements.txt

============================================================
6. EJECUCIÓN DE STREAMLIT
============================================================

Desde la carpeta raíz del proyecto, ejecutar:

    streamlit run 01_eda/app.py

La aplicación permite explorar:

- Carga y estructura de los datos.
- Valores faltantes.
- Registros duplicados.
- Estadísticas descriptivas.
- Valores atípicos.
- Distribuciones y relaciones entre variables.

La aplicación utiliza el archivo CSV original como fuente de información y realiza el análisis de los ocho departamentos de la región Caribe.

Para ejecutar las verificaciones de carga:

    python 01_eda/verificar_carga.py

============================================================
7. CONFIGURACIÓN DE POSTGRESQL NEON
============================================================

PASO 1. Crear o disponer de una base de datos PostgreSQL en Neon.

PASO 2. Crear un archivo llamado .env en la raíz del proyecto.

Su contenido debe tener la siguiente estructura:

    DATABASE_URL=postgresql://USUARIO:CONTRASEÑA@HOST/BASE_DE_DATOS?sslmode=require

Reemplazar los valores de ejemplo por los datos de conexión proporcionados por Neon.

IMPORTANTE:
El archivo .env contiene credenciales privadas. No debe compartirse ni publicarse.

PASO 3. Revisar el script de creación de tablas:

    02_base_de_datos/01_crear_tablas.sql

PASO 4. Ejecutar el proceso de preparación y carga:

    python 02_base_de_datos/guardar_limpios.py

El proceso comprende tres fases:

1. PREPARAR:
   Genera delitos_limpios.csv y control.json cuando corresponde.

2. CARGAR:
   Crea o verifica las tablas, valida los catálogos y carga los registros en PostgreSQL.

3. VERIFICAR:
   Compara los registros almacenados en la base de datos con el archivo preparado.

============================================================
8. OPCIONES DEL SCRIPT DE CARGA
============================================================

Para consultar las opciones disponibles:

    python 02_base_de_datos/guardar_limpios.py --help

Opciones:

--solo-preparar
Ejecuta únicamente la preparación de los datos.

--solo-verificar
Ejecuta únicamente las verificaciones.

--regenerar
Fuerza la regeneración del archivo preparado.

--lote
Permite modificar el tamaño de los lotes de carga.

--permitir-local
Permite utilizar una conexión local cuando corresponda.

============================================================
9. SCRIPTS DE VERIFICACIÓN
============================================================

Los siguientes archivos permiten comprobar el proceso:

- 01_eda/verificar_carga.py:
  Comprueba la lectura y las cifras de control del conjunto original.

- 02_base_de_datos/validar_codigos_dane.py:
  Valida los códigos DANE utilizados en los datos.

- 02_base_de_datos/verificar_modelo.py:
  Comprueba aspectos del modelo de datos.

- 02_base_de_datos/02_verificaciones.sql:
  Contiene consultas para comprobar la estructura, integridad y contenido de PostgreSQL. Se ejecuta desde el editor SQL de Neon.

============================================================
10. CONSIDERACIONES METODOLÓGICAS
============================================================

- El archivo CSV original se conserva sin modificaciones.
- El análisis se concentra en los ocho departamentos de la región Caribe.
- No se eliminan registros del conjunto analizado.
- Los valores faltantes se identifican y se tratan mediante categorías explícitas cuando corresponde.
- Los registros repetidos se identifican y marcan, pero no se eliminan.
- Los valores atípicos se conservan y se analizan.
- Las cifras representan registros reportados y no tasas de ocurrencia poblacional.
- Los resultados deben interpretarse teniendo en cuenta las limitaciones de la fuente y los cambios en el registro de la información.

============================================================
11. AUTORES
============================================================

Miguel Caicedo - Jordy Cardenas

Proyecto académico desarrollado para la asignatura Minería de Datos.