import pandas as pd
import plotly.express as px
import streamlit as st

from contexto import contexto
from estilo import (decision, dec, encabezado, grafico, indice, ir_a,
                    justificacion, limitacion, miles, mostrar_tabla,
                    observacion, ref, seccion)

UMBRAL_ALTO = 15   # % de «NO REPORTA» a partir del cual un año se considera alto
CORTE = 2018       # año que separa los dos periodos del análisis de nulos

c = contexto()
raw, df = c.raw, c.df
raw = raw.assign(dep=raw["departamento_norm"])   # nombre oficial para las tablas
COLS_RAW = ["fecha_hecho", "departamento", "municipio", "codigo_dane", "delito",
            "genero", "grupo_etario", "armas_medios", "cantidad"]

n = len(raw)
total_nulos = int(raw["genero"].isna().sum())
nulos_eta = int(raw["grupo_etario"].isna().sum())
p_gen = total_nulos / n * 100
p_eta = nulos_eta / n * 100

encabezado("2 · Valores faltantes",
           "¿Qué datos faltan, en qué periodos y territorios se concentran y "
           "cómo se tratan?",
           "originales (antes de la limpieza); el último apartado los compara "
           "con los datos limpios")
st.caption("Esta página analiza los datos originales porque, después de la "
           "limpieza, los nulos ya no existen. Las cifras del archivo completo "
           "están en la página de carga.")
indice([("columnas", "Nulos por columna"), ("noreporta", "«NO REPORTA»"),
        ("medio", "Medio por año"), ("genero-anio", "Género por año"),
        ("departamento", "Por departamento"), ("cruce", "Departamento y periodo"),
        ("decision", "Decisión"), ("limpieza", "Resultado de la limpieza")])

# ------------------------------------------------------------------ 1. por columna
seccion("columnas", "1. Valores nulos por columna")
nulos = raw[COLS_RAW].isna().sum()
tabla_nulos = pd.DataFrame({"nulos": nulos,
                            "% del total": (nulos / n * 100).round(2)})
c1, c2 = st.columns(2)
mostrar_tabla(tabla_nulos, ["nulos"], ["% del total"], donde=c1)
con_nulos = tabla_nulos[tabla_nulos["nulos"] > 0].reset_index(names="columna")
if len(con_nulos):
    grafico(px.bar(con_nulos, x="columna", y="% del total", text="nulos"), c2)
    detalle = "; ".join(f"`{r['columna']}`: {miles(r['nulos'])} nulos "
                        f"({dec(r['% del total'], 2)} %)"
                        for _, r in con_nulos.iterrows())
    sin_nulos = int((tabla_nulos["nulos"] == 0).sum())
    observacion(f"Sobre {miles(n)} registros, solo {len(con_nulos)} columna(s) "
                f"tienen nulos: {detalle}. Las otras {sin_nulos} columnas "
                "están completas.")
else:
    observacion("Ninguna columna tiene nulos en la selección actual.")

# ------------------------------------------------------------------ 2. NO REPORTA
seccion("noreporta", "2. Categorías «NO REPORTA» (declaradas por la fuente)")
sentinela = {}
for col in ["genero", "grupo_etario", "armas_medios", "municipio"]:
    s = raw[col].dropna().astype(str).str.upper()
    sentinela[col] = int(s.str.startswith("NO REPORT").sum())
tabla_sent = pd.DataFrame({
    "filas": sentinela,
    "% del total": {k: round(v / n * 100, 2) for k, v in sentinela.items()}})
c1, c2 = st.columns(2)
mostrar_tabla(tabla_sent, ["filas"], ["% del total"], donde=c1)
con_sent = {k: v for k, v in sentinela.items() if v > 0}
with c2:
    if con_sent:
        detalle = "; ".join(f"`{k}`: {miles(v)} filas ({dec(v / n * 100, 2)} %)"
                            for k, v in con_sent.items())
        mayor_col = max(con_sent, key=con_sent.get)
        observacion(
            f"La fuente declara el dato como no reportado en: {detalle}. Es "
            "distinto de un nulo: aquí la fuente escribió la categoría; en un "
            "nulo el campo llegó vacío. La columna donde pesa más es "
            f"`{mayor_col}` ({dec(con_sent[mayor_col] / n * 100, 2)} %).")
    else:
        observacion("La fuente no usa la categoría «NO REPORTA» en estas "
                    "columnas para la selección actual.")

# ------------------------------------------------------------------ 3. medio por año
seccion("medio", "3. ¿Cuándo se concentra el «NO REPORTA» en `armas_medios`?")
marca_arm = raw.assign(nr=raw["armas_medios"].fillna("").astype(str)
                       .str.upper().str.startswith("NO REPORT"))
arm_anio = (marca_arm.groupby("año")["nr"]
            .agg(**{"no reporta": "sum", "total": "size"}).reset_index())
arm_anio["no reporta"] = arm_anio["no reporta"].astype(int)
arm_anio["% no reporta"] = (arm_anio["no reporta"] / arm_anio["total"] * 100).round(2)
c1, c2 = st.columns(2)
mostrar_tabla(arm_anio, ["no reporta", "total"], ["% no reporta"],
              donde=c1, hide_index=True)
grafico(px.line(arm_anio, x="año", y="% no reporta", markers=True), c2)

nr_lab = next((v for v in raw["armas_medios"].dropna().unique()
               if str(v).upper().startswith("NO REPORT")), "NO REPORTA")
tot_nr = int(arm_anio["no reporta"].sum())
if tot_nr > 0:
    primero, ultimo = arm_anio.iloc[0], arm_anio.iloc[-1]
    a_max = arm_anio.sort_values("% no reporta", ascending=False).iloc[0]
    altos = arm_anio[arm_anio["% no reporta"] > UMBRAL_ALTO]
    bajos = arm_anio[arm_anio["% no reporta"] < 0.1]
    texto = (f"En {int(primero['año'])} el porcentaje de «{nr_lab}» en "
             f"`armas_medios` era {dec(primero['% no reporta'], 2)} %; el "
             f"máximo se alcanza en {int(a_max['año'])} "
             f"({dec(a_max['% no reporta'], 2)} %) y en {int(ultimo['año'])} es "
             f"{dec(ultimo['% no reporta'], 2)} %. ")
    if len(altos):
        lista = ", ".join(altos["año"].astype(int).astype(str))
        texto += (f"Los años por encima de {UMBRAL_ALTO} % son {lista} y reúnen "
                  f"el {dec(altos['no reporta'].sum() / tot_nr * 100)} % de todos "
                  "los «no reportado». ")
    if len(bajos):
        desde = int(bajos["año"].min())
        if (arm_anio[arm_anio["año"] >= desde]["% no reporta"] < 0.1).all():
            texto += f"Desde {desde} el porcentaje es inferior a 0,1 %. "
    texto += ("Un cambio tan marcado entre años sugiere que el criterio de "
              "registro del medio no es comparable en todo el periodo.")
    observacion(texto)
    ir_a("paginas/p4_descriptivas.py",
         "Ver el medio utilizado en las estadísticas descriptivas")

# ------------------------------------------------------------------ 4. género por año
seccion("genero-anio", "4. ¿Los nulos de género se concentran en algún periodo?")
marcado = raw.assign(nulo=raw["genero"].isna())
por_anio = (marcado.groupby("año")["nulo"]
            .agg(nulos="sum", total="size").reset_index())
por_anio["nulos"] = por_anio["nulos"].astype(int)
por_anio["% nulos"] = (por_anio["nulos"] / por_anio["total"] * 100).round(2)
c1, c2 = st.columns(2)
mostrar_tabla(por_anio, ["nulos", "total"], ["% nulos"], donde=c1, hide_index=True)
grafico(px.bar(por_anio, x="año", y="nulos", hover_data=["total", "% nulos"]), c2)

if total_nulos > 0:
    top = por_anio.sort_values("nulos", ascending=False).iloc[0]
    anios_cero = por_anio[por_anio["nulos"] == 0]["año"].astype(int).tolist()
    pre = marcado[marcado["año"] < CORTE]["nulo"]
    post = marcado[marcado["año"] >= CORTE]["nulo"]
    texto = (f"El año con más nulos de género es {int(top['año'])}, con "
             f"{miles(top['nulos'])} ({dec(top['nulos'] / total_nulos * 100)} % "
             f"del total y {dec(top['% nulos'], 2)} % de los registros de ese "
             "año). ")
    if len(pre) > 0 and len(post) > 0:
        texto += (f"Antes de {CORTE} hubo {miles(pre.sum())} nulos "
                  f"({dec(pre.mean() * 100, 2)} % de los registros); desde "
                  f"{CORTE}, {miles(post.sum())} ({dec(post.mean() * 100, 2)} %), "
                  f"es decir el {dec(post.sum() / total_nulos * 100)} % de todos "
                  "los nulos. ")
    if anios_cero:
        texto += "Años sin ningún nulo: " + ", ".join(map(str, anios_cero)) + "."
    observacion(texto)
else:
    observacion("No hay nulos de género en la selección actual.")

# ------------------------------------------------------------------ 5. por departamento
seccion("departamento", "5. ¿Y por departamento?")
por_depto = (marcado.groupby("dep")["nulo"]
             .agg(nulos="sum", total="size").reset_index()
             .rename(columns={"dep": "departamento"}))
por_depto["nulos"] = por_depto["nulos"].astype(int)
por_depto["% nulos"] = (por_depto["nulos"] / por_depto["total"] * 100).round(2)
mostrar_tabla(por_depto.sort_values("nulos", ascending=False),
              ["nulos", "total"], ["% nulos"], hide_index=True)
if total_nulos > 0:
    mayor_abs = por_depto.sort_values("nulos", ascending=False).iloc[0]
    mayor_pct = por_depto.sort_values("% nulos", ascending=False).iloc[0]
    observacion(
        f"{mayor_abs['departamento']} tiene más nulos en términos absolutos "
        f"({miles(mayor_abs['nulos'])}, "
        f"{dec(mayor_abs['nulos'] / total_nulos * 100)} % del total). El mayor "
        f"porcentaje es de {mayor_pct['departamento']} "
        f"({dec(mayor_pct['% nulos'], 2)} % de sus {miles(mayor_pct['total'])} "
        f"registros), frente a {dec(p_gen, 2)} % del conjunto. El número "
        "absoluto depende del tamaño del departamento; el porcentaje permite "
        "compararlos.")

# ------------------------------------------------------------------ 6. cruce
seccion("cruce", "6. Departamento y periodo juntos")
st.caption("¿La diferencia entre departamentos es real o se explica porque los "
           "nulos están concentrados en los años recientes?")
etq_pre, etq_post = f"2010-{CORTE - 1}", f"{CORTE} en adelante"
marcado["periodo"] = marcado["año"].apply(
    lambda a: etq_post if a >= CORTE else etq_pre)
cruce = (marcado.groupby(["dep", "periodo"])["nulo"]
         .agg(nulos="sum", total="size").reset_index()
         .rename(columns={"dep": "departamento"}))
cruce["nulos"] = cruce["nulos"].astype(int)
cruce["% nulos"] = (cruce["nulos"] / cruce["total"] * 100).round(2)
mostrar_tabla(cruce, ["nulos", "total"], ["% nulos"], hide_index=True)

reciente = (cruce[cruce["periodo"] == etq_post]
            .sort_values("% nulos", ascending=False))
antes = cruce[cruce["periodo"] == etq_pre]
if total_nulos > 0 and len(reciente) > 1:
    r1, r2 = reciente.iloc[0], reciente.iloc[1]
    texto = (f"Desde {CORTE}, {r1['departamento']} tiene el mayor porcentaje "
             f"({dec(r1['% nulos'], 2)} % de {miles(r1['total'])} registros), "
             f"frente a {dec(r2['% nulos'], 2)} % de {r2['departamento']}, el "
             "segundo. ")
    if r2["% nulos"] > 0:
        texto += (f"Es {dec(r1['% nulos'] / r2['% nulos'])} veces el porcentaje "
                  "del segundo. ")
    if len(antes):
        texto += (f"Antes de {CORTE}, el máximo porcentaje departamental fue "
                  f"{dec(antes['% nulos'].max(), 2)} %. Si el departamento "
                  "destaca incluso dentro del mismo periodo, la diferencia no "
                  "se explica solo por el tiempo.")
    observacion(texto)

# ------------------------------------------------------------------ decisión
seccion("decision", "Decisión sobre los valores faltantes")
decision("No se imputa con la moda: los nulos de `genero` y `grupo_etario` se "
         "reemplazan por la categoría `SIN DATO`, y «NO REPORTA» se conserva "
         "como categoría propia de la fuente (incluido `armas_medios`). Para "
         "el medio utilizado se reportan el periodo completo y 2021 en "
         "adelante.")
justificacion(
    f"El porcentaje global de nulos es bajo (`genero` {dec(p_gen, 2)} %, "
    f"`grupo_etario` {dec(p_eta, 2)} %), pero los nulos de género no se "
    f"distribuyen al azar en el tiempo ({ref('genero-anio', 'apartado 4')}). "
    "Imputar con la categoría más frecuente introduciría sesgo en un tema "
    "sensible, mientras que una categoría explícita deja visible el dato "
    "faltante y permite medir su peso. El «NO REPORTA» del medio cambia de "
    f"forma marcada entre años ({ref('medio', 'apartado 3')}), así que su "
    "evolución no se interpreta como cambio de conducta.")
limitacion(
    "Los análisis de género de los años recientes tienen una categoría `SIN "
    "DATO` algo mayor, y el medio utilizado no es comparable en todo el "
    "periodo. La fuente indica que actualizó sus cifras con una nueva "
    "metodología de validación con la Fiscalía, sin precisar desde cuándo; "
    "con estos datos no se puede atribuir estos cambios a una causa.")

# ------------------------------------------------------------------ resultado de la limpieza
seccion("limpieza", "7. Resultado de la limpieza (antes / después)")
con_ct = int(raw["municipio"].str.contains(r"\(CT\)", na=False).sum())
ct_despues = int(df["municipio"].str.contains(r"\(CT\)", na=False).sum())
sd_gen = int((df["genero"] == "SIN DATO").sum())
sd_eta = int((df["grupo_etario"] == "SIN DATO").sum())
ba = pd.DataFrame({"antes": [total_nulos, nulos_eta, con_ct],
                   "después": [sd_gen, sd_eta, ct_despues]},
                  index=["genero: nulos → 'SIN DATO'",
                         "grupo_etario: nulos → 'SIN DATO'",
                         "municipio: con sufijo (CT)"])
mostrar_tabla(ba, ["antes", "después"])
coincide = (sd_gen == total_nulos and sd_eta == nulos_eta)
observacion(
    ("La cantidad de `SIN DATO` coincide con los nulos originales, así que "
     "ningún valor se perdió ni se creó. " if coincide else
     "La cantidad de `SIN DATO` no coincide con los nulos originales; revisar "
     "la limpieza. ")
    + f"El sufijo «(CT)» aparecía en {miles(con_ct)} registros y quedan "
      f"{miles(ct_despues)}. El total de registros se mantiene en "
      f"{miles(len(df))}.")
st.caption("En `municipio` se elimina el sufijo «(CT)» para que un mismo "
           "municipio no aparezca con dos nombres. El sufijo marca la capital "
           "del departamento y se conserva en la columna `es_capital`. "
           "Ningún registro se elimina.")
ir_a("paginas/p3_duplicados.py", "Siguiente: duplicados")
