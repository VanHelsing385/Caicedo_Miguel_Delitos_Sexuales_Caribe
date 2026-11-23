
from pathlib import Path
import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================

CSV_PATH = Path("00_datos_originales/delitos_sexuales_nacional.csv")

# Códigos DANE de los departamentos del Caribe.
CODIGOS_CARIBE = {
    "08",  # Atlántico
    "13",  # Bolívar
    "20",  # Cesar
    "23",  # Córdoba
    "44",  # La Guajira
    "47",  # Magdalena
    "70",  # Sucre
    "88",  # San Andrés
}


# =====================================================
# LECTURA
# =====================================================

if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo: {CSV_PATH.resolve()}"
    )

df = pd.read_csv(
    CSV_PATH,
    dtype=str,
    encoding="utf-8-sig",
    keep_default_na=False
)

# Normalizar encabezados sin modificar el archivo original.
# Ejemplo: "CODIGO DANE" -> "codigo_dane"
import re
import unicodedata

def normalizar_columna(nombre):
    nombre = nombre.strip().strip('"')
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = "".join(
        c for c in nombre
        if not unicodedata.combining(c)
    )
    nombre = re.sub(r"[^a-zA-Z0-9]+", "_", nombre)
    return nombre.strip("_").lower()

df.columns = [normalizar_columna(c) for c in df.columns]

print("Columnas reconocidas:")
print(df.columns.tolist())

# Comprobar columnas necesarias.
columnas = [
    "departamento",
    "municipio",
    "codigo_dane"
]

faltantes = [c for c in columnas if c not in df.columns]

if faltantes:
    raise ValueError(
        f"Faltan columnas en el CSV: {faltantes}. "
        f"Columnas encontradas: {df.columns.tolist()}"
    )

print("\n" + "=" * 65)
print("VALIDACIÓN DE CÓDIGOS DANE - REGIÓN CARIBE")
print("=" * 65)


# =====================================================
# PREPARACIÓN
# =====================================================

df["codigo_original"] = df["codigo_dane"].str.strip()
df["municipio_original"] = df["municipio"].str.strip()

# No rellenamos ceros ni corregimos códigos.
# Queremos detectar problemas, no ocultarlos.

df["codigo_valido"] = (
    df["codigo_original"].str.fullmatch(r"\d{8}")
)

df["prefijo_municipio"] = (
    df["codigo_original"].str[:5]
)

df["sufijo_centro"] = (
    df["codigo_original"].str[5:]
)

df["es_capital_ct"] = (
    df["municipio_original"].str.contains(
        r"\(CT\)", regex=True, case=False
    )
)

# =====================================================
# FILTRO CARIBE
# =====================================================

df_caribe = df[
    df["codigo_original"].str[:2].isin(CODIGOS_CARIBE)
].copy()

print(f"\n1. REGISTROS")
print(f"Registros nacionales: {len(df):,}")
print(f"Registros Caribe:     {len(df_caribe):,}")

# =====================================================
# VALIDACIÓN DE LONGITUD Y FORMATO
# =====================================================

validos = df_caribe["codigo_valido"]

print("\n2. VALIDACIÓN DEL CÓDIGO ORIGINAL")
print(f"Códigos válidos (8 dígitos): {validos.sum():,}")
print(f"Códigos inválidos:           {(~validos).sum():,}")

if (~validos).any():
    print("\nEjemplos de códigos inválidos:")
    print(
        df_caribe.loc[
            ~validos,
            ["departamento", "municipio_original",
             "codigo_original"]
        ].head(15).to_string(index=False)
    )

# Continuamos únicamente con códigos válidos.
d = df_caribe[validos].copy()

# =====================================================
# COMPARACIÓN 464 VS 1415
# =====================================================

d["sufijo_distinto_000"] = (
    d["sufijo_centro"] != "000"
)

d["capital_no_000"] = (
    d["es_capital_ct"] & d["sufijo_distinto_000"]
)

d["no_capital_no_000"] = (
    ~d["es_capital_ct"] & d["sufijo_distinto_000"]
)

print("\n3. COMPARACIÓN DE LOS REGISTROS")

print(
    "Total con sufijo distinto de 000:",
    f"{d['sufijo_distinto_000'].sum():,}"
)

print(
    "Registros de capital (CT) con sufijo distinto de 000:",
    f"{d['capital_no_000'].sum():,}"
)

print(
    "Registros de otros municipios con sufijo distinto de 000:",
    f"{d['no_capital_no_000'].sum():,}"
)

print(
    "Registros con sufijo 000:",
    f"{(d['sufijo_centro'] == '000').sum():,}"
)

# =====================================================
# CÓDIGOS Y MUNICIPIOS DISTINTOS
# =====================================================

no_000 = d[d["sufijo_distinto_000"]]

print("\n4. CÓDIGOS DISTINTOS")

print(
    "Códigos completos distintos:",
    f"{no_000['codigo_original'].nunique():,}"
)

print(
    "Prefijos municipales distintos (todos los registros):",
    f"{d['prefijo_municipio'].nunique():,}"
)

print(
    "Prefijos municipales con sufijo distinto de 000:",
    f"{no_000['prefijo_municipio'].nunique():,}"
)

print(
    "Sufijos distintos:",
    f"{no_000['sufijo_centro'].nunique():,}"
)

print(
    "Códigos distintos en capitales:",
    f"{d.loc[d['capital_no_000'], 'codigo_original'].nunique():,}"
)

# =====================================================
# DETALLE POR DEPARTAMENTO
# =====================================================

print("\n5. DETALLE POR DEPARTAMENTO")

resumen = (
    d.groupby("departamento", dropna=False)
    .agg(
        registros=("codigo_original", "size"),
        registros_no_000=("sufijo_distinto_000", "sum"),
        registros_capital_no_000=("capital_no_000", "sum"),
        municipios_no_000=("prefijo_municipio",
                           lambda x: x[
                               d.loc[x.index, "sufijo_distinto_000"]
                           ].nunique())
    )
    .sort_values("registros_no_000", ascending=False)
)

print(resumen.to_string())

# =====================================================
# RECONSTRUCCIÓN DEL CÓDIGO DANE
# =====================================================

d["codigo_reconstruido"] = (
    d["prefijo_municipio"] + d["sufijo_centro"]
)

d["reconstruccion_correcta"] = (
    d["codigo_reconstruido"] == d["codigo_original"]
)

errores = (~d["reconstruccion_correcta"]).sum()

print("\n6. RECONSTRUCCIÓN DEL CÓDIGO DANE")
print(f"Reconstrucciones correctas: {len(d) - errores:,}")
print(f"Reconstrucciones incorrectas: {errores:,}")

# =====================================================
# COMPROBACIÓN DE CAPITAL
# =====================================================

print("\n7. CAPITALIDADES")

print(
    "Registros marcados con (CT):",
    f"{d['es_capital_ct'].sum():,}"
)

print(
    "Capitales distintas por departamento:",
    f"{d.loc[d['es_capital_ct'], 'prefijo_municipio'].nunique():,}"
)

print("\nCapitales con sus códigos:")

capitales = (
    d[d["es_capital_ct"]]
    .groupby(
        ["departamento", "municipio_original",
         "prefijo_municipio", "sufijo_centro"],
        dropna=False
    )
    .size()
    .reset_index(name="registros")
)

print(capitales.to_string(index=False))

# =====================================================
# COMPROBACIÓN DE LOS 464 REGISTROS
# =====================================================

print("\n8. COMPROBACIÓN FINAL")

print(
    "¿Coincide con los 464 registros de capitales de la bitácora?",
    d["capital_no_000"].sum() == 464
)

print(
    "¿Coincide con los 1.415 registros con sufijo distinto de 000 de la verificación del modelo?",
    d["sufijo_distinto_000"].sum() == 1415
)

print("\n" + "=" * 65)
print("VALIDACIÓN TERMINADA")
print("=" * 65)
