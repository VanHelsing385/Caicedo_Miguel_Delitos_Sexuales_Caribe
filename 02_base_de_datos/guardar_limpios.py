"""Guarda en PostgreSQL (Neon) los datos limpios del Caribe y verifica la carga.

Fases (cada una se puede repetir sin rehacer las anteriores):
  1. PREPARAR  Lee el CSV original, aplica la limpieza del EDA y escribe
               salida/delitos_limpios.csv con un archivo de control. Si ya
               existen y coinciden, esta fase se omite (no se vuelve a limpiar
               aunque falle la conexion). Se fuerza con --regenerar.
  2. CARGAR    Se conecta a Neon con DATABASE_URL (archivo .env), crea las
               tablas si no existen, carga los catalogos y los hechos por
               lotes. Solo inserta lo que falta, asi que se puede reanudar.
  3. VERIFICAR Compara los conteos de la base con las cifras validadas en el
               EDA. Solo declara la carga verificada si todo coincide.

Uso (desde la raiz del proyecto, con el entorno activo):
    python 02_base_de_datos/guardar_limpios.py                  # todo
    python 02_base_de_datos/guardar_limpios.py --solo-preparar  # sin conexion
    python 02_base_de_datos/guardar_limpios.py --solo-verificar # solo conteos
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "01_eda"))

SALIDA = AQUI / "salida"
CSV_SALIDA = SALIDA / "delitos_limpios.csv"
CONTROL = SALIDA / "control.json"
SQL_TABLAS = AQUI / "01_crear_tablas.sql"

# Cifras validadas en el EDA (si algo no coincide, no se da la carga por buena)
ESPERADO = {"filas": 67122, "departamentos": 8, "municipios": 197,
            "tipos_delito": 22, "generos": 4, "grupos_etarios": 4, "medios": 11,
            "genero_sin_dato": 370, "genero_no_reporta": 113,
            "grupo_sin_dato": 68, "repetidos": 4688, "en_capitales": 32131,
            "menor_14": 38973, "centro_poblado": 1415, "suma_cantidad": 67122}
POR_DEPARTAMENTO = {"Atlántico": 16664, "Bolívar": 13670, "Magdalena": 8725,
                    "Cesar": 8613, "Córdoba": 8372, "Sucre": 6413,
                    "La Guajira": 3938, "San Andrés y Providencia": 727}
EDADES = {"MENORES": (0, 12), "ADOLESCENTES": (13, 17),
          "ADULTOS": (18, None), "SIN DATO": (None, None)}
PATRON_ARTICULO = re.compile(r"ART[ÍI]CULO\s+(\d+)(?:\s*([A-Z]))?\s*\.", re.IGNORECASE)

VERSION_PREPARACION = "1"
ARCHIVOS_PREPARACION = (
    RAIZ / "01_eda" / "datos.py",
    RAIZ / "01_eda" / "limpieza.py",
)


def huella_preparacion() -> dict:
    return {
        ruta.name: sha256(ruta)
        for ruta in ARCHIVOS_PREPARACION
    }


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


# ====================================================================== fase 1
def preparar(regenerar: bool) -> pd.DataFrame:
    """Devuelve los datos listos para cargar, leyéndolos del archivo local si
    ya existe y coincide con el CSV original."""
    from datos import ARCHIVO   # CSV original

    if CSV_SALIDA.exists() and CONTROL.exists() and not regenerar:
        ctl = json.loads(CONTROL.read_text(encoding="utf-8"))
        if (ctl.get("sha256_salida") == sha256(CSV_SALIDA)
                and ctl.get("sha256_origen") == sha256(ARCHIVO)
                and ctl.get("version_preparacion") == VERSION_PREPARACION
                and ctl.get("huella_preparacion") == huella_preparacion()):
            print(f"[1/3] PREPARAR: ya existe {CSV_SALIDA.name} "
                  f"({ctl['filas']:,} filas, generado {ctl['generado']}); "
                  "se omite la limpieza.".replace(",", "."))
            return pd.read_csv(CSV_SALIDA, dtype=str, encoding="utf-8", keep_default_na=False)
        print("[1/3] PREPARAR: el archivo local no coincide con el CSV original; "
              "se regenera.")

    print("[1/3] PREPARAR: leyendo el CSV y aplicando la limpieza (puede tardar)...")
    from datos import cargar_nacional, filtrar_caribe
    from limpieza import preparar as limpiar

    d = limpiar(filtrar_caribe(cargar_nacional()))
    articulo = {t: (lambda m: (m.group(1) + (m.group(2) or "")) if m else None)(
        PATRON_ARTICULO.search(t)) for t in d["delito"].unique()}
    sin_articulo = [t for t, a in articulo.items() if a is None]
    if sin_articulo:
        raise SystemExit(f"Delitos sin número de artículo reconocido: {sin_articulo}")

    est = pd.DataFrame({
        "fila_origen": d["id"],
        "fecha_hecho": d["fecha_hecho"].dt.strftime("%Y-%m-%d"),
        "cod_depto": d["codigo_dane"].str[:2],
        "departamento": d["departamento"],
        "cod_municipio": d["codigo_dane"].str[:5],
        "municipio": d["municipio"],
        "es_capital": d["es_capital"],
        "centro_poblado": d["codigo_dane"].str[5:],
        "articulo": d["delito"].map(articulo),
        "tipo_delito": d["delito"],
        "es_menor_14": d["delito"].str.upper().str.contains("MENOR DE 14"),
        "genero": d["genero"],
        "grupo_etario": d["grupo_etario"],
        "medio": d["armas_medios"],
        "cantidad": d["cantidad"],
        "es_repetido": d["es_repetido"]})

    # Coherencia antes de escribir nada
    errores = []
    if len(est) != ESPERADO["filas"]:
        errores.append(f"filas: {len(est)} (esperado {ESPERADO['filas']})")
    m = est.groupby("cod_municipio").agg(n=("municipio", "nunique"),
                                         cap=("es_capital", "nunique"),
                                         dep=("cod_depto", "nunique"))
    if (m[["n", "cap", "dep"]] > 1).any().any():
        errores.append("algún municipio tiene más de un nombre, marca o departamento")
    if (est["cod_municipio"].str[:2] != est["cod_depto"]).any():
        errores.append("el prefijo del municipio no coincide con su departamento")
    if est.isna().any().any():
        errores.append("hay valores nulos en las columnas de carga")
    if errores:
        raise SystemExit("No se escribe el archivo de salida: " + "; ".join(errores))

    SALIDA.mkdir(exist_ok=True)
    est.to_csv(CSV_SALIDA, index=False, encoding="utf-8")
    CONTROL.write_text(json.dumps({
        "filas": len(est),
        "sha256_salida": sha256(CSV_SALIDA),
        "sha256_origen": sha256(ARCHIVO),
        "version_preparacion": VERSION_PREPARACION,
        "huella_preparacion": huella_preparacion(),
        "generado": datetime.now().strftime("%d/%m/%Y %H:%M")
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      escrito {CSV_SALIDA.name}: {len(est):,} filas".replace(",", "."))
    return pd.read_csv(CSV_SALIDA, dtype=str, encoding="utf-8", keep_default_na=False)


# ====================================================================== fase 2
def url_neon(permitir_local: bool) -> str:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")           # solo lee: nunca modifica el .env
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("Falta DATABASE_URL en el archivo .env de la raíz del "
                         "proyecto (la cadena de conexión de Neon).")
    host = urlparse(url).hostname or ""
    if host in ("localhost", "127.0.0.1", "::1") and not permitir_local:
        raise SystemExit("DATABASE_URL apunta a un servidor local (localhost). "
                         "El entregable es Neon: pon ahí la cadena de Neon. "
                         "Para una prueba local usa --permitir-local.")
    return url


def conectar(url: str):
    import psycopg
    for intento in range(1, 6):
        try:
            return psycopg.connect(url, connect_timeout=30)
        except psycopg.OperationalError as e:
            espera = 5 * intento
            motivo = str(e).strip().splitlines()[0][:120] if str(e).strip() else "sin detalle"
            print(f"      intento {intento}/5 sin conexión ({motivo}); "
                  f"reintento en {espera} s (Neon puede estar despertando)")
            time.sleep(espera)
    raise SystemExit("No se pudo conectar. Los datos limpios siguen guardados en "
                     "salida/: al volver a ejecutar no se limpiará de nuevo.")


def crear_tablas(conn):
    sql = SQL_TABLAS.read_text(encoding="utf-8")
    sentencias = [s.strip() for s in re.split(r";[ \t]*\n", sql) if s.strip()]
    with conn.cursor() as cur:
        for s in sentencias:
            cur.execute(s)
    conn.commit()
    print(f"      tablas verificadas/creadas ({len(sentencias)} sentencias)")


def mapa(cur, sql: str) -> dict:
    cur.execute(sql)
    return {k: v for k, v in cur.fetchall()}



def cargar_catalogos(conn, est: pd.DataFrame) -> dict:
    deptos = (
        est[["cod_depto", "departamento"]]
        .drop_duplicates()
        .sort_values("cod_depto")
    )
    mpios = (
        est[["cod_municipio", "cod_depto", "municipio", "es_capital"]]
        .drop_duplicates()
        .sort_values("cod_municipio")
    )
    delitos = (
        est[["articulo", "tipo_delito", "es_menor_14"]]
        .drop_duplicates()
        .sort_values("tipo_delito")
    )

    if not mpios["cod_municipio"].is_unique:
        raise SystemExit("Un código de municipio aparece con datos distintos.")

    grupos = sorted(est["grupo_etario"].unique())
    desconocidos = [g for g in grupos if g not in EDADES]
    if desconocidos:
        raise SystemExit(
            f"Grupos etarios sin rango definido: {desconocidos}"
        )

    esperados = {
        "departamentos": {
            (str(cod), nombre)
            for cod, nombre in deptos.itertuples(index=False, name=None)
        },
        "municipios": {
            (str(cod), str(dep), nombre, cap == "True")
            for cod, dep, nombre, cap
            in mpios.itertuples(index=False, name=None)
        },
        "tipos_delito": {
            (art, descripcion, menor == "True")
            for art, descripcion, menor
            in delitos.itertuples(index=False, name=None)
        },
        "generos": {
            (g,) for g in est["genero"].unique()
        },
        "grupos_etarios": {
            (g, *EDADES[g]) for g in grupos
        },
        "medios": {
            (m,) for m in est["medio"].unique()
        }
    }

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO departamentos (cod_dane, nombre) "
            "SELECT * FROM unnest(%s::char(2)[], %s::text[]) "
            "ON CONFLICT (cod_dane) DO NOTHING",
            (deptos["cod_depto"].tolist(),
             deptos["departamento"].tolist())
        )

        cur.execute(
            "INSERT INTO municipios "
            "(departamento_id, cod_dane, nombre, es_capital) "
            "SELECT d.id, m.cod, m.nombre, m.cap "
            "FROM unnest(%s::char(5)[], %s::char(2)[], "
            "%s::text[], %s::boolean[]) "
            "AS m(cod, dep, nombre, cap) "
            "JOIN departamentos d ON d.cod_dane = m.dep "
            "ON CONFLICT (cod_dane) DO NOTHING",
            (
                mpios["cod_municipio"].tolist(),
                mpios["cod_depto"].tolist(),
                mpios["municipio"].tolist(),
                (mpios["es_capital"] == "True").tolist()
            )
        )

        cur.executemany(
            "INSERT INTO tipos_delito "
            "(articulo, descripcion, es_menor_14) "
            "VALUES (%s, %s, %s) "
            "ON CONFLICT (descripcion) DO NOTHING",
            [
                (a, t, m == "True")
                for a, t, m in delitos.itertuples(index=False)
            ]
        )

        cur.executemany(
            "INSERT INTO generos (nombre) "
            "VALUES (%s) ON CONFLICT (nombre) DO NOTHING",
            [(g,) for g in sorted(est["genero"].unique())]
        )

        cur.executemany(
            "INSERT INTO grupos_etarios (nombre, edad_min, edad_max) "
            "VALUES (%s, %s, %s) "
            "ON CONFLICT (nombre) DO NOTHING",
            [(g, *EDADES[g]) for g in grupos]
        )

        cur.executemany(
            "INSERT INTO medios (nombre) "
            "VALUES (%s) ON CONFLICT (nombre) DO NOTHING",
            [(m,) for m in sorted(est["medio"].unique())]
        )

        # Leer los catálogos existentes para compararlos con el CSV.
        cur.execute(
            "SELECT RTRIM(cod_dane), nombre FROM departamentos"
        )
        reales_deptos = set(cur.fetchall())

        cur.execute(
            "SELECT RTRIM(m.cod_dane), RTRIM(d.cod_dane), "
            "m.nombre, m.es_capital "
            "FROM municipios m "
            "JOIN departamentos d ON d.id = m.departamento_id"
        )
        reales_mpios = set(cur.fetchall())

        cur.execute(
            "SELECT articulo, descripcion, es_menor_14 "
            "FROM tipos_delito"
        )
        reales_delitos = set(cur.fetchall())

        cur.execute("SELECT nombre FROM generos")
        reales_generos = set(cur.fetchall())

        cur.execute(
            "SELECT nombre, edad_min, edad_max FROM grupos_etarios"
        )
        reales_grupos = set(cur.fetchall())

        cur.execute("SELECT nombre FROM medios")
        reales_medios = set(cur.fetchall())

        reales = {
            "departamentos": reales_deptos,
            "municipios": reales_mpios,
            "tipos_delito": reales_delitos,
            "generos": reales_generos,
            "grupos_etarios": reales_grupos,
            "medios": reales_medios
        }

        errores = []
        for tabla, esperado in esperados.items():
            actual = reales[tabla]
            faltantes = esperado - actual
            adicionales = actual - esperado

            if faltantes or adicionales:
                errores.append(
                    f"{tabla}: {len(faltantes)} faltantes, "
                    f"{len(adicionales)} adicionales o diferentes"
                )

        if errores:
            raise SystemExit(
                "Catálogos inconsistentes. No se cargarán los hechos:\n- "
                + "\n- ".join(errores)
            )

        ids = {
            "municipio": mapa(
                cur, "SELECT RTRIM(cod_dane), id FROM municipios"
            ),
            "tipo": mapa(
                cur, "SELECT descripcion, id FROM tipos_delito"
            ),
            "genero": mapa(
                cur, "SELECT nombre, id FROM generos"
            ),
            "grupo": mapa(
                cur, "SELECT nombre, id FROM grupos_etarios"
            ),
            "medio": mapa(
                cur, "SELECT nombre, id FROM medios"
            )
        }

    conn.commit()

    print(
        "      catálogos verificados: "
        + ", ".join(f"{k} {len(v)}" for k, v in ids.items())
    )

    return ids


COLS_LOTE = ("fila_origen, fecha_hecho, municipio_id, centro_poblado, tipo_delito_id, "
             "genero_id, grupo_etario_id, medio_id, cantidad, es_repetido")



def cargar_hechos(conn, est: pd.DataFrame, ids: dict, lote: int):
    est = est.copy()
    est["fila_origen"] = est["fila_origen"].astype(int)

    if est["fila_origen"].duplicated().any():
        raise SystemExit("El CSV contiene valores fila_origen duplicados.")

    est["municipio_id"] = est["cod_municipio"].map(ids["municipio"])
    est["tipo_delito_id"] = est["tipo_delito"].map(ids["tipo"])
    est["genero_id"] = est["genero"].map(ids["genero"])
    est["grupo_etario_id"] = est["grupo_etario"].map(ids["grupo"])
    est["medio_id"] = est["medio"].map(ids["medio"])

    ids_cols = [
        "municipio_id", "tipo_delito_id", "genero_id",
        "grupo_etario_id", "medio_id"
    ]

    if est[ids_cols].isna().any().any():
        raise SystemExit("Hay registros sin su catálogo en la base; no se carga nada.")

    filas = list(zip(
        est["fila_origen"].tolist(),
        pd.to_datetime(est["fecha_hecho"]).dt.date.tolist(),
        est["municipio_id"].astype(int).tolist(),
        est["centro_poblado"].tolist(),
        est["tipo_delito_id"].astype(int).tolist(),
        est["genero_id"].astype(int).tolist(),
        est["grupo_etario_id"].astype(int).tolist(),
        est["medio_id"].astype(int).tolist(),
        est["cantidad"].astype(int).tolist(),
        (est["es_repetido"] == "True").tolist()
    ))

    with conn.cursor() as cur:
        # Tabla temporal que conserva los datos durante los COMMIT.
        cur.execute(
            "CREATE TEMP TABLE tmp_esperados ("
            "fila_origen INTEGER PRIMARY KEY, "
            "fecha_hecho DATE NOT NULL, "
            "municipio_id SMALLINT NOT NULL, "
            "centro_poblado CHAR(3) NOT NULL, "
            "tipo_delito_id SMALLINT NOT NULL, "
            "genero_id SMALLINT NOT NULL, "
            "grupo_etario_id SMALLINT NOT NULL, "
            "medio_id SMALLINT NOT NULL, "
            "cantidad SMALLINT NOT NULL, "
            "es_repetido BOOLEAN NOT NULL"
            ") ON COMMIT PRESERVE ROWS"
        )

        # Copiar todos los registros esperados desde el CSV.
        with cur.copy(
            f"COPY tmp_esperados ({COLS_LOTE}) FROM STDIN"
        ) as copia:
            for fila in filas:
                copia.write_row(fila)

        # Comprobar registros existentes con el mismo origen
        # pero con algún dato diferente.
        cur.execute(
            "SELECT COUNT(*) "
            "FROM tmp_esperados t "
            "JOIN delitos_limpios f USING (fila_origen) "
            "WHERE ROW("
            "f.fecha_hecho, f.municipio_id, f.centro_poblado, "
            "f.tipo_delito_id, f.genero_id, f.grupo_etario_id, "
            "f.medio_id, f.cantidad, f.es_repetido"
            ") IS DISTINCT FROM ROW("
            "t.fecha_hecho, t.municipio_id, t.centro_poblado, "
            "t.tipo_delito_id, t.genero_id, t.grupo_etario_id, "
            "t.medio_id, t.cantidad, t.es_repetido"
            ")"
        )
        diferentes = int(cur.fetchone()[0])

        # Detectar registros en la base que no existen en el CSV.
        cur.execute(
            "SELECT COUNT(*) "
            "FROM delitos_limpios f "
            "LEFT JOIN tmp_esperados t USING (fila_origen) "
            "WHERE t.fila_origen IS NULL"
        )
        adicionales = int(cur.fetchone()[0])

        if diferentes or adicionales:
            raise SystemExit(
                "No se puede continuar: los datos existentes no "
                "coinciden con el CSV.\n"
                f"- Registros con datos diferentes: {diferentes:,}\n"
                f"- Registros adicionales en la base: {adicionales:,}"
                .replace(",", ".")
            )

        cur.execute("SELECT COUNT(*) FROM delitos_limpios")
        existentes = int(cur.fetchone()[0])

        pendientes = len(filas) - existentes

        print(
            f"      en la base: {existentes:,} · "
            f"pendientes: {pendientes:,}".replace(",", ".")
        )

    conn.commit()

    if pendientes == 0:
        print("      todas las filas ya estaban cargadas y coinciden con el CSV.")
        return

    n_lotes = -(-pendientes // lote)
    insertadas = 0

    for i in range(n_lotes):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO delitos_limpios ({COLS_LOTE}) "
                f"SELECT {COLS_LOTE} "
                "FROM tmp_esperados t "
                "WHERE NOT EXISTS ("
                "SELECT 1 FROM delitos_limpios f "
                "WHERE f.fila_origen = t.fila_origen"
                ") "
                "ORDER BY fila_origen "
                "LIMIT %s "
                "ON CONFLICT (fila_origen) DO NOTHING",
                (lote,)
            )
            nuevas = cur.rowcount

        if nuevas == 0:
            raise SystemExit(
                "La carga se detuvo: no se insertaron filas "
                "aunque todavía había registros pendientes."
            )

        conn.commit()
        insertadas += nuevas

        print(
            f"      lote {i + 1}/{n_lotes}: "
            f"{nuevas:,} filas insertadas "
            f"(acumulado {insertadas:,})".replace(",", ".")
        )

    print("      carga de registros finalizada.")



def comparar_hechos(conn, est: pd.DataFrame, ids: dict) -> bool:
    print("[COMPARACIÓN] Contrastando los registros contra el CSV...")

    datos = est.copy()
    datos["fila_origen"] = datos["fila_origen"].astype(int)

    datos["municipio_id"] = datos["cod_municipio"].map(ids["municipio"])
    datos["tipo_delito_id"] = datos["tipo_delito"].map(ids["tipo"])
    datos["genero_id"] = datos["genero"].map(ids["genero"])
    datos["grupo_etario_id"] = datos["grupo_etario"].map(ids["grupo"])
    datos["medio_id"] = datos["medio"].map(ids["medio"])

    columnas_ids = [
        "municipio_id", "tipo_delito_id", "genero_id",
        "grupo_etario_id", "medio_id"
    ]

    if datos[columnas_ids].isna().any().any():
        print("      ERROR: faltan valores en los catálogos.")
        return False

    filas = list(zip(
        datos["fila_origen"].tolist(),
        pd.to_datetime(datos["fecha_hecho"]).dt.date.tolist(),
        datos["municipio_id"].astype(int).tolist(),
        datos["centro_poblado"].tolist(),
        datos["tipo_delito_id"].astype(int).tolist(),
        datos["genero_id"].astype(int).tolist(),
        datos["grupo_etario_id"].astype(int).tolist(),
        datos["medio_id"].astype(int).tolist(),
        datos["cantidad"].astype(int).tolist(),
        (datos["es_repetido"] == "True").tolist()
    ))

    with conn.cursor() as cur:
        cur.execute(
            "CREATE TEMP TABLE tmp_comparacion ("
            "fila_origen INTEGER, fecha_hecho DATE, "
            "municipio_id SMALLINT, centro_poblado CHAR(3), "
            "tipo_delito_id SMALLINT, genero_id SMALLINT, "
            "grupo_etario_id SMALLINT, medio_id SMALLINT, "
            "cantidad SMALLINT, es_repetido BOOLEAN"
            ") ON COMMIT PRESERVE ROWS"
        )

        with cur.copy(
            f"COPY tmp_comparacion ({COLS_LOTE}) FROM STDIN"
        ) as copia:
            for fila in filas:
                copia.write_row(fila)

        cur.execute(
            "SELECT COUNT(*) FROM tmp_comparacion t "
            "LEFT JOIN delitos_limpios f USING (fila_origen) "
            "WHERE f.fila_origen IS NULL"
        )
        faltantes = int(cur.fetchone()[0])

        cur.execute(
            "SELECT COUNT(*) FROM delitos_limpios f "
            "LEFT JOIN tmp_comparacion t USING (fila_origen) "
            "WHERE t.fila_origen IS NULL"
        )
        adicionales = int(cur.fetchone()[0])

        cur.execute(
            "SELECT COUNT(*) "
            "FROM tmp_comparacion t "
            "JOIN delitos_limpios f USING (fila_origen) "
            "WHERE ROW("
            "f.fecha_hecho, f.municipio_id, f.centro_poblado, "
            "f.tipo_delito_id, f.genero_id, f.grupo_etario_id, "
            "f.medio_id, f.cantidad, f.es_repetido"
            ") IS DISTINCT FROM ROW("
            "t.fecha_hecho, t.municipio_id, t.centro_poblado, "
            "t.tipo_delito_id, t.genero_id, t.grupo_etario_id, "
            "t.medio_id, t.cantidad, t.es_repetido"
            ")"
        )
        diferentes = int(cur.fetchone()[0])

    conn.commit()

    resultados = [
        ("registros faltantes", faltantes),
        ("registros adicionales", adicionales),
        ("registros con datos diferentes", diferentes)
    ]

    ok = True
    for nombre, cantidad in resultados:
        bien = cantidad == 0
        ok &= bien
        print(
            f"      {nombre:<34}{cantidad:>8,}  "
            f"{'OK' if bien else 'REVISAR'}".replace(",", ".")
        )

    if ok:
        print("      Los registros coinciden exactamente con el CSV.")

    return ok


def obtener_ids_catalogos(conn) -> dict:
    """Obtiene los identificadores existentes sin modificar la base."""
    with conn.cursor() as cur:
        return {
            "municipio": mapa(
                cur, "SELECT RTRIM(cod_dane), id FROM municipios"
            ),
            "tipo": mapa(
                cur, "SELECT descripcion, id FROM tipos_delito"
            ),
            "genero": mapa(
                cur, "SELECT nombre, id FROM generos"
            ),
            "grupo": mapa(
                cur, "SELECT nombre, id FROM grupos_etarios"
            ),
            "medio": mapa(
                cur, "SELECT nombre, id FROM medios"
            )
        }


# ====================================================================== fase 3
CONSULTAS = [
    ("filas", "SELECT COUNT(*) FROM delitos_limpios"),
    ("filas con fila_origen distinta", "SELECT COUNT(DISTINCT fila_origen) FROM delitos_limpios"),
    ("departamentos", "SELECT COUNT(*) FROM departamentos"),
    ("municipios", "SELECT COUNT(*) FROM municipios"),
    ("tipos_delito", "SELECT COUNT(*) FROM tipos_delito"),
    ("generos", "SELECT COUNT(*) FROM generos"),
    ("grupos_etarios", "SELECT COUNT(*) FROM grupos_etarios"),
    ("medios", "SELECT COUNT(*) FROM medios"),
    ("genero_sin_dato", "SELECT COUNT(*) FROM delitos_limpios f JOIN generos g ON g.id = f.genero_id WHERE g.nombre = 'SIN DATO'"),
    ("genero_no_reporta", "SELECT COUNT(*) FROM delitos_limpios f JOIN generos g ON g.id = f.genero_id WHERE g.nombre = 'NO REPORTA'"),
    ("grupo_sin_dato", "SELECT COUNT(*) FROM delitos_limpios f JOIN grupos_etarios g ON g.id = f.grupo_etario_id WHERE g.nombre = 'SIN DATO'"),
    ("repetidos", "SELECT COUNT(*) FROM delitos_limpios WHERE es_repetido"),
    ("en_capitales", "SELECT COUNT(*) FROM delitos_limpios f JOIN municipios m ON m.id = f.municipio_id WHERE m.es_capital"),
    ("menor_14", "SELECT COUNT(*) FROM delitos_limpios f JOIN tipos_delito t ON t.id = f.tipo_delito_id WHERE t.es_menor_14"),
    ("centro_poblado", "SELECT COUNT(*) FROM delitos_limpios WHERE centro_poblado <> '000'"),
    ("suma_cantidad", "SELECT COALESCE(SUM(cantidad), 0) FROM delitos_limpios"),
]


def verificar(conn, est: pd.DataFrame, ids: dict) -> bool:
    print("[3/3] VERIFICAR: conteos y registros contra las cifras validadas")
    ok = True
    with conn.cursor() as cur:
        for nombre, sql in CONSULTAS:
            cur.execute(sql)
            obtenido = int(cur.fetchone()[0])
            clave = "filas" if nombre == "filas con fila_origen distinta" else nombre
            esperado = ESPERADO[clave]
            bien = obtenido == esperado
            ok &= bien
            print(f"      {nombre:<34}{obtenido:>8,}  "
                  f"{'OK' if bien else f'<-- ESPERADO {esperado:,}'}".replace(",", "."))
        cur.execute("SELECT d.nombre, COUNT(*) FROM delitos_limpios f "
                    "JOIN municipios m ON m.id = f.municipio_id "
                    "JOIN departamentos d ON d.id = m.departamento_id GROUP BY d.nombre")
        por_dep = {n: c for n, c in cur.fetchall()}
        for nombre, esperado in POR_DEPARTAMENTO.items():
            obtenido = por_dep.get(nombre, 0)
            bien = obtenido == esperado
            ok &= bien
            print(f"      registros en {nombre:<22}{obtenido:>8,}  "
                  f"{'OK' if bien else f'<-- ESPERADO {esperado:,}'}".replace(",", "."))
        cur.execute("SELECT COUNT(*) FROM municipios m JOIN departamentos d "
                    "ON d.id = m.departamento_id WHERE LEFT(m.cod_dane, 2) <> d.cod_dane")
        incoherentes = int(cur.fetchone()[0])
        ok &= incoherentes == 0
        print(f"      {'municipios fuera de su departamento':<34}{incoherentes:>8}  "
              f"{'OK' if incoherentes == 0 else '<-- ESPERADO 0'}")
        cur.execute("SELECT MIN(fecha_hecho)::text, MAX(fecha_hecho)::text FROM delitos_limpios")
        fmin, fmax = cur.fetchone()
        bien = (fmin, fmax) == ("2010-01-01", "2026-07-31")
        ok &= bien
        print(f"      {'rango de fechas':<34}{fmin} a {fmax}  "
              f"{'OK' if bien else '<-- ESPERADO 2010-01-01 a 2026-07-31'}")
        ok &= comparar_hechos(conn, est, ids)
    if ok:
        print("\nVERIFICACIÓN COMPLETA: todas las comprobaciones coinciden.")
    else:
        print("\nNO se da la carga por verificada: hay diferencias (revisar arriba).")
    return ok


# ====================================================================== principal
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regenerar", action="store_true",
                    help="vuelve a limpiar aunque exista salida/ coincidente")
    ap.add_argument("--solo-preparar", action="store_true",
                    help="solo la fase 1 (no se conecta a ninguna base)")
    ap.add_argument("--solo-verificar", action="store_true",
                    help="solo la fase 3 sobre lo que ya hay en la base")
    ap.add_argument("--lote", type=int, default=5000, help="filas por lote (5000)")
    ap.add_argument("--permitir-local", action="store_true",
                    help="acepta una DATABASE_URL local (solo para pruebas)")
    a = ap.parse_args()

    if a.lote <= 0:
        raise SystemExit("El tamaño del lote debe ser un entero mayor que cero.")

    if a.solo_verificar:
        est = preparar(a.regenerar)
        import psycopg  # noqa: F401
        with conectar(url_neon(a.permitir_local)) as conn:
            ids = obtener_ids_catalogos(conn)
            sys.exit(0 if verificar(conn, est, ids) else 1)

    est = preparar(a.regenerar)
    if a.solo_preparar:
        print("Fase 1 lista. No se tocó ninguna base de datos.")
        return

    import psycopg
    url = url_neon(a.permitir_local)
    print("[2/3] CARGAR: conectando a la base de datos (cadena oculta)...")
    for intento in range(1, 4):
        try:
            with conectar(url) as conn:
                crear_tablas(conn)
                ids = cargar_catalogos(conn, est)
                cargar_hechos(conn, est, ids, a.lote)
                ok = verificar(conn, est, ids)
            sys.exit(0 if ok else 1)
        except psycopg.OperationalError as e:
            print(f"      conexión interrumpida ({str(e).strip().splitlines()[0][:100]}); "
                  f"reanudando ({intento}/3). No se limpia de nuevo.")
            time.sleep(10)
    raise SystemExit("No se pudo completar. Vuelve a ejecutar: continuará donde quedó.")


if __name__ == "__main__":
    main()