import pandas as pd
import numpy as np

df = pd.read_csv("data/clean/enaho_2024_clean.csv",
                 encoding="utf-8", low_memory=False)
ifh = pd.read_csv("data/clean/ifh_2024.csv",
                  encoding="utf-8", low_memory=False)
res = pd.read_csv("data/clean/resultados_rdd_ampliado.csv",
                  encoding="utf-8", low_memory=False)

df['IFH']          = ifh['IFH']
df['ELEGIBLE_IFH'] = ifh['ELEGIBLE_IFH']
df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
df['EDAD_C'] = df['EDAD'] - 65

sub = df[
    (df['ELEGIBLE_IFH'] == 1) &
    (df['EDAD_C'] >= -5) &
    (df['EDAD_C'] <= 5)
].copy()

izq = sub[sub['EDAD_C'] < 0]
der = sub[sub['EDAD_C'] >= 0]

print("=== MUESTRA GENERAL ===")
print(f"Total personas: {len(df):,}")
print(f"Total hogares: {df.drop_duplicates(['CONGLOME','VIVIENDA','HOGAR']).shape[0]:,}")
print(f"Hogares con IFH: {ifh['IFH'].notna().sum():,} ({100*ifh['IFH'].notna().mean():.1f}%)")

print("\n=== IFH ===")
print(ifh['IFH'].describe().round(2))

print("\n=== VALIDACION IFH vs POBREZA ===")
if 'POBREZA' in df.columns:
    print(df.groupby('POBREZA')['IFH'].mean().round(2))
    corr = df[['IFH','POBREZA']].dropna().corr().iloc[0,1]
    print(f"Correlacion: {corr:.4f}")

print("\n=== ELEGIBILIDAD ===")
print(f"Elegibles IFH: {ifh['ELEGIBLE_IFH'].sum():,} ({100*ifh['ELEGIBLE_IFH'].mean():.1f}%)")
print(f"Elegibles SIS: {ifh['ELEGIBLE_SIS'].sum():,} ({100*ifh['ELEGIBLE_SIS'].mean():.1f}%)")

print("\n=== SUBMUESTRA RDD ===")
print(f"N total ventana +-5: {len(sub):,}")
print(f"Izquierda (<65): {len(izq):,}")
print(f"Derecha (>=65): {len(der):,}")

print("\n=== FIRST STAGE ===")
fs_izq = izq['RECIBE_P65_PERSONA'].mean()
fs_der = der['RECIBE_P65_PERSONA'].mean()
print(f"P65 <65: {100*fs_izq:.1f}%")
print(f"P65 >=65: {100*fs_der:.1f}%")
print(f"Salto: {100*(fs_der-fs_izq):.1f} pp")

print("\n=== OUTCOMES EN SUBMUESTRA ===")
for var in ['TIENE_BILLETERA','USA_BILLETERA',
            'BANCO_PREVIO','BANCO_PRIVADO','BANCO_NACION']:
    if var in sub.columns:
        v_izq = izq[var].mean()
        v_der = der[var].mean()
        print(f"{var}: <65={100*v_izq:.1f}% | >=65={100*v_der:.1f}% | salto={100*(v_der-v_izq):.1f} pp")

print("\n=== RESULTADOS RDD ===")
print(res.to_string(index=False))

print("\n=== IFH Y PENSION 65 ===")
m65 = df[df['EDAD'] >= 65]
rec   = m65[m65['RECIBE_P65_PERSONA'] == 1]
norec = m65[m65['RECIBE_P65_PERSONA'] == 0]
print(f"IFH promedio receptores P65: {rec['IFH'].mean():.2f}")
print(f"IFH promedio no receptores:  {norec['IFH'].mean():.2f}")
