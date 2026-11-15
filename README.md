# Proyecto final: Evaluación del Rendimiento Académico (xAPI-Edu-Data)

Flujo: **CSV (Kaggle) → ETL (Python) → modelo estrella (CSV) → Power BI + DAX → ANOVA (Python)**

## 1. Archivos

| Archivo | Para qué sirve |
|---|---|
| `01_etl.py` | Extrae, limpia, valida calidad, deriva campos y genera el modelo estrella en `salida/` |
| `02_anova.py` | ANOVA de una y dos vías, Tukey, Kruskal-Wallis, Levene, Shapiro, chi-cuadrado |
| `medidas_dax.dax` | Todas las medidas DAX, con las relaciones del modelo en el encabezado |

## 2. Ejecución

```bash
pip install pandas numpy scipy statsmodels
# 1) Descarga xAPI-Edu-Data.csv desde Kaggle (aljarah/xAPI-Edu-Data) y ponlo junto a los scripts
python 01_etl.py   --entrada xAPI-Edu-Data.csv --salida salida
python 02_anova.py --entrada salida/dataset_limpio.csv --salida salida
```

Cargar en Power BI: Obtener datos → Texto/CSV → los 8 archivos `Dim_*.csv` y `Fact_Desempeno.csv` de `salida/`.

## 3. Adaptación del dataset (importante, decláralo en el informe)

El dataset real tiene 480 estudiantes y 17 columnas, **sin notas numéricas, facultades, programas, cohortes ni deserción**. Para cubrir los 10 requerimientos se hicieron estos mapeos, que debes justificar como supuestos metodológicos:

| Concepto del enunciado | Campo del dataset | Nota |
|---|---|---|
| Materia | `Topic` (12 materias) | directo |
| Semestre | `Semester` (F/S) | solo 2 semestres |
| Nota | `Class` (L / M / H) | L = 0-69, M = 70-89, H = 90-100. Se crea `Nota_Ordinal` (1-3) y `Nota_Aproximada` (60 / 80 / 95, valores de referencia) |
| Facultad | `StageID` (3 niveles) | proxy |
| Programa | `GradeID` (grados) | proxy |
| Cohorte | `SectionID` (A/B/C) | proxy |
| Reprobación | `Class = L` | |
| Sobresaliente | `Class = H` | |
| Asistencia | `StudentAbsenceDays` (<7 / ≥7) | |
| Deserción | **no existe**; proxy = Class L **y** ≥7 ausencias | llámala "riesgo de deserción" |

## 4. Tablero (4 páginas)

**Página 1: Resumen ejecutivo.** Tarjetas: Total Estudiantes, Promedio Nota, Tasa Reprobación, Tasa Deserción, % Sobresalientes. Segmentadores: Facultad, Semestre, Género, Cohorte. Dona de `Nivel_Rendimiento`.

**Página 2: Desempeño académico.**
- Req. 1: matriz Materia × Semestre con `Promedio Nota` (formato condicional).
- Req. 5: columnas/línea por `Semestre` con `Promedio Nota` y tarjeta `Tendencia Texto`.
- Req. 6: barras horizontales por Materia con `Tasa Reprobacion`, filtro Top N = 10, color con `Color Semaforo Reprobacion`.
- Req. 8: tabla de `Estudiantes Sobresalientes` y `Pct Sobresalientes` por Materia/Programa.

**Página 3: Comparativas.**
- Req. 2: barras por Facultad con `Tasa Desercion`.
- Req. 3: columnas agrupadas por Género con `Promedio Nota` + tarjeta `Brecha de Genero (F - M)`.
- Req. 4: barras por Programa con `Promedio Nota` y `Ranking Programa`.
- Req. 9: barras 100 % apiladas por Cohorte con `Distribucion Nivel %`.

**Página 4: Factores de éxito.**
- Req. 7: columnas por `Asistencia` con `Promedio Nota`, más `Efecto Asistencia (puntos)`.
- Req. 10: barras agrupadas de los 4 indicadores de participación por `Nivel_Rendimiento`; columnas por `Rango_Participacion` con `Pct Sobresalientes`; tarjeta `Correlacion Participacion vs Nota`; tabla con los resultados de ANOVA importando `resultados_anova.csv`.

## 5. Validación estadística (ANOVA)

Hipótesis para cada indicador de participación: H0: las medias son iguales entre rendimiento Bajo, Medio y Alto; H1: al menos una difiere (α = 0.05).

Lectura de resultados:
1. Si **Levene p < 0.05** (varianzas desiguales), apóyate también en Kruskal-Wallis, que se reporta al lado.
2. Si **p_anova < 0.05**, rechazas H0 y miras Tukey para saber qué pares difieren.
3. Reporta el tamaño del efecto **η²** (<0.06 pequeño, 0.06-0.14 mediano, >0.14 grande).
4. Con n = 480 el Shapiro suele rechazar normalidad por poco; el ANOVA es robusto con grupos de este tamaño, y Kruskal-Wallis confirma.

`ANOVA` sobre `Nota_Aproximada` por Materia/Programa/Facultad tiene la limitación de que la nota es una variable ordinal discretizada en 3 valores; menciónalo como limitación.

> Los resultados que viste al probar los scripts salieron de **datos simulados** con el mismo esquema, solo para verificar que el código corre. Tus conclusiones deben salir de ejecutarlo con el CSV real de Kaggle.

## 6. Estructura sugerida del informe

1. Problema y objetivo. 2. Dataset y supuestos de mapeo (sección 3). 3. ETL (extracción, limpieza, modelo estrella, calidad). 4. Modelo semántico y DAX. 5. Tablero con capturas por requerimiento. 6. ANOVA (hipótesis, supuestos, resultados, Tukey, η²). 7. Conclusiones y recomendaciones. 8. Limitaciones (proxies, solo 480 registros, nota ordinal).
