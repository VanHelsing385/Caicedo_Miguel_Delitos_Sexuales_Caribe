import pandas as pd
import plotly.express as px
import streamlit as st

from contexto import contexto
from estilo import (CFG, decision, dec, encabezado, grafico, indice, ir_a,
                    justificacion, kpi, limitacion, miles, mostrar_df,
                    mostrar_tabla, observacion, seccion)

c = contexto()
raw, df, original = c.raw, c.df, c.original
COLS_RAW = ["fecha_hecho", "departamento", "municipio", "codigo_dane", "delito",
            "genero", "grupo_etario", "armas_medios", "cantidad"]

encabezado("3 · Duplicados",
           "¿Hay filas repetidas y cambian los resultados si se excluyen?",
           "originales para definir los grupos; limpios con la marca "
           "`es_repetido` para el resto")
indice([("definicion", "Definición"), ("cuantas", "Cuántas hay"),
        ("departamento", "Por departamento"), ("anio", "Por año"),
        ("sensibilidad-anio", "Sensibilidad por año"),
        ("sensibilidad-depto", "Sensibilidad por departamento"),
        ("decision", "Decisión")])

# ------------------------------------------------------------------ 1. definición
seccion("definicion", "1. ¿Qué es una fila repetida?")
st.markdown(
    "La fuente **no trae un identificador de caso**. Dos filas con la misma "
    "fecha, departamento, municipio, delito, género, grupo etario, medio y "
    "cantidad pueden ser denuncias distintas o un registro duplicado, y con "
    "estos datos no es posible distinguirlo.")
st.markdown(
    "Un **grupo** es un conjunto de filas idénticas en todas las columnas. "
    "Por eso **no se eliminan**: borrar filas que pueden ser casos reales "
    "sesgaría los conteos hacia abajo, y no hay un criterio objetivo para "
    "decidir cuál de ellas sobra. En cambio, se marca con `es_repetido` cada "
    "fila de un grupo salvo la primera aparición en el archivo (las "
    "**excedentes**), y así se puede comparar el análisis con y sin ellas.")

# ------------------------------------------------------------------ 2. cuántas
seccion("cuantas", "2. ¿Cuántas filas repetidas hay?")
n_rep = int(df["es_repetido"].sum())

# Los grupos se definen sobre los valores originales
grupos = raw.groupby(COLS_RAW, dropna=False).size()
grupos = grupos[grupos > 1]
n_grupos = len(grupos)
n_en_grupos = int(grupos.sum())
n_exced = int((grupos - 1).sum())

por_anio3 = (df.groupby("año")["es_repetido"]
             .agg(repetidos="sum", registros="size").reset_index())
por_anio3["repetidos"] = por_anio3["repetidos"].astype(int)
por_anio3["% repetidos"] = (por_anio3["repetidos"] / por_anio3["registros"] * 100).round(1)

c1, c2, c3 = st.columns(3)
kpi(c1, "Filas marcadas como repetidas", miles(n_rep))
kpi(c2, "% del total", f"{dec(n_rep / len(df) * 100)} %")
kpi(c3, "Grupos de filas idénticas", miles(n_grupos))

if n_grupos > 0:
    tam = grupos.value_counts().sort_index()
    tabla_tam = pd.DataFrame({"filas idénticas en el grupo": tam.index,
                              "grupos": tam.values})
    tabla_tam["filas excedentes"] = (
        (tabla_tam["filas idénticas en el grupo"] - 1) * tabla_tam["grupos"])
    mostrar_tabla(tabla_tam, ["grupos", "filas excedentes"], hide_index=True)

    pares = int(tam.get(2, 0))
    observacion(
        f"{miles(n_rep)} filas ({dec(n_rep / len(df) * 100)} %) repiten "
        f"íntegramente a otra anterior. Pertenecen a {miles(n_grupos)} grupos "
        f"de filas idénticas ({miles(n_en_grupos)} filas en total). El grupo "
        f"más grande tiene {miles(grupos.max())} filas y "
        f"{dec(pares / n_grupos * 100)} % de los grupos son pares.")
    if n_exced == n_rep:
        st.caption("Verificación: la suma de filas excedentes de la tabla "
                   "coincide con las filas marcadas como repetidas.")
    else:
        st.warning("Las filas excedentes no coinciden con las marcadas como "
                   "repetidas; revisar el criterio en limpieza.py.")

    # ---- grupos más grandes (se definen con valores originales, se muestran limpios)
    mayor = (grupos.sort_values(ascending=False).head(3)
             .reset_index(name="filas idénticas"))
    mapa_depto = (original.drop_duplicates("departamento_original")
                  .set_index("departamento_original")["departamento_norm"])
    mayor_vista = mayor.copy()
    mayor_vista["departamento"] = mayor_vista["departamento"].map(mapa_depto)
    mayor_vista["municipio"] = (mayor_vista["municipio"]
                                .str.replace(r"\s*\(CT\)\s*$", "", regex=True)
                                .str.strip())
    st.markdown("**Los 3 grupos más grandes de filas idénticas**")
    mostrar_df(mayor_vista, column_config=CFG, hide_index=True)
    st.caption("Los grupos se determinan con los valores originales de la "
               "fuente; aquí se muestran con los nombres ya limpios.")

    g1, g1v = mayor.iloc[0], mayor_vista.iloc[0]
    n1 = int(g1["filas idénticas"])
    anio_g1 = int(g1["fecha_hecho"].year)
    fila_anio = por_anio3[por_anio3["año"] == anio_g1]
    texto = (f"El grupo más grande reúne {miles(n1)} filas idénticas del "
             f"{g1['fecha_hecho']:%d/%m/%Y} en {g1v['departamento']} "
             f"({g1v['municipio']}). ")
    if len(fila_anio):
        rep_anio = int(fila_anio["repetidos"].iloc[0])
        if rep_anio > 0:
            texto += (f"Sus {miles(n1 - 1)} filas excedentes son el "
                      f"{dec((n1 - 1) / rep_anio * 100)} % de los repetidos de "
                      f"{anio_g1} ({miles(rep_anio)}). ")
    inconsist = int(sum(
        ("MENOR DE 14" in str(r["delito"]).upper()
         and str(r["grupo_etario"]).upper() != "MENORES")
        for _, r in mayor.iterrows()))
    if inconsist:
        texto += (f"En {inconsist} de estos 3 grupos el delito es «con menor de "
                  "14 años» pero el grupo etario no es «MENORES»: posible "
                  "inconsistencia entre campos.")
    observacion(texto)
    ir_a("paginas/p6_relaciones.py",
         "Ver la coherencia entre delito y grupo etario")
    st.caption("Un grupo muy grande suele indicar un registro por defecto o "
               "una carga repetida, no denuncias independientes. Con estos "
               "datos no se puede determinar la causa.")
else:
    observacion("No hay filas repetidas en la selección actual.")

# ------------------------------------------------------------------ 3. por departamento
seccion("departamento", "3. ¿Se concentran en algún departamento?")
por_depto3 = (df.groupby("departamento")["es_repetido"]
              .agg(repetidos="sum", registros="size").reset_index())
por_depto3["repetidos"] = por_depto3["repetidos"].astype(int)
por_depto3["% repetidos"] = (por_depto3["repetidos"] / por_depto3["registros"] * 100).round(1)
mostrar_tabla(por_depto3.sort_values("% repetidos", ascending=False),
              ["repetidos", "registros"], ["% repetidos"], n=1, hide_index=True)
grafico(px.bar(por_depto3.sort_values("% repetidos"), x="% repetidos",
               y="departamento", orientation="h",
               hover_data=["repetidos", "registros"]),
        alto=70 + 42 * len(por_depto3))
if n_rep > 0:
    alto = por_depto3.sort_values("% repetidos", ascending=False).iloc[0]
    bajo = por_depto3.sort_values("% repetidos").iloc[0]
    observacion(
        f"El mayor porcentaje de repetidos es de {alto['departamento']} "
        f"({dec(alto['% repetidos'])} % de {miles(alto['registros'])} "
        f"registros) y el menor de {bajo['departamento']} "
        f"({dec(bajo['% repetidos'])} %). El promedio del conjunto es "
        f"{dec(n_rep / len(df) * 100)} %.")

# ------------------------------------------------------------------ 4. por año
seccion("anio", "4. ¿Cambia el porcentaje de repetidos con el tiempo?")
c1, c2 = st.columns(2)
mostrar_tabla(por_anio3, ["repetidos", "registros"], ["% repetidos"], n=1,
              donde=c1, hide_index=True)
grafico(px.line(por_anio3, x="año", y="% repetidos", markers=True), c2)
if n_rep > 0:
    a_alto = por_anio3.sort_values("% repetidos", ascending=False).iloc[0]
    a_bajo = por_anio3.sort_values("% repetidos").iloc[0]
    desp = por_anio3[por_anio3["año"] > int(a_alto["año"])]
    texto = (f"El porcentaje anual de repetidos va de {dec(a_bajo['% repetidos'])} % "
             f"({int(a_bajo['año'])}) a {dec(a_alto['% repetidos'])} % "
             f"({int(a_alto['año'])}). ")
    if len(desp) > 0:
        texto += (f"Después del máximo, entre {int(desp['año'].min())} y "
                  f"{int(desp['año'].max())}, se mantiene entre "
                  f"{dec(desp['% repetidos'].min())} % y "
                  f"{dec(desp['% repetidos'].max())} %.")
    observacion(texto)

# ------------------------------------------------------------------ 5. sensibilidad por año
seccion("sensibilidad-anio", "5. Sensibilidad: casos por año con y sin repetidos")
sens = por_anio3[["año", "registros", "repetidos"]].copy()
sens["sin repetidos"] = sens["registros"] - sens["repetidos"]
sens = sens.rename(columns={"registros": "con repetidos"})
sens = sens[["año", "con repetidos", "sin repetidos"]]
c1, c2 = st.columns(2)
mostrar_tabla(sens, ["con repetidos", "sin repetidos"], donde=c1, hide_index=True)
grafico(px.line(sens, x="año", y=["con repetidos", "sin repetidos"], markers=True,
                labels={"value": "casos", "variable": ""}), c2)

con = sens.set_index("año")["con repetidos"]
sin = sens.set_index("año")["sin repetidos"]
pico_igual = con.idxmax() == sin.idxmax()
sube_baja = None
if len(con) > 1:
    mismo = (con.diff().dropna() > 0) == (sin.diff().dropna() > 0)
    sube_baja = (int(mismo.sum()), len(mismo))
texto = (f"El año con más casos es {int(con.idxmax())} con repetidos y "
         f"{int(sin.idxmax())} sin ellos" + (" (el mismo)." if pico_igual else " (cambia)."))
if sube_baja:
    texto += (f" En {sube_baja[0]} de {sube_baja[1]} variaciones año a año, las "
              "dos series suben o bajan en la misma dirección.")
observacion(texto)

# ------------------------------------------------------------------ 6. sensibilidad por departamento
seccion("sensibilidad-depto", "6. Sensibilidad: ranking de departamentos con y sin repetidos")
rk = pd.DataFrame({
    "departamento": por_depto3["departamento"],
    "con repetidos": por_depto3["registros"],
    "sin repetidos": por_depto3["registros"] - por_depto3["repetidos"]})
rk["puesto con"] = rk["con repetidos"].rank(ascending=False, method="min").astype(int)
rk["puesto sin"] = rk["sin repetidos"].rank(ascending=False, method="min").astype(int)
mostrar_tabla(rk.sort_values("puesto con"), ["con repetidos", "sin repetidos"],
              hide_index=True)
mismo_orden = bool((rk["puesto con"] == rk["puesto sin"]).all())
cambian = rk[rk["puesto con"] != rk["puesto sin"]]["departamento"].tolist()
if mismo_orden:
    observacion("El orden de los departamentos por número de casos es el "
                "mismo con y sin repetidos.")
else:
    observacion("El orden cambia en: " + ", ".join(cambian) + ". Revisa en la "
                "tabla qué tan cerca están sus cifras.")

# ------------------------------------------------------------------ decisión
seccion("decision", "Decisión sobre los repetidos")
decision("Las filas repetidas **no se eliminan**: la fuente no permite "
         "distinguir entre denuncias distintas y registros duplicados, y "
         "borrarlas sesgaría los conteos. Se conservan y se marcan con "
         "`es_repetido`, y los resultados clave se reportan con y sin ellas.")
detalle_rank = ("" if mismo_orden else
                " El orden de departamentos cambia solo en: " + ", ".join(cambian) + ".")
justificacion(
    "El año pico " + ("coincide" if pico_igual else "no coincide")
    + " con y sin repetidas"
    + (f" y {sube_baja[0]} de {sube_baja[1]} variaciones anuales van en la "
       "misma dirección" if sube_baja else "")
    + "." + detalle_rank
    + " La tendencia temporal es robusta; los cambios de puesto entre "
      "departamentos con cifras cercanas deben interpretarse con cautela.")
limitacion("La ausencia de un identificador único de caso impide saber si las "
           "filas repetidas son denuncias distintas o registros duplicados. "
           "Los resultados no prueban una cosa ni la otra.")
c1, c2 = st.columns(2)
with c1:
    ir_a("paginas/p5_atipicos.py",
         "Ver cómo afectan las repetidas a los atípicos")
with c2:
    ir_a("paginas/p4_descriptivas.py", "Siguiente: estadísticas descriptivas")