# Observatorio Académico — Evaluación del Rendimiento Académico

**Dataset:** xAPI-Edu-Data · Kaggle (aljarah/xAPI-Edu-Data) · 480 estudiantes  
**Tablero publicado:** https://app.powerbi.com/view?r=eyJrIjoiMTE0NGRmOWEtMDc2ZS00M2RmLWJjMDYtMzM3MzM1NDI5YzI4IiwidCI6IjhkMzY4MzZlLTZiNzUtNGRlNi1iYWI5LTVmNGIxNzc1NDI3ZiIsImMiOjR9  
**HTML desplegado:** `tablero.html` (publicado en Vercel)

---

## Qué hace este proyecto

Analiza el rendimiento académico de 480 estudiantes registrados en un LMS. Responde 10 preguntas analíticas sobre desempeño, deserción, género, materias y factores de éxito, usando un flujo completo de ETL, modelado semántico en Power BI y validación estadística con ANOVA.

```
xAPI-Edu-Data.csv → ETL (Python) → Modelo estrella (CSV) → Power BI + DAX → ANOVA (Python)
```

---

## Archivos del proyecto

| Archivo | Qué es |
|---|---|
| `01_etl.py` | ETL: limpia el CSV original y genera el modelo estrella en `salida/` |
| `02_anova.py` | ANOVA, Tukey, chi-cuadrado sobre los datos limpios |
| `medidas_dax.dax` | Las 36 medidas DAX del tablero |
| `tablero.html` | Página web con el tablero embebido, publicada en Vercel |
| `docker-compose.yml` | Levanta PostgreSQL con el esquema de la BD |
| `sql/init.sql` | Esquema estrella en SQL (tablas, claves, índices, vistas) |
| `03_carga_postgres.py` | Carga los CSV en PostgreSQL |
| `salida/` | CSVs generados por el ETL (modelo estrella + resultados estadísticos) |

---

## Cómo reproducir el flujo completo

**1. Instalar dependencias**
```bash
pip install pandas numpy scipy statsmodels psycopg2-binary sqlalchemy
```

**2. Descargar el dataset**  
Descargar `xAPI-Edu-Data.csv` desde https://www.kaggle.com/datasets/aljarah/xAPI-Edu-Data y colocarlo en la raíz del proyecto.

**3. Ejecutar el ETL**
```bash
python 01_etl.py --entrada xAPI-Edu-Data.csv --salida salida
```
Genera `Fact_Desempeno.csv` y los 7 `Dim_*.csv` en `salida/`.

**4. Ejecutar el ANOVA**
```bash
python 02_anova.py --entrada salida/dataset_limpio.csv --salida salida
```
Genera `resultados_anova.csv`, `chi_cuadrado.csv` y los 4 `tukey_*.csv`.

**5. Levantar la base de datos (opcional)**
```bash
docker compose up -d
python 03_carga_postgres.py --salida salida
```
Conexión: `localhost:5432` · BD: `rendimiento_academico` · Usuario: `admin` · Contraseña: `admin123`

---

## Lo que se construyó

### ETL
- Extracción del CSV original (17 columnas, 480 filas)
- Limpieza: nulos, duplicados, rangos fuera de escala
- Campos derivados: `Nota_Aproximada` (60/80/95), `Indice_Participacion`, `Es_Reprobado`, `Es_Sobresaliente`, `Es_Riesgo_Desercion`
- Carga en modelo estrella: 1 tabla de hechos + 7 dimensiones

### Modelo estrella

```
Dim_Facultad ──┐
Dim_Programa ──┤
Dim_Materia  ──┤
Dim_Semestre ──┼──► Fact_Desempeno (480 filas · 22 columnas)
Dim_Cohorte  ──┤
Dim_Genero   ──┤
Dim_Estudiante─┘
```

### Tablero Power BI — 4 páginas

| Página | Contenido | Requerimientos |
|---|---|---|
| Resumen ejecutivo | 5 KPIs, dona de distribución, nota por nivel | — |
| Desempeño académico | Matriz materia × semestre, top 10 reprobación, sobresalientes | 1, 5, 6, 8 |
| Comparativas | Deserción por nivel, nota por género, ranking programas, distribución por sección | 2, 3, 4, 9 |
| Factores de éxito | Asistencia vs nota, correlación participación, actividad por nivel, tabla ANOVA | 7, 10 |

### Medidas DAX destacadas

| Medida | Qué hace |
|---|---|
| `Total Estudiantes` | Conteo distinto de IDs |
| `Promedio Nota` | Media de `Nota_Aproximada` con contexto de filtro |
| `Tasa Reprobacion` | `Es_Reprobado / Total` con `DIVIDE` |
| `Tasa Desercion` | Proxy: nivel Bajo + 7 o más ausencias |
| `Brecha de Genero (F - M)` | Diferencia de promedios entre géneros |
| `Tendencia Texto` | ▲ Mejora / ▼ Deterioro / ● Estable según variación S2 − S1 |
| `Ranking Programa` | `RANKX` por promedio de nota |
| `Color Semaforo Reprobacion` | Rojo ≥ 40% · Ámbar ≥ 25% · Verde |
| `Correlacion Participacion vs Nota` | Pearson calculado con `SUMX` |
| `Efecto Asistencia (puntos)` | Diferencia de nota entre grupos de asistencia |

### Validación estadística

- **ANOVA de una vía:** cada indicador de participación vs nivel de rendimiento
- **Post-hoc Tukey HSD:** qué pares de grupos difieren (Bajo/Medio/Alto)
- **Levene:** verificación de homogeneidad de varianzas
- **Shapiro-Wilk:** verificación de normalidad por grupo
- **Kruskal-Wallis:** alternativa no paramétrica cuando Levene falla
- **Tamaño del efecto η²:** pequeño < 0.06 · mediano 0.06–0.14 · grande > 0.14
- **Chi-cuadrado + V de Cramér:** variables categóricas vs nivel de rendimiento

---

## Supuestos metodológicos

El dataset es de educación escolar, no universitaria. Se hicieron las siguientes adaptaciones:

| Original en el dataset | Adaptado como |
|---|---|
| `StageID` (etapa escolar) | Facultad / Nivel educativo |
| `GradeID` (grado) | Programa |
| `SectionID` (sección A/B/C) | Cohorte |
| `Class` L/M/H | Nota aproximada 60 / 80 / 95 |
| Sin dato de deserción | Proxy: nivel Bajo + 7 o más ausencias |

---

## Resultados principales

| Indicador | Valor |
|---|---|
| Nota promedio global | 79,15 |
| Tasa de reprobación | 26,5% (127 estudiantes) |
| Riesgo de deserción (proxy) | 24,2% (116 estudiantes) |
| Sobresalientes | 29,6% (142 estudiantes) |
| Diferencia asistencia alta vs baja | +18,2 puntos |
| Correlación participación vs nota | 0,70 |
| Brecha género F − M | +7,1 puntos |

---

*Python 3.x · pandas · numpy · scipy · statsmodels · Power BI Desktop · PostgreSQL 16 · Docker*
