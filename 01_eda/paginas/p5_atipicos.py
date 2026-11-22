import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from contexto import contexto, datos_caribe
from estilo import (ACENTO, PRIMARIO, decision, dec, encabezado,
                    grafico, indice, ir_a, justificacion, limitacion, miles,
                    mostrar_tabla, observacion, ref, seccion)

# Convenciones elegidas por el autor (si se cambian, anotarlo en la bitácora)
UMBRAL_NIVEL = 10   # casos/mes de nivel local por debajo de los cuales el z es poco fiable
VENTANA = 13        # meses de la mediana móvil (nivel local)
Z_UMBRAL = 3.5      # desviaciones robustas a partir de las cuales un mes es atípico B

COLS_RAW = ["fecha_hecho", "departamento", "municipio", "codigo_dane", "delito",
            "genero", "grupo_etario", "armas_medios", "cantidad"]


@st.cache_data(show_spinner="Calculando los meses atípicos...")
def calcular(sel: tuple) -> dict:
    """Marca los atípicos con los criterios A y B, con y sin filas repetidas."""
    _, limpio = datos_caribe()
    df = limpio[limpio["departamento"].isin(sel)]

    ultima = df["fecha_hecho"].max()
    mes_ultimo = ultima.to_period("M").to_timestamp()
    parcial = ultima.day < ultima.days_in_month
    ultimo_completo = (mes_ultimo - pd.DateOffset(months=1)) if parcial else mes_ultimo
    meses_det = pd.date_range(df["mes"].min(), ultimo_completo, freq="MS")
    deptos_det = sorted(df["departamento"].unique())

    def conteo_mensual(d):
        """Casos por departamento y mes; los meses sin casos cuentan como 0."""
        cm = d.groupby(["departamento", "mes"]).size()
        idx = pd.MultiIndex.from_product([deptos_det, meses_det],
                                         names=["departamento", "mes"])
        return cm.reindex(idx, fill_value=0).reset_index(name="casos")

    def marcar(conteo):
        partes = []
        for dep, g in conteo.groupby("departamento"):
            g = g.sort_values("mes").copy()
            q1, q3 = g["casos"].quantile(0.25), g["casos"].quantile(0.75)
            iqr = q3 - q1
            g["lim_inf"] = max(q1 - 1.5 * iqr, 0)
            g["lim_sup"] = q3 + 1.5 * iqr
            g["tipo_iqr"] = ""
            g.loc[g["casos"] > g["lim_sup"], "tipo_iqr"] = "alto"
            g.loc[g["casos"] < g["lim_inf"], "tipo_iqr"] = "bajo"
            g["atipico_iqr"] = g["tipo_iqr"] != ""
            g["esperado"] = g["casos"].rolling(VENTANA, center=True,
                                               min_periods=7).median()
            res = g["casos"] - g["esperado"]
            mad = (res - res.median()).abs().median()
            g["z_robusto"] = (0.6745 * (res - res.median()) / mad
                              if mad > 0 else float("nan"))
            g["atipico_local"] = g["z_robusto"].abs() > Z_UMBRAL
            partes.append(g)
        m = pd.concat(partes, ignore_index=True)
        m["año"] = m["mes"].dt.year
        m["ambos"] = m["atipico_iqr"] & m["atipico_local"]
        m["nivel_bajo"] = m["esperado"] < UMBRAL_NIVEL
        return m

    return {"m5": marcar(conteo_mensual(df)),
            "m5_sin": marcar(conteo_mensual(df[~df["es_repetido"]])),
            "ultima": ultima, "mes_ultimo": mes_ultimo, "parcial": parcial,
            "meses_det": meses_det, "deptos_det": deptos_det}


c = contexto()
res = calcular(tuple(c.seleccion))
m5, m5_sin = res["m5"], res["m5_sin"]
meses_det, deptos_det = res["meses_det"], res["deptos_det"]

n_iqr = int(m5["atipico_iqr"].sum())
n_alto = int((m5["tipo_iqr"] == "alto").sum())
n_bajo = int((m5["tipo_iqr"] == "bajo").sum())
n_local = int(m5["atipico_local"].sum())
n_ambos = int(m5["ambos"].sum())
pct_ambos = (n_ambos / n_iqr * 100) if n_iqr else 0
n_local_bajo = int((m5["atipico_local"] & m5["nivel_bajo"]).sum())
solidos = m5[m5["ambos"] & ~m5["nivel_bajo"]]

claves_con = set(zip(m5.loc[m5["atipico_local"], "departamento"],
                     m5.loc[m5["atipico_local"], "mes"]))
claves_sin = set(zip(m5_sin.loc[m5_sin["atipico_local"], "departamento"],
                     m5_sin.loc[m5_sin["atipico_local"], "mes"]))
comunes = len(claves_con & claves_sin)
solo_con = len(claves_con - claves_sin)
solo_sin = len(claves_sin - claves_con)
pct_persist = (comunes / len(claves_con) * 100) if claves_con else 0

encabezado("5 · Atípicos",
           "¿Hay meses fuera de lo esperado y dependen de las filas repetidas?",
           "limpios, con las filas repetidas incluidas (la sensibilidad las excluye)")
st.caption("No hay variable numérica con varianza, así que los atípicos se buscan "
           "en los casos por mes y departamento.")
indice([("metodo", "Método"), ("criterio-a", "Criterio A"), ("anios", "Años"),
        ("criterio-b", "Criterio B"), ("candidatos", "Candidatos"),
        ("sensibilidad", "Sensibilidad"), ("decision", "Decisión")])

# ------------------------------------------------------------------ 1. método
seccion("metodo", "1. Método")
st.markdown(
    "Se cuentan los casos de cada mes por departamento y se aplican **dos "
    "criterios**:\n\n"
    "- **A. IQR global:** un mes es atípico si queda fuera de `Q1 − 1,5·IQR` y "
    "`Q3 + 1,5·IQR` de su departamento.\n"
    f"- **B. Local:** un mes es atípico si se aleja del nivel de su entorno "
    f"(mediana móvil de {VENTANA} meses) más de {dec(Z_UMBRAL)} desviaciones "
    "robustas (MAD). Detecta anomalías aunque la serie suba o baje.\n\n"
    "Como la serie cambia de nivel con los años, el criterio A usa límites muy "
    "amplios y marca pocos meses. Los meses marcados por **A y B** son los "
    "candidatos a anomalía real.")
nota = (f"Se analizan {len(meses_det)} meses por departamento "
        f"({meses_det.min():%m/%Y} a {meses_det.max():%m/%Y}); los meses sin casos "
        "cuentan como 0.")
if res["parcial"]:
    nota += (f" {res['mes_ultimo']:%m/%Y} está incompleto (último registro "
             f"{res['ultima']:%d/%m/%Y}) y se excluye de la detección; el dato "
             "se conserva.")
st.caption(nota)

# ------------------------------------------------------------------ 2. criterio A
seccion("criterio-a", "2. Criterio A: IQR global por departamento")
grafico(px.box(m5, x="departamento", y="casos", points="outliers"), alto=420)
resumen = (m5.groupby("departamento")
           .agg(meses=("casos", "size"), mediana=("casos", "median"),
                altos=("tipo_iqr", lambda s: int((s == "alto").sum())),
                bajos=("tipo_iqr", lambda s: int((s == "bajo").sum())),
                locales=("atipico_local", "sum"), ambos=("ambos", "sum"))
           .reset_index())
resumen["locales"] = resumen["locales"].astype(int)
resumen["ambos"] = resumen["ambos"].astype(int)
resumen = resumen.rename(columns={
    "meses": "meses analizados", "mediana": "mediana mensual",
    "altos": "atípicos altos (A)", "bajos": "atípicos bajos (A)",
    "locales": "atípicos locales (B)", "ambos": "en ambos (A y B)"})
mostrar_tabla(resumen, ["meses analizados", "atípicos altos (A)", "atípicos bajos (A)",
                        "atípicos locales (B)", "en ambos (A y B)"],
              ["mediana mensual"], n=1, hide_index=True)
pct_a = n_iqr / len(m5) * 100
observacion(
    f"El criterio A marca {miles(n_iqr)} meses atípicos ({miles(n_alto)} altos y "
    f"{miles(n_bajo)} bajos), el {dec(pct_a, 2)} % de los {miles(len(m5))} "
    f"meses-departamento. El criterio B marca {miles(n_local)}, y "
    f"{miles(n_ambos)} coinciden en los dos ({dec(pct_ambos)} % de los de A). "
    "Los demás de A se destacan frente a todo el periodo pero no frente a su "
    "entorno, lo que es compatible con meses de nivel alto. Además, el cambio "
    "de nivel ensancha el rango intercuartílico y puede ocultar anomalías en el "
    "criterio A. Los departamentos con conteos bajos tienen límites inestables.")

# ------------------------------------------------------------------ 3. por año (A)
seccion("anios", "3. ¿En qué años caen los atípicos del criterio A?")
if n_iqr:
    por_anio5 = (m5[m5["atipico_iqr"]].groupby(["año", "tipo_iqr"]).size()
                 .unstack(fill_value=0)
                 .reindex(columns=["alto", "bajo"], fill_value=0)
                 .rename(columns={"alto": "altos", "bajo": "bajos"}).reset_index())
    por_anio5["total"] = por_anio5["altos"] + por_anio5["bajos"]
    c1, c2 = st.columns(2)
    mostrar_tabla(por_anio5, ["altos", "bajos", "total"], donde=c1, hide_index=True)
    grafico(px.bar(por_anio5, x="año", y=["altos", "bajos"],
                   labels={"value": "meses atípicos", "variable": ""}), c2)
    orden = por_anio5.sort_values("total", ascending=False)
    top_a, top3_a = orden.iloc[0], orden.head(3)
    anios_top3 = ", ".join(top3_a.sort_values("año")["año"].astype(int).astype(str))
    primer_anio = int(por_anio5["año"].min())
    observacion(
        f"El año con más meses atípicos por A es {int(top_a['año'])} "
        f"({miles(top_a['total'])}, {dec(top_a['total'] / n_iqr * 100)} % del "
        f"total). Los tres años con más atípicos ({anios_top3}) reúnen el "
        f"{dec(top3_a['total'].sum() / n_iqr * 100)} %. El primer año con algún "
        f"atípico es {primer_anio}"
        + (" y todos son altos." if n_bajo == 0 else ".")
        + " Los atípicos de A se concentran en los años de nivel alto de la serie.")
    ir_a("paginas/p4_descriptivas.py", "Ver los niveles anuales de la serie")
else:
    observacion("El criterio A no marca meses atípicos en la selección actual.")

# ------------------------------------------------------------------ 4. criterio B
seccion("criterio-b", "4. Criterio B: atípicos respecto del nivel local")
dep_sel = st.selectbox("Departamento a ver en detalle", deptos_det, key="dep_detalle")
gs = m5[m5["departamento"] == dep_sel]
fig = go.Figure()
fig.add_trace(go.Scatter(x=gs["mes"], y=gs["casos"], mode="lines", name="casos",
                         line=dict(color=PRIMARIO, width=2)))
fig.add_trace(go.Scatter(x=gs["mes"], y=gs["esperado"], mode="lines",
                         name=f"nivel local (mediana de {VENTANA} meses)",
                         line=dict(color="#6C757D", dash="dash", width=2)))
aa = gs[gs["atipico_local"]]
fig.add_trace(go.Scatter(x=aa["mes"], y=aa["casos"], mode="markers",
                         name="atípico local",
                         marker=dict(color=ACENTO, size=11, symbol="x",
                                     line=dict(width=2))))
fig.update_layout(xaxis_title="mes", yaxis_title="casos",
                  legend=dict(orientation="h", y=1.12, x=0))
grafico(fig, alto=380)

st.markdown("**Los 15 meses más alejados de su nivel local** (todos los departamentos)")
top_loc = (m5[m5["atipico_local"]].assign(abs_z=lambda x: x["z_robusto"].abs())
           .sort_values("abs_z", ascending=False).head(15).copy())
if len(top_loc):
    tabla_loc = pd.DataFrame({
        "departamento": top_loc["departamento"],
        "mes": top_loc["mes"].dt.strftime("%m/%Y"),
        "casos": top_loc["casos"], "nivel local": top_loc["esperado"],
        "z robusto": top_loc["z_robusto"],
        f"nivel local < {UMBRAL_NIVEL}": top_loc["nivel_bajo"].map({True: "sí", False: "no"}),
        "también atípico en A": top_loc["atipico_iqr"].map({True: "sí", False: "no"})})
    mostrar_tabla(tabla_loc, ["casos"], ["nivel local", "z robusto"], n=1,
                  hide_index=True)
    r0 = top_loc.iloc[0]
    positivos = int((m5.loc[m5["atipico_local"], "casos"]
                     > m5.loc[m5["atipico_local"], "esperado"]).sum())
    observacion(
        f"El criterio B marca {miles(n_local)} meses. El más alejado es "
        f"{r0['departamento']} en {r0['mes']:%m/%Y}: {miles(r0['casos'])} casos "
        f"frente a un nivel local de {dec(r0['esperado'])} (z = "
        f"{dec(r0['z_robusto'])}). "
        + ("Todos están por encima de su nivel local. " if positivos == n_local
           else f"{miles(positivos)} de los {miles(n_local)} están por encima de "
                "su nivel local y el resto por debajo. ")
        + f"{miles(n_local_bajo)} de los {miles(n_local)} caen en meses con "
        f"nivel local menor que "
        f"{UMBRAL_NIVEL} casos, donde el z se infla con variaciones pequeñas y el "
        "resultado es poco fiable. Una desviación local no prueba un error: puede "
        "ser un aumento real, una carga masiva o un cambio de registro.")
else:
    observacion("El criterio B no marca meses atípicos en la selección actual.")

# ------------------------------------------------------------------ 5. candidatos
seccion("candidatos", "5. Candidatos a anomalía: marcados por A y B con nivel local suficiente")
st.caption(f"Meses atípicos por los dos criterios y con nivel local de al menos "
           f"{UMBRAL_NIVEL} casos al mes. Se indica si siguen siendo atípicos al "
           "quitar las filas repetidas.")
if len(solidos):
    cand = solidos[["departamento", "mes", "casos", "esperado", "z_robusto"]].merge(
        m5_sin[["departamento", "mes", "casos", "atipico_iqr", "atipico_local"]]
        .rename(columns={"casos": "casos sin rep.", "atipico_iqr": "A sin rep.",
                         "atipico_local": "B sin rep."}),
        on=["departamento", "mes"], how="left")
    cand["filas repetidas del mes"] = cand["casos"] - cand["casos sin rep."]
    cand["sigue atípico sin repetidas"] = (
        (cand["A sin rep."] & cand["B sin rep."]).map({True: "sí", False: "no"}))
    cand["mes"] = cand["mes"].dt.strftime("%m/%Y")
    cand = cand.rename(columns={"esperado": "nivel local", "z_robusto": "z robusto",
                                "casos": "casos con rep."})
    cand = cand[["departamento", "mes", "casos con rep.", "casos sin rep.",
                 "filas repetidas del mes", "nivel local", "z robusto",
                 "sigue atípico sin repetidas"]]
    mostrar_tabla(cand, ["casos con rep.", "casos sin rep.", "filas repetidas del mes"],
                  ["nivel local", "z robusto"], n=1, hide_index=True)
    persisten = int((cand["sigue atípico sin repetidas"] == "sí").sum())
    rmin = int(cand["filas repetidas del mes"].min())
    rmax = int(cand["filas repetidas del mes"].max())
    texto = (f"{len(cand)} de los {miles(n_ambos)} meses marcados por A y B tienen "
             f"nivel local de al menos {UMBRAL_NIVEL} casos; los otros "
             f"{miles(n_ambos - len(cand))} están en meses de conteos muy bajos. ")
    if persisten == 0:
        texto += ("Ninguno sigue siendo atípico al quitar las filas repetidas: "
                  "todos dependen de ellas. ")
    else:
        texto += (f"De esos {len(cand)}, {persisten} siguen siendo atípicos al "
                  f"quitar las filas repetidas; los otros {len(cand) - persisten} "
                  "dependen de ellas. ")
    texto += ("Cada uno de esos meses contiene "
              + (f"{miles(rmin)} filas" if rmin == rmax
                 else f"entre {miles(rmin)} y {miles(rmax)} filas")
              + " marcadas como repetidas.")
    observacion(texto)
else:
    observacion(f"Ningún mes marcado por A y B tiene nivel local de al menos "
                f"{UMBRAL_NIVEL} casos.")
ir_a("paginas/p3_duplicados.py", "Ver los grupos de filas repetidas")

# ------------------------------------------------------------------ 6. sensibilidad
seccion("sensibilidad", "6. Sensibilidad: atípicos con y sin filas repetidas")
comp = pd.DataFrame({
    "concepto": ["Atípicos criterio A (IQR global)", "Atípicos criterio B (local)",
                 "En ambos criterios"],
    "con repetidos": [n_iqr, n_local, n_ambos],
    "sin repetidos": [int(m5_sin["atipico_iqr"].sum()),
                      int(m5_sin["atipico_local"].sum()),
                      int(m5_sin["ambos"].sum())]})
mostrar_tabla(comp, ["con repetidos", "sin repetidos"], hide_index=True)


def tabla_claves(claves, base):
    k = pd.DataFrame(sorted(claves), columns=["departamento", "mes"])
    k = k.merge(base[["departamento", "mes", "casos", "esperado"]],
                on=["departamento", "mes"], how="left")
    k["mes"] = k["mes"].dt.strftime("%m/%Y")
    return k.rename(columns={"esperado": "nivel local"})


c1, c2 = st.columns(2)
c1.markdown("Atípicos locales (B) **solo con** las filas repetidas")
if solo_con:
    mostrar_tabla(tabla_claves(claves_con - claves_sin, m5), ["casos"],
                  ["nivel local"], n=1, donde=c1, hide_index=True)
else:
    c1.caption("Ninguno.")
c2.markdown("Atípicos locales (B) **solo sin** las filas repetidas")
if solo_sin:
    mostrar_tabla(tabla_claves(claves_sin - claves_con, m5_sin), ["casos"],
                  ["nivel local"], n=1, donde=c2, hide_index=True)
else:
    c2.caption("Ninguno.")

texto = (f"Con el criterio B, los meses atípicos en ambos escenarios son "
         f"{miles(comunes)} ({dec(pct_persist)} % de los {miles(len(claves_con))} "
         f"que lo son con repetidos); solo con las filas repetidas, "
         f"{miles(solo_con)}; solo sin ellas, {miles(solo_sin)}. ")
if pct_persist < 75:
    texto += ("El conjunto cambia de forma notable al quitar las repetidas: al "
              "cambiar los conteos mensuales también se mueven el nivel local y "
              "la desviación robusta, sobre todo en departamentos pequeños. ")

# Mes del grupo de filas idénticas más grande (página de duplicados)
grupos = c.raw.groupby(COLS_RAW, dropna=False).size()
grupos = grupos[grupos > 1]
if len(grupos) > 0:
    clave = grupos.idxmax()
    n_g = int(grupos.max())
    fecha_g = pd.Timestamp(clave[COLS_RAW.index("fecha_hecho")])
    mapa = (c.original.drop_duplicates("departamento_original")
            .set_index("departamento_original")["departamento_norm"])
    dep_g = mapa.get(clave[COLS_RAW.index("departamento")])
    mes_g = fecha_g.to_period("M").to_timestamp()
    fc = m5[(m5["departamento"] == dep_g) & (m5["mes"] == mes_g)]
    fs = m5_sin[(m5_sin["departamento"] == dep_g) & (m5_sin["mes"] == mes_g)]
    if len(fc) and len(fs):
        fc, fs = fc.iloc[0], fs.iloc[0]
        si_no = lambda v: "sí" if v else "no"
        dif = int(fc["casos"] - fs["casos"])
        texto += (
            f"El grupo más grande de filas idénticas ({miles(n_g)} filas, "
            f"{fecha_g:%d/%m/%Y}, {dep_g}) cae en {mes_g:%m/%Y}: ese mes tiene "
            f"{miles(fc['casos'])} casos con repetidos y {miles(fs['casos'])} sin "
            f"ellos (nivel local con repetidos {dec(fc['esperado'])}). La "
            f"diferencia de {miles(dif)} casos corresponde a filas marcadas como "
            f"repetidas en ese mes, de las cuales {miles(n_g - 1)} pertenecen a ese "
            "grupo. "
            f"Atípico por A: {si_no(fc['atipico_iqr'])} con y "
            f"{si_no(fs['atipico_iqr'])} sin repetidos; por B: "
            f"{si_no(fc['atipico_local'])} con y {si_no(fs['atipico_local'])} sin "
            "repetidos.")
observacion(texto)

# ------------------------------------------------------------------ decisión
seccion("decision", "Decisión sobre los valores atípicos")
decision(
    "Los atípicos **no se eliminan ni se corrigen**: se identifican, se "
    "analizan y se conservan. Se usan dos criterios (IQR global y desviación "
    "local) y se consideran candidatos a anomalía real los meses marcados por "
    f"ambos con un nivel local de al menos {UMBRAL_NIVEL} casos al mes. El último "
    "mes, si está incompleto, no entra en la detección. Los resultados se "
    "reportan con y sin filas repetidas.")
justificacion(
    f"La serie mensual cambia de nivel con los años ({ref('criterio-a', 'apartado 2')}). "
    f"El IQR global marca pocos meses ({miles(n_iqr)}) porque ese cambio ensancha "
    f"los límites, y solo {miles(n_ambos)} ({dec(pct_ambos)} %) coinciden con el "
    "criterio local, por lo que se usan los dos. Al quitar las filas repetidas, "
    f"solo el {dec(pct_persist)} % de los atípicos locales se mantiene "
    f"({ref('sensibilidad', 'apartado 6')}), de modo que el criterio B es sensible "
    f"a esa decisión. Además, {miles(n_local_bajo)} de los {miles(n_local)} "
    f"atípicos locales están en meses con nivel local menor que {UMBRAL_NIVEL} "
    "casos, donde una variación pequeña da un z elevado; por eso los candidatos "
    f"más sólidos son los {len(solidos)} marcados por ambos criterios con nivel "
    f"local suficiente ({ref('candidatos', 'apartado 5')}). Un mes atípico puede "
    "deberse a un aumento real, a una carga masiva o a un cambio de registro, y "
    "con estos datos no se puede distinguir.")
limitacion(
    "Los departamentos con conteos bajos tienen límites inestables. Los "
    f"umbrales ({dec(Z_UMBRAL)} desviaciones, ventana de {VENTANA} meses y nivel "
    f"local de {UMBRAL_NIVEL} casos) son convenciones, no verdades. La fuente "
    "indica que sus cifras están sujetas a variación por consolidación con la "
    "Fiscalía.")
c1, c2 = st.columns(2)
with c1:
    ir_a("paginas/p3_duplicados.py", "Volver a los duplicados")
with c2:
    ir_a("paginas/p6_relaciones.py", "Siguiente: distribuciones y relaciones")