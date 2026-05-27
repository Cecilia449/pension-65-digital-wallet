"""
explorar_variables_enaho.py
───────────────────────────
Script de exploración rápida de variables ENAHO 2024 para la construcción
del proxy SISFOH. Descarga solo los módulos necesarios (01, 18 y Sumaria),
lista todas las columnas disponibles y verifica cuáles de las variables
candidatas para el PCA realmente existen en los datos.

USO:
    python explorar_variables_enaho.py

OUTPUTS (en el mismo directorio):
    variables_enaho_exploración.txt   — reporte completo en texto
    variables_pca_disponibles.csv     — tabla de variables candidatas con estado
"""

import io
import sys
import subprocess
import urllib.request
import urllib.error
import zipfile
from pathlib import Path

# ── Instalar dependencias mínimas ─────────────────────────────────────────────
for pkg in ["pandas", "numpy"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

import pandas as pd
import numpy as np

# ── Configuración ─────────────────────────────────────────────────────────────
OUTPUT_DIR   = Path(__file__).resolve().parent
REPORT_TXT   = OUTPUT_DIR / "variables_enaho_exploracion.txt"
REPORT_CSV   = OUTPUT_DIR / "variables_pca_disponibles.csv"
EXTRACT_DIR  = OUTPUT_DIR / "_enaho_temp"
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

INEI_BASE    = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV"
SURVEY_CODE  = "966"
HEADERS      = {"User-Agent": "Mozilla/5.0"}

# Solo los módulos relevantes para el PCA SISFOH
MODULES_NEEDED = [
    ("01", "Enaho01-2024-100.csv",  "m01_vivienda"),
    ("18", "Enaho01-2024-612.csv",  "m18_equipamiento"),
    ("34", "Sumaria-2024.csv",      "sumaria"),
]

# Variables candidatas para el PCA SISFOH con todos sus posibles alias en ENAHO
# Formato: nombre_canónico → {alias posibles, módulo fuente, descripción}
PCA_CANDIDATES = {
    "PARED": {
        "aliases": ["PARED", "P102"],
        "module": "m01_vivienda",
        "description": "Material predominante de paredes exteriores",
        "filmer_pritchett": True,
    },
    "PISO": {
        "aliases": ["PISO", "P103"],
        "module": "m01_vivienda",
        "description": "Material predominante de pisos",
        "filmer_pritchett": True,
    },
    "CUARTOS": {
        "aliases": ["P104", "CUARTOS"],
        "module": "m01_vivienda",
        "description": "Número de habitaciones del hogar (para hacinamiento)",
        "filmer_pritchett": True,
    },
    "ABASTAGUADOM": {
        "aliases": ["ABASTAGUADOM", "P110"],
        "module": "m01_vivienda",
        "description": "Abastecimiento de agua en el hogar",
        "filmer_pritchett": True,
    },
    "SERVSANIT": {
        "aliases": ["SERVSANIT", "P111"],
        "module": "m01_vivienda",
        "description": "Servicio sanitario / desagüe",
        "filmer_pritchett": True,
    },
    "ALUMBRADO": {
        "aliases": ["ALUMBRADO", "P112"],
        "module": "m01_vivienda",
        "description": "Alumbrado del hogar",
        "filmer_pritchett": True,
    },
    "COMBUSTIBLE": {
        "aliases": ["COMBUSTIBLE", "P113"],
        "module": "m01_vivienda",
        "description": "Combustible para cocinar",
        "filmer_pritchett": False,
    },
    "INTERNET_HOGAR": {
        "aliases": ["P114B2", "INTERNET_HOGAR"],
        "module": "m01_vivienda",
        "description": "Acceso a internet en el hogar",
        "filmer_pritchett": False,
    },
    "SMARTPHONE": {
        "aliases": ["SMARTPHONE"],
        "module": "m18_equipamiento",
        "description": "Tenencia de smartphone (P612N=10)",
        "filmer_pritchett": False,
    },
    "REFRIGERADOR": {
        "aliases": ["REFRIGERADOR"],
        "module": "m18_equipamiento",
        "description": "Tenencia de refrigeradora (P612N=4)",
        "filmer_pritchett": False,
    },
    "TIENE_TV": {
        "aliases": ["TIENE_TV"],
        "module": "m18_equipamiento",
        "description": "Tenencia de televisor (P612N=2)",
        "filmer_pritchett": False,
    },
    "LAVADORA": {
        "aliases": ["LAVADORA"],
        "module": "m18_equipamiento",
        "description": "Tenencia de lavadora (P612N=5)",
        "filmer_pritchett": False,
    },
    "COMPUTADORA": {
        "aliases": ["COMPUTADORA"],
        "module": "m18_equipamiento",
        "description": "Tenencia de computadora/laptop (P612N=3 o 9)",
        "filmer_pritchett": False,
    },
    "INGRESO_PC": {
        "aliases": ["INGRESO_PC", "INGHOG2D"],
        "module": "sumaria",
        "description": "Ingreso per cápita del hogar",
        "filmer_pritchett": True,
    },
    "MIEPERHO": {
        "aliases": ["MIEPERHO"],
        "module": "sumaria",
        "description": "Número de miembros del hogar",
        "filmer_pritchett": False,
    },
    "POBREZA": {
        "aliases": ["POBREZA"],
        "module": "sumaria",
        "description": "Clasificación de pobreza monetaria INEI",
        "filmer_pritchett": False,
    },
}

# ── Funciones ─────────────────────────────────────────────────────────────────

def download_module(code: str, csv_name: str, alias: str) -> pd.DataFrame | None:
    url = f"{INEI_BASE}/{SURVEY_CODE}-Modulo{code}.zip"
    dest = EXTRACT_DIR / csv_name
    if dest.exists():
        print(f"  [{alias}] Ya existe localmente: {csv_name}")
    else:
        print(f"  [{alias}] Descargando módulo {code} desde INEI...")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=120) as resp:
                zip_bytes = resp.read()
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                matches = [n for n in zf.namelist() if n.endswith(csv_name)]
                if not matches:
                    print(f"    ERROR: {csv_name} no encontrado en el zip.")
                    print(f"    Contenido: {zf.namelist()[:10]}")
                    return None
                with zf.open(matches[0]) as src:
                    dest.write_bytes(src.read())
            size_mb = dest.stat().st_size / 1e6
            print(f"    OK ({size_mb:.1f} MB)")
        except urllib.error.HTTPError as e:
            print(f"    ERROR HTTP {e.code}: {e.reason} — URL: {url}")
            return None
        except Exception as e:
            print(f"    ERROR: {e}")
            return None

    df = pd.read_csv(dest, encoding="latin-1", low_memory=False, nrows=5)
    df.columns = [c.upper() for c in df.columns]
    return df


def check_m18_items(m18_sample: pd.DataFrame) -> dict:
    """
    El módulo 18 es formato long: P612N identifica el bien.
    Mapea los códigos de ítems relevantes para el PCA.
    """
    item_map = {
        2:  "TIENE_TV",
        3:  "COMPUTADORA_DESKTOP",
        4:  "REFRIGERADOR",
        5:  "LAVADORA",
        9:  "LAPTOP",
        10: "SMARTPHONE",
        11: "TABLET",
    }
    found = {}
    if "P612N" in m18_sample.columns:
        unique_codes = pd.to_numeric(m18_sample["P612N"], errors="coerce").dropna().unique()
        for code, name in item_map.items():
            found[name] = {
                "code_P612N": code,
                "in_data": int(code) in [int(x) for x in unique_codes],
                "description": f"Tenencia del bien (P612N={code})",
            }
        print(f"    Códigos P612N encontrados: {sorted([int(x) for x in unique_codes if not np.isnan(x)])}")
    else:
        print("    ADVERTENCIA: columna P612N no encontrada en módulo 18.")
    return found


def explore_module_columns(df: pd.DataFrame, alias: str) -> dict:
    """Retorna stats básicos de todas las columnas del módulo."""
    stats = {}
    for col in df.columns:
        s = df[col]
        stats[col] = {
            "dtype": str(s.dtype),
            "n_unique_sample": s.nunique(),
            "sample_values": str(s.dropna().head(3).tolist()),
        }
    return stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    lines = []  # para el reporte .txt
    results = []  # para el reporte .csv

    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 70)
    log("EXPLORACIÓN DE VARIABLES ENAHO 2024 — PROXY SISFOH")
    log("=" * 70)

    modules_data = {}
    for code, csv_name, alias in MODULES_NEEDED:
        print(f"\n[Descarga] {alias}")
        df = download_module(code, csv_name, alias)
        if df is not None:
            modules_data[alias] = df
            log(f"\n{'─'*60}")
            log(f"MÓDULO: {alias.upper()} ({csv_name})")
            log(f"  Filas (muestra): {len(df)} | Columnas: {len(df.columns)}")
            log(f"  Columnas disponibles:")
            for i, col in enumerate(sorted(df.columns)):
                log(f"    {col}")
        else:
            log(f"\n  ERROR: no se pudo cargar {alias}")

    # ── Verificación de variables candidatas PCA ──────────────────────────────
    log("\n" + "=" * 70)
    log("VERIFICACIÓN DE VARIABLES CANDIDATAS PARA EL PCA SISFOH")
    log("=" * 70)
    log(f"{'Variable':<20} {'Estado':<12} {'Alias encontrado':<25} {'F&P?':<6} {'Descripción'}")
    log("─" * 100)

    # Verificar m18 items por separado (formato long)
    m18_items = {}
    if "m18_equipamiento" in modules_data:
        log("\n[M18 Equipamiento — formato long, columna P612N]")
        m18_items = check_m18_items(modules_data["m18_equipamiento"])
        for item_name, info in m18_items.items():
            status = "✓ EXISTE" if info["in_data"] else "✗ NO"
            log(f"    P612N={info['code_P612N']:>2}  {item_name:<20} {status}")

    for canon, info in PCA_CANDIDATES.items():
        mod_alias = info["module"]
        fp_flag = "✓" if info["filmer_pritchett"] else " "

        # Caso especial: variables derivadas del módulo 18
        if mod_alias == "m18_equipamiento":
            in_data = m18_items.get(canon, {}).get("in_data", False)
            found_alias = f"P612N={m18_items.get(canon, {}).get('code_P612N', '?')}" if in_data else "—"
            status = "✓ EXISTE" if in_data else "✗ NO"
            log(f"  {canon:<20} {status:<12} {found_alias:<25} {fp_flag:<6} {info['description']}")
            results.append({
                "variable_canonica": canon,
                "estado": status,
                "alias_encontrado": found_alias,
                "modulo": mod_alias,
                "filmer_pritchett": info["filmer_pritchett"],
                "descripcion": info["description"],
            })
            continue

        if mod_alias not in modules_data:
            status = "⚠ MÓDULO NO CARGADO"
            found_alias = "—"
        else:
            df_mod = modules_data[mod_alias]
            found_alias = next((a for a in info["aliases"] if a in df_mod.columns), None)
            status = f"✓ EXISTE" if found_alias else "✗ NO ENCONTRADA"
            found_alias = found_alias or "—"

        log(f"  {canon:<20} {status:<12} {found_alias:<25} {fp_flag:<6} {info['description']}")
        results.append({
            "variable_canonica": canon,
            "estado": status,
            "alias_encontrado": found_alias,
            "modulo": mod_alias,
            "filmer_pritchett": info["filmer_pritchett"],
            "descripcion": info["description"],
        })

    # ── Resumen ───────────────────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("RESUMEN")
    log("=" * 70)

    disponibles = [r for r in results if "EXISTE" in r["estado"]]
    faltantes   = [r for r in results if "EXISTE" not in r["estado"]]
    fp_disp     = [r for r in disponibles if r["filmer_pritchett"]]

    log(f"\n  Variables disponibles:          {len(disponibles)} / {len(results)}")
    log(f"  Filmer & Pritchett disponibles: {len(fp_disp)} / {sum(1 for r in results if r['filmer_pritchett'])}")
    log(f"  Variables no encontradas:       {len(faltantes)}")

    if faltantes:
        log("\n  Variables faltantes:")
        for r in faltantes:
            log(f"    - {r['variable_canonica']} ({r['modulo']}): {r['descripcion']}")

    log("\n  Variables recomendadas para el PCA (Filmer & Pritchett 2001 + bienes durables):")
    for r in disponibles:
        marker = "[F&P]" if r["filmer_pritchett"] else "[bien durable]"
        log(f"    ✓ {r['variable_canonica']:<20} {marker:<16} alias={r['alias_encontrado']}")

    log("\n" + "=" * 70)
    log("NOTA METODOLÓGICA")
    log("=" * 70)
    log("""
  El proxy SISFOH sigue la lógica del proxy means test del MIDIS.
  Las variables de Filmer & Pritchett (2001) son el núcleo canónico:
  vivienda (paredes, piso, agua, saneamiento, electricidad) + bienes durables.

  Orientación del PC1: valores altos = más pobre (verificar con POBREZA==1).
  Umbral: promedio entre max(POBREZA=2) y min(POBREZA=1) sobre adultos ≥65.

  Variables a evitar en el PCA:
    - INGRESO_PC y POBREZA: endógenas al tratamiento (la transferencia las altera)
    - TIENE_BILLETERA: es la variable de resultado, no puede ser input del índice
    - NIVEL_EDUCATIVO: puede usarse como covariable externa pero no en el índice
""")

    # ── Guardar outputs ────────────────────────────────────────────────────────
    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[Output] Reporte guardado en: {REPORT_TXT}")

    df_results = pd.DataFrame(results)
    df_results.to_csv(REPORT_CSV, index=False, encoding="utf-8")
    print(f"[Output] Tabla CSV guardada en: {REPORT_CSV}")


if __name__ == "__main__":
    main()
