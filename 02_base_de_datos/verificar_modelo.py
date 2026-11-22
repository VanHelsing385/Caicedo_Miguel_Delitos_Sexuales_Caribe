"""Verifica los supuestos del diseño de la base de datos con los datos reales.

No escribe nada: solo lee el CSV, aplica la limpieza del EDA y comprueba que
el modelo previsto (departamentos, municipios, catálogos y tabla central) es
coherente con los datos.

Uso (desde la raíz del proyecto, con el entorno activo):
    python 02_base_de_datos/verificar_modelo.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01_eda"))
from datos import CARIBE, cargar_nacional, filtrar_caribe   # noqa: E402
from limpieza import preparar                                # noqa: E402


def linea(nombre, obtenido, esperado=None):
    estado = ""
    if esperado is not None:
        estado = "  OK" if obtenido == esperado else f"  <-- ESPERADO {esperado}"
    print(f"{nombre:<66}{obtenido}{estado}")


def ejemplos(serie_bool, d, cols, n=5):
    """Muestra algunas filas que incumplen una comprobación."""
    if serie_bool.any():
        print("    ejemplos:")
        print(d.loc[serie_bool, cols].drop_duplicates().head(n).to_string(index=False))


car = filtrar_caribe(cargar_nacional())
d = preparar(car)
d["cod_depto"] = d["codigo_dane"].str[:2]
d["cod_mpio"] = d["codigo_dane"].str[:5]
d["cod_cp"] = d["codigo_dane"].str[5:]

print("\n== 1. Municipios (prefijo de 5 dígitos del código DANE) ==")
g = d.groupby("cod_mpio").agg(nombres=("municipio", "nunique"),
                              deptos=("cod_depto", "nunique"),
                              capital=("es_capital", "nunique"))
linea("Municipios distintos (prefijos de 5 dígitos)", len(g))
linea("Prefijos con más de un nombre de municipio", int((g["nombres"] > 1).sum()), 0)
linea("Prefijos con más de un departamento", int((g["deptos"] > 1).sum()), 0)
linea("Prefijos con es_capital no constante", int((g["capital"] > 1).sum()), 0)
ejemplos(d["cod_mpio"].isin(g.index[g["nombres"] > 1]), d,
         ["cod_mpio", "municipio", "departamento"])
h = d.groupby(["cod_depto", "municipio"])["cod_mpio"].nunique()
linea("Nombres de municipio repetidos en un departamento (otro código)",
      int((h > 1).sum()), 0)
por_depto = d.groupby("departamento")["cod_mpio"].nunique().sort_values(ascending=False)
print("  municipios por departamento:", por_depto.to_dict())
dep_ok = d.groupby("cod_depto")["departamento"].nunique()
linea("Códigos de departamento con más de un nombre", int((dep_ok > 1).sum()), 0)
linea("Códigos de departamento fuera de los 8 del Caribe",
      int((~d["cod_depto"].isin(CARIBE)).sum()), 0)

print("\n== 2. Capitales ==")
cap = d[d["es_capital"]].groupby("cod_mpio")["municipio"].first()
linea("Municipios marcados como capital (sufijo (CT))", len(cap), 8)
linea("  de ellos, con código de municipio terminado en 001",
      int(cap.index.str.endswith("001").sum()), 8)
no_cap = d[(d["cod_mpio"].str[2:] == "001") & ~d["es_capital"]]
linea("Municipios 001 que NO están marcados como capital",
      no_cap["cod_mpio"].nunique(), 0)
mostrar = list(cap.items())[:12]
print("  capitales:", dict(mostrar), "..." if len(cap) > 12 else "")

print("\n== 3. Centro poblado (3 últimos dígitos del código DANE) ==")
linea("Códigos con los 3 últimos caracteres no numéricos",
      int((~d["cod_cp"].str.fullmatch(r"\d{3}")).sum()), 0)
en_cab = int((d["cod_cp"] == "000").sum())
linea("Registros en cabecera municipal (000)", en_cab)
linea("Registros en centro poblado (001 en adelante)", len(d) - en_cab)
cp = d[d["cod_cp"] != "000"]
linea("  códigos DANE distintos de centro poblado", cp["codigo_dane"].nunique())
linea("  municipios que tienen algún centro poblado", cp["cod_mpio"].nunique())

print("\n== 4. Catálogos ==")
linea("Tipos de delito distintos", d["delito"].nunique(), 22)
linea("Medios distintos", d["armas_medios"].nunique(), 11)
linea("Géneros distintos", d["genero"].nunique(), 4)
linea("Grupos etarios distintos", d["grupo_etario"].nunique(), 4)
print("  géneros:", sorted(d["genero"].unique()))
print("  grupos etarios:", sorted(d["grupo_etario"].unique()))
print("  medios:", sorted(d["armas_medios"].unique()))

print("\n== 5. Tipos de delito: número de artículo y marca «menor de 14» ==")
patron = re.compile(r"ART[ÍI]CULO\s+(\d+)(?:\s*([A-Z]))?\s*\.", re.IGNORECASE)
cat = (d.groupby("delito").size().rename("registros").reset_index())
parsed = cat["delito"].apply(lambda t: patron.search(t))
cat["articulo"] = parsed.apply(lambda m: (m.group(1) + (m.group(2) or "")) if m else None)
cat["es_menor_14"] = cat["delito"].str.upper().str.contains("MENOR DE 14")
linea("Delitos sin número de artículo reconocido", int(cat["articulo"].isna().sum()), 0)
linea("Delitos distintos con el mismo número de artículo",
      int(cat["articulo"].dropna().duplicated().sum()), 0)
linea("Delitos marcados como «menor de 14»", int(cat["es_menor_14"].sum()))
print(cat.sort_values("registros", ascending=False)
      .to_string(index=False, formatters={"delito": lambda s: s[:72]}))

print("\n== 6. Tabla central y longitudes ==")
linea("id (posición en el CSV) único", bool(d["id"].is_unique), True)
linea("id en orden ascendente", bool(d["id"].is_monotonic_increasing), True)
linea("Registros", len(d), 67122)
linea("Fechas fuera de 01/01/2010 - 31/07/2026",
      int(((d["fecha_hecho"] < "2010-01-01") | (d["fecha_hecho"] > "2026-07-31")).sum()), 0)
linea("cantidad: valores distintos", sorted(d["cantidad"].unique().tolist()), [1])
linea("Nulos en las columnas de la tabla central",
      int(d[["fecha_hecho", "municipio", "codigo_dane", "delito", "genero",
             "grupo_etario", "armas_medios", "cantidad"]].isna().sum().sum()), 0)
for col in ["municipio", "delito", "armas_medios", "genero", "grupo_etario"]:
    linea(f"Longitud máxima de {col}", int(d[col].str.len().max()))
print()