import pandas as pd
import plotly.express as px
import streamlit as st

from contexto import contexto
from estilo import (CFG, decision, dec, encabezado, frecuencias, grafico,
                    indice, ir_a, justificacion, kpi, limitacion, miles,
                    mostrar_df, mostrar_tabla, observacion, pct_no_reporta,
                    ref, seccion)

CORTE_MEDIO = 2021   # desde este año se reporta aparte el medio utilizado
TOP_MEDIO = 15       # máximo de categorías del medio que se muestran
TOP_DELITOS = 10     # máximo de delitos que se muestran

c = contexto()
df = c.df
COLS_LIMPIO = ["fecha_hecho", "departamento", "municipio", "codigo_dane",
               "delito", "genero", "grupo_etario", "armas_medios", "cantidad"]

encabezado("4 · Estadísticas descriptivas",
           "¿Cómo se ven los datos ya limpios?",
           "limpios (después de las decisiones de calidad), con las filas "
           "repetidas incluidas")
st.caption("Son denuncias registradas, no la ocurrencia real de los hechos. La "
           "sensibilidad a las filas repetidas se vio en la página de duplicados.")
indice([("muestra", "Muestra"), ("cantidad", "Cantidad"), ("anio", "Por año"),
        ("mes", "Por mes"), ("genero", "Género y grupo etario"),
        ("medio", "Medio utilizado"), ("delito", "Delitos"),
        ("coherencia", "Coherencia"), ("departamento", "Departamentos"),
        ("decision", "Decisión")])

# ------------------------------------------------------------------ 1. muestra
seccion("muestra", "1. Muestra de los datos limpios")
mostrar_df(df[COLS_LIMPIO].head(15), column_config=CFG, hide_index=True)
nulos_restantes = int(df[COLS_LIMPIO].isna().sum().sum())
ct_restante = int(df["municipio"].str.contains(r"\(CT\)", na=False).sum())
observacion(
    f"{miles(len(df))} registros y {len(COLS_LIMPIO)} columnas. Tras la "
    f"limpieza quedan {miles(nulos_restantes)} nulos y {miles(ct_restante)} "
    "municipios con sufijo «(CT)». "
    + ("Los reemplazos se aplicaron a todas las filas."
       if nulos_restantes == 0 and ct_restante == 0
       else "Revisar la limpieza: no se aplicó a todas las filas."))

# ------------------------------------------------------------------ 2. cantidad
seccion("cantidad", "2. Variable numérica: `cantidad`")
cant = df[["cantidad"]].describe().T
mostrar_tabla(cant, ["count"], [x for x in cant.columns if x != "count"])
if df["cantidad"].nunique() == 1:
    observacion(f"`cantidad` vale {int(df['cantidad'].iloc[0])} en los "
                f"{miles(len(df))} registros (desviación estándar 0). Es una "
                "constante: no aporta información y cada fila equivale a un caso.")
else:
    observacion(f"`cantidad` varía entre {df['cantidad'].min()} y "
                f"{df['cantidad'].max()} (media {dec(df['cantidad'].mean(), 2)}).")

# ------------------------------------------------------------------ 3. por año
seccion("anio", "3. Registros por año")
por_anio4 = df.groupby("año").size().reset_index(name="registros")
por_anio4["% del total"] = (por_anio4["registros"] / len(df) * 100).round(1)
por_anio4["variación % anual"] = (por_anio4["registros"].pct_change() * 100).round(1)
c1, c2 = st.columns(2)
mostrar_tabla(por_anio4, ["registros"], ["% del total", "variación % anual"],
              n=1, donde=c1, hide_index=True)
grafico(px.bar(por_anio4, x="año", y="registros"), c2)

ultima_fecha = df["fecha_hecho"].max()
ultimo_anio = int(ultima_fecha.year)
meses_ult = int(ultima_fecha.month)
parcial = meses_ult < 12
completos = por_anio4[por_anio4["año"] < ultimo_anio] if parcial else por_anio4
var_ok = completos.dropna(subset=["variación % anual"])
pico = por_anio4.sort_values("registros", ascending=False).iloc[0]
texto = (f"El año con más registros es {int(pico['año'])} "
         f"({miles(pico['registros'])}, {dec(pico['% del total'])} % del total). ")
if len(var_ok):
    sube = var_ok.sort_values("variación % anual", ascending=False).iloc[0]
    baja = var_ok.sort_values("variación % anual").iloc[0]
    texto += (f"Entre años completos, la mayor subida es la de {int(sube['año'])} "
              f"({dec(sube['variación % anual'])} %) y la mayor caída la de "
              f"{int(baja['año'])} ({dec(baja['variación % anual'])} %). ")
if parcial:
    ant = por_anio4[por_anio4["año"] == ultimo_anio - 1]
    reg_ult = int(por_anio4[por_anio4["año"] == ultimo_anio]["registros"].iloc[0])
    texto += (f"{ultimo_anio} es un año incompleto (último registro: "
              f"{ultima_fecha:%d/%m/%Y}), así que su variación anual no es "
              "comparable. ")
    if len(ant):
        texto += (f"Por promedio mensual, {ultimo_anio} tiene "
                  f"{dec(reg_ult / meses_ult)} registros por mes frente a "
                  f"{dec(int(ant['registros'].iloc[0]) / 12)} en {ultimo_anio - 1}. ")
texto += ("Estos conteos mezclan hechos con cambios en la denuncia y el "
          "registro; el aumento no se interpreta como más delitos.")
observacion(texto)

# ------------------------------------------------------------------ 4. por mes
seccion("mes", "4. Casos por mes")
st.caption("Como `cantidad` es constante, las estadísticas numéricas se "
           "calculan sobre el número de casos de cada mes.")
mensual = df.groupby("mes").size().reset_index(name="casos")
cm = mensual["casos"]
cv = cm.std() / cm.mean() * 100
resumen_m = pd.DataFrame([{"meses": len(cm), "media": cm.mean(),
                           "mediana": cm.median(), "desv. estándar": cm.std(),
                           "mínimo": cm.min(), "máximo": cm.max(),
                           "coef. variación (%)": cv}])
mostrar_tabla(resumen_m, ["meses", "mínimo", "máximo"],
              ["media", "mediana", "desv. estándar", "coef. variación (%)"],
              n=1, hide_index=True)
grafico(px.line(mensual, x="mes", y="casos"))
mes_max = mensual.sort_values("casos", ascending=False).iloc[0]
mes_min = mensual.sort_values("casos").iloc[0]
observacion(
    f"En {len(cm)} meses, la media es {dec(cm.mean())} casos y la mediana "
    f"{dec(cm.median())}. El máximo es {miles(mes_max['casos'])} "
    f"({mes_max['mes']:%m/%Y}) y el mínimo {miles(mes_min['casos'])} "
    f"({mes_min['mes']:%m/%Y}). El coeficiente de variación es {dec(cv)} %, pero "
    f"esa dispersión incluye los cambios de nivel entre años "
    f"({ref('anio', 'apartado 3')}), no solo la variación de un mes a otro. En "
    "la serie se ven escalones de nivel; la causa no se puede determinar con "
    "estos datos.")

# ------------------------------------------------------------------ 5. género y grupo etario
seccion("genero", "5. Género y grupo etario")
c1, c2 = st.columns(2)
partes = []
for col, donde in [("genero", c1), ("grupo_etario", c2)]:
    t = frecuencias(df[col])
    donde.markdown(f"**`{col}`**")
    mostrar_tabla(t.rename(columns={"categoría": col}), ["registros"], ["%"],
                  donde=donde, hide_index=True)
    fig = px.pie(t, names="categoría", values="registros", hole=0.5)
    fig.update_traces(texttemplate="%{percent:.1%}", textposition="auto", sort=False)
    grafico(fig, donde)
    top = t.iloc[0]
    p = f"En `{col}` la categoría más frecuente es {top['categoría']} ({dec(top['%'])} %)"
    sd = t[t["categoría"] == "SIN DATO"]["%"]
    nr = t[t["categoría"] == "NO REPORTA"]["%"]
    if len(sd):
        p += f"; «SIN DATO» pesa {dec(sd.iloc[0], 2)} %"
    if len(nr):
        p += f"; «NO REPORTA» pesa {dec(nr.iloc[0], 2)} %"
    partes.append(p)
observacion(". ".join(partes) + ". Las porciones muy pequeñas casi no se "
            "distinguen en la dona; sus valores están en la tabla. El grupo "
            "etario sigue la Ley 1098 de 2006: menores de 0 a 12 años, "
            "adolescentes de 13 a 17 y adultos desde los 18.")
ir_a("paginas/p6_relaciones.py", "Ver la relación entre género y grupo etario")

# ------------------------------------------------------------------ 6. medio utilizado
seccion("medio", "6. Medio utilizado (`armas_medios`)")
a = df["armas_medios"].value_counts()
rec = df[df["año"] >= CORTE_MEDIO]["armas_medios"].value_counts()
etq_rec = f"desde {CORTE_MEDIO}"
tabla_m = pd.DataFrame({"todo el periodo": a, etq_rec: rec}).fillna(0).astype(int)
tabla_m["% todo el periodo"] = (tabla_m["todo el periodo"]
                                / tabla_m["todo el periodo"].sum() * 100).round(2)
cols_m = ["medio", "todo el periodo", "% todo el periodo"]
pct_cols_m, miles_m = ["% todo el periodo"], ["todo el periodo"]
if rec.sum() > 0:
    tabla_m[f"% {etq_rec}"] = (tabla_m[etq_rec] / tabla_m[etq_rec].sum() * 100).round(2)
    cols_m += [etq_rec, f"% {etq_rec}"]
    pct_cols_m += [f"% {etq_rec}"]
    miles_m += [etq_rec]
tabla_m = (tabla_m.sort_values("todo el periodo", ascending=False)
           .head(TOP_MEDIO).reset_index(names="medio")[cols_m])
mostrar_tabla(tabla_m, miles_m, pct_cols_m, hide_index=True)
st.caption(f"Se muestran todas las categorías ({len(a)})." if len(a) <= TOP_MEDIO
           else f"Se muestran las {TOP_MEDIO} categorías más frecuentes de {len(a)}.")

nr_lab = next((x for x in a.index if str(x).upper().startswith("NO REPORT")),
              "NO REPORTA")
cortos = [x for x in a.index if "CORTOPUNZANTE" in str(x).upper()]
nr_todo = pct_no_reporta(df["armas_medios"])
nr_rec = None
texto = (f"En todo el periodo la categoría más frecuente es {a.idxmax()} "
         f"({dec(a.max() / a.sum() * 100)} %) y «{nr_lab}» pesa {dec(nr_todo, 2)} %. ")
if rec.sum() > 0:
    nr_rec = pct_no_reporta(df[df["año"] >= CORTE_MEDIO]["armas_medios"])
    texto += (f"Desde {CORTE_MEDIO} la categoría más frecuente es {rec.idxmax()} "
              f"({dec(rec.max() / rec.sum() * 100)} %) y «{nr_lab}» pesa "
              f"{dec(nr_rec, 2)} %. ")
if len(cortos) > 1:
    texto += (f"Además, {len(cortos)} categorías distintas nombran un tipo de "
              f"medio muy parecido ({', '.join(cortos)}), lo que indica que la "
              "clasificación cambió con el tiempo. ")
texto += (f"Como el criterio de registro cambia entre periodos, las dos "
          f"columnas no son comparables entre sí; la comparación fiable es la "
          f"de {CORTE_MEDIO} en adelante.")
observacion(texto)
ir_a("paginas/p2_faltantes.py", "Ver cuándo se concentra el «no reportado»")

# ------------------------------------------------------------------ 7. delitos
seccion("delito", "7. Tipos de delito")
fd = frecuencias(df["delito"])
top_d = fd.head(TOP_DELITOS)
mostrar_tabla(fd.rename(columns={"categoría": "delito"}), ["registros"], ["%"],
              hide_index=True)
st.caption(f"La tabla incluye los {len(fd)} delitos."
           + ("" if len(fd) <= TOP_DELITOS else
              f" El gráfico muestra los {TOP_DELITOS} más frecuentes."))
grafico(px.bar(top_d.sort_values("registros"), x="registros", y="categoría",
               orientation="h", labels={"categoría": ""}),
        alto=70 + 42 * len(top_d), fmt_x=",d")
es_m14 = df["delito"].str.upper().str.contains("MENOR DE 14", na=False)
n_m14 = int(es_m14.sum())
top1 = fd.iloc[0]
observacion(
    f"Hay {len(fd)} tipos de delito. El más frecuente es «{top1['categoría']}» "
    f"({dec(top1['%'], 2)} %) y los tres primeros reúnen el "
    f"{dec(fd.head(3)['%'].sum(), 2)} % de los registros. Los delitos «con "
    f"menor de 14 años» suman {miles(n_m14)} registros "
    f"({dec(n_m14 / len(df) * 100, 2)} %)"
    + ("; es más de la mitad de los registros." if n_m14 / len(df) > 0.5 else "."))

# ------------------------------------------------------------------ 8. coherencia
seccion("coherencia", "8. Coherencia entre delito y grupo etario")
st.caption("Si el delito es «con menor de 14 años», se esperaría que el grupo "
           "etario sea MENORES o ADOLESCENTES (Ley 1098 de 2006).")
n_men_adol = int(df["grupo_etario"].isin(["MENORES", "ADOLESCENTES"]).sum())
minimo = max(0, n_m14 - n_men_adol)
tabla_coh = pd.DataFrame({
    "concepto": ["Registros con delito «con menor de 14 años»",
                 "Registros con grupo etario MENORES o ADOLESCENTES",
                 "Mínimo con delito «menor de 14» y otro grupo etario"],
    "registros": [n_m14, n_men_adol, minimo],
    "% del total": [round(x / len(df) * 100, 2) for x in (n_m14, n_men_adol, minimo)]})
mostrar_tabla(tabla_coh, ["registros"], ["% del total"], hide_index=True)
if minimo > 0:
    observacion(
        f"Hay {miles(n_m14)} registros con delito «con menor de 14 años», pero "
        f"solo {miles(n_men_adol)} con grupo etario MENORES o ADOLESCENTES. Por "
        f"lo tanto, al menos {miles(minimo)} registros "
        f"({dec(minimo / len(df) * 100, 2)} %) tienen un delito de menor de 14 "
        "años con un grupo etario distinto (adultos o sin dato). Es una cota "
        "mínima deducida de los totales; el cruce exacto está en la página de "
        "relaciones.")
    ir_a("paginas/p6_relaciones.py", "Ver el cruce exacto delito y grupo etario")
else:
    observacion("Los totales no muestran una incoherencia entre el delito y el "
                "grupo etario.")

# ------------------------------------------------------------------ 9. departamentos y capitales
seccion("departamento", "9. Departamentos y capitales")
gd = (df.groupby("departamento")
      .agg(registros=("id", "size"), en_capital=("es_capital", "sum")).reset_index())
gd["en_capital"] = gd["en_capital"].astype(int)
gd["% del total"] = (gd["registros"] / len(df) * 100).round(1)
gd["% en la capital"] = (gd["en_capital"] / gd["registros"] * 100).round(1)
gd = gd.sort_values("registros", ascending=False)
c1, c2 = st.columns([1.2, 1])
mostrar_tabla(gd, ["registros", "en_capital"], ["% del total", "% en la capital"],
              n=1, donde=c1, hide_index=True)
larga = pd.concat([
    gd.assign(zona="Capital", n=gd["en_capital"])[["departamento", "zona", "n"]],
    gd.assign(zona="Resto del departamento",
              n=gd["registros"] - gd["en_capital"])[["departamento", "zona", "n"]]])
fig = px.bar(larga, x="n", y="departamento", color="zona", orientation="h",
             category_orders={"departamento": gd["departamento"].tolist()},
             labels={"n": "registros", "departamento": ""})
grafico(fig, alto=70 + 42 * len(gd), fmt_x=",d")

d1 = gd.iloc[0]
d_cap = gd.sort_values("% en la capital", ascending=False).iloc[0]
d_cap_bajo = gd.sort_values("% en la capital").iloc[0]
top2 = gd.head(2)
texto = (f"{d1['departamento']} concentra más registros ({miles(d1['registros'])}, "
         f"{dec(d1['% del total'])} % del total)")
if len(top2) == 2:
    texto += (f"; junto con {top2.iloc[1]['departamento']} reúnen el "
              f"{dec(top2['% del total'].sum())} %")
texto += (f". En el conjunto, el {dec(df['es_capital'].mean() * 100)} % de los "
          "registros corresponde a capitales departamentales: el peso de la "
          f"capital va de {dec(d_cap_bajo['% en la capital'])} % "
          f"({d_cap_bajo['departamento']}) a {dec(d_cap['% en la capital'])} % "
          f"({d_cap['departamento']}). ")
if d_cap["% en la capital"] > 80:
    texto += (f"El valor de {d_cap['departamento']} probablemente se explica "
              "por la estructura del departamento (pocos municipios) y no "
              "equivale a una concentración como la de los demás. ")
texto += ("Son conteos, no tasas: sin población no se puede decir que un "
          "territorio tenga más denuncias por habitante.")
observacion(texto)
limitacion("El sufijo «(CT)», que identifica las capitales, no está definido en "
           "la documentación de la fuente: se infiere de los datos (un único "
           "municipio por departamento, la capital).")

# ------------------------------------------------------------------ decisión
seccion("decision", "Decisión sobre las estadísticas descriptivas")
decision(
    "`cantidad` se excluye del análisis numérico y los casos se cuentan con el "
    "número de registros. La tendencia central y la dispersión se calculan "
    f"sobre los conteos mensuales. El medio utilizado se reporta para todo el "
    f"periodo y para {CORTE_MEDIO} en adelante, y su comparación fiable es la "
    f"de {CORTE_MEDIO} en adelante. El año en curso, al estar incompleto, se "
    "compara por promedio mensual y no por total anual. La incoherencia entre "
    "delito y grupo etario no se corrige ni se imputa: se conserva y se "
    "reporta como limitación.")
pieza_medio = ""
if nr_rec is not None:
    pieza_medio = (f" El medio utilizado cambia de criterio entre periodos "
                   f"(«{nr_lab}» pesa {dec(nr_todo, 2)} % en todo el periodo y "
                   f"{dec(nr_rec, 2)} % desde {CORTE_MEDIO}), por lo que su "
                   "evolución no se interpreta como cambio de conducta.")
pieza_coh = ""
if minimo > 0:
    pieza_coh = (f" Al menos {miles(minimo)} registros "
                 f"({dec(minimo / len(df) * 100, 2)} %) tienen delito de menor "
                 "de 14 años con otro grupo etario, por lo que el grupo etario "
                 "se usa con cautela.")
justificacion(
    "`cantidad` es constante (desviación 0), así que no discrimina; los "
    f"conteos mensuales sí varían (coeficiente de variación {dec(cv)} %), "
    f"aunque esa dispersión incluye los cambios de nivel entre años "
    f"({ref('anio', 'apartado 3')})." + pieza_medio + pieza_coh
    + " Las cifras son conteos de denuncias, no tasas ni ocurrencia real.")
c1, c2 = st.columns(2)
with c1:
    ir_a("paginas/p5_atipicos.py", "Siguiente: atípicos")
with c2:
    ir_a("paginas/p6_relaciones.py", "Distribuciones y relaciones")