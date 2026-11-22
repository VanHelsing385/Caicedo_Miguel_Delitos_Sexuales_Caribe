import pandas as pd

# Criterio de fila idéntica, calculado SOBRE LOS VALORES ORIGINALES
COLS_REPETIDO = ["departamento_original", "municipio", "codigo_dane",
                 "armas_medios", "fecha_hecho", "genero", "grupo_etario",
                 "cantidad", "delito"]


def preparar(df_original: pd.DataFrame) -> pd.DataFrame:
    """Limpia reemplazando valores. No elimina ningún registro."""
    df = df_original.copy()

    # 1. Banderas que se calculan antes de modificar nada
    df["es_repetido"] = df.duplicated(subset=COLS_REPETIDO, keep="first")
    df["es_capital"] = df["municipio"].str.contains(r"\(CT\)", na=False)

    # 2. Reemplazos (una sola columna por concepto)
    df["genero"] = df["genero"].fillna("SIN DATO")
    df["grupo_etario"] = df["grupo_etario"].fillna("SIN DATO")
    df["municipio"] = (df["municipio"]
                       .str.replace(r"\s*\(CT\)\s*$", "", regex=True)
                       .str.strip())
    df["departamento"] = df["departamento_norm"]

    # 3. Auxiliares para agrupar por tiempo
    df["anio"] = df["fecha_hecho"].dt.year
    df["mes"] = df["fecha_hecho"].dt.to_period("M").dt.to_timestamp()

    return df[["id", "fecha_hecho", "departamento", "municipio", "codigo_dane",
               "delito", "genero", "grupo_etario", "armas_medios", "cantidad",
               "es_repetido", "es_capital", "anio", "mes"]]