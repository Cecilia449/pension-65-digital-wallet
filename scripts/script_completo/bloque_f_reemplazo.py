# ════════════════════════════════════════════════════════════════════════════
# BLOQUE F — RDD2: proxy SISFOH como running variable.
# Replica Bando, Galiani y Gertler (2020). Resuelve el
# problema de potencia del RDD1 al usar toda la muestra
# de adultos mayores (EDAD>=65) en vez del 5% en extrema
# pobreza dentro del bandwidth de edad.
#
# VARIABLES PCA — ENAHO 2024 (aliases verificados empíricamente):
#   Vivienda (Filmer & Pritchett 2001):
#     P102  → material de paredes
#     P103  → material de piso
#     P104  → número de cuartos (denominador de hacinamiento)
#     P110  → abastecimiento de agua
#     P111A → servicio sanitario  [alias corregido: era P111]
#     P112A → tipo de alumbrado   [alias corregido: era P112]
#     P113A → combustible para cocinar [alias corregido: era P113]
#   Bienes durables (Módulo 18, formato long via P612N):
#     P612N=4  → refrigeradora
#     P612N=2  → televisor
#     P612N=10 → smartphone      [confirmado en dataset completo]
#   Variable derivada:
#     HACINAMIENTO = MIEPERHO / P104  (construida aquí, no en Fase 1)
#
# EXCLUIDAS del PCA (con justificación):
#   INGRESO_PC  → endógena: la transferencia eleva el ingreso del hogar
#   POBREZA     → clasificación monetaria post-tratamiento, no proxy SISFOH
#   LAVADORA    → varianza casi nula en adultos mayores en pobreza (8.9% general)
#   LAPTOP      → sesgo etario: discrimina jóvenes, no pobreza en adultos mayores
#   COMPUTADORA → ídem laptop
#   TABLET      → 0.1% de tenencia, sin varianza útil
#   MIEPERHO    → entra indirectamente vía HACINAMIENTO; meterla dos veces infla su peso
#   TIENE_BILLETERA → es la variable de resultado, nunca puede ser input del índice
# ════════════════════════════════════════════════════════════════════════════
def phase_3b_bloque_f():
    print("\n" + "=" * 70)
    print("BLOQUE F — RDD2: Proxy SISFOH como running variable")
    print("=" * 70)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
    except ImportError:
        print("  ADVERTENCIA: scikit-learn no disponible. Saltando BLOQUE F.")
        return

    df_full = pd.read_csv(PATHS["clean_data_full"])

    # ── PASO 1: Filtrar adultos mayores (EDAD >= 65) ──────────────────────
    edad_col = RUNNING_VAR_RAW  # "EDAD"
    df_full[edad_col] = pd.to_numeric(df_full[edad_col], errors="coerce")
    df_mayores = df_full[df_full[edad_col] >= 65].copy().reset_index(drop=True)
    print(f"\n── PASO 1: Construir proxy SISFOH ──")
    print(f"  Adultos mayores (EDAD>=65): {len(df_mayores):,}")

    # ── PASO 1a: Construir HACINAMIENTO si no viene de Fase 1 ─────────────
    # HACINAMIENTO = miembros del hogar / número de cuartos
    # Usamos P104 (cuartos) y MIEPERHO (miembros), ambos verificados en ENAHO 2024
    cuartos_col  = next((c for c in ("P104", "CUARTOS") if c in df_mayores.columns), None)
    mieperho_col = "MIEPERHO" if "MIEPERHO" in df_mayores.columns else None

    if cuartos_col and mieperho_col:
        cuartos  = pd.to_numeric(df_mayores[cuartos_col],  errors="coerce").replace(0, np.nan)
        mieperho = pd.to_numeric(df_mayores[mieperho_col], errors="coerce")
        df_mayores["HACINAMIENTO"] = mieperho / cuartos
        print(f"  HACINAMIENTO construida: media={df_mayores['HACINAMIENTO'].mean():.2f}, "
              f"mediana={df_mayores['HACINAMIENTO'].median():.2f}")
    else:
        df_mayores["HACINAMIENTO"] = np.nan
        print(f"  ADVERTENCIA: HACINAMIENTO no pudo construirse "
              f"(cuartos={cuartos_col}, mieperho={mieperho_col}).")

    # ── Variables PCA — aliases verificados en ENAHO 2024 ─────────────────
    # Cada entrada: nombre_canónico → lista de aliases en orden de preferencia
    # La exploración empírica confirmó los aliases correctos para 2024.
    VAR_CANDIDATES = {
        # Vivienda — Filmer & Pritchett (2001)
        "PARED":        ["P102", "PARED"],          # material paredes
        "PISO":         ["P103", "PISO"],            # material piso
        "ABASTAGUADOM": ["P110", "ABASTAGUADOM"],    # agua
        "SERVSANIT":    ["P111A", "SERVSANIT"],      # saneamiento (alias 2024)
        "ALUMBRADO":    ["P112A", "ALUMBRADO"],      # alumbrado (alias 2024)
        "COMBUSTIBLE":  ["P113A", "COMBUSTIBLE"],    # combustible (alias 2024)
        "HACINAMIENTO": ["HACINAMIENTO"],            # construida arriba
        # Bienes durables — construidos en Fase 1 desde M18 formato long
        "REFRIGERADOR": ["REFRIGERADOR"],            # P612N=4
        "TIENE_TV":     ["TIENE_TV"],                # P612N=2
        "SMARTPHONE":   ["SMARTPHONE"],              # P612N=10
    }

    print("\n  Verificando variables para PCA:")
    pca_cols = {}
    for canon, candidates in VAR_CANDIDATES.items():
        found = next((c for c in candidates if c in df_mayores.columns), None)
        if found:
            pca_cols[canon] = found
            n_valid = df_mayores[found].notna().sum()
            pct_valid = 100 * n_valid / len(df_mayores)
            print(f"    {canon:<15}: encontrada como '{found}' "
                  f"(N válidos={n_valid:,}, {pct_valid:.1f}%)")
        else:
            print(f"    {canon:<15}: ADVERTENCIA — no encontrada "
                  f"(candidatas: {candidates}). Se omite del PCA.")

    if len(pca_cols) < 3:
        print("  ADVERTENCIA: menos de 3 variables PCA disponibles. Saltando BLOQUE F.")
        return

    print(f"\n  Total variables que entran al PCA: {len(pca_cols)}")

    # ── Construir matriz para PCA ─────────────────────────────────────────
    pca_data = df_mayores[[v for v in pca_cols.values()]].copy()
    pca_data.columns = list(pca_cols.keys())
    pca_data = pca_data.apply(pd.to_numeric, errors="coerce")

    # Imputar NaN con mediana por columna (imputación conservadora)
    for col in pca_data.columns:
        n_miss = pca_data[col].isna().sum()
        if n_miss > 0:
            med = pca_data[col].median()
            pca_data[col] = pca_data[col].fillna(med)
            print(f"    Imputados {n_miss:,} NaN en {col} con mediana={med:.2f}")

    print(f"\n  Filas adultos mayores: {len(pca_data):,}")
    print(f"  Variables PCA finales ({len(pca_cols)}): {list(pca_cols.keys())}")

    # ── PCA — 1 componente principal ──────────────────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(pca_data.values)
    pca_model = PCA(n_components=min(3, len(pca_cols)), random_state=RANDOM_SEED)
    components = pca_model.fit_transform(X_scaled)
    pc1 = components[:, 0]

    var_explained = pca_model.explained_variance_ratio_
    print(f"\n  Varianza explicada:")
    for i, ve in enumerate(var_explained):
        print(f"    PC{i+1}: {ve:.1%}")

    # Cargas del PC1 — útil para verificar que el índice tenga sentido
    loadings = pd.Series(pca_model.components_[0], index=list(pca_cols.keys()))
    print(f"\n  Cargas del PC1 (loadings):")
    for var, load in loadings.sort_values(key=abs, ascending=False).items():
        direction = "↑pobre" if load > 0 else "↓pobre"
        print(f"    {var:<15}: {load:+.3f}  ({direction})")

    # Orientar PC1: valores más altos = más pobre
    # Verificar con POBREZA: hogares con POBREZA==1 deben tener PC1 más alto
    if "POBREZA" in df_mayores.columns:
        pob_num = pd.to_numeric(df_mayores["POBREZA"], errors="coerce")
        mean_ep = float(pd.Series(pc1)[pob_num == 1].mean()) if (pob_num == 1).any() else np.nan
        mean_np = float(pd.Series(pc1)[pob_num >= 2].mean()) if (pob_num >= 2).any() else np.nan
        if not np.isnan(mean_ep) and not np.isnan(mean_np):
            print(f"\n  Verificación de orientación:")
            print(f"    Media PC1 (POBREZA=1, extrema pobreza): {mean_ep:.3f}")
            print(f"    Media PC1 (POBREZA>=2, no extrema):     {mean_np:.3f}")
            if mean_ep < mean_np:
                pc1 = -pc1
                print("    → PC1 invertido (extrema pobreza tenía valores menores; corregido).")
            else:
                print("    → Orientación correcta (extrema pobreza ya tiene valores mayores).")
        corr_pob = pd.Series(pc1).corr(pob_num.fillna(pob_num.median()))
        print(f"  Correlación SISFOH_PROXY con POBREZA: {corr_pob:.3f}")
        if abs(corr_pob) < 0.2:
            print("  ADVERTENCIA: correlación baja con POBREZA — revisar variables del PCA.")
    else:
        print("  POBREZA no disponible para verificar orientación del PCA.")

    df_mayores["SISFOH_PROXY"] = pc1

    # ── PASO 2: Definir cutoff SISFOH_PROXY ──────────────────────────────
    print("\n── PASO 2: Definir cutoff SISFOH_PROXY ──")
    # Estrategia: umbral entre la distribución de POBREZA=1 y POBREZA=2
    # entre adultos mayores. Esto aproxima el corte que usa el MIDIS para
    # clasificar extrema pobreza según el proxy means test del SISFOH.
    if "POBREZA" in df_mayores.columns:
        pob = pd.to_numeric(df_mayores["POBREZA"], errors="coerce")
        proxy_ep  = df_mayores.loc[pob == 1, "SISFOH_PROXY"].dropna()
        proxy_nep = df_mayores.loc[pob == 2, "SISFOH_PROXY"].dropna()
        print(f"  N adultos mayores POBREZA=1 (extrema):  {len(proxy_ep):,}")
        print(f"  N adultos mayores POBREZA=2 (pobre):    {len(proxy_nep):,}")
        if len(proxy_ep) > 10 and len(proxy_nep) > 10:
            # Cutoff = promedio entre el máximo de POBREZA=2 y el mínimo de POBREZA=1
            cutoff_sisfoh = (proxy_nep.max() + proxy_ep.min()) / 2
            print(f"  max(POBREZA=2)={proxy_nep.max():.4f}, "
                  f"min(POBREZA=1)={proxy_ep.min():.4f}")
            print(f"  → Cutoff = promedio de ambos extremos")
        else:
            cutoff_sisfoh = df_mayores["SISFOH_PROXY"].median()
            print("  Cutoff calculado como mediana (grupos muy pequeños).")
    else:
        cutoff_sisfoh = df_mayores["SISFOH_PROXY"].median()
        print("  POBREZA no disponible. Cutoff = mediana de SISFOH_PROXY.")

    print(f"  CUTOFF_SISFOH = {cutoff_sisfoh:.4f}")

    df_mayores["running_sisfoh"] = df_mayores["SISFOH_PROXY"] - cutoff_sisfoh
    df_mayores["treat_sisfoh"]   = (df_mayores["running_sisfoh"] >= 0).astype(int)

    n_below = int((df_mayores["running_sisfoh"] < 0).sum())
    n_above = int((df_mayores["running_sisfoh"] >= 0).sum())
    print(f"  Debajo del corte (no extrema pobreza): {n_below:,}")
    print(f"  Encima del corte (extrema pobreza):    {n_above:,}")

    # ── PASO 3: Estimar RDD2 ──────────────────────────────────────────────
    print("\n── PASO 3: Estimación RDD2 ──")
    # Covariables para RDD2: solo predeterminadas, NO endógenas al tratamiento.
    # INTERNET_HOGAR y NIVEL_EDUCATIVO son predeterminadas al ingreso al programa.
    # INGRESO_PC excluida (endógena). SMARTPHONE excluida (también es outcome relevante).
    EP_COVARIATES_F = [c for c in ["INTERNET_HOGAR", "NIVEL_EDUCATIVO"]
                       if c in df_mayores.columns]

    # Remap columnas para que run_rdd() las encuentre con sus nombres globales
    df_rdd2 = df_mayores.copy()
    df_rdd2[RUNNING_VAR] = df_rdd2["running_sisfoh"]
    df_rdd2["treat"]     = df_rdd2["treat_sisfoh"]

    rdd2_results = []
    for outcome in [o for o in OUTCOME_VARS if o in df_rdd2.columns]:
        print(f"\n  Outcome: {outcome}")

        sub = df_rdd2.dropna(subset=["running_sisfoh", outcome]).copy()
        if len(sub) < 100:
            print(f"    Insuficiente muestra (N={len(sub)}). Saltando.")
            continue

        # Baseline sin covariables
        res_b = run_rdd(sub, outcome, label="RDD2_SISFOH_baseline")
        res_b["outcome"] = outcome
        rdd2_results.append(res_b)

        bw     = res_b.get("bandwidth", np.nan)
        n_eff  = res_b.get("N_eff", 0)
        print(f"    [RDD2_SISFOH_baseline]    "
              f"est={res_b['estimate']:.4f}  SE={res_b['se_robust']:.4f}")
        if not np.isnan(bw):
            print(f"    BW={bw:.3f}  N_eff={n_eff}  Method={res_b['method']}")

        # Con covariables predeterminadas
        if EP_COVARIATES_F:
            res_cov = run_rdd(sub, outcome,
                              covariates=EP_COVARIATES_F,
                              label="RDD2_SISFOH_covariates")
            res_cov["outcome"] = outcome
            rdd2_results.append(res_cov)
            print(f"    [RDD2_SISFOH_covariates]  "
                  f"est={res_cov['estimate']:.4f}  SE={res_cov['se_robust']:.4f}")

        # Reporte de observaciones a cada lado del corte dentro del bandwidth
        if not np.isnan(bw):
            in_bw      = sub[sub["running_sisfoh"].abs() <= bw]
            n_bw_below = int((in_bw["running_sisfoh"] < 0).sum())
            n_bw_above = int((in_bw["running_sisfoh"] >= 0).sum())
            print(f"    Dentro del BW ±{bw:.2f}: "
                  f"debajo={n_bw_below}, encima={n_bw_above}")
            if n_bw_below < 100 or n_bw_above < 100:
                print(f"    ADVERTENCIA: bajo poder estadístico (N<100 en un lado).")
                res_b["low_power"] = True

            m_below = in_bw.loc[in_bw["running_sisfoh"] < 0, outcome].mean()
            m_above = in_bw.loc[in_bw["running_sisfoh"] >= 0, outcome].mean()
            print(f"    Media {outcome}: "
                  f"debajo (no pobre)={m_below:.4f}, encima (pobre)={m_above:.4f}")

    # ── PASO 4: Diagnósticos ──────────────────────────────────────────────
    print("\n── PASO 4: Diagnósticos RDD2 ──")

    # 4.1 Gráfico de densidad del running variable SISFOH
    fig, ax = plt.subplots(figsize=(8, 5))
    valid_rs = df_mayores["running_sisfoh"].dropna()
    window   = min(valid_rs.abs().quantile(0.95), 5)
    plot_vals = valid_rs[valid_rs.abs() <= window]
    ax.hist(plot_vals[plot_vals < 0],  bins=40, color="#2166ac", alpha=0.7,
            label="No extrema pobreza (proxy)")
    ax.hist(plot_vals[plot_vals >= 0], bins=40, color="#b2182b", alpha=0.7,
            label="Extrema pobreza (proxy)")
    ax.axvline(x=0, color="black", linestyle="--", linewidth=1.5,
               label="Cutoff SISFOH proxy")
    ax.set_xlabel("SISFOH_PROXY centrado en cutoff", fontsize=11)
    ax.set_ylabel("Frecuencia", fontsize=11)
    ax.set_title(
        "RDD2: Densidad del índice de bienestar proxy (adultos ≥65)\n"
        f"PCA sobre {len(pca_cols)} variables ENAHO 2024 — "
        f"PC1 explica {var_explained[0]:.1%} de la varianza",
        fontsize=11
    )
    ax.legend(fontsize=9)
    plt.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIGURES_DIR / f"figure_rdd2_density.{ext}",
                    dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Guardado: figure_rdd2_density.png/.pdf")

    # 4.2 RD plot: billetera digital vs índice SISFOH proxy
    outcome_rdplot = "TIENE_BILLETERA"
    if outcome_rdplot in df_mayores.columns:
        sub_plot  = df_mayores.dropna(
            subset=["running_sisfoh", outcome_rdplot]
        ).copy()
        sub_plot  = sub_plot[sub_plot["running_sisfoh"].between(-3, 3)]
        bin_width = 0.2
        bins      = np.arange(-3, 3 + bin_width, bin_width)
        bin_centers, bin_means, bin_side = [], [], []
        for i in range(len(bins) - 1):
            lo, hi = bins[i], bins[i + 1]
            mask   = (sub_plot["running_sisfoh"] >= lo) & \
                     (sub_plot["running_sisfoh"] <  hi)
            if mask.sum() >= 3:
                bin_centers.append((lo + hi) / 2)
                bin_means.append(sub_plot.loc[mask, outcome_rdplot].mean())
                bin_side.append("left" if (lo + hi) / 2 < 0 else "right")

        bin_centers = np.array(bin_centers)
        bin_means   = np.array(bin_means)
        bin_side    = np.array(bin_side)

        fig2, ax2 = plt.subplots(figsize=(8, 5))
        left_m  = bin_side == "left"
        right_m = bin_side == "right"
        ax2.scatter(bin_centers[left_m],  bin_means[left_m],
                    color="#2166ac", s=55, zorder=3, label="No extrema pobreza")
        ax2.scatter(bin_centers[right_m], bin_means[right_m],
                    color="#b2182b", s=55, zorder=3, label="Extrema pobreza")

        for mask_side, color in [(left_m, "#2166ac"), (right_m, "#b2182b")]:
            xs = sub_plot.loc[
                sub_plot["running_sisfoh"] < 0
                if mask_side is left_m
                else sub_plot["running_sisfoh"] >= 0,
                "running_sisfoh"
            ].values
            ys = sub_plot.loc[
                sub_plot["running_sisfoh"] < 0
                if mask_side is left_m
                else sub_plot["running_sisfoh"] >= 0,
                outcome_rdplot
            ].values
            if len(xs) > 5:
                coeffs  = np.polyfit(xs, ys, 1)
                xrange  = np.linspace(xs.min(), xs.max(), 200)
                ax2.plot(xrange, np.poly1d(coeffs)(xrange),
                         color=color, linewidth=2)

        ax2.axvline(x=0, color="black", linestyle="--",
                    linewidth=1.3, alpha=0.8, label="Cutoff SISFOH")
        ax2.set_xlim(-3, 3)
        ax2.set_xlabel(
            "SISFOH_PROXY centrado en cutoff (índice de bienestar)", fontsize=11
        )
        ax2.set_ylabel("Proporción con billetera digital", fontsize=11)
        ax2.set_title(
            "RDD2: Digital Wallet Ownership by SISFOH Welfare Index\n"
            "(Adults 65+, following Bando, Galiani and Gertler 2020)",
            fontsize=11
        )
        ax2.legend(fontsize=9)
        plt.tight_layout()
        for ext in ("png", "pdf"):
            fig2.savefig(FIGURES_DIR / f"figure_rdd2_rdplot.{ext}",
                         dpi=150, bbox_inches="tight")
        plt.close(fig2)
        print("  Guardado: figure_rdd2_rdplot.png/.pdf")

    # 4.3 Balance de covariables en el nuevo cutoff
    print("\n  Balance de covariables en cutoff SISFOH_PROXY:")
    balance_covs = [c for c in ["INTERNET_HOGAR", "NIVEL_EDUCATIVO", "INGRESO_PC"]
                    if c in df_rdd2.columns]
    balance_results = []
    for cov in balance_covs:
        sub_cov = df_rdd2.dropna(subset=["running_sisfoh", cov]).copy()
        if len(sub_cov) < 50:
            continue
        res_bal = run_rdd(sub_cov, cov, label=f"RDD2_SISFOH_balance_{cov}")
        res_bal["outcome"] = cov
        balance_results.append(res_bal)
        sig = "*" if abs(res_bal["estimate"]) > 1.96 * res_bal["se_robust"] else ""
        print(f"    {cov:<20}: est={res_bal['estimate']:.4f}  "
              f"SE={res_bal['se_robust']:.4f}  {sig}")
    if not balance_results:
        print("    (no hay covariables disponibles para balance)")

    # 4.4 Guardar datasets y resultados
    df_mayores.to_csv(PATHS["rdd2_mayores"], index=False)
    print(f"\n  Guardado: {PATHS['rdd2_mayores']}")

    all_rdd2 = rdd2_results + balance_results
    if all_rdd2:
        pd.DataFrame(all_rdd2).to_csv(PATHS["rdd2_results"], index=False)
        print(f"  Guardado: {PATHS['rdd2_results']} ({len(all_rdd2)} filas)")
    else:
        print("  ADVERTENCIA: no hay resultados RDD2 para guardar.")

    # 4.5 Resumen del índice construido
    print("\n── RESUMEN ÍNDICE SISFOH_PROXY ──")
    proxy = df_mayores["SISFOH_PROXY"]
    print(f"  N adultos mayores: {proxy.notna().sum():,}")
    print(f"  Media:   {proxy.mean():.4f}")
    print(f"  Std:     {proxy.std():.4f}")
    print(f"  Min:     {proxy.min():.4f}")
    print(f"  Max:     {proxy.max():.4f}")
    print(f"  Cutoff:  {cutoff_sisfoh:.4f}")
    print(f"  Variables usadas en PCA: {list(pca_cols.keys())}")
    print(f"  Varianza explicada PC1:  {var_explained[0]:.1%}")
