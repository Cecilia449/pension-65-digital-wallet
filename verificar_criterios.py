import pandas as pd
import numpy as np

df = pd.read_csv("data/clean/enaho_2024_clean.csv",
                 encoding="utf-8", low_memory=False)
ifh = pd.read_csv("data/clean/ifh_2024.csv",
                  encoding="utf-8", low_memory=False)

df['IFH']          = ifh['IFH']
df['ELEGIBLE_IFH'] = ifh['ELEGIBLE_IFH']
df['ELEGIBLE_SIS'] = ifh['ELEGIBLE_SIS']
df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
df['EDAD_C'] = df['EDAD'] - 65

print("=" * 44)
print("QUE MIDE CADA CRITERIO DE SUBMUESTRA?")
print("=" * 44)

print("\n1. ELEGIBLE_IFH=1 (criterio que usamos)")
print("   Definicion: IFH <= umbral departamental")
print("   Incluye: pobres Y pobres extremos segun SISFOH")
e_ifh = df[df['ELEGIBLE_IFH'] == 1]
print(f"   N total: {len(e_ifh):,}")
if 'POBREZA' in df.columns:
    print("   Composicion por pobreza monetaria INEI:")
    dist = e_ifh['POBREZA'].value_counts().sort_index()
    labels = {1:'Extrema pobreza', 2:'Pobre no extremo', 3:'No pobre'}
    for k, v in dist.items():
        print(f"     POBREZA={k} ({labels[k]}): "
              f"{v:,} ({100*v/len(e_ifh):.1f}%)")

print("\n2. ELEGIBLE_SIS=1 (criterio mas estricto)")
print("   Definicion: IFH + agua + electricidad")
print("   Mas cercano a pobre extremo real")
e_sis = df[df['ELEGIBLE_SIS'] == 1]
print(f"   N total: {len(e_sis):,}")
if 'POBREZA' in df.columns:
    print("   Composicion por pobreza monetaria INEI:")
    dist2 = e_sis['POBREZA'].value_counts().sort_index()
    for k, v in dist2.items():
        print(f"     POBREZA={k} ({labels[k]}): "
              f"{v:,} ({100*v/len(e_sis):.1f}%)")

print("\n3. POBREZA=1 (pobreza extrema monetaria INEI)")
print("   Definicion: gasto pc < linea de pobreza extrema")
if 'POBREZA' in df.columns:
    e_pob = df[df['POBREZA'] == 1]
    print(f"   N total: {len(e_pob):,}")

print("\n4. CRUCE: cuantos pobres extremos captura cada criterio?")
if 'POBREZA' in df.columns:
    tot_ext = (df['POBREZA'] == 1).sum()
    cap_ifh = ((df['ELEGIBLE_IFH']==1) & (df['POBREZA']==1)).sum()
    cap_sis = ((df['ELEGIBLE_SIS']==1) & (df['POBREZA']==1)).sum()
    print(f"   Total pobres extremos en muestra: {tot_ext:,}")
    print(f"   Capturados por ELEGIBLE_IFH: "
          f"{cap_ifh:,} ({100*cap_ifh/tot_ext:.1f}%)")
    print(f"   Capturados por ELEGIBLE_SIS: "
          f"{cap_sis:,} ({100*cap_sis/tot_ext:.1f}%)")

print("\n5. EN LA VENTANA +-5 ANOS -- lo que importa para el RDD")
for nombre, mascara in [
    ("ELEGIBLE_IFH=1", df['ELEGIBLE_IFH'] == 1),
    ("ELEGIBLE_SIS=1", df['ELEGIBLE_SIS'] == 1),
    ("POBREZA=1",      df['POBREZA'] == 1),
]:
    v = df[
        mascara &
        (df['EDAD_C'] >= -5) &
        (df['EDAD_C'] <= 5)
    ]
    izq = v[v['EDAD_C'] < 0]
    der = v[v['EDAD_C'] >= 0]
    p65_izq = izq['RECIBE_P65_PERSONA'].mean()
    p65_der = der['RECIBE_P65_PERSONA'].mean()
    print(f"\n   {nombre}:")
    print(f"     N en ventana: {len(v):,} "
          f"(izq={len(izq):,} / der={len(der):,})")
    print(f"     % P65 <65: {100*p65_izq:.1f}% | "
          f">=65: {100*p65_der:.1f}% | "
          f"Salto: {100*(p65_der-p65_izq):.1f} pp")
    if 'TIENE_BILLETERA' in v.columns:
        b_izq = izq['TIENE_BILLETERA'].mean()
        b_der = der['TIENE_BILLETERA'].mean()
        print(f"     % billetera <65: {100*b_izq:.1f}% | "
              f">=65: {100*b_der:.1f}%")
    if 'POBREZA' in v.columns:
        ext = (v['POBREZA']==1).sum()
        print(f"     Pobres extremos (POBREZA=1): "
              f"{ext:,} ({100*ext/len(v):.1f}%)")
