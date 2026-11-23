# Proyecto de Minería de Datos: Delitos Sexuales en la Región Caribe

**Asignatura:** Minería de Datos  
**Autores:** Miguel Caicedo - Jordy Cardenas

## 1. Descripción del proyecto

Este proyecto desarrolla un proceso de análisis exploratorio y almacenamiento de datos relacionados con los delitos sexuales reportados por la Policía Nacional de Colombia, con énfasis en los ocho departamentos de la región Caribe.

El proceso comprende la lectura y exploración del conjunto de datos original, la limpieza y transformación de la información, su almacenamiento en PostgreSQL mediante Neon y la preparación de los datos para su análisis y visualización en Power BI.

La aplicación de análisis exploratorio se desarrolla en Python y Streamlit.

## 2. Flujo de trabajo

El proyecto se organiza en las siguientes fases:

1. **Carga de datos:** lectura y validación del archivo CSV original.
2. **Análisis exploratorio:** identificación de valores faltantes, registros repetidos, estadísticas descriptivas, valores atípicos, distribuciones y relaciones.
3. **Almacenamiento:** preparación y carga de los datos limpios en PostgreSQL Neon.
4. **Visualización:** conexión de Power BI con la base de datos para construir el tablero interactivo.

## 3. Tecnologías utilizadas

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

Las dependencias de Python se encuentran especificadas en `requirements.txt`.

## 4. Estructura del proyecto

```text
Caicedo_Miguel_Delitos_Sexuales_Caribe/
│
├── README.md
├── requirements.txt
│
├── .streamlit/
│   └── config.toml
│
├── 00_datos_originales/
│   └── delitos_sexuales_nacional.csv
│
├── 01_eda/
│   ├── app.py
│   ├── contexto.py
│   ├── datos.py
│   ├── estilo.py
│   ├── limpieza.py
│   ├── verificar_carga.py
│   │
│   └── paginas/
│       ├── inicio.py
│       ├── p1_carga.py
│       ├── p2_faltantes.py
│       ├── p3_duplicados.py
│       ├── p4_descriptivas.py
│       ├── p5_atipicos.py
│       └── p6_relaciones.py
│
└── 02_base_de_datos/
    ├── 01_crear_tablas.sql
    ├── 02_verificaciones.sql
    ├── guardar_limpios.py
    ├── validar_codigos_dane.py
    ├── verificar_modelo.py
    │
    └── salida/
        ├── delitos_limpios.csv
        └── control.json
```

**Nota:** La carpeta `salida/` se genera durante el proceso de preparación de los datos. El archivo `control.json` permite comprobar la correspondencia entre el CSV original, el CSV preparado y los archivos utilizados en la limpieza.

## 5. Requisitos previos

Para ejecutar el proyecto se necesita:

- Python instalado.
- Git (opcional, para clonar el repositorio).
- Acceso a internet para instalar las dependencias y conectarse a Neon.
- Una cuenta y una base de datos PostgreSQL en Neon para ejecutar el proceso de almacenamiento.
- Power BI Desktop para abrir y utilizar el proyecto de visualización.

## 6. Instalación

### 6.1. Obtener el proyecto

Clonar el repositorio:

```bash
git clone https://github.com/VanHelsing385/Caicedo_Miguel_Delitos_Sexuales_Caribe.git
```

Ingresar a la carpeta:

```bash
cd Caicedo_Miguel_Delitos_Sexuales_Caribe
```

### 6.2. Crear un entorno virtual

En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

En Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 6.3. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

## 7. Ejecución del análisis exploratorio

Desde la carpeta raíz del proyecto, ejecutar:

```bash
streamlit run 01_eda/app.py
```

La aplicación permite explorar:

- Carga y estructura de los datos.
- Valores faltantes.
- Registros duplicados.
- Estadísticas descriptivas.
- Valores atípicos.
- Distribuciones y relaciones entre variables.

La aplicación utiliza el archivo CSV original como fuente de información. El filtro de la región Caribe se realiza mediante los códigos DANE de los departamentos correspondientes.

Para ejecutar las verificaciones de carga:

```bash
python 01_eda/verificar_carga.py
```

## 8. Almacenamiento en PostgreSQL Neon

### 8.1. Configurar la conexión

El proyecto utiliza una variable de entorno llamada `DATABASE_URL` para establecer la conexión con PostgreSQL.

Se debe crear un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
DATABASE_URL=postgresql://USUARIO:CONTRASEÑA@HOST/BASE_DE_DATOS?sslmode=require
```

Se deben reemplazar los valores de ejemplo por los datos de conexión proporcionados por Neon.

**Importante:** el archivo `.env` contiene credenciales y no debe compartirse, publicarse ni incluirse en el ZIP de entrega.

### 8.2. Crear las tablas

El script de creación de la estructura se encuentra en:

```text
02_base_de_datos/01_crear_tablas.sql
```

También se dispone del archivo:

```text
02_base_de_datos/02_verificaciones.sql
```

Este contiene consultas para comprobar la estructura, integridad y contenido de la base de datos. Se ejecuta desde el editor SQL de Neon.

### 8.3. Preparar y cargar los datos

Desde la raíz del proyecto:

```bash
python 02_base_de_datos/guardar_limpios.py
```

El proceso comprende tres fases:

1. **Preparar:** genera el archivo `delitos_limpios.csv` y el archivo de control `control.json`, cuando corresponde.
2. **Cargar:** crea o verifica las tablas, valida los catálogos y carga los registros en PostgreSQL.
3. **Verificar:** compara los registros almacenados con el archivo preparado.

El script dispone de las siguientes opciones:

```bash
python 02_base_de_datos/guardar_limpios.py --help
```

- `--solo-preparar`: ejecuta únicamente la preparación de los datos.
- `--solo-verificar`: ejecuta únicamente las verificaciones.
- `--regenerar`: fuerza la regeneración del archivo preparado.
- `--lote`: permite modificar el tamaño de los lotes de carga.
- `--permitir-local`: permite utilizar una conexión local cuando corresponda.

## 9. Pruebas y verificaciones

El proyecto incorpora scripts para comprobar diferentes aspectos del proceso:

| Archivo | Propósito |
|---|---|
| `01_eda/verificar_carga.py` | Comprueba la lectura y las cifras de control del conjunto original. |
| `02_base_de_datos/validar_codigos_dane.py` | Valida los códigos DANE utilizados en los datos. |
| `02_base_de_datos/verificar_modelo.py` | Comprueba aspectos del modelo de datos. |
| `02_base_de_datos/02_verificaciones.sql` | Ejecuta consultas de verificación en PostgreSQL. |

La carga de los datos se verificó mediante la comparación de los registros del archivo preparado con los almacenados en PostgreSQL.

## 10. Consideraciones metodológicas

- El archivo CSV original se conserva sin modificaciones.
- El análisis se concentra en los ocho departamentos de la región Caribe.
- No se eliminan registros del conjunto analizado.
- Los valores faltantes se identifican y se tratan mediante categorías explícitas cuando corresponde.
- Los registros repetidos se identifican y marcan, pero no se eliminan.
- Los valores atípicos se conservan y se analizan.
- Las cifras representan registros reportados y no tasas de ocurrencia poblacional.
- Los resultados deben interpretarse teniendo en cuenta las limitaciones de la fuente y los cambios en el registro de la información.

## 11. Autores

**Miguel Caicedo - Jordy Cardenas**

Proyecto académico desarrollado para la asignatura Minería de Datos.