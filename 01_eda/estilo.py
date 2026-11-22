"""Estilo y componentes compartidos por todas las páginas del EDA."""
import pandas as pd
import streamlit as st
import plotly.express as px

# ------------------------------------------------------------------ paleta
PRIMARIO = "#0F6E8C"     # azul petróleo
ACENTO = "#E07B39"       # naranja (resalta lo importante)
GRIS = "#C5CDD6"         # lo que queda en segundo plano
PALETA = ["#0F6E8C", "#E07B39", "#4C9F70", "#8E6BBF",
          "#D1495B", "#EDAE49", "#5B8E7D", "#6C757D"]

# Plotly Express asigna los colores al crear la figura: la paleta del proyecto
# debe fijarse como valor por defecto, no solo en el diseño final.
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PALETA
px.defaults.color_continuous_scale = "Teal"

CSS = """
<style>
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px;}
h1 {font-weight: 700; letter-spacing: -0.5px; margin-bottom: 0.2rem;}
h2, h3 {font-weight: 650;}
[data-testid="stMetricValue"] {font-size: 1.75rem; font-weight: 650;}
[data-testid="stMetricLabel"] p {font-size: 0.85rem; color: #52606D;}
[data-testid="stSidebar"] {border-right: 1px solid #E4E9EE;}
</style>
"""


def aplicar_estilo():
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ formato
def miles(n) -> str:
    """67122 -> 67.122"""
    return f"{int(n):,}".replace(",", ".")


def dec(x, n: int = 1) -> str:
    """0.553 -> 0,55 (coma decimal, punto de miles)"""
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Formatos de visualización (no cambian el tipo de dato)
CFG = {
    "fecha_hecho": st.column_config.DateColumn("fecha_hecho", format="DD/MM/YYYY"),
    "mes": st.column_config.DateColumn("mes", format="MM/YYYY"),
    "año": st.column_config.NumberColumn("año", format="%d"),
}


# ------------------------------------------------------------------ estructura de página
def encabezado(titulo: str, pregunta: str, datos: str | None = None):
    st.title(titulo)
    st.markdown(f"*{pregunta}*")
    if datos:
        st.markdown(f":gray-badge[Datos: {datos}]")


def seccion(ancla: str, titulo: str):
    st.subheader(titulo, anchor=ancla)


def indice(items):
    """Fila de enlaces a los apartados de la misma página: [(ancla, texto), ...]"""
    st.markdown("**Contenido:** " + " · ".join(f"[{t}](#{a})" for a, t in items))

def ref(ancla: str, texto: str) -> str:
    """Enlace dentro de un texto que lleva a un apartado de la misma página.
    Se usa dentro de f-strings: f"... ({ref('genero-anio', 'apartado 4')}) ..."."""
    return f"[{texto}](#{ancla})"

def ir_a(ruta: str, etiqueta: str, icono: str = ":material/arrow_forward:"):
    """Enlace clicable a otra página; si la página aún no existe, muestra texto."""
    try:
        st.page_link(ruta, label=etiqueta, icon=icono)
    except Exception:
        st.caption(f"{etiqueta} (próximamente)")


def kpi(donde, etiqueta: str, valor, ayuda: str | None = None):
    with donde.container(border=True):
        st.metric(etiqueta, valor, help=ayuda)


# ------------------------------------------------------------------ cajas de análisis
TIPOS = {"observacion": ("Observación", "blue"),
         "decision": ("Decisión", "green"),
         "justificacion": ("Justificación", "violet"),
         "limitacion": ("Limitación", "orange")}


def caja(tipo: str, texto: str):
    etiqueta, color = TIPOS[tipo]
    with st.container(border=True):
        st.markdown(f":{color}-badge[{etiqueta}]\n\n{texto}")


def observacion(texto): caja("observacion", texto)
def decision(texto): caja("decision", texto)
def justificacion(texto): caja("justificacion", texto)
def limitacion(texto): caja("limitacion", texto)


# ------------------------------------------------------------------ tablas y gráficos
def mostrar_tabla(d, miles_cols=(), dec_cols=(), n=2, donde=st,
                  fecha_cols=(), mes_cols=(), **kw):
    """Tabla con formato español sin convertir a texto: la columna sigue
    siendo numérica (alineada a la derecha y ordenable)."""
    fmt = {c: miles for c in miles_cols}
    for c in dec_cols:
        fmt[c] = (lambda x, n=n: dec(x, n))
    for c in fecha_cols:
        fmt[c] = lambda x: "" if pd.isna(x) else x.strftime("%d/%m/%Y")
    for c in mes_cols:
        fmt[c] = lambda x: "" if pd.isna(x) else x.strftime("%m/%Y")
    estilo = d.style.format(fmt, na_rep="–")
    try:
        donde.dataframe(estilo, width="stretch", **kw)
    except TypeError:  # versiones anteriores de Streamlit
        donde.dataframe(estilo, use_container_width=True, **kw)


def mostrar_df(d, donde=st, **kw):
    """DataFrame simple (sin formato numérico) a todo el ancho."""
    try:
        donde.dataframe(d, width="stretch", **kw)
    except TypeError:
        donde.dataframe(d, use_container_width=True, **kw)


def grafico(fig, donde=st, alto: int | None = None, fmt_x: str | None = None,
            fmt_y: str | None = None):
    """Gráfico con el estilo del proyecto: coma decimal, punto de miles,
    bordes en histogramas y separación entre celdas en mapas de calor."""
    fig.update_layout(separators=",.", template="plotly_white", colorway=PALETA,
                      font=dict(size=13), margin=dict(l=10, r=10, t=40, b=10),
                      legend_title_text="")
    if alto:
        fig.update_layout(height=alto)
    if fmt_x:   # p. ej. ",d" muestra 20.000 en lugar de 20k
        fig.update_xaxes(tickformat=fmt_x)
    if fmt_y:
        fig.update_yaxes(tickformat=fmt_y)
    fig.update_traces(marker_line_width=1, marker_line_color="white",
                      selector=dict(type="histogram"))
    fig.update_traces(xgap=1, ygap=1, selector=dict(type="heatmap"))
    try:
        donde.plotly_chart(fig, width="stretch", theme=None)
    except TypeError:
        donde.plotly_chart(fig, use_container_width=True, theme=None)


def frecuencias(serie: pd.Series) -> pd.DataFrame:
    """Tabla de frecuencias: categoría, registros y % del total."""
    f = serie.value_counts(dropna=False)
    t = pd.DataFrame({"categoría": f.index.astype(str), "registros": f.values})
    t["%"] = (t["registros"] / len(serie) * 100).round(2)
    return t


def pct_no_reporta(serie: pd.Series) -> float:
    """% de valores que empiezan por «NO REPORT»."""
    return serie.astype(str).str.upper().str.startswith("NO REPORT").mean() * 100