"""
01_etl.py - ETL del dataset xAPI-Edu-Data (Kaggle: aljarah/xAPI-Edu-Data)

EXTRACT   : lee xAPI-Edu-Data.csv
TRANSFORM : limpia, renombra, valida calidad, deriva campos y construye un modelo estrella
LOAD      : escribe CSV en ./salida/ listos para importar en Power BI

Uso:
    python 01_etl.py --entrada xAPI-Edu-Data.csv --salida salida
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Supuestos de mapeo (el dataset NO trae facultades, programas ni notas numericas)
# ----------------------------------------------------------------------------
NOTA_ORDINAL = {"L": 1, "M": 2, "H": 3}
NOTA_ETIQUETA = {"L": "Bajo", "M": "Medio", "H": "Alto"}
# Punto medio aproximado de las bandas oficiales: L = 0-69, M = 70-89, H = 90-100
NOTA_APROX = {"L": 60.0, "M": 80.0, "H": 95.0}
FACULTAD = {"lowerlevel": "Nivel Basico", "MiddleSchool": "Nivel Medio", "HighSchool": "Nivel Superior"}
SEMESTRE = {"F": "Primer semestre", "S": "Segundo semestre"}
SEMESTRE_ORDEN = {"F": 1, "S": 2}

COLUMNAS_ESPERADAS = [
    "gender", "NationalITy", "PlaceofBirth", "StageID", "GradeID", "SectionID", "Topic",
    "Semester", "Relation", "raisedhands", "VisITedResources", "AnnouncementsView",
    "Discussion", "ParentAnsweringSurvey", "ParentschoolSatisfaction",
    "StudentAbsenceDays", "Class",
]


def extraer(ruta):
    if not os.path.exists(ruta):
        sys.exit(f"No se encontro {ruta}. Descargalo de Kaggle (aljarah/xAPI-Edu-Data).")
    df = pd.read_csv(ruta)
    faltan = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    if faltan:
        sys.exit(f"Columnas faltantes en el CSV: {faltan}")
    print(f"[EXTRACT] {len(df)} filas, {df.shape[1]} columnas")
    return df


def calidad(df):
    print("[CALIDAD] nulos por columna:")
    print(df.isna().sum()[df.isna().sum() > 0].to_string() or "  sin nulos")
    dup = df.duplicated().sum()
    print(f"[CALIDAD] filas duplicadas exactas: {dup}")
    for c in ["raisedhands", "VisITedResources", "AnnouncementsView", "Discussion"]:
        fuera = ((df[c] < 0) | (df[c] > 100)).sum() if c in ("raisedhands", "VisITedResources") else (df[c] < 0).sum()
        print(f"[CALIDAD] {c}: min={df[c].min()} max={df[c].max()} fuera de rango={fuera}")


def transformar(df):
    df = df.copy()
    # Limpieza de texto
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype(str).str.strip()
    # Datos con ruido: duplicados exactos se conservan (pueden ser estudiantes distintos
    # con el mismo perfil, el dataset no trae ID); solo se reporta en calidad().

    df["ID_Estudiante"] = np.arange(1, len(df) + 1)

    # Renombrar a nombres de negocio
    df = df.rename(columns={
        "gender": "Genero_Codigo", "NationalITy": "Nacionalidad", "PlaceofBirth": "Lugar_Nacimiento",
        "StageID": "Facultad_Origen", "GradeID": "Grado", "SectionID": "Cohorte_Codigo",
        "Topic": "Materia", "Semester": "Semestre_Codigo", "Relation": "Acudiente",
        "raisedhands": "Manos_Levantadas", "VisITedResources": "Recursos_Visitados",
        "AnnouncementsView": "Anuncios_Vistos", "Discussion": "Participacion_Foros",
        "ParentAnsweringSurvey": "Acudiente_Responde_Encuesta",
        "ParentschoolSatisfaction": "Satisfaccion_Acudiente",
        "StudentAbsenceDays": "Ausencias_Codigo", "Class": "Nivel_Codigo",
    })

    # Campos derivados
    df["Genero"] = df["Genero_Codigo"].map({"M": "Masculino", "F": "Femenino"})
    df["Facultad"] = df["Facultad_Origen"].map(FACULTAD)
    df["Programa"] = "Grado " + df["Grado"].str.replace("G-", "", regex=False)
    df["Cohorte"] = "Seccion " + df["Cohorte_Codigo"]
    df["Semestre"] = df["Semestre_Codigo"].map(SEMESTRE)
    df["Semestre_Orden"] = df["Semestre_Codigo"].map(SEMESTRE_ORDEN)
    df["Nivel_Rendimiento"] = df["Nivel_Codigo"].map(NOTA_ETIQUETA)
    df["Nota_Ordinal"] = df["Nivel_Codigo"].map(NOTA_ORDINAL)
    df["Nota_Aproximada"] = df["Nivel_Codigo"].map(NOTA_APROX)
    df["Asistencia"] = np.where(df["Ausencias_Codigo"] == "Under-7", "Menos de 7 ausencias", "7 o mas ausencias")
    df["Es_Reprobado"] = (df["Nivel_Codigo"] == "L").astype(int)
    df["Es_Sobresaliente"] = (df["Nivel_Codigo"] == "H").astype(int)
    # PROXY de desercion: bajo rendimiento + 7 o mas ausencias
    df["Es_Riesgo_Desercion"] = ((df["Nivel_Codigo"] == "L") & (df["Ausencias_Codigo"] == "Above-7")).astype(int)
    df["Indice_Participacion"] = (
        df[["Manos_Levantadas", "Recursos_Visitados", "Anuncios_Vistos", "Participacion_Foros"]].mean(axis=1).round(2)
    )
    df["Rango_Participacion"] = pd.cut(
        df["Indice_Participacion"], bins=[-1, 25, 50, 75, 101],
        labels=["0-25", "26-50", "51-75", "76-100"],
    ).astype(str)
    df["Acudiente_Responde_Encuesta"] = df["Acudiente_Responde_Encuesta"].map({"Yes": "Si", "No": "No"})
    df["Satisfaccion_Acudiente"] = df["Satisfaccion_Acudiente"].map({"Good": "Buena", "Bad": "Mala"})
    df["Acudiente"] = df["Acudiente"].map({"Father": "Padre", "Mum": "Madre"})
    return df


def cargar(df, carpeta):
    os.makedirs(carpeta, exist_ok=True)

    def dim(cols, nombre, clave):
        d = df[cols].drop_duplicates().sort_values(cols).reset_index(drop=True)
        d.insert(0, clave, np.arange(1, len(d) + 1))
        d.to_csv(os.path.join(carpeta, f"{nombre}.csv"), index=False, encoding="utf-8-sig")
        return d

    d_fac = dim(["Facultad"], "Dim_Facultad", "SK_Facultad")
    d_pro = dim(["Programa", "Facultad"], "Dim_Programa", "SK_Programa")
    d_mat = dim(["Materia"], "Dim_Materia", "SK_Materia")
    d_sem = dim(["Semestre", "Semestre_Orden"], "Dim_Semestre", "SK_Semestre")
    d_coh = dim(["Cohorte"], "Dim_Cohorte", "SK_Cohorte")
    d_gen = dim(["Genero"], "Dim_Genero", "SK_Genero")

    dim_est = df[["ID_Estudiante", "Genero", "Nacionalidad", "Lugar_Nacimiento", "Acudiente",
                  "Acudiente_Responde_Encuesta", "Satisfaccion_Acudiente"]]
    dim_est.to_csv(os.path.join(carpeta, "Dim_Estudiante.csv"), index=False, encoding="utf-8-sig")

    f = df.merge(d_pro, on=["Programa", "Facultad"]).merge(d_fac, on="Facultad") \
          .merge(d_mat, on="Materia").merge(d_sem, on=["Semestre", "Semestre_Orden"]) \
          .merge(d_coh, on="Cohorte").merge(d_gen, on="Genero")
    cols = ["ID_Estudiante", "SK_Facultad", "SK_Programa", "SK_Materia", "SK_Semestre", "SK_Cohorte",
            "SK_Genero", "Nivel_Rendimiento", "Nivel_Codigo", "Nota_Ordinal", "Nota_Aproximada",
            "Asistencia", "Ausencias_Codigo", "Manos_Levantadas", "Recursos_Visitados",
            "Anuncios_Vistos", "Participacion_Foros", "Indice_Participacion", "Rango_Participacion",
            "Es_Reprobado", "Es_Sobresaliente", "Es_Riesgo_Desercion"]
    f[cols].sort_values("ID_Estudiante").to_csv(
        os.path.join(carpeta, "Fact_Desempeno.csv"), index=False, encoding="utf-8-sig")
    # Tabla plana para ANOVA / revision
    df.to_csv(os.path.join(carpeta, "dataset_limpio.csv"), index=False, encoding="utf-8-sig")
    print(f"[LOAD] archivos escritos en {carpeta}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="xAPI-Edu-Data.csv")
    ap.add_argument("--salida", default="salida")
    a = ap.parse_args()
    datos = extraer(a.entrada)
    calidad(datos)
    limpio = transformar(datos)
    cargar(limpio, a.salida)
