# Proyecto Final — Evaluación del Rendimiento Académico
### Dataset: xAPI-Edu-Data (Kaggle · aljarah/xAPI-Edu-Data)

> **Para compañeros que retoman el proyecto:** lean primero la sección **"Estado actual"** para saber qué está terminado y qué falta hacer. Luego sigan el orden de las secciones.

---

## Tabla de contenidos

1. [Descripción general](#1-descripción-general)
2. [Estado actual del proyecto](#2-estado-actual-del-proyecto)
3. [Estructura de archivos](#3-estructura-de-archivos)
4. [Cómo ejecutar los scripts Python](#4-cómo-ejecutar-los-scripts-python)
5. [Supuestos metodológicos](#5-supuestos-metodológicos)
6. [Modelo de datos (estrella)](#6-modelo-de-datos-estrella)
7. [Armar el tablero en Power BI — paso a paso](#7-armar-el-tablero-en-power-bi--paso-a-paso)
8. [Medidas DAX — qué hace cada una y dónde usarla](#8-medidas-dax--qué-hace-cada-una-y-dónde-usarla)
9. [Validación estadística (ANOVA)](#9-validación-estadística-anova)
10. [Requerimientos analíticos cubiertos](#10-requerimientos-analíticos-cubiertos)
11. [Limitaciones del dataset](#11-limitaciones-del-dataset)
12. [Estructura sugerida del informe](#12-estructura-sugerida-del-informe)

---

## 1. Descripción general

El proyecto implementa un flujo completo de análisis de datos sobre el rendimiento académico de **480 estudiantes** registrados en un sistema de aprendizaje virtual (LMS). El flujo va de extremo a extremo:

```
xAPI-Edu-Data.csv  →  ETL (Python)  →  Modelo estrella (CSV)  →  Power BI + DAX  →  ANOVA (Python)
```

**Objetivo:** construir un tablero ejecutivo en Power BI que responda 10 preguntas analíticas sobre desempeño, deserción, género, programas, asistencia y factores de éxito, respaldado por pruebas estadísticas formales.

---

## 2. Estado actual del proyecto

### ✅ Terminado

| Componente | Archivo | Estado |
|---|---|---|
| Script ETL | `01_etl.py` | Completo y probado |
| Script ANOVA | `02_anova.py` | Completo y probado |
| Medidas DAX | `medidas_dax.dax` | 30+ medidas, todas escritas |
| Archivos del modelo estrella | `salida/Dim_*.csv` + `salida/Fact_Desempeno.csv` | Generados |
| Resultados estadísticos | `salida/resultados_anova.csv`, `salida/chi_cuadrado.csv`, `salida/tukey_*.csv` | Generados |

### ⏳ Pendiente (lo que falta hacer)

| Tarea | Responsable sugerido | Referencia |
|---|---|---|
| Importar los 8 CSV en Power BI | — | Sección 7, Paso 1 |
| Crear las 7 relaciones entre tablas | — | Sección 7, Paso 2 |
| Crear la tabla `_Medidas` y pegar el DAX | — | Sección 7, Paso 3 |
| Configurar el orden de columnas | — | Sección 7, Paso 4 |
| Construir las 4 páginas del tablero | — | Sección 7, Pasos 5–8 |
| Redactar el informe escrito | — | Sección 12 |

---

## 3. Estructura de archivos

```
proyecto_final_powerbi/
│
├── xAPI-Edu-Data.csv          ← Dataset original de Kaggle (NO modificar)
│
├── 01_etl.py                  ← Script ETL: lee el CSV, limpia, genera el modelo estrella
├── 02_anova.py                ← Script estadístico: ANOVA, Tukey, chi-cuadrado
├── medidas_dax.dax            ← Todas las medidas DAX listas para copiar en Power BI
├── README.md                  ← Este archivo
│
└── salida/                    ← Generada automáticamente por 01_etl.py y 02_anova.py
    ├── Fact_Desempeno.csv     ← Tabla de hechos (480 filas, 22 columnas)
    ├── Dim_Facultad.csv       ← 3 filas
    ├── Dim_Programa.csv       ← 11 filas
    ├── Dim_Materia.csv        ← 12 materias
    ├── Dim_Semestre.csv       ← 2 semestres
    ├── Dim_Cohorte.csv        ← 3 secciones (A, B, C)
    ├── Dim_Genero.csv         ← 2 géneros
    ├── Dim_Estudiante.csv     ← 480 filas (datos demográficos)
    ├── dataset_limpio.csv     ← Tabla plana para ANOVA (no se importa en Power BI)
    ├── resultados_anova.csv   ← Resultados de todas las pruebas ANOVA
    ├── chi_cuadrado.csv       ← Resultados chi-cuadrado
    ├── tukey_Manos_Levantadas.csv
    ├── tukey_Recursos_Visitados.csv
    ├── tukey_Anuncios_Vistos.csv
    ├── tukey_Participacion_Foros.csv
    └── anova_dos_vias.csv
```

> **Nota:** `dataset_limpio.csv` y los archivos `tukey_*.csv` / `anova_*.csv` / `chi_cuadrado.csv` son para el análisis estadístico, **no** se importan en Power BI (excepto `resultados_anova.csv` si quieren mostrar la tabla en el tablero).

---

## 4. Cómo ejecutar los scripts Python

### Requisitos previos

```bash
pip install pandas numpy scipy statsmodels
```

### Paso 1 — Descargar el dataset

Descargar `xAPI-Edu-Data.csv` desde:
https://www.kaggle.com/datasets/aljarah/xAPI-Edu-Data

Colocarlo en la raíz del proyecto (junto a `01_etl.py`).

### Paso 2 — Ejecutar el ETL

```bash
python 01_etl.py --entrada xAPI-Edu-Data.csv --salida salida
```

Genera todos los `Dim_*.csv` y `Fact_Desempeno.csv` en la carpeta `salida/`.

### Paso 3 — Ejecutar el análisis estadístico

```bash
python 02_anova.py --entrada salida/dataset_limpio.csv --salida salida
```

Genera `resultados_anova.csv`, `chi_cuadrado.csv`, los 4 `tukey_*.csv` y `anova_dos_vias.csv`.

> Si los archivos de `salida/` ya existen (están en el repositorio), **no es necesario volver a ejecutar los scripts** a menos que modifiquen el dataset o el ETL.

---

## 5. Supuestos metodológicos

El dataset original no tiene notas numéricas, ni facultades, ni deserción explícita. Se aplicaron los siguientes mapeos, que **deben declararse como supuestos en el informe**:

| Concepto del enunciado | Campo del dataset | Criterio aplicado |
|---|---|---|
| Materia | `Topic` | 12 materias, directo |
| Semestre | `Semester` (F / S) | F = Primer semestre, S = Segundo semestre |
| Nota numérica | `Class` (L / M / H) | L = 60, M = 80, H = 95 (punto medio de cada banda oficial) |
| Facultad | `StageID` (3 niveles) | lowerlevel → Nivel Básico, MiddleSchool → Nivel Medio, HighSchool → Nivel Superior |
| Programa | `GradeID` (grados G-02 a G-12) | Proxy del nivel de grado escolar |
| Cohorte | `SectionID` (A / B / C) | Sección del aula como proxy de cohorte |
| Reprobación | `Class = L` | Nivel Bajo = reprobado |
| Sobresaliente | `Class = H` | Nivel Alto = sobresaliente |
| Ausencias | `StudentAbsenceDays` | Under-7 = menos de 7 ausencias, Above-7 = 7 o más |
| Deserción | No existe en el dataset | **Proxy:** rendimiento Bajo (L) **y** 7 o más ausencias = "riesgo de deserción" |

---

## 6. Modelo de datos (estrella)

El modelo tiene una tabla de hechos central relacionada con 7 dimensiones. Todas las relaciones son de **uno a muchos (1:*)** desde la dimensión hacia la tabla de hechos, con **filtro unidireccional**.

```
Dim_Facultad   ──┐
Dim_Programa   ──┤
Dim_Materia    ──┤
Dim_Semestre   ──┼──► Fact_Desempeno
Dim_Cohorte    ──┤
Dim_Genero     ──┤
Dim_Estudiante ──┘
```

### Columnas clave de Fact_Desempeno

| Columna | Tipo | Descripción |
|---|---|---|
| `ID_Estudiante` | Entero | Clave foránea → Dim_Estudiante |
| `SK_Facultad` | Entero | Clave foránea → Dim_Facultad |
| `SK_Programa` | Entero | Clave foránea → Dim_Programa |
| `SK_Materia` | Entero | Clave foránea → Dim_Materia |
| `SK_Semestre` | Entero | Clave foránea → Dim_Semestre |
| `SK_Cohorte` | Entero | Clave foránea → Dim_Cohorte |
| `SK_Genero` | Entero | Clave foránea → Dim_Genero |
| `Nota_Aproximada` | Decimal | 60 / 80 / 95 — para promedios |
| `Nota_Ordinal` | Entero | 1 / 2 / 3 — para ordenar niveles |
| `Nivel_Rendimiento` | Texto | Bajo / Medio / Alto |
| `Manos_Levantadas` | Entero | 0–100 |
| `Recursos_Visitados` | Entero | 0–100 |
| `Anuncios_Vistos` | Entero | 0–100 |
| `Participacion_Foros` | Entero | 0–100 |
| `Indice_Participacion` | Decimal | Promedio de los 4 anteriores |
| `Es_Reprobado` | 0/1 | 1 si Nivel = Bajo |
| `Es_Sobresaliente` | 0/1 | 1 si Nivel = Alto |
| `Es_Riesgo_Desercion` | 0/1 | 1 si Nivel = Bajo y ausencias ≥ 7 |

---

## 7. Armar el tablero en Power BI — paso a paso

### Paso 1 — Importar los 8 archivos CSV

1. Abrir **Power BI Desktop**.
2. Clic en **Inicio → Obtener datos → Texto/CSV**.
3. Importar estos 8 archivos de la carpeta `salida/` (uno por uno):
   - `Fact_Desempeno.csv`
   - `Dim_Facultad.csv`
   - `Dim_Programa.csv`
   - `Dim_Materia.csv`
   - `Dim_Semestre.csv`
   - `Dim_Cohorte.csv`
   - `Dim_Genero.csv`
   - `Dim_Estudiante.csv`
4. En el diálogo de cada archivo, verificar que el **delimitador sea coma** y la **codificación UTF-8**. Clic en **Cargar** (no en Transformar datos, a menos que noten algo raro).

> Opcional: también pueden importar `resultados_anova.csv` si quieren mostrar la tabla de ANOVA en la Página 4.

---

### Paso 2 — Crear las relaciones entre tablas

1. Ir a la vista **Modelo** (ícono de diagrama en el panel izquierdo).
2. Crear las siguientes 7 relaciones arrastrando la columna de la dimensión hacia la tabla de hechos:

| Desde (dimensión) | Columna | Hacia (hechos) | Columna |
|---|---|---|---|
| `Dim_Facultad` | `SK_Facultad` | `Fact_Desempeno` | `SK_Facultad` |
| `Dim_Programa` | `SK_Programa` | `Fact_Desempeno` | `SK_Programa` |
| `Dim_Materia` | `SK_Materia` | `Fact_Desempeno` | `SK_Materia` |
| `Dim_Semestre` | `SK_Semestre` | `Fact_Desempeno` | `SK_Semestre` |
| `Dim_Cohorte` | `SK_Cohorte` | `Fact_Desempeno` | `SK_Cohorte` |
| `Dim_Genero` | `SK_Genero` | `Fact_Desempeno` | `SK_Genero` |
| `Dim_Estudiante` | `ID_Estudiante` | `Fact_Desempeno` | `ID_Estudiante` |

3. Para cada relación, verificar en el panel de propiedades:
   - **Cardinalidad:** Uno a varios (1:*)
   - **Dirección del filtro cruzado:** Única (de la dimensión hacia los hechos)

---

### Paso 3 — Crear la tabla de medidas y pegar el DAX

1. En la vista **Datos**, ir a **Inicio → Especificar datos**.
2. Crear una tabla con una sola columna vacía y nombrarla `_Medidas`. Confirmar.
3. Seleccionar la tabla `_Medidas` en el panel de campos.
4. Ir a **Inicio → Nueva medida** y crear la primera medida. Luego repetir para cada una, o usar el método más rápido:
   - Abrir el archivo `medidas_dax.dax` en cualquier editor de texto.
   - Copiar el bloque de código de cada medida.
   - En Power BI, con `_Medidas` seleccionada, clic en **Nueva medida** y pegar.

> **Consejo:** crear las medidas de la sección `// Base` primero, porque las demás dependen de ellas (`Promedio Nota`, `Total Estudiantes`).

---

### Paso 4 — Configurar el orden de columnas

Dos columnas necesitan ordenarse por otra columna para que los gráficos salgan bien:

**a) Semestre (orden cronológico)**
1. En la vista **Datos**, seleccionar la tabla `Dim_Semestre`.
2. Clic en la columna `Semestre`.
3. En la cinta superior: **Herramientas de columna → Ordenar por columna → Semestre_Orden**.

**b) Nivel de rendimiento (orden lógico: Bajo → Medio → Alto)**
1. En la vista **Datos**, seleccionar la tabla `Fact_Desempeno`.
2. Clic en la columna `Nivel_Rendimiento`.
3. En la cinta superior: **Herramientas de columna → Ordenar por columna → Nota_Ordinal**.

---

### Paso 5 — Página 1: Resumen ejecutivo

**Objetivo:** vista de alto nivel con los KPIs principales y segmentadores globales.

**Segmentadores (filtros globales, colocar en la parte superior o lateral):**
- `Dim_Facultad[Facultad]`
- `Dim_Semestre[Semestre]`
- `Dim_Genero[Genero]`
- `Dim_Cohorte[Cohorte]`

**Visualizaciones:**

| Visual | Tipo | Campos |
|---|---|---|
| Total de estudiantes | Tarjeta | Medida: `Total Estudiantes` |
| Promedio de nota | Tarjeta | Medida: `Promedio Nota` |
| Tasa de reprobación | Tarjeta | Medida: `Tasa Reprobacion` (formato %) |
| Tasa de riesgo de deserción | Tarjeta | Medida: `Tasa Desercion` (formato %) |
| % Sobresalientes | Tarjeta | Medida: `Pct Sobresalientes` (formato %) |
| Distribución de niveles | Gráfico de dona | Eje: `Fact_Desempeno[Nivel_Rendimiento]` · Valores: `Total Estudiantes` |

---

### Paso 6 — Página 2: Desempeño académico

**Cubre:** Req. 1, 5, 6, 8.

| Visual | Tipo | Configuración |
|---|---|---|
| **Req. 1** Promedio por materia y semestre | Matriz | Filas: `Dim_Materia[Materia]` · Columnas: `Dim_Semestre[Semestre]` · Valores: `Promedio Nota` · Formato condicional en Valores: escala de color |
| **Req. 5** Tendencia por semestre | Gráfico de columnas + línea | Eje X: `Dim_Semestre[Semestre]` · Columnas: `Promedio Nota` · Línea: `Promedio Nota` · Agregar tarjeta con `Tendencia Texto` al lado |
| **Req. 6** Top 10 reprobación | Barras horizontales | Eje Y: `Dim_Materia[Materia]` · Valores: `Tasa Reprobacion` · **Filtro del visual → Materia → Top N = 10 por `Tasa Reprobacion`** · Formato condicional por `Color Semaforo Reprobacion` |
| **Req. 8** Sobresalientes | Tabla | Columnas: `Dim_Materia[Materia]`, `Estudiantes Sobresalientes`, `Pct Sobresalientes` · Ordenar por `Estudiantes Sobresalientes` descendente |

---

### Paso 7 — Página 3: Comparativas

**Cubre:** Req. 2, 3, 4, 9.

| Visual | Tipo | Configuración |
|---|---|---|
| **Req. 2** Deserción por facultad | Barras verticales | Eje X: `Dim_Facultad[Facultad]` · Valores: `Tasa Desercion` (formato %) |
| **Req. 3** Desempeño por género | Columnas agrupadas | Eje X: `Dim_Genero[Genero]` · Valores: `Promedio Nota` · Agregar tarjeta con `Brecha de Genero (F - M)` |
| **Req. 4** Comparativa entre programas | Barras horizontales + tabla | Eje Y: `Dim_Programa[Programa]` · Valores: `Promedio Nota` · Agregar columna `Ranking Programa` en tooltip |
| **Req. 9** Distribución por cohorte | Barras 100% apiladas | Eje X: `Dim_Cohorte[Cohorte]` · Leyenda: `Fact_Desempeno[Nivel_Rendimiento]` · Valores: `Total Estudiantes` |

---

### Paso 8 — Página 4: Factores de éxito

**Cubre:** Req. 7, 10.

| Visual | Tipo | Configuración |
|---|---|---|
| **Req. 7** Asistencia vs rendimiento | Columnas agrupadas | Eje X: `Fact_Desempeno[Asistencia]` · Valores: `Promedio Nota` · Agregar tarjeta con `Efecto Asistencia (puntos)` |
| **Req. 10a** Participación por nivel | Barras agrupadas | Eje X: `Fact_Desempeno[Nivel_Rendimiento]` · Valores: `Promedio Manos Levantadas`, `Promedio Recursos Visitados`, `Promedio Anuncios Vistos`, `Promedio Participacion Foros` |
| **Req. 10b** Sobresalientes por rango de participación | Columnas | Eje X: `Fact_Desempeno[Rango_Participacion]` · Valores: `Pct Sobresalientes` |
| **Req. 10c** Correlación | Tarjeta | Medida: `Correlacion Participacion vs Nota` |
| **Req. 10d** Tabla ANOVA | Tabla | Importar `resultados_anova.csv` como tabla adicional · Mostrar columnas: `variable`, `factor`, `F`, `p_anova`, `eta2`, `concluye` |

---

## 8. Medidas DAX — qué hace cada una y dónde usarla

Todas las medidas viven en la tabla `_Medidas`. Están agrupadas por tema.

### Grupo 1: Base (crear primero)

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Total Estudiantes` | Conteo distinto de estudiantes | Tarjetas, todos los visuales |
| `Promedio Nota` | Promedio de `Nota_Aproximada` | Matrices, barras, líneas |
| `Promedio Nivel Ordinal` | Promedio de `Nota_Ordinal` (1-3) | Comparaciones ordinales |
| `Promedio Nota Global` | Promedio ignorando todos los filtros de dimensiones | Referencia para comparar |
| `Diferencia vs Promedio Global` | Resta entre `Promedio Nota` y el global | Formato condicional, tooltips |

### Grupo 2: Req. 1 y 5 — Materias y semestres

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Promedio Nota Semestre 1` | Promedio del primer semestre | Comparativa semestral |
| `Promedio Nota Semestre 2` | Promedio del segundo semestre | Comparativa semestral |
| `Variacion Semestral` | Diferencia S2 − S1 | Tarjeta de tendencia |
| `Tendencia Texto` | Texto dinámico: ▲ Mejora / ▼ Deterioro / ● Estable | Tarjeta en Pág. 2 |

### Grupo 3: Req. 2 — Deserción

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Estudiantes en Riesgo de Desercion` | Suma de `Es_Riesgo_Desercion` | Barras por facultad |
| `Tasa Desercion` | Riesgo / Total (%) | Tarjeta y barras Pág. 3 |

### Grupo 4: Req. 3 — Género

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Promedio Nota Femenino` | Promedio solo para género femenino | Columnas agrupadas Pág. 3 |
| `Promedio Nota Masculino` | Promedio solo para género masculino | Columnas agrupadas Pág. 3 |
| `Brecha de Genero (F - M)` | Diferencia entre ambos promedios | Tarjeta Pág. 3 |

### Grupo 5: Req. 6 — Reprobación

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Estudiantes Reprobados` | Suma de `Es_Reprobado` | Tabla y barras |
| `Tasa Reprobacion` | Reprobados / Total (%) | Top 10 barras Pág. 2 |
| `Ranking Reprobacion Materia` | Posición 1–12 según tasa | Tooltip o columna de tabla |
| `Color Semaforo Reprobacion` | Rojo ≥40% / Amarillo ≥25% / Verde | Formato condicional de barras |

### Grupo 6: Req. 7 — Asistencia

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Estudiantes Asistencia Alta` | Conteo con < 7 ausencias | Comparativa |
| `Pct Asistencia Alta` | % de asistencia alta | Tarjeta |
| `Promedio Nota Asistencia Alta` | Promedio de quienes faltan poco | Columnas agrupadas Pág. 4 |
| `Promedio Nota Asistencia Baja` | Promedio de quienes faltan mucho | Columnas agrupadas Pág. 4 |
| `Efecto Asistencia (puntos)` | Diferencia entre ambos promedios | Tarjeta Pág. 4 |

### Grupo 7: Req. 8 — Sobresalientes

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Estudiantes Sobresalientes` | Suma de `Es_Sobresaliente` | Tabla Pág. 2 |
| `Pct Sobresalientes` | % sobresalientes sobre total | Columnas Pág. 4 |

### Grupo 8: Req. 4 y 9 — Comparativas

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Distribucion Nivel %` | % de cada nivel dentro del programa o cohorte | Barras 100% apiladas Pág. 3 |
| `Ranking Programa` | Posición del programa por promedio | Tooltip en barras Pág. 3 |

### Grupo 9: Req. 10 — Factores de éxito

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Promedio Manos Levantadas` | Promedio del indicador | Barras agrupadas Pág. 4 |
| `Promedio Recursos Visitados` | Promedio del indicador | Barras agrupadas Pág. 4 |
| `Promedio Anuncios Vistos` | Promedio del indicador | Barras agrupadas Pág. 4 |
| `Promedio Participacion Foros` | Promedio del indicador | Barras agrupadas Pág. 4 |
| `Promedio Indice Participacion` | Promedio del índice combinado | Tarjeta general |
| `Correlacion Participacion vs Nota` | Correlación de Pearson entre índice y nota ordinal | Tarjeta Pág. 4 |
| `Pct Alto Rendimiento por Rango Participacion` | % sobresalientes por rango | Columnas Pág. 4 |

### Grupo 10: Presentación

| Medida | Qué calcula | Dónde se usa |
|---|---|---|
| `Titulo Materia` | Texto dinámico con el semestre filtrado | Título del visual de materias |
| `Color Semaforo Reprobacion` | Código de color HEX | Formato condicional de barras |

---

## 9. Validación estadística (ANOVA)

Los resultados de los scripts están en `salida/`. Esta sección explica cómo leerlos.

### Hipótesis general

- **H₀:** las medias de los grupos comparados son iguales.
- **H₁:** al menos un grupo tiene media diferente.
- **Nivel de significancia α = 0.05.**

### Cómo interpretar `resultados_anova.csv`

| Columna | Qué significa |
|---|---|
| `variable` | La columna que se analiza (ej: `Manos_Levantadas`) |
| `factor` | La variable de agrupación (ej: `Nivel_Rendimiento`) |
| `F` | Estadístico F del ANOVA |
| `p_anova` | Si < 0.05, hay diferencias significativas → rechazar H₀ |
| `eta2` | Tamaño del efecto: < 0.06 pequeño, 0.06–0.14 mediano, > 0.14 grande |
| `levene_p` | Si < 0.05, las varianzas no son iguales → apoyarse en Kruskal-Wallis |
| `kruskal_H` y `p_kruskal` | Alternativa no paramétrica (usar cuando Levene falla) |
| `concluye` | Resumen automático del resultado |

### Cómo interpretar los archivos `tukey_*.csv`

Muestran qué pares de grupos difieren entre sí (Bajo vs Medio, Bajo vs Alto, Medio vs Alto). La columna `reject` indica si el par es significativamente diferente (`True`) o no (`False`).

### Prueba chi-cuadrado (`chi_cuadrado.csv`)

Para variables categóricas (asistencia, género, etc.) vs nivel de rendimiento.
- `V_Cramer` mide la fuerza de asociación: < 0.1 débil, 0.1–0.3 moderada, > 0.3 fuerte.

---

## 10. Requerimientos analíticos cubiertos

| # | Requerimiento | Página Power BI | Medida principal | Estado |
|---|---|---|---|---|
| 1 | Promedio de notas por materia y semestre | Pág. 2 | `Promedio Nota` | ✅ |
| 2 | Tasa de deserción por facultad | Pág. 3 | `Tasa Desercion` | ✅ |
| 3 | Análisis de desempeño por género | Pág. 3 | `Brecha de Genero (F - M)` | ✅ |
| 4 | Comparativa entre programas | Pág. 3 | `Ranking Programa` | ✅ |
| 5 | Tendencias por semestre | Pág. 2 | `Tendencia Texto` | ✅ |
| 6 | Top 10 asignaturas con mayor reprobación | Pág. 2 | `Tasa Reprobacion` | ✅ |
| 7 | Relación entre asistencia y rendimiento | Pág. 4 | `Efecto Asistencia (puntos)` | ✅ |
| 8 | Estudiantes sobresalientes | Pág. 2 | `Pct Sobresalientes` | ✅ |
| 9 | Comparativa entre cohortes | Pág. 3 | `Distribucion Nivel %` | ✅ |
| 10 | Factores que influyen en el éxito | Pág. 4 | `Correlacion Participacion vs Nota` | ✅ |

---

## 11. Limitaciones del dataset

Declarar estas limitaciones en el informe final:

1. **Sin notas numéricas reales.** La variable `Class` solo tiene tres valores (L/M/H). Los valores 60/80/95 son puntos de referencia aproximados, no notas reales.
2. **Sin deserción explícita.** El "riesgo de deserción" es un proxy basado en dos condiciones, no un dato registrado.
3. **Solo dos semestres.** El análisis de tendencias tiene muy poco alcance temporal.
4. **Solo 480 registros.** Muestra pequeña para generalizaciones; los resultados estadísticos son válidos internamente pero no extrapolables.
5. **Facultad, programa y cohorte son proxies.** El dataset no tiene estas variables; se derivaron de campos de nivel escolar y sección.
6. **Nota ordinal en ANOVA.** El ANOVA sobre `Nota_Aproximada` asume continuidad en una variable que solo toma 3 valores discretos; los resultados deben interpretarse con cautela.

---

## 12. Estructura sugerida del informe

1. **Portada y datos del equipo**
2. **Problema y objetivo** — qué pregunta responde el análisis
3. **Dataset y fuente** — Kaggle, 480 registros, 17 columnas originales
4. **Supuestos metodológicos** — tabla de la sección 5 de este README
5. **ETL** — descripción del proceso (extracción, limpieza, campos derivados, modelo estrella)
6. **Modelo semántico y DAX** — diagrama de relaciones + descripción de las medidas principales
7. **Tablero Power BI** — captura de cada página con descripción de cada visual
8. **Validación estadística** — hipótesis, resultados ANOVA, Tukey, chi-cuadrado, tamaño del efecto
9. **Conclusiones** — qué factores impactan más el rendimiento, hallazgos por género, facultad, etc.
10. **Limitaciones** — sección 11 de este README
11. **Referencias** — dataset Kaggle, librerías Python usadas

---

*Proyecto desarrollado con Python 3.x · pandas · numpy · scipy · statsmodels · Power BI Desktop*
