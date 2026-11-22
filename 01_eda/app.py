"""Punto de entrada: navegación por páginas, estilo y filtro de departamentos.

Ejecutar desde la raíz del proyecto:  streamlit run 01_eda/app.py
"""
from pathlib import Path

import streamlit as st

from contexto import departamentos, filtro_sidebar
from estilo import aplicar_estilo

st.set_page_config(page_title="EDA · Delitos sexuales, región Caribe",
                   page_icon=":material/analytics:", layout="wide",
                   initial_sidebar_state="expanded")
aplicar_estilo()

CARPETA = Path(__file__).parent / "paginas"

# (sección, archivo, título, icono, ruta en la URL). Solo aparecen las páginas
# cuyo archivo existe, así se pueden ir agregando una a una.
ESTRUCTURA = [
    ("Proyecto", "inicio.py", "Inicio", ":material/home:", "inicio"),
    ("1 · Fuente", "p1_carga.py", "Carga y estructura",
     ":material/upload_file:", "carga"),
    ("2 · Calidad", "p2_faltantes.py", "Valores faltantes",
     ":material/help_center:", "faltantes"),
    ("2 · Calidad", "p3_duplicados.py", "Duplicados",
     ":material/content_copy:", "duplicados"),
    ("3 · Análisis", "p4_descriptivas.py", "Descriptivas",
     ":material/bar_chart:", "descriptivas"),
    ("3 · Análisis", "p5_atipicos.py", "Atípicos",
     ":material/monitoring:", "atipicos"),
    ("3 · Análisis", "p6_relaciones.py", "Relaciones",
     ":material/hub:", "relaciones"),
]

paginas = {}
for seccion, archivo, titulo, icono, url in ESTRUCTURA:
    if (CARPETA / archivo).exists():
        paginas.setdefault(seccion, []).append(
            st.Page(f"paginas/{archivo}", title=titulo, icon=icono,
                    url_path=url, default=(url == "inicio")))

pg = st.navigation(paginas)

# Filtro de departamentos: solo en las páginas que analizan el Caribe.
if pg.url_path not in ("inicio", "carga"):
    filtro_sidebar(departamentos())
    if not st.session_state["deptos_guardados"]:
        st.warning("Selecciona al menos un departamento en la barra lateral.")
        st.stop()

with st.sidebar:
    st.divider()
    st.caption("Miguel Caicedo - Jordy Cardenas · Minería de Datos")

pg.run()