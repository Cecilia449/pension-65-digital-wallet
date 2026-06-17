import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv('data/clean/enaho_2024_clean.csv', encoding='utf-8', low_memory=False)
ifh = pd.read_csv('data/clean/ifh_2024.csv', encoding='utf-8', low_memory=False)

df['IFH']          = ifh['IFH']
df['ELEGIBLE_IFH'] = ifh['ELEGIBLE_IFH']
df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
df['EDAD_C']  = df['EDAD'] - 65
df['MAYOR65'] = (df['EDAD'] >= 65).astype(int)
# AREA: 1=urbano, 2=rural (numerico en CSV). Rural es categoria base.
df['AREA_urbano'] = (pd.to_numeric(df['AREA'], errors='coerce') == 1).astype(int)

sub = df[
    (df['ELEGIBLE_IFH'] == 1) &
    (df['EDAD_C'] >= -5) &
    (df['EDAD_C'] <= 5)
].copy()
print(f'Submuestra base: N={len(sub):,}')

def ols_hc1(X, y):
    mask = ~np.isnan(y) & ~np.any(np.isnan(X), axis=1)
    X_, y_ = X[mask], y[mask]
    n, k = X_.shape
    coef = np.linalg.lstsq(X_, y_, rcond=None)[0]
    resid = y_ - X_ @ coef
    XtX_inv = np.linalg.inv(X_.T @ X_)
    meat = X_.T @ np.diag(resid**2) @ X_
    vcov = (n / (n - k)) * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(vcov))
    t_stats = coef / se
    p_vals = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-k))
    return coef, se, t_stats, p_vals, n

def iv_se(coef_rf, se_rf, coef_fs, se_fs):
    var_iv = ((1/coef_fs**2) * se_rf**2 +
              (coef_rf**2 / coef_fs**4) * se_fs**2)
    return np.sqrt(var_iv)

def sig(p):
    return ('***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else 'n.s.')

OUTCOMES = [
    ('TIENE_BILLETERA', 'Billetera digital (tenencia o uso)'),
    ('USA_BILLETERA',   'Billetera digital (solo uso activo)'),
    ('BANCO_PREVIO',    'Cuenta bancaria (combinada)'),
    ('BANCO_PRIVADO',   'Cuenta en banco privado'),
    ('BANCO_NACION',    'Cuenta en Banco de la Nacion'),
]

resultados = []

for outcome_var, outcome_label in OUTCOMES:
    for con_controles in [False, True]:

        vars_needed = ['EDAD_C', 'MAYOR65', 'RECIBE_P65_PERSONA', outcome_var]
        if con_controles:
            vars_needed += ['NIVEL_EDUCATIVO', 'AREA_urbano', 'POBREZA']
        ventana = sub.dropna(subset=vars_needed).copy()
        N = len(ventana)
        etiqueta = 'Con controles' if con_controles else 'Sin controles'

        print(f"\n{'='*65}")
        print(f'OUTCOME: {outcome_label}')
        print(f'Especificacion: {etiqueta} | N={N:,}')
        print(f"{'='*65}")

        cols_base = [
            np.ones(N),
            ventana['MAYOR65'].values,
            ventana['EDAD_C'].values,
            (ventana['MAYOR65'] * ventana['EDAD_C']).values,
        ]
        if con_controles:
            cols_base += [
                ventana['NIVEL_EDUCATIVO'].values,
                ventana['AREA_urbano'].values,
                ventana['POBREZA'].values,
            ]
        X = np.column_stack(cols_base)

        # First Stage: RECIBE_P65_PERSONA ~ MAYOR65 + controles
        y_fs = ventana['RECIBE_P65_PERSONA'].values.astype(float)
        coef_fs, se_fs, t_fs, p_fs, n_fs = ols_hc1(X, y_fs)
        fs = coef_fs[1]; fs_se = se_fs[1]; fs_p = p_fs[1]
        print(f'First Stage (MAYOR65 -> P65):')
        print(f'  coef = {fs:.4f}  SE = {fs_se:.4f}  p = {fs_p:.4f} {sig(fs_p)}')

        # Reduced Form: outcome ~ MAYOR65 + controles
        y_rf = ventana[outcome_var].values.astype(float)
        coef_rf, se_rf, t_rf, p_rf, n_rf = ols_hc1(X, y_rf)
        rf = coef_rf[1]; rf_se = se_rf[1]; rf_p = p_rf[1]
        print(f'Reduced Form (MAYOR65 -> {outcome_var}):')
        print(f'  coef = {rf:.4f}  SE = {rf_se:.4f}  p = {rf_p:.4f} {sig(rf_p)}')

        # LATE = RF / FS
        late = rf / fs
        late_se = iv_se(rf, rf_se, fs, fs_se)
        late_p  = 2 * (1 - stats.norm.cdf(abs(late / late_se)))
        ic_lo   = late - 1.96 * late_se
        ic_hi   = late + 1.96 * late_se
        print(f'LATE (IV):')
        print(f'  coef = {late:.4f}  SE = {late_se:.4f}  p = {late_p:.4f} {sig(late_p)}')
        print(f'  IC 95%: [{ic_lo:.3f}, {ic_hi:.3f}]')

        resultados.append({
            'outcome':        outcome_var,
            'especificacion': etiqueta,
            'N':              N,
            'fs_coef':        round(fs, 4),
            'fs_se':          round(fs_se, 4),
            'fs_p':           round(fs_p, 4),
            'fs_sig':         sig(fs_p),
            'rf_coef':        round(rf, 4),
            'rf_se':          round(rf_se, 4),
            'rf_p':           round(rf_p, 4),
            'rf_sig':         sig(rf_p),
            'late':           round(late, 4),
            'late_se':        round(late_se, 4),
            'late_p':         round(late_p, 4),
            'late_sig':       sig(late_p),
            'ic95_lo':        round(ic_lo, 3),
            'ic95_hi':        round(ic_hi, 3),
        })

out = pd.DataFrame(resultados)
out.to_csv('data/clean/resultados_rdd_ampliado.csv', index=False)
print(f'\n\nGuardado: data/clean/resultados_rdd_ampliado.csv')
print(out[['outcome','especificacion','N','fs_coef','fs_sig',
           'late','late_se','late_p','late_sig']].to_string(index=False))
