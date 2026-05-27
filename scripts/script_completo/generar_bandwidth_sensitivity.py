"""
Genera figure_bandwidth_sensitivity_granular.png/.pdf
Sensibilidad del RDD1 (sharp, running var = edad centrada en 65) al bandwidth.
Bandwidths: h = 3, 5, 7, 10, 14, 18, 24 años.
Referencia MSE-óptimo Calonico et al. = 18.04 yrs (rdrobust sobre muestra completa).
Referencia Torres & Salinas 2016 = h = 10.
"""

import os, sys, importlib.util
import numpy as np
import pandas as pd

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

# ── Cargar script principal para reutilizar run_rdd y sus globals ──────────
spec = importlib.util.spec_from_file_location(
    "script",
    os.path.join(os.path.dirname(__file__), "script.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA_DIR    = mod.DATA_DIR
FIGURES_DIR = mod.FIGURES_DIR

# ── Datos ──────────────────────────────────────────────────────────────────
df_full = pd.read_csv(mod.PATHS["clean_data_full"])

BANDWIDTHS   = [3, 5, 7, 10, 14, 18, 24]
H_MSE        = 18.04   # MSE-óptimo rdrobust (Calonico, Cattaneo, Titiunik 2014)
H_TORRES     = 10      # Torres & Salinas 2016 benchmark
OUTCOMES     = ["TIENE_BILLETERA", "USA_BILLETERA"]
OUTCOME_LABELS = {
    "TIENE_BILLETERA": "Tiene Billetera (tenencia o uso)",
    "USA_BILLETERA":   "Usa Billetera (uso activo)",
}
COLORS = {
    "TIENE_BILLETERA": "#1a6fad",
    "USA_BILLETERA":   "#b2182b",
}

# ── Estimar para cada h ────────────────────────────────────────────────────
print("Estimando RDD1 para cada bandwidth...")
results = {out: [] for out in OUTCOMES}

for h in BANDWIDTHS:
    print(f"  h = {h} ...", end=" ")
    for out in OUTCOMES:
        res = mod.run_rdd(df_full, out, h=h, label=f"bw_{h}")
        results[out].append({
            "h":        h,
            "estimate": res["estimate"],
            "ci_lower": res["ci_lower"],
            "ci_upper": res["ci_upper"],
            "N_eff":    res["N_eff"],
            "method":   res["method"],
        })
    print("OK")

# ── Guardar tabla de sensibilidad como CSV ─────────────────────────────────
rows_all = []
for out in OUTCOMES:
    for r in results[out]:
        rows_all.append({"outcome": out, **r})
df_sens = pd.DataFrame(rows_all)
sens_csv = os.path.join(str(DATA_DIR), "bandwidth_sensitivity_rdd1.csv")
df_sens.to_csv(sens_csv, index=False, encoding="utf-8")
print(f"\nGuardado tabla: {sens_csv}")
print(df_sens.to_string())

# ── Gráfico ────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(
    1, 2, figsize=(13, 5.5), sharey=False,
    gridspec_kw={"wspace": 0.38}
)

for ax, out in zip(axes, OUTCOMES):
    df_o = pd.DataFrame(results[out])
    hs   = df_o["h"].values.astype(float)
    est  = df_o["estimate"].values
    lo   = df_o["ci_lower"].values
    hi   = df_o["ci_upper"].values
    color = COLORS[out]

    # Banda de IC
    ax.fill_between(hs, lo, hi, alpha=0.18, color=color, label="95% CI")

    # Línea del estimado
    ax.plot(hs, est, color=color, linewidth=2.2, zorder=4, label="Point estimate")

    # Puntos
    ax.scatter(hs, est, color=color, s=60, zorder=5)

    # IC bars verticales en cada punto
    for h_i, e_i, l_i, u_i in zip(hs, est, lo, hi):
        ax.plot([h_i, h_i], [l_i, u_i], color=color, linewidth=1.2,
                alpha=0.6, zorder=3)

    # Línea nula
    ax.axhline(0, color="black", linewidth=0.9, linestyle="-", alpha=0.4, zorder=2)

    # Línea MSE-óptimo
    ax.axvline(H_MSE, color="#444444", linewidth=1.3, linestyle="--",
               zorder=2, label=f"MSE-óptimo $h^* = {H_MSE}$ yrs")

    # Línea Torres & Salinas 2016
    ax.axvline(H_TORRES, color="#777777", linewidth=1.3, linestyle=":",
               zorder=2, label=f"Torres & Salinas 2016 ($h = {H_TORRES}$)")

    # Etiquetas de N_eff bajo cada punto
    y_range = hi.max() - lo.min()
    offset  = y_range * 0.06
    for h_i, e_i, l_i, n_i in zip(hs, est, lo, df_o["N_eff"].values):
        ax.text(h_i, l_i - offset, f"N={n_i:,}",
                ha="center", va="top", fontsize=6.5, color="#555555", zorder=6)

    ax.set_xlabel("Bandwidth $h$ (años)", fontsize=11)
    ax.set_ylabel("Estimado RDD (pp)", fontsize=11)
    ax.set_title(OUTCOME_LABELS[out], fontsize=11, pad=8)
    ax.set_xticks(BANDWIDTHS)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
    ax.tick_params(labelsize=9)

    # Anotaciones textuales en las líneas de referencia
    ylim_lo, ylim_hi = ax.get_ylim()
    ax.annotate(
        f"$h^*={H_MSE}$\n(MSE-opt.)",
        xy=(H_MSE, ylim_hi),
        xytext=(H_MSE + 0.5, ylim_hi * 0.97),
        fontsize=7.5, color="#444444", ha="left", va="top",
    )
    ax.annotate(
        f"$h={H_TORRES}$\n(T&S 2016)",
        xy=(H_TORRES, ylim_hi),
        xytext=(H_TORRES + 0.4, ylim_hi * 0.85),
        fontsize=7.5, color="#777777", ha="left", va="top",
    )

fig.suptitle(
    "RDD1 Bandwidth Sensitivity — Effect of Pensión 65 Age-65 Threshold on Digital Wallet Adoption\n"
    "ENAHO 2024, rdrobust, kernel triangular, HC robust SE",
    fontsize=11, y=1.02,
)

plt.tight_layout()

for ext in ("png", "pdf"):
    out_path = FIGURES_DIR / f"figure_bandwidth_sensitivity_granular.{ext}"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    print(f"Guardado: {out_path}")

plt.close(fig)
print("\nHecho.")
