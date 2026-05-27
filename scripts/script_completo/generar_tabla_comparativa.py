"""
Genera tabla_resultados_comparativa.csv y tabla_resultados_comparativa.tex
comparando RDD1 (sharp, running variable = edad) con RDD2 (proxy SISFOH PCA).
"""
import os
import pandas as pd

DATA_DIR  = r"C:\Users\Usuario\OneDrive\Imágenes\pension-65-digital-wallet-main\data\clean"
OUT_CSV   = os.path.join(DATA_DIR, "tabla_resultados_comparativa.csv")
OUT_TEX   = os.path.join(DATA_DIR, "tabla_resultados_comparativa.tex")


def stars(est, se):
    t = abs(est / se) if se > 0 else 0
    if t > 2.576: return "***"
    if t > 1.960: return "**"
    if t > 1.645: return "*"
    return ""


def fmt_est(est, se):
    sign = "+" if est >= 0 else ""
    return f"{sign}{est:.4f}{stars(est, se)}"


def fmt_ci(lo, hi):
    return f"[{lo:.4f},\\ {hi:.4f}]"


# ── Cargar resultados ──────────────────────────────────────────────────────
rdd1_df = pd.read_csv(os.path.join(DATA_DIR, "main_results.csv"))
rdd2_df = pd.read_csv(os.path.join(DATA_DIR, "rdd2_results.csv"))

r1 = (rdd1_df[rdd1_df["specification"] == "MAIN_baseline"]
      .set_index("outcome"))
r2 = (rdd2_df[rdd2_df["specification"] == "RDD2_SISFOH_baseline"]
      .set_index("outcome"))

OUTCOMES = ["TIENE_BILLETERA", "USA_BILLETERA"]

# ── Construir DataFrame comparativo ───────────────────────────────────────
rows = []
for out in OUTCOMES:
    o1, o2 = r1.loc[out], r2.loc[out]
    rows.append({
        "outcome":           out,
        "rdd1_estimate":     round(float(o1["estimate"]),    4),
        "rdd1_se":           round(float(o1["se_robust"]),   4),
        "rdd1_ci_lower":     round(float(o1["ci_lower"]),    4),
        "rdd1_ci_upper":     round(float(o1["ci_upper"]),    4),
        "rdd1_bandwidth_yr": round(float(o1["bandwidth"]),   2),
        "rdd1_N_eff":        int(o1["N_eff"]),
        "rdd1_method":       o1["method"],
        "rdd2_estimate":     round(float(o2["estimate"]),    4),
        "rdd2_se":           round(float(o2["se_robust"]),   4),
        "rdd2_ci_lower":     round(float(o2["ci_lower"]),    4),
        "rdd2_ci_upper":     round(float(o2["ci_upper"]),    4),
        "rdd2_bandwidth_sd": round(float(o2["bandwidth"]),   3),
        "rdd2_N_eff":        int(o2["N_eff"]),
        "rdd2_method":       o2["method"],
    })

df_comp = pd.DataFrame(rows)
df_comp.to_csv(OUT_CSV, index=False, encoding="utf-8")
print(f"Guardado CSV: {OUT_CSV}")
print(df_comp.to_string())

# ── Generar LaTeX ──────────────────────────────────────────────────────────
tb = df_comp[df_comp["outcome"] == "TIENE_BILLETERA"].iloc[0]
ub = df_comp[df_comp["outcome"] == "USA_BILLETERA"].iloc[0]

# Separador de miles sin comas (LaTeX)
def N(n): return f"{n:,}".replace(",", "{,}")

lines = [
    r"% ============================================================",
    r"% Tabla comparativa RDD1 vs. RDD2",
    r"% ENAHO 2024. rdrobust, kernel triangular, HC robust SE.",
    r"% Generada automaticamente por generar_tabla_comparativa.py",
    r"% ============================================================",
    r"\begin{table}[htbp]",
    r"  \centering",
    (r"  \caption{Comparative RDD Estimates: Sharp Age Cutoff (RDD1) vs.\ "
     r"Proxy SISFOH Welfare Index (RDD2)}"),
    r"  \label{tab:rdd_comparativa}",
    r"  \small",
    r"  \begin{tabular}{l cc cc}",
    r"    \toprule",
    (r"    & \multicolumn{2}{c}{\textbf{RDD1: Sharp (Age $\geq 65$)}}"
     r" & \multicolumn{2}{c}{\textbf{RDD2: SISFOH Proxy Index}} \\"),
    r"    \cmidrule(lr){2-3}\cmidrule(lr){4-5}",
    (r"    & \textit{Tiene Billetera} & \textit{Usa Billetera}"
     r" & \textit{Tiene Billetera} & \textit{Usa Billetera} \\"),
    r"    \midrule",
    # Estimate row
    (r"    \textbf{Estimate}"
     f" & {fmt_est(tb['rdd1_estimate'], tb['rdd1_se'])}"
     f" & {fmt_est(ub['rdd1_estimate'], ub['rdd1_se'])}"
     f" & {fmt_est(tb['rdd2_estimate'], tb['rdd2_se'])}"
     f" & {fmt_est(ub['rdd2_estimate'], ub['rdd2_se'])} \\\\"),
    # SE row
    (r"    Robust SE"
     f" & ({tb['rdd1_se']:.4f})"
     f" & ({ub['rdd1_se']:.4f})"
     f" & ({tb['rdd2_se']:.4f})"
     f" & ({ub['rdd2_se']:.4f}) \\\\"),
    # CI row
    (r"    95\% CI"
     f" & {fmt_ci(tb['rdd1_ci_lower'], tb['rdd1_ci_upper'])}"
     f" & {fmt_ci(ub['rdd1_ci_lower'], ub['rdd1_ci_upper'])}"
     f" & {fmt_ci(tb['rdd2_ci_lower'], tb['rdd2_ci_upper'])}"
     f" & {fmt_ci(ub['rdd2_ci_lower'], ub['rdd2_ci_upper'])} \\\\"),
    r"    \addlinespace",
    # Bandwidth row
    (r"    Bandwidth ($h$)"
     f" & {tb['rdd1_bandwidth_yr']:.2f} yrs"
     f" & {ub['rdd1_bandwidth_yr']:.2f} yrs"
     f" & {tb['rdd2_bandwidth_sd']:.3f} SD"
     f" & {ub['rdd2_bandwidth_sd']:.3f} SD \\\\"),
    # N_eff row
    (r"    $N_{\mathrm{eff}}$"
     f" & ${N(tb['rdd1_N_eff'])}$"
     f" & ${N(ub['rdd1_N_eff'])}$"
     f" & ${N(tb['rdd2_N_eff'])}$"
     f" & ${N(ub['rdd2_N_eff'])}$ \\\\"),
    r"    \midrule",
    r"    \multicolumn{5}{l}{\textit{Design details}} \\",
    (r"    Running variable"
     r" & \multicolumn{2}{c}{Age (years), $c = 65$}"
     r" & \multicolumn{2}{c}{SISFOH proxy index, $c = 1.668$} \\"),
    (r"    Sample"
     r" & \multicolumn{2}{c}{Full ENAHO 2024 ($N=113{,}755$)}"
     r" & \multicolumn{2}{c}{Adults $\geq 65$ ($N=14{,}088$)} \\"),
    (r"    PCA variables"
     r" & \multicolumn{2}{c}{---}"
     r" & \multicolumn{2}{c}{10 (F\&P 2001 + durables)} \\"),
    (r"    PC1 var.\ explained"
     r" & \multicolumn{2}{c}{---}"
     r" & \multicolumn{2}{c}{31.4\%} \\"),
    (r"    Estimator"
     r" & \multicolumn{4}{c}{\texttt{rdrobust},"
     r" triangular kernel, MSE-optimal $h$, HC robust SE} \\"),
    r"    \bottomrule",
    r"  \end{tabular}",
    r"  \begin{minipage}{\linewidth}",
    r"    \smallskip\footnotesize",
    r"    \textit{Notes:} Robust standard errors in parentheses.",
    r"    *** $p<0.01$, ** $p<0.05$, * $p<0.10$.",
    (r"    RDD1 uses the full ENAHO 2024 sample; the running variable is age"
     r" in years centered at 65 (ITT of crossing the Pens\'ion~65 eligibility threshold)."),
    (r"    RDD2 restricts to adults $\geq 65$ and uses a proxy SISFOH welfare index"
     r" constructed via PCA on 10 predetermined housing and durable-goods variables"
     r" from ENAHO 2024 (modules 01 and 18); the index is standardized and centered"
     r" at the cutoff separating the estimated extreme-poor from the non-extreme-poor."),
    (r"    Bandwidth units: years (RDD1) and standard deviations of the proxy"
     r" index (RDD2). Source: ENAHO 2024 microdata (INEI)."),
    r"  \end{minipage}",
    r"\end{table}",
]

latex_str = "\n".join(lines)

with open(OUT_TEX, "w", encoding="utf-8") as f:
    f.write(latex_str)

print(f"\nGuardado LaTeX: {OUT_TEX}")
print("\n--- Preview LaTeX ---")
print(latex_str)
