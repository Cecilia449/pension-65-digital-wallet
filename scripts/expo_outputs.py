"""
expo_outputs.py — Genera todos los outputs para la exposición parcial de tesis.
Pensión 65 × Billetera Digital — RDD Paper, ENAHO 2024.
Ejecutar desde la raíz del repo: python scripts/expo_outputs.py
"""
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

REPO_ROOT  = Path(__file__).resolve().parent.parent
DATA_DIR   = REPO_ROOT / "data" / "clean"
TABLES_DIR = REPO_ROOT / "paper" / "tables"
FIGURES_DIR= REPO_ROOT / "paper" / "figures"
PAPER_DIR  = REPO_ROOT / "paper"

for d in (TABLES_DIR, FIGURES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Palette ──────────────────────────────────────────────────────────────────
C_ABOVE = "#b2182b"   # rojo — above threshold (>=65)
C_BELOW = "#2166ac"   # azul — below threshold (<65)
C_P1    = "#d73027"
C_P2    = "#fc8d59"
C_P3    = "#4dac26"

# ── Cargar datos ─────────────────────────────────────────────────────────────
print("=" * 60)
print("Cargando main_dataset.csv...")
df = pd.read_csv(DATA_DIR / "main_dataset.csv", low_memory=False)
print(f"  N = {len(df):,}  cols = {df.shape[1]}")

# Subconjuntos reutilizables
above = df[df["treat"] == 1].copy()
below = df[df["treat"] == 0].copy()
recep = df[df["RECIBE_P65_PERSONA"] == 1].copy()

# ═════════════════════════════════════════════════════════════════════════════
# 1. TABLE 1 — Estadísticas descriptivas
# ═════════════════════════════════════════════════════════════════════════════
print("\n[1] Generando table_1_summary_expo.tex ...")

VARS = [
    ("TIENE_BILLETERA",   "Tiene billetera digital (tenencia o uso)"),
    ("USA_BILLETERA",     "Usa billetera digital (solo uso activo)"),
    ("INTERNET_HOGAR",    "Internet en el hogar"),
    ("SMARTPHONE",        "Smartphone en el hogar"),
    ("POBREZA",           "Pobreza monetaria INEI (1=ext, 2=pob, 3=no pob)"),
    ("INGRESO_PC",        "Ingreso per cápita anual (S/.)"),
    ("NIVEL_EDUCATIVO",   "Nivel educativo (1=sin educ \\ldots 11=posg.)"),
    ("RECIBE_P65_PERSONA","Recibe Pensión 65 (P5567A)"),
]

def fmt(x, decimals=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "---"
    return f"{float(x):.{decimals}f}"

def fmt_n(x):
    try:
        return f"{int(x):,}".replace(",", "{,}")
    except Exception:
        return "---"

rows = []
for col, label in VARS:
    if col not in df.columns:
        rows.append((label, "---", "---", "---", "---", "---", "---"))
        continue
    a = above[col].dropna()
    b = below[col].dropna()
    rows.append((
        label,
        fmt(a.mean()), fmt(a.std()), fmt_n(len(a)),
        fmt(b.mean()), fmt(b.std()), fmt_n(len(b)),
    ))

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Estadísticas Descriptivas — ENAHO 2024}",
    r"\label{tab:descriptivos}",
    r"\begin{threeparttable}",
    r"\begin{tabular}{l ccc ccc}",
    r"\toprule",
    r"& \multicolumn{3}{c}{\textbf{Above Threshold} ($\geq 65$ años)} "
    r"& \multicolumn{3}{c}{\textbf{Below Threshold} ($< 65$ años)} \\",
    r"\cmidrule(lr){2-4} \cmidrule(lr){5-7}",
    r"Variable & Media & D.E. & $N$ & Media & D.E. & $N$ \\",
    r"\midrule",
]

for (label, am, asd, an, bm, bsd, bn) in rows:
    lines.append(f"  {label} & {am} & {asd} & {an} & {bm} & {bsd} & {bn} \\\\")

lines += [
    r"\midrule",
    f"  \\textit{{Total individuos}} & \\multicolumn{{3}}{{c}}{{{fmt_n(len(above))}}} "
    f"& \\multicolumn{{3}}{{c}}{{{fmt_n(len(below))}}} \\\\",
    r"\bottomrule",
    r"\end{tabular}",
    r"\begin{tablenotes}[flushleft]",
    r"\footnotesize",
    r"\item \textit{Notas:} \textbf{Above Threshold} corresponde a personas de 65 años "
    r"o más, elegibles por edad para Pensión 65 ($N=14{,}088$). "
    r"\textbf{Below Threshold} corresponde a personas menores de 65 años ($N=99{,}667$). "
    r"La muestra completa es de $N=113{,}755$ individuos de ENAHO 2024 (Encuesta 966, "
    r"período anual Ene--Dic 2024). "
    r"POBREZA es la clasificación monetaria del INEI (gasto pc vs.\ línea de pobreza); "
    r"no equivale a la categoría SISFOH de Pensión 65. "
    r"D.E. = desviación estándar.",
    r"\end{tablenotes}",
    r"\end{threeparttable}",
    r"\end{table}",
]

content = "\n".join(lines)
out = TABLES_DIR / "table_1_summary_expo.tex"
out.write_text(content, encoding="utf-8")
print(f"  Guardado: {out}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. TABLE 2 — Primera etapa fuzzy RDD
# ═════════════════════════════════════════════════════════════════════════════
print("\n[2] Generando table_first_stage_expo.tex ...")

EDADES_FS = [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 75, 80]

df_edad = df[["EDAD", "RECIBE_P65_PERSONA"]].copy()
df_edad["EDAD"] = pd.to_numeric(df_edad["EDAD"], errors="coerce")

fs_rows = []
for edad in EDADES_FS:
    sub = df_edad[df_edad["EDAD"] == edad]
    n_total = len(sub)
    n_rec   = int(sub["RECIBE_P65_PERSONA"].sum()) if n_total > 0 else 0
    pct     = (n_rec / n_total * 100) if n_total > 0 else 0.0
    fs_rows.append((edad, n_total, n_rec, pct))

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Primera Etapa del Fuzzy RDD: Probabilidad de Recibir Pensión 65 por Edad}",
    r"\label{tab:primera_etapa}",
    r"\begin{threeparttable}",
    r"\begin{tabular}{r ccc}",
    r"\toprule",
    r"Edad & $N$ total & Receptores P65 & \% receptores \\",
    r"\midrule",
]

for (edad, nt, nr, pct) in fs_rows:
    if edad == 65:
        lines.append(r"\midrule")
    lines.append(
        f"  {edad} & {fmt_n(nt)} & {fmt_n(nr)} & {pct:.1f}\\% \\\\"
    )
    if edad == 64:
        pass  # \midrule se pone antes del 65

lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\begin{tablenotes}[flushleft]",
    r"\footnotesize",
    r"\item \textit{Notas:} La tabla muestra la probabilidad de recibir Pensión 65 "
    r"(variable \texttt{P5567A==1} del Módulo 5 de ENAHO 2024) para edades seleccionadas. "
    r"La línea horizontal separa individuos por debajo del corte de edad ($< 65$ años) "
    r"de los elegibles ($\geq 65$ años). "
    r"El salto discontinuo a los 65 años constituye la primera etapa del fuzzy RDD: "
    r"la probabilidad pasa de 0\% en edades 60--64 a valores crecientes desde los 65. "
    r"Fuente: ENAHO 2024 (Encuesta 966).",
    r"\end{tablenotes}",
    r"\end{threeparttable}",
    r"\end{table}",
]

out = TABLES_DIR / "table_first_stage_expo.tex"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"  Guardado: {out}")

# ═════════════════════════════════════════════════════════════════════════════
# 3. TABLE 3 — Resultados fuzzy RDD (valores hardcoded de CLAUDE.md)
# ═════════════════════════════════════════════════════════════════════════════
print("\n[3] Generando table_fuzzy_rdd_expo.tex ...")

# Candidatos: (label, N_bw, FS, FS_F, RF, RF_lo, RF_hi, LATE, LATE_lo, LATE_hi)
CANDS = [
    ("A — Muestra completa",       "27{,}214", "0.104", "310",
     "$-$0.001", "$-$0.020", "$+$0.017",
     "$-$0.012", "$-$0.190", "$+$0.166"),
    ("B — POBREZA$=1$ (ext.~pobre)",  "1{,}213",  "0.258",  "50",
     "$+$0.027", "$-$0.008", "$+$0.063",
     "$+$0.106", "$-$0.032", "$+$0.243"),
    ("C — POBREZA$\\leq 2$ (pobres)", "5{,}119",  "0.202", "138",
     "$+$0.019", "$-$0.006", "$+$0.043",
     "$+$0.093", "$-$0.030", "$+$0.215"),
]

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Resultados del Fuzzy RDD: Primera Etapa, Forma Reducida y LATE}",
    r"\label{tab:fuzzy_rdd}",
    r"\begin{threeparttable}",
    r"\begin{tabular}{l c c c c c}",
    r"\toprule",
    r"& & \multicolumn{2}{c}{\textbf{Primera etapa}} "
    r"& \textbf{Forma reducida} & \textbf{LATE} \\",
    r"\cmidrule(lr){3-4}",
    r"Candidato & $N$ (BW) & Coef. & $F$ & Coef.\ [IC 95\%] & Coef.\ [IC 95\%] \\",
    r"\midrule",
]

for (label, nbw, fs, fsf, rf, rf_lo, rf_hi, late, late_lo, late_hi) in CANDS:
    lines.append(
        f"  {label} & ${nbw}$ & {fs} & {fsf} "
        f"& {rf} [{rf_lo}, {rf_hi}] "
        f"& {late} [{late_lo}, {late_hi}] \\\\"
    )

lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\begin{tablenotes}[flushleft]",
    r"\footnotesize",
    r"\item \textbf{Candidato A} es la estimación primaria del paper: fuzzy RDD sobre la "
    r"muestra completa de ENAHO 2024, sin restricción por pobreza monetaria. "
    r"\textbf{Candidatos B y C} son análisis de heterogeneidad descriptiva post-tratamiento: "
    r"la variable POBREZA es una clasificación monetaria del INEI calculada ex post y "
    r"con probable reverse causality (recibir S/250/mes eleva el gasto del hogar), "
    r"por lo que NO constituyen restricciones de elegibilidad válidas. "
    r"Todas las estimaciones usan kernel triangular, regresión local-lineal y "
    r"errores estándar HC1. Bandwidth $h = 14$ años en torno al corte de edad 65. "
    r"Variable dependiente: \texttt{TIENE\_BILLETERA} (tenencia o uso de billetera digital). "
    r"Instrumento: $\mathbf{1}[\text{Edad} \geq 65]$. "
    r"Tratamiento endógeno: \texttt{P5567A} (recepción individual de Pensión 65).",
    r"\end{tablenotes}",
    r"\end{threeparttable}",
    r"\end{table}",
]

out = TABLES_DIR / "table_fuzzy_rdd_expo.tex"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"  Guardado: {out}")

# ═════════════════════════════════════════════════════════════════════════════
# 4. TABLE 4 — Hallazgo crítico: receptores reales por categoría POBREZA
# ═════════════════════════════════════════════════════════════════════════════
print("\n[4] Generando table_pobreza_receptores_expo.tex ...")

pob_labels = {
    1: ("Extremo pobre monetario", "Ingreso pc bajo línea extrema"),
    2: ("Pobre no extremo monetario", "Ingreso pc bajo línea de pobreza"),
    3: ("No pobre monetario", "Ingreso pc sobre línea de pobreza"),
}

recep_total = len(recep)
pob_rows = []
for code in [1, 2, 3]:
    n = int((recep["POBREZA"] == code).sum())
    pct = n / recep_total * 100 if recep_total > 0 else 0
    pob_rows.append((code, pob_labels[code][0], n, pct, pob_labels[code][1]))

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Hallazgo Crítico: Distribución de Receptores Reales de Pensión 65 "
    r"según Clasificación de Pobreza Monetaria del INEI}",
    r"\label{tab:pobreza_receptores}",
    r"\begin{threeparttable}",
    r"\begin{tabular}{l l cc l}",
    r"\toprule",
    r"Código & Clasificación INEI & Receptores & \% del total & Descripción \\",
    r"\midrule",
]

for (code, label, n, pct, desc) in pob_rows:
    bold_open  = r"\textbf{" if code == 1 else ""
    bold_close = r"}" if code == 1 else ""
    lines.append(
        f"  {bold_open}POBREZA$={code}${bold_close} & "
        f"{bold_open}{label}{bold_close} & "
        f"{bold_open}{fmt_n(n)}{bold_close} & "
        f"{bold_open}{pct:.1f}\\%{bold_close} & "
        f"{bold_open}{desc}{bold_close} \\\\"
    )

lines += [
    r"\midrule",
    f"  \\textit{{Total receptores}} & & {fmt_n(recep_total)} & 100.0\\% & \\\\",
    r"\bottomrule",
    r"\end{tabular}",
    r"\begin{tablenotes}[flushleft]",
    r"\footnotesize",
    r"\item \textit{Notas:} La tabla muestra la distribución de los "
    f"{fmt_n(recep_total)} receptores reales de Pensión 65 "
    r"identificados en ENAHO 2024 mediante la variable \texttt{P5567A==1} "
    r"(Módulo 5, declaración individual), según su clasificación de "
    r"pobreza monetaria del INEI (variable \texttt{POBREZA} de Sumaria). "
    r"En \textbf{negrita} la categoría que el diseño anterior del paper "
    r"usaba como muestra primaria (\texttt{POBREZA=1}), lo cual excluye al "
    r"\textbf{88.7\%} de los receptores reales. "
    r"La discrepancia se explica por: (1) reverse causality — recibir "
    r"S/250/mes durante años eleva el gasto del hogar, sacando al receptor "
    r"de la categoría extremo pobre; (2) el criterio de elegibilidad de "
    r"Pensión 65 es el puntaje SISFOH (proxy means test de MIDIS), no la "
    r"pobreza monetaria del INEI.",
    r"\end{tablenotes}",
    r"\end{threeparttable}",
    r"\end{table}",
]

out = TABLES_DIR / "table_pobreza_receptores_expo.tex"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"  Guardado: {out}")

# ═════════════════════════════════════════════════════════════════════════════
# 5. FIGURAS
# ═════════════════════════════════════════════════════════════════════════════

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "figure.dpi": 150,
})

# ── Figura 1: verificar existencia (ya existe) ────────────────────────────
f1 = FIGURES_DIR / "figure_1_rdplot.png"
print(f"\n[5.1] figure_1_rdplot.png: {'EXISTE [OK]' if f1.exists() else 'NO ENCONTRADO'}")

# ── Figura 2: figure_first_stage.png ─────────────────────────────────────
print("\n[5.2] Generando figure_first_stage.png ...")

df_fs = df[["EDAD", "RECIBE_P65_PERSONA"]].copy()
df_fs["EDAD"] = pd.to_numeric(df_fs["EDAD"], errors="coerce")

# Rango 55–82
edades_plot = list(range(55, 83))
pct_por_edad = []
n_por_edad   = []
for e in edades_plot:
    sub = df_fs[df_fs["EDAD"] == e]
    n_por_edad.append(len(sub))
    pct_por_edad.append(sub["RECIBE_P65_PERSONA"].mean() * 100 if len(sub) > 0 else 0)

fig, ax = plt.subplots(figsize=(9, 5))
colors = [C_ABOVE if e >= 65 else C_BELOW for e in edades_plot]

bars = ax.bar(edades_plot, pct_por_edad, color=colors, width=0.8, alpha=0.85, edgecolor="white")
ax.axvline(x=64.5, color="black", linestyle="--", linewidth=1.8, label="Corte de edad (65 años)", zorder=5)
ax.set_xlabel("Edad (años)", fontsize=12)
ax.set_ylabel("% que recibe Pensión 65 (P5567A)", fontsize=12)
ax.set_title("Primera Etapa del Fuzzy RDD:\nProbabilidad de Recibir Pensión 65 por Edad", fontsize=13, fontweight="bold")
ax.set_xticks(edades_plot[::2])
ax.set_xticklabels(edades_plot[::2], fontsize=9)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=C_ABOVE, alpha=0.85, label="Elegibles por edad (≥ 65 años)"),
    Patch(facecolor=C_BELOW, alpha=0.85, label="No elegibles (< 65 años)"),
    plt.Line2D([0], [0], color="black", linestyle="--", linewidth=1.8, label="Corte de edad 65"),
]
ax.legend(handles=legend_elements, fontsize=9, loc="upper left")
ax.annotate(
    "Salto discontinuo\n= Primera etapa\ndel fuzzy RDD",
    xy=(65.5, pct_por_edad[edades_plot.index(66)]),
    xytext=(69, pct_por_edad[edades_plot.index(66)] + 3),
    arrowprops=dict(arrowstyle="->", color="black", lw=1.3),
    fontsize=9, ha="center",
)

plt.tight_layout()
fig.savefig(FIGURES_DIR / "figure_first_stage.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES_DIR / "figure_first_stage.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)
print("  Guardado: figure_first_stage.png/.pdf")

# ── Figura 3: figure_pobreza_receptores.png ───────────────────────────────
print("\n[5.3] Generando figure_pobreza_receptores.png ...")

pob_ns   = [int((recep["POBREZA"] == c).sum()) for c in [1, 2, 3]]
pob_pcts = [n / recep_total * 100 for n in pob_ns]
pob_lbls = [
    "POBREZA=1\n(Extremo pobre\nmonetario)",
    "POBREZA=2\n(Pobre no extremo\nmonetario)",
    "POBREZA=3\n(No pobre\nmonetario)",
]

fig, ax = plt.subplots(figsize=(8, 5.5))
bar_colors = [C_P1, C_P2, C_P3]
bars = ax.bar(range(3), pob_pcts, color=bar_colors, width=0.55, alpha=0.88, edgecolor="white")

for bar, pct, n in zip(bars, pob_pcts, pob_ns):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
            f"{pct:.1f}%\n(n={n:,})", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_xticks(range(3))
ax.set_xticklabels(pob_lbls, fontsize=10)
ax.set_ylabel("% de receptores reales de Pensión 65", fontsize=11)
ax.set_title(
    "Distribución de Receptores Reales de Pensión 65\nsegún Clasificación de Pobreza Monetaria del INEI",
    fontsize=13, fontweight="bold"
)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_ylim(0, max(pob_pcts) * 1.35)

# Anotación del 88.7% excluido
excluido_pct = pob_pcts[1] + pob_pcts[2]
ax.annotate(
    f"⟵  {excluido_pct:.1f}% excluido si\nse restringe a POBREZA=1  ⟶",
    xy=(1.5, max(pob_pcts[1], pob_pcts[2]) / 2),
    fontsize=10, ha="center", color="#7b2d8b", fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#f2e6f7", edgecolor="#7b2d8b", alpha=0.85),
)

plt.tight_layout()
fig.savefig(FIGURES_DIR / "figure_pobreza_receptores.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES_DIR / "figure_pobreza_receptores.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)
print("  Guardado: figure_pobreza_receptores.png/.pdf")

# ── Figura 4: verificar existencia ───────────────────────────────────────
f4 = FIGURES_DIR / "figure_2_bandwidth_sensitivity.png"
print(f"\n[5.4] figure_2_bandwidth_sensitivity.png: {'EXISTE [OK]' if f4.exists() else 'NO ENCONTRADO'}")

# ── Figura 5: figure_descriptivos_brecha.png ─────────────────────────────
print("\n[5.5] Generando figure_descriptivos_brecha.png ...")

VARS_BAR = [
    ("TIENE_BILLETERA",  "Billetera digital\n(tenencia o uso)"),
    ("INTERNET_HOGAR",   "Internet\nen el hogar"),
    ("SMARTPHONE",       "Smartphone\nen el hogar"),
]

above_means = []
below_means = []
var_labels  = []

for col, label in VARS_BAR:
    if col in df.columns:
        above_means.append(above[col].mean() * 100)
        below_means.append(below[col].mean() * 100)
        var_labels.append(label)

x = np.arange(len(var_labels))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5.5))
bars_b = ax.bar(x - width / 2, below_means, width, label="Below Threshold (< 65 años)",
                color=C_BELOW, alpha=0.85, edgecolor="white")
bars_a = ax.bar(x + width / 2, above_means, width, label="Above Threshold (≥ 65 años)",
                color=C_ABOVE, alpha=0.85, edgecolor="white")

for bar, val in zip(bars_b, below_means):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=9, color=C_BELOW, fontweight="bold")
for bar, val in zip(bars_a, above_means):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=9, color=C_ABOVE, fontweight="bold")

ax.set_ylabel("Proporción (%)", fontsize=11)
ax.set_title(
    "Brecha Digital por Grupo de Edad:\nBelow vs. Above Threshold (Corte Pensión 65)",
    fontsize=13, fontweight="bold"
)
ax.set_xticks(x)
ax.set_xticklabels(var_labels, fontsize=11)
ax.legend(fontsize=10)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_ylim(0, max(max(above_means), max(below_means)) * 1.22)

plt.tight_layout()
fig.savefig(FIGURES_DIR / "figure_descriptivos_brecha.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES_DIR / "figure_descriptivos_brecha.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)
print("  Guardado: figure_descriptivos_brecha.png/.pdf")

# ═════════════════════════════════════════════════════════════════════════════
# 6. ECUACIONES LaTeX
# ═════════════════════════════════════════════════════════════════════════════
print("\n[6] Generando paper/equations_expo.tex ...")

eq_content = r"""% ============================================================
%  equations_expo.tex
%  Ecuaciones principales del fuzzy RDD — listo para Overleaf
%  Pensión 65 × Billetera Digital, ENAHO 2024
% ============================================================

% ── Notación ──────────────────────────────────────────────
% i       = individuo
% D_i     = 1 si la persona i recibe Pensión 65 (P5567A = 1)
% Y_i     = TIENE_BILLETERA (billetera digital, tenencia o uso)
% Z_i     = 1(Edad_i >= 65)   [instrumento / discontinuidad]
% r_i     = Edad_i - 65       [running variable centrada]
% h       = ancho de banda (h* = 14 años)
% K(·)    = kernel triangular
% ──────────────────────────────────────────────────────────

% ── Ecuación 1: Primera Etapa (First Stage) ───────────────
% Estima cómo el instrumento Z_i predice el tratamiento D_i.
% El coeficiente rho (ρ) es el salto en la probabilidad de
% recibir Pensión 65 exactamente en el corte de edad 65.

\begin{equation}
    \label{eq:first_stage}
    D_i
    \;=\;
    \alpha_0
    + \underbrace{\rho}_{\text{1ra etapa}}
        \cdot \mathbf{1}[\text{Edad}_i \geq 65]
    + \alpha_1 \, r_i
    + \alpha_2 \, r_i \cdot \mathbf{1}[r_i \geq 0]
    + \varepsilon_i
    \quad
    \left| \, |r_i| \leq h \right.
\end{equation}

% Resultado estimado (Candidato A, muestra completa, h = 14):
%   \hat{\rho} = 0.104,  F-estadístico \approx 310  (instrumento fuerte)

% ── Ecuación 2: Segunda Etapa (IV / 2SLS) ────────────────
% Regresa el outcome Y_i sobre la predicción \hat{D}_i
% de la primera etapa. El coeficiente tau (τ) es el LATE:
% Local Average Treatment Effect para los compliers.

\begin{equation}
    \label{eq:second_stage}
    Y_i
    \;=\;
    \beta_0
    + \underbrace{\tau}_{\text{LATE}}
        \cdot \widehat{D}_i
    + \beta_1 \, r_i
    + \beta_2 \, r_i \cdot \mathbf{1}[r_i \geq 0]
    + u_i
    \quad
    \left| \, |r_i| \leq h \right.
\end{equation}

% Resultado estimado (Candidato A, muestra completa):
%   \hat{\tau}_{LATE} = -0.012,  IC_{95\%} = [-0.190,\; +0.166]
%   No rechazamos nulo. Cota superior excluye efectos > +17 pp.

% ── Ecuación 3: Relación ITT – LATE (Wald / 2SLS) ────────
% La estimación de variables instrumentales en el RDD se
% interpreta como el cociente entre la forma reducida (RF,
% efecto del instrumento sobre el outcome) y la primera
% etapa (FS, efecto del instrumento sobre el tratamiento).
% Siguiendo Angrist y Pischke (2009), cap. 4.

\begin{equation}
    \label{eq:late_wald}
    \hat{\tau}_{\text{LATE}}
    \;=\;
    \frac{\hat{\tau}_{\text{RF}}}{\hat{\rho}}
    \;=\;
    \frac{
        \displaystyle\lim_{r \downarrow 0} \mathbb{E}[Y_i \mid r_i = r]
        -
        \displaystyle\lim_{r \uparrow 0}  \mathbb{E}[Y_i \mid r_i = r]
    }{
        \displaystyle\lim_{r \downarrow 0} \mathbb{E}[D_i \mid r_i = r]
        -
        \displaystyle\lim_{r \uparrow 0}  \mathbb{E}[D_i \mid r_i = r]
    }
\end{equation}

% El LATE identifica el efecto causal de Pensión 65 sobre
% la adopción de billetera digital ÚNICAMENTE para los
% "compliers": individuos que reciben el bono si y solo si
% tienen 65 años o más (Imbens y Angrist, 1994).
%
% Referencia:
%   Angrist, J. D., & Pischke, J. S. (2009).
%   \textit{Mostly Harmless Econometrics}.
%   Princeton University Press. Cap. 4.6.
"""

out_eq = PAPER_DIR / "equations_expo.tex"
out_eq.write_text(eq_content, encoding="utf-8")
print(f"  Guardado: {out_eq}")

# ═════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("RESUMEN — Archivos generados para la exposición:")
print("=" * 60)

outputs = [
    ("TABLAS", [
        TABLES_DIR / "table_1_summary_expo.tex",
        TABLES_DIR / "table_first_stage_expo.tex",
        TABLES_DIR / "table_fuzzy_rdd_expo.tex",
        TABLES_DIR / "table_pobreza_receptores_expo.tex",
    ]),
    ("FIGURAS (nuevas)", [
        FIGURES_DIR / "figure_first_stage.png",
        FIGURES_DIR / "figure_pobreza_receptores.png",
        FIGURES_DIR / "figure_descriptivos_brecha.png",
    ]),
    ("FIGURAS (verificadas existentes)", [
        FIGURES_DIR / "figure_1_rdplot.png",
        FIGURES_DIR / "figure_2_bandwidth_sensitivity.png",
    ]),
    ("ECUACIONES", [
        PAPER_DIR / "equations_expo.tex",
    ]),
]

all_ok = True
for category, paths in outputs:
    print(f"\n  {category}:")
    for p in paths:
        status = "OK" if p.exists() else "FALTANTE"
        size   = f"{p.stat().st_size / 1024:.1f} KB" if p.exists() else ""
        print(f"    [{status}] {p.name}  {size}")
        if status == "FALTANTE":
            all_ok = False

print("\n" + ("Todos los archivos generados correctamente." if all_ok
              else "ADVERTENCIA: algunos archivos no se generaron."))
