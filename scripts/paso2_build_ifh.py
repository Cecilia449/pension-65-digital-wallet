"""
PASO 2 — Construir variables crudas del IFH (SISFOH) con ENAHO 2024.

Lee los modulos crudos de ENAHO 2024, mapea cada variable de la receta
Bernal-Carpio-Klein (2017) a su codigo ENAHO y construye un CSV a nivel
HOGAR con las categorias canonicas que usaran los pesos de
scripts/ifh_weights.py (Paso 1).

Output:
    data/clean/ifh_raw_variables.csv  (1 fila por hogar)

Variables construidas (categorias canonicas que matchean los pesos):
    combustible_cocina, agua, paredes, desague, miembros_con_seguro,
    bienes_riqueza, telefono_fijo, techo, educacion_jefe, piso,
    hacinamiento, educacion_max_hogar, electricidad, piso_tierra

Mapeo critico ENAHO 2024 -> BCK 2017 (ver dictionary lookup en script):
    P102 paredes  -> ladrillo/piedra_concreto/adobe/barro/quincha_barro/...
    P103 piso     -> parquet/vinilico/losetas/madera/cemento/tierra/otro
    P103A techo   -> concreto/madera_estera/tejas/...
    P110 agua     -> dentro/fuera/tuberia/cisterna/pozo/rio/otro
    P111A desague -> dentro_vivienda/fuera_vivienda/pozo_septico/...
    P113A combust -> electricidad/gas/carbon/lena/otro/no_cocina
    P1121 electr  -> si/no
    P1141 tel fijo-> si/no
    P301A educ    -> ninguno/preescolar/primaria/secundaria/tecnico/
                     universitario/postgrado
    P419x seguro  -> contar miembros con seguro EXCLUYENDO SIS (P4195)
    P612N bienes  -> contar tenencia de TV color, equipo sonido,
                     refrigeradora, lavadora, computadora/laptop
    P104/MIEPERHO -> hacinamiento = miembros / cuartos

NOTA: NO calcula el IFH numerico. Eso es el Paso 4. Aqui solo dejamos
las CATEGORIAS canonicas. El Paso 3 asigna cluster geografico y el
Paso 4 aplica los pesos.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

RAW_DIR = Path(r"C:\Users\Alexander\AppData\Local\Temp\enaho2024_check")
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYS_H = ["CONGLOME", "VIVIENDA", "HOGAR"]
KEYS_P = KEYS_H + ["CODPERSO"]


# ============================================================================
# Mapas ENAHO 2024 -> categorias canonicas BCK 2017
# ============================================================================

# P102 - material paredes (codigos 1-9 ENAHO -> nombre BCK)
PAREDES_MAP = {
    1: "ladrillo",          # Ladrillo o bloque de cemento
    2: "piedra_concreto",   # Piedra o sillar con cal/cemento
    3: "adobe",             # Adobe
    4: "barro",             # Tapia (BCK lo agrupa con "clay")
    5: "quincha_barro",     # Quincha (cana con barro)
    6: "piedra_con_barro",  # Piedra con barro
    7: "madera_estera",     # Madera (pona, tornillo, etc)
    8: "madera_estera",     # Triplay/calamina/estera (mismo grupo BCK)
    9: "otro",              # Otro material
}

# P103 - material piso (codigos 1-7)
PISO_MAP = {
    1: "parquet",   # Parquet o madera pulida
    2: "vinilico",  # Laminas asfalticas, vinilicos
    3: "losetas",   # Losetas, terrazos
    4: "madera",    # Madera (pona, tornillo)
    5: "cemento",   # Cemento
    6: "tierra",    # Tierra
    7: "otro",      # Otro material
}

# P103A - material techo (codigos 1-8)
TECHO_MAP = {
    1: "concreto",       # Concreto armado
    2: "madera_estera",  # Madera (no hay equivalente exacto BCK; agrupa)
    3: "tejas",          # Tejas
    4: "tejas",          # Calamina (material industrial duro; mapeo a tejas)
    5: "carrizo",        # Cana o estera con torta de barro/cemento
    6: "estera",         # Triplay/estera/carrizo (sin barro)
    7: "paja",           # Paja, hojas de palmera
    8: "otro",           # Otro material
}

# P110 - agua (codigos 1-8)
AGUA_MAP = {
    1: "dentro",     # Red publica dentro de la vivienda
    2: "fuera",      # Red publica fuera de la vivienda (dentro edificio)
    3: "tuberia",    # Pilon o pileta publica
    4: "cisterna",   # Camion-cisterna u otro similar
    5: "pozo",       # Pozo (agua subterranea)
    6: "rio",        # Manantial o puquio (agua superficial natural)
    7: "otro",       # Otra
    8: "rio",        # Rio, acequia, lago, laguna
}

# P111A - desague (codigos 1-7, 9)
DESAGUE_MAP = {
    1: "dentro_vivienda",   # Red publica desague dentro de vivienda
    2: "fuera_vivienda",    # Red publica desague fuera (dentro edificio)
    3: "pozo_septico",      # Letrina con tratamiento (similar)
    4: "pozo_septico",      # Pozo septico, tanque septico, biodigestor
    5: "pozo_ciego",        # Pozo ciego o negro
    6: "rio",               # Rio, acequia, canal
    7: "ninguno",           # Otra
    9: "ninguno",           # Campo abierto o al aire libre
}

# P113A - combustible mayor frecuencia (codigos 1-8)
COMBUSTIBLE_MAP = {
    1: "electricidad",   # Electricidad
    2: "gas",            # Gas (Balon GLP)
    3: "gas",            # Gas Natural (sistema de tuberias)
    5: "carbon",         # Carbon
    6: "lena",           # Lena
    7: "otro",           # Otro (residuos agricolas, bosta, etc.)
    8: "no_cocina",      # No cocinan
}

# P301A - nivel educativo (12 valores ENAHO -> 7 categorias BCK)
EDUCACION_MAP = {
    1:  "ninguno",         # Sin nivel
    2:  "preescolar",      # Inicial
    3:  "primaria",        # Primaria incompleta
    4:  "primaria",        # Primaria completa
    5:  "secundaria",      # Secundaria incompleta
    6:  "secundaria",      # Secundaria completa
    7:  "tecnico",         # Superior no universitaria incompleta
    8:  "tecnico",         # Superior no universitaria completa
    9:  "universitario",   # Superior universitaria incompleta
    10: "universitario",   # Superior universitaria completa
    11: "postgrado",       # Maestria
    12: "postgrado",       # Doctorado
}

# Categorias rurales tienen menos niveles
EDUCACION_RURAL_MAP = {
    1:  "ninguno",
    2:  "primaria",
    3:  "primaria",
    4:  "primaria",
    5:  "secundaria",
    6:  "secundaria",
    7:  "tecnico",
    8:  "tecnico",
    9:  "universitario",
    10: "universitario",
    11: "universitario",
    12: "universitario",
}

# Bienes que contamos (codigos P612N para SISFOH canonico)
# 2=TV color, 4=Equipo sonido, 7=Computadora/laptop, 12=Refrigeradora,
# 13=Lavadora. NOTA: el paper BCK no lista los items exactos; este set es
# el estandar SISFOH-2010 segun la literatura peruana de focalizacion.
BIENES_CANONICOS = [2, 4, 7, 12, 13]


# ============================================================================
# Helpers
# ============================================================================
def _to_num(s):
    return pd.to_numeric(s, errors="coerce")


def _cat_from_map(s, m, fallback="otro"):
    n = _to_num(s)
    return n.map(m).fillna(fallback)


def _bucket_count(n: int) -> str:
    """Bucket entero positivo -> categoria BCK."""
    if pd.isna(n):
        return "ninguno"
    n = int(n)
    if n <= 0:
        return "ninguno"
    if n == 1:
        return "uno"
    if n == 2:
        return "dos"
    if n == 3:
        return "tres"
    if n == 4:
        return "cuatro"
    return "cinco"


def _hacinamiento_bucket(r: float) -> str:
    if pd.isna(r):
        return "entre_2_y_4"
    if r < 1:
        return "menos_de_1"
    if r < 2:
        return "entre_1_y_2"
    if r < 4:
        return "entre_2_y_4"
    if r <= 6:
        return "entre_4_y_6"
    return "mas_de_seis"


# ============================================================================
# Loaders por modulo
# ============================================================================
def load_m01() -> pd.DataFrame:
    """Modulo 01 - Vivienda: paredes, piso, techo, agua, desague,
    combustible, electricidad, telefono fijo, hacinamiento (P104).

    Filtra hogares fantasma (RESULT in {3,4,5,6,7} = rechazo/ausente/
    vivienda desocupada/no inicio/otro). Solo conserva hogares con
    entrevista valida (RESULT in {1,2}).
    """
    f = RAW_DIR / "966-Modulo01" / "Enaho01-2024-100.csv"
    cols = KEYS_H + ["UBIGEO", "DOMINIO", "ESTRATO", "RESULT",
                     "P102", "P103", "P103A", "P104",
                     "P110", "P111A",
                     "P113A", "P1121", "P1141"]
    df = pd.read_csv(f, encoding="latin-1", low_memory=False, usecols=cols)

    n_raw = len(df)
    # Filtrar hogares con entrevista valida (RESULT 1 = Completa, 2 = Incompleta)
    df = df[_to_num(df["RESULT"]).isin([1, 2])].copy()
    # Filtrar tambien por P102 no-blank (sanidad por si RESULT marca incompleta
    # pero no llego a recoger las variables IFH).
    df = df[df["P102"].astype(str).str.strip() != ""].copy()
    print(f"  m01: {n_raw:,} hogares raw -> {len(df):,} validos (RESULT in {{1,2}} y P102 valido)")

    out = df[KEYS_H + ["UBIGEO", "DOMINIO", "ESTRATO"]].copy()
    out["DOMINIO"]  = _to_num(df["DOMINIO"])
    out["ESTRATO"]  = _to_num(df["ESTRATO"])

    out["paredes"] = _cat_from_map(df["P102"],  PAREDES_MAP)
    out["piso"]    = _cat_from_map(df["P103"],  PISO_MAP)
    out["techo"]   = _cat_from_map(df["P103A"], TECHO_MAP)
    out["agua"]    = _cat_from_map(df["P110"],  AGUA_MAP)
    out["desague"] = _cat_from_map(df["P111A"], DESAGUE_MAP)
    out["combustible_cocina"] = _cat_from_map(df["P113A"], COMBUSTIBLE_MAP)
    out["electricidad"] = np.where(_to_num(df["P1121"]) == 1, "si", "no")
    out["telefono_fijo"] = np.where(_to_num(df["P1141"]) == 1, "si", "no")

    # Hacinamiento: necesitamos miembros / cuartos. Cuartos = P104.
    # Miembros viene de Sumaria (MIEPERHO). Lo terminamos despues del merge.
    out["_cuartos"] = _to_num(df["P104"]).replace({99: np.nan, 0: np.nan})

    # Piso tierra (variable propia rural): 1 si P103 == 6 (tierra), 0 si no.
    out["piso_tierra"] = np.where(_to_num(df["P103"]) == 6, "si", "no")

    return out


def load_m02_jefe_pob() -> pd.DataFrame:
    """Modulo 02 - Miembros: identifica jefe de hogar (P203==1) y devuelve
    pareja (jefe-> CODPERSO) por hogar. Tambien devuelve un DF persona-level
    para cruzar con educacion/seguro."""
    f = RAW_DIR / "966-Modulo02" / "Enaho01-2024-200.csv"
    df = pd.read_csv(f, encoding="latin-1", low_memory=False,
                     usecols=KEYS_P + ["P203", "P204", "P208A"])
    df["P203_NUM"] = _to_num(df["P203"])
    df["P204_NUM"] = _to_num(df["P204"])
    df["EDAD"]     = _to_num(df["P208A"])
    # Solo miembros del hogar (P204==1) y no domesticos (P203 not in 8,9)
    df = df[(df["P204_NUM"] == 1) & (~df["P203_NUM"].isin([8, 9]))].copy()
    print(f"  m02: {len(df):,} personas validas")
    return df


def load_m03_education(personas: pd.DataFrame) -> pd.DataFrame:
    """Modulo 03 - Educacion: nivel educativo de cada persona (P301A).
    Devuelve dos cosas:
      - educacion_jefe       (categoria BCK del jefe de hogar)
      - educacion_max_hogar  (categoria BCK del nivel maximo en el hogar)
    """
    f = RAW_DIR / "966-Modulo03" / "Enaho01A-2024-300.csv"
    df = pd.read_csv(f, encoding="latin-1", low_memory=False,
                     usecols=KEYS_P + ["P301A"])
    df["P301A_NUM"] = _to_num(df["P301A"]).replace({99: np.nan})
    pers = personas[KEYS_P + ["P203_NUM"]].merge(df, on=KEYS_P, how="left")

    # Educacion del jefe
    jefe = pers[pers["P203_NUM"] == 1][KEYS_H + ["P301A_NUM"]].copy()
    jefe = jefe.drop_duplicates(subset=KEYS_H, keep="first")
    jefe["educacion_jefe"] = jefe["P301A_NUM"].map(EDUCACION_MAP).fillna("ninguno")

    # Educacion maxima del hogar (rural variant)
    max_hogar = (
        pers.groupby(KEYS_H)["P301A_NUM"].max().rename("max_educ").reset_index()
    )
    max_hogar["educacion_max_hogar"] = (
        max_hogar["max_educ"].map(EDUCACION_RURAL_MAP).fillna("ninguno")
    )

    out = jefe[KEYS_H + ["educacion_jefe"]].merge(
        max_hogar[KEYS_H + ["educacion_max_hogar"]], on=KEYS_H, how="outer"
    )
    print(f"  m03: educacion para {len(out):,} hogares")
    return out


def load_m04_seguro(personas: pd.DataFrame) -> pd.DataFrame:
    """Modulo 04 - Salud: cuenta miembros con seguro EXCLUYENDO SIS
    (P4195). Sigue la regla SISFOH: P4191 (ESSALUD) + P4192 (privado) +
    P4193 (FFAA/Policia) + P4194 (EPS) + P4196 + P4197 + P4198.
    """
    f = RAW_DIR / "966-Modulo04" / "Enaho01A-2024-400.csv"
    cols = KEYS_P + ["P4191", "P4192", "P4193", "P4194",
                     "P4196", "P4197", "P4198"]   # NOTA: P4195 (SIS) excluido
    df = pd.read_csv(f, encoding="latin-1", low_memory=False, usecols=cols)
    # Tiene cualquier seguro no-SIS?
    seguro = pd.DataFrame({
        c: (_to_num(df[c]) == 1).astype(int) for c in cols if c.startswith("P41")
    })
    df["tiene_seguro_no_sis"] = (seguro.sum(axis=1) > 0).astype(int)

    # Filtrar solo personas validas via merge
    df = personas[KEYS_P].merge(df[KEYS_P + ["tiene_seguro_no_sis"]],
                                on=KEYS_P, how="left")
    df["tiene_seguro_no_sis"] = df["tiene_seguro_no_sis"].fillna(0).astype(int)

    n_seguro = df.groupby(KEYS_H)["tiene_seguro_no_sis"].sum().reset_index()
    n_seguro["miembros_con_seguro"] = n_seguro["tiene_seguro_no_sis"].apply(_bucket_count)
    print(f"  m04: seguro para {len(n_seguro):,} hogares "
          f"(media miembros no-SIS = {n_seguro['tiene_seguro_no_sis'].mean():.2f})")
    return n_seguro[KEYS_H + ["miembros_con_seguro"]]


def load_m18_bienes() -> pd.DataFrame:
    """Modulo 18 - Equipamiento: cuenta cuantos de los 5 bienes canonicos
    tiene el hogar (TV color, equipo sonido, computadora, refrigeradora,
    lavadora).
    """
    f = RAW_DIR / "966-Modulo18" / "Enaho01-2024-612.csv"
    df = pd.read_csv(f, encoding="latin-1", low_memory=False,
                     usecols=KEYS_H + ["P612N", "P612"])
    df["P612N_NUM"] = _to_num(df["P612N"])
    df["TIENE"]     = (_to_num(df["P612"]) == 1).astype(int)

    sub = df[df["P612N_NUM"].isin(BIENES_CANONICOS)].copy()
    cnt = sub.groupby(KEYS_H)["TIENE"].sum().reset_index()
    cnt["bienes_riqueza"] = cnt["TIENE"].apply(_bucket_count)
    print(f"  m18: bienes para {len(cnt):,} hogares "
          f"(media canasta 5 bienes = {cnt['TIENE'].mean():.2f})")
    return cnt[KEYS_H + ["bienes_riqueza"]]


def load_sumaria() -> pd.DataFrame:
    """Sumaria: MIEPERHO, POBREZA, INGTPU03, FACTOR07 — para validacion
    y para el calculo de hacinamiento (necesita MIEPERHO)."""
    f = RAW_DIR / "966-Modulo34" / "Sumaria-2024.csv"
    df = pd.read_csv(f, encoding="latin-1", low_memory=False,
                     usecols=KEYS_H + ["MIEPERHO", "POBREZA", "POBREZAV",
                                       "INGTPU03", "INGTPU01",
                                       "INGHOG2D", "FACTOR07"])
    df["MIEPERHO"]  = _to_num(df["MIEPERHO"])
    df["POBREZA"]   = _to_num(df["POBREZA"])
    df["POBREZAV"]  = _to_num(df["POBREZAV"])
    df["FACTOR07"]  = _to_num(df["FACTOR07"])
    df["RECIBE_P65_HOGAR"]    = (_to_num(df["INGTPU03"]) > 0).astype(int)
    df["RECIBE_JUNTOS_HOGAR"] = (_to_num(df["INGTPU01"]) > 0).astype(int)
    df["INGRESO_PC"] = _to_num(df["INGHOG2D"]) / df["MIEPERHO"].replace(0, np.nan)
    print(f"  sumaria: {len(df):,} hogares")
    return df


# ============================================================================
# Main
# ============================================================================
def main() -> None:
    print("=" * 78)
    print("PASO 2 — Extraer variables crudas del IFH (SISFOH) — ENAHO 2024")
    print("=" * 78)

    print("\n[load] Modulos crudos...")
    m01 = load_m01()
    personas = load_m02_jefe_pob()
    educ = load_m03_education(personas)
    seguro = load_m04_seguro(personas)
    bienes = load_m18_bienes()
    sumaria = load_sumaria()

    print("\n[merge] Combinando todo a nivel hogar...")
    df = m01.copy()
    df = df.merge(educ,    on=KEYS_H, how="left")
    df = df.merge(seguro,  on=KEYS_H, how="left")
    df = df.merge(bienes,  on=KEYS_H, how="left")
    df = df.merge(sumaria[KEYS_H + ["MIEPERHO", "POBREZA", "POBREZAV",
                                    "FACTOR07", "INGRESO_PC",
                                    "RECIBE_P65_HOGAR", "RECIBE_JUNTOS_HOGAR"]],
                  on=KEYS_H, how="left")

    # Hacinamiento = MIEPERHO / cuartos
    df["_ratio"] = df["MIEPERHO"] / df["_cuartos"]
    df["hacinamiento"] = df["_ratio"].apply(_hacinamiento_bucket)
    df = df.drop(columns=["_ratio", "_cuartos"])

    # Llenar NaN en categoricas con fallback
    cat_cols = ["paredes", "piso", "techo", "agua", "desague",
                "combustible_cocina", "electricidad", "telefono_fijo",
                "piso_tierra", "educacion_jefe", "educacion_max_hogar",
                "miembros_con_seguro", "bienes_riqueza", "hacinamiento"]
    for c in cat_cols:
        df[c] = df[c].fillna("otro" if c not in
                              ("electricidad", "telefono_fijo", "piso_tierra")
                              else "no")

    # Guardar
    out_csv = OUT_DIR / "ifh_raw_variables.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n[save] {out_csv}")
    print(f"  Shape: {df.shape}")
    print(f"  Hogares: {df[KEYS_H].drop_duplicates().shape[0]:,}")

    # Diagnostico: ver distribucion de cada categoria
    print("\n[diagnostico] Distribucion de variables IFH:")
    for c in cat_cols:
        d = df[c].value_counts(normalize=True).round(3) * 100
        print(f"\n  {c}:")
        for k, v in d.head(10).items():
            print(f"    {k:25s} {v:>5.1f}%")


if __name__ == "__main__":
    main()
