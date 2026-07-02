"""
Script mínimo para regenerar paper/figures/figure_mccrary_density.{png,pdf}
sin correr el pipeline completo.

Uso:
    python scripts/generar_figura2.py
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
RUNNING_VAR     = "running_centered"
THRESHOLD       = 65

# ── Cargar datos ───────────────────────────────────────────────────────────
for candidate in ["main_dataset.csv", "enaho_rdd_full.csv"]:
    csv_path = DATA_DIR / candidate
    if csv_path.exists():
        break
else:
    raise FileNotFoundError(f"No se encontró main_dataset.csv ni enaho_rdd_full.csv en {DATA_DIR}")

print(f"Cargando {csv_path.name} ...")
df = pd.read_csv(csv_path, low_memory=False)

if RUNNING_VAR not in df.columns:
    if "EDAD" in df.columns:
        df[RUNNING_VAR] = pd.to_numeric(df["EDAD"], errors="coerce") - THRESHOLD
    else:
        raise KeyError("No se encontró 'running_centered' ni 'EDAD' en el dataset.")

df[PRIMARY_OUTCOME] = pd.to_numeric(df[PRIMARY_OUTCOME], errors="coerce")
df[RUNNING_VAR]     = pd.to_numeric(df[RUNNING_VAR],     errors="coerce")

y_all = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR])[RUNNING_VAR].values
print(f"  N total (con outcome): {len(y_all):,}")

# ── Calcular estadístico T con rddensity ───────────────────────────────────
mccrary_pval = np.nan
try:
    from rddensity import rddensity
    rd_den = rddensity(X=y_all, c=0)
    try:
        mccrary_pval = rd_den.p if hasattr(rd_den, "p") else np.nan
    except Exception:
        pass
    print(f"  rddensity T: {mccrary_pval}")
except ImportError:
    print("  rddensity no instalado — título mostrará sin valor T.")
except Exception as e:
    print(f"  rddensity falló: {e}")

# ── Generar figura ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

window = 30
mask   = np.abs(y_all) <= window
y_win  = y_all[mask]
bin_edges   = np.arange(np.floor(y_win.min()) - 0.5,
                        np.ceil(y_win.max()) + 1.5, 1.0)
left_vals  = y_win[y_win < 0]
right_vals = y_win[y_win >= 0]

ax.hist(left_vals, bins=bin_edges, color="#2166ac", alpha=0.7,
        edgecolor="white", linewidth=0.5,
        label="Bajo el umbral (edad $<$ 65)")
ax.hist(right_vals, bins=bin_edges, color="#b2182b", alpha=0.7,
        edgecolor="white", linewidth=0.5,
        label="Sobre el umbral (edad $\\geq$ 65)")
ax.axvline(x=0, color="black", linestyle="--", linewidth=1.2,
           alpha=0.8, label="Umbral (65 años)")

ax.set_xlabel("Edad centrada en 65 años", fontsize=12)
ax.set_ylabel("Frecuencia (número de individuos)", fontsize=12)

test_label = (
    f"Test de densidad - Cattaneo, Jansson y Ma (2018): T $=$ {float(mccrary_pval):.2f}"
    if isinstance(mccrary_pval, (int, float)) and not np.isnan(mccrary_pval)
    else "Test de densidad - Cattaneo, Jansson y Ma (2018)"
)
ax.set_title(test_label, fontsize=12)
ax.legend(loc="upper right", fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()

for ext in ("png", "pdf"):
    out = FIGURES_DIR / f"figure_mccrary_density.{ext}"
    plt.savefig(out, dpi=150 if ext == "png" else 300, bbox_inches="tight")
    print(f"  Guardado: {out}")

plt.close("all")
print("Listo.")
