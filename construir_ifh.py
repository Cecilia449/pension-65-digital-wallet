import pandas as pd
import numpy as np

KEYS_HOUSEHOLD = ['CONGLOME', 'VIVIENDA', 'HOGAR']

df = pd.read_csv(
    "data/clean/enaho_2024_clean.csv",
    encoding="utf-8", low_memory=False
)
print(f"Dataset cargado: {df.shape}")

# ════════════════════════════════════════════════
# CORRECCIÓN 1 — COMBUSTIBLE=9.0 → tratar como 7
# En ENAHO 2024 código 9 = "No cocina/No aplica"
# equivalente al código 7 del Apéndice F
# ════════════════════════════════════════════════
df['COMBUSTIBLE_LIMPIO'] = pd.to_numeric(
    df['COMBUSTIBLE'], errors='coerce'
)
n_antes = (df['COMBUSTIBLE_LIMPIO'] == 9.0).sum()
df['COMBUSTIBLE_LIMPIO'] = df['COMBUSTIBLE_LIMPIO'].replace(9.0, 7.0)
print(f"\nCOMBUSTIBLE: {n_antes:,} registros con código 9 "
      f"reclasificados como 7")
print("Distribución post-corrección:")
print(df['COMBUSTIBLE_LIMPIO'].value_counts().sort_index())

# ════════════════════════════════════════════════
# CORRECCIÓN 2 — Reconstruir IFH con COMBUSTIBLE
# corregido y pesos del Apéndice F
# ════════════════════════════════════════════════

PESOS_COMBUSTIBLE = {
    'lima':   {7:-0.49, 5:-0.40, 4:-0.37, 3:-0.33,
               2:-0.29, 1:0.02,  6:0.43},
    'urbano': {7:-0.67, 5:-0.50, 4:-0.33, 3:-0.22,
               2:-0.19, 1:0.12,  6:0.69},
    'rural':  {7:-0.76, 5:-0.38, 4:0.05,  3:0.36,
               2:0.37,  1:0.52,  6:0.52},
}
PESOS_AGUA = {
    'lima':   {8:-0.78, 6:-0.65, 7:-0.65, 5:-0.62,
               4:-0.51, 3:-0.41, 2:-0.35, 1:0.10},
    'urbano': {8:-0.58, 6:-0.42, 7:-0.42, 5:-0.37,
               4:-0.34, 3:-0.32, 2:-0.25, 1:0.12},
    'rural':  {8:-0.78, 6:-0.65, 7:-0.65, 5:-0.62,
               4:-0.51, 3:-0.41, 2:-0.35, 1:0.10},
}
PESOS_PAREDES = {
    'lima':   {7:-0.70, 9:-0.70, 6:-0.48, 5:-0.41,
               8:-0.44, 4:-0.48, 3:-0.37, 2:-0.33, 1:0.10},
    'urbano': {7:-0.80, 9:-0.80, 6:-0.55, 5:-0.43,
               8:-0.46, 4:-0.55, 3:-0.20, 2:-0.07, 1:0.25},
    'rural':  {7:-0.80, 9:-0.80, 6:-0.55, 5:-0.43,
               8:-0.46, 4:-0.55, 3:-0.20, 2:-0.07, 1:0.25},
}
PESOS_TECHO = {
    'lima':   {7:-0.86, 6:-0.74, 5:-0.67, 4:-0.38,
               3:-0.23, 2:-0.21, 1:0.17},
    'urbano': {7:-0.90, 6:-0.72, 5:-0.62, 4:-0.23,
               3:0.03,  2:0.07,  1:0.32},
    'rural':  {7:-0.90, 6:-0.72, 5:-0.62, 4:-0.23,
               3:0.03,  2:0.07,  1:0.32},
}
PESOS_PISO = {
    'lima':   {7:-0.97, 6:-0.60, 5:-0.16, 4:0.08,
               3:0.16,  2:0.28,  1:0.51},
    'urbano': {7:-1.12, 6:-0.47, 5:-0.01, 4:0.30,
               3:0.40,  2:0.51,  1:0.71},
    'rural':  {7:-1.12, 6:-0.47, 5:-0.01, 4:0.30,
               3:0.40,  2:0.51,  1:0.71},
}
PESOS_DESAGUE = {
    'lima':   {9:-0.89, 6:-0.89, 7:-0.75, 5:-0.75,
               4:-0.59, 3:-0.46, 2:-0.39, 1:0.10},
    'urbano': {9:-0.68, 6:-0.68, 7:-0.49, 5:-0.49,
               4:-0.40, 3:-0.30, 2:-0.21, 1:0.20},
    'rural':  {9:-0.68, 6:-0.68, 7:-0.49, 5:-0.49,
               4:-0.40, 3:-0.30, 2:-0.21, 1:0.20},
}
PESOS_SEGURO = {
    'lima':   {0:-0.26, 1:-0.04, 2:0.06, 3:0.14, 4:0.32},
    'urbano': {0:-0.25, 1:0.06,  2:0.17, 3:0.27, 4:0.48},
    'rural':  {0:-0.10, 1:0.50,  2:0.59, 3:0.66, 4:0.86},
}
PESOS_BIENES = {
    'lima':   {0:-0.47, 1:-0.17, 2:0.02, 3:0.15, 4:0.25, 5:0.47},
    'urbano': {0:-0.35, 1:0.05,  2:0.25, 3:0.40, 4:0.52, 5:0.75},
    'rural':  {0:-0.11, 1:0.64,  2:0.83, 3:0.90, 4:1.09, 5:1.09},
}
PESOS_HACINAMIENTO = {
    'lima': {
        'menos_1':   0.24,
        'entre_1_2': -0.07,
        'entre_2_4': -0.31,
        'entre_4_6': -0.51,
        'mas_6':     -0.68,
    }
}
PESOS_EDUC_JEFE = {
    'lima':   {1:-0.51, 2:-0.43, 3:-0.28, 4:-0.06,
               5:0.10,  6:0.10,  11:0.10,
               7:0.22,  8:0.22,  9:0.40,  10:-0.28},
    'urbano': {1:-0.57, 2:-0.25, 3:0.01,  4:0.19,
               5:0.33,  6:0.33,  11:0.33,
               7:0.55,  8:0.55,  9:0.55,  10:0.01},
    'rural':  {1:-0.59, 2:-0.08, 3:0.35,  4:0.59,
               5:0.68,  6:0.68,  11:0.68,
               7:0.88,  8:0.88,  9:0.88,  10:0.35},
}
PESOS_MAX_EDUC = {
    'lima': {1:-0.35, 2:-0.35, 3:0.11,  4:0.41,
             5:0.62,  6:0.62,  11:0.62,
             7:0.83,  8:0.83,  9:0.83,  10:0.11}
}
PESOS_ELECTRICIDAD = {
    'rural': {1:0.22, 2:-0.29, 3:-0.29}
}

def aplicar_peso(df, col, pesos_dict, nombre):
    resultado = pd.Series(np.nan, index=df.index)
    for area, pesos in pesos_dict.items():
        mask = df['AREA_SISFOH'] == area
        col_num = pd.to_numeric(df.loc[mask, col], errors='coerce')
        resultado.loc[mask] = col_num.map(pesos)
    n_nan = resultado.isna().sum()
    if n_nan > 0:
        print(f"  {nombre}: {n_nan:,} nulos ({100*n_nan/len(df):.1f}%)")
    return resultado

# Hacinamiento
df['P104_num'] = pd.to_numeric(
    df['P104'], errors='coerce'
).replace(0, np.nan)
df['HACINAMIENTO'] = df['MIEPERHO'] / df['P104_num']
def cat_hac(h):
    if pd.isna(h):  return np.nan
    if h < 1:       return 'menos_1'
    elif h <= 2:    return 'entre_1_2'
    elif h <= 4:    return 'entre_2_4'
    elif h <= 6:    return 'entre_4_6'
    else:           return 'mas_6'
df['HAC_CAT'] = df['HACINAMIENTO'].apply(cat_hac)

# Bienes
df['N_BIENES'] = (
    df['REFRIGERADOR'].fillna(0) +
    df['TIENE_TV'].fillna(0) +
    df['SMARTPHONE'].fillna(0)
).clip(upper=5).astype(int)

# Aplicar pesos
print("\nAplicando pesos (versión corregida):")
df['w_combustible'] = aplicar_peso(
    df, 'COMBUSTIBLE_LIMPIO', PESOS_COMBUSTIBLE, 'combustible'
)
df['w_agua']        = aplicar_peso(df, 'P110', PESOS_AGUA, 'agua')
df['w_paredes']     = aplicar_peso(df, 'P102', PESOS_PAREDES, 'paredes')
df['w_techo']       = aplicar_peso(df, 'TECHO', PESOS_TECHO, 'techo')
df['w_piso']        = aplicar_peso(df, 'P103', PESOS_PISO, 'piso')
df['w_desague']     = aplicar_peso(
    df, 'SERVSANIT', PESOS_DESAGUE, 'desague'
)
df['w_seguro']      = aplicar_peso(
    df, 'N_SEGURO_NO_SIS', PESOS_SEGURO, 'seguro'
)
df['w_bienes']      = aplicar_peso(
    df, 'N_BIENES', PESOS_BIENES, 'bienes'
)
df['w_educ_jefe']   = aplicar_peso(
    df, 'EDUC_JEFE', PESOS_EDUC_JEFE, 'educ_jefe'
)

mask_lima  = df['AREA_SISFOH'] == 'lima'
mask_rural = df['AREA_SISFOH'] == 'rural'

df['w_hacinamiento'] = np.nan
df.loc[mask_lima, 'w_hacinamiento'] = (
    df.loc[mask_lima, 'HAC_CAT'].map(PESOS_HACINAMIENTO['lima'])
)
df['w_max_educ'] = np.nan
df.loc[mask_lima, 'w_max_educ'] = (
    pd.to_numeric(df.loc[mask_lima, 'MAX_EDUC_HOGAR'], errors='coerce')
    .map(PESOS_MAX_EDUC['lima'])
)
df['w_electricidad'] = np.nan
df.loc[mask_rural, 'w_electricidad'] = (
    pd.to_numeric(df.loc[mask_rural, 'ALUMBRADO'], errors='coerce')
    .map(PESOS_ELECTRICIDAD['rural'])
)

# IFH_RAW
vars_comunes = [
    'w_combustible','w_agua','w_paredes','w_techo',
    'w_piso','w_desague','w_seguro','w_bienes','w_educ_jefe'
]
df['IFH_RAW'] = df[vars_comunes].sum(axis=1, skipna=False)
df.loc[mask_lima, 'IFH_RAW'] = (
    df.loc[mask_lima, vars_comunes +
           ['w_hacinamiento','w_max_educ']]
    .sum(axis=1, skipna=False)
)
df.loc[mask_rural, 'IFH_RAW'] = (
    df.loc[mask_rural, vars_comunes + ['w_electricidad']]
    .sum(axis=1, skipna=False)
)

print("\nIFH_RAW — estadísticas:")
print(df['IFH_RAW'].describe())
print("Nulos en IFH_RAW:", df['IFH_RAW'].isna().sum())

# ════════════════════════════════════════════════
# CORRECCIÓN 3 — Estandarizar y aplicar umbrales
# correctos por departamento (Tabla A.10)
# ════════════════════════════════════════════════

def estandarizar(x):
    rng = x.max() - x.min()
    if rng == 0:
        return pd.Series(50.0, index=x.index)
    return 100 * (x - x.min()) / rng

df['IFH'] = df.groupby('DPTO')['IFH_RAW'].transform(estandarizar)

print("\nIFH estandarizado [0-100]:")
print(df['IFH'].describe())
print("Nulos en IFH:", df['IFH'].isna().sum())

# Umbrales por departamento (Tabla A.10 Apéndice F)
UMBRALES_DPTO = {
    15:55, 1:50,  2:44,  3:44,  4:44,
    5:50,  6:52,  7:52,  8:42,  9:44,
    10:44, 11:50, 12:42, 13:52, 14:43,
    16:43, 17:43, 18:38, 19:35, 20:36,
    21:34, 22:52, 23:33, 24:34, 25:36,
}
df['UMBRAL'] = df['DPTO'].map(UMBRALES_DPTO)

df['ELEGIBLE_IFH']   = (df['IFH'] <= df['UMBRAL']).astype(int)
df['ELEGIBLE_AGUA']  = (df['GASTO_AGUA_MENSUAL'] <= 20).astype(int)
df['ELEGIBLE_ELECTR']= (df['GASTO_ELECTR_MENSUAL'] <= 25).astype(int)
df['ELEGIBLE_SIS']   = (
    (df['ELEGIBLE_IFH']   == 1) &
    (df['ELEGIBLE_AGUA']  == 1) &
    (df['ELEGIBLE_ELECTR']== 1)
).astype(int)

print("\nElegibilidad SIS (versión final):")
print(f"  Elegibles por IFH (umbral x dpto): "
      f"{df['ELEGIBLE_IFH'].sum():,} "
      f"({100*df['ELEGIBLE_IFH'].mean():.1f}%)")
print(f"  Elegibles por agua (<=20 s/mes):   "
      f"{df['ELEGIBLE_AGUA'].sum():,} "
      f"({100*df['ELEGIBLE_AGUA'].mean():.1f}%)")
print(f"  Elegibles por electr (<=25 s/mes): "
      f"{df['ELEGIBLE_ELECTR'].sum():,} "
      f"({100*df['ELEGIBLE_ELECTR'].mean():.1f}%)")
print(f"  ELEGIBLES SIS FINAL (los 3):        "
      f"{df['ELEGIBLE_SIS'].sum():,} "
      f"({100*df['ELEGIBLE_SIS'].mean():.1f}%)")

# Validación final
if 'POBREZA' in df.columns:
    print("\nValidación IFH vs POBREZA:")
    print(df.groupby('POBREZA')['IFH'].mean().round(2))
    corr = df[['IFH','POBREZA']].dropna().corr().iloc[0,1]
    print(f"Correlación IFH-POBREZA: {corr:.4f}")

# Guardar
cols_ifh = [
    'w_combustible','w_agua','w_paredes','w_techo','w_piso',
    'w_desague','w_seguro','w_bienes','w_educ_jefe',
    'w_hacinamiento','w_max_educ','w_electricidad',
    'IFH_RAW','IFH','UMBRAL',
    'ELEGIBLE_IFH','ELEGIBLE_AGUA','ELEGIBLE_ELECTR','ELEGIBLE_SIS'
]
df[cols_ifh].to_csv(
    "data/clean/ifh_2024.csv", index=False, encoding="utf-8"
)
df.to_csv(
    "data/clean/enaho_2024_clean.csv", index=False, encoding="utf-8"
)
print("\nGuardado: ifh_2024.csv y enaho_2024_clean.csv")
print("IFH construido. Script completado.")
