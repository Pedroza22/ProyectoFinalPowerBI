"""
02_anova.py - Validacion estadistica (ANOVA) sobre el dataset limpio generado por 01_etl.py

Pruebas:
  A) ANOVA de una via: cada indicador de participacion (Manos_Levantadas, Recursos_Visitados,
     Anuncios_Vistos, Participacion_Foros) segun Nivel_Rendimiento (Bajo / Medio / Alto)
     -> normalidad (Shapiro por grupo), homogeneidad (Levene), ANOVA, eta cuadrado,
        Kruskal-Wallis (alternativa no parametrica) y Tukey HSD post hoc.
  B) ANOVA de una via: Nota_Aproximada por Materia, por Programa, por Facultad y por Genero(t).
  C) ANOVA de dos vias: Indice_Participacion ~ Nivel_Rendimiento * Genero.
  D) Chi-cuadrado para variables categoricas vs rendimiento (asistencia, acudiente, etc.)

Uso:
    python 02_anova.py --entrada salida/dataset_limpio.csv --salida salida
Requiere: pandas, scipy, statsmodels
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd

ALFA = 0.05
METRICAS = ["Manos_Levantadas", "Recursos_Visitados", "Anuncios_Vistos", "Participacion_Foros"]


def anova_una_via(df, y, factor):
    grupos = [g[y].values for _, g in df.groupby(factor)]
    nombres = [n for n, _ in df.groupby(factor)]
    sh = {n: stats.shapiro(g).pvalue if 3 <= len(g) <= 5000 else np.nan for n, g in zip(nombres, grupos)}
    lev = stats.levene(*grupos).pvalue
    f, p = stats.f_oneway(*grupos)
    h, p_kw = stats.kruskal(*grupos)
    modelo = ols(f"{y} ~ C({factor})", data=df).fit()
    tabla = sm.stats.anova_lm(modelo, typ=2)
    ss_between = tabla["sum_sq"].iloc[0]
    ss_total = tabla["sum_sq"].sum()
    eta2 = ss_between / ss_total
    return {
        "variable": y, "factor": factor, "k_grupos": len(grupos),
        "F": round(f, 4), "p_anova": p, "eta2": round(eta2, 4),
        "levene_p": lev, "kruskal_H": round(h, 4), "p_kruskal": p_kw,
        "shapiro_p_min": np.nanmin(list(sh.values())),
        "concluye": "Diferencias significativas" if p < ALFA else "Sin evidencia de diferencias",
    }


def interpreta_eta(e):
    return "pequeno" if e < 0.06 else "mediano" if e < 0.14 else "grande"


def main(entrada, salida):
    df = pd.read_csv(entrada)
    os.makedirs(salida, exist_ok=True)
    out = []

    print("=" * 70)
    print("A) ANOVA: participacion segun nivel de rendimiento")
    for m in METRICAS:
        r = anova_una_via(df, m, "Nivel_Rendimiento")
        r["efecto"] = interpreta_eta(r["eta2"])
        out.append(r)
        print(f"  {m}: F={r['F']}  p={r['p_anova']:.2e}  eta2={r['eta2']} ({r['efecto']})  "
              f"Levene p={r['levene_p']:.3f}  Kruskal p={r['p_kruskal']:.2e}")
        tk = pairwise_tukeyhsd(df[m], df["Nivel_Rendimiento"], alpha=ALFA)
        print(tk.summary())
        pd.DataFrame(tk._results_table.data[1:], columns=tk._results_table.data[0]).to_csv(
            os.path.join(salida, f"tukey_{m}.csv"), index=False)

    print("=" * 70)
    print("B) ANOVA: Nota_Aproximada segun Materia / Programa / Facultad")
    for fac in ["Materia", "Programa", "Facultad"]:
        r = anova_una_via(df, "Nota_Aproximada", fac)
        r["efecto"] = interpreta_eta(r["eta2"])
        out.append(r)
        print(f"  Nota ~ {fac}: F={r['F']}  p={r['p_anova']:.4f}  eta2={r['eta2']} ({r['efecto']})")

    t, p = stats.ttest_ind(df.loc[df.Genero == "Femenino", "Nota_Aproximada"],
                           df.loc[df.Genero == "Masculino", "Nota_Aproximada"], equal_var=False)
    print(f"  Nota ~ Genero (t de Welch, equivale a ANOVA de 2 grupos): t={t:.3f} p={p:.2e}")
    out.append({"variable": "Nota_Aproximada", "factor": "Genero", "k_grupos": 2, "F": round(t ** 2, 4),
                "p_anova": p, "concluye": "Diferencias significativas" if p < ALFA else "Sin evidencia de diferencias"})

    print("=" * 70)
    print("C) ANOVA de dos vias: Indice_Participacion ~ Nivel_Rendimiento * Genero")
    m2 = ols("Indice_Participacion ~ C(Nivel_Rendimiento) * C(Genero)", data=df).fit()
    t2 = sm.stats.anova_lm(m2, typ=2)
    print(t2.round(4).to_string())
    t2.to_csv(os.path.join(salida, "anova_dos_vias.csv"))

    print("=" * 70)
    print("D) Chi-cuadrado: variables categoricas vs Nivel_Rendimiento")
    chi_rows = []
    for c in ["Asistencia", "Genero", "Acudiente_Responde_Encuesta", "Satisfaccion_Acudiente",
              "Acudiente", "Facultad", "Semestre"]:
        ct = pd.crosstab(df[c], df["Nivel_Rendimiento"])
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
        chi_rows.append({"variable": c, "chi2": round(chi2, 3), "gl": dof, "p": p, "V_Cramer": round(v, 3)})
        print(f"  {c}: chi2={chi2:.2f} gl={dof} p={p:.2e} V de Cramer={v:.3f}")
    pd.DataFrame(chi_rows).to_csv(os.path.join(salida, "chi_cuadrado.csv"), index=False)

    pd.DataFrame(out).to_csv(os.path.join(salida, "resultados_anova.csv"), index=False)
    print("\nResultados guardados en", salida)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="salida/dataset_limpio.csv")
    ap.add_argument("--salida", default="salida")
    a = ap.parse_args()
    main(a.entrada, a.salida)
