# BITÁCORA DE DECISIONES
Proyecto: Delitos sexuales, Policía Nacional (región Caribe)
Asignatura: Minería de Datos
Autor: Miguel Caicedo - Jordy Cardenas

Convención: [ ] = dato pendiente de completar con lo que se vea en pantalla.
No se inventan cifras: lo que no se ha verificado queda como pendiente.
Las cifras marcadas «cálculo propio» se obtuvieron combinando tablas de la
aplicación; el resto se leyó directamente de la aplicación.

---

## FLUJO DEL PROYECTO (definido por el profesor)
1. Cargar el CSV o la fuente de datos ............. Fase 1
2. EDA completo con Python ........................ Fase 2
3. Almacenar los datos limpios en la base ......... Fase 3
4. Tablero en Power BI conectado a la base ........ Fase 4
El artículo documenta la gestión realizada ........ Fase 5

## PRINCIPIO DE CONSERVACIÓN DE DATOS
El dato fuente no se modifica: el CSV original se conserva intacto en
00_datos_originales/ y el análisis parte siempre de él. La limpieza
produce una copia derivada (que se guardará en la base de datos como
delitos_limpios) en la que no se elimina ningún registro del Caribe: los
nulos se reemplazan por una categoría explícita, las filas repetidas se
marcan en lugar de borrarse y los atípicos se conservan. Motivo: la fuente
no permite distinguir entre registros duplicados y casos distintos, y
eliminar filas sesgaría los conteos.

## DECISIÓN METODOLÓGICA GENERAL
La limpieza, transformación y exploración se realizan en Python con
Streamlit, para justificar cada decisión con evidencia visual.
PostgreSQL (Neon) almacena los datos ya limpios y Power BI se conecta
directamente a la base.

---

## FASE 0. PREPARACIÓN

### 0.1 Entorno y estructura
- Entorno virtual (.venv) en la raíz del proyecto; no se entrega.
- Credenciales en .env (se usarán en la Fase 3; no se entrega); se
  entrega .env.example.
- requirements.txt generado con pip freeze.
- Carpetas: 00_datos_originales, 01_eda, 02_base_de_datos, 03_powerbi,
  04_capturas, 05_articulo.
- La copia original del CSV se conserva intacta en 00_datos_originales/.

### 0.2 Preguntas de negocio (borrador)
1. ¿Cómo ha evolucionado la cantidad de casos reportados en la región
   Caribe por año y por mes?
2. ¿Qué departamentos y municipios concentran la mayor cantidad de casos?
3. ¿Cuál es el perfil según género y grupo etario, y cómo varía por
   departamento?
4. ¿Qué tipos de delito predominan y cuál es su tendencia?
Decisión que apoyan: priorizar territorios, grupos poblacionales y tipos
de delito para focalizar prevención y atención.
[DECIDIR] La fuente no trae población: se trabaja con conteos absolutos,
no con tasas por 100.000 habitantes, y se declara como limitación.

### 0.3 Cambio de flujo y reconstrucción (09/11/2026)
Cambio: el profesor define el proceso así: 1) cargar el CSV, 2) EDA
completo en Python, 3) guardar en la base los datos ya limpios, 4) Power
BI conectado a la base. La gestión debe quedar documentada en el artículo.
Decisión: reconstruir el proyecto desde cero siguiendo ese orden. Se
descarta la API de FastAPI (Streamlit ya no consulta la base) y la tabla
cruda de Neon (la base guardará solo los datos limpios del Caribe). Se
conserva la lógica de limpieza, las páginas del EDA y todas las decisiones
documentadas. Respaldo previo del proyecto anterior.
Verificación: las cifras de control de la versión anterior (405.193 filas,
67.122 en el Caribe, 370 y 68 nulos, 4.688 repetidos, 17 y 20 atípicos)
se reproducen con la lectura directa del CSV.

Historial (versión anterior, descartada): la primera versión cargaba los
405.193 registros nacionales a PostgreSQL (tabla delitos, con una tabla
temporal de carga) y los servía a Streamlit mediante una API FastAPI. Al
cambiar el flujo, la base pasa a guardar solo los datos limpios y la API
deja de ser necesaria. De esa versión se conservan los hallazgos y las
cifras de control.

---

## FASE 1. CARGA DE LA FUENTE

### 1.1 Fuente y documentación
- Dataset: Reporte Delitos Sexuales, Policía Nacional (CSV). Cobertura
  nacional: 33 valores distintos en DEPARTAMENTO. Filas (sin encabezado):
  405.193. Codificación UTF-8: las tildes se visualizan bien.
- Fuente: DIJIN - Policía Nacional (GICRI). Cobertura: 01/01/2010 a
  31/07/2026; datos extraídos el 31/08/2026. Cifras sujetas a variación
  (integración y consolidación con la Fiscalía). Nota de la fuente: cifras
  de todos los delitos actualizadas según una nueva metodología de
  validación de denuncias con la Fiscalía (fecha de aplicación no indicada).
- La fuente procesa, valida e imputa los registros antes de publicarlos, y
  declara que la operación no capta lo que la comunidad no denuncia.
- Variables públicas: armas medios, departamento, municipio, fecha, delito,
  género, agrupación de edad de la persona, código DANE y cantidad. El
  conjunto no trae diccionario de variables.
- Agrupación de edad (Ley 1098 de 2006, art. 3): menores 0-12, adolescentes
  13-17, adultos desde 18.
- El sufijo (CT) no está definido en la documentación consultada; se infiere
  de los datos (capitales de los 8 departamentos).
- Documentación consultada: copias archivadas de 2022 de la ficha técnica;
  falta contrastar con la versión vigente.

### 1.1b Contraste con la documentación oficial
Confirmado (pendiente de verificar versión vigente y página):
- Los 3 últimos dígitos del código DANE identifican la cabecera municipal
  (000) o un centro poblado (001 en adelante): DANE, Marco Geoestadístico
  Nacional (ficha técnica). [Referencia completa]
- El registro describe a la víctima: la ficha metodológica de la Policía
  define el indicador como número de personas víctimas de delitos sexuales
  y el registro como información biográfica de la víctima. [Referencia,
  versión y página]
- Agrupación de edad: Ley 1098 de 2006, art. 3 (descripción de la variable
  en el conjunto de datos).
- La base de datos se reestructuró técnicamente en 2014 (normalización de
  tablas), según la ficha metodológica (copia archivada de 2022).
  Compatible con el escalón de nivel de 2015; no lo demuestra.
Sin confirmar:
- Significado del sufijo (CT): no está definido en la documentación
  consultada. Coincide con la capital en los 8 departamentos. Capital se
  define además por la convención DIVIPOLA (municipio 001), por comprobar.
- Fecha con la que se calcula la edad registrada: no documentada.
- La suposición de que (CT) depende de la guía interna 2DI-GU-0004 no tiene
  respaldo documental y no se usa.

### 1.2 Lectura del CSV (01_eda/datos.py)
- Todo se lee como texto; solo los campos vacíos son nulos (en lugar del
  criterio por defecto de pandas, que convertiría textos como "NA").
- codigo_dane se completa a 8 caracteres (conserva ceros iniciales).
  Largo original: todos los códigos tenían 8 caracteres (405.193); no
  hubo pérdida de ceros iniciales.
- id = posición de la fila en el CSV, para trazabilidad hasta el original.
- Filtro del Caribe por código DANE (2 primeros dígitos) sobre una copia;
  validado contra el filtro por nombre de departamento (67.122 en ambos).
- Resultado de verificar_carga.py: las 20 verificaciones coinciden con las
  cifras de control (405.193 filas; 33 departamentos; 2.417, 653 y 635
  nulos nacionales; 34.855 grupos de duplicados; 67.122 en el Caribe por
  código y por nombre; 370 y 68 nulos en el Caribe; 10.822 «NO REPORTADO»
  en el medio).
Evidencia: Figura [fig01_verificacion_carga.png].

### 1.3 Hallazgos de calidad a nivel nacional (al leer el CSV)
- genero NULL: 2.417 (0,60 %); genero = 'NO REPORTA': 653 (0,16 %);
  grupo_etario NULL: 635 (0,16 %). No hay cadenas vacías: los blancos
  son NULL.
- Nombres de departamento no oficiales: "GUAJIRA", "SAN ANDRÉS",
  "BOGOTA", "VALLE". Por eso el filtro se hace por código DANE.
- cantidad = 1 en todas las filas del Caribe: variable constante; se
  excluye de correlaciones y los casos se cuentan con el número de
  registros.
- Duplicados (nacional): 34.855 grupos de filas idénticas, 87.618 filas
  en grupos (21,6 %), 52.763 filas excedentes (13,0 %).
  Decisión: no eliminar. La fuente no tiene identificador de caso, por lo
  que no se distingue entre denuncias distintas con atributos idénticos y
  registros repetidos; borrarlas sesgaría los conteos.
(Las cifras del Caribe están en la Fase 2.)
Evidencia: Figura [X] (página «Carga y estructura»).

### 1.4 Validación del filtro Caribe
- Filtro por código DANE (2 primeros dígitos): 67.122 registros (16,6 %
  del total nacional).
- Filtro por nombre de departamento: 67.122 registros.
- Coinciden: queda validado el uso del código DANE.
Evidencia: Figura [X] (tabla de departamentos y ranking nacional).

---

## FASE 2. EDA EN STREAMLIT (Caribe, 67.122 registros)

### 2.1 Datos y flujo de la aplicación
La aplicación lee el CSV directamente (datos.py); no consulta ninguna base
de datos. Los datos originales no se modifican: el filtro por departamento
y la limpieza se hacen sobre copias.
Verificación: 67.122 registros del Caribe; las cifras de control se
reproducen (sección 0.3).

### 2.2 Orden y presentación del EDA
Decisión: ordenar la aplicación según el proceso: carga y estructura
(datos originales) -> valores faltantes -> duplicados -> estadísticas
descriptivas (datos limpios) -> atípicos -> distribuciones y relaciones.
Motivo: los problemas (nulos, duplicados) solo se miden antes de limpiar;
las estadísticas se calculan después.
Presentación: cada tabla o gráfico lleva debajo su observación, calculada
con los mismos datos mostrados, para que se vea el origen de cada cifra.
La decisión, la justificación y la limitación van al final de cada página.
Interfaz: la aplicación pasa de pestañas a páginas con navegación lateral
agrupada según el proceso. Motivo: con pestañas no es posible enlazar de un
apartado a otra pestaña; con páginas, cada referencia es un enlace clicable.
Diseño: tema claro con paleta propia; cajas de análisis diferenciadas por
tipo (observación, decisión, justificación, limitación); formato español
(punto de miles, coma decimal, fechas dd/mm/aaaa); filtro de departamentos
solo en las páginas de análisis y conservado entre páginas.
Constantes elegidas por el autor: umbral de «año alto» de NO REPORTA = 15 %;
corte de periodos para los nulos = 2018; corte del medio utilizado = 2021
(por confirmar); nivel local mínimo = 10 casos/mes, ventana = 13 meses y
|z| > 3,5 en los atípicos.

### 2.3 Limpieza (limpieza.py)
Decisión: reemplazar valores en las mismas columnas, sin columnas
"normalizadas" paralelas.
- genero, grupo_etario: NULL -> 'SIN DATO'.
- municipio: se elimina el sufijo (CT).
- departamento: nombre limpio desde la tabla de referencia de la región.
- es_repetido: marca filas idénticas a una anterior; se calcula sobre los
  valores originales antes de reemplazar.
- es_capital: conserva la información del sufijo (CT); se calcula antes
  de quitarlo.
- año y mes: auxiliares para agrupar por tiempo.
Ningún registro se elimina.

Verificación del sufijo (CT):
- Aparece en un único municipio por departamento: la capital (Barranquilla,
  Cartagena, Valledupar, Santa Marta, Montería, Sincelejo, Riohacha,
  San Andrés). Esas capitales suman 32.131 registros (47,9 % de 67.122).
- Sobre la tabla nacional hay 3 municipios con dos escrituras (Armenia,
  Florencia, San Andrés): son nombres de municipios distintos en
  departamentos distintos. El nombre del municipio no es llave única.
- Cada codigo_dane del Caribe aparece siempre con una sola escritura del
  municipio (0 variantes): quitar el sufijo no altera los grupos de
  repetidos.
- codigo_dane de las capitales tiene 81 códigos distintos que no terminan
  en 000 (464 registros), con los mismos 5 primeros dígitos.
Regla: contar por municipio agrupando por departamento + nombre limpio
(o por los 5 primeros dígitos), nunca por el código completo.
Pendiente: confirmar en la documentación (DANE / Policía Nacional) el
significado de (CT) y de los últimos 3 dígitos del código.
Evidencia: Figuras [X] (variantes), [X] (capitales).

### 2.4 Estructura (datos originales)
Registros: 67.122. Columnas: 9 (fecha_hecho, departamento, municipio,
codigo_dane, delito, genero, grupo_etario, armas_medios, cantidad).
Casi todas son categóricas; cantidad es numérica. Rango de fechas:
2010 a 2026.
Evidencia: Figura [X].

### 2.5 Valores faltantes (datos originales)
Por columna: genero 370 nulos (0,55 %); grupo_etario 68 (0,10 %); las
otras 7 columnas, 0.

Categorías «NO REPORTA» (declaradas por la fuente): armas_medios 10.822
(16,12 %); genero 113 (0,17 %); grupo_etario y municipio, 0.
Es una categoría escrita por la fuente, distinta de un nulo.

Nulos de genero por periodo:
- 2010-2017: 7 nulos en 22.536 registros (0,03 %).
- 2018-2026: 363 nulos en 44.586 registros (0,81 %), el 98,1 % del total.
- Porcentaje anual: de 0,33 % (2018) a 2,12 % (2025). El año con más
  nulos es 2025: 91 (24,6 % del total).
- Años sin nulos: 2012, 2016, 2017 y 2020 (2020 con 5.472 registros).
- 2026 es un año incompleto (2.508 registros).

Nulos de genero por departamento:
- Atlántico: más nulos absolutos (113; 30,5 % del total).
- La Guajira: mayor porcentaje (1,42 % de 3.938 registros).
- Córdoba 1 nulo; San Andrés 0.
Cruce departamento x periodo:
- 2010-2017: ningún departamento supera 0,11 %.
- 2018 en adelante: La Guajira 2,46 %, Magdalena 1,03 %, Atlántico 1,02 %,
  Bolívar 0,81 %, Sucre 0,58 %, Cesar 0,53 %, Córdoba 0,02 %, San Andrés 0 %.
- El aumento es sobre todo temporal. La Guajira tiene más del doble que
  el siguiente, por lo que hay además un componente territorial. Córdoba
  casi no presenta nulos (1 de 5.096 desde 2018); la causa se desconoce.

«NO REPORTA» en armas_medios por año (10.822 filas):
- 2010-2012: 74,8 % a 86,7 % (3.742 filas, 34,6 % del total).
- 2013-2017: baja a 3,1 % (2016) y sube a 7,9 % (2017).
- 2018-2020: 28,1 %, 38,0 % y 19,0 % (5.540 filas, 51,2 %).
- 2021-2026: prácticamente 0 % (2 casos en 2022 y 1 en 2023).
- Umbral de "año alto": 15 % (incluye 2020 como parte del rebote
  2018-2020; es una decisión del autor). Los años altos (2010-2013 y
  2018-2020) reúnen el 91,0 % de los «NO REPORTA».
Hallazgo: el criterio de registro del medio no es comparable en todo el
periodo.

Decisión: no imputar con la moda (introduce sesgo en un tema sensible);
NULL -> 'SIN DATO'; 'NO REPORTA' se conserva como categoría de la fuente.
Para armas_medios se reporta el periodo completo y 2021 en adelante, y no
se interpreta su evolución como cambio de conducta. [Confirmar el corte.]
Alternativa considerada y descartada: convertir los nulos a «NO REPORTA».
Son cosas distintas (en una la fuente escribió la categoría; en el nulo el
campo llegó vacío), la mezcla no se puede deshacer y en grupo_etario esa
categoría no existe. En gráficos o en Power BI pueden agruparse sin tocar
los datos.
Justificación: el porcentaje global de nulos es bajo, pero no es aleatorio
en el tiempo.
Resultado de la limpieza: SIN DATO coincide con los nulos originales;
el sufijo (CT) se elimina; el total de registros no cambia.
Evidencia: Figuras [X] (por columna), [X] (NO REPORTA), [X] (armas por
año), [X] (genero por año), [X] (por departamento), [X] (cruce),
[X] (antes/después).

### 2.6 Duplicados
Definición: fila repetida = fila idéntica en todas las columnas a otra
anterior. La fuente no trae identificador de caso: no se puede distinguir
entre denuncias distintas con atributos iguales y un registro duplicado.
Criterio: se calcula sobre los valores originales (antes de reemplazar
NULL y quitar (CT)); validado con 0 variantes de escritura por código.

Resultados:
- 4.688 filas marcadas como repetidas (6,98 %), en 3.760 grupos de filas
  idénticas (8.448 filas en total).
- 3.225 grupos son pares (85,8 %). El grupo más grande tiene 86 filas.
- Verificación: la suma de filas excedentes por tamaño de grupo (4.688)
  coincide con las filas marcadas y con las sumas por departamento y año.
- Por departamento: mayor porcentaje Atlántico (8,7 %; 1.443 de 16.664);
  menor Córdoba (4,5 %; 373 de 8.372).
- Por año: 2,4 % (2010) hasta 9,8 % (2018) y 9,5 % (2019); desde 2020 entre
  7,1 % y 8,0 % (7,2 % en 2026, año incompleto). Salto entre 2016 (4,7 %) y
  2018 (9,8 %).

Grupos más grandes:
- 86 filas idénticas: 16/05/2018, Cesar, Valledupar, Art. 208, femenino,
  adultos, arma blanca. Sus 85 excedentes son el 12,9 % de los 657
  repetidos de 2018.
- 18 filas (Barranquilla, 01/11/2019, Art. 209) y 16 filas (Barranquilla,
  16/06/2015, Art. 205).
- Un grupo de este tamaño es improbable como denuncias independientes;
  la causa no se puede determinar (carga masiva, registro por defecto o
  error de captura).
- Posible inconsistencia entre campos: en los dos primeros grupos el delito
  es «con menor de 14 años» y el grupo etario es «ADULTOS» / «ADOLESCENTES»
  (cuantificada en la sección 2.9).

Sensibilidad (con vs. sin repetidos):
- Año pico: 2019 en ambos escenarios (6.904 con; 6.245 sin).
- Dirección año a año: coincide en las 16 variaciones.
- Ranking de departamentos: igual salvo Cesar y Córdoba, que intercambian
  los puestos 4 y 5 (con repetidos: Cesar 8.613 y Córdoba 8.372; sin
  ellos: Córdoba 7.999 y Cesar 7.918).

Decisión: no eliminar. Se conservan y se marcan con es_repetido; los
resultados clave se reportan con y sin ellas.
Justificación: la tendencia temporal es robusta; los cambios de puesto
entre departamentos con cifras cercanas se interpretan con cautela.
Nota de presentación: los grupos se calculan con valores originales y se
muestran con nombres limpios por legibilidad.
Evidencia: Figuras [X] (tamaños), [X] (departamento), [X] (año),
[X] (sensibilidad por año), [X] (ranking), [X] (grupos más grandes).

### 2.7 Estadísticas descriptivas (datos limpios, 67.122 registros)

cantidad: constante (valor 1, desviación 0). No se usa como variable.

Por año: pico en 2019 (6.904; 10,3 %). Mayor aumento anual: 2015 (+63,9 %).
Entre 2019 y 2025 los registros bajan 37,7 % (cálculo propio). 2026 es
incompleto (2.508 registros, hasta el 31/07/2026); su promedio mensual es
similar al de 2025 (358 vs. 358, cálculo propio).

Por mes (199 meses): media 337,3; mediana 341; desviación estándar 149,9;
mínimo 47; máximo 661 en 05/2018;
coeficiente de variación 44,4 %. La dispersión mezcla tendencia y variación
mensual. En la serie se observa un escalón de nivel hacia 2015.

Género: femenino 86,13 %; masculino 13,16 %; SIN DATO 0,55 %;
NO REPORTA 0,17 %.
Grupo etario: adultos 62,80 %; menores 19,24 %; adolescentes 17,86 %;
SIN DATO 0,10 %.

Medio utilizado: sin empleo de armas 58,54 % en todo el periodo y 80,66 %
desde 2021; «NO REPORTADO» 16,12 % y 0,01 %. Las categorías cambian entre
periodos (p. ej. «ARMA BLANCA / CORTOPUNZANTE» y «CORTOPUNZANTES», esta
última sin registros desde 2021), por lo que no se compara la composición
entre periodos.

Delito: los artículos 209 (31,72 %), 208 (25,83 %) y 205 (15,43 %) reúnen
el 72,98 % (cálculo propio). Los delitos «con menor de 14 años» suman
38.973 registros (58,06 %).

Coherencia delito / grupo etario (cota deducida de los totales): 38.973
registros (58,06 %) tienen un delito «con menor de 14 años», pero solo
24.902 (37,10 %) tienen grupo etario MENORES o ADOLESCENTES. Por lo tanto,
al menos 14.071 registros (20,96 %) tienen delito de menor de 14 años con
otro grupo etario (adultos o sin dato). El cruce exacto está en la
sección 2.9.

Capitales: pesan entre 38,6 % (Sucre) y 52,7 % (Atlántico) de los
registros de su departamento; San Andrés 90,8 % (departamento insular).
Atlántico y Bolívar concentran el 45,2 % del total (cálculo propio).
Conteos absolutos, no tasas.

Decisión: estadísticas numéricas sobre conteos mensuales (cantidad es
constante); medio reportado por periodos; año incompleto fuera de las
comparaciones.
Hipótesis (no verificada): escalones de nivel hacia 2015 y 2018 podrían
reflejar cambios en el registro o la cobertura de la fuente.
Limitación: conteos de denuncias, no tasas ni ocurrencia real.
Evidencia: Figuras [X] a [X].

### 2.8 Atípicos (datos limpios, Caribe)

Problema: no hay variable numérica con varianza; los atípicos se buscan
en los casos por mes y departamento (199 meses por departamento, enero
2010 a julio 2026; los meses sin casos cuentan como 0).
Método: criterio A (IQR global por departamento) y criterio B (mediana
móvil de 13 meses y desviación robusta MAD, |z| > 3,5). Candidatos a
anomalía: meses marcados por ambos con nivel local de al menos 10 casos
al mes (umbral elegido por el autor: por debajo, el z se infla).
Motivo: la serie cambia de nivel (2015, 2018-2021 y caída posterior).

Resultados (1.592 meses-departamento):
- A marca 17 meses (1,07 %), todos altos. B marca 20 (1,26 %). Coinciden 7
  (41,2 % de los de A).
- Años de los atípicos de A: 2019 (10), 2018 (4), 2021 (2), 2022 (1);
  ninguno antes de 2018. 2018 y 2019 reúnen 14 de 17 (82,4 %).
- Por departamento (A / B / ambos): Atlántico 8/1/1; Bolívar 0/2/0;
  Cesar 1/4/1; Córdoba 0/3/0; La Guajira 0/0/0; Magdalena 0/2/0;
  San Andrés 4/6/4; Sucre 4/2/1.
- El cambio de nivel ensancha el IQR: A marca pocos meses y puede ocultar
  anomalías; B detecta desviaciones locales que A no ve.
- Mes más alejado de su nivel local: Cesar, 05/2018 (159 casos frente a
  65; z = 12,7), también atípico en A.
- Entre los 15 más alejados, 13 están por encima de su nivel y 2 por
  debajo (Cesar 11/2024 y Córdoba 12/2013).
- Meses con nivel local menor que 10: 6 de los 20 atípicos locales (30 %),
  todos de San Andrés (niveles de 2 a 7).

Candidatos (A y B, nivel local >= 10): 3 meses.
- Cesar 05/2018: 159 casos con repetidas y 65 sin ellas (94 filas
  repetidas); nivel local 65; z = 12,7.
- Atlántico 08/2018: 203 y 166 (37 filas repetidas); nivel local 140.
- Sucre 10/2019: 67 y 59 (8 filas repetidas); nivel local 39.
Ninguno sigue siendo atípico al quitar las filas repetidas. Los tres caen
en 2018-2019, los años de mayor porcentaje de repetidos (9,8 % y 9,5 %).

Sensibilidad (con vs. sin repetidas): A 17 vs. 16; B 20 vs. 21; ambos 7
vs. 6. Con el criterio B, 11 meses son atípicos en ambos escenarios (55 %
de los 20), 9 solo con repetidas y 10 solo sin ellas.
- Solo con repetidas (9): 6 altos y 3 bajos; desaparecen al quitar las
  filas repetidas, coherente con que esas filas inflaban los meses.
- Solo sin repetidas (10): 5 altos y 5 bajos; es probable que reflejen el
  recálculo del nivel local y la desviación y no anomalías nuevas
  (interpretación no verificada). Magdalena aporta 4 de los 10.

Caso del grupo de 86 filas idénticas (16/05/2018, Cesar, Valledupar): ese
mes tiene 94 filas marcadas como repetidas, de las cuales 85 son del grupo
(las otras 9, de otros grupos; cálculo propio). Es atípico por A y por B
con repetidas y por ninguno sin ellas. El exceso del mes proviene por
completo de filas repetidas.

Cautela: San Andrés aporta 6 atípicos locales y 4 de los 7 que coinciden
en ambos criterios, con conteos muy bajos (11 a 14 casos frente a un nivel
local de 2 a 7); con conteos tan pequeños el z se infla.

Decisión: los atípicos no se eliminan ni se corrigen; se identifican, se
analizan y se conservan, y se reportan con y sin filas repetidas.
Justificación: la serie cambia de nivel; A es conservador y B es sensible
a las repetidas (55 % de estabilidad). Un mes atípico puede deberse a un
aumento real, a una carga masiva o a un cambio de registro; con estos
datos no se puede distinguir. Los tres candidatos más sólidos dependen de
filas repetidas y caen en 2018-2019.
Hipótesis (no verificada): en 2018-2019 el registro generó filas repetidas
en exceso, posiblemente por cargas masivas o cambios en el sistema.
Limitación: departamentos con conteos bajos tienen límites inestables;
los umbrales (3,5; 13 meses; nivel local 10) son convenciones.
Evidencia: Figuras [X] (boxplot), [X] (resumen), [X] (por año),
[X] (los 15 meses), [X] (candidatos), [X] (sensibilidad), [X] (serie de
Cesar con su nivel local).

### 2.9 Distribuciones y relaciones (datos limpios, Caribe)

Delito «con menor de 14 años» y grupo etario (cruce exacto):
- De 38.973 registros: MENORES 11.268 (28,91 %), ADOLESCENTES 7.027
  (18,03 %), ADULTOS 20.630 (52,93 %), SIN DATO 48 (0,12 %).
- Tienen otro grupo etario que menores o adolescentes 20.678 registros
  (53,06 % de ese delito; 30,8 % del total, cálculo propio). La cota de la
  sección 2.7 era 14.071: subestimaba porque 6.607 registros de menores y
  adolescentes están en otros delitos.
- Entre los demás delitos (28.149), el 76,46 % es ADULTOS.
- Sin repetidas, el % de ADULTOS dentro de este delito es 52,44 % (con
  ellas, 52,93 %): las filas repetidas no explican la incoherencia.
- Por año, el % de ADULTOS va de 23,62 % (2013) a 67,53 % (2025): 39,0 %
  en 2010-2017 y 59,8 % en 2018-2026 (cálculo propio). 2015 destaca
  (58,38 %, entre 34,81 % y 39,11 %) y desde 2022 sube cada año (56,07 %
  a 67,53 %).
Definición del grupo etario: Ley 1098 de 2006, art. 3 (menores 0-12,
adolescentes 13-17, adultos desde 18).
Argumento aritmético: una persona menor de 14 años necesita más de 4 años
para cumplir 18. Los hechos de 2023 en adelante tienen menos de 4 años hasta
la extracción (31/08/2026) y, sin embargo, 5.339 de 8.225 (64,91 %) tienen
grupo ADULTOS (cálculo propio; por año: 63,73 %, 62,71 %, 67,53 % y
65,96 %). La aplicación calcula el mismo argumento con los hechos posteriores
al 31/08/2022: [__ de __ (__ %), pegar de la aplicación]. Por lo tanto, las
denuncias tardías no explican esos casos, sea cual sea la fecha de registro
de la edad.
Condición: vale si el grupo etario describe a la víctima; la documentación
no precisa a qué persona ni en qué fecha se refiere la edad.
Explicaciones que quedan (sin verificar): error de captura, definición
distinta de la persona registrada o cambio de registro; el salto de 2018
coincide con otros cambios.

Género y grupo etario (66.639 registros, sin SIN DATO ni NO REPORTA):
V de Cramér = 0,060 (chi-cuadrado 238,4; cálculo propio): asociación débil.
Femenino: 18,54 % MENORES, 18,55 % ADOLESCENTES, 62,91 % ADULTOS.
Masculino: 24,80 %, 14,26 % y 60,94 %. La mayor diferencia está en MENORES
(6,26 puntos).

Departamento y periodo (años completos 2010-2025 en tercios: 2010–2015,
2016–2020 y 2021–2025; 13.700, 27.895 y 23.019 registros; cálculo propio):
- Cesar gana más peso (de 8,0 % a 16,4 %; +8,4 pp), seguido de Bolívar
  (de 17,3 % a 23,0 %; +5,8 pp).
- Sucre pierde más (de 15,2 % a 7,9 %; -7,3 pp), seguido de La Guajira
  (de 8,5 % a 5,2 %).
- Córdoba sube y luego baja (12,4 %, 15,1 % y 9,7 %): pasa de 81 (2012) a
  533 (2013) registros y cae de 1.029 (2021) a 197 (2023), un 81 % en dos
  años, mientras Atlántico cae 35 %.
- Comparar solo 2010 con 2025 daría otro líder (Bolívar, +8,7 pp) porque
  2010 tiene solo 1.062 registros; por eso se usan periodos.
Hipótesis (no verificada): cambios de registro propios de Córdoba.

Distribución mensual (199 meses): media 337,3; mediana 341,0; asimetría
0,13 con los datos originales y -0,97 con el logaritmo; curtosis en exceso
-0,60 y 0,49, respectivamente. Con errores estándar aproximados (0,17 para
la asimetría y 0,34 para la curtosis; cálculo propio), la asimetría original
es compatible con simetría (0,8 errores estándar) y la curtosis original
(-1,7 errores estándar) indica una distribución algo aplanada; con el
logaritmo, la asimetría es claramente distinta de cero (-5,6 errores
estándar). La transformación logarítmica empeora la simetría, por lo que no
se aplica. Se muestra el histograma (escala de densidad) con un estimador de
núcleo gaussiano (Silverman).
En la escala original, la curva muestra una moda principal entre 300 y 400
casos, un hombro entre 100 y 250 y un segundo hombro hacia 500-600; con el
logaritmo, una moda cerca de 5,9 con una cola izquierda larga y un hombro
entre 5,0 y 5,4 (lectura visual del autor). Los hombros son compatibles con
los distintos niveles de la serie (años iniciales y meseta de 2018 a 2021). La forma refleja los cambios de nivel de la serie.

Estacionalidad (años completos 2010 a 2025): mayor índice mediano en agosto
(1,10) y menor en diciembre (0,73), 37,0 puntos de diferencia. Diciembre
quedó por debajo del promedio mensual del año en los 16 años (máximo 0,99);
noviembre tiene índice mediano 0,84. 9 de 12 meses están entre 0,90 y 1,10.
Causa desconocida: debe respaldarse con bibliografía.

Relación entre departamentos: correlación media 0,59 en niveles y 0,17 en
cambios mensuales. Pareja más correlacionada en cambios: Bolívar y Magdalena
(0,34); menos: Bolívar y San Andrés y Providencia (-0,05). San Andrés tiene
correlación casi nula con todos en los cambios (conteos muy pequeños).
Atlántico y Bolívar: r = 0,82 en niveles (r² = 0,67, cálculo propio) y
0,33 en cambios según el mapa de calor (r² ≈ 0,11): casi toda la relación
en niveles viene de la tendencia común.

Decisión: relaciones entre categóricas con tablas de contingencia y V de
Cramér; entre territorios, con correlaciones de conteos mensuales en
niveles y en cambios. No se transforman los datos: el análisis es
descriptivo y el logaritmo no corrige la forma de la distribución.
Justificación: no hay variables numéricas con varianza en el archivo; los
conteos comparten tendencia, por eso se reportan también los cambios; con
muchos registros se reporta la magnitud (V) y no el valor p.
Limitación: el grupo etario se interpreta con cautela hasta confirmar su
definición (53,06 % de los delitos de menor de 14 tiene otro grupo);
la estacionalidad es descriptiva, no una prueba.
Evidencia: Figuras [X] a [X].

---

## FASE 3. ALMACENAMIENTO EN POSTGRESQL NEON (datos limpios)

### 3.1 Diseño de la base de datos
Proyecto nuevo en Neon, base neondb. Siete tablas: departamentos (8),
municipios (197), tipos_delito (22), generos (4), grupos_etarios (4),
medios (11) y la tabla central delitos_limpios (67.122).
Decisiones:
- Claves primarias autogeneradas (IDENTITY); claves naturales como UNIQUE
  (códigos DANE, descripción del delito, nombres de los catálogos).
- Claves foráneas: municipios -> departamentos; delitos_limpios -> municipios,
  tipos_delito, generos, grupos_etarios y medios.
- fila_origen (única): posición del registro en el CSV original nacional;
  conserva la trazabilidad y permite reanudar la carga.
- Municipio = 5 primeros dígitos del código DANE (197 prefijos, cada uno con
  un solo nombre y un solo departamento). centro_poblado = 3 últimos dígitos,
  conservados para reconstruir el código completo (000 = cabecera municipal;
  001 en adelante = centro poblado, según el DANE).
- Capital: es_capital deriva de la marca (CT) de los datos originales (8
  municipios, todos con código de municipio terminado en 001; ningún municipio
  001 queda sin marcar). No se define por el sufijo del código.
- tipos_delito.articulo no es único (el artículo 211 tiene 6 descripciones);
  la clave natural es la descripción.
- Grupos etarios: categorías de la fuente (MENORES 0-12, ADOLESCENTES 13-17,
  ADULTOS desde 18, SIN DATO); no se recalculan edades.
- cantidad se mantiene SMALLINT. Todas las columnas de la tabla central son
  NOT NULL (la limpieza ya reemplazó los nulos por SIN DATO).
- Atributos derivados guardados: es_capital, es_menor_14 y es_repetido (cada
  uno depende solo de la clave de su propia tabla).
- Índices: fecha, municipio y tipo de delito, además de los de claves
  primarias y únicas. Género, grupo y medio tienen 4, 4 y 11 valores.

Evidencia: Figuras [X] (tablas), [X] (estructura), [X] (código SQL).

### 3.2 Preparación y carga (guardar_limpios.py)
Tres fases independientes y reanudables:
1. Preparar: lee el CSV, aplica la limpieza ya validada y escribe
   salida/delitos_limpios.csv (67.122 filas, 16 columnas) y control.json,
   con las huellas SHA-256 del CSV original, del CSV preparado y de los
   archivos de limpieza. Si coinciden, no se vuelve a limpiar.
2. Cargar: DATABASE_URL en el .env (no se entrega). Crea las tablas desde
   01_crear_tablas.sql, carga y compara los catálogos con los esperados del
   CSV, e inserta los hechos en 14 lotes de 5.000, confirmados uno a uno con
   ON CONFLICT. Solo inserta lo que falta.
3. Verificar: conteos, distribución territorial y comparación exacta
   registro a registro entre la base y el CSV preparado.
Nota: el id puede tener huecos si hubo reintentos; la garantía de
trazabilidad es fila_origen.

### 3.3 Resultados de la carga (salida del script)
Registros 67.122; departamentos 8; municipios 197; tipos de delito 22;
géneros 4; grupos etarios 4; medios 11. Género SIN DATO 370 y NO REPORTA 113;
grupo etario SIN DATO 68. Repetidos 4.688; registros en capitales 32.131;
delitos de menor de 14 años 38.973; registros con centro poblado distinto de
000 1.415; suma de cantidad 67.122. Municipios fuera de su departamento: 0.
Rango de fechas: 01/01/2010 a 31/07/2026.
Por departamento: Atlántico 16.664; Bolívar 13.670; Magdalena 8.725; Cesar
8.613; Córdoba 8.372; Sucre 6.413; La Guajira 3.938; San Andrés y Providencia
727.
Comparación exacta contra el CSV preparado: faltantes 0, adicionales 0,
con diferencias 0.
Resultado: «VERIFICACIÓN COMPLETA: todas las comprobaciones coinciden».
Evidencia: Figura [X] (terminal).

### 3.4 Verificación en el editor SQL de Neon (02_verificaciones.sql)
Las consultas de comprobación V1 a V12 se ejecutaron correctamente en el
editor SQL de PostgreSQL (Neon) y todos los resultados coincidieron con los
valores esperados. Son consultas de solo lectura: no modifican la base.

Valores comprobados:
- V1 (filas por tabla): departamentos 8; municipios 197; tipos_delito 22;
  generos 4; grupos_etarios 4; medios 11; delitos_limpios 67.122.
- V2 (trazabilidad): 67.122 registros y 67.122 valores distintos de
  fila_origen; primera fila del CSV original 6 y última 405.192.
- V3 y V4 (integridad): 0 registros sin catálogo asociado y 0 municipios
  fuera de su departamento.
- V5 (por departamento): Atlántico 16.664; Bolívar 13.670; Magdalena 8.725;
  Cesar 8.613; Córdoba 8.372; Sucre 6.413; La Guajira 3.938; San Andrés y
  Providencia 727.
- V6 (género y grupo etario): género SIN DATO 370 y NO REPORTA 113; grupo
  etario SIN DATO 68.
- V7 (atributos derivados): repetidos 4.688; registros en capitales 32.131;
  delitos de menor de 14 años 38.973.
- V8 (centro poblado y códigos DANE): 1.415 registros con sufijo distinto de
  000; 477 códigos completos con ese sufijo; 674 códigos completos distintos
  en todos los registros (477 + 197 municipios con registros en cabecera).
- V9 (fechas y cantidad): del 01/01/2010 al 31/07/2026; suma de cantidad
  67.122.
- V10 (capitales): 8 municipios con es_capital (Barranquilla, Cartagena,
  Valledupar, Montería, Riohacha, Santa Marta, Sincelejo y San Andrés). La
  capitalidad se determina con es_capital, derivada de la marca (CT) de los
  datos originales, no con el sufijo del código DANE.
- V11 (prueba de lectura): los registros se leen con sus nombres de catálogo
  y coinciden con los del CSV (fila_origen 6, 8 y 9; la fila 9, idéntica a la
  8, aparece marcada como repetida).
- V12 (estructura): columnas, restricciones e índices del esquema.

Documentación del esquema: se documentaron las tablas y columnas mediante
comentarios COMMENT ON en PostgreSQL.

Con esta verificación se da por cerrada la Fase 3.
Evidencia: Figuras [X] a [X].

## FASE 4. TABLERO EN POWER BI

**Convención de estado**
- **Implementado:** construido en Power BI Desktop según lo confirmado.
- **Verificado:** con cifra registrada.
- **Reportado correcto:** confirmado como «coincide» o «todo correcto» sin registrar la cifra.
- **[ ]:** pendiente de confirmar o completar.

### 4.1 Conexión y requisitos
- Power BI Desktop 2.159.1231.0 (64 bits, octubre de 2026), en Windows.
- Conexión a PostgreSQL Neon (base `neondb`), modo **Importar**, SSL activo. No hay consulta en vivo: el tablero guarda una instantánea de los datos al actualizar. Credenciales solo en el equipo local; no se crearon usuarios ni roles y no se modificó Neon.
- En «Archivo actual» se desactivaron «Fecha y hora automáticas» y la detección de relaciones, para crear las relaciones a mano.
- Evidencia: Figuras [X] (Navegador con las siete tablas) y [X] (Power Query), sin host ni credenciales.

### 4.2 Verificaciones previas en Neon (solo lectura, consultas A1 a D2)
- `medios.nombre`: 11 categorías; el texto exacto es `NO REPORTADO` y existe `SIN EMPLEO DE ARMAS`.
- `generos.nombre`: FEMENINO, MASCULINO, NO REPORTA, SIN DATO. `grupos_etarios.nombre`: ADOLESCENTES, ADULTOS, MENORES, SIN DATO.
- Sin espacios extremos; longitudes reales iguales a las declaradas (`centro_poblado` CHARACTER(3), `municipios.cod_dane` CHARACTER(5), `departamentos.cod_dane` CHARACTER(2)).
- Ceros iniciales: los 67.122 `centro_poblado`, 23 códigos de municipio y 1 de departamento empiezan en cero; por eso se conservan como **texto**.
- Cero nulos en todos los campos comprobados de `delitos_limpios` y de los catálogos.
- Rango 01/01/2010 a 31/07/2026; 6.003 días con registros y 53 sin registros (suman los 6.056 días del rango). Los años 2010 a 2025 tienen registros en sus 12 meses; 2026, en 7.
- Los años 2010 (27/12), 2014 (30/12) y 2024 (29/12) terminan antes del 31 de diciembre.

### 4.3 Importación y transformaciones (Power Query)
Implementado:
- Siete tablas importadas: `delitos_limpios`, `departamentos`, `municipios`, `tipos_delito`, `generos`, `grupos_etarios`, `medios`. En Power BI aparecen con el prefijo `public` (por ejemplo `'public delitos_limpios'`).
- Cambios de nombre visibles en columnas: `Departamento`, `Municipio`, `Género`, `Grupo etario`, `Medio`, `Artículo`, `Delito`, `Fecha del hecho`. No se renombraron tablas, claves ni columnas `es_*`.
- Columna condicional `Orden grupo etario` en `grupos_etarios` (MENORES 1, ADOLESCENTES 2, ADULTOS 3, SIN DATO 4). Se creó en Power Query porque la versión en DAX generó una dependencia circular al ordenar `Grupo etario` por ella.
- **Alcance de las transformaciones:** no se eliminaron registros ni se alteraron los valores originales de las variables analíticas. Los cambios fueron de otra naturaleza: nombres visibles, la columna de orden añadida y la revisión de tipos de dato (`centro_poblado` y los dos `cod_dane` se mantuvieron como texto).

Reportado correcto (sin detalle): revisión de tipos y perfilado (100 % válido) y recuento de filas tras cargar.
**[ ]** Si apareció el paso «Tipo cambiado» y qué contenía; si hubo corrección de tipo en `Fecha del hecho`.

### 4.4 Modelo de datos
Implementado: siete relaciones, todas varios a uno con filtro en un solo sentido.

| Desde (muchos) | Hacia (uno) |
|---|---|
| `municipios[departamento_id]` | `departamentos[id]` |
| `delitos_limpios[municipio_id]` | `municipios[id]` |
| `delitos_limpios[tipo_delito_id]` | `tipos_delito[id]` |
| `delitos_limpios[genero_id]` | `generos[id]` |
| `delitos_limpios[grupo_etario_id]` | `grupos_etarios[id]` |
| `delitos_limpios[medio_id]` | `medios[id]` |
| `Calendario[Fecha]` | `delitos_limpios[Fecha del hecho]` |

Tablas sin relaciones: `Medidas` (contenedor de medidas; `Columna1` oculta porque Power BI no permite eliminarla) y `Selector repetidos`.
Reportado correcto: ocultación de columnas técnicas (`id`, claves foráneas, `fila_origen`, `cantidad`, `cod_dane`, `edad_min`, `edad_max`, `Orden grupo etario`). **[ ]** Lista efectiva de columnas ocultas.

### 4.5 Calendario
Tabla calculada en DAX de 6.056 filas (verificado: coincide con el total de días de D1), del 01/01/2010 al 31/07/2026, marcada como tabla de fechas y relacionada con `Fecha del hecho`.
Columnas: `Fecha`, `Año`, `Mes número`, `Mes` (ordenada por `Mes número`), `Mes (inicio)`, `Periodo` (2010-2015, 2016-2020, 2021-2025, «2026 (parcial)») y `Estado del año` («Año con registros en los 12 meses» / «Periodo parcial»).
Incidencia: `Fecha` y `Mes (inicio)` mostraban hora; se corrigió. La hora aparecía solo en el Calendario, no en `delitos_limpios`.
«Año con registros en los 12 meses» no afirma cobertura diaria completa.

### 4.6 Medidas DAX
Implementado: medidas en la tabla `Medidas`, cada una con numerador, denominador y tratamiento de `SIN DATO` / `NO REPORTA` definidos antes de escribirla. Las fórmulas usan el prefijo `public` en los nombres de tabla.

**Reglas generales**
- Conteo con `COUNTROWS`; `SUM(cantidad)` solo como validación.
- Denominador: todos los registros del contexto, con `SIN DATO`, `NO REPORTA` y `NO REPORTADO` dentro y separadas.
- `[Registros]` obedece al interruptor de repetidos; `[Registros totales]` no.

**Grupos de medidas**
- **Conteo:** Registros totales, Registros repetidos, Registros sin repetidos, Registros, Suma de cantidad (validación).
- **Perfil:** % por género, % por grupo etario, % menores y adolescentes, % femenino.
- **Territorio:** Registros en capitales, % en capitales, Municipios con registros, % municipio sobre su departamento, Participación territorial.
- **Delitos:** Registros delito menor de 14, % delitos de menor de 14, % por delito.
- **Incoherencia etaria (con interruptor):** % ADULTOS en delito menor de 14 y % grupo distinto de menores y adolescentes en delito menor de 14 (incluye `SIN DATO`).
- **Incoherencia etaria (calidad):** las mismas sobre `[Registros totales]`, más la versión sobre `[Registros sin repetidos]`.
- **Calidad (sobre `[Registros totales]`):** % repetidos, Registros y % género SIN DATO, Registros y % medio NO REPORTADO.
- **Medio (provisional):** Corte medio (provisional) = 2021, % sin empleo de armas (todo el periodo), % sin empleo de armas desde el corte, % medio desde el corte.
- **Temporales:** Registros año anterior, Variación interanual (solo años con registros en los 12 meses; 2010 y 2026 devuelven vacío), Registros año completo, Registros año parcial.

**Incidencias corregidas**
1. Dependencia circular en el orden de grupo etario (resuelta en Power Query).
2. `% en capitales`: el denominador con `REMOVEFILTERS(municipios)` quitaba también el filtro de departamento; con Atlántico daba 13,08 % en lugar de ~52,7 %. Fórmula final: `DIVIDE([Registros en capitales], [Registros])`.
3. `% municipio sobre su departamento`: mismo riesgo; corregida reponiendo `departamento_id` con `VALUES`.

Lección: los controles sin filtros no detectan este tipo de error; hay que probar con un departamento seleccionado.

### 4.7 Páginas del informe (cinco)
Implementado según el diseño acordado; reportado correcto por el autor. Las características visuales (paleta, fondo, formato de títulos) no se registran como confirmadas.

| Página | Pregunta | Contenido principal | Cautela prevista en el diseño |
|---|---|---|---|
| 1. Resumen | P1 | 4 KPI (registros, % femenino, % menores y adolescentes, % en capitales); serie mensual; columnas por año | 2026 parcial; saltos de 2015 y 2018 sin causa verificada |
| 2. Territorio | P2 | 3 KPI; departamentos; 15 municipios; % en capital; participación por periodo | Conteos, no tasas; significado de (CT) no definido |
| 3. Perfil | P3 | 3 KPI; género; grupo etario; matriz género × grupo; composición y % femenino por departamento | Edad: persona y fecha no precisadas |
| 4. Delitos y medio | P4 | 4 KPI; artículos; tendencia de los 3 principales; detalle del artículo 211; medio desde el corte | Medio **provisional** (corte 2021) |
| 5. Calidad | Limitaciones | 5 KPI; repetidos por año y departamento; SIN DATO y NO REPORTADO por año; incoherencia etaria | Siempre incluye repetidos; hipótesis de cambios de registro no verificada |

**Filtros:** interruptor de repetidos (páginas 1 a 4), Año y Departamento (1 a 5), Artículo (página 4). La sincronización de segmentadores fue realizada.
**Quedaron fuera del tablero:** atípicos, V de Cramér, correlaciones y mapa (el modelo no tiene coordenadas).

### 4.8 Verificaciones y resultados

**Verificado (con cifra en la conversación)**
- Calendario: 6.056 filas, rango correcto.
- Consultas A1 a D2: valores de 4.2 (fuente de control: consultas V1 a V12 de la sección 3.4).
- `% menores y adolescentes`: 37,10 % con repetidos (coincide con 24.902 / 67.122); 37,25 % sin repetidos (cifra nueva).
- Género y grupo etario con repetidos: 86,13 / 13,16 / 0,55 / 0,17 y 62,80 / 19,24 / 17,86 / 0,10, coincidentes con la bitácora; ambas tablas suman 100 %.
- Armas con repetidos: coinciden con 58,54 % y 80,66 %. Sin repetidos: 58,04 % y 80,12 % (cifras nuevas, provisionales).
- `% en capitales` con Atlántico: 13,08 % antes de la corrección (error documentado).

**Reportado correcto (sin cifra)**
- Recuento de las siete tablas; tarjetas de conteo (67.122; 4.688; 62.434; suma de cantidad 67.122).
- Medidas de los pasos 10 y 11 (incluidos 52,93 % y 53,06 %).
- Variación interanual (2015 +63,9 %), 2019 = 6.904, Atlántico + Bolívar = 45,2 %, matriz por periodo.
- Ranking de departamentos y `% en capitales` tras la corrección.
- Controles «sin repetidos» con referencia en el EDA: 6.245 en 2019, Córdoba 7.999 frente a Cesar 7.918, 52,44 %.
- Las cinco páginas.

**[ ] Sin confirmar valor:** véase «Verificaciones complementarias».

### 4.9 Decisiones metodológicas de la fase
1. Denominador sobre todos los registros del contexto; categorías sin información visibles y separadas.
2. Interruptor «Con repetidos» (por defecto) / «Sin repetidos»; la página 5 siempre muestra repetidos.
3. 2026 es periodo parcial: visible en la serie mensual, fuera de las comparaciones interanuales.
4. 2010 a 2025 se denominan «años con registros en los 12 meses», sin afirmar cobertura diaria completa.
5. `armas_medios` desde 2021: **provisional**, con una sola medida de corte.
6. Solo conteos absolutos, sin tasas por 100.000 habitantes.
7. Artículos en los gráficos principales; descripciones solo para el artículo 211.
8. Dos medidas de incoherencia etaria con nombre y definición distintos.
9. Credenciales solo locales; Neon sin cambios.

### 4.10 Limitaciones de la fase
- 2010, 2014 y 2024 terminan antes del 31/12; los 53 días sin registros no se han distribuido por año.
- El modelo de importación guarda una instantánea de los datos.
- Las cifras «sin repetidos» son nuevas y, salvo las indicadas, no tienen referencia en el EDA.
- Las medidas del medio siguen sujetas al corte provisional.
- Atípicos, correlaciones y V de Cramér no forman parte del tablero.

### Estado de la fase
**Dashboard construido** (modelo, medidas, cinco páginas y sincronización de segmentadores). Lo pendiente es limpieza del PBIX, evidencias y verificaciones complementarias, que no cuestionan la construcción. Para esta versión se asume eliminada la página de prueba.

### Pendientes de la Fase 4

**1. Funcionalidad del dashboard**
- Ninguno identificado. La sincronización está realizada.

**2. Limpieza y revisión del PBIX**
- Página de prueba: se asume eliminada para efectos de esta documentación; comprobar su eliminación durante la revisión final del PBIX.
- Revisar el origen de datos y decidir opción A o B sobre el host.
- Revisar la configuración del origen de datos y las credenciales antes de compartir el archivo. No incluir contraseñas ni cadenas de conexión sensibles en las evidencias.
- Guardar con nombre coherente (por ejemplo `Apellido_Nombre_Dashboard.pbix`).

**3. Evidencias para la entrega**
- Las capturas de Power BI corresponden a la Fase 4, sin host ni credenciales: Navegador, Power Query, Vista de datos (67.122), Vista de modelo, panel de medidas, cinco páginas, un filtro aplicado, interruptor «Sin repetidos».
- Guardarlas en `04_capturas/`.
- La entrega completa también debe incluir evidencias gráficas de PostgreSQL Neon, Python y Streamlit, según los requisitos de la actividad.

**4. Verificaciones complementarias**
- Escritura del artículo 211 y sus seis descripciones; número de artículos distintos.
- NO REPORTADO del visual 4; `% delitos de menor de 14` sin repetidos; valores por año de la página 5.
- Paso «Tipo cambiado» y tipo de `Fecha del hecho`; lista efectiva de columnas ocultas.
- Consulta opcional de los 53 días sin registros por año.
- Heredadas, abiertas en la bitácora general: corte 2021, (CT), persona y fecha de la edad, documentación vigente, consulta al docente.

### Revisión crítica de la Fase 4

**Omisiones posibles**
- Un anexo con las fórmulas finales tal como quedaron en el equipo (con prefijo `public`), útil para entrega y artículo.
- Mencionar Power BI y su origen de datos en el README.
- Fecha y hora de la última actualización de datos.

**Inconsistencias a corregir en la bitácora general**
- La sección 2.5 mezcla «NO REPORTA» y «NO REPORTADO»; esta fase fijó `NO REPORTADO` en medio y `NO REPORTA` en género.
- «Power BI conectado directamente» debería precisar que es modo Importar.
- «2021 en adelante» no aclara si incluye 2026. Solo se puede afirmar que la fórmula indicada usa `Año >= corte`, es decir, lo incluye; no se comprobó lo que quedó en el equipo.

**Sugerencias**
- Registrar la cifra al verificar cada control, aunque sea en una tabla breve.
- Si en el artículo se menciona cómo interactúan las medidas de corte o de año anterior con el segmentador de Año, comprobarlo antes contra las fórmulas finales del equipo.

## FASE 5. HALLAZGOS, RECOMENDACIONES Y REDACCIÓN

Convención de esta fase: cada resultado se clasifica como CONFIRMADO
(leído en el dashboard durante la revisión de las cinco páginas),
PENDIENTE (requiere verificación contra datos o scripts), LIMITACIÓN o
INTERPRETACIÓN (lectura del autor, no demostrada). Las cifras del
dashboard no se recalcularon. Donde coinciden con cifras ya documentadas
del EDA (Fase 2) o de la base (Fase 3) se indica la coincidencia como
contraste cruzado, sin sustituir la verificación formal.
Esta fase es documental: no modifica código Python, scripts SQL, la
estructura de Neon, los datos, el dashboard ni el archivo de Power BI.

### 5.1 Alcance de la revisión
Se revisaron las cinco páginas del dashboard conectado a delitos_limpios
(67.122 registros, Caribe, 01/01/2010 a 31/07/2026). Cada página responde
a una de las preguntas de negocio de la sección 0.2 (evolución temporal,
territorios, perfil, delitos) más una página de calidad de datos que
permite al lector del tablero medir la fiabilidad de lo anterior.
Variables del modelo utilizadas (según el esquema de la sección 3.1):
fecha (año y mes), departamento, municipio, género, grupo etario, tipo de
delito (artículo y descripción), medio, es_capital, es_menor_14 y
es_repetido.
[PENDIENTE] Registrar los nombres exactos de las medidas DAX y de los
segmentadores de cada página (no se documentaron en esta revisión).

### 5.2 Página 1. Análisis temporal
Qué se analizó: la evolución de los registros por año y por mes, para
responder cómo ha cambiado el volumen de casos reportados.
Variables: fecha (año, mes); conteo de registros (cantidad es constante = 1).
CONFIRMADO:
- Total de registros analizados: 67.122.
- Entre los años completos, el máximo es 2019 con 6.904 registros.
Contraste cruzado: coincide con la sección 2.7 (pico en 2019; 6.904; 10,3 %
del total, cálculo del EDA).
Interpretación: el volumen no crece de forma monótona; alcanza un máximo
en 2019 y disminuye después (en el EDA, -37,7 % entre 2019 y 2025, cálculo
propio de la Fase 2). La caída no puede leerse como reducción real de la
violencia sexual (ver limitaciones).
Limitaciones: son denuncias, no ocurrencia (subregistro); 2026 es un año
incompleto (hasta el 31/07/2026) y no debe compararse con años completos;
los escalones de nivel hacia 2015 y 2018 pueden reflejar cambios de
registro (hipótesis de la sección 2.7, no verificada).
PENDIENTE: confirmar que el dashboard muestra 2026 diferenciado como año
incompleto y registrar qué filtros temporales ofrece.

### 5.3 Página 2. Análisis territorial
Qué se analizó: la concentración de casos por departamento (y municipio,
con capitales marcadas con es_capital).
Variables: departamento, municipio, es_capital; conteo de registros.
CONFIRMADO:
- Atlántico: 24,83 % de los registros.
- Bolívar: 20,37 % de los registros.
Contraste cruzado: equivalen a 16.664 y 13.670 registros (secciones 2.7 y
3.3); juntos suman 45,2 % del total, como ya documentado.
Interpretación: dos de ocho departamentos reúnen casi la mitad de los
casos, lo que orienta la priorización territorial, que es la decisión que
el proyecto busca apoyar (sección 0.2).
Limitaciones: conteos absolutos, no tasas por 100.000 habitantes; la
fuente no trae población, por lo que un departamento grande aparece alto
por tamaño y no necesariamente por mayor incidencia. Pesos de capitales
entre 38,6 % y 52,7 % (San Andrés 90,8 %), ver sección 2.7. Los
rankings entre departamentos con cifras cercanas son sensibles a las
filas repetidas (Cesar y Córdoba intercambian puestos, sección 2.6).
PENDIENTE: decidir si se incorporan tasas con población externa (pendiente
general) y registrar si el dashboard muestra el ranking con y sin repetidos.

### 5.4 Página 3. Perfil de las víctimas
Qué se analizó: composición por género y grupo etario, y su variación por
territorio.
Variables: género, grupo etario, es_menor_14.
CONFIRMADO:
- Participación femenina: 86,13 %.
- Menores y adolescentes: 37,10 % de los registros.
Contraste cruzado: coincide con la sección 2.7 (femenino 86,13 %; 24.902
registros de MENORES o ADOLESCENTES = 37,10 %).
Interpretación: el fenómeno registrado es predominantemente femenino y
más de un tercio de los registros corresponde a personas menores de 18
años según la categoría de la fuente. La asociación entre género y grupo
etario es débil (V de Cramér = 0,060, sección 2.9), por lo que el perfil
etario es similar entre géneros.
Limitaciones: la categoría etaria no es consistente con el tipo de delito:
53,06 % de los registros con delito «con menor de 14 años» tiene otro grupo
etario (sección 2.9); la documentación no precisa a quién ni en qué fecha
se refiere la edad. Por ello el 37,10 % debe presentarse como lo que
registra la fuente, no como medida definitiva de la proporción de
víctimas menores. SIN DATO (género 0,55 %; grupo 0,10 %) y NO REPORTA
(género 0,17 %) se mantienen como categorías separadas.
PENDIENTE: porcentaje de registros de delito «con menor de 14 años» sin
filas repetidas (valor aún no verificado para esta página; el dato
disponible, 52,44 % de ADULTOS dentro de ese delito sin repetidas, es
otra medida y no lo sustituye). Registrar cómo muestra el dashboard esta
incoherencia, si la muestra.

### 5.5 Página 4. Delitos y medios
Qué se analizó: los tipos de delito predominantes, su tendencia y el medio
utilizado.
Variables: tipo de delito (artículo y descripción), medio, año.
CONFIRMADO:
- Los artículos 209, 208 y 205 concentran conjuntamente el 72,98 % de los
  registros del análisis por artículos.
- Se revisó la tendencia de los tres artículos principales.
- Se examinó el detalle del artículo 211.
- Se revisó la distribución de medios con un corte provisional desde 2021.
Contraste cruzado: 72,98 % coincide con la sección 2.7 (209: 31,72 %;
208: 25,83 %; 205: 15,43 %).
Interpretación: la concentración en tres artículos indica que la
priorización por tipo de delito puede centrarse en pocas conductas. El
artículo 211 requiere lectura aparte porque agrupa seis descripciones
distintas (sección 3.1): agregarlo por artículo oculta diferencias
entre modalidades.
Limitaciones: la distribución de medios no es comparable en todo el
periodo. «NO REPORTADO» pesa 16,12 % del total, concentrado en 2010-2013 y
2018-2020 y prácticamente ausente desde 2021 (sección 2.5); el cambio
refleja el criterio de registro, no la conducta. Por eso el corte
«desde 2021» es provisional (marcado «por confirmar» en la sección 2.2) y la
evolución del medio no se interpreta como cambio de comportamiento.
PENDIENTE (no presentar como definitivo):
- Detalle específico del artículo 211 (qué descripciones y qué cifras
  muestra el dashboard).
- Las seis descripciones de artículos pendientes de validar.
- Número definitivo de artículos analizados (la base tiene 22 descripciones
  de delito; el número de artículos distintos no está confirmado).
- Interpretación del indicador «NO REPORTADO» de la página 4.
- Interpretación del corte provisional de medios desde 2021.

### 5.6 Página 5. Calidad de los datos
Qué se analizó: la fiabilidad del conjunto: filas repetidas, valores sin
dato y consistencia, para que el lector sepa cuánto confiar en las
páginas 1 a 4.
Variables: es_repetido, género, grupo etario, medio, año.
CONFIRMADO:
- 4.688 registros excedentes por repetidos, equivalentes al 6,98 %.
- Se revisaron los indicadores de calidad y consistencia.
Contraste cruzado: coincide con la sección 2.6 (4.688 filas; 6,98 %; 3.760
grupos).
Interpretación: casi 7 de cada 100 filas son excedentes de otra idéntica.
Como la fuente no tiene identificador de caso, no se pueden distinguir
registros duplicados de denuncias distintas con atributos iguales; por eso
se marcaron y no se eliminaron. La conclusión temporal es robusta (año pico
y dirección de las variaciones coinciden con y sin repetidos, sección 2.6).
Limitaciones: la causa de los repetidos es desconocida; se concentran en
2018-2019 (9,8 % y 9,5 % en el EDA).
PENDIENTE: valores anuales de la página 5 (se revisaron, pero no se
registraron en esta bitácora; deben contrastarse con la sección 2.6 antes
de citarlos). Registrar qué indicadores de consistencia aparecen en la
página.

### 5.7 Patrones transversales
1. Concentración: pocos territorios (Atlántico y Bolívar) y pocos delitos
   (209, 208, 205) explican la mayor parte de los registros.
2. Perfil: predominio femenino (86,13 %) y más de un tercio de menores y
   adolescentes (37,10 %), con la reserva de la incoherencia entre delito y
   grupo etario.
3. Dependencia de la calidad del registro: los cambios de nivel, repetidos,
   nulos de género y «NO REPORTADO» se concentran hacia 2018 y alrededor de
   2021. La interpretación temporal debe leerse junto con la página 5.
4. Coherencia dashboard-EDA: las cifras confirmadas de las páginas 1 a 5
   coinciden con las del EDA y la base, lo que respalda que el tablero no
   introdujo discrepancias (contraste cruzado; no sustituye la
   verificación formal de las medidas DAX).

### 5.8 Cuadro de estado
CONFIRMADO: 67.122 registros; 2019 máximo con 6.904; Atlántico 24,83 %;
Bolívar 20,37 %; femenino 86,13 %; menores y adolescentes 37,10 %;
artículos 209, 208 y 205 = 72,98 %; 4.688 repetidos (6,98 %).
PENDIENTE DE VERIFICACIÓN: detalle del artículo 211; seis descripciones
por validar; número definitivo de artículos; interpretación de «NO
REPORTADO» (página 4); % de menores de 14 años sin repetidos; valores
anuales de la página 5; corte de medios desde 2021; nombres de medidas y
segmentadores.
LIMITACIONES: denuncias, no ocurrencia; sin población (sin tasas); sin
identificador de caso; criterio de medio y género cambiante en el tiempo;
incoherencia delito/grupo etario; 2026 incompleto; cifras sujetas a
consolidación con la Fiscalía.
INTERPRETACIONES (no demostradas): descenso posterior a 2019 como cambio
de registro y no solo de ocurrencia; repetidos de 2018-2019 por cargas
masivas o cambios de sistema; incoherencia etaria por error de captura o
definición distinta de la persona registrada.

### 5.9 Recomendaciones candidatas (borrador para el artículo)
Derivadas solo de resultados confirmados; se validan al redactar.
- Focalizar prevención y atención en los departamentos y delitos de mayor
  concentración, usando tasas cuando se disponga de población.
- Priorizar la atención de población femenina y de menores y adolescentes.
- Mejorar el registro: identificador único de caso, diccionario de
  variables, criterio estable del medio y de la edad (persona y fecha).
- Presentar siempre los resultados con y sin repetidos y señalar los años
  de cambio de criterio.
Estado: borrador; no se redacta el artículo todavía.
Evidencia: Figuras [X] (cinco páginas del dashboard; pendiente numerar
y guardar en 04_capturas/).

---

## ENTREGA FINAL (instrucciones del profesor, 21/11/2026)
Fecha límite: 23 de noviembre de 2026, 3:30 p. m.
1. Artículo científico únicamente en formato Word (.docx).
2. Carpeta comprimida con el proyecto Python: script de la base de datos,
   códigos Python y README.txt con instalación, proceso y pruebas.
3. Un único archivo individual del proyecto de Power BI, sin comprimir.
   El profesor indicó la extensión «.pbi»; [PENDIENTE] confirmar si se
   refiere a .pbix o .pbip.
Notas:
- No incluir .env ni .venv; incluir .env.example y requirements.txt.
- [PENDIENTE] Confirmar con el profesor si la copia del CSV original y las
  capturas siguen siendo exigibles, ya que la guía inicial (ACTIVIDAD
  FINAL) los pedía y estas instrucciones no los mencionan. Las capturas
  deben ir dentro del artículo en Word.
- La guía inicial mantiene: mínimo 4.000 palabras, 15 referencias APA,
  máximo 15 % de similitud y de IA, evidencias de Neon, Python, Streamlit
  y Power BI.
- Verificar que el README.txt permita reproducir las pruebas (por ejemplo,
  verificar_carga.py y 02_verificaciones.sql).
---

## CIFRAS CLAVE
Nacional: 405.193 registros | Caribe: 67.122 (16,6 %)
Caribe, nulos: genero 370 (0,55 %), grupo_etario 68 (0,10 %)
Concentración: 98,1 % de los nulos de genero desde 2018
NO REPORTA en armas_medios: 10.822 (16,12 %)
Repetidos: 4.688 (6,98 %), en 3.760 grupos; grupo máximo de 86 filas
Capitales: 32.131 registros (47,9 %)
Atípicos: A 17 (1,07 %), B 20 (1,26 %), ambos 7; con B, solo 11 de 20
persisten sin repetidas
Candidatos sólidos: 3 (todos en 2018-2019), ninguno persiste sin repetidas
Delito de menor de 14 con otro grupo etario: 20.678 (53,06 % de ese delito)

## HIPÓTESIS (no verificadas)
- Los repetidos, los nulos de genero y el «NO REPORTA» del medio cambian
  alrededor de 2017-2018 (y el «NO REPORTA» desaparece desde 2021). Podría
  reflejar cambios en el sistema de registro de la fuente. La fuente
  documenta una nueva metodología de validación con la Fiscalía, sin fecha:
  es compatible, pero no demostrada.
- Los candidatos a anomalía caen en 2018-2019, años de mayor porcentaje de
  filas repetidas.
- Cambios de nivel propios de Córdoba (2013 y 2022-2023).
- El % de ADULTOS dentro de los delitos de menor de 14 sube de 39,0 % a
  59,8 % desde 2018.

## LIMITACIONES A DECLARAR
- Sin identificador único de caso (duplicados indistinguibles).
- Nulos de genero concentrados desde 2018, causa desconocida.
- armas_medios no comparable en todo el periodo.
- Los datos son denuncias, no ocurrencia real (subregistro).
- Sin población: conteos absolutos, no tasas.
- 53,06 % de los delitos de menor de 14 años tiene grupo etario ADULTOS o
  SIN DATO (20.678 registros); la documentación no precisa a qué persona ni
  en qué fecha se refiere la edad registrada.
- Criterio B de atípicos sensible a las filas repetidas.
- Cifras recientes sujetas a variación por consolidación con la Fiscalía.
- El conjunto no trae diccionario de variables ((CT), persona y fecha de
  la edad).

## PENDIENTES
- Confirmar con la fuente el significado de (CT), de los 3 últimos dígitos
  del código DANE y de la persona y la fecha de la edad registrada (la
  propia fuente invita a reportar inconsistencias por correo).
- Contrastar la documentación archivada (2022) con la versión vigente.
- Confirmar el corte "2021 en adelante" para armas_medios.
- Decidir tasas por 100.000 habitantes o solo conteos.
- Completar los marcadores de las secciones 2.7 (mes del máximo) y 2.9
  (argumento desde el 31/08/2022 y descripción de las curvas).
- Fases 4 (Power BI) y 5 (artículo).
- Numerar y guardar las capturas (04_capturas/).
- Consultar al docente si los datos y la Ley 1098 pueden citarse aparte de
  las 15 referencias de los últimos 3 años.

---

## PENDIENTES (actualización 21/11/2026, Fase 5 y entrega)
- Recuperar o pegar el texto de la Fase 4 (partes 1 a 4) de la última versión.
- Verificar: artículo 211, seis descripciones, número de artículos,
  indicador «NO REPORTADO», % de menores de 14 sin repetidos, valores
  anuales de la página 5, corte de medios desde 2021.
- Registrar nombres de medidas DAX y segmentadores; numerar capturas del
  dashboard (04_capturas/).
- Confirmar extensión del archivo de Power BI (.pbi / .pbix / .pbip) y si
  el CSV original sigue siendo exigible.
- Preparar README.txt y la carpeta comprimida del proyecto Python.
- Redactar el artículo en Word con la PLANTILLA (después de cerrar esta
  documentación): 4.000+ palabras, 15 referencias de los últimos 3 años.
- Entregar antes del 23/11/2026, 3:30 p. m.
---

## NOTAS PARA REDACTAR EL ARTÍCULO

Valores faltantes. Los valores nulos se reemplazaron por la categoría
«SIN DATO» y se mantuvieron diferenciados de «NO REPORTA», que es una
categoría declarada por la fuente. La distinción permitió identificar que
los nulos de género se concentran desde 2018, y deja abierta la
posibilidad de agruparlos en el análisis.

Conservación de datos. El dato fuente no se modificó: la limpieza produjo
una copia derivada en la que no se eliminó ningún registro. Los nulos se
reemplazaron por una categoría explícita, las filas repetidas se marcaron
y los atípicos se conservaron, porque la fuente no permite distinguir
entre registros duplicados y casos distintos.

Gestión de datos (estructura sugerida de la metodología): fuente y
descripción; lectura y filtro de la región; limpieza y EDA en Python;
almacenamiento de los datos limpios en PostgreSQL (Neon); conexión directa
de Power BI.

---

## PLAN DE CAPTURAS (EDA)
Guardar en 04_capturas/ con nombre numerado; cada figura se menciona y se
comenta en el texto («Figura N. Título. Elaboración propia»).
fig01_verificacion_carga.png ............ salida de verificar_carga.py (hecha)
fig02_app_inicio.png .................... Inicio: menú y proceso
fig03_filtro_caribe.png ................. Carga: tabla de departamentos y ranking
fig04_no_reporta_medio_anio.png ......... Faltantes, apartado 3
fig05_nulos_genero_anio.png ............. Faltantes, apartado 4
fig06_duplicados_grupos.png ............. Duplicados, apartado 2 (grupos más grandes)
fig07_duplicados_sensibilidad.png ....... Duplicados, apartados 4 y 5
fig08_serie_mensual.png ................. Descriptivas, apartado 4
fig09_genero_grupo_etario.png ........... Descriptivas, apartado 5 (donas)
fig10_atipicos_cesar.png ................ Atípicos, apartado 4 (serie con nivel local)
fig11_atipicos_candidatos.png ........... Atípicos, apartado 5
fig12_delito_grupo_etario.png ........... Relaciones, apartado 1
fig13_departamento_periodo.png .......... Relaciones, apartado 3
fig14_estacionalidad.png ................ Relaciones, apartado 5
fig15_correlaciones.png .................. Relaciones, apartado 6
fig16_codigo_streamlit.png ............... código (datos.py y limpieza.py)
Pendientes de las fases 3 y 4: panel y tablas de Neon, modelo y tablero de
Power BI.