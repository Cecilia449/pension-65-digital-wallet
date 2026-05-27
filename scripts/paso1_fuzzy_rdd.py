"""
PASO 1 — Comparación de 3 candidatos de grupo de análisis para el RDD
de Pensión 65 sobre adopción de billetera digital (ENAHO 2024).

Construye:
  - RECIBE_P65_PERSONA  (P5567A==1 en módulo 5, nivel individuo)
  - RECIBE_P65_HOGAR    (INGTPU03>0 en Sumaria, nivel hogar)
  - TIENE_BILLETERA     (tenencia OR uso, igual que el paper)

Corre RDD local-linear (kernel triangular, OLS con HC1) en:
  Candidato A — full sample (replica el paper actual, ITT diluido)
  Candidato B — POBREZA==1 (extrema pobreza, ITT focal)
  Candidato C — POBREZA in {1,2} (pobres y extrema pobreza, fuzzy RDD)

Reporta para cada candidato: first stage en RECIBE_P65, reduced form en
TIENE_BILLETERA, y LATE = RF / FS (Wald IV).

NO MUTA el paper. Solo lee datos crudos y produce un reporte por stdout
+ un CSV con la tabla comparativa.
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

RAW_DIR = Path(r"C:\Users\Alexander\AppData\Local\Temp\enaho2024_check")
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYS_H = ["CONGLOME", "VIVIENDA", "HOGAR"]
KEYS_P = KEYS_H + ["CODPERSO"]
CUTOFF = 65


def load_sumaria() -> pd.DataFrame:
    f = RAW_DIR / "966-Modulo34" / "Sumaria-2024.csv"
    s = pd.read_csv(f, encoding="latin-1", low_memory=False)
    keep = KEYS_H + ["INGTPU03", "INGTPU01", "INGHOG2D", "MIEPERHO",
                     "POBREZA", "FACTOR07"]
    s = s[[c for c in keep if c in s.columns]].copy()
    s["RECIBE_P65_HOGAR"]    = (pd.to_numeric(s["INGTPU03"], errors="coerce") > 0).astype(int)
    s["RECIBE_JUNTOS_HOGAR"] = (pd.to_numeric(s["INGTPU01"], errors="coerce") > 0).astype(int)
    s["POBREZA"]    = pd.to_numeric(s["POBREZA"],   errors="coerce")
    s["MIEPERHO"]   = pd.to_numeric(s["MIEPERHO"],  errors="coerce")
    s["INGRESO_PC"] = (pd.to_numeric(s["INGHOG2D"], errors="coerce")
                       / s["MIEPERHO"].replace(0, np.nan))
    print(f"  Sumaria: {len(s):,} hogares")
    return s


def load_personas() -> pd.DataFrame:
    f = RAW_DIR / "966-Modulo02" / "Enaho01-2024-200.csv"
    p = pd.read_csv(f, encoding="latin-1", low_memory=False)
    p = p[KEYS_P + ["P204", "P203", "P208A", "P207"]].copy()
    p["EDAD"] = pd.to_numeric(p["P208A"], errors="coerce")
    p["SEXO"] = pd.to_numeric(p["P207"], errors="coerce")
    p["P204_NUM"] = pd.to_numeric(p["P204"], errors="coerce")
    p["P203_NUM"] = pd.to_numeric(p["P203"], errors="coerce")
    p = p[(p["P204_NUM"] == 1) & (~p["P203_NUM"].isin([8, 9]))].copy()
    p = p.dropna(subset=["EDAD"])
    print(f"  Personas: {len(p):,}")
    return p[KEYS_P + ["EDAD", "SEXO"]]


def load_billetera_y_p65_persona() -> pd.DataFrame:
    f = RAW_DIR / "966-Modulo05" / "Enaho01a-2024-500.csv"
    cols = (KEYS_P
            + ["P5567A"]                          # recepción Pensión 65 (persona)
            + ["P558E1_9"]                        # tenencia billetera
            + [f"P558H{g}_7" for g in range(1, 13)])  # uso billetera
    m = pd.read_csv(f, encoding="latin-1", low_memory=False, usecols=cols)
    m["RECIBE_P65_PERSONA"] = (pd.to_numeric(m["P5567A"], errors="coerce") == 1).astype(int)
    m["TENENCIA"] = (pd.to_numeric(m["P558E1_9"], errors="coerce") == 9).astype(int)
    uso = pd.DataFrame({
        g: (pd.to_numeric(m[f"P558H{g}_7"], errors="coerce") == 7).astype(int)
        for g in range(1, 13)
    })
    m["USO_BILLETERA"] = (uso.sum(axis=1) > 0).astype(int)
    m["TIENE_BILLETERA"] = ((m["TENENCIA"] == 1) | (m["USO_BILLETERA"] == 1)).astype(int)
    m["USA_BILLETERA"] = m["USO_BILLETERA"]
    print(f"  Modulo 05: {len(m):,} personas")
    keep = KEYS_P + ["RECIBE_P65_PERSONA", "TIENE_BILLETERA", "USA_BILLETERA"]
    return m[keep]


def triangular(c: pd.Series, bw: float) -> pd.Series:
    """Kernel triangular: max(1 - |x|/bw, 0)."""
    w = 1.0 - c.abs() / bw
    return w.clip(lower=0.0)


def rdd_local_linear(df: pd.DataFrame, y: str, bw: float) -> dict:
    """RDD local-linear con kernel triangular y SE HC1.

    Modelo: y = a + tau*D + b1*(x-c) + b2*D*(x-c)  con x = EDAD-65.
    """
    d = df.dropna(subset=[y, "running_centered"]).copy()
    d = d[d["running_centered"].abs() <= bw]
    if len(d) < 100:
        return {"tau": np.nan, "se": np.nan, "ci_lo": np.nan,
                "ci_hi": np.nan, "n": len(d), "n_lo": 0, "n_hi": 0,
                "y_below_mean": np.nan, "y_above_mean": np.nan}
    x = d["running_centered"].astype(float).values
    treat = (x >= 0).astype(int)
    X = np.column_stack([np.ones(len(d)), treat, x, treat * x])
    w = triangular(d["running_centered"], bw).values
    yv = d[y].astype(float).values
    mod = sm.WLS(yv, X, weights=w).fit(cov_type="HC1")
    tau = float(mod.params[1])
    se  = float(mod.bse[1])
    n_lo = int((x < 0).sum())
    n_hi = int((x >= 0).sum())
    return {
        "tau": tau, "se": se,
        "ci_lo": tau - 1.96 * se, "ci_hi": tau + 1.96 * se,
        "n": len(d), "n_lo": n_lo, "n_hi": n_hi,
        "y_below_mean": float(d.loc[x < 0,  y].mean()),
        "y_above_mean": float(d.loc[x >= 0, y].mean()),
    }


def mse_optimal_bw(df: pd.DataFrame, y: str, h_grid=(8, 10, 12, 14, 16, 18, 20)) -> float:
    """Selecciona bandwidth minimizando MSE-proxy via SE^2 + (estimate-overall)^2."""
    # Heurística simple: usa el bandwidth donde el estimate se estabiliza.
    # Para simplicidad y replicabilidad reportamos varios bandwidths.
    return 14.0  # alineado con h*≈14.24 del paper actual


def fmt(r: dict, scale=1.0) -> str:
    if np.isnan(r["tau"]):
        return f"   N={r['n']:,} (insuficiente)"
    return (f"   tau={r['tau']*scale:+.4f}  SE={r['se']*scale:.4f}  "
            f"CI=[{r['ci_lo']*scale:+.4f},{r['ci_hi']*scale:+.4f}]  "
            f"N={r['n']:,} (lo={r['n_lo']:,} hi={r['n_hi']:,})")


def main() -> None:
    print("=" * 78)
    print("PASO 1 — Comparación de 3 candidatos de grupo de análisis")
    print("=" * 78)

    print("\n[load] Cargando módulos...")
    sumaria  = load_sumaria()
    personas = load_personas()
    m05      = load_billetera_y_p65_persona()

    print("\n[merge] Personas + Sumaria(hogar) + Módulo 5...")
    df = personas.merge(sumaria, on=KEYS_H, how="left")
    df = df.merge(m05, on=KEYS_P, how="inner")  # solo adultos con módulo 5
    df["running_centered"] = df["EDAD"] - CUTOFF
    print(f"  Muestra integrada: {len(df):,} personas con EDAD y módulo 5")

    # Llenar NaN en outcomes para personas que no contestaron módulo 5
    # (niños y excluidos del módulo de empleo). Esos quedan fuera por el merge inner.

    print("\n[check] First stage RECIBE_P65_PERSONA por edad (bins de 1 año):")
    fs = (df.groupby("EDAD")[["RECIBE_P65_PERSONA", "RECIBE_P65_HOGAR"]]
            .agg(["mean", "count"]))
    print(fs.loc[range(50, 81)].round(3).to_string())

    bw = 14.0
    print(f"\nBandwidth fijo h = {bw} anios (alineado con h* aprox 14.24 del paper).")

    results: list[dict] = []

    # ------------------------- CANDIDATO A: full sample -----------------------
    print("\n" + "=" * 78)
    print("CANDIDATO A — Full sample (replica el diseño actual)")
    print("=" * 78)
    fs_A = rdd_local_linear(df, "RECIBE_P65_PERSONA", bw)
    rf_A = rdd_local_linear(df, "TIENE_BILLETERA",   bw)
    print(f"\n First stage  (RECIBE_P65_PERSONA, persona-level):")
    print(fmt(fs_A))
    print(f"\n Reduced form (TIENE_BILLETERA):")
    print(fmt(rf_A))
    if fs_A["tau"] > 0:
        late = rf_A["tau"] / fs_A["tau"]
        late_se = rf_A["se"] / abs(fs_A["tau"])  # delta aproximada con FS fijo
        print(f"\n LATE (Wald, aprox): {late:+.4f}  SE~{late_se:.4f}  "
              f"[{late-1.96*late_se:+.4f},{late+1.96*late_se:+.4f}]")
    results.append({"candidato": "A_full", **{f"fs_{k}": v for k, v in fs_A.items()},
                    **{f"rf_{k}": v for k, v in rf_A.items()}})

    # ------------------------- CANDIDATO B: POBREZA==1 ------------------------
    print("\n" + "=" * 78)
    print("CANDIDATO B — POBREZA == 1 (extrema pobreza, target del programa)")
    print("=" * 78)
    df_B = df[df["POBREZA"] == 1].copy()
    print(f"  N total en EP: {len(df_B):,}")
    fs_B = rdd_local_linear(df_B, "RECIBE_P65_PERSONA", bw)
    rf_B = rdd_local_linear(df_B, "TIENE_BILLETERA",   bw)
    print(f"\n First stage  (RECIBE_P65_PERSONA):")
    print(fmt(fs_B))
    print(f"\n Reduced form (TIENE_BILLETERA):")
    print(fmt(rf_B))
    if fs_B["tau"] > 0:
        late = rf_B["tau"] / fs_B["tau"]
        late_se = rf_B["se"] / abs(fs_B["tau"])
        print(f"\n LATE (Wald, aprox): {late:+.4f}  SE~{late_se:.4f}  "
              f"[{late-1.96*late_se:+.4f},{late+1.96*late_se:+.4f}]")
    results.append({"candidato": "B_EP", **{f"fs_{k}": v for k, v in fs_B.items()},
                    **{f"rf_{k}": v for k, v in rf_B.items()}})

    # ------------------ CANDIDATO C: POBREZA in {1, 2} ------------------------
    print("\n" + "=" * 78)
    print("CANDIDATO C — POBREZA in {1,2} (pobre + extrema pobre)")
    print("=" * 78)
    df_C = df[df["POBREZA"].isin([1, 2])].copy()
    print(f"  N total en pobreza ampliada: {len(df_C):,}")
    fs_C = rdd_local_linear(df_C, "RECIBE_P65_PERSONA", bw)
    rf_C = rdd_local_linear(df_C, "TIENE_BILLETERA",   bw)
    print(f"\n First stage  (RECIBE_P65_PERSONA):")
    print(fmt(fs_C))
    print(f"\n Reduced form (TIENE_BILLETERA):")
    print(fmt(rf_C))
    if fs_C["tau"] > 0:
        late = rf_C["tau"] / fs_C["tau"]
        late_se = rf_C["se"] / abs(fs_C["tau"])
        print(f"\n LATE (Wald, aprox): {late:+.4f}  SE~{late_se:.4f}  "
              f"[{late-1.96*late_se:+.4f},{late+1.96*late_se:+.4f}]")
    results.append({"candidato": "C_EP_plus_P", **{f"fs_{k}": v for k, v in fs_C.items()},
                    **{f"rf_{k}": v for k, v in rf_C.items()}})

    # --------------- Placebo: same RDD pero outcome = Juntos ------------------
    print("\n" + "=" * 78)
    print("PLACEBO — Salto en RECIBE_JUNTOS a edad 65 (no debería existir)")
    print("=" * 78)
    pl = rdd_local_linear(df, "RECIBE_JUNTOS_HOGAR", bw)
    print(fmt(pl))
    print("  (Juntos NO depende de edad >=65; salto cercano a 0 valida el corte.)")

    # ----------------------------- Sensibilidad de bw -------------------------
    print("\n" + "=" * 78)
    print("Sensibilidad de bandwidth — TIENE_BILLETERA en CANDIDATO B (EP)")
    print("=" * 78)
    for bw_alt in [7, 10, 14, 18, 24]:
        r = rdd_local_linear(df_B, "TIENE_BILLETERA", bw_alt)
        print(f"  h={bw_alt:>3}: {fmt(r)}")

    # ------------------------------ Persistir CSV -----------------------------
    out_csv = OUT_DIR / "paso1_comparacion_candidatos.csv"
    pd.DataFrame(results).to_csv(out_csv, index=False)
    print(f"\n[save] Tabla comparativa → {out_csv}")


if __name__ == "__main__":
    main()
