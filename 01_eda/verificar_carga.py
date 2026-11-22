"""Verifica la lectura del CSV y el filtro del Caribe contra las cifras de control.

Uso (desde la raíz del proyecto, con el entorno activo):
    python 01_eda/verificar_carga.py
"""
import pandas as pd

from datos import (ARCHIVO, CARIBE, COLUMNAS, NOMBRES_CSV_CARIBE,
                   cargar_nacional, filtrar_caribe)

COLS_FILA = ["departamento", "municipio", "codigo_dane", "armas_medios",
             "fecha_hecho", "genero", "grupo_etario", "cantidad", "delito"]


def linea(nombre, obtenido, esperado=None):
    estado = ""
    if esperado is not None:
        estado = "  OK" if obtenido == esperado else f"  <-- ESPERADO {esperado}"
    print(f"{nombre:<58}{obtenido}{estado}")


crudo = pd.read_csv(ARCHIVO, dtype=str, encoding="utf-8-sig",
                    keep_default_na=False, na_values=[""])
nac = cargar_nacional()
car = filtrar_caribe(nac)

print("\n== 1. Lectura del CSV (todo el país) ==")
linea("Filas leídas", len(nac), 405193)
linea("Columnas del archivo", len(crudo.columns), len(COLUMNAS))
linea("Departamentos distintos", nac["departamento"].nunique(), 33)
linea("Fecha mínima", f"{nac['fecha_hecho'].min():%d/%m/%Y}", "01/01/2010")
linea("Fecha máxima", f"{nac['fecha_hecho'].max():%d/%m/%Y}", "31/07/2026")
linea("Largo original del código DANE (valor: filas)",
      crudo["CODIGO DANE"].str.len().value_counts().to_dict())
linea("Largo del código DANE tras zfill(8)",
      nac["codigo_dane"].str.len().value_counts().to_dict(), {8: len(nac)})

print("\n== 2. Calidad a nivel nacional ==")
linea("genero nulo", int(nac["genero"].isna().sum()), 2417)
linea("genero = NO REPORTA", int((nac["genero"] == "NO REPORTA").sum()), 653)
linea("grupo_etario nulo", int(nac["grupo_etario"].isna().sum()), 635)
g = nac.groupby(COLS_FILA, dropna=False).size()
g = g[g > 1]
linea("Grupos de filas idénticas", len(g), 34855)
linea("Filas en esos grupos", int(g.sum()), 87618)
linea("Filas excedentes", int((g - 1).sum()), 52763)

print("\n== 3. Filtro del Caribe ==")
linea("Filas por código DANE (2 primeros dígitos)", len(car), 67122)
por_nombre = int(nac["departamento"].isin(NOMBRES_CSV_CARIBE).sum())
linea("Filas por nombre de departamento", por_nombre, 67122)
linea("Departamentos del Caribe presentes", car["cod_depto"].nunique(), len(CARIBE))
linea("cantidad: valores distintos en el Caribe",
      sorted(car["cantidad"].unique().tolist()), [1])
linea("genero nulo (Caribe)", int(car["genero"].isna().sum()), 370)
linea("grupo_etario nulo (Caribe)", int(car["grupo_etario"].isna().sum()), 68)
linea("armas_medios que empiezan por NO REPORT (Caribe)",
      int(car["armas_medios"].astype(str).str.upper().str.startswith("NO REPORT").sum()),
      10822)
print()