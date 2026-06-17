import pandas as pd
import numpy as np

df = pd.read_csv("data/clean/enaho_2024_clean.csv",
                 encoding="utf-8", low_memory=False)
ifh = pd.read_csv("data/clean/ifh_2024.csv",
                  encoding="utf-8", low_memory=False)

df['IFH']          = ifh['IFH']
df['ELEGIBLE_IFH'] = ifh['ELEGIBLE_IFH']
df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
df['EDAD_C']  = df['EDAD'] - 65
df['MAYOR65'] = (df['EDAD'] >= 65).astype(int)

print("=== VERIFICACION DE VARIABLES FUENTE ===")
for col in ['P558E1_1', 'P558E1_8']:
    if col in df.columns:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).head(10))
    else:
        print(f"\n{col}: NO ENCONTRADA en el dataset")

if 'P558E1_1' in df.columns:
    df['BANCO_PRIVADO'] = (
        df['P558E1_1'].astype(str).str.strip() == '1'
    ).astype(int)
else:
    df['BANCO_PRIVADO'] = 0
    print("BANCO_PRIVADO creada como cero (P558E1_1 no disponible)")

if 'P558E1_8' in df.columns:
    df['BANCO_NACION'] = (
        df['P558E1_8'].astype(str).str.strip() == '8'
    ).astype(int)
else:
    df['BANCO_NACION'] = 0
    print("BANCO_NACION creada como cero (P558E1_8 no disponible)")

sub = df[
    (df['ELEGIBLE_IFH'] == 1) &
    (df['EDAD_C'] >= -5) &
    (df['EDAD_C'] <= 5)
].copy()

print(f"\n=== SUBMUESTRA: N={len(sub):,} ===")

for var in ['BANCO_PRIVADO', 'BANCO_NACION', 'BANCO_PREVIO']:
    if var in sub.columns:
        izq = sub[sub['EDAD_C'] < 0][var].mean()
        der = sub[sub['EDAD_C'] >= 0][var].mean()
        print(f"\n{var}:")
        print(f"  Total: {100*sub[var].mean():.1f}%")
        print(f"  Antes de 65:   {100*izq:.1f}%")
        print(f"  Despues de 65: {100*der:.1f}%")
        print(f"  Salto bruto:   {100*(der-izq):.1f} pp")
