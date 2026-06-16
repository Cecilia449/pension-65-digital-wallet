"""
Auditoría independiente de variables para construcción del IFH.
"""
import pandas as pd

VARIABLES_NECESARIAS = {
    "combustible":    ["COMBUSTIBLE", "P113A", "P113"],
    "agua":           ["ABASTAGUADOM", "P110", "P106"],
    "paredes":        ["PARED", "P102"],
    "techo":          ["P102", "TECHO"],
    "piso":           ["PISO", "P103"],
    "desague":        ["SERVSANIT", "P111A", "P111", "P108"],
    "electricidad":   ["ALUMBRADO", "P112A", "P112"],
    "cuartos":        ["P104", "CUARTOS"],
    "miembros":       ["MIEPERHO"],
    "telefono_fijo":  ["P2011", "P209", "TELEFONO"],
    "refrigerador":   ["REFRIGERADOR", "P2061"],
    "tv":             ["TIENE_TV", "P2062"],
    "smartphone":     ["SMARTPHONE", "P2069"],
    "seguro_no_sis":  ["P4191", "SEGURO"],
    "educ_nivel":     ["NIVEL_EDUCATIVO", "P301A"],
    "area":           ["AREA", "DOMINIO", "ESTRATO"],
    "departamento":   ["DPTO", "UBIGEO"],
    "gasto_agua":     ["GASTA_AGUA", "GRU51"],
    "gasto_electr":   ["GASTA_ELECTR", "GRU52"],
}

df = pd.read_csv(
    "data/clean/enaho_2024_clean.csv",
    encoding="latin-1",
    low_memory=False
)
print(f"Dataset: {df.shape[0]:,} filas x {df.shape[1]} columnas\n")

reporte = []
for concepto, candidatas in VARIABLES_NECESARIAS.items():
    encontrada = None
    for col in candidatas:
        if col in df.columns:
            encontrada = col
            break

    if encontrada:
        serie = df[encontrada]
        reporte.append({
            "concepto":         concepto,
            "columna":          encontrada,
            "dtype":            str(serie.dtype),
            "pct_nulos":        f"{100*serie.isna().mean():.1f}%",
            "n_valores_unicos": serie.nunique(),
            "valores_unicos":   str(sorted(serie.dropna().unique()[:10].tolist())),
            "estado":           "OK"
        })
    else:
        reporte.append({
            "concepto":         concepto,
            "columna":          "NO ENCONTRADA",
            "dtype":            "-",
            "pct_nulos":        "-",
            "n_valores_unicos": "-",
            "valores_unicos":   "-",
            "estado":           "FALTANTE"
        })

df_rep = pd.DataFrame(reporte)
print(df_rep.to_string(index=False))
df_rep.to_csv("auditoria_variables_ifh.csv", index=False)
print("\nGuardado: auditoria_variables_ifh.csv")
