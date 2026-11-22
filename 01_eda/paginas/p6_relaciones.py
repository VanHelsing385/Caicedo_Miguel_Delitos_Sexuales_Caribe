import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from contexto import FECHA_EXTRACCION, contexto
from estilo import (ACENTO, decision, dec, encabezado, grafico, indice, ir_a,
                    justificacion, limitacion, miles, mostrar_tabla,
                    observacion, ref, seccion)

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
ORDEN_GRUPO = ["MENORES", "ADOLESCENTES", "ADULTOS", "SIN DATO"]

c = contexto()
df = c.df

encabezado("6 · Distribuciones y relaciones",
           "¿Cómo se distribuyen los casos y qué relaciones hay entre las variables?",
           "limpios, con las filas repetidas incluidas")
st.caption("Casi todas las variables son categóricas, así que las relaciones se "
           "miden con tablas de contingencia, V de Cramér y correlaciones entre "
           "conteos mensuales.")
indice([("delito-grupo", "Delito y grupo etario"), ("genero-grupo", "Género y grupo etario"),
        ("depto-anio", "Departamento y año"), ("distribucion", "Distribución mensual"),
        ("estacionalidad", "Estacionalidad"), ("correlacion", "Entre departamentos"),
        ("decision", "Decisión")])

ultima6 = df["fecha_hecho"].max()
parcial6 = ultima6.day < ultima6.days_in_month
anio_ult6 = int(ultima6.year)
anio_incompleto = (ultima6.month < 12) or parcial6
anios_completos = sorted(a for a in df["año"].unique()
                         if not (a == anio_ult6 and anio_incompleto))

df6 = df.copy()
df6["tipo_delito"] = np.where(
    df6["delito"].str.upper().str.contains("MENOR DE 14", na=False),
    "Con menor de 14 años", "Otros delitos")

# ------------------------------------------------------------------ 1. delito x grupo etario
seccion("delito-grupo", "1. Delito «con menor de 14 años» y grupo etario")
st.caption("Cuantifica con exactitud la incoherencia que en la página de "
           "estadísticas descriptivas solo se pudo acotar con los totales. El "
           "grupo etario sigue la Ley 1098 de 2006: menores de 0 a 12 años, "
           "adolescentes de 13 a 17 y adultos desde los 18.")
ct = pd.crosstab(df6["tipo_delito"], df6["grupo_etario"])
cols_g = ([x for x in ORDEN_GRUPO if x in ct.columns]
          + [x for x in ct.columns if x not in ORDEN_GRUPO])
ct = ct[cols_g]
ct_pct = (ct.div(ct.sum(axis=1), axis=0) * 100).round(2)

c1, c2 = st.columns(2)
c1.markdown("Registros")
mostrar_tabla(ct.reset_index().rename(columns={"tipo_delito": "tipo de delito"}),
              cols_g, donde=c1, hide_index=True)
c2.markdown("% dentro de cada tipo de delito")
mostrar_tabla(ct_pct.reset_index().rename(columns={"tipo_delito": "tipo de delito"}),
              dec_cols=cols_g, n=2, donde=c2, hide_index=True)
grafico(px.imshow(ct_pct, text_auto=".1f", aspect="auto",
                  labels=dict(x="grupo etario", y="", color="% de la fila")), alto=260)

if "Con menor de 14 años" in ct.index:
    m14 = ct.loc["Con menor de 14 años"]
    n_m14 = int(m14.sum())
    n_men_adol_m14 = int(m14.get("MENORES", 0) + m14.get("ADOLESCENTES", 0))
    n_adultos_m14 = int(m14.get("ADULTOS", 0))
    n_otros_m14 = n_m14 - n_men_adol_m14
    n_men_adol_total = int(df6["grupo_etario"].isin(["MENORES", "ADOLESCENTES"]).sum())
    cota = max(0, n_m14 - n_men_adol_total)
    otros = ct.loc["Otros delitos"] if "Otros delitos" in ct.index else None
    pct_adultos_otros = (otros.get("ADULTOS", 0) / otros.sum() * 100
                         if otros is not None and otros.sum() > 0 else float("nan"))
    sr = df6[~df6["es_repetido"] & (df6["tipo_delito"] == "Con menor de 14 años")]
    pct_ad_sin = (sr["grupo_etario"] == "ADULTOS").mean() * 100 if len(sr) else float("nan")
    observacion(
        f"De {miles(n_m14)} registros con delito «con menor de 14 años», "
        f"{miles(n_men_adol_m14)} ({dec(n_men_adol_m14 / n_m14 * 100, 2)} %) "
        f"tienen grupo etario MENORES o ADOLESCENTES y {miles(n_otros_m14)} "
        f"({dec(n_otros_m14 / n_m14 * 100, 2)} %) tienen otro: "
        f"{miles(n_adultos_m14)} ADULTOS ({dec(n_adultos_m14 / n_m14 * 100, 2)} %) "
        f"y el resto SIN DATO. Para comparar, entre los demás delitos el "
        f"{dec(pct_adultos_otros, 2)} % es ADULTOS. La cota mínima de la página de "
        f"estadísticas descriptivas era {miles(cota)} registros; el valor exacto es "
        f"{miles(n_otros_m14)}. Sin las filas repetidas, el porcentaje de ADULTOS "
        f"dentro de este delito es {dec(pct_ad_sin, 2)} %.")
    ir_a("paginas/p4_descriptivas.py", "Ver la cota mínima en estadísticas descriptivas")

    st.markdown("**¿Cambia con los años?** % de registros con delito «con menor de "
                "14 años» cuyo grupo etario es ADULTOS")
    m14df = df6[df6["tipo_delito"] == "Con menor de 14 años"]
    inc = (m14df.assign(adulto=m14df["grupo_etario"] == "ADULTOS")
           .groupby("año")["adulto"].agg(adultos="sum", total="size").reset_index())
    inc["adultos"] = inc["adultos"].astype(int)
    inc["% adultos"] = (inc["adultos"] / inc["total"] * 100).round(2)
    c1, c2 = st.columns(2)
    mostrar_tabla(inc, ["adultos", "total"], ["% adultos"], n=2, donde=c1,
                  hide_index=True)
    grafico(px.line(inc, x="año", y="% adultos", markers=True), c2)
    if len(inc) > 1:
        i_max = inc.sort_values("% adultos", ascending=False).iloc[0]
        i_min = inc.sort_values("% adultos").iloc[0]
        primero, ultimo = inc.iloc[0], inc.iloc[-1]
        observacion(
            f"El porcentaje de ADULTOS dentro de este delito va de "
            f"{dec(i_min['% adultos'], 2)} % ({int(i_min['año'])}) a "
            f"{dec(i_max['% adultos'], 2)} % ({int(i_max['año'])}), un rango de "
            f"{dec(i_max['% adultos'] - i_min['% adultos'], 2)} puntos "
            f"porcentuales. En {int(primero['año'])} fue "
            f"{dec(primero['% adultos'], 2)} % y en {int(ultimo['año'])} "
            f"{dec(ultimo['% adultos'], 2)} %.")

    limite_rec = FECHA_EXTRACCION - pd.DateOffset(years=4)
    recientes = m14df[m14df["fecha_hecho"] > limite_rec]
    if len(recientes):
        n_rec = len(recientes)
        n_ad_rec = int((recientes["grupo_etario"] == "ADULTOS").sum())
        observacion(
            "Una persona menor de 14 años en la fecha del hecho necesita más de 4 "
            f"años para cumplir 18. Los hechos posteriores al {limite_rec:%d/%m/%Y} "
            "tienen menos de 4 años de antigüedad hasta la extracción de los datos "
            f"({FECHA_EXTRACCION:%d/%m/%Y}, según la fuente). Entre esos "
            f"{miles(n_rec)} registros con delito «con menor de 14 años», "
            f"{miles(n_ad_rec)} ({dec(n_ad_rec / n_rec * 100, 2)} %) tienen grupo "
            "etario ADULTOS. Si el grupo etario describe a la víctima, las "
            "denuncias tardías no pueden explicar estos casos, cualquiera sea la "
            "fecha en que se registró la edad. La documentación no precisa a qué "
            "persona ni en qué fecha se refiere la edad registrada.")
    limitacion("Las explicaciones que quedan (error de captura, definición "
               "distinta de la persona registrada o cambio de registro) no se "
               "pueden verificar con estos datos. La incoherencia se conserva y "
               "se reporta; el grupo etario se usa con cautela.")
else:
    observacion("La selección actual no contiene delitos «con menor de 14 años».")

# ------------------------------------------------------------------ 2. género x grupo etario
seccion("genero-grupo", "2. Género y grupo etario")
base2 = df6[~df6["genero"].isin(["SIN DATO", "NO REPORTA"])
            & (df6["grupo_etario"] != "SIN DATO")]
ct2 = pd.crosstab(base2["genero"], base2["grupo_etario"])
cols2 = ([x for x in ORDEN_GRUPO if x in ct2.columns]
         + [x for x in ct2.columns if x not in ORDEN_GRUPO])
ct2 = ct2[cols2]
pct2 = (ct2.div(ct2.sum(axis=1), axis=0) * 100).round(2)
st.caption(f"Se excluyen las categorías SIN DATO y NO REPORTA; quedan "
           f"{miles(len(base2))} de {miles(len(df6))} registros.")
c1, c2 = st.columns(2)
c1.markdown("Registros")
mostrar_tabla(ct2.reset_index(), cols2, donde=c1, hide_index=True)
c2.markdown("% de cada grupo etario dentro de cada género")
mostrar_tabla(pct2.reset_index(), dec_cols=cols2, n=2, donde=c2, hide_index=True)
grafico(px.imshow(pct2, text_auto=".1f", aspect="auto",
                  labels=dict(x="grupo etario", y="género", color="% de la fila")),
        alto=260)


def cramer_v(tabla):
    obs = tabla.values.astype(float)
    n = obs.sum()
    esp = np.outer(obs.sum(axis=1), obs.sum(axis=0)) / n
    chi2 = ((obs - esp) ** 2 / esp).sum()
    k = min(obs.shape) - 1
    return (float(np.sqrt(chi2 / (n * k))) if k > 0 else float("nan")), float(chi2)


if ct2.shape[0] >= 2 and ct2.shape[1] >= 2:
    v, chi2 = cramer_v(ct2)
    texto = (f"La V de Cramér entre género y grupo etario es {dec(v, 3)} "
             f"(chi-cuadrado = {dec(chi2, 1)}). ")
    if pct2.shape[0] == 2:
        dif_col = (pct2.iloc[0] - pct2.iloc[1]).abs()
        col_mx = dif_col.idxmax()
        texto += (f"La mayor diferencia entre géneros está en {col_mx}: "
                  f"{dec(pct2.loc[pct2.index[0], col_mx], 2)} % en {pct2.index[0]} y "
                  f"{dec(pct2.loc[pct2.index[1], col_mx], 2)} % en {pct2.index[1]} "
                  f"({dec(dif_col[col_mx], 2)} puntos porcentuales). ")
    texto += ("Con convenciones habituales (0,1 débil, 0,3 moderada, 0,5 fuerte), "
              "la asociación es "
              + ("débil. " if v < 0.1 else "entre débil y moderada. " if v < 0.3
                 else "entre moderada y fuerte. " if v < 0.5 else "fuerte. ")
              + "Con tantos registros casi cualquier diferencia sería "
                "estadísticamente significativa, por eso se reporta la magnitud "
                "(V) y no el valor p.")
    observacion(texto)
else:
    observacion("La selección actual no tiene suficientes categorías para medir "
                "la asociación.")

# ------------------------------------------------------------------ 3. departamento x año
seccion("depto-anio", "3. Departamento y año")
piv = df6.pivot_table(index="departamento", columns="año", values="id",
                      aggfunc="count", fill_value=0)
grafico(px.imshow(piv, text_auto=True, aspect="auto",
                  labels=dict(x="año", y="", color="registros")),
        alto=60 + 48 * len(piv))

if len(anios_completos) >= 2:
    n_per = min(3, len(anios_completos))
    trozos = np.array_split(np.array(anios_completos), n_per)
    etiquetas = [f"{int(t[0])}–{int(t[-1])}" for t in trozos]
    mapa_per = {int(a): et for t, et in zip(trozos, etiquetas) for a in t}
    c6 = df6[df6["año"].isin(anios_completos)].copy()
    c6["periodo"] = c6["año"].map(mapa_per)
    per = c6.groupby(["periodo", "departamento"]).size().reset_index(name="registros")
    per["% del periodo"] = (per["registros"]
                            / per.groupby("periodo")["registros"].transform("sum") * 100)
    orden_dep = (per[per["periodo"] == etiquetas[-1]]
                 .sort_values("% del periodo", ascending=False)["departamento"].tolist())
    fig_c = px.bar(per, x="departamento", y="% del periodo", color="periodo",
                   barmode="group",
                   category_orders={"departamento": orden_dep, "periodo": etiquetas},
                   labels={"periodo": "periodo", "departamento": ""})
    fig_c.update_traces(texttemplate="%{y:.1f}", textposition="outside")
    grafico(fig_c, alto=420)
    st.caption(f"Peso de cada departamento en los registros de cada periodo (años "
               f"completos; {anio_ult6} se excluye si está incompleto). Los "
               "periodos son tercios de los años completos.")

    tab_per = per.pivot(index="departamento", columns="periodo",
                        values="% del periodo").reindex(orden_dep)
    tab_per = tab_per[etiquetas].fillna(0)
    tab_per["cambio (pp)"] = tab_per[etiquetas[-1]] - tab_per[etiquetas[0]]
    tab_per = tab_per.reset_index()
    tot_per = per.groupby("periodo")["registros"].sum()
    mostrar_tabla(tab_per, dec_cols=etiquetas + ["cambio (pp)"], n=1, hide_index=True)
    d_up = tab_per.sort_values("cambio (pp)", ascending=False).iloc[0]
    d_dn = tab_per.sort_values("cambio (pp)").iloc[0]
    observacion(
        f"Entre {etiquetas[0]} y {etiquetas[-1]}, {d_up['departamento']} es el "
        f"departamento que más gana peso (de {dec(d_up[etiquetas[0]], 1)} % a "
        f"{dec(d_up[etiquetas[-1]], 1)} %, {dec(d_up['cambio (pp)'], 1)} puntos "
        f"porcentuales) y {d_dn['departamento']} el que más lo pierde (de "
        f"{dec(d_dn[etiquetas[0]], 1)} % a {dec(d_dn[etiquetas[-1]], 1)} %, "
        f"{dec(d_dn['cambio (pp)'], 1)} puntos). El primer periodo reúne "
        f"{miles(tot_per[etiquetas[0]])} registros y el último "
        f"{miles(tot_per[etiquetas[-1]])}. Un cambio de peso puede deberse a "
        "cambios reales o a diferencias en la captura entre territorios; los "
        "datos no permiten distinguirlo.")

# ------------------------------------------------------------------ 4. distribución mensual
seccion("distribucion", "4. Distribución de los casos mensuales")
men_tot = df6.groupby("mes").size().rename("casos").reset_index()
if parcial6:
    men_tot = men_tot.iloc[:-1]
cm6 = men_tot["casos"]
lg6 = np.log(cm6.clip(lower=1))
asim, asim_log = float(cm6.skew()), float(lg6.skew())
curt, curt_log = float(cm6.kurt()), float(lg6.kurt())


def kde_gauss(valores, puntos):
    """Estimador de núcleo gaussiano con ancho de banda de Silverman."""
    x = np.asarray(valores, float)
    n = len(x)
    sd = x.std(ddof=1)
    iqr = np.subtract(*np.percentile(x, [75, 25]))
    h = 0.9 * min(sd, iqr / 1.34) * n ** (-0.2)
    if not h > 0:
        h = sd * n ** (-0.2) if sd > 0 else 1.0
    z = (puntos[:, None] - x[None, :]) / h
    return np.exp(-0.5 * z ** 2).sum(axis=1) / (n * h * np.sqrt(2 * np.pi))


def histograma(datos, col, etiqueta, donde):
    x = datos[col].to_numpy(float)
    fig = px.histogram(datos, x=col, nbins=25, histnorm="probability density",
                       labels={col: etiqueta})
    margen = 0.15 * (x.max() - x.min())
    malla = np.linspace(x.min() - margen, x.max() + margen, 300)
    fig.add_trace(go.Scatter(x=malla, y=kde_gauss(x, malla), mode="lines",
                             name="estimador de núcleo",
                             line=dict(color=ACENTO, width=3)))
    fig.update_layout(yaxis_title="densidad", showlegend=False)
    grafico(fig, donde, alto=340)


c1, c2 = st.columns(2)
histograma(men_tot, "casos", "casos en el mes", c1)
histograma(men_tot.assign(log_casos=lg6), "log_casos",
           "logaritmo natural de los casos del mes", c2)
st.caption("Curva naranja: estimador de núcleo gaussiano (ancho de banda de "
           "Silverman), que muestra la forma de la distribución. El eje vertical "
           "es una densidad, no un conteo.")
mejora = abs(asim_log) < abs(asim)
observacion(
    f"Los {len(cm6)} meses tienen media {dec(cm6.mean(), 1)} y mediana "
    f"{dec(cm6.median(), 1)} casos. La asimetría es {dec(asim, 2)} con los datos "
    f"originales y {dec(asim_log, 2)} con el logaritmo, y la curtosis en exceso es "
    f"{dec(curt, 2)} y {dec(curt_log, 2)}, respectivamente (0 en una normal): "
    + ("la transformación reduce la asimetría. " if mejora else
       "la transformación no mejora la simetría. ")
    + "La asimetría y la curtosis miden cuánto se aleja la distribución de una "
      "normal; su forma refleja los cambios de nivel de la serie más que una "
      "variación aleatoria alrededor de un valor típico.")
ir_a("paginas/p4_descriptivas.py", "Ver la serie mensual")

# ------------------------------------------------------------------ 5. estacionalidad
seccion("estacionalidad", "5. ¿Hay estacionalidad por mes del año?")
est = (df6[df6["año"].isin(anios_completos)].groupby(["año", "mes"]).size()
       .rename("casos").reset_index())
if len(est):
    est["indice"] = est["casos"] / est.groupby("año")["casos"].transform("mean")
    est["mes_num"] = est["mes"].dt.month
    est["mes del año"] = est["mes_num"].map(lambda m: MESES_ES[m - 1])
    resumen_est = (est.groupby(["mes_num", "mes del año"])["indice"]
                   .agg(mediana="median", minimo="min", maximo="max")
                   .reset_index().sort_values("mes_num"))
    fig_e = px.box(est.sort_values("mes_num"), x="mes del año", y="indice",
                   labels={"indice": "casos del mes / promedio mensual del año"})
    fig_e.add_hline(y=1, line_dash="dash")
    grafico(fig_e, alto=400)
    mostrar_tabla(resumen_est[["mes del año", "mediana", "minimo", "maximo"]],
                  dec_cols=["mediana", "minimo", "maximo"], n=2, hide_index=True)
    if len(resumen_est) >= 2:
        n_cerca = int(((resumen_est["mediana"] >= 0.9)
                       & (resumen_est["mediana"] <= 1.1)).sum())
        r_hi = resumen_est.sort_values("mediana", ascending=False).iloc[0]
        r_lo = resumen_est.sort_values("mediana").iloc[0]
        meses_lo = est[est["mes del año"] == r_lo["mes del año"]]
        n_bajo_prom = int((meses_lo["indice"] < 1).sum())
        observacion(
            f"El índice 1 equivale al promedio mensual de cada año (se usan solo "
            f"años completos: {anios_completos[0]} a {anios_completos[-1]}). El mes "
            f"con mayor índice mediano es {r_hi['mes del año']} "
            f"({dec(r_hi['mediana'], 2)}) y el menor {r_lo['mes del año']} "
            f"({dec(r_lo['mediana'], 2)}), una diferencia de "
            f"{dec((r_hi['mediana'] - r_lo['mediana']) * 100, 1)} puntos "
            f"porcentuales del promedio. En {n_bajo_prom} de los {len(meses_lo)} "
            f"años, {r_lo['mes del año']} quedó por debajo del promedio mensual "
            f"del año. {n_cerca} de los {len(resumen_est)} meses tienen un índice "
            "mediano entre 0,90 y 1,10 (±10 % del promedio, umbral elegido por "
            "convención). Los años difieren entre sí por los cambios de nivel de "
            "la serie, por lo que este patrón es una descripción y no una prueba "
            "de estacionalidad.")
else:
    observacion("No hay años completos en la selección actual.")

# ------------------------------------------------------------------ 6. correlación entre departamentos
seccion("correlacion", "6. Relación entre departamentos (conteos mensuales)")
pv = df6.groupby(["mes", "departamento"]).size().unstack(fill_value=0)
if parcial6:
    pv = pv.iloc[:-1]

if pv.shape[1] >= 2:
    corr_niv = pv.corr()
    corr_dif = pv.diff().dropna().corr()
    c1, c2 = st.columns(2)
    c1.markdown("Correlación entre **niveles** mensuales")
    grafico(px.imshow(corr_niv, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                      color_continuous_scale="RdBu_r"), c1, alto=460)
    c2.markdown("Correlación entre **cambios** de un mes al siguiente")
    grafico(px.imshow(corr_dif, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                      color_continuous_scale="RdBu_r"), c2, alto=460)

    def pares(m):
        mascara = np.triu(np.ones(m.shape), k=1).astype(bool)
        return m.where(mascara).stack()

    p_niv, p_dif = pares(corr_niv), pares(corr_dif)
    a_hi, b_hi = p_dif.idxmax()
    a_lo, b_lo = p_dif.idxmin()
    observacion(
        f"La correlación media entre departamentos es {dec(p_niv.mean(), 2)} con "
        f"los niveles mensuales y {dec(p_dif.mean(), 2)} con los cambios de un mes "
        f"al siguiente. Con los cambios, la pareja más correlacionada es {a_hi} y "
        f"{b_hi} ({dec(p_dif.max(), 2)}) y la menos, {a_lo} y {b_lo} "
        f"({dec(p_dif.min(), 2)}). La correlación entre niveles incluye la "
        "tendencia que comparten los departamentos, por lo que sobreestima su "
        "relación; la de cambios mide si suben y bajan juntos mes a mes. La "
        "correlación no implica causalidad.")

    st.markdown("**Dispersión entre dos departamentos**")
    deps = list(pv.columns)
    tipo_disp = st.radio("Dispersión de:", ["Niveles mensuales",
                                            "Cambios de un mes al siguiente"],
                         horizontal=True, key="disp_tipo")
    cA, cB = st.columns(2)
    dep_x = cA.selectbox("Departamento en el eje X", deps, index=0, key="disp_x")
    dep_y = cB.selectbox("Departamento en el eje Y", deps,
                         index=1 if len(deps) > 1 else 0, key="disp_y")
    if dep_x != dep_y:
        base_d = pv if tipo_disp == "Niveles mensuales" else pv.diff().dropna()
        pts = base_d[[dep_x, dep_y]].reset_index()
        unidad = "casos" if tipo_disp == "Niveles mensuales" else "cambio en casos"
        fig_d = px.scatter(pts, x=dep_x, y=dep_y,
                           labels={dep_x: f"{unidad} en {dep_x}",
                                   dep_y: f"{unidad} en {dep_y}"})
        xv, yv = pts[dep_x].to_numpy(float), pts[dep_y].to_numpy(float)
        pend, ordenada = np.polyfit(xv, yv, 1)
        xs = np.array([xv.min(), xv.max()])
        fig_d.add_trace(go.Scatter(x=xs, y=ordenada + pend * xs, mode="lines",
                                   name="recta de ajuste", showlegend=True,
                                   line=dict(color=ACENTO, width=3)))
        fig_d.update_layout(legend=dict(orientation="h", y=1.1, x=0))
        grafico(fig_d, alto=420)
        r = float(np.corrcoef(xv, yv)[0, 1])
        observacion(
            f"Entre {dep_x} y {dep_y} ({tipo_disp.lower()}, {len(pts)} meses) la "
            f"correlación de Pearson es {dec(r, 2)} y r² = {dec(r ** 2, 2)}: la "
            f"recta de ajuste explica el {dec(r ** 2 * 100, 1)} % de la variación "
            f"de {dep_y}. Su pendiente es {dec(pend, 2)}. "
            + ("Con niveles, esta relación incluye la tendencia que comparten ambos "
               "departamentos." if tipo_disp == "Niveles mensuales"
               else "Con cambios, se elimina la mayor parte de la tendencia común."))
    else:
        st.caption("Elige dos departamentos distintos.")
else:
    observacion("Para comparar departamentos hay que seleccionar al menos dos en "
                "la barra lateral.")

# ------------------------------------------------------------------ decisión
seccion("decision", "Decisión sobre distribuciones y relaciones")
decision(
    "Las relaciones entre variables categóricas se miden con tablas de "
    "contingencia y V de Cramér, y las relaciones entre territorios con "
    "correlaciones entre conteos mensuales (en niveles y en cambios). No se "
    f"transforman los datos, porque el análisis es descriptivo y el logaritmo no "
    f"corrige la forma de la distribución mensual ({ref('distribucion', 'apartado 4')}). "
    "Si se modelaran los conteos, se usaría un modelo para datos de conteo y no "
    "una transformación. La incoherencia entre delito y grupo etario no se "
    "corrige: se conserva y se declara como limitación.")
pieza_inc = ""
if "Con menor de 14 años" in ct.index:
    pieza_inc = (f" El {dec(n_otros_m14 / n_m14 * 100, 2)} % de los registros con "
                 "delito «con menor de 14 años» tiene un grupo etario distinto de "
                 "menores y adolescentes, y las denuncias tardías no lo explican en "
                 f"los hechos recientes ({ref('delito-grupo', 'apartado 1')}); por "
                 "eso el grupo etario se interpreta con cautela hasta confirmar con "
                 "la fuente a qué persona y en qué fecha se refiere la edad "
                 "registrada.")
justificacion(
    "Casi todas las variables son categóricas y `cantidad` es constante, por lo "
    "que no hay correlaciones entre variables numéricas del archivo; las únicas "
    "magnitudes con varianza son los conteos por mes. Los conteos comparten la "
    "tendencia de la serie, por eso se reporta también la correlación entre "
    "cambios. Con decenas de miles de registros casi cualquier asociación resulta "
    "significativa, por lo que se reporta la magnitud y no el valor p." + pieza_inc)
limitacion("La estacionalidad es una descripción, no una prueba, y las causas de "
           "los patrones (el descenso de diciembre, los cambios de peso entre "
           "departamentos) no se pueden determinar con estos datos: deben "
           "respaldarse con la literatura.")
ir_a("paginas/p5_atipicos.py", "Volver a los atípicos")