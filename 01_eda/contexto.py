"""Datos compartidos por todas las páginas (con caché) y filtro de departamentos."""
from types import SimpleNamespace

import pandas as pd
import streamlit as st

from datos import (CARIBE, NOMBRES_CSV_CARIBE, cargar_nacional,
                   filtrar_caribe)
from limpieza import preparar

# Fecha de extracción de los datos, según la documentación de la fuente
FECHA_EXTRACCION = pd.Timestamp("2026-08-31")

COLS_FILA = ["departamento", "municipio", "codigo_dane", "armas_medios",
             "fecha_hecho", "genero", "grupo_etario", "cantidad", "delito"]


@st.cache_resource(show_spinner="Leyendo el CSV original...")
def nacional() -> pd.DataFrame:
    """CSV completo (todo el país). No se modifica: las páginas trabajan sobre copias."""
    return cargar_nacional()


@st.cache_data(show_spinner="Preparando los datos del Caribe...")
def datos_caribe():
    original = filtrar_caribe(nacional())
    limpio = preparar(original).rename(columns={"anio": "año"})
    return original, limpio


@st.cache_data(show_spinner="Calculando la calidad del archivo completo...")
def resumen_nacional() -> dict:
    nac = nacional()
    nulos = nac[COLS_FILA].isna().sum()
    tabla_nulos = pd.DataFrame({"nulos": nulos,
                                "% del total": (nulos / len(nac) * 100).round(2)})
    g = nac.groupby(COLS_FILA, dropna=False).size()
    g = g[g > 1]
    por_depto = (nac.groupby("departamento").size()
                 .rename("registros").reset_index())
    return {"nulos": tabla_nulos,
            "grupos": len(g), "filas_en_grupos": int(g.sum()),
            "excedentes": int((g - 1).sum()),
            "no_reporta_genero": int((nac["genero"] == "NO REPORTA").sum()),
            "por_depto": por_depto}


def departamentos() -> list:
    return sorted(datos_caribe()[1]["departamento"].unique())


def seleccion() -> list:
    sel = st.session_state.get("deptos_guardados")
    return list(sel) if sel else departamentos()


def contexto() -> SimpleNamespace:
    """Datos del Caribe filtrados por los departamentos elegidos en la barra lateral.

    df  : datos limpios       raw : datos originales del mismo subconjunto
    """
    original, limpio = datos_caribe()
    sel = seleccion()
    df = limpio[limpio["departamento"].isin(sel)].copy()
    raw = original[original["id"].isin(df["id"])].copy()
    raw = raw.rename(columns={"departamento_original": "departamento"})
    raw["año"] = raw["fecha_hecho"].dt.year
    return SimpleNamespace(df=df, raw=raw, original=original, limpio=limpio,
                           seleccion=sel)

def _boton(donde, etiqueta: str, **kw):
    """Botón a todo el ancho (compatible con versiones anteriores de Streamlit)."""
    try:
        return donde.button(etiqueta, width="stretch", **kw)
    except TypeError:
        return donde.button(etiqueta, use_container_width=True, **kw)


def filtro_sidebar(todos: list):
    """Filtro de departamentos para la barra lateral: casillas dentro de un
    desplegable, un resumen siempre visible y botones «Todos» / «Ninguno».

    La selección vive en st.session_state["deptos_guardados"], de modo que se
    conserva al cambiar de página (las casillas se vuelven a crear desde ahí)."""
    if "deptos_guardados" not in st.session_state:
        st.session_state["deptos_guardados"] = list(todos)
    guardados = st.session_state["deptos_guardados"]

    def actualizar():
        st.session_state["deptos_guardados"] = [
            d for d in todos if st.session_state.get(f"chk_{d}", False)]

    def marcar(valor: bool):
        for d in todos:
            st.session_state[f"chk_{d}"] = valor
        actualizar()

    for d in todos:   # las casillas pierden su estado al salir de la página
        if f"chk_{d}" not in st.session_state:
            st.session_state[f"chk_{d}"] = d in guardados

    with st.sidebar:
        st.divider()
        st.markdown("**Filtro de la región Caribe**")
        n = len(st.session_state["deptos_guardados"])
        if n == len(todos):
            st.caption(f"Los {n} departamentos")
        elif n == 0:
            st.caption(":red[Ningún departamento seleccionado]")
        elif n <= 2:
            st.caption(", ".join(st.session_state["deptos_guardados"]))
        else:
            st.caption(f"{n} de {len(todos)} departamentos")
        with st.expander("Elegir departamentos"):
            b1, b2 = st.columns(2)
            _boton(b1, "Todos", on_click=marcar, args=(True,))
            _boton(b2, "Ninguno", on_click=marcar, args=(False,))
            for d in todos:
                st.checkbox(d, key=f"chk_{d}", on_change=actualizar)
        st.caption("Selección para el análisis: los datos originales no se "
                   "modifican.")