import pandas as pd
import numpy as np

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

izq = sub[sub['EDAD_C'] < 0]
der = sub[sub['EDAD_C'] >= 0]

print("=" * 42)
print("AUDITORIA INDEPENDIENTE -- VERIFICACION")
print("=" * 42)

print(f"\n1. TAMANO DE MUESTRA")
print(f"   Submuestra total:      {len(sub):,}")
print(f"   Lado izquierdo (<65):  {len(izq):,}")
print(f"   Lado derecho (>=65):   {len(der):,}")
print(f"   Suma izq+der:          {len(izq)+len(der):,}")
print(f"   Coincide con total?    "
      f"{'SI' if len(izq)+len(der)==len(sub) else 'ERROR'}")

print(f"\n2. VARIABLES -- EXISTEN Y SON BINARIAS (0/1)")
for var in ['TIENE_BILLETERA', 'USA_BILLETERA',
            'BANCO_PREVIO', 'BANCO_PRIVADO',
            'BANCO_NACION', 'RECIBE_P65_PERSONA']:
    if var in sub.columns:
        vals = sub[var].dropna().unique()
        es_binaria = set(vals).issubset({0, 1})
        nulos = sub[var].isna().sum()
        print(f"   {var}:")
        print(f"     Existe: SI | "
              f"Valores unicos: {sorted(vals)} | "
              f"Binaria: {'SI' if es_binaria else 'NO'} | "
              f"Nulos: {nulos}")
    else:
        print(f"   {var}: NO EXISTE -- ERROR")

print(f"\n3. FIRST STAGE -- VERIFICACION MANUAL")
print(f"   (% que recibe P65 antes y despues de 65)")
fs_izq = izq['RECIBE_P65_PERSONA'].mean()
fs_der = der['RECIBE_P65_PERSONA'].mean()
print(f"   Antes de 65: {100*fs_izq:.2f}%")
print(f"   Despues de 65: {100*fs_der:.2f}%")
print(f"   Salto bruto: {100*(fs_der-fs_izq):.2f} pp")
print(f"   Nadie <65 recibe P65? "
      f"{'SI' if fs_izq == 0 else 'NO -- REVISAR'}")

print(f"\n4. OUTCOMES -- VERIFICACION MANUAL DE SALTOS BRUTOS")
print(f"   (% con valor=1 antes y despues de 65)")
print(f"   {'Variable':<22} {'Antes':>8} {'Despues':>8} {'Salto':>9}")
print(f"   {'-'*52}")
for var in ['TIENE_BILLETERA', 'USA_BILLETERA',
            'BANCO_PREVIO', 'BANCO_PRIVADO',
            'BANCO_NACION']:
    if var in sub.columns:
        v_izq = izq[var].mean()
        v_der = der[var].mean()
        salto = v_der - v_izq
        print(f"   {var:<22} "
              f"{100*v_izq:>7.1f}% "
              f"{100*v_der:>7.1f}% "
              f"{100*salto:>+8.1f} pp")

print(f"\n5. BANCO_PRIVADO -- VERIFICACION DE CONSTRUCCION")
print(f"   Viene de P558E1_1?")
if 'P558E1_1' in df.columns:
    print(f"   P558E1_1 existe en el dataset: SI")
    test = (df['P558E1_1'].astype(str).str.strip() == '1').astype(int)
    coincide = (test == df['BANCO_PRIVADO']).all()
    print(f"   BANCO_PRIVADO == (P558E1_1==\"1\")? "
          f"{'SI' if coincide else 'NO -- ERROR'}")
else:
    print(f"   P558E1_1 NO esta en el dataset limpio.")
    print(f"   BANCO_PRIVADO fue construida durante")
    print(f"   el re-procesamiento del pipeline.")
    print(f"   Verificacion alternativa:")
    bp_total = df['BANCO_PRIVADO'].sum()
    bp_sub   = sub['BANCO_PRIVADO'].sum()
    print(f"   Total con BANCO_PRIVADO=1: {bp_total:,}")
    print(f"   En submuestra:             {bp_sub:,}")

print(f"\n6. CONSISTENCIA BANCO_PREVIO vs DESAGREGACION")
print(f"   BANCO_PREVIO debe ser <= BANCO_PRIVADO + BANCO_NACION")
sub['CHECK'] = ((sub['BANCO_PRIVADO'].fillna(0).astype(int)) |
                (sub['BANCO_NACION'].fillna(0).astype(int)))
inconsistentes = (
    (sub['BANCO_PREVIO'] == 1) & (sub['CHECK'] == 0)
).sum()
print(f"   Hogares con BANCO_PREVIO=1 pero")
print(f"   BANCO_PRIVADO=0 y BANCO_NACION=0: {inconsistentes:,}")
if inconsistentes > 0:
    print(f"   ADVERTENCIA: hay inconsistencia")
else:
    print(f"   Consistencia: OK")

print(f"\n7. RESUMEN FINAL")
print(f"   Todo cuadra para usar en la tesis?")
errores = []
for var in ['TIENE_BILLETERA', 'USA_BILLETERA',
            'BANCO_PREVIO', 'BANCO_PRIVADO',
            'BANCO_NACION', 'RECIBE_P65_PERSONA']:
    if var not in sub.columns:
        errores.append(f"{var} no existe")
if inconsistentes > 0:
    errores.append("inconsistencia en desagregacion banco")
if fs_izq != 0:
    errores.append("personas <65 reciben P65")

if len(errores) == 0:
    print(f"   SI. No se encontraron errores criticos.")
else:
    print(f"   NO. Errores encontrados:")
    for e in errores:
        print(f"     - {e}")
