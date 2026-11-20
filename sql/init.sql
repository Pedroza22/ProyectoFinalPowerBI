-- ============================================================
-- init.sql
-- Esquema estrella: Evaluación del Rendimiento Académico
-- Base de datos: rendimiento_academico
-- Ejecutado automáticamente por Docker al primer arranque
-- ============================================================

-- ============================================================
-- DIMENSIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_facultad (
    sk_facultad   SERIAL PRIMARY KEY,
    facultad      VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_programa (
    sk_programa   SERIAL PRIMARY KEY,
    programa      VARCHAR(50) NOT NULL,
    facultad      VARCHAR(50) NOT NULL,
    UNIQUE (programa, facultad)
);

CREATE TABLE IF NOT EXISTS dim_materia (
    sk_materia    SERIAL PRIMARY KEY,
    materia       VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_semestre (
    sk_semestre     SERIAL PRIMARY KEY,
    semestre        VARCHAR(30) NOT NULL UNIQUE,
    semestre_orden  SMALLINT    NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_cohorte (
    sk_cohorte    SERIAL PRIMARY KEY,
    cohorte       VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_genero (
    sk_genero     SERIAL PRIMARY KEY,
    genero        VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_estudiante (
    id_estudiante                 INTEGER      PRIMARY KEY,
    genero                        VARCHAR(20),
    nacionalidad                  VARCHAR(50),
    lugar_nacimiento              VARCHAR(50),
    acudiente                     VARCHAR(20),
    acudiente_responde_encuesta   VARCHAR(5),
    satisfaccion_acudiente        VARCHAR(10)
);

-- ============================================================
-- TABLA DE HECHOS
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_desempeno (
    id_hecho              SERIAL       PRIMARY KEY,
    id_estudiante         INTEGER      NOT NULL REFERENCES dim_estudiante(id_estudiante),
    sk_facultad           INTEGER      NOT NULL REFERENCES dim_facultad(sk_facultad),
    sk_programa           INTEGER      NOT NULL REFERENCES dim_programa(sk_programa),
    sk_materia            INTEGER      NOT NULL REFERENCES dim_materia(sk_materia),
    sk_semestre           INTEGER      NOT NULL REFERENCES dim_semestre(sk_semestre),
    sk_cohorte            INTEGER      NOT NULL REFERENCES dim_cohorte(sk_cohorte),
    sk_genero             INTEGER      NOT NULL REFERENCES dim_genero(sk_genero),

    -- Rendimiento
    nivel_rendimiento     VARCHAR(10)  NOT NULL CHECK (nivel_rendimiento IN ('Bajo','Medio','Alto')),
    nivel_codigo          CHAR(1)      NOT NULL CHECK (nivel_codigo IN ('L','M','H')),
    nota_ordinal          SMALLINT     NOT NULL CHECK (nota_ordinal BETWEEN 1 AND 3),
    nota_aproximada       NUMERIC(5,2) NOT NULL,

    -- Asistencia
    asistencia            VARCHAR(30)  NOT NULL,
    ausencias_codigo      VARCHAR(10)  NOT NULL,

    -- Métricas de participación (0-100)
    manos_levantadas      SMALLINT     NOT NULL CHECK (manos_levantadas BETWEEN 0 AND 100),
    recursos_visitados    SMALLINT     NOT NULL CHECK (recursos_visitados BETWEEN 0 AND 100),
    anuncios_vistos       SMALLINT     NOT NULL CHECK (anuncios_vistos BETWEEN 0 AND 100),
    participacion_foros   SMALLINT     NOT NULL CHECK (participacion_foros BETWEEN 0 AND 100),
    indice_participacion  NUMERIC(5,2) NOT NULL,
    rango_participacion   VARCHAR(10)  NOT NULL,

    -- Banderas calculadas
    es_reprobado          SMALLINT     NOT NULL DEFAULT 0 CHECK (es_reprobado IN (0,1)),
    es_sobresaliente      SMALLINT     NOT NULL DEFAULT 0 CHECK (es_sobresaliente IN (0,1)),
    es_riesgo_desercion   SMALLINT     NOT NULL DEFAULT 0 CHECK (es_riesgo_desercion IN (0,1))
);

-- ============================================================
-- TABLA DE RESULTADOS ANOVA (estática, para reportes)
-- ============================================================

CREATE TABLE IF NOT EXISTS resultados_anova (
    id_resultado  SERIAL       PRIMARY KEY,
    variable      VARCHAR(50)  NOT NULL,
    factor        VARCHAR(50)  NOT NULL,
    k_grupos      SMALLINT,
    f_estadistico NUMERIC(10,4),
    p_anova       NUMERIC(15,10),
    p_anova_fmt   VARCHAR(15),   -- formato legible: "< 0.001" o el valor
    eta2          NUMERIC(8,4),
    efecto        VARCHAR(10),
    levene_p      NUMERIC(10,6),
    kruskal_h     NUMERIC(10,4),
    p_kruskal     NUMERIC(15,10),
    concluye      VARCHAR(60)
);

-- ============================================================
-- ÍNDICES para las consultas más frecuentes en Power BI
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_facultad   ON fact_desempeno(sk_facultad);
CREATE INDEX IF NOT EXISTS idx_fact_programa   ON fact_desempeno(sk_programa);
CREATE INDEX IF NOT EXISTS idx_fact_materia    ON fact_desempeno(sk_materia);
CREATE INDEX IF NOT EXISTS idx_fact_semestre   ON fact_desempeno(sk_semestre);
CREATE INDEX IF NOT EXISTS idx_fact_cohorte    ON fact_desempeno(sk_cohorte);
CREATE INDEX IF NOT EXISTS idx_fact_genero     ON fact_desempeno(sk_genero);
CREATE INDEX IF NOT EXISTS idx_fact_nivel      ON fact_desempeno(nivel_rendimiento);
CREATE INDEX IF NOT EXISTS idx_fact_asistencia ON fact_desempeno(ausencias_codigo);

-- ============================================================
-- VISTAS útiles (equivalen a las consultas del tablero)
-- ============================================================

-- Req. 1: promedio de nota por materia y semestre
CREATE OR REPLACE VIEW v_nota_materia_semestre AS
SELECT
    m.materia,
    s.semestre,
    s.semestre_orden,
    ROUND(AVG(f.nota_aproximada), 2)  AS promedio_nota,
    COUNT(*)                           AS total_estudiantes
FROM fact_desempeno f
JOIN dim_materia  m ON f.sk_materia  = m.sk_materia
JOIN dim_semestre s ON f.sk_semestre = s.sk_semestre
GROUP BY m.materia, s.semestre, s.semestre_orden
ORDER BY m.materia, s.semestre_orden;

-- Req. 2: tasa de deserción por facultad
CREATE OR REPLACE VIEW v_desercion_facultad AS
SELECT
    fa.facultad,
    COUNT(*)                                              AS total_estudiantes,
    SUM(f.es_riesgo_desercion)                           AS en_riesgo,
    ROUND(SUM(f.es_riesgo_desercion)::NUMERIC / COUNT(*), 4) AS tasa_desercion
FROM fact_desempeno f
JOIN dim_facultad fa ON f.sk_facultad = fa.sk_facultad
GROUP BY fa.facultad
ORDER BY tasa_desercion DESC;

-- Req. 3: desempeño por género
CREATE OR REPLACE VIEW v_desempeno_genero AS
SELECT
    g.genero,
    ROUND(AVG(f.nota_aproximada), 2) AS promedio_nota,
    SUM(f.es_reprobado)              AS reprobados,
    SUM(f.es_sobresaliente)          AS sobresalientes,
    COUNT(*)                          AS total
FROM fact_desempeno f
JOIN dim_genero g ON f.sk_genero = g.sk_genero
GROUP BY g.genero;

-- Req. 6: top 10 materias con mayor reprobación
CREATE OR REPLACE VIEW v_top10_reprobacion AS
SELECT
    m.materia,
    COUNT(*)                                           AS total_estudiantes,
    SUM(f.es_reprobado)                               AS reprobados,
    ROUND(SUM(f.es_reprobado)::NUMERIC / COUNT(*), 4) AS tasa_reprobacion,
    RANK() OVER (ORDER BY SUM(f.es_reprobado)::NUMERIC / COUNT(*) DESC) AS ranking
FROM fact_desempeno f
JOIN dim_materia m ON f.sk_materia = m.sk_materia
GROUP BY m.materia
ORDER BY tasa_reprobacion DESC
LIMIT 10;

-- Req. 7: asistencia vs rendimiento
CREATE OR REPLACE VIEW v_asistencia_rendimiento AS
SELECT
    asistencia,
    ausencias_codigo,
    ROUND(AVG(nota_aproximada), 2)   AS promedio_nota,
    COUNT(*)                          AS total_estudiantes,
    SUM(es_reprobado)                AS reprobados,
    SUM(es_sobresaliente)            AS sobresalientes
FROM fact_desempeno
GROUP BY asistencia, ausencias_codigo
ORDER BY ausencias_codigo;

-- Req. 10: factores de participación por nivel
CREATE OR REPLACE VIEW v_participacion_nivel AS
SELECT
    nivel_rendimiento,
    ROUND(AVG(manos_levantadas), 2)     AS prom_manos,
    ROUND(AVG(recursos_visitados), 2)   AS prom_recursos,
    ROUND(AVG(anuncios_vistos), 2)      AS prom_anuncios,
    ROUND(AVG(participacion_foros), 2)  AS prom_foros,
    ROUND(AVG(indice_participacion), 2) AS prom_indice,
    COUNT(*)                             AS total
FROM fact_desempeno
GROUP BY nivel_rendimiento
ORDER BY nota_ordinal DESC;

-- Resumen ejecutivo global
CREATE OR REPLACE VIEW v_resumen_ejecutivo AS
SELECT
    COUNT(DISTINCT id_estudiante)                              AS total_estudiantes,
    ROUND(AVG(nota_aproximada), 2)                            AS promedio_nota,
    ROUND(SUM(es_reprobado)::NUMERIC      / COUNT(*), 4)      AS tasa_reprobacion,
    ROUND(SUM(es_riesgo_desercion)::NUMERIC / COUNT(*), 4)   AS tasa_desercion,
    ROUND(SUM(es_sobresaliente)::NUMERIC  / COUNT(*), 4)      AS pct_sobresalientes
FROM fact_desempeno;
