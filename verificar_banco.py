import pandas as pd

df = pd.read_csv("data/clean/enaho_2024_clean.csv",
                 encoding="utf-8", low_memory=False)
ifh = pd.read_csv("data/clean/ifh_2024.csv",
                  encoding="utf-8", low_memory=False)

df['ELEGIBLE_IFH'] = ifh['ELEGIBLE_IFH']
df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
df['EDAD_C'] = df['EDAD'] - 65

sub = df[
    (df['ELEGIBLE_IFH'] == 1) &
    (df['EDAD_C'] >= -5) &
    (df['EDAD_C'] <= 5)
].copy()

print(f"Submuestra: N={len(sub):,}")
print()

for var in ['BANCO_PREVIO', 'BANCO_PRIVADO', 'BANCO_NACION']:
    if var in sub.columns:
        izq = sub[sub['EDAD_C'] < 0][var].mean()
        der = sub[sub['EDAD_C'] >= 0][var].mean()
        print(f"{var}:")
        print(f"  Total:         {100*sub[var].mean():.1f}%")
        print(f"  Antes de 65:   {100*izq:.1f}%")
        print(f"  Despues de 65: {100*der:.1f}%")
        print(f"  Salto bruto:   {100*(der-izq):.1f} pp")
        print()
    else:
        print(f"{var}: NO ENCONTRADA -- el cambio no funciono")
        print()
