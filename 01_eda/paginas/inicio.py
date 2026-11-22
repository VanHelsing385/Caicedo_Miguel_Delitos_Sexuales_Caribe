import streamlit as st

from contexto import FECHA_EXTRACCION, datos_caribe, nacional
from estilo import encabezado, ir_a, kpi, limitacion, miles, observacion

nac = nacional()
original, limpio = datos_caribe()

encabezado("Delitos sexuales en la región Caribe de Colombia",
           "Análisis exploratorio de datos del Reporte de Delitos Sexuales de "
           "la Policía Nacional · Minería de Datos")

c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Registros del Caribe", miles(len(original)),
    f"De {miles(len(nac))} registros del archivo nacional.")
kpi(c2, "Departamentos", len(limpio["departamento"].unique()))
kpi(c3, "Periodo",
    f"{nac['fecha_hecho'].min():%Y} – {nac['fecha_hecho'].max():%Y}",
    f"Del {nac['fecha_hecho'].min():%d/%m/%Y} al {nac['fecha_hecho'].max():%d/%m/%Y}.")
kpi(c4, "Datos extraídos", f"{FECHA_EXTRACCION:%d/%m/%Y}")

st.subheader("Proceso del proyecto")
cols = st.columns(4)
pasos = [
    ("1 · Cargar la fuente", "Lectura del CSV original y selección de la "
     "región Caribe por código DANE."),
    ("2 · EDA con Python", "Calidad, limpieza, descripción, atípicos y "
     "relaciones. Cada decisión queda justificada."),
    ("3 · Guardar datos limpios", "Los datos ya limpios se almacenan en "
     "PostgreSQL (Neon) con un script de Python."),
    ("4 · Tablero en Power BI", "El tablero utiliza los datos almacenados en PostgreSQL (Neon), "
     "mediante una conexión en modo Importar.base de datos."),
]
for col, (titulo, texto) in zip(cols, pasos):
    with col.container(border=True, height=175):
        st.markdown(f"**{titulo}**")
        st.caption(texto)

st.subheader("Recorrido del análisis")
paginas = [
    ("paginas/p1_carga.py", "Carga y estructura",
     "¿Qué contiene el archivo y cómo se obtiene la región Caribe?"),
    ("paginas/p2_faltantes.py", "Valores faltantes",
     "¿Qué datos faltan y cómo se tratan?"),
    ("paginas/p3_duplicados.py", "Duplicados",
     "¿Hay filas repetidas y cambia algo si se excluyen?"),
    ("paginas/p4_descriptivas.py", "Estadísticas descriptivas",
     "¿Cómo se ven los datos ya limpios?"),
    ("paginas/p5_atipicos.py", "Atípicos",
     "¿Hay meses fuera de lo esperado?"),
    ("paginas/p6_relaciones.py", "Distribuciones y relaciones",
     "¿Cómo se distribuyen los casos y qué relaciones hay?"),
]
for i in range(0, len(paginas), 3):
    cols = st.columns(3)
    for col, (ruta, titulo, pregunta) in zip(cols, paginas[i:i + 3]):
        with col.container(border=True, height=125):
            ir_a(ruta, titulo, ":material/arrow_forward:")
            st.caption(pregunta)

observacion("Los datos son **denuncias registradas por la Policía Nacional**, "
            "no la ocurrencia real de los hechos. En todo el análisis se "
            "trabaja con conteos absolutos, no con tasas por habitante.")
limitacion("El conjunto de datos no incluye diccionario de variables. Las "
           "cifras están sujetas a variación (integración y consolidación "
           "con la Fiscalía General de la Nación).")

st.caption("Fuente: Reporte Delitos Sexuales, DIJIN – Policía Nacional "
           "(datos abiertos). En las páginas de análisis, la barra lateral "
           "permite elegir los departamentos.")