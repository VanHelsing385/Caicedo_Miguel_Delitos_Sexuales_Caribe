# Análisis de delitos sexuales en la región Caribe colombiana

Proyecto académico de Minería de Datos orientado al almacenamiento, limpieza, análisis exploratorio y visualización de registros de delitos sexuales correspondientes a los departamentos de la región Caribe de Colombia.

## 1. Descripción del proyecto

El proyecto desarrolla un proceso de análisis de datos que comprende:

- Exploración y caracterización del conjunto de datos original.
- Limpieza y transformación de los registros, conservando la información original.
- Identificación y análisis de valores faltantes, duplicados y atípicos.
- Análisis descriptivo, distribuciones y relaciones entre variables.
- Modelado y almacenamiento de los datos en PostgreSQL.
- Visualización interactiva mediante Python, Streamlit y Power BI.

El análisis regional comprende ocho departamentos del Caribe colombiano.

## 2. Tecnologías utilizadas

| Tecnología | Aplicación |
|---|---|
| Python 3.14.4 | Procesamiento y análisis de datos |
| Pandas | Manipulación de datos |
| NumPy | Operaciones numéricas |
| Streamlit | Aplicación interactiva de análisis exploratorio |
| Plotly | Visualizaciones interactivas |
| PostgreSQL | Almacenamiento de datos |
| Neon | Servicio de PostgreSQL en la nube |
| Psycopg 3 | Conexión desde Python con PostgreSQL |
| Power BI | Elaboración de dashboards e informes |

## 3. Estructura del proyecto

```text
Caicedo_Miguel_Delitos_Sexuales_Caribe/
│
├── 00_datos_originales/
│   └── delitos_sexuales_nacional.csv
│
├── 01_eda/
│   ├── app.py
│   ├── datos.py
│   ├── limpieza.py
│   ├── contexto.py
│   ├── estilo.py
│   ├── verificar_carga.py
│   └── paginas/
│
├── 02_base_de_datos/
│   ├── 01_crear_tablas.sql
│   ├── 02_verificaciones.sql
│   ├── guardar_limpios.py
│   ├── verificar_modelo.py
│   └── validar_codigos_dane.py
│
├── 03_powerbi/
│
├── 04_capturas/
│
├── 05_articulo/
│
├── .streamlit/
│   └── config.toml
│
├── .gitignore
├── bitacora_decisiones.md
├── requirements.txt
└── README.md
```

Las carpetas de Power BI, evidencias y artículo se incorporarán conforme se completen esas fases del proyecto.

## 4. Requisitos previos

Para ejecutar la aplicación se necesita:

- Python 3.14.4.
- Git.
- El archivo CSV original ubicado en `00_datos_originales/`.
- Las dependencias especificadas en `requirements.txt`.

## 5. Instalación y ejecución del análisis exploratorio

### 5.1. Clonar el repositorio

```bash
git clone URL_DEL_REPOSITORIO
cd Caicedo_Miguel_Delitos_Sexuales_Caribe
```

El repositorio es privado, por lo que se necesita tener acceso autorizado para clonarlo.

### 5.2. Crear un entorno virtual

```bash
python -m venv .venv
```

### 5.3. Activar el entorno virtual

En Linux:

```bash
source .venv/bin/activate
```

En Windows:

```bash
.venv\Scripts\activate
```

### 5.4. Instalar las dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5.5. Ejecutar Streamlit

Desde la raíz del proyecto:

```bash
streamlit run 01_eda/app.py
```

Streamlit iniciará la aplicación y mostrará la dirección local desde la cual se puede consultar el análisis exploratorio.

**Importante:** el archivo original debe conservar su ubicación y nombre dentro de `00_datos_originales/` para que la aplicación pueda localizarlo.

## 6. Base de datos PostgreSQL

El proyecto incluye los scripts utilizados para crear, cargar y verificar el modelo relacional en PostgreSQL.

Los archivos principales son:

- `01_crear_tablas.sql`: definición de las tablas, relaciones y restricciones.
- `02_verificaciones.sql`: consultas de comprobación de la estructura y los registros.
- `guardar_limpios.py`: proceso de carga de los datos preparados.
- `verificar_modelo.py`: comprobaciones del modelo y de los datos.
- `validar_codigos_dane.py`: validaciones relacionadas con los códigos DANE.

La base de datos implementada contiene siete tablas: departamentos, municipios, tipos de delito, géneros, grupos etarios, medios y delitos limpios.

La carga original del proyecto se realizó utilizando PostgreSQL mediante Neon.

### 6.1. Reproducción de la base de datos

La ejecución de esta fase es independiente de la aplicación Streamlit.

Quien desee reproducirla debe disponer de una instancia propia de PostgreSQL y configurar sus credenciales localmente. No se deben utilizar ni compartir credenciales de otras personas.

El script de carga utiliza la variable de entorno `DATABASE_URL`, leída desde un archivo `.env` ubicado en la raíz del proyecto.

No se deben publicar archivos `.env`, contraseñas ni cadenas de conexión.

**Advertencia:** antes de ejecutar los scripts de creación o carga, se recomienda utilizar una base de datos de prueba propia y revisar las instrucciones del código. No se debe ejecutar la carga sobre una base de datos ajena o de producción.

## 7. Bitácora de decisiones metodológicas

El archivo `bitacora_decisiones.md` documenta las decisiones tomadas durante el desarrollo del proyecto, incluyendo:

- Características del conjunto de datos.
- Criterios de limpieza y transformación.
- Tratamiento de valores faltantes y registros duplicados.
- Identificación y tratamiento de valores atípicos.
- Justificación del modelo relacional.
- Validaciones realizadas.
- Limitaciones y decisiones metodológicas.

Se recomienda consultar este documento antes de modificar los procesos de limpieza o las estructuras de almacenamiento, para conservar la trazabilidad y coherencia del análisis.

## 8. Consideraciones sobre los datos

- Se conserva el conjunto de datos original.
- No se eliminan registros del conjunto original.
- Las decisiones de limpieza y transformación se documentan.
- Los registros duplicados se identifican y se conservan.
- Los valores faltantes y las categorías originales se tratan de acuerdo con los criterios documentados en la bitácora.
- Los resultados deben interpretarse considerando las limitaciones del conjunto de datos y de las variables disponibles.

## 9. Autores y contexto académico

Proyecto desarrollado en el marco de la asignatura **Minería de Datos**, como ejercicio académico de aplicación de técnicas de almacenamiento, análisis exploratorio y visualización de datos.