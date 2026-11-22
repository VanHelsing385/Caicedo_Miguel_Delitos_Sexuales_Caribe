import pandas as pd
import plotly.express as px
import streamlit as st

from contexto import (CARIBE, FECHA_EXTRACCION, NOMBRES_CSV_CARIBE,
                      datos_caribe, nacional, resumen_nacional)
from estilo import (ACENTO, CFG, GRIS, decision, dec, encabezado, grafico,
                    indice, ir_a, justificacion, kpi, limitacion, miles,
                    mostrar_df, mostrar_tabla, observacion, seccion)

nac = nacional()
original, _ = datos_caribe()
res = resumen_nacional()

encabezado("1 · Carga y estructura",
           "¿Qué contiene el archivo original y cómo se obtiene la región Caribe?",
           "originales, tal como vienen de la fuente")
indice([("fuente", "Fuente"), ("estructura", "Estructura"),
        ("calidad", "Calidad del archivo"), ("filtro", "Filtro del Caribe"),
        ("caribe", "Conjunto del Caribe")])

# ------------------------------------------------------------------ fuente
seccion("fuente", "Fuente")
c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Registros del archivo", miles(len(nac)))
kpi(c2, "Departamentos", nac["departamento"].nunique())
kpi(c3, "Periodo",
    f"{nac['fecha_hecho'].min():%Y} – {nac['fecha_hecho'].max():%Y}",
    f"Del {nac['fecha_hecho'].min():%d/%m/%Y} al {nac['fecha_hecho'].max():%d/%m/%Y}.")
kpi(c4, "Datos extraídos", f"{FECHA_EXTRACCION:%d/%m/%Y}")
st.caption("Reporte de delitos sexuales, DIJIN – Policía Nacional. Cifras sujetas "
           "a variación (integración y consolidación con la Fiscalía). El "
           "conjunto no incluye diccionario de variables.")

# ------------------------------------------------------------------ estructura
seccion("estructura", "1. Estructura del archivo completo")
st.write("Primeras filas, tal como vienen en el archivo")
mostrar_df(nac.drop(columns=["id"]).head(12), column_config=CFG, hide_index=True)


def tipo_legible(dtype) -> str:
    nombre = str(dtype)
    if nombre.startswith("datetime"):
        return "fecha"
    if nombre.startswith(("int", "Int")):
        return "entero"
    return "texto"


cols_arch = [c for c in nac.columns if c != "id"]
primer = nac[cols_arch].iloc[0].astype(str).str.replace(" 00:00:00", "", regex=False)
estructura = pd.DataFrame({
    "tipo": [tipo_legible(nac[c].dtype) for c in cols_arch],
    "valores únicos": [nac[c].nunique() for c in cols_arch],
    "primer valor": primer.values,
}, index=cols_arch)
mostrar_tabla(estructura, miles_cols=["valores únicos"])
observacion(f"El archivo tiene {miles(len(nac))} registros y {len(cols_arch)} "
            "columnas. Casi todas son categóricas; `cantidad` es la única "
            "numérica. La lectura conserva todas las filas: no se elimina "
            "ningún registro.")

# ------------------------------------------------------------------ calidad
seccion("calidad", "2. Calidad del archivo completo (todo el país)")
c1, c2, c3 = st.columns(3)
kpi(c1, "Filas repetidas (excedentes)", miles(res["excedentes"]),
    "Filas idénticas en todas las columnas a otra anterior.")
kpi(c2, "Grupos de filas idénticas", miles(res["grupos"]))
kpi(c3, "«NO REPORTA» en género", miles(res["no_reporta_genero"]))
tabla_nulos = res["nulos"]
mostrar_tabla(tabla_nulos, ["nulos"], ["% del total"])
n_gen = int(tabla_nulos.loc["genero", "nulos"])
n_eta = int(tabla_nulos.loc["grupo_etario", "nulos"])
observacion(f"En todo el país hay {miles(n_gen)} nulos en `genero` "
            f"({dec(tabla_nulos.loc['genero', '% del total'], 2)} %) y "
            f"{miles(n_eta)} en `grupo_etario` "
            f"({dec(tabla_nulos.loc['grupo_etario', '% del total'], 2)} %); las "
            f"demás columnas están completas. Además, {miles(res['excedentes'])} "
            f"filas ({dec(res['excedentes'] / len(nac) * 100)} %) repiten a otra "
            "anterior. El análisis detallado se hace sobre la región Caribe.")
c1, c2 = st.columns(2)
with c1:
    ir_a("paginas/p2_faltantes.py", "Valores faltantes de la región Caribe")
with c2:
    ir_a("paginas/p3_duplicados.py", "Duplicados de la región Caribe")

# ------------------------------------------------------------------ filtro
seccion("filtro", "3. Filtro de la región Caribe")
st.write("La región Caribe se selecciona con los **dos primeros dígitos del "
         "código DANE** de cada registro.")

por_cod = (original.groupby("cod_depto")
           .agg(registros=("id", "size"),
                nombre_csv=("departamento_original",
                            lambda s: " / ".join(sorted(s.unique()))))
           .reset_index())
por_cod["nombre oficial"] = por_cod["cod_depto"].map(CARIBE)
por_cod["% del Caribe"] = (por_cod["registros"] / len(original) * 100).round(1)
tabla_dep = (por_cod.rename(columns={"cod_depto": "código", "nombre_csv": "nombre en el CSV"})
             [["código", "nombre oficial", "nombre en el CSV", "registros", "% del Caribe"]]
             .sort_values("registros", ascending=False))

mostrar_tabla(tabla_dep, ["registros"], ["% del Caribe"], n=1, hide_index=True)

por_depto = res["por_depto"].copy()
por_depto["región"] = por_depto["departamento"].isin(NOMBRES_CSV_CARIBE).map(
    {True: "Caribe", False: "Resto del país"})
orden = por_depto.sort_values("registros", ascending=False)["departamento"].tolist()
st.markdown("**Registros por departamento en todo el archivo** (la región Caribe, "
            "en naranja)")
fig = px.bar(por_depto, x="registros", y="departamento", color="región",
             orientation="h", category_orders={"departamento": orden},
             color_discrete_map={"Caribe": ACENTO, "Resto del país": GRIS},
             labels={"departamento": "", "registros": "registros"})
grafico(fig, alto=120 + 22 * len(por_depto), fmt_x=",d")

por_codigo = len(original)
por_nombre = int(nac["departamento"].isin(NOMBRES_CSV_CARIBE).sum())
c1, c2, c3 = st.columns(3)
kpi(c1, "Por código DANE", miles(por_codigo))
kpi(c2, "Por nombre de departamento", miles(por_nombre))
kpi(c3, "Participación en el archivo", f"{dec(por_codigo / len(nac) * 100)} %")

coincide = por_codigo == por_nombre
observacion(
    f"El archivo contiene {nac['departamento'].nunique()} valores distintos de "
    f"departamento. El filtro por código DANE selecciona {miles(por_codigo)} "
    f"registros ({dec(por_codigo / len(nac) * 100)} % del archivo) y el filtro "
    f"por nombre {miles(por_nombre)}: "
    + ("los dos criterios seleccionan exactamente los mismos registros."
       if coincide else "los dos criterios no coinciden; revisar.")
)

distintos = tabla_dep[tabla_dep["nombre en el CSV"].str.casefold()
                      != tabla_dep["nombre oficial"].str.casefold()]
ejemplos = "; ".join(f"«{r['nombre en el CSV']}» en lugar de «{r['nombre oficial']}»"
                     for _, r in distintos.iterrows())
decision("La región Caribe se filtra por el **código DANE**, no por el nombre. "
         "El filtro es una selección sobre una copia: el archivo original no "
         "se modifica y ningún registro se elimina.")
justificacion(
    "Los nombres del CSV no siguen la nomenclatura oficial"
    + (f" ({ejemplos})" if ejemplos else "")
    + ", mientras que el código DANE es un identificador estable. La "
      "validación cruzada confirma que ambos criterios seleccionan los "
      "mismos registros."
)

# ------------------------------------------------------------------ Caribe
seccion("caribe", "4. Conjunto de la región Caribe")
c1, c2, c3 = st.columns(3)
kpi(c1, "Registros del Caribe", miles(len(original)))
kpi(c2, "Departamentos", original["cod_depto"].nunique())
kpi(c3, "Valores de `cantidad`", ", ".join(map(str, sorted(original["cantidad"].unique()))))

muestra = original[["fecha_hecho", "departamento_original", "municipio",
                    "codigo_dane", "delito", "genero", "grupo_etario",
                    "armas_medios", "cantidad"]].head(10)
mostrar_df(muestra.rename(columns={"departamento_original": "departamento"}),
           column_config=CFG, hide_index=True)

cant_const = original["cantidad"].nunique() == 1
observacion(
    f"El conjunto del Caribe tiene {miles(len(original))} registros. "
    + ("`cantidad` vale 1 en todos: es una constante, no aporta información "
       "y cada fila equivale a un caso."
       if cant_const else "`cantidad` toma varios valores.")
)
limitacion("Las filas son denuncias registradas, no la ocurrencia real de los "
           "hechos, y el archivo no tiene identificador de caso.")
ir_a("paginas/p2_faltantes.py", "Siguiente: valores faltantes")