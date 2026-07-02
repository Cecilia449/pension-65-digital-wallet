"""
script.py — Pipeline completo end-to-end del paper sobre adopción de billetera
digital (Pensión 65 RDD). Reúne los 5 scripts originales en un solo archivo
PORTABLE que cualquiera que clone el repositorio pueda ejecutar.

PIPELINE (5 fases):
    Fase 0  — Descarga los 6 módulos ENAHO 2024 directamente desde INEI
              (https://proyectos.inei.gob.pe/microdatos — Encuesta 966)
    Fase 1  — preprocess: mergea los 6 módulos ENAHO 2024 → enaho_2024_clean.csv
    Fase 2  — clean: filtra muestra RDD, centra running variable → clean_data.csv
    Fase 3  — main: estima el RDD principal (rdrobust + fallback WLS) → main_results.csv
    Fase 4  — robustness: McCrary, placebos, BW, donut, balance, polinomios, etc.
    Fase 5  — output: tablas LaTeX y figuras del paper

USO:
    python scripts/script_completo/script.py

REQUISITOS:
    - Python 3.9+
    - pandas, numpy, matplotlib, statsmodels (se intentan instalar si faltan)
    - rdrobust, rddensity, linearmodels (opcionales, hay fallback)
    - Conexión a internet para descargar de INEI (~38 MB de zips → ~511 MB de CSVs)

OUTPUTS (todos relativos al repo):
    data/clean/enaho_2024_clean.csv
    data/clean/clean_data.csv
    data/clean/main_results.csv
    data/clean/robustness_results.csv
    paper/figures/figure_mccrary_density.{png,pdf}
    paper/figures/figure_1_rdplot.{png,pdf}
    paper/figures/figure_2_bandwidth_sensitivity.{png,pdf}
    paper/tables/table_1_summary.tex
    paper/tables/table_2_main_results.tex
    paper/tables/table_3_robustness.tex
    paper/tables/table_4_covariate_balance.tex
"""

from __future__ import annotations

import io
import json
import sys
import subprocess
import urllib.request
import urllib.error
import warnings
import zipfile
from pathlib import Path

warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════════════════
# RUTAS PORTABLES (todas derivadas de la ubicación de este script)
# ════════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent                           # scripts/script_completo/
REPO_ROOT = SCRIPT_DIR.parent.parent                       # raíz del repo

DATA_DIR = REPO_ROOT / "data" / "clean"
RAW_EXTRACTED_DIR = DATA_DIR / "_raw_extracted"
PAPER_DIR = REPO_ROOT / "paper"
TABLES_DIR = PAPER_DIR / "tables"
FIGURES_DIR = PAPER_DIR / "figures"

# Archivos intermedios y finales
ENAHO_CLEAN_CSV = DATA_DIR / "enaho_2024_clean.csv"
CLEAN_DATA_CSV  = DATA_DIR / "clean_data.csv"
MAIN_RESULTS_CSV = DATA_DIR / "main_results.csv"
ROBUSTNESS_CSV  = DATA_DIR / "robustness_results.csv"

# Diccionario central de rutas (incluye archivos de CAMBIOS 2 y 4)
PATHS = {
    "enaho_clean":      ENAHO_CLEAN_CSV,
    "clean_data_full":  DATA_DIR / "enaho_rdd_full.csv",
    "clean_data_main":  DATA_DIR / "enaho_rdd_main.csv",  # legacy: se mantiene para fases 3-5
    "main_dataset":     DATA_DIR / "main_dataset.csv",    # NUEVO 2026-05-21: muestra completa + SAMPLE_FLAG
    "main_results":     MAIN_RESULTS_CSV,
    "robustness":       ROBUSTNESS_CSV,
    "dilution_calc":    DATA_DIR / "dilution_calc.json",
    "rdd2_mayores":     DATA_DIR / "enaho_rdd2_mayores.csv",
    "rdd2_results":     DATA_DIR / "rdd2_results.csv",
}

# Asegurar que los directorios existan
for d in (DATA_DIR, TABLES_DIR, FIGURES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Reproducibilidad
RANDOM_SEED = 42

# ════════════════════════════════════════════════════════════════════════════
# INEI: Descarga de microdata ENAHO 2024
# ════════════════════════════════════════════════════════════════════════════
# Patrón verificado de URL:
#   https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV/{cod_encuesta}-Modulo{XX}.zip
# Encuesta 966 = ENAHO Metodología ACTUALIZADA — Condiciones de Vida y Pobreza,
# año 2024, período Anual (Ene-Dic).
INEI_BASE_URL = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV"
INEI_SURVEY_CODE = "966"
INEI_USER_AGENT = "Mozilla/5.0"

# (módulo_INEI, archivo_CSV_objetivo, alias_interno)
# El alias se usa luego para indexar los DataFrames en phase_1_preprocess.
INEI_MODULES = [
    ("01", "Enaho01-2024-100.csv",  "m01"),  # Vivienda
    ("02", "Enaho01-2024-200.csv",  "m02"),  # Miembros del hogar
    ("03", "Enaho01A-2024-300.csv", "m03"),  # Educación
    ("05", "Enaho01a-2024-500.csv", "m05"),  # Empleo + Billetera
    ("18", "Enaho01-2024-612.csv",  "m18"),  # Equipamiento del hogar
    ("34", "Sumaria-2024.csv",      "sum"),  # Sumaria
]

# Después de la descarga, los CSVs viven directamente en RAW_EXTRACTED_DIR
# (sin la subcarpeta raw_data_X/ que tenían los zips legacy).
EXPECTED_CSVS = {alias: csv_name for _, csv_name, alias in INEI_MODULES}


# ════════════════════════════════════════════════════════════════════════════
# INSTALADOR DE DEPENDENCIAS
# ════════════════════════════════════════════════════════════════════════════
def ensure_package(pkg: str, import_name: str | None = None) -> bool:
    """Instala pkg vía pip si no está disponible. Retorna True si quedó importable."""
    name = import_name or pkg
    try:
        __import__(name)
        return True
    except ImportError:
        print(f"  [deps] Installing {pkg}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            __import__(name)
            return True
        except Exception as e:
            print(f"  [deps] FAILED to install {pkg}: {e}")
            return False


def install_dependencies():
    print("\n[deps] Verificando dependencias...")
    # Núcleo (obligatorias)
    for pkg in ["pandas", "numpy", "matplotlib", "statsmodels"]:
        ok = ensure_package(pkg)
        if not ok:
            print(f"[deps] FATAL: '{pkg}' es obligatorio. Abortando.")
            sys.exit(1)
    # Opcionales (hay fallback)
    ensure_package("rdrobust")
    ensure_package("rddensity")
    ensure_package("linearmodels")
    ensure_package("scikit-learn", "sklearn")
    print("[deps] Dependencias OK.\n")


# Llamamos antes de importar pandas/numpy
install_dependencies()

import numpy as np                                              # noqa: E402
import pandas as pd                                             # noqa: E402

np.random.seed(RANDOM_SEED)

# Imports opcionales con flags
try:
    from rdrobust import rdrobust
    RDROBUST_OK = True
except ImportError:
    RDROBUST_OK = False
    print("[warn] rdrobust no disponible — usando fallback statsmodels.")

try:
    import linearmodels  # noqa: F401
except ImportError:
    pass


# ════════════════════════════════════════════════════════════════════════════
# FASE 0 — Descargar microdata ENAHO 2024 desde INEI
# ════════════════════════════════════════════════════════════════════════════
def phase_0_download_from_inei():
    """Descarga los 6 módulos ENAHO 2024 directamente desde INEI.

    Cada módulo viene como un .zip que contiene 1 o más CSVs (más algunos
    diccionarios auxiliares CIIU/CIUO/CNO). Extraemos solamente el CSV que
    necesita el pipeline y lo dejamos en RAW_EXTRACTED_DIR.

    SIEMPRE descarga (no usa cache). Esto es lo que pidió el profe:
    descarga automática y fresca cada corrida, sin depender de zips locales.
    """
    print("=" * 70)
    print("FASE 0 — Descargar microdata ENAHO 2024 desde INEI")
    print("=" * 70)
    print(f"  Encuesta {INEI_SURVEY_CODE} — Condiciones de Vida y Pobreza, Anual 2024")
    print(f"  Origen: {INEI_BASE_URL}/")
    print(f"  Destino: {RAW_EXTRACTED_DIR}\n")

    RAW_EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": INEI_USER_AGENT}

    total_bytes = 0
    for code, csv_name, alias in INEI_MODULES:
        url = f"{INEI_BASE_URL}/{INEI_SURVEY_CODE}-Modulo{code}.zip"
        print(f"  [{alias}] Modulo{code} -> {csv_name}")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                zip_bytes = resp.read()
        except urllib.error.HTTPError as e:
            print(f"      ERROR HTTP {e.code}: {e.reason}")
            print(f"      URL: {url}")
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"      ERROR de red: {e.reason}")
            print(f"      Verificá tu conexión a internet o si INEI está caído.")
            sys.exit(1)

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                matches = [n for n in zf.namelist() if n.endswith(csv_name)]
                if not matches:
                    print(f"      ERROR: {csv_name} no está en el zip de INEI.")
                    print(f"      Contenido del zip: {zf.namelist()}")
                    sys.exit(1)
                with zf.open(matches[0]) as src:
                    target = RAW_EXTRACTED_DIR / csv_name
                    target.write_bytes(src.read())
        except zipfile.BadZipFile:
            print(f"      ERROR: el archivo descargado no es un ZIP válido.")
            print(f"      Posiblemente INEI cambió el patrón de URL o devolvió HTML de error.")
            sys.exit(1)

        size_mb = target.stat().st_size / 1024 / 1024
        total_bytes += target.stat().st_size
        print(f"      OK ({size_mb:.2f} MB)")

    print(f"\n  6 CSVs descargados — {total_bytes / 1024 / 1024:.2f} MB total\n")


# ════════════════════════════════════════════════════════════════════════════
# FASE 1 — Preprocess ENAHO 2024 (preprocess_enaho_2024.py)
# ════════════════════════════════════════════════════════════════════════════
BILLETERA_E1_CODE = 9
BILLETERA_H_CODE = 7
KEYS_PERSON = ["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"]
KEYS_HOUSEHOLD = ["CONGLOME", "VIVIENDA", "HOGAR"]


def _load_csv(label: str, path: Path) -> pd.DataFrame:
    print(f"  [load] {label}: {path.name}")
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    print(f"         shape: {df.shape}")
    return df


def _detect_billetera_tenencia(m05: pd.DataFrame) -> pd.Series:
    col = f"P558E1_{BILLETERA_E1_CODE}"
    if col not in m05.columns:
        print(f"  [warn] {col} not found — tiene_billetera will be all 0")
        return pd.Series(0, index=m05.index)
    return (m05[col].astype(str).str.strip() == str(BILLETERA_E1_CODE)).astype(int)


def _detect_billetera_uso(m05: pd.DataFrame) -> pd.Series:
    use = pd.Series(0, index=m05.index)
    for g in range(1, 13):
        col = f"P558H{g}_{BILLETERA_H_CODE}"
        if col in m05.columns:
            sel = (m05[col].astype(str).str.strip() == str(BILLETERA_H_CODE)).astype(int)
            use = use | sel
    return use


def phase_1_preprocess():
    print("=" * 70)
    print("FASE 1 — Preprocess ENAHO 2024 (merge a nivel persona)")
    print("=" * 70)

    files = {k: RAW_EXTRACTED_DIR / rel for k, rel in EXPECTED_CSVS.items()}

    print("\n[1] Loading modules...")
    m01 = _load_csv("m01-Vivienda", files["m01"])
    m02 = _load_csv("m02-Miembros", files["m02"])
    m03 = _load_csv("m03-Educacion", files["m03"])
    m05 = _load_csv("m05-Empleo+Billetera", files["m05"])
    m18 = _load_csv("m18-Equipamiento", files["m18"])
    sumaria = _load_csv("sumaria", files["sum"])

    # ── Variables billetera ───────────────────────────────────────────────
    print("\n[2] Building billetera variables from m05...")
    # CAMBIO 1: TIENE_BILLETERA = tenencia OR uso. Alinea con cifra BCRP/INEI
    # 2024 (~46% adultos). La variable anterior solo capturaba P558E1 y
    # subcapturaba usuarios que solo reportan billetera en P558H.
    _tenencia = _detect_billetera_tenencia(m05)
    _uso      = _detect_billetera_uso(m05)
    m05["TIENE_BILLETERA"] = ((_tenencia == 1) | (_uso == 1)).astype(int)
    m05["USA_BILLETERA"]   = _uso
    print(f"  Media tenencia (P558E1): {_tenencia.mean():.3f}")
    print(f"  Media uso (P558H):       {_uso.mean():.3f}")
    print(f"  Media combinada:         {m05['TIENE_BILLETERA'].mean():.3f}")

    # Recepción individual de Pensión 65 (P5567A == 1)
    # Tratamiento endógeno del fuzzy RDD. i=7 en P556iA identifica Pensión 65.
    if "P5567A" in m05.columns:
        m05["RECIBE_P65_PERSONA"] = (
            pd.to_numeric(m05["P5567A"], errors="coerce") == 1
        ).astype(int)
        print(f"  RECIBE_P65_PERSONA: {m05['RECIBE_P65_PERSONA'].sum():,} receptores")
    else:
        print("  ADVERTENCIA: P5567A no encontrada en módulo 5.")
        m05["RECIBE_P65_PERSONA"] = 0

    m05["TIENE_BILLETERA_ALT_E10"] = (
        m05["P558E1_10"].astype(str).str.strip() == "10"
    ).astype(int) if "P558E1_10" in m05.columns else 0
    m05["TIENE_BILLETERA_ALT_E6"] = (
        m05["P558E1_6"].astype(str).str.strip() == "6"
    ).astype(int) if "P558E1_6" in m05.columns else 0

    use_h6 = pd.Series(0, index=m05.index)
    for g in range(1, 13):
        col = f"P558H{g}_6"
        if col in m05.columns:
            use_h6 = use_h6 | (m05[col].astype(str).str.strip() == "6").astype(int)
    m05["USA_BILLETERA_ALT_H6"] = use_h6

    print(f"  tiene_billetera (combinada):               {m05['TIENE_BILLETERA'].mean()*100:.1f}%")
    print(f"  usa_billetera (any H_{BILLETERA_H_CODE}): {m05['USA_BILLETERA'].mean()*100:.1f}%")

    # ── Banco previo / formal / ocupado ───────────────────────────────────
    m05["BANCO_PREVIO"] = (
        ((m05["P558E1_1"].astype(str).str.strip() == "1").astype(int)) |
        ((m05["P558E1_8"].astype(str).str.strip() == "8").astype(int))
        if "P558E1_1" in m05.columns and "P558E1_8" in m05.columns
        else pd.Series(0, index=m05.index)
    ).astype(int)

    m05["BANCO_PRIVADO"] = (
        ((m05["P558E1_1"].astype(str).str.strip() == "1").astype(int))
        if "P558E1_1" in m05.columns
        else pd.Series(0, index=m05.index)
    ).astype(int)

    m05["BANCO_NACION"] = (
        ((m05["P558E1_8"].astype(str).str.strip() == "8").astype(int))
        if "P558E1_8" in m05.columns
        else pd.Series(0, index=m05.index)
    ).astype(int)

    if "P514" in m05.columns:
        m05["FORMAL"] = (pd.to_numeric(m05["P514"], errors="coerce") == 1).astype(int)
    else:
        m05["FORMAL"] = 0

    if "OCU500" in m05.columns:
        m05["OCUPADO"] = (pd.to_numeric(m05["OCU500"], errors="coerce") == 1).astype(int)
    else:
        m05["OCUPADO"] = 0

    m05_keep = [c for c in (KEYS_PERSON + [
        "TIENE_BILLETERA", "USA_BILLETERA",
        "TIENE_BILLETERA_ALT_E10", "TIENE_BILLETERA_ALT_E6", "USA_BILLETERA_ALT_H6",
        "BANCO_PREVIO", "BANCO_PRIVADO", "BANCO_NACION", "FORMAL", "OCUPADO",
        "RECIBE_P65_PERSONA",  # tratamiento endógeno fuzzy RDD (P5567A)
    ]) if c in m05.columns]
    m05_p = m05[m05_keep].drop_duplicates(subset=KEYS_PERSON, keep="first")
    print(f"  m05 person-level: {m05_p.shape}")

    # ── m02 demografía ────────────────────────────────────────────────────
    print("\n[3] Extracting m02 demographics + FACPOB07...")
    m02_keep = [c for c in (KEYS_PERSON + ["P207", "P208A", "FACPOB07"]) if c in m02.columns]
    m02_p = m02[m02_keep].copy().rename(columns={
        "P207": "GENERO", "P208A": "EDAD", "FACPOB07": "FACTOR_EXPANSION",
    })

    # ── m03 educación ─────────────────────────────────────────────────────
    print("\n[4] Extracting m03 education...")
    m03_keep = [c for c in (KEYS_PERSON + ["P301A"]) if c in m03.columns]
    m03_p = m03[m03_keep].copy().rename(columns={"P301A": "NIVEL_EDUCATIVO"})

    # ── m18 equipamiento (long → wide): smartphone, refrigerador, TV ─────
    print("\n[5] Extracting m18 smartphone/refrigerador/TV (long-format pivot)...")
    # Items: (P612N code, output column name)
    M18_ITEMS = [(10, "SMARTPHONE"), (4, "REFRIGERADOR"), (2, "TIENE_TV")]
    m18_h = None
    for item_code, col_name in M18_ITEMS:
        rows = m18[m18["P612N"] == item_code].copy()
        rows[col_name] = (pd.to_numeric(rows["P612"], errors="coerce") == 1).astype(int)
        item_h = rows[KEYS_HOUSEHOLD + [col_name]].drop_duplicates(
            subset=KEYS_HOUSEHOLD, keep="first"
        )
        print(f"  {col_name.lower()}: {item_h[col_name].mean()*100:.1f}% of households")
        if m18_h is None:
            m18_h = item_h
        else:
            m18_h = m18_h.merge(item_h, on=KEYS_HOUSEHOLD, how="outer")

    # ── m01 internet ──────────────────────────────────────────────────────
    print("\n[6] Extracting m01 housing/internet...")
    if "P114B2" in m01.columns:
        m01["INTERNET_HOGAR"] = (m01["P114B2"].astype(str).str.strip() == "1").astype(int)
    else:
        m01["INTERNET_HOGAR"] = 0
    print(f"  internet_hogar: {m01['INTERNET_HOGAR'].mean()*100:.1f}% of households")

    # Variables de vivienda para BLOQUE F PCA (aliases verificados en ENAHO 2024):
    # P111A=saneamiento, P112A=alumbrado, P113A=combustible (renombradas abajo)
    HOUSING_PCA_VARS = [
        "P102", "P103", "P104", "P110",
        "P111A", "P112A", "P113A",
        "PARED", "PISO", "ABASTAGUADOM", "SERVSANIT", "ALUMBRADO", "COMBUSTIBLE",
    ]
    m01_keep = [c for c in (
        KEYS_HOUSEHOLD + ["UBIGEO", "ESTRATO", "DOMINIO", "INTERNET_HOGAR"]
        + [v for v in HOUSING_PCA_VARS if v in m01.columns]
    ) if c in m01.columns]
    m01_keep = list(dict.fromkeys(m01_keep))  # deduplica preservando orden
    # CAMBIO 3 (Bloque C): AREA necesaria para heterogeneidad urbano/rural
    if "AREA" in m01.columns:
        m01_keep.append("AREA")
    m01_h = m01[m01_keep].drop_duplicates(subset=KEYS_HOUSEHOLD, keep="first")
    # Renombrar aliases 2024 a nombres canónicos del PCA
    m01_h = m01_h.rename(columns={
        "P111A": "SERVSANIT",
        "P112A": "ALUMBRADO",
        "P113A": "COMBUSTIBLE",
    })
    for col, src in [("SERVSANIT", "P111A"), ("ALUMBRADO", "P112A"), ("COMBUSTIBLE", "P113A")]:
        if col in m01_h.columns:
            print(f"  {col} ({src}): {m01_h[col].notna().sum():,} hogares con dato")
        else:
            print(f"  ADVERTENCIA: {src} no encontrada en módulo 01.")
    # Derivar AREA de DOMINIO si no existe directamente
    # DOMINIO: 1-4=urbano (Costa/Sierra/Selva urbana + Lima), 5-7=rural
    if "AREA" not in m01_h.columns and "DOMINIO" in m01_h.columns:
        dom = pd.to_numeric(m01_h["DOMINIO"], errors="coerce")
        m01_h["AREA"] = np.where(dom.isin([1, 2, 3, 4]), 1,
                        np.where(dom.isin([5, 6, 7]), 2, np.nan))
        n_urb = (m01_h["AREA"] == 1).sum()
        n_rur = (m01_h["AREA"] == 2).sum()
        print(f"  AREA derivada de DOMINIO: urbano={n_urb:,}, rural={n_rur:,}")
    elif "AREA" not in m01_h.columns:
        print("  ADVERTENCIA: columna AREA no encontrada en módulo 01.")

    # ── Sumaria ingreso pc + transferencias ──────────────────────────────
    print("\n[7] Extracting sumaria income + P65/Juntos transfers...")
    sum_keep = [c for c in (KEYS_HOUSEHOLD +
                            ["INGHOG2D", "GASHOG2D", "MIEPERHO",
                             "POBREZA", "POBREZAV",
                             "INGTPU01", "INGTPU03", "FACTOR07"])
                if c in sumaria.columns]
    sum_h = sumaria[sum_keep].drop_duplicates(subset=KEYS_HOUSEHOLD, keep="first")
    sum_h["INGRESO_PC"] = (
        pd.to_numeric(sum_h["INGHOG2D"], errors="coerce") /
        pd.to_numeric(sum_h["MIEPERHO"], errors="coerce").replace(0, np.nan)
    )
    # Recepción de transferencias a nivel hogar (tratamiento endógeno fuzzy RDD)
    sum_h["RECIBE_P65_HOGAR"] = (
        pd.to_numeric(sum_h["INGTPU03"], errors="coerce") > 0
    ).astype(int)
    sum_h["RECIBE_JUNTOS_HOGAR"] = (
        pd.to_numeric(sum_h["INGTPU01"], errors="coerce") > 0
    ).astype(int)
    print(f"  RECIBE_P65_HOGAR:    {sum_h['RECIBE_P65_HOGAR'].sum():,} hogares receptores")
    print(f"  RECIBE_JUNTOS_HOGAR: {sum_h['RECIBE_JUNTOS_HOGAR'].sum():,} hogares receptores")

    # ── Merge total ───────────────────────────────────────────────────────
    print("\n[8] Merging all modules at person level...")
    df = m02_p.copy()
    df = df.merge(m03_p, on=KEYS_PERSON, how="left")
    df = df.merge(m05_p, on=KEYS_PERSON, how="left")
    df = df.merge(m01_h, on=KEYS_HOUSEHOLD, how="left")
    df = df.merge(m18_h, on=KEYS_HOUSEHOLD, how="left")
    df = df.merge(sum_h, on=KEYS_HOUSEHOLD, how="left")

    if "UBIGEO" in df.columns:
        df["DPTO"] = df["UBIGEO"].astype(str).str.zfill(6).str[:2]

    # HACINAMIENTO = miembros / cuartos (para BLOQUE F PCA)
    # P104 = número de cuartos del hogar (módulo 01)
    rooms_col = next((c for c in ("P104", "CUARTOS") if c in df.columns), None)
    if rooms_col and "MIEPERHO" in df.columns:
        cuartos = pd.to_numeric(df[rooms_col], errors="coerce").replace(0, np.nan)
        mieperho = pd.to_numeric(df["MIEPERHO"], errors="coerce")
        df["HACINAMIENTO"] = mieperho / cuartos
        print(f"  HACINAMIENTO construida: media={df['HACINAMIENTO'].mean():.2f}")
    else:
        print("  HACINAMIENTO: P104 o MIEPERHO no disponible, se omite del PCA.")

    for col in ["TIENE_BILLETERA", "USA_BILLETERA", "BANCO_PREVIO", "FORMAL"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    print(f"  Final shape: {df.shape}")
    print(f"\n[9] Saving to {ENAHO_CLEAN_CSV}...")
    df.to_csv(ENAHO_CLEAN_CSV, index=False, encoding="utf-8")
    size_mb = ENAHO_CLEAN_CSV.stat().st_size / 1024 / 1024
    print(f"  Saved ({size_mb:.1f} MB)\n")


# ════════════════════════════════════════════════════════════════════════════
# FASE 2 — Cleaning RDD (00_clean.py)
# ════════════════════════════════════════════════════════════════════════════
RUNNING_VAR_RAW = "EDAD"
THRESHOLD = 65
TREATMENT_VAR = ""
OUTCOME_VARS = ["TIENE_BILLETERA", "USA_BILLETERA"]
CLUSTER_VAR = "DPTO"
TIME_VAR = None
COVARIATES = ["INTERNET_HOGAR", "SMARTPHONE", "INGRESO_PC", "NIVEL_EDUCATIVO"]
PLACEBO_OUTCOMES = ["INTERNET_HOGAR", "SMARTPHONE"]


def phase_2_clean():
    print("=" * 70)
    print("FASE 2 — RDD Data Cleaning")
    print("=" * 70)

    print(f"Loading: {ENAHO_CLEAN_CSV}")
    df = pd.read_csv(ENAHO_CLEAN_CSV, encoding="latin-1", low_memory=False)
    print(f"Raw data: {len(df):,} rows x {df.shape[1]} cols")

    # Missingness
    print("\n--- Missingness table (key variables) ---")
    key_vars = [RUNNING_VAR_RAW, TREATMENT_VAR, CLUSTER_VAR] + OUTCOME_VARS + COVARIATES
    if TIME_VAR:
        key_vars.append(TIME_VAR)
    key_vars = [v for v in key_vars if v and v in df.columns]
    for var in key_vars:
        n_miss = df[var].isna().sum()
        pct = 100 * n_miss / len(df)
        print(f"  {var:30s}: {n_miss:6,} missing ({pct:.1f}%)")

    if RUNNING_VAR_RAW not in df.columns:
        print(f"\nERROR: Running variable '{RUNNING_VAR_RAW}' not in data.")
        sys.exit(1)

    # Coerce running variable a numérico (strings vacíos / espacios → NaN)
    # Sin esto, la resta `df[EDAD] - THRESHOLD` truena si la columna es object.
    df[RUNNING_VAR_RAW] = pd.to_numeric(df[RUNNING_VAR_RAW], errors="coerce")

    # Filtrar
    n_before = len(df)
    df_rdd = df.dropna(subset=[RUNNING_VAR_RAW]).copy()
    print(f"\n--- Filter: running variable non-missing ---")
    print(f"  Before: {n_before:,}  After: {len(df_rdd):,}")

    # Centrar
    if isinstance(THRESHOLD, (int, float)) and THRESHOLD != 0:
        df_rdd["running_centered"] = df_rdd[RUNNING_VAR_RAW] - THRESHOLD
        print(f"  Centered at threshold = {THRESHOLD}")
    else:
        df_rdd["running_centered"] = df_rdd[RUNNING_VAR_RAW]

    # Tratamiento
    if TREATMENT_VAR and TREATMENT_VAR in df_rdd.columns:
        df_rdd["treat"] = df_rdd[TREATMENT_VAR].astype(float)
    else:
        df_rdd["treat"] = (df_rdd["running_centered"] >= 0).astype(float)
    print(f"  Treated: {int(df_rdd['treat'].sum()):,}  "
          f"Control: {len(df_rdd) - int(df_rdd['treat'].sum()):,}")

    # Validación outcomes
    print("\n--- Outcome validation ---")
    outcomes_present = [o for o in OUTCOME_VARS if o in df_rdd.columns]
    if not outcomes_present:
        print("  ERROR: No outcome variables found!")
        sys.exit(1)
    for var in outcomes_present:
        s = df_rdd[var].dropna()
        corr = df_rdd[[var, "running_centered"]].dropna().corr().iloc[0, 1]
        ctrl_mean = df_rdd.loc[df_rdd["treat"] == 0, var].mean()
        treat_mean = df_rdd.loc[df_rdd["treat"] == 1, var].mean()
        print(f"  {var}: N={len(s)}, ctrl={ctrl_mean:.4f}, "
              f"treat={treat_mean:.4f}, corr={corr:.4f}")

    # Top correlates
    print("\n--- Top 10 variables correlated with running variable ---")
    numeric_cols = df_rdd.select_dtypes(include=[np.number]).columns
    corrs = {}
    for col in numeric_cols:
        if col in ("running_centered", "treat", RUNNING_VAR_RAW):
            continue
        try:
            r = df_rdd[["running_centered", col]].dropna().corr().iloc[0, 1]
            if not np.isnan(r):
                corrs[col] = abs(r)
        except Exception:
            pass
    for i, (col, r) in enumerate(sorted(corrs.items(), key=lambda x: -x[1])[:10], 1):
        print(f"  {i:2d}. {col:40s} |r| = {r:.4f}")

    # Save legacy (backward compat con fases que leen CLEAN_DATA_CSV)
    df_rdd.to_csv(CLEAN_DATA_CSV, index=False)
    print(f"\nSaved: {CLEAN_DATA_CSV} ({len(df_rdd):,} rows x {df_rdd.shape[1]} cols)")

    # ── Construcción del dataset analítico corregido (2026-05-21) ─────────
    # DISEÑO CORREGIDO: NO restringimos por POBREZA como muestra primaria.
    # POBREZA es clasificación monetaria de ENAHO (gasto pc vs línea de pobreza),
    # NO la categoría SISFOH que usa Pensión 65. Restringir por POBREZA=1
    # excluye al ~88.7% de los receptores reales (verificable con INGTPU03>0).
    # El estimand primario es un fuzzy RDD sobre la muestra completa usando
    # RECIBE_P65_PERSONA (P5567A) como tratamiento endógeno y 1(EDAD>=65) como
    # instrumento. POBREZA y POBREZAV entran como heterogeneidad descriptiva.
    main_dataset = df_rdd.copy()

    # SAMPLE_FLAG: permite recuperar particiones para heterogeneidad descriptiva.
    # ADVERTENCIA: estas particiones son ex-post post-tratamiento, NO son
    # restricciones de elegibilidad. No usarlas como diseño primario del RDD.
    main_dataset["SAMPLE_FLAG_A_FULL"] = 1
    main_dataset["SAMPLE_FLAG_B_POBREZA_EXT"] = (
        pd.to_numeric(main_dataset["POBREZA"], errors="coerce") == 1
    ).astype(int) if "POBREZA" in main_dataset.columns else 0
    main_dataset["SAMPLE_FLAG_C_POBREZA_POOR"] = (
        pd.to_numeric(main_dataset["POBREZA"], errors="coerce").isin([1, 2])
    ).astype(int) if "POBREZA" in main_dataset.columns else 0

    # SAMPLE_FLAG_D — elegibilidad IFH (Bernal, Carpio y Klein 2017)
    # A diferencia de POBREZA (monetaria, post-tratamiento), el IFH se basa en
    # características predeterminadas de vivienda y no es endógeno al programa.
    # ELEGIBLE_SIS = IFH <= UMBRAL AND gasto_agua <= 20 AND gasto_electr <= 25.
    _IFH_CSV   = DATA_DIR / "ifh_2024.csv"
    _CLEAN_CSV = DATA_DIR / "enaho_2024_clean.csv"
    if _IFH_CSV.exists() and _CLEAN_CSV.exists():
        _keys = pd.read_csv(
            _CLEAN_CSV,
            usecols=["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"],
            dtype=str
        )
        _ifh = pd.read_csv(
            _IFH_CSV,
            usecols=["IFH", "UMBRAL", "ELEGIBLE_IFH", "ELEGIBLE_SIS"]
        )
        _ifh_keys = pd.concat(
            [_keys.reset_index(drop=True), _ifh.reset_index(drop=True)], axis=1
        )
        for _c in ["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"]:
            main_dataset[_c] = main_dataset[_c].astype(str)
        main_dataset = main_dataset.merge(
            _ifh_keys, on=["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"], how="left"
        )
        main_dataset["SAMPLE_FLAG_D_ELEGIBLE_SIS"] = (
            main_dataset["ELEGIBLE_SIS"].fillna(0).astype(int)
        )
        print("  IFH (BCK 2017) mergeado correctamente.")
    else:
        main_dataset["SAMPLE_FLAG_D_ELEGIBLE_SIS"] = 0
        print("  ADVERTENCIA: ifh_2024.csv no encontrado — SAMPLE_FLAG_D = 0.")

    print(f"\nmain_dataset (muestra completa con SAMPLE_FLAG): N = {len(main_dataset):,}")
    print(f"  SAMPLE A (full):              {main_dataset['SAMPLE_FLAG_A_FULL'].sum():,}")
    print(f"  SAMPLE B (POBREZA=1):         {main_dataset['SAMPLE_FLAG_B_POBREZA_EXT'].sum():,}")
    print(f"  SAMPLE C (POBREZA in {{1,2}}): {main_dataset['SAMPLE_FLAG_C_POBREZA_POOR'].sum():,}")
    print(f"  SAMPLE D (ELEGIBLE_SIS=1):    {main_dataset['SAMPLE_FLAG_D_ELEGIBLE_SIS'].sum():,}")

    if "RECIBE_P65_PERSONA" in main_dataset.columns:
        recep_total = main_dataset["RECIBE_P65_PERSONA"].sum()
        if recep_total > 0:
            recep_B = ((main_dataset["RECIBE_P65_PERSONA"] == 1) &
                       (main_dataset["SAMPLE_FLAG_B_POBREZA_EXT"] == 1)).sum()
            recep_C = ((main_dataset["RECIBE_P65_PERSONA"] == 1) &
                       (main_dataset["SAMPLE_FLAG_C_POBREZA_POOR"] == 1)).sum()
            recep_D = ((main_dataset["RECIBE_P65_PERSONA"] == 1) &
                       (main_dataset["SAMPLE_FLAG_D_ELEGIBLE_SIS"] == 1)).sum()
            print(f"\n  Receptores P65 totales:          {recep_total:,}")
            print(f"    en SAMPLE B (POBREZA=1):       {recep_B:,} ({recep_B/recep_total*100:.1f}%)")
            print(f"    en SAMPLE C (POBREZA<=2):      {recep_C:,} ({recep_C/recep_total*100:.1f}%)")
            print(f"    en SAMPLE D (ELEGIBLE_SIS=1):  {recep_D:,} ({recep_D/recep_total*100:.1f}%)")

    main_dataset.to_csv(PATHS["main_dataset"], index=False)
    print(f"Saved: {PATHS['main_dataset']}")

    # Archivos legacy para fases 3-5 (sin modificar esas fases)
    df_full = main_dataset.copy()
    if "POBREZA" in main_dataset.columns:
        df_main = main_dataset[main_dataset["SAMPLE_FLAG_B_POBREZA_EXT"] == 1].copy()
    else:
        df_main = df_full.copy()

    bw_check = 14.24
    dentro = df_main[df_main["running_centered"].abs() <= bw_check]
    n_below = int((dentro["running_centered"] < 0).sum())
    n_above = int((dentro["running_centered"] >= 0).sum())
    print(f"\ndf_main (POBREZA=1, solo para heterogeneidad descriptiva): N = {len(df_main):,}")
    print(f"  Dentro del bandwidth (±{bw_check}):")
    print(f"  - Debajo del corte: N = {n_below:,}")
    print(f"  - Encima del corte: N = {n_above:,}")
    if n_below < 200 or n_above < 200:
        print("  ADVERTENCIA: menos de 200 obs en un lado — estimadores ruidosos.")

    df_full.to_csv(PATHS["clean_data_full"], index=False)
    df_main.to_csv(PATHS["clean_data_main"], index=False)
    print(f"Saved: {PATHS['clean_data_full']}")
    print(f"Saved: {PATHS['clean_data_main']}")

    # Placeholder de results
    if not MAIN_RESULTS_CSV.exists():
        pd.DataFrame(columns=["outcome", "specification", "estimate", "se_robust",
                              "ci_lower", "ci_upper", "bandwidth", "N_eff", "method"]
                     ).to_csv(MAIN_RESULTS_CSV, index=False)
        print(f"Saved placeholder: {MAIN_RESULTS_CSV}")
    print()


# ════════════════════════════════════════════════════════════════════════════
# FASE 3 — Main RDD (01_main.py)
# ════════════════════════════════════════════════════════════════════════════
RUNNING_VAR = "running_centered"
COVARIATES_BASIC = ["INTERNET_HOGAR", "SMARTPHONE"]
COVARIATES_EXT = ["INTERNET_HOGAR", "SMARTPHONE", "POBREZA", "INGRESO_PC", "NIVEL_EDUCATIVO"]
EXPECTED_SIGNS = {"TIENE_BILLETERA": "+", "USA_BILLETERA": "+"}
HETEROGENEITY_VARS = ["POBREZA", "INTERNET_HOGAR", "SMARTPHONE"]


def _safe_scalar(obj, idx=0):
    try:
        if hasattr(obj, "iloc"):
            return float(obj.iloc[idx])
        elif hasattr(obj, "__getitem__") and hasattr(obj, "__len__"):
            return float(obj[idx])
        return float(obj)
    except Exception:
        return np.nan


def _run_rdd_rdrobust(y, x, cluster=None, covs=None, h=None, fuzzy=None):
    kwargs = dict(y=y, x=x, kernel="triangular", bwselect="mserd")
    if cluster is not None:
        kwargs["cluster"] = cluster
    if covs is not None:
        kwargs["covs"] = covs
    if h is not None:
        kwargs["h"] = h
        del kwargs["bwselect"]
    if fuzzy is not None:
        kwargs["fuzzy"] = fuzzy

    rd = rdrobust(**kwargs)

    estimate = _safe_scalar(rd.coef, 0)
    estimate_bc = (_safe_scalar(rd.coef, 1)
                   if hasattr(rd.coef, "__len__") and len(rd.coef) > 1 else estimate)
    se_conv = _safe_scalar(rd.se, 0)
    se_robust = _safe_scalar(rd.se, -1)

    try:
        ci_lower = float(rd.ci.iloc[-1, 0]) if hasattr(rd.ci, "iloc") else np.nan
        ci_upper = float(rd.ci.iloc[-1, 1]) if hasattr(rd.ci, "iloc") else np.nan
    except Exception:
        ci_lower = estimate - 1.96 * se_conv if not np.isnan(se_conv) else np.nan
        ci_upper = estimate + 1.96 * se_conv if not np.isnan(se_conv) else np.nan

    bandwidth = (float(rd.bws.iloc[0, 0]) if hasattr(rd.bws, "iloc")
                 else _safe_scalar(rd.bws, 0))

    try:
        n_left = int(rd.N_h[0])
        n_right = int(rd.N_h[1]) if len(rd.N_h) > 1 else 0
    except Exception:
        n_left = n_right = 0

    if np.isnan(estimate) and not np.isnan(ci_lower) and not np.isnan(ci_upper):
        estimate = (ci_lower + ci_upper) / 2.0
        se_robust = (ci_upper - ci_lower) / (2 * 1.96)

    return {
        "estimate": estimate, "estimate_bc": estimate_bc,
        "se_conv": se_conv, "se_robust": se_robust,
        "ci_lower": ci_lower, "ci_upper": ci_upper,
        "bandwidth": bandwidth,
        "N_left": n_left, "N_right": n_right, "N_eff": n_left + n_right,
        "method": "rdrobust_fuzzy" if fuzzy is not None else "rdrobust",
    }


def _run_rdd_statsmodels(y, x, cluster=None, h=None):
    from statsmodels.regression.linear_model import WLS
    from statsmodels.tools.tools import add_constant
    if h is None:
        h = 1.5 * np.std(x)
    mask = np.abs(x) <= h
    y_bw, x_bw = y[mask], x[mask]
    if len(y_bw) < 10:
        return None
    treat = (x_bw >= 0).astype(float)
    weights = np.maximum(1 - np.abs(x_bw) / h, 0)
    X = add_constant(np.column_stack([treat, x_bw, treat * x_bw]))
    try:
        mod = WLS(y_bw, X, weights=weights).fit(cov_type="HC2")
        ci = mod.conf_int()[1]
        return {
            "estimate": mod.params[1], "estimate_bc": mod.params[1],
            "se_conv": mod.bse[1], "se_robust": mod.bse[1],
            "ci_lower": ci[0], "ci_upper": ci[1],
            "bandwidth": h,
            "N_left": int((x_bw < 0).sum()), "N_right": int((x_bw >= 0).sum()),
            "N_eff": len(y_bw),
            "method": "statsmodels_WLS",
        }
    except Exception:
        return None


def run_rdd(df, outcome, covariates=None, h=None, label="baseline", fuzzy_col=None):
    """RDD con fallback automático. Siempre devuelve dict completo."""
    drop_cols = [outcome, RUNNING_VAR]
    if fuzzy_col and fuzzy_col in df.columns:
        drop_cols.append(fuzzy_col)
    sub = df.dropna(subset=drop_cols).copy()
    y = sub[outcome].values
    x = sub[RUNNING_VAR].values
    cluster = sub[CLUSTER_VAR].values if CLUSTER_VAR in sub.columns else None
    fuzzy = sub[fuzzy_col].values if fuzzy_col and fuzzy_col in sub.columns else None

    cov_matrix = None
    if covariates:
        avail = [c for c in covariates if c in sub.columns]
        if avail:
            cov_sub = sub[avail].dropna()
            valid = cov_sub.index.intersection(sub.index)
            if len(valid) > 50:
                y = sub.loc[valid, outcome].values
                x = sub.loc[valid, RUNNING_VAR].values
                cluster = (sub.loc[valid, CLUSTER_VAR].values
                           if CLUSTER_VAR in sub.columns else None)
                cov_matrix = cov_sub.loc[valid].values

    result = {
        "outcome": outcome, "specification": label,
        "estimate": np.nan, "estimate_bc": np.nan,
        "se_conv": np.nan, "se_robust": np.nan,
        "ci_lower": np.nan, "ci_upper": np.nan,
        "bandwidth": np.nan, "N_eff": len(y),
        "N_left": np.nan, "N_right": np.nan,
        "method": "none",
    }

    if len(y) < 20:
        print(f"    Insufficient obs for {outcome} (N={len(y)}). Skipping.")
        return result

    if RDROBUST_OK:
        try:
            res = _run_rdd_rdrobust(y, x, cluster=cluster, covs=cov_matrix, h=h, fuzzy=fuzzy)
            result.update(res)
            return result
        except Exception as e:
            print(f"    rdrobust failed: {e}. Using statsmodels fallback.")

    fb = _run_rdd_statsmodels(y, x, cluster=cluster, h=h)
    if fb:
        result.update(fb)
    else:
        print(f"    Both estimators failed for {outcome}.")
    return result


def phase_3_main():
    print("=" * 70)
    print("FASE 3 — RDD Main Estimation")
    print("=" * 70)

    df_main = pd.read_csv(PATHS["clean_data_main"])
    df_full = pd.read_csv(PATHS["clean_data_full"])
    print(f"Loaded df_main (extrema pobreza): {len(df_main):,} rows x {df_main.shape[1]} cols")
    print(f"Loaded df_full (completa):        {len(df_full):,} rows x {df_full.shape[1]} cols")

    all_results = []
    outcomes_full = [o for o in OUTCOME_VARS if o in df_full.columns]
    outcomes_main = [o for o in OUTCOME_VARS if o in df_main.columns]
    EP_COVARIATES = ["INTERNET_HOGAR", "SMARTPHONE", "INGRESO_PC", "NIVEL_EDUCATIVO"]

    # ── BLOQUE A (PRINCIPAL): estimaciones sobre df_full ──────────────────────
    print("\n── BLOQUE A (PRINCIPAL): estimaciones principales (df_full, muestra completa) ──")
    for outcome in outcomes_full:
        print(f"\n  Outcome: {outcome}")

        res = run_rdd(df_full, outcome, label="MAIN_baseline")
        all_results.append(res)
        print(f"    [MAIN_baseline] est={res['estimate']:.4f}  SE={res['se_robust']:.4f}")
        print(f"    BW={res['bandwidth']:.3f}  N_eff={res['N_eff']}  Method={res['method']}")

        covs = [c for c in EP_COVARIATES if c in df_full.columns]
        if covs:
            res_cov = run_rdd(df_full, outcome, covariates=covs, label="MAIN_covariates")
            all_results.append(res_cov)
            print(f"    [MAIN_covariates] est={res_cov['estimate']:.4f}  SE={res_cov['se_robust']:.4f}")

        if "RECIBE_P65_PERSONA" in df_full.columns and RDROBUST_OK:
            res_fuzzy = run_rdd(df_full, outcome,
                                fuzzy_col="RECIBE_P65_PERSONA",
                                label="MAIN_fuzzy")
            all_results.append(res_fuzzy)
            print(f"    [MAIN_fuzzy] est={res_fuzzy['estimate']:.4f}  "
                  f"SE={res_fuzzy['se_robust']:.4f}  "
                  f"BW={res_fuzzy['bandwidth']:.3f}  N_eff={res_fuzzy['N_eff']}  "
                  f"Method={res_fuzzy['method']}")
        else:
            print("    [MAIN_fuzzy] rdrobust no disponible o RECIBE_P65_PERSONA ausente. Saltando.")

        if "DPTO" in df_full.columns:
            dpto_dummies = pd.get_dummies(
                df_full["DPTO"].astype(str), prefix="DPTO", drop_first=True
            )
            df_full_dpto = pd.concat(
                [df_full.reset_index(drop=True), dpto_dummies.reset_index(drop=True)], axis=1
            )
            covs_dpto = (
                [c for c in EP_COVARIATES if c in df_full_dpto.columns]
                + dpto_dummies.columns.tolist()
            )
            res_dpto = run_rdd(
                df_full_dpto, outcome, covariates=covs_dpto, label="MAIN_dpto_fe"
            )
            all_results.append(res_dpto)
            print(f"    [MAIN_dpto_fe] est={res_dpto['estimate']:.4f}  "
                  f"SE={res_dpto['se_robust']:.4f}  Method={res_dpto['method']}")

    # ── BLOQUE F_SAMPLE: RDD edad restringido a ELEGIBLE_SIS=1 (IFH BCK 2017) ──
    # Restricción de muestra correcta para el programa Pensión 65: el SISFOH usa
    # un proxy means test sobre características predeterminadas de vivienda, no
    # pobreza monetaria. ELEGIBLE_SIS=1 identifica hogares bajo el umbral IFH por
    # departamento (Tabla A.10, Bernal, Carpio y Klein 2017).
    print("\n── BLOQUE F_SAMPLE: RDD edad — muestra ELEGIBLE_SIS=1 (IFH BCK 2017) ──")
    if "SAMPLE_FLAG_D_ELEGIBLE_SIS" not in df_full.columns:
        print("  ADVERTENCIA: SAMPLE_FLAG_D_ELEGIBLE_SIS no encontrada en df_full. "
              "Re-ejecutar phase_2_clean() para regenerar enaho_rdd_full.csv.")
    else:
        df_ifh = df_full[df_full["SAMPLE_FLAG_D_ELEGIBLE_SIS"] == 1].copy()
        print(f"  Muestra ELEGIBLE_SIS=1: N = {len(df_ifh):,}")
        EP_COVARIATES_IFH = [c for c in EP_COVARIATES if c in df_ifh.columns]

        for outcome in outcomes_full:
            print(f"\n  Outcome: {outcome}")
            sub = df_ifh.dropna(subset=[RUNNING_VAR, outcome]).copy()
            if len(sub) < 100:
                print(f"    N={len(sub):,} insuficiente. Saltando.")
                continue

            dentro = sub[sub[RUNNING_VAR].abs() <= 14.24]
            n_bw_b = int((dentro[RUNNING_VAR] < 0).sum())
            n_bw_a = int((dentro[RUNNING_VAR] >= 0).sum())
            print(f"    Dentro del BW ±14.24: debajo={n_bw_b}, encima={n_bw_a}")
            if n_bw_b < 100 or n_bw_a < 100:
                print(f"    ADVERTENCIA: bajo poder estadístico (N<100 en un lado).")

            res_ifh = run_rdd(sub, outcome, label="IFH_sample_baseline")
            res_ifh["low_power"] = (n_bw_b < 100 or n_bw_a < 100)
            all_results.append(res_ifh)
            print(f"    [IFH_sample_baseline] est={res_ifh['estimate']:.4f}  "
                  f"SE={res_ifh['se_robust']:.4f}  "
                  f"BW={res_ifh['bandwidth']:.3f}  N_eff={res_ifh['N_eff']}")

            if EP_COVARIATES_IFH:
                res_ifh_cov = run_rdd(sub, outcome,
                                      covariates=EP_COVARIATES_IFH,
                                      label="IFH_sample_covariates")
                res_ifh_cov["low_power"] = (n_bw_b < 100 or n_bw_a < 100)
                all_results.append(res_ifh_cov)
                print(f"    [IFH_sample_covariates] est={res_ifh_cov['estimate']:.4f}  "
                      f"SE={res_ifh_cov['se_robust']:.4f}")

    # ── BLOQUE B: extrema pobreza como heterogeneidad ─────────────────────────
    print("\n── BLOQUE B: extrema pobreza (df_main, heterogeneidad) ──")
    bw_b = 14.24
    for outcome in outcomes_main:
        dentro = df_main[df_main[RUNNING_VAR].abs() <= bw_b]
        n_below = int((dentro[RUNNING_VAR] < 0).sum())
        n_above = int((dentro[RUNNING_VAR] >= 0).sum())
        print(f"\n  Outcome: {outcome}")
        print(f"    Dentro del BW ±{bw_b}: debajo={n_below}, encima={n_above}")
        if n_below < 200 or n_above < 200:
            print(f"    ADVERTENCIA: bajo poder estadístico (N<200 en un lado).")
        res = run_rdd(df_main, outcome, label="EP_het_baseline")
        if n_below < 200 or n_above < 200:
            res["low_power"] = True
        all_results.append(res)
        print(f"    [EP_het_baseline] est={res['estimate']:.4f}  "
              f"SE={res['se_robust']:.4f}  N_eff={res['N_eff']}")

    # ── BLOQUE C: heterogeneidad urbano/rural en df_full ──────────────────────
    print("\n── BLOQUE C: heterogeneidad urbano/rural (df_full, TIENE_BILLETERA) ──")
    if "AREA" not in df_full.columns:
        print("  ADVERTENCIA: columna AREA no disponible. Saltando Bloque C.")
    elif "TIENE_BILLETERA" not in df_full.columns:
        print("  ADVERTENCIA: TIENE_BILLETERA no disponible. Saltando Bloque C.")
    else:
        bw_c = 14.24
        area_map = {1: "urbano", 2: "rural"}
        for area_code, area_label in area_map.items():
            sub = df_full[
                pd.to_numeric(df_full["AREA"], errors="coerce") == area_code
            ].copy()
            if len(sub) < 20:
                print(f"  AREA={area_code} ({area_label}): N={len(sub)}, insuficiente. Saltando.")
                continue
            dentro = sub[sub[RUNNING_VAR].abs() <= bw_c]
            n_below = int((dentro[RUNNING_VAR] < 0).sum())
            n_above = int((dentro[RUNNING_VAR] >= 0).sum())
            print(f"\n  AREA={area_code} ({area_label}): N total={len(sub):,}")
            print(f"    Dentro del BW ±{bw_c}: debajo={n_below}, encima={n_above}")
            if n_below < 200 or n_above < 200:
                print(f"    ADVERTENCIA: bajo poder estadístico (N<200 en un lado).")
            res = run_rdd(sub, "TIENE_BILLETERA", label=f"MAIN_het_AREA_{area_label}")
            if n_below < 200 or n_above < 200:
                res["low_power"] = True
            all_results.append(res)
            print(f"    est={res['estimate']:.4f}  CI=[{res['ci_lower']:.4f}, {res['ci_upper']:.4f}]")

    # ── BLOQUE D: cálculo de dilución ITT → LATE ──────────────────────────────
    # tau_ITT = tau_LATE * P(recibe|elegible) * P(elegible|en corte). Angrist y Pischke (2009).
    print("\n── BLOQUE D: cálculo de dilución ITT → LATE ──")
    try:
        bw_dil = 14.24
        TAKEUP  = 0.75
        corte   = df_full[df_full[RUNNING_VAR].abs() <= bw_dil]
        if "POBREZA" in corte.columns and len(corte) > 0:
            frac_ep = corte[corte[RUNNING_VAR] >= 0]["POBREZA"].eq(1).mean()
        else:
            frac_ep = np.nan
            print("  POBREZA no disponible en df_full. frac_ep no calculable.")

        main_base = [r for r in all_results
                     if r.get("specification") == "MAIN_baseline"
                     and r.get("outcome") == "TIENE_BILLETERA"]
        tau_itt  = (main_base[0]["estimate"]
                    if main_base and not np.isnan(main_base[0]["estimate"]) else None)
        tau_late = (tau_itt / (frac_ep * TAKEUP)
                    if tau_itt is not None and not np.isnan(frac_ep) and frac_ep > 0
                    else None)

        if not np.isnan(frac_ep):
            print(f"Fracción EP entre >=65 en bandwidth:  {frac_ep:.1%}")
        print(f"Tasa de take-up asumida (MIDIS 2024): {TAKEUP:.0%}")
        if tau_itt is not None:
            print(f"τ_ITT (muestra completa):             {tau_itt:.4f}")
        if tau_late is not None:
            print(f"τ_LATE implícito:                     {tau_late:.4f}")
            print(f"→ El estimado ITT captura el gradiente de adopción en la población general.")
            print(f"  El LATE implica un efecto de {tau_late:.3f} pp sobre beneficiarios reales,")
            print(f"  diluido a {tau_itt:.3f} pp al observar toda la muestra.")
            print(f"  La baja penetración EP (~{frac_ep:.0%} en el bandwidth) explica la dilución.")
        else:
            print("τ_LATE: no calculable")

        dilution = {
            "frac_ep_in_bandwidth": round(float(frac_ep), 4) if not np.isnan(frac_ep) else None,
            "takeup_assumed": TAKEUP,
            "tau_itt":          round(float(tau_itt), 4) if tau_itt is not None else None,
            "tau_late_implicit": round(float(tau_late), 4) if tau_late is not None else None,
        }
        with open(PATHS["dilution_calc"], "w", encoding="utf-8") as f:
            json.dump(dilution, f, indent=2)
        print(f"Saved: {PATHS['dilution_calc']}")
    except Exception as e:
        print(f"  Cálculo de dilución falló: {e}")

    # ── BLOQUE E: df_main descriptivo (apéndice) ──────────────────────────────
    print("\n── BLOQUE E: df_main descriptivo (apéndice, extrema pobreza) ──")
    for outcome in outcomes_main:
        res = run_rdd(df_main, outcome, label="EP_descriptivo")
        all_results.append(res)
        print(f"  {outcome}: est={res['estimate']:.4f}  SE={res['se_robust']:.4f}  N_eff={res['N_eff']}")

    # Save
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(MAIN_RESULTS_CSV, index=False)
    print(f"\nSaved: {MAIN_RESULTS_CSV} ({len(results_df)} rows)")
    for col in ["estimate", "ci_lower", "ci_upper"]:
        n_nan = results_df[col].isna().sum()
        if n_nan > 0:
            print(f"  WARNING: {n_nan} NaN values in '{col}'")
    print()


# ════════════════════════════════════════════════════════════════════════════
# BLOQUE F — RDD2: proxy SISFOH como running variable.
# Replica Bando, Galiani y Gertler (2020). Resuelve el
# problema de potencia del RDD1 al usar toda la muestra
# de adultos mayores (EDAD>=65) en vez del 5% en extrema
# pobreza dentro del bandwidth de edad.
#
# VARIABLES PCA — ENAHO 2024 (aliases verificados empíricamente):
#   Vivienda (Filmer & Pritchett 2001):
#     P102  → material de paredes
#     P103  → material de piso
#     P104  → número de cuartos (denominador de hacinamiento)
#     P110  → abastecimiento de agua
#     P111A → servicio sanitario  [alias corregido: era P111]
#     P112A → tipo de alumbrado   [alias corregido: era P112]
#     P113A → combustible para cocinar [alias corregido: era P113]
#   Bienes durables (Módulo 18, formato long via P612N):
#     P612N=4  → refrigeradora
#     P612N=2  → televisor
#     P612N=10 → smartphone      [confirmado en dataset completo]
#   Variable derivada:
#     HACINAMIENTO = MIEPERHO / P104  (construida aquí, no en Fase 1)
#
# EXCLUIDAS del PCA (con justificación):
#   INGRESO_PC  → endógena: la transferencia eleva el ingreso del hogar
#   POBREZA     → clasificación monetaria post-tratamiento, no proxy SISFOH
#   LAVADORA    → varianza casi nula en adultos mayores en pobreza (8.9% general)
#   LAPTOP      → sesgo etario: discrimina jóvenes, no pobreza en adultos mayores
#   COMPUTADORA → ídem laptop
#   TABLET      → 0.1% de tenencia, sin varianza útil
#   MIEPERHO    → entra indirectamente vía HACINAMIENTO; meterla dos veces infla su peso
#   TIENE_BILLETERA → es la variable de resultado, nunca puede ser input del índice
# ════════════════════════════════════════════════════════════════════════════
def phase_3b_bloque_f():
    print("\n" + "=" * 70)
    print("BLOQUE F — RDD2: IFH Bernal-Carpio-Klein 2017 como running variable")
    print("=" * 70)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    IFH_CSV   = DATA_DIR / "ifh_2024.csv"
    CLEAN_CSV = DATA_DIR / "enaho_2024_clean.csv"

    if not IFH_CSV.exists():
        print("  ERROR: ifh_2024.csv no encontrado. Ejecutar construir_ifh.py primero.")
        return
    if not CLEAN_CSV.exists():
        print("  ERROR: enaho_2024_clean.csv no encontrado.")
        return

    # ── PASO 1: Cargar IFH (Bernal, Carpio y Klein 2017) ─────────────────
    print(f"\n── PASO 1: Cargar IFH (Bernal, Carpio y Klein 2017) ──")
    df_full = pd.read_csv(PATHS["clean_data_full"])

    # Si phase_2_clean ya incluyó las columnas IFH en enaho_rdd_full.csv,
    # no hacemos merge de nuevo (evita conflicto IFH_x / IFH_y).
    if "IFH" not in df_full.columns:
        keys_clean = pd.read_csv(
            CLEAN_CSV,
            usecols=["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"],
            dtype=str
        )
        ifh_vals = pd.read_csv(
            IFH_CSV,
            usecols=["IFH", "IFH_RAW", "UMBRAL", "ELEGIBLE_IFH", "ELEGIBLE_SIS"]
        )
        ifh_with_keys = pd.concat(
            [keys_clean.reset_index(drop=True), ifh_vals.reset_index(drop=True)],
            axis=1
        )
        for col in ["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"]:
            df_full[col] = df_full[col].astype(str)
        df_full = df_full.merge(
            ifh_with_keys,
            on=["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"],
            how="left"
        )
        print("  IFH cargado vía merge posicional.")
    else:
        print("  IFH ya presente en enaho_rdd_full.csv (cargado directamente).")

    print(f"  Observaciones en df_full:            {len(df_full):,}")
    print(f"  Con IFH no nulo:                     {df_full['IFH'].notna().sum():,}")
    print(f"  ELEGIBLE_SIS=1 (toda la muestra):    "
          f"{int(df_full['ELEGIBLE_SIS'].fillna(0).sum()):,}")

    edad_col = RUNNING_VAR_RAW
    df_full[edad_col] = pd.to_numeric(df_full[edad_col], errors="coerce")
    df_mayores = df_full[df_full[edad_col] >= 65].copy().reset_index(drop=True)
    print(f"  Adultos mayores (EDAD>=65):          {len(df_mayores):,}")
    print(f"    Con IFH no nulo:                   {df_mayores['IFH'].notna().sum():,}")
    print(f"    ELEGIBLE_SIS=1:                    "
          f"{int(df_mayores['ELEGIBLE_SIS'].fillna(0).sum()):,}")

    # ── PASO 2: Definir running variable IFH centrada en umbral ──────────
    print("\n── PASO 2: Definir running variable IFH ──")
    # running_ifh = IFH - UMBRAL  (umbral varía por departamento, Tabla A.10 BCK)
    # Tratamiento conceptual: IFH <= UMBRAL → elegible SISFOH (running_ifh <= 0)
    df_mayores["running_ifh"] = (
        pd.to_numeric(df_mayores["IFH"],    errors="coerce") -
        pd.to_numeric(df_mayores["UMBRAL"], errors="coerce")
    )
    df_mayores["treat_ifh"] = (df_mayores["running_ifh"] <= 0).astype(int)

    n_below = int((df_mayores["running_ifh"] < 0).sum())
    n_above = int((df_mayores["running_ifh"] >= 0).sum())
    print(f"  Elegibles IFH (running_ifh <= 0): {n_below:,}")
    print(f"  No elegibles  (running_ifh >  0): {n_above:,}")
    ifh_s = df_mayores["IFH"].dropna()
    umb_s = df_mayores["UMBRAL"].dropna()
    print(f"  IFH — media={ifh_s.mean():.2f}, std={ifh_s.std():.2f}")
    print(f"  UMBRAL — media={umb_s.mean():.2f}, "
          f"rango=[{umb_s.min():.0f}, {umb_s.max():.0f}]")

    # ── PASO 3: Estimar RDD2 ──────────────────────────────────────────────
    print("\n── PASO 3: Estimación RDD2 ──")
    # Covariables para RDD2: solo predeterminadas, NO endógenas al tratamiento.
    # INTERNET_HOGAR y NIVEL_EDUCATIVO son predeterminadas al ingreso al programa.
    # INGRESO_PC excluida (endógena). SMARTPHONE excluida (también es outcome relevante).
    EP_COVARIATES_F = [c for c in ["INTERNET_HOGAR", "NIVEL_EDUCATIVO"]
                       if c in df_mayores.columns]

    # Remap columnas para que run_rdd() las encuentre con sus nombres globales
    df_rdd2 = df_mayores.copy()
    df_rdd2[RUNNING_VAR] = df_rdd2["running_ifh"]
    df_rdd2["treat"]     = df_rdd2["treat_ifh"]

    rdd2_results = []
    for outcome in [o for o in OUTCOME_VARS if o in df_rdd2.columns]:
        print(f"\n  Outcome: {outcome}")

        sub = df_rdd2.dropna(subset=["running_ifh", outcome]).copy()
        if len(sub) < 100:
            print(f"    Insuficiente muestra (N={len(sub)}). Saltando.")
            continue

        # Baseline sin covariables
        res_b = run_rdd(sub, outcome, label="RDD2_IFH_baseline")
        res_b["outcome"] = outcome
        rdd2_results.append(res_b)

        bw     = res_b.get("bandwidth", np.nan)
        n_eff  = res_b.get("N_eff", 0)
        print(f"    [RDD2_IFH_baseline]    "
              f"est={res_b['estimate']:.4f}  SE={res_b['se_robust']:.4f}")
        if not np.isnan(bw):
            print(f"    BW={bw:.3f}  N_eff={n_eff}  Method={res_b['method']}")

        # Con covariables predeterminadas
        if EP_COVARIATES_F:
            res_cov = run_rdd(sub, outcome,
                              covariates=EP_COVARIATES_F,
                              label="RDD2_IFH_covariates")
            res_cov["outcome"] = outcome
            rdd2_results.append(res_cov)
            print(f"    [RDD2_IFH_covariates]  "
                  f"est={res_cov['estimate']:.4f}  SE={res_cov['se_robust']:.4f}")

        # Reporte de observaciones a cada lado del corte dentro del bandwidth
        if not np.isnan(bw):
            in_bw      = sub[sub["running_ifh"].abs() <= bw]
            n_bw_below = int((in_bw["running_ifh"] < 0).sum())
            n_bw_above = int((in_bw["running_ifh"] >= 0).sum())
            print(f"    Dentro del BW ±{bw:.2f}: "
                  f"debajo={n_bw_below}, encima={n_bw_above}")
            if n_bw_below < 100 or n_bw_above < 100:
                print(f"    ADVERTENCIA: bajo poder estadístico (N<100 en un lado).")
                res_b["low_power"] = True

            m_below = in_bw.loc[in_bw["running_ifh"] < 0, outcome].mean()
            m_above = in_bw.loc[in_bw["running_ifh"] >= 0, outcome].mean()
            print(f"    Media {outcome}: "
                  f"debajo (elegible IFH)={m_below:.4f}, encima (no elegible)={m_above:.4f}")

    # ── PASO 4: Diagnósticos ──────────────────────────────────────────────
    print("\n── PASO 4: Diagnósticos RDD2 ──")

    # 4.1 Gráfico de densidad del running variable IFH
    fig, ax = plt.subplots(figsize=(8, 5))
    valid_rs  = df_mayores["running_ifh"].dropna()
    window    = min(valid_rs.abs().quantile(0.95), 50)
    plot_vals = valid_rs[valid_rs.abs() <= window]
    ax.hist(plot_vals[plot_vals < 0],  bins=40, color="#2166ac", alpha=0.7,
            label="Elegible SISFOH (IFH ≤ umbral)")
    ax.hist(plot_vals[plot_vals >= 0], bins=40, color="#b2182b", alpha=0.7,
            label="No elegible SISFOH (IFH > umbral)")
    ax.axvline(x=0, color="black", linestyle="--", linewidth=1.5,
               label="Umbral IFH por departamento")
    ax.set_xlabel("IFH centrado en umbral departamental (BCK 2017)", fontsize=11)
    ax.set_ylabel("Frecuencia", fontsize=11)
    ax.set_title(
        "RDD2 (BCK IFH): Densidad del índice SISFOH (adultos ≥65)\n"
        "Bernal, Carpio y Klein (2017), pesos Tabla A.8/A.9 — ENAHO 2024",
        fontsize=11
    )
    ax.legend(fontsize=9)
    plt.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIGURES_DIR / f"figure_rdd2_density.{ext}",
                    dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Guardado: figure_rdd2_density.png/.pdf")

    # 4.2 RD plot: billetera digital vs índice IFH BCK
    outcome_rdplot = "TIENE_BILLETERA"
    if outcome_rdplot in df_mayores.columns:
        # Ventana ±30 puntos IFH (escala [0-100])
        plot_window = 30
        sub_plot = df_mayores.dropna(
            subset=["running_ifh", outcome_rdplot]
        ).copy()
        sub_plot = sub_plot[sub_plot["running_ifh"].between(-plot_window, plot_window)]
        bin_width = plot_window / 15
        bins      = np.arange(-plot_window, plot_window + bin_width, bin_width)
        bin_centers, bin_means, bin_side = [], [], []
        for i in range(len(bins) - 1):
            lo, hi = bins[i], bins[i + 1]
            mask   = (sub_plot["running_ifh"] >= lo) & \
                     (sub_plot["running_ifh"] <  hi)
            if mask.sum() >= 3:
                bin_centers.append((lo + hi) / 2)
                bin_means.append(sub_plot.loc[mask, outcome_rdplot].mean())
                bin_side.append("left" if (lo + hi) / 2 < 0 else "right")

        bin_centers = np.array(bin_centers)
        bin_means   = np.array(bin_means)
        bin_side    = np.array(bin_side)

        fig2, ax2 = plt.subplots(figsize=(8, 5))
        left_m  = bin_side == "left"
        right_m = bin_side == "right"
        ax2.scatter(bin_centers[left_m],  bin_means[left_m],
                    color="#2166ac", s=55, zorder=3, label="Elegible SISFOH")
        ax2.scatter(bin_centers[right_m], bin_means[right_m],
                    color="#b2182b", s=55, zorder=3, label="No elegible SISFOH")

        for mask_side, color in [(left_m, "#2166ac"), (right_m, "#b2182b")]:
            xs = sub_plot.loc[
                sub_plot["running_ifh"] < 0
                if mask_side is left_m
                else sub_plot["running_ifh"] >= 0,
                "running_ifh"
            ].values
            ys = sub_plot.loc[
                sub_plot["running_ifh"] < 0
                if mask_side is left_m
                else sub_plot["running_ifh"] >= 0,
                outcome_rdplot
            ].values
            if len(xs) > 5:
                coeffs  = np.polyfit(xs, ys, 1)
                xrange  = np.linspace(xs.min(), xs.max(), 200)
                ax2.plot(xrange, np.poly1d(coeffs)(xrange),
                         color=color, linewidth=2)

        ax2.axvline(x=0, color="black", linestyle="--",
                    linewidth=1.3, alpha=0.8, label="Umbral IFH por departamento")
        ax2.set_xlim(-plot_window, plot_window)
        ax2.set_xlabel(
            "IFH centrado en umbral departamental (BCK 2017, escala 0–100)", fontsize=11
        )
        ax2.set_ylabel("Proporción con billetera digital", fontsize=11)
        ax2.set_title(
            "RDD2: Adopción de billetera digital vs. índice SISFOH BCK\n"
            "(Adultos ≥65, siguiendo Bando, Galiani y Gertler 2020)",
            fontsize=11
        )
        ax2.legend(fontsize=9)
        plt.tight_layout()
        for ext in ("png", "pdf"):
            fig2.savefig(FIGURES_DIR / f"figure_rdd2_rdplot.{ext}",
                         dpi=150, bbox_inches="tight")
        plt.close(fig2)
        print("  Guardado: figure_rdd2_rdplot.png/.pdf")

    # 4.3 Balance de covariables en el umbral IFH
    print("\n  Balance de covariables en umbral IFH:")
    balance_covs = [c for c in ["INTERNET_HOGAR", "NIVEL_EDUCATIVO", "INGRESO_PC"]
                    if c in df_rdd2.columns]
    balance_results = []
    for cov in balance_covs:
        sub_cov = df_rdd2.dropna(subset=["running_ifh", cov]).copy()
        if len(sub_cov) < 50:
            continue
        res_bal = run_rdd(sub_cov, cov, label=f"RDD2_IFH_balance_{cov}")
        res_bal["outcome"] = cov
        balance_results.append(res_bal)
        sig = "*" if abs(res_bal["estimate"]) > 1.96 * res_bal["se_robust"] else ""
        print(f"    {cov:<20}: est={res_bal['estimate']:.4f}  "
              f"SE={res_bal['se_robust']:.4f}  {sig}")
    if not balance_results:
        print("    (no hay covariables disponibles para balance)")

    # 4.4 Guardar datasets y resultados
    df_mayores.to_csv(PATHS["rdd2_mayores"], index=False)
    print(f"\n  Guardado: {PATHS['rdd2_mayores']}")

    all_rdd2 = rdd2_results + balance_results
    if all_rdd2:
        pd.DataFrame(all_rdd2).to_csv(PATHS["rdd2_results"], index=False)
        print(f"  Guardado: {PATHS['rdd2_results']} ({len(all_rdd2)} filas)")
    else:
        print("  ADVERTENCIA: no hay resultados RDD2 para guardar.")

    # 4.5 Resumen del índice IFH BCK
    print("\n── RESUMEN ÍNDICE IFH (Bernal, Carpio y Klein 2017) ──")
    ifh_col = df_mayores["IFH"]
    print(f"  N adultos mayores con IFH: {ifh_col.notna().sum():,}")
    print(f"  Media:   {ifh_col.mean():.2f}")
    print(f"  Std:     {ifh_col.std():.2f}")
    print(f"  Min:     {ifh_col.min():.2f}")
    print(f"  Max:     {ifh_col.max():.2f}")
    umb_col = df_mayores["UMBRAL"]
    print(f"  UMBRAL — media={umb_col.mean():.2f}, "
          f"rango=[{umb_col.min():.0f}, {umb_col.max():.0f}]")
    print(f"  Elegibles IFH (IFH<=UMBRAL): "
          f"{int(df_mayores['ELEGIBLE_IFH'].fillna(0).sum()):,}")
    print(f"  ELEGIBLE_SIS (IFH+agua+electr): "
          f"{int(df_mayores['ELEGIBLE_SIS'].fillna(0).sum()):,}")


# ════════════════════════════════════════════════════════════════════════════
# FASE 4 — Robustness (02_robustness.py)
# ════════════════════════════════════════════════════════════════════════════
PRIMARY_OUTCOME = "TIENE_BILLETERA"


def phase_4_robustness():
    print("=" * 70)
    print("FASE 4 — RDD Robustness Checks")
    print("=" * 70)

    np.random.seed(RANDOM_SEED)
    df = pd.read_csv(PATHS["clean_data_full"])  # CAMBIO: muestra completa
    print(f"Loaded df_full (muestra completa): {len(df):,} rows x {df.shape[1]} cols")

    all_results = []
    y_all = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR])[RUNNING_VAR].values

    # 1. McCrary
    print("\n--- 1. McCrary/rddensity manipulation test ---")
    mccrary_pval = np.nan
    try:
        from rddensity import rddensity
        rd_den = rddensity(X=y_all, c=0)
        try:
            mccrary_pval = rd_den.p if hasattr(rd_den, "p") else np.nan
        except Exception:
            pass
        print(f"  rddensity p-value: {mccrary_pval}")

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 5))
            window = 30
            mask = np.abs(y_all) <= window
            y_win = y_all[mask]
            bin_edges = np.arange(np.floor(y_win.min()) - 0.5,
                                  np.ceil(y_win.max()) + 1.5, 1.0)
            left_vals = y_win[y_win < 0]
            right_vals = y_win[y_win >= 0]

            ax.hist(left_vals, bins=bin_edges, color="#2166ac", alpha=0.7,
                    edgecolor="white", linewidth=0.5,
                    label="Bajo el umbral (edad $<$ 65)")
            ax.hist(right_vals, bins=bin_edges, color="#b2182b", alpha=0.7,
                    edgecolor="white", linewidth=0.5,
                    label="Sobre el umbral (edad $\\geq$ 65)")
            ax.axvline(x=0, color="black", linestyle="--", linewidth=1.2,
                       alpha=0.8, label="Umbral (65 años)")
            ax.set_xlabel("Edad centrada en 65 años", fontsize=12)
            ax.set_ylabel("Frecuencia (número de individuos)", fontsize=12)
            test_label = (f"Test de densidad - Cattaneo, Jansson y Ma (2018): T $=$ {float(mccrary_pval):.2f}"
                          if isinstance(mccrary_pval, (int, float))
                          and not np.isnan(mccrary_pval)
                          else "Test de densidad - Cattaneo, Jansson y Ma (2018)")
            ax.set_title(test_label, fontsize=12)
            ax.legend(loc="upper right", fontsize=10)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            for ext in ("png", "pdf"):
                plt.savefig(FIGURES_DIR / f"figure_mccrary_density.{ext}",
                            dpi=150 if ext == "png" else 300, bbox_inches="tight")
            plt.close("all")
            print("  Saved: figure_mccrary_density.png/.pdf")
        except Exception as e:
            print(f"  Density plot failed: {e}")
    except ImportError:
        print("  rddensity not installed. Skipping.")
    except Exception as e:
        print(f"  McCrary test failed: {e}")

    all_results.append({
        "test": "mccrary", "outcome": "density", "estimate": mccrary_pval,
        "se_robust": np.nan, "ci_lower": np.nan, "ci_upper": np.nan,
        "bandwidth": np.nan, "N_eff": len(y_all), "method": "rddensity",
    })

    # 2. Placebo outcomes
    print("\n--- 2. Placebo outcomes ---")
    placebo_present = [p for p in PLACEBO_OUTCOMES if p in df.columns]
    for pv in placebo_present:
        res = run_rdd(df, pv, label="placebo")
        res["test"] = "placebo"
        all_results.append(res)
        sig = "*" if res.get("ci_lower", -1) > 0 or res.get("ci_upper", 1) < 0 else ""
        print(f"  {pv}: est={res['estimate']:.4f} CI=[{res.get('ci_lower', np.nan):.4f}, "
              f"{res.get('ci_upper', np.nan):.4f}] {sig}")

    # 3. Bandwidth sensitivity
    print("\n--- 3. Bandwidth sensitivity ---")
    baseline = run_rdd(df, PRIMARY_OUTCOME, label="bw_optimal")
    h_opt = baseline.get("bandwidth", 2.0)
    if np.isnan(h_opt) or h_opt <= 0:
        h_opt = 2.0
    for multiplier, label in [(0.5, "h_half"), (1.0, "h_optimal"), (2.0, "h_double")]:
        h = h_opt * multiplier
        res = run_rdd(df, PRIMARY_OUTCOME, h=h, label=f"bandwidth_{label}")
        res["test"] = f"bandwidth_{label}"
        all_results.append(res)
        print(f"  {label} (h={h:.2f}): est={res['estimate']:.4f} "
              f"CI=[{res.get('ci_lower', np.nan):.4f}, {res.get('ci_upper', np.nan):.4f}] "
              f"N_eff={res.get('N_eff', '?')}")

    # 4. Donut-hole
    print("\n--- 4. Donut-hole specifications ---")
    for donut in [0.5, 1.0, 2.0]:
        df_donut = df[np.abs(df[RUNNING_VAR]) > donut].copy()
        res = run_rdd(df_donut, PRIMARY_OUTCOME, h=h_opt, label=f"donut_{donut}")
        res["test"] = f"donut_{donut}"
        all_results.append(res)
        print(f"  Exclude |x|<={donut}: est={res['estimate']:.4f} "
              f"CI=[{res.get('ci_lower', np.nan):.4f}, {res.get('ci_upper', np.nan):.4f}] "
              f"N={len(df_donut)}")

    # 4b. SISFOH heterogeneity
    print("\n--- 4b. Heterogeneity by SISFOH (POBREZA) ---")
    if "POBREZA" in df.columns:
        sisfoh_labels = {1: "extreme_poor", 2: "non_extreme_poor", 3: "non_poor"}
        for code, label in sisfoh_labels.items():
            sub = df[df["POBREZA"] == code].copy()
            if len(sub) < 100:
                print(f"  POBREZA={code} ({label}): n={len(sub)}, skipping (too few obs)")
                continue
            try:
                res = run_rdd(sub, PRIMARY_OUTCOME, h=h_opt, label=f"het_sisfoh_{label}")
                res["test"] = f"het_sisfoh_{label}"
                all_results.append(res)
                print(f"  POBREZA={code} ({label}): est={res['estimate']:.4f} "
                      f"CI=[{res.get('ci_lower', np.nan):.4f}, {res.get('ci_upper', np.nan):.4f}] "
                      f"N_eff={res.get('N_eff', '?')}")
            except Exception as e:
                print(f"  POBREZA={code} ({label}): RDD failed ({e})")
    else:
        print("  POBREZA column not in data — skipping SISFOH heterogeneity")

    # 5. Covariate balance at bandwidth
    print(f"\n--- 5. Covariate balance at bandwidth (h={h_opt:.2f}) ---")
    df_bw = df[np.abs(df[RUNNING_VAR]) <= h_opt].copy()
    print(f"  Observations within bandwidth: {len(df_bw)}")
    cov_avail = [c for c in COVARIATES if c in df_bw.columns]
    for cov in cov_avail:
        res = run_rdd(df_bw, cov, h=h_opt, label="covariate_balance")
        res["test"] = "covariate_balance"
        res["outcome"] = cov
        all_results.append(res)
        sig = (" *IMBALANCED*"
               if (res.get("ci_lower", -1) > 0 or res.get("ci_upper", 1) < 0) else "")
        print(f"  {cov:20s}: est={res['estimate']:.4f} "
              f"CI=[{res.get('ci_lower', np.nan):.4f}, {res.get('ci_upper', np.nan):.4f}]{sig}")

    # 6. Polynomial sensitivity
    print("\n--- 6. Polynomial order sensitivity ---")
    if RDROBUST_OK:
        sub = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR])
        y_sub = sub[PRIMARY_OUTCOME].values
        x_sub = sub[RUNNING_VAR].values
        cl_sub = sub[CLUSTER_VAR].values if CLUSTER_VAR in sub.columns else None

        for p_order, p_label in [(1, "linear"), (2, "quadratic")]:
            try:
                kwargs = dict(y=y_sub, x=x_sub, p=p_order,
                              kernel="triangular", bwselect="mserd")
                if cl_sub is not None:
                    kwargs["cluster"] = cl_sub
                rd = rdrobust(**kwargs)
                est = _safe_scalar(rd.coef, 0)
                try:
                    ci_lo = float(rd.ci.iloc[-1, 0])
                    ci_hi = float(rd.ci.iloc[-1, 1])
                except Exception:
                    ci_lo = ci_hi = np.nan
                if np.isnan(est) and not np.isnan(ci_lo) and not np.isnan(ci_hi):
                    est = (ci_lo + ci_hi) / 2.0
                bw = float(rd.bws.iloc[0, 0]) if hasattr(rd.bws, "iloc") else np.nan
                n_eff = (int(rd.N_h[0]) + int(rd.N_h[1])
                         if hasattr(rd.N_h, "__getitem__") else 0)
                res = {"test": f"polynomial_{p_label}", "outcome": PRIMARY_OUTCOME,
                       "estimate": est, "se_robust": _safe_scalar(rd.se, -1),
                       "ci_lower": ci_lo, "ci_upper": ci_hi,
                       "bandwidth": bw, "N_eff": n_eff, "method": "rdrobust"}
                all_results.append(res)
                print(f"  p={p_order} ({p_label}): est={est:.4f} "
                      f"CI=[{ci_lo:.4f}, {ci_hi:.4f}] N_eff={n_eff}")
            except Exception as e:
                print(f"  p={p_order} ({p_label}): failed ({e})")
    else:
        print("  rdrobust not available — skipping polynomial sensitivity.")

    # 7. Placebo cutoff
    print("\n--- 7. Placebo cutoff test ---")
    sub_pc = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR]).copy()
    x_vals = sub_pc[RUNNING_VAR].values
    n_unique_x = len(np.unique(x_vals))
    if n_unique_x < 10:
        print(f"  Running variable has only {n_unique_x} unique values.")

    for pctile, label in [(25, "left_placebo"), (75, "right_placebo")]:
        cutoff = np.percentile(x_vals, pctile)
        if abs(cutoff) < 0.1:
            print(f"  {label}: cutoff={cutoff:.2f} too close to 0. Skipping.")
            continue
        if n_unique_x < 20:
            unique_sorted = np.sort(np.unique(x_vals))
            cutoff = unique_sorted[np.argmin(np.abs(unique_sorted - cutoff))]
        df_placebo_c = sub_pc.copy()
        df_placebo_c["_running_placebo"] = df_placebo_c[RUNNING_VAR] - cutoff
        if cutoff < 0:
            df_placebo_c = df_placebo_c[df_placebo_c[RUNNING_VAR] < 0]
        else:
            df_placebo_c = df_placebo_c[df_placebo_c[RUNNING_VAR] >= 0]
        if len(df_placebo_c) >= 30:
            y_pc = df_placebo_c[PRIMARY_OUTCOME].values
            x_pc = df_placebo_c["_running_placebo"].values
            try:
                if RDROBUST_OK:
                    rd_pc = rdrobust(y=y_pc, x=x_pc, kernel="triangular", bwselect="mserd")
                    est_pc = _safe_scalar(rd_pc.coef, 0)
                    try:
                        ci_lo_pc = float(rd_pc.ci.iloc[-1, 0])
                        ci_hi_pc = float(rd_pc.ci.iloc[-1, 1])
                    except Exception:
                        ci_lo_pc = ci_hi_pc = np.nan
                    if np.isnan(est_pc) and not np.isnan(ci_lo_pc) and not np.isnan(ci_hi_pc):
                        est_pc = (ci_lo_pc + ci_hi_pc) / 2.0
                    sig = " *FAILS*" if (ci_lo_pc > 0 or ci_hi_pc < 0) else ""
                    print(f"  {label} (cutoff={cutoff:.2f}): est={est_pc:.4f}  "
                          f"CI=[{ci_lo_pc:.4f}, {ci_hi_pc:.4f}]{sig}")
                    all_results.append({
                        "test": f"placebo_cutoff_{label}", "outcome": PRIMARY_OUTCOME,
                        "estimate": est_pc, "se_robust": _safe_scalar(rd_pc.se, -1),
                        "ci_lower": ci_lo_pc, "ci_upper": ci_hi_pc,
                        "bandwidth": (float(rd_pc.bws.iloc[0, 0])
                                      if hasattr(rd_pc.bws, "iloc") else np.nan),
                        "N_eff": len(df_placebo_c), "method": "rdrobust_placebo_cutoff",
                    })
            except Exception as e:
                print(f"  {label}: failed ({e})")

    # 8. Permutation inference
    print("\n--- 8. Permutation inference (randomized cutoffs) ---")
    sub_perm = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR]).copy()
    if len(sub_perm) >= 30:
        try:
            import statsmodels.api as sm
            y_perm = sub_perm[PRIMARY_OUTCOME].values
            x_perm = sub_perm[RUNNING_VAR].values
            x_std_perm = np.std(x_perm)
            if x_std_perm < 1e-10:
                raise ValueError("zero variance")
            h_perm = 1.5 * x_std_perm
            mask_real = np.abs(x_perm) <= h_perm
            y_bw_real = y_perm[mask_real]
            x_bw_real = x_perm[mask_real]
            treat_real = (x_bw_real >= 0).astype(float)
            weights_real = np.maximum(1 - np.abs(x_bw_real) / h_perm, 0)
            X_real = sm.add_constant(np.column_stack(
                [treat_real, x_bw_real, treat_real * x_bw_real]))
            mod_real = sm.WLS(y_bw_real, X_real, weights=weights_real).fit()
            t_real = mod_real.tvalues[1]

            n_perms = 500
            rng = np.random.default_rng(RANDOM_SEED)
            x_quantiles = np.percentile(x_perm, np.linspace(10, 90, 50))
            t_perms = []
            for _ in range(n_perms):
                c_fake = rng.choice(x_quantiles)
                x_shifted = x_perm - c_fake
                mask_p = np.abs(x_shifted) <= h_perm
                y_bw_p = y_perm[mask_p]
                x_bw_p = x_shifted[mask_p]
                if len(y_bw_p) < 10:
                    continue
                treat_p = (x_bw_p >= 0).astype(float)
                weights_p = np.maximum(1 - np.abs(x_bw_p) / h_perm, 0)
                X_p = sm.add_constant(np.column_stack(
                    [treat_p, x_bw_p, treat_p * x_bw_p]))
                try:
                    mod_p = sm.WLS(y_bw_p, X_p, weights=weights_p).fit()
                    t_perms.append(mod_p.tvalues[1])
                except Exception:
                    pass

            success_rate = len(t_perms) / n_perms if n_perms > 0 else 0
            if len(t_perms) > 100:
                t_perms = np.array(t_perms)
                perm_pval = np.mean(np.abs(t_perms) >= np.abs(t_real))
                print(f"  t_real: {t_real:.3f}")
                print(f"  Permutation p-value ({len(t_perms)} valid, "
                      f"{success_rate:.0%} success): {perm_pval:.4f}")
                all_results.append({
                    "test": "permutation_inference", "outcome": PRIMARY_OUTCOME,
                    "estimate": t_real, "se_robust": np.nan,
                    "pvalue": perm_pval,
                    "ci_lower": np.nan, "ci_upper": np.nan,
                    "bandwidth": h_perm, "N_eff": len(sub_perm),
                    "method": f"permutation_{len(t_perms)}",
                })
        except Exception as e:
            print(f"  Permutation inference failed: {e}")

    # 9. BH FDR
    print("\n--- 9. Multiple hypothesis correction (BH FDR) ---")
    testable = [r for r in all_results
                if "pvalue" in r and pd.notna(r.get("pvalue"))
                and r.get("pvalue", 1) < 1]
    if len(testable) > 1:
        pvals = np.array([r["pvalue"] for r in testable])
        n_p = len(pvals)
        ranked = np.argsort(pvals)
        adj = np.empty(n_p)
        for i, rank_idx in enumerate(reversed(ranked)):
            rank = n_p - i
            if i == 0:
                adj[rank_idx] = pvals[rank_idx]
            else:
                adj[rank_idx] = min(pvals[rank_idx] * n_p / rank,
                                    adj[ranked[n_p - i]])
        adj = np.minimum(adj, 1.0)
        for i, r in enumerate(testable):
            r["pvalue_bh"] = adj[i]
        print(f"  Corrected {n_p} tests.")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(ROBUSTNESS_CSV, index=False)
    print(f"\nSaved: {ROBUSTNESS_CSV} ({len(results_df)} rows)\n")


# ════════════════════════════════════════════════════════════════════════════
# FASE 5 — Output: tablas y figuras (03_output.py)
# ════════════════════════════════════════════════════════════════════════════
def _fmt(val, decimals=4):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "---"
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)


def _texvar(name: str) -> str:
    return str(name).replace("_", "\\_")


def _validate_table(content, filename):
    problems = []
    if "nan" in content.lower():
        problems.append("Contains 'nan'")
    if "& &" in content:
        problems.append("Contains empty cells (& &)")
    if "& \\\\" in content:
        problems.append("Contains empty last column (& \\\\)")
    if problems:
        print(f"  WARNING in {filename}: {', '.join(problems)}")
        content = content.replace("nan", "---")
        content = content.replace("NaN", "---")
        content = content.replace("None", "---")
        while "& &" in content:
            content = content.replace("& &", "& --- &")
        content = content.replace("& \\\\", "& --- \\\\")
        print("  Auto-fixed.")
    return content


def _make_table1(df):
    print("Generating Table 1: Summary statistics...")
    treated = df[df["treat"] == 1]
    control = df[df["treat"] == 0]

    h_opt = 14.24
    bw_mask = np.abs(df.get("running_centered", df[RUNNING_VAR_RAW] - 65)) <= h_opt
    df_bw = df[bw_mask]
    n_below_bw = int((df_bw.get("running_centered",
                                 df_bw[RUNNING_VAR_RAW] - 65) < 0).sum())
    n_above_bw = int((df_bw.get("running_centered",
                                 df_bw[RUNNING_VAR_RAW] - 65) >= 0).sum())

    stat_vars = [v for v in (OUTCOME_VARS + COVARIATES) if v in df.columns]

    tex = [
        r"\begin{threeparttable}",
        r"\begin{tabular}{l cccc cccc}",
        r"\toprule",
        r"& \multicolumn{4}{c}{Above Threshold (Treated)} & \multicolumn{4}{c}{Below Threshold (Control)} \\",
        r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}",
        r"Variable & Mean & SD & N & --- & Mean & SD & N & --- \\",
        r"\midrule",
    ]

    for var in stat_vars:
        t_s = treated[var].dropna()
        c_s = control[var].dropna()
        tex.append(
            f"  {_texvar(var)} & {_fmt(t_s.mean())} & {_fmt(t_s.std())} & {len(t_s)} & --- "
            f"& {_fmt(c_s.mean())} & {_fmt(c_s.std())} & {len(c_s)} & --- \\\\"
        )

    tex += [
        r"\midrule",
        f"  Observations & \\multicolumn{{4}}{{c}}{{{len(treated)}}} "
        f"& \\multicolumn{{4}}{{c}}{{{len(control)}}} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        (
            r"\item \textit{Notes:} Summary statistics for the full RDD analysis sample. "
            r"'Above Threshold' (treated$=1$) denotes individuals aged 65 and above; "
            r"'Below Threshold' (treated$=0$) under age 65. The treated/control split (" +
            f"{len(treated):,}".replace(",", "{,}") + r" vs.\ " +
            f"{len(control):,}".replace(",", "{,}") + r") is asymmetric; within the bandwidth-"
            r"restricted estimation window ($\pm h^{\ast}\!=\!\pm 14.24$ years) the split is " +
            f"{n_below_bw:,}".replace(",", "{,}") + r" below and " +
            f"{n_above_bw:,}".replace(",", "{,}") + r" above the cutoff. "
            r"'---' indicates unavailable data."
        ),
        r"\end{tablenotes}",
        r"\end{threeparttable}",
    ]

    content = _validate_table("\n".join(tex), "table_1_summary.tex")
    path = TABLES_DIR / "table_1_summary.tex"
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path}")


def _make_rdd_table(results_df, spec_filter_fn, title, filename, footnote, outcomes=None):
    """CAMBIO 6: generador genérico de tabla RDD filtrada por especificación."""
    print(f"Generating {filename}...")
    filtered = results_df[results_df["specification"].apply(spec_filter_fn)].copy()
    if len(filtered) == 0:
        print(f"  No matching results. Skipping {filename}.")
        return

    if outcomes is None:
        outcomes = filtered["outcome"].unique().tolist()

    ncols = len(outcomes)
    tex = [
        r"\begin{threeparttable}",
        r"\begin{tabular}{l " + "c" * ncols + "}",
        r"\toprule",
        r"\multicolumn{" + str(ncols + 1) + r"}{c}{\textit{" + title + r"}} \\",
        r"\midrule",
        "  & " + " & ".join(_texvar(o) for o in outcomes) + " \\\\",
        r"\midrule",
    ]

    for spec in filtered["specification"].unique():
        tex.append(r"\addlinespace")
        tex.append(
            f"\\multicolumn{{{ncols + 1}}}{{l}}"
            f"{{\\textit{{{_texvar(spec)}}}}} \\\\"
        )
        spec_data = filtered[filtered["specification"] == spec]

        for lbl, key, fd in [("Estimate", "estimate", 4), ("SE (robust)", "se_robust", 4)]:
            row = f"  {lbl}"
            for outcome in outcomes:
                m = spec_data[spec_data["outcome"] == outcome]
                if len(m) > 0:
                    val = m.iloc[0].get(key, np.nan)
                    row += f" & ({_fmt(val, fd)})" if key == "se_robust" else f" & {_fmt(val, fd)}"
                else:
                    row += " & ---"
            tex.append(row + " \\\\")

        row = r"  95\% CI"
        for outcome in outcomes:
            m = spec_data[spec_data["outcome"] == outcome]
            if len(m) > 0:
                row += f" & [{_fmt(m.iloc[0].get('ci_lower', np.nan))}, {_fmt(m.iloc[0].get('ci_upper', np.nan))}]"
            else:
                row += " & ---"
        tex.append(row + " \\\\")

        row = "  N / BW"
        for outcome in outcomes:
            m = spec_data[spec_data["outcome"] == outcome]
            if len(m) > 0:
                try:
                    n_str = f"{int(float(m.iloc[0].get('N_eff', 0))):,}".replace(",", "{,}")
                except (ValueError, TypeError):
                    n_str = "---"
                row += f" & {n_str} / {_fmt(m.iloc[0].get('bandwidth', np.nan), 2)}"
            else:
                row += " & ---"
        tex.append(row + " \\\\")

        row = "  Method"
        for outcome in outcomes:
            m = spec_data[spec_data["outcome"] == outcome]
            row += f" & {_texvar(str(m.iloc[0].get('method', '---')))}" if len(m) > 0 else " & ---"
        tex.append(row + " \\\\")

    tex += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        r"\item \textit{Notes:} " + footnote,
        r"\end{tablenotes}",
        r"\end{threeparttable}",
    ]

    content = _validate_table("\n".join(tex), filename)
    (TABLES_DIR / filename).write_text(content, encoding="utf-8")
    print(f"  Saved: {TABLES_DIR / filename}")


def _make_table3(robust):
    print("Generating Table 3: Robustness...")
    tex = [
        r"\begin{threeparttable}",
        r"\begin{tabular}{l ccccc}",
        r"\toprule",
        r"Test & Estimate & SE & 95\% CI & BW & N \\",
        r"\midrule",
    ]
    panels = [
        ("Panel A: Bandwidth sensitivity",   "bandwidth"),
        ("Panel B: Donut-hole",                "donut"),
        ("Panel C: Polynomial",                "polynomial"),
        ("Panel D: Placebo (covariates as outcomes)", "placebo"),
    ]
    for panel_name, prefix in panels:
        panel_data = robust[
            robust["test"].str.startswith(prefix) &
            ~robust["test"].str.startswith("het_sisfoh_")
        ]
        if len(panel_data) == 0:
            continue
        tex.append(f"\\multicolumn{{6}}{{l}}{{\\textit{{{panel_name}}}}} \\\\")
        for _, r in panel_data.iterrows():
            test_name = r.get("test", "")
            if prefix == "donut":
                tail = test_name.replace("donut_", "")
                label = r"$\pm$" + tail + " yr"
            elif prefix == "placebo":
                outcome = r.get("outcome", "")
                label = _texvar(outcome.replace("placebo_", ""))
            else:
                label = test_name.replace(f"{prefix}_", "").replace("_", " ").title()
            try:
                n_eff_int = (int(float(r["N_eff"]))
                             if pd.notna(r.get("N_eff"))
                             and float(r["N_eff"]) > 0 else None)
            except (ValueError, TypeError):
                n_eff_int = None
            n_str = f"{n_eff_int:,}".replace(",", "{,}") if n_eff_int else "---"
            tex.append(
                f"  {label} & {_fmt(r['estimate'])} & {_fmt(r.get('se_robust', np.nan))} "
                f"& [{_fmt(r.get('ci_lower', np.nan))}, {_fmt(r.get('ci_upper', np.nan))}] "
                f"& {_fmt(r.get('bandwidth', np.nan), 2)} "
                f"& {n_str} \\\\"
            )
        tex.append(r"\addlinespace")

    tex += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        (
            r"\item \textit{Notes:} All specifications use local linear regression with "
            r"triangular kernel and MSE-optimal bandwidth. Robust bias-corrected confidence "
            r"intervals reported."
        ),
        r"\end{tablenotes}",
        r"\end{threeparttable}",
    ]

    content = _validate_table("\n".join(tex), "table_3_robustness.tex")
    path = TABLES_DIR / "table_3_robustness.tex"
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path}")


def _make_table4(robust):
    print("Generating Table 4: Covariate balance...")
    cov_data = robust[robust["test"] == "covariate_balance"]
    if len(cov_data) == 0:
        print("  No covariate balance results. Skipping.")
        return

    tex = [
        r"\begin{threeparttable}",
        r"\begin{tabular}{l ccccc}",
        r"\toprule",
        r"Covariate & RD Estimate & SE & 95\% CI & BW & N \\",
        r"\midrule",
    ]
    for _, r in cov_data.iterrows():
        ci_lo = r.get("ci_lower", np.nan)
        ci_hi = r.get("ci_upper", np.nan)
        sig = ""
        if pd.notna(ci_lo) and pd.notna(ci_hi):
            if ci_lo > 0 or ci_hi < 0:
                sig = "$^{*}$"
        try:
            n_eff_int = (int(float(r["N_eff"]))
                         if pd.notna(r.get("N_eff"))
                         and float(r["N_eff"]) > 0 else None)
        except (ValueError, TypeError):
            n_eff_int = None
        n_str = f"{n_eff_int:,}".replace(",", "{,}") if n_eff_int else "---"
        tex.append(
            f"  {_texvar(r['outcome'])} & {_fmt(r['estimate'])}{sig} "
            f"& {_fmt(r.get('se_robust', np.nan))} "
            f"& [{_fmt(ci_lo)}, {_fmt(ci_hi)}] "
            f"& {_fmt(r.get('bandwidth', np.nan), 2)} "
            f"& {n_str} \\\\"
        )

    tex += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        (
            r"\item \textit{Notes:} RDD estimates with each covariate as outcome, "
            r"restricted to within the MSE-optimal bandwidth. $^{*}$ 95\% CI excludes zero."
        ),
        r"\end{tablenotes}",
        r"\end{threeparttable}",
    ]

    content = _validate_table("\n".join(tex), "table_4_covariate_balance.tex")
    path = TABLES_DIR / "table_4_covariate_balance.tex"
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path}")


def _make_figure1(df):
    print("Generating Figure 1: RD plot...")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sub = df.dropna(subset=[PRIMARY_OUTCOME, RUNNING_VAR])
    x = sub[RUNNING_VAR].values
    y = sub[PRIMARY_OUTCOME].values
    if len(x) < 20:
        print("  Insufficient data. Skipping.")
        return

    x_range = 18.04
    mask = np.abs(x) <= x_range
    x_p, y_p = x[mask], y[mask]
    n_bins = 25

    def bin_scatter(xv, yv, nbins):
        if len(xv) < nbins:
            return xv, yv
        bins = np.linspace(xv.min(), xv.max(), nbins + 1)
        cx, cy = [], []
        for i in range(nbins):
            m = (xv >= bins[i]) & (xv < bins[i + 1])
            if i == nbins - 1:
                m = (xv >= bins[i]) & (xv <= bins[i + 1])
            if m.sum() > 0:
                cx.append(xv[m].mean())
                cy.append(yv[m].mean())
        return np.array(cx), np.array(cy)

    x_left, y_left = x_p[x_p < 0], y_p[x_p < 0]
    x_right, y_right = x_p[x_p >= 0], y_p[x_p >= 0]

    fig, ax = plt.subplots(figsize=(8, 5))
    if len(x_left) > 3:
        bx, by = bin_scatter(x_left, y_left, n_bins)
        ax.scatter(bx, by, color="#2166ac", s=60, zorder=3, label="Bajo el umbral")
        coeffs = np.polyfit(x_left, y_left, 1)
        xs = np.linspace(x_left.min(), 0, 100)
        ax.plot(xs, np.poly1d(coeffs)(xs), color="#2166ac", linewidth=2)
    if len(x_right) > 3:
        bx, by = bin_scatter(x_right, y_right, n_bins)
        ax.scatter(bx, by, color="#b2182b", s=60, zorder=3, label="Sobre el umbral")
        coeffs = np.polyfit(x_right, y_right, 1)
        xs = np.linspace(0, x_right.max(), 100)
        ax.plot(xs, np.poly1d(coeffs)(xs), color="#b2182b", linewidth=2)
    ax.axvline(x=0, color="black", linestyle="--", linewidth=1, alpha=0.7,
               label="Umbral (65 años)")
    ax.set_xlim(-x_range, x_range)
    ax.set_xlabel("Edad centrada en 65 años", fontsize=12)
    ax.set_ylabel("Tiene Billetera", fontsize=12)
    ax.set_title("Adopción de billeteras digitales por edad (ENAHO 2024)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.text(0.02, 0.97, "Ancho de banda óptimo: h = 18.04 años",
            transform=ax.transAxes, fontsize=9, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    plt.tight_layout()
    for ext in ["png", "pdf"]:
        plt.savefig(FIGURES_DIR / f"figure_1_rdplot.{ext}",
                    dpi=150 if ext == "png" else 300, bbox_inches="tight")
    plt.close("all")
    print("  Saved: figure_1_rdplot.png/.pdf")


def _make_figure2(robust):
    print("Generating Figure 2: Bandwidth sensitivity...")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bw_data = robust[robust["test"].str.startswith("bandwidth")].copy()
    if len(bw_data) == 0:
        print("  No bandwidth results. Skipping.")
        return

    bw_data = bw_data.sort_values("bandwidth")
    estimates = bw_data["estimate"].values.copy()
    ci_lo = bw_data["ci_lower"].values
    ci_hi = bw_data["ci_upper"].values
    for i in range(len(estimates)):
        if np.isnan(estimates[i]) and not np.isnan(ci_lo[i]) and not np.isnan(ci_hi[i]):
            estimates[i] = (ci_lo[i] + ci_hi[i]) / 2.0

    labels = []
    for _, r in bw_data.iterrows():
        bw = r.get("bandwidth", np.nan)
        lab = r["test"].replace("bandwidth_", "")
        labels.append(f"{lab}\n(h={bw:.2f})" if pd.notna(bw) else lab)

    yerr_lo = np.where(np.isnan(estimates - ci_lo), 0, estimates - ci_lo)
    yerr_hi = np.where(np.isnan(ci_hi - estimates), 0, ci_hi - estimates)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.errorbar(range(len(estimates)), estimates, yerr=[yerr_lo, yerr_hi],
                fmt="o", color="#2166ac", capsize=5, capthick=2,
                markersize=8, linewidth=2)
    ax.axhline(y=0, color="black", linestyle="--", linewidth=1, alpha=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("RD Estimate", fontsize=12)
    ax.set_title("Bandwidth Sensitivity", fontsize=13)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    for ext in ["png", "pdf"]:
        plt.savefig(FIGURES_DIR / f"figure_2_bandwidth_sensitivity.{ext}",
                    dpi=150 if ext == "png" else 300, bbox_inches="tight")
    plt.close("all")
    print("  Saved: figure_2_bandwidth_sensitivity.png/.pdf")


def phase_5_output():
    print("=" * 70)
    print("FASE 5 — Tables and Figures")
    print("=" * 70)

    # Lee muestra completa para tabla 1 y figuras (muestra principal)
    df = pd.read_csv(PATHS["clean_data_full"])
    print(f"Clean data (df_full): {len(df)} rows")
    main_results = pd.read_csv(MAIN_RESULTS_CSV)
    print(f"Main results: {len(main_results)} rows")
    robust = pd.read_csv(ROBUSTNESS_CSV) if ROBUSTNESS_CSV.exists() else None
    if robust is not None:
        print(f"Robustness: {len(robust)} rows")

    print()
    _make_table1(df)

    # Four output tables: main (MAIN_ not het), heterogeneity (het + EP_descriptivo),
    # RDD2 SISFOH, appendix EP descriptivo.
    _note_main = (
        r"Local linear RDD (\texttt{rdrobust}), triangular kernel, MSE-optimal bandwidth. "
        r"Robust bias-corrected SE in parentheses. "
        r"Sample is the full ENAHO 2024 near the age-65 threshold."
    )
    _make_rdd_table(
        main_results,
        lambda s: str(s).startswith("MAIN_") and "het" not in str(s),
        "Main RDD Estimates: Full ENAHO Sample",
        "table_2_main_results.tex",
        _note_main,
    )
    _make_rdd_table(
        main_results,
        lambda s: "het" in str(s) or str(s).startswith("EP_descriptivo"),
        "Heterogeneity Analysis",
        "table_3_heterogeneity.tex",
        (r"Panel A (EP\_het\_): extreme-poor subsample (POBREZA$=1$). "
         r"Panel B (MAIN\_het\_AREA\_): full sample split by urban/rural. "
         r"Panel C (EP\_descriptivo): extreme-poor baseline for reference. "
         r"\textit{low\_power} flag indicates N$<$200 on either side of the cutoff. "
         r"Urban--rural digital gap documented in BCRP (2024) and BIS WP 1200 (2024)."),
    )
    _make_rdd_table(
        main_results,
        lambda s: str(s).startswith("EP_descriptivo"),
        "Appendix: Extreme-Poor Subsample (Descriptive)",
        "table_A1_ep_descriptivo.tex",
        (r"These estimates describe the RDD estimates within the extreme-poor subsample "
         r"(POBREZA$=1$) for reference. Power is limited due to the small share of "
         r"extreme-poor respondents ($\approx5\%$) near the age-65 cutoff."),
    )

    if robust is not None:
        _make_table3(robust)
        _make_table4(robust)

    # BLOQUE F: tabla RDD2 IFH (Bernal, Carpio y Klein 2017)
    if PATHS["rdd2_results"].exists():
        rdd2_res = pd.read_csv(PATHS["rdd2_results"])
        _make_rdd_table(
            rdd2_res,
            lambda s: str(s).startswith("RDD2_IFH_") and "balance" not in str(s),
            ("RDD2: Índice de Focalización de Hogares (IFH) como running variable "
             "(Adultos ≥65, siguiendo Bando, Galiani y Gertler 2020)"),
            "table_4_rdd2_ifh.tex",
            (r"La running variable es el Índice de Focalización de Hogares (IFH) de "
             r"Bernal, Carpio y Klein (2017), construido con pesos de las Tablas A.8/A.9 "
             r"del Apéndice F y estandarizado en [0--100] por departamento. "
             r"El umbral varía por departamento según la Tabla A.10 (rango: 33--55). "
             r"Muestra: adultos mayores (EDAD$\geq$65) en ENAHO 2024 con IFH no nulo "
             r"(N=13{,}766). Este diseño replica la estrategia de identificación de "
             r"Bando, Galiani y Gertler (2020) aplicada a la adopción de billetera digital."),
        )
    else:
        print("  table_4_rdd2_ifh.tex: rdd2_results.csv no encontrado, saltando.")

    print()
    _make_figure1(df)
    if robust is not None:
        _make_figure2(robust)

    print("\n--- Final table validation ---")
    all_clean = True
    for tex_file in sorted(TABLES_DIR.iterdir()):
        if tex_file.suffix == ".tex":
            content = tex_file.read_text(encoding="utf-8")
            if "nan" in content.lower() or "& &" in content:
                print(f"  PROBLEM: {tex_file.name} still has blank/NaN cells!")
                all_clean = False
    if all_clean:
        print("  All tables validated: no NaN or blank cells.")
    print()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "#" * 70)
    print("# PIPELINE COMPLETO — Pensión 65 RDD digital wallet")
    print(f"# Repo root: {REPO_ROOT}")
    print("#" * 70 + "\n")

    print("  RESULTADO PRINCIPAL: muestra completa (df_full)")
    print("  ANÁLISIS COMPLEMENTARIO: extrema pobreza (df_main) y RDD2")
    phase_0_download_from_inei()
    phase_1_preprocess()
    phase_2_clean()
    phase_3_main()
    phase_3b_bloque_f()
    phase_4_robustness()
    phase_5_output()

    print("#" * 70)
    print("# PIPELINE COMPLETO — DONE")
    print("#" * 70)
    print(f"\nOutputs generados:")
    print(f"\n  [Datos]")
    print(f"  {ENAHO_CLEAN_CSV}")
    print(f"  {CLEAN_DATA_CSV}  (legacy)")
    print(f"  {PATHS['clean_data_full']}")
    print(f"  {PATHS['clean_data_main']}")
    print(f"  {MAIN_RESULTS_CSV}")
    print(f"  {ROBUSTNESS_CSV}")
    print(f"  {PATHS['dilution_calc']}")
    print(f"\n  [Tablas LaTeX]")
    print(f"  {TABLES_DIR / 'table_1_summary.tex'}")
    print(f"  {TABLES_DIR / 'table_2_main_results.tex'}     ← MAIN_ baseline/covariates/dpto_fe (df_full)")
    print(f"  {TABLES_DIR / 'table_3_heterogeneity.tex'}    ← EP_het_ + MAIN_het_AREA_ + EP_descriptivo")
    print(f"  {TABLES_DIR / 'table_3_robustness.tex'}")
    print(f"  {TABLES_DIR / 'table_4_covariate_balance.tex'}")
    print(f"  {TABLES_DIR / 'table_4_rdd2_ifh.tex'}    ← BLOQUE F: RDD2 IFH (BCK 2017)")
    print(f"  {TABLES_DIR / 'table_A1_ep_descriptivo.tex'} ← apéndice extrema pobreza")
    print(f"\n  [Datos BLOQUE F]")
    print(f"  {PATHS['rdd2_mayores']}")
    print(f"  {PATHS['rdd2_results']}")
    print(f"\n  [Figuras]")
    print(f"  {FIGURES_DIR}/figure_mccrary_density.png/.pdf")
    print(f"  {FIGURES_DIR}/figure_1_rdplot.png/.pdf")
    print(f"  {FIGURES_DIR}/figure_2_bandwidth_sensitivity.png/.pdf")
    print(f"  {FIGURES_DIR}/figure_rdd2_density.png/.pdf")
    print(f"  {FIGURES_DIR}/figure_rdd2_rdplot.png/.pdf")


if __name__ == "__main__":
    main()
