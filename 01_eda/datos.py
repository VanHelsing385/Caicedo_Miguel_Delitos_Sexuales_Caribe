from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).parent.parent
ARCHIVO = RAIZ / "00_datos_originales" / "delitos_sexuales_nacional.csv"

# Región Caribe: código DANE del departamento (2 primeros dígitos) -> nombre oficial
CARIBE = {"08": "Atlántico", "13": "Bolívar", "20": "Cesar", "23": "Córdoba",
          "44": "La Guajira", "47": "Magdalena", "70": "Sucre",
          "88": "San Andrés y Providencia"}

# Nombres tal como vienen en el CSV (solo para validar el filtro por código)
NOMBRES_CSV_CARIBE = ["ATLÁNTICO", "BOLÍVAR", "CESAR", "CÓRDOBA", "GUAJIRA",
                      "MAGDALENA", "SAN ANDRÉS", "SUCRE"]

COLUMNAS = {"DEPARTAMENTO": "departamento", "MUNICIPIO": "municipio",
            "CODIGO DANE": "codigo_dane", "ARMAS MEDIOS": "armas_medios",
            "FECHA HECHO": "fecha_hecho", "GENERO": "genero",
            "GRUPO ETARIO": "grupo_etario", "CANTIDAD": "cantidad",
            "delito": "delito"}


def cargar_nacional(ruta: Path = ARCHIVO) -> pd.DataFrame:
    """Lee el CSV original completo (todo el país) sin eliminar ninguna fila.

    - Todo se lee como texto y solo los campos vacíos cuentan como nulos
      (así no se confunden valores como "NA" con datos faltantes).
    - codigo_dane se conserva como texto de 8 caracteres (ceros iniciales).
    - id = posición de la fila en el CSV (1, 2, 3...), para poder rastrear
      cada registro hasta el archivo original.
    """
    df = pd.read_csv(ruta, dtype=str, encoding="utf-8-sig",
                     keep_default_na=False, na_values=[""])
    df = df.rename(columns=COLUMNAS)
    faltan = set(COLUMNAS.values()) - set(df.columns)
    if faltan:
        raise ValueError(f"Faltan columnas en el CSV: {sorted(faltan)}")

    df["codigo_dane"] = df["codigo_dane"].str.zfill(8)
    df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], format="%d/%m/%Y")
    df["cantidad"] = pd.to_numeric(df["cantidad"]).astype(int)
    df.insert(0, "id", np.arange(1, len(df) + 1))
    return df


def filtrar_caribe(nacional: pd.DataFrame) -> pd.DataFrame:
    """Selecciona los 8 departamentos del Caribe por código DANE.

    Es una selección sobre una copia: el DataFrame nacional no se modifica.
    Devuelve las columnas con el esquema que usa el EDA.
    """
    d = nacional.copy()
    d["cod_depto"] = d["codigo_dane"].str[:2]
    d = d[d["cod_depto"].isin(CARIBE)].copy()
    d["departamento_norm"] = d["cod_depto"].map(CARIBE)
    d = d.rename(columns={"departamento": "departamento_original"})
    return d[["id", "cod_depto", "departamento_norm", "departamento_original",
              "municipio", "codigo_dane", "armas_medios", "fecha_hecho",
              "genero", "grupo_etario", "cantidad", "delito"]].reset_index(drop=True)


def cargar_delitos() -> pd.DataFrame:
    """Registros del Caribe (misma estructura que usan las pestañas del EDA)."""
    return filtrar_caribe(cargar_nacional())