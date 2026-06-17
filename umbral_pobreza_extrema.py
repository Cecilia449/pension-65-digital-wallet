import pandas as pd
import numpy as np

df = pd.read_csv("data/clean/enaho_2024_clean.csv",
                 encoding="utf-8", low_memory=False)
ifh = pd.read_csv("data/clean/ifh_2024.csv",
                  encoding="utf-8", low_memory=False)

df['IFH']          = ifh['IFH']
df['ELEGIBLE_IFH'] = ifh['ELEGIBLE_IFH']

print("=== DISTRIBUCION DEL IFH POR GRUPO DE POBREZA ===")
print("(Para identificar si hay un segundo umbral natural)")
print()

if 'POBREZA' in df.columns:
    for grupo, label in [(1,'Extrema pobreza'),
                          (2,'Pobre no extremo'),
                          (3,'No pobre')]:
        sub = df[df['POBREZA'] == grupo]['IFH'].dropna()
        print(f"POBREZA={grupo} ({label}):")
        print(f"  N: {len(sub):,}")
        print(f"  IFH promedio: {sub.mean():.2f}")
        print(f"  IFH mediana:  {sub.median():.2f}")
        print(f"  IFH p25:      {sub.quantile(0.25):.2f}")
        print(f"  IFH p75:      {sub.quantile(0.75):.2f}")
        print(f"  IFH minimo:   {sub.min():.2f}")
        print(f"  IFH maximo:   {sub.max():.2f}")
        print()

print("=== A QUE GRUPO DE POBREZA PERTENECEN ===")
print("=== LOS QUE ESTAN DEBAJO DEL UMBRAL IFH? ===")
print()
elegibles = df[df['ELEGIBLE_IFH'] == 1]
if 'POBREZA' in df.columns:
    dist = elegibles['POBREZA'].value_counts().sort_index()
    labels = {1:'Extrema pobreza', 2:'Pobre no extremo', 3:'No pobre'}
    for k, v in dist.items():
        print(f"  POBREZA={k} ({labels[k]}): "
              f"{v:,} ({100*v/len(elegibles):.1f}%)")

print()
print("=== UMBRAL NATURAL DE POBREZA EXTREMA ===")
print("Que IFH maximo tiene el 95% de los pobres extremos?")
if 'POBREZA' in df.columns:
    ext = df[df['POBREZA']==1]['IFH'].dropna()
    for p in [75, 90, 95, 99]:
        print(f"  Percentil {p} de IFH entre pobres extremos: "
              f"{ext.quantile(p/100):.2f}")
