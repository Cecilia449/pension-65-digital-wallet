"""
Script mínimo para regenerar paper/figures/figure_1_rdplot.{png,pdf}
sin correr el pipeline completo.

Uso:
    python scripts/generar_figura1.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Rutas ──────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
DATA_DIR    = REPO_ROOT / "data" / "clean"
FIGURES_DIR = REPO_ROOT / "paper" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Constantes ─────────────────────────────────────────────────────────────
PRIMARY_OUTCOME = "TIENE_BILLETERA"
RUNNING_VAR     = "running_centered"   # EDAD - 65
THRESHOLD       = 65

# ── Cargar datos ───────────────────────────────────────────────────────────
csv_path = DATA_DIR / "main_dataset.csv"
if not csv_path.exists():
    # Fallback al CSV legacy si main_dataset aún no fue generado
    csv_path = DATA_DIR / "enaho_rdd_full.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No se encontró main_dataset.csv ni enaho_rdd_full.csv en {DATA_DIR}"
        )
    print(f"  Usando CSV legacy: {csv_path.name}")

print(f"Cargando {csv_path.name} ...")
df = pd.read_csv(csv_path, low_memory=False)

# Asegurar columna running_centered
if RUNNING_VAR not in df.columns:
    if "EDAD" in df.columns:
        df[RUNNING_VAR] = pd.to_numeric(df["EDAD"], errors="coerce") - THRESHOLD
    else:
        raise KeyError("No se encontró 'running_centered' ni 'EDAD' en el dataset.")

df[PRIMARY_OUTCOME] = pd.to_numeric(df[PRIMARY_OUTCOME], errors="coerce")
df[RUNNING_VAR]     = pd.to_numeric(df[RUNNING_VAR],     errors="coerce")

print(f"  N total: {len(df):,}")

# ── Generar figura ─────────────────────────────────────────────────────────
sub = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR])
x   = sub[RUNNING_VAR].values
y   = sub[PRIMARY_OUTCOME].values

x_range = 18.04
mask    = np.abs(x) <= x_range
x_p, y_p = x[mask], y[mask]
n_bins  = 25

print(f"  Observaciones en ±{x_range} años: {mask.sum():,}")


def bin_scatter(xv, yv, nbins):
    if len(xv) < nbins:
        return xv, yv
    bins = np.linspace(xv.min(), xv.max(), nbins + 1)
    cx, cy = [], []
    for i in range(nbins):
        m = (xv >= bins[i]) & (xv < bins[i + 1])
        if i == nbins - 1:
            m = (xv >= bins[i]) & (xv <= bins[i + 1])
        if m.sum() > 0:
            cx.append(xv[m].mean())
            cy.append(yv[m].mean())
    return np.array(cx), np.array(cy)


x_left,  y_left  = x_p[x_p < 0],  y_p[x_p < 0]
x_right, y_right = x_p[x_p >= 0], y_p[x_p >= 0]

fig, ax = plt.subplots(figsize=(8, 5))

if len(x_left) > 3:
    bx, by = bin_scatter(x_left, y_left, n_bins)
    ax.scatter(bx, by, color="#2166ac", s=60, zorder=3, label="Bajo el umbral")
    coeffs = np.polyfit(x_left, y_left, 1)
    xs = np.linspace(x_left.min(), 0, 100)
    ax.plot(xs, np.poly1d(coeffs)(xs), color="#2166ac", linewidth=2)

if len(x_right) > 3:
    bx, by = bin_scatter(x_right, y_right, n_bins)
    ax.scatter(bx, by, color="#b2182b", s=60, zorder=3, label="Sobre el umbral")
    coeffs = np.polyfit(x_right, y_right, 1)
    xs = np.linspace(0, x_right.max(), 100)
    ax.plot(xs, np.poly1d(coeffs)(xs), color="#b2182b", linewidth=2)

ax.axvline(x=0, color="black", linestyle="--", linewidth=1, alpha=0.7,
           label="Umbral (65 años)")
ax.set_xlim(-x_range, x_range)
ax.set_xlabel("Edad centrada en 65 años", fontsize=12)
ax.set_ylabel("Tiene Billetera", fontsize=12)
ax.set_title("Adopción de billeteras digitales por edad (ENAHO 2024)", fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.text(0.02, 0.97, "Ancho de banda óptimo: h = 18.04 años",
        transform=ax.transAxes, fontsize=9, va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

plt.tight_layout()

for ext in ["png", "pdf"]:
    out = FIGURES_DIR / f"figure_1_rdplot.{ext}"
    plt.savefig(out, dpi=150 if ext == "png" else 300, bbox_inches="tight")
    print(f"  Guardado: {out}")

plt.close("all")
print("Listo.")
