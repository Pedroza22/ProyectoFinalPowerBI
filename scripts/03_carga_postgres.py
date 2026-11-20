"""
03_carga_postgres.py
Lee los CSV generados por 01_etl.py y los carga en PostgreSQL.

Requisitos:
    pip install pandas psycopg2-binary sqlalchemy

Uso:
    python 03_carga_postgres.py --salida salida

La base de datos debe estar corriendo:
    docker compose up -d
    (esperar ~10 segundos a que Postgres termine de inicializar)
"""

import argparse
import os
import sys
import time

import pandas as pd
from sqlalchemy import create_engine, text

# ── Conexión ────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST",     "localhost")
DB_PORT = os.getenv("DB_PORT",     "5432")
DB_NAME = os.getenv("DB_NAME",     "rendimiento_academico")
DB_USER = os.getenv("DB_USER",     "admin")
DB_PASS = os.getenv("DB_PASS",     "admin123")

CONNECTION_STRING = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def conectar(reintentos=5, espera=3):
    """Reintenta la conexión mientras Postgres termina de arrancar."""
    engine = create_engine(CONNECTION_STRING)
    for intento in range(1, reintentos + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[DB] Conexión exitosa a {DB_NAME}@{DB_HOST}:{DB_PORT}")
            return engine
        except Exception as e:
            print(f"[DB] Intento {intento}/{reintentos} fallido: {e}")
            if intento < reintentos:
                time.sleep(espera)
    sys.exit("[DB] No se pudo conectar. ¿Está corriendo 'docker compose up -d'?")


def limpiar_tablas(engine):
    """Elimina datos previos respetando el orden de las claves foráneas."""
    orden = [
        "fact_desempeno",
        "resultados_anova",
        "dim_estudiante",
        "dim_facultad",
        "dim_programa",
        "dim_materia",
        "dim_semestre",
        "dim_cohorte",
        "dim_genero",
    ]
    with engine.begin() as conn:
        for tabla in orden:
            conn.execute(text(f"TRUNCATE TABLE {tabla} RESTART IDENTITY CASCADE"))
    print("[DB] Tablas vaciadas")


def cargar_dim(engine, df_csv, tabla, columnas, rename=None):
    """Carga una dimensión. rename: dict {col_csv: col_bd}."""
    df = df_csv[columnas].copy()
    if rename:
        df = df.rename(columns=rename)
    # Quitar la columna SK (el serial de Postgres la genera sola)
    sk_cols = [c for c in df.columns if c.lower().startswith("sk_")]
    df = df.drop(columns=sk_cols)
    df.to_sql(tabla, engine, if_exists="append", index=False)
    print(f"[LOAD] {tabla}: {len(df)} filas")


def main(carpeta):
    engine = conectar()
    limpiar_tablas(engine)

    # ── Leer CSVs ──────────────────────────────────────────
    def leer(nombre):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            sys.exit(f"No se encontró {ruta}. Ejecuta primero 01_etl.py")
        return pd.read_csv(ruta)

    dim_fac  = leer("Dim_Facultad.csv")
    dim_pro  = leer("Dim_Programa.csv")
    dim_mat  = leer("Dim_Materia.csv")
    dim_sem  = leer("Dim_Semestre.csv")
    dim_coh  = leer("Dim_Cohorte.csv")
    dim_gen  = leer("Dim_Genero.csv")
    dim_est  = leer("Dim_Estudiante.csv")
    fact     = leer("Fact_Desempeno.csv")
    anova    = leer("resultados_anova.csv")

    # ── Dimensiones ────────────────────────────────────────
    # dim_facultad
    dim_fac[["Facultad"]].rename(columns={"Facultad": "facultad"}) \
        .to_sql("dim_facultad", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_facultad: {len(dim_fac)} filas")

    # dim_programa
    dim_pro[["Programa", "Facultad"]].rename(
        columns={"Programa": "programa", "Facultad": "facultad"}
    ).to_sql("dim_programa", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_programa: {len(dim_pro)} filas")

    # dim_materia
    dim_mat[["Materia"]].rename(columns={"Materia": "materia"}) \
        .to_sql("dim_materia", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_materia: {len(dim_mat)} filas")

    # dim_semestre
    dim_sem[["Semestre", "Semestre_Orden"]].rename(
        columns={"Semestre": "semestre", "Semestre_Orden": "semestre_orden"}
    ).to_sql("dim_semestre", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_semestre: {len(dim_sem)} filas")

    # dim_cohorte
    dim_coh[["Cohorte"]].rename(columns={"Cohorte": "cohorte"}) \
        .to_sql("dim_cohorte", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_cohorte: {len(dim_coh)} filas")

    # dim_genero
    dim_gen[["Genero"]].rename(columns={"Genero": "genero"}) \
        .to_sql("dim_genero", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_genero: {len(dim_gen)} filas")

    # dim_estudiante
    dim_est.rename(columns={
        "ID_Estudiante":               "id_estudiante",
        "Genero":                      "genero",
        "Nacionalidad":                "nacionalidad",
        "Lugar_Nacimiento":            "lugar_nacimiento",
        "Acudiente":                   "acudiente",
        "Acudiente_Responde_Encuesta": "acudiente_responde_encuesta",
        "Satisfaccion_Acudiente":      "satisfaccion_acudiente",
    }).to_sql("dim_estudiante", engine, if_exists="append", index=False)
    print(f"[LOAD] dim_estudiante: {len(dim_est)} filas")

    # ── Tabla de hechos ────────────────────────────────────
    # Reconstruir las SKs desde las dimensiones (Postgres las asignó en orden)
    # En el CSV las SKs empiezan en 1 y coinciden con el SERIAL de Postgres
    # porque TRUNCATE RESTART IDENTITY las resetea. Solo renombramos columnas.
    fact_bd = fact.rename(columns={
        "ID_Estudiante":       "id_estudiante",
        "SK_Facultad":         "sk_facultad",
        "SK_Programa":         "sk_programa",
        "SK_Materia":          "sk_materia",
        "SK_Semestre":         "sk_semestre",
        "SK_Cohorte":          "sk_cohorte",
        "SK_Genero":           "sk_genero",
        "Nivel_Rendimiento":   "nivel_rendimiento",
        "Nivel_Codigo":        "nivel_codigo",
        "Nota_Ordinal":        "nota_ordinal",
        "Nota_Aproximada":     "nota_aproximada",
        "Asistencia":          "asistencia",
        "Ausencias_Codigo":    "ausencias_codigo",
        "Manos_Levantadas":    "manos_levantadas",
        "Recursos_Visitados":  "recursos_visitados",
        "Anuncios_Vistos":     "anuncios_vistos",
        "Participacion_Foros": "participacion_foros",
        "Indice_Participacion":"indice_participacion",
        "Rango_Participacion": "rango_participacion",
        "Es_Reprobado":        "es_reprobado",
        "Es_Sobresaliente":    "es_sobresaliente",
        "Es_Riesgo_Desercion": "es_riesgo_desercion",
    })
    fact_bd.to_sql("fact_desempeno", engine, if_exists="append", index=False)
    print(f"[LOAD] fact_desempeno: {len(fact_bd)} filas")

    # ── Resultados ANOVA ───────────────────────────────────
    # Formatear p-valores: si < 0.001 mostrar "< 0.001"
    def fmt_p(val):
        try:
            v = float(val)
            return "< 0.001" if v < 0.001 else f"{v:.4f}"
        except Exception:
            return str(val)

    anova_bd = anova.copy()
    anova_bd.columns = [c.lower() for c in anova_bd.columns]
    # Renombrar columnas que chocan con palabras reservadas
    anova_bd = anova_bd.rename(columns={"f": "f_estadistico"})
    if "p_anova" in anova_bd.columns:
        anova_bd["p_anova_fmt"] = anova_bd["p_anova"].apply(fmt_p)
    if "p_kruskal" in anova_bd.columns:
        anova_bd["p_kruskal"] = pd.to_numeric(anova_bd["p_kruskal"], errors="coerce")

    cols_bd = [
        "variable", "factor", "k_grupos", "f_estadistico", "p_anova",
        "p_anova_fmt", "eta2", "efecto", "levene_p", "kruskal_h",
        "p_kruskal", "concluye",
    ]
    cols_presentes = [c for c in cols_bd if c in anova_bd.columns]
    anova_bd[cols_presentes].to_sql(
        "resultados_anova", engine, if_exists="append", index=False
    )
    print(f"[LOAD] resultados_anova: {len(anova_bd)} filas")

    # ── Verificación final ─────────────────────────────────
    print("\n[VERIFY] Conteos en la base de datos:")
    tablas = [
        "dim_facultad", "dim_programa", "dim_materia", "dim_semestre",
        "dim_cohorte", "dim_genero", "dim_estudiante",
        "fact_desempeno", "resultados_anova",
    ]
    with engine.connect() as conn:
        for tabla in tablas:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
            print(f"  {tabla:<25} {n:>5} filas")

    print("\n[VERIFY] Resumen ejecutivo desde la vista:")
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM v_resumen_ejecutivo")).fetchone()
        if row:
            print(f"  Estudiantes      : {row[0]}")
            print(f"  Promedio nota    : {row[1]}")
            print(f"  Tasa reprobación : {float(row[2]):.1%}")
            print(f"  Tasa deserción   : {float(row[3]):.1%}")
            print(f"  % sobresalientes : {float(row[4]):.1%}")

    print("\n✅ Carga completada. Conecta Power BI a:")
    print(f"   Host: {DB_HOST}:{DB_PORT}  BD: {DB_NAME}  Usuario: {DB_USER}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="datos/modelo_estrella",
                    help="Carpeta con los CSV generados por 01_etl.py")
    a = ap.parse_args()
    main(a.salida)
