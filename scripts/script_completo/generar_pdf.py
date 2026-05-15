"""
generar_pdf.py — Genera explicacion_codigo.pdf con el resumen del pipeline script.py
"""

import subprocess
import sys

def ensure_pkg(pkg, import_name=None):
    name = import_name or pkg
    try:
        __import__(name)
        return True
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])
        return True

ensure_pkg("reportlab")

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PDF  = SCRIPT_DIR / "explicacion_codigo.pdf"

# ── Estilos ────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

AZUL_OSCURO  = colors.HexColor("#1a3a5c")
AZUL_MEDIO   = colors.HexColor("#2166ac")
AZUL_CLARO   = colors.HexColor("#d6e8f7")
GRIS_LINEA   = colors.HexColor("#cccccc")
VERDE        = colors.HexColor("#276221")
ROJO         = colors.HexColor("#8b1a1a")

titulo_style = ParagraphStyle(
    "Titulo", parent=styles["Title"],
    fontSize=22, textColor=AZUL_OSCURO,
    spaceAfter=6, alignment=TA_CENTER, leading=28,
)
subtitulo_style = ParagraphStyle(
    "Subtitulo", parent=styles["Normal"],
    fontSize=12, textColor=AZUL_MEDIO,
    spaceAfter=14, alignment=TA_CENTER, italic=True,
)
h1_style = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=14, textColor=AZUL_OSCURO,
    spaceBefore=18, spaceAfter=6,
    borderPad=4, leading=18,
)
h2_style = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=12, textColor=AZUL_MEDIO,
    spaceBefore=12, spaceAfter=4, leading=16,
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=10, leading=15, spaceAfter=6,
    alignment=TA_JUSTIFY,
)
code_style = ParagraphStyle(
    "Code", parent=styles["Code"],
    fontSize=8.5, leading=13,
    backColor=colors.HexColor("#f5f5f5"),
    leftIndent=12, rightIndent=12,
    borderPad=6, spaceAfter=8,
    fontName="Courier",
)
bullet_style = ParagraphStyle(
    "Bullet", parent=body_style,
    leftIndent=16, spaceAfter=4,
)
note_style = ParagraphStyle(
    "Note", parent=body_style,
    fontSize=9, textColor=colors.HexColor("#555555"),
    leftIndent=12, italic=True,
)

def H1(text):
    return [
        Paragraph(text, h1_style),
        HRFlowable(width="100%", thickness=1.5, color=AZUL_OSCURO, spaceAfter=6),
    ]

def H2(text):
    return [Paragraph(text, h2_style)]

def P(text):
    return Paragraph(text, body_style)

def Code(text):
    return Paragraph(text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style)

def Bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(i, bullet_style), leftIndent=20, bulletColor=AZUL_MEDIO)
         for i in items],
        bulletType="bullet", bulletFontName="Symbol",
        leftIndent=16, spaceBefore=2, spaceAfter=6,
    )

def spacer(h=0.3):
    return Spacer(1, h * cm)

# ── Tabla de fases ─────────────────────────────────────────────────────────
def tabla_fases():
    data = [
        [Paragraph("<b>Fase</b>", body_style),
         Paragraph("<b>Nombre</b>", body_style),
         Paragraph("<b>Función principal</b>", body_style),
         Paragraph("<b>Output clave</b>", body_style)],
        ["0", "Descarga INEI",       "phase_0_download_from_inei()", "6 CSVs en data/clean/_raw_extracted/"],
        ["1", "Preprocesamiento",    "phase_1_preprocess()",         "enaho_2024_clean.csv"],
        ["2", "Limpieza RDD",        "phase_2_clean()",              "clean_data.csv"],
        ["3", "Estimación principal","phase_3_main()",               "main_results.csv"],
        ["4", "Robustez",            "phase_4_robustness()",         "robustness_results.csv"],
        ["5", "Tablas y figuras",    "phase_5_output()",             "4 tablas .tex + 3 figuras .png/.pdf"],
    ]
    col_widths = [1.0*cm, 3.5*cm, 5.5*cm, 6.8*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  AZUL_OSCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0),  9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, AZUL_CLARO]),
        ("FONTSIZE",     (0,1), (-1,-1), 8.5),
        ("GRID",         (0,0), (-1,-1), 0.4, GRIS_LINEA),
        ("ALIGN",        (0,0), (0,-1),  "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
    ]))
    return t

# ── Tabla de archivos de salida ────────────────────────────────────────────
def tabla_outputs():
    data = [
        [Paragraph("<b>Archivo</b>", body_style),
         Paragraph("<b>Descripción</b>", body_style)],
        ["data/clean/enaho_2024_clean.csv",            "Dataset ENAHO 2024 fusionado a nivel de persona"],
        ["data/clean/clean_data.csv",                  "Muestra RDD filtrada con running variable centrada"],
        ["data/clean/main_results.csv",                "Estimaciones RDD principales (todas las especificaciones)"],
        ["data/clean/robustness_results.csv",          "Resultados de todas las pruebas de robustez"],
        ["paper/tables/table_1_summary.tex",           "Estadísticas descriptivas tratados vs. control"],
        ["paper/tables/table_2_main_results.tex",      "Tabla principal de resultados RDD"],
        ["paper/tables/table_3_robustness.tex",        "Sensibilidad de ancho de banda, donut, polinomios, placebos"],
        ["paper/tables/table_4_covariate_balance.tex", "Balance de covariables en el ancho de banda"],
        ["paper/figures/figure_mccrary_density.{png,pdf}", "Densidad de la variable de corrida (test de McCrary)"],
        ["paper/figures/figure_1_rdplot.{png,pdf}",    "Gráfico RDD principal (billetera vs. edad centrada)"],
        ["paper/figures/figure_2_bandwidth_sensitivity.{png,pdf}", "Sensibilidad de estimados al ancho de banda"],
    ]
    col_widths = [7.5*cm, 9.3*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  AZUL_OSCURO),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, AZUL_CLARO]),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.4, GRIS_LINEA),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("FONTNAME",      (0,1), (0,-1),  "Courier"),
    ]))
    return t

# ── Variables clave ────────────────────────────────────────────────────────
def tabla_variables():
    data = [
        [Paragraph("<b>Variable</b>", body_style),
         Paragraph("<b>Tipo</b>", body_style),
         Paragraph("<b>Descripción</b>", body_style)],
        ["EDAD (running var)",    "Continua", "Edad del individuo; centrada en 65 → running_centered"],
        ["TIENE_BILLETERA",       "Binaria",  "1 = posee billetera digital (ENAHO P558E1_9)"],
        ["USA_BILLETERA",         "Binaria",  "1 = usó billetera en alguna transacción (P558H*_7)"],
        ["treat",                 "Binaria",  "1 si running_centered ≥ 0 (i.e., edad ≥ 65)"],
        ["INTERNET_HOGAR",        "Binaria",  "Acceso a internet en el hogar (covariate / placebo)"],
        ["SMARTPHONE",            "Binaria",  "Hogar tiene smartphone (covariate / placebo)"],
        ["POBREZA",               "Categórica","Condición de pobreza SISFOH (1=extrema, 2=no extrema, 3=no pobre)"],
        ["INGRESO_PC",            "Continua", "Ingreso per cápita del hogar (sumaria)"],
        ["NIVEL_EDUCATIVO",       "Ordinal",  "Máximo nivel educativo alcanzado"],
        ["DPTO",                  "Cluster",  "Código de departamento — usado para SE clusterizados"],
        ["FACTOR_EXPANSION",      "Peso",     "Factor de expansión poblacional ENAHO (FACPOB07)"],
    ]
    col_widths = [4.2*cm, 2.4*cm, 10.2*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  AZUL_OSCURO),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, AZUL_CLARO]),
        ("FONTSIZE",      (0,1), (-1,-1), 8.5),
        ("GRID",          (0,0), (-1,-1), 0.4, GRIS_LINEA),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("FONTNAME",      (0,1), (0,-1),  "Courier"),
    ]))
    return t

# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL DOCUMENTO
# ══════════════════════════════════════════════════════════════════════════════
doc = SimpleDocTemplate(
    str(OUTPUT_PDF),
    pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2.2*cm, bottomMargin=2.2*cm,
    title="Explicación del Script — Pensión 65 RDD",
    author="Pipeline de análisis Pensión 65",
)

story = []

# ── Portada ────────────────────────────────────────────────────────────────
story += [
    spacer(1.5),
    Paragraph("Explicación del Código", titulo_style),
    Paragraph("Pipeline de Análisis RDD — Adopción de Billetera Digital (Pensión 65)", subtitulo_style),
    Paragraph("<font color='#888888'>script.py · scripts/script_completo/</font>", subtitulo_style),
    HRFlowable(width="100%", thickness=2, color=AZUL_OSCURO, spaceAfter=18),
    spacer(0.5),
]

# ── 1. Descripción general ─────────────────────────────────────────────────
story += H1("1. Descripción general")
story += [
    P("El archivo <b>script.py</b> implementa un <b>pipeline econométrico completo de extremo a extremo</b> "
      "para estimar el efecto causal de la afiliación a Pensión 65 sobre la adopción de billeteras "
      "digitales en Perú, utilizando un diseño de <b>Regresión Discontinua (RDD)</b> basado en el "
      "umbral de elegibilidad de 65 años."),
    P("El script está diseñado para ser <b>portable y autosuficiente</b>: cualquier persona que clone "
      "el repositorio puede ejecutarlo con un solo comando (<font face='Courier'>python scripts/script_completo/script.py</font>) "
      "sin necesidad de preparar datos manualmente. Descarga los microdatos directamente desde el INEI, "
      "los procesa y produce todos los outputs del paper (tablas LaTeX y figuras)."),
    spacer(0.2),
]

# ── 2. Estructura del pipeline ─────────────────────────────────────────────
story += H1("2. Estructura del pipeline (6 fases)")
story += [
    P("El pipeline se organiza en seis fases secuenciales, cada una encapsulada en su propia función:"),
    spacer(0.2),
    tabla_fases(),
    spacer(0.4),
]

# ── 3. Configuración global ────────────────────────────────────────────────
story += H1("3. Configuración global y rutas")
story += [
    P("Al inicio del script se definen todas las <b>rutas de forma relativa a la ubicación del propio archivo</b>, "
      "lo que garantiza portabilidad entre sistemas operativos:"),
    Bullets([
        "<b>REPO_ROOT</b>: raíz del repositorio (dos niveles arriba de script.py).",
        "<b>DATA_DIR</b>: <font face='Courier'>data/clean/</font> — almacena todos los CSV intermedios y finales.",
        "<b>RAW_EXTRACTED_DIR</b>: <font face='Courier'>data/clean/_raw_extracted/</font> — CSVs crudos descargados de INEI.",
        "<b>TABLES_DIR / FIGURES_DIR</b>: <font face='Courier'>paper/tables/</font> y <font face='Courier'>paper/figures/</font> — outputs del paper.",
        "<b>RANDOM_SEED = 42</b>: semilla para reproducibilidad en permutaciones y simulaciones.",
    ]),
    spacer(0.2),
]

# ── 4. Gestión de dependencias ─────────────────────────────────────────────
story += H1("4. Gestión automática de dependencias")
story += [
    P("La función <b><font face='Courier'>install_dependencies()</font></b> y el auxiliar "
      "<b><font face='Courier'>ensure_package()</font></b> verifican e instalan automáticamente "
      "los paquetes necesarios mediante <font face='Courier'>pip</font> antes de importarlos:"),
    Bullets([
        "<b>Obligatorias</b> (abortan si no se pueden instalar): <font face='Courier'>pandas, numpy, matplotlib, statsmodels</font>.",
        "<b>Opcionales con fallback</b>: <font face='Courier'>rdrobust, rddensity, linearmodels</font>. "
        "Si <font face='Courier'>rdrobust</font> no está disponible, el estimador RDD cae automáticamente "
        "a una regresión WLS local con pesos triangulares via <font face='Courier'>statsmodels</font>.",
    ]),
    spacer(0.2),
]

# ── 5. Fase 0 ─────────────────────────────────────────────────────────────
story += H1("5. Fase 0 — Descarga de microdatos ENAHO 2024")
story += [
    P("La función <b><font face='Courier'>phase_0_download_from_inei()</font></b> descarga los "
      "<b>6 módulos de la Encuesta ENAHO 2024</b> (código 966) directamente desde el servidor del INEI "
      "sin depender de archivos locales preexistentes. El proceso es:"),
    Bullets([
        "Construye la URL de cada módulo siguiendo el patrón: "
        "<font face='Courier'>https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV/966-ModuloXX.zip</font>.",
        "Descarga el ZIP en memoria (sin guardarlo en disco).",
        "Extrae únicamente el CSV objetivo dentro del ZIP y lo escribe en <font face='Courier'>_raw_extracted/</font>.",
        "Los 6 módulos descargados suman aproximadamente <b>511 MB</b> de CSVs.",
    ]),
    P("Los seis módulos descargados son:"),
    Bullets([
        "<b>Módulo 01</b> (Vivienda) — <font face='Courier'>Enaho01-2024-100.csv</font>: variables de vivienda e internet.",
        "<b>Módulo 02</b> (Miembros del hogar) — <font face='Courier'>Enaho01-2024-200.csv</font>: demografía, edad, sexo.",
        "<b>Módulo 03</b> (Educación) — <font face='Courier'>Enaho01A-2024-300.csv</font>: nivel educativo.",
        "<b>Módulo 05</b> (Empleo + Billetera) — <font face='Courier'>Enaho01a-2024-500.csv</font>: variables de outcome principal.",
        "<b>Módulo 18</b> (Equipamiento) — <font face='Courier'>Enaho01-2024-612.csv</font>: tenencia de smartphone.",
        "<b>Sumaria</b> — <font face='Courier'>Sumaria-2024.csv</font>: ingreso y gasto per cápita del hogar.",
    ]),
    spacer(0.2),
]

# ── 6. Fase 1 ─────────────────────────────────────────────────────────────
story += H1("6. Fase 1 — Preprocesamiento ENAHO 2024")
story += [
    P("La función <b><font face='Courier'>phase_1_preprocess()</font></b> fusiona los 6 módulos "
      "a nivel de <b>persona</b> y construye las variables analíticas:"),
    Bullets([
        "<b>Variables de billetera digital</b> (del módulo 05): "
        "<font face='Courier'>TIENE_BILLETERA</font> (ítem P558E1_9 = 9) y "
        "<font face='Courier'>USA_BILLETERA</font> (cualquier P558H*_7 = 7). "
        "También construye versiones alternativas con códigos 6 y 10 para robustez.",
        "<b>Variables de formalidad laboral</b>: <font face='Courier'>BANCO_PREVIO, FORMAL, OCUPADO</font>.",
        "<b>Demografía</b> (módulo 02): género, edad (<font face='Courier'>EDAD</font>), factor de expansión.",
        "<b>Educación</b> (módulo 03): nivel educativo máximo.",
        "<b>Smartphone</b> (módulo 18 en formato long → wide): indicador de tenencia.",
        "<b>Internet en hogar</b> (módulo 01): variable binaria.",
        "<b>Ingreso per cápita</b> (sumaria): INGHOG2D / MIEPERHO.",
    ]),
    P("El merge final es por llaves <font face='Courier'>CONGLOME, VIVIENDA, HOGAR, CODPERSO</font> "
      "a nivel persona, y por <font face='Courier'>CONGLOME, VIVIENDA, HOGAR</font> a nivel hogar. "
      "El output es <b><font face='Courier'>enaho_2024_clean.csv</font></b>."),
    spacer(0.2),
]

# ── 7. Fase 2 ─────────────────────────────────────────────────────────────
story += H1("7. Fase 2 — Limpieza y construcción de la muestra RDD")
story += [
    P("La función <b><font face='Courier'>phase_2_clean()</font></b> prepara el dataset para la "
      "estimación RDD:"),
    Bullets([
        "Elimina observaciones con <font face='Courier'>EDAD</font> missing.",
        "<b>Centra la variable de corrida</b>: <font face='Courier'>running_centered = EDAD − 65</font>. "
        "Valores negativos corresponden a personas menores de 65 (control); positivos a mayores (tratados).",
        "Crea la variable de <b>tratamiento</b>: <font face='Courier'>treat = 1 si running_centered ≥ 0</font>.",
        "Reporta estadísticas de missingness, correlaciones y medias por grupo.",
    ]),
    P("El output es <b><font face='Courier'>clean_data.csv</font></b>, que es el input de todas las fases siguientes."),
    spacer(0.2),
]

# ── 8. Fase 3 ─────────────────────────────────────────────────────────────
story += H1("8. Fase 3 — Estimación RDD principal")
story += [
    P("La función <b><font face='Courier'>phase_3_main()</font></b> estima el efecto causal de "
      "cruzar el umbral de 65 años sobre la adopción de billetera digital. "
      "El flujo de estimación está implementado en la función <b><font face='Courier'>run_rdd()</font></b> "
      "con doble fallback:"),
    Bullets([
        "<b>Estimador primario</b> — <font face='Courier'>rdrobust</font> (Calonico, Cattaneo & Titiunik): "
        "regresión local con kernel triangular, ancho de banda MSE-óptimo, "
        "errores estándar robustos bias-corrected clusterizados por departamento.",
        "<b>Estimador de respaldo</b> — WLS local vía <font face='Courier'>statsmodels</font> "
        "con pesos triangulares y errores HC2, si rdrobust falla.",
    ]),
    P("Se estiman <b>tres especificaciones</b> para cada outcome:"),
    Bullets([
        "<b>baseline</b>: sin covariables.",
        "<b>with_covariates</b>: con internet + smartphone.",
        "<b>extended_covariates</b>: con internet, smartphone, pobreza, ingreso_pc, educación.",
    ]),
    P("Adicionalmente se calculan tamaños de efecto (Cohen's d, % de cambio respecto a la media) "
      "y análisis de <b>heterogeneidad por subgrupos</b> (pobreza, acceso a internet, smartphone)."),
    spacer(0.2),
]

# ── 9. Fase 4 ─────────────────────────────────────────────────────────────
story += H1("9. Fase 4 — Pruebas de robustez")
story += [
    P("La función <b><font face='Courier'>phase_4_robustness()</font></b> implementa una batería "
      "exhaustiva de verificaciones que son estándar en la literatura RDD:"),
]

rob_data = [
    [Paragraph("<b>#</b>", body_style),
     Paragraph("<b>Prueba</b>", body_style),
     Paragraph("<b>Descripción</b>", body_style)],
    ["1", "McCrary / rddensity",
     "Detecta manipulación en la variable de corrida. Un p-valor pequeño sugeriría selección en torno al umbral."],
    ["2", "Outcomes placebo",
     "Estima el RDD usando covariables pre-tratamiento (internet, smartphone) como outcome. No debe haber efectos."],
    ["3", "Sensibilidad al BW",
     "Repite la estimación con h×0.5 (medio BW), h×1.0 (óptimo) y h×2.0 (doble BW)."],
    ["4", "Donut-hole",
     "Excluye observaciones con |running_centered| ≤ 0.5 / 1.0 / 2.0 años para descartar manipulación local."],
    ["4b", "Heterogeneidad SISFOH",
     "Separa la muestra por condición de pobreza (extrema, no extrema, no pobre) y re-estima el RDD."],
    ["5", "Balance de covariables",
     "Estima el RDD con cada covariable como outcome dentro del BW óptimo. Ninguna debería ser significativa."],
    ["6", "Orden del polinomio",
     "Compara estimaciones con polinomio local de grado 1 (lineal) y grado 2 (cuadrático)."],
    ["7", "Placebo de umbral",
     "Aplica el estimador en percentiles 25 y 75 de la distribución de x. No debe haber efectos."],
    ["8", "Inferencia por permutación",
     "500 corridas con umbrales aleatorios para obtener una distribución nula del estadístico t."],
    ["9", "Corrección FDR (BH)",
     "Ajusta los p-valores de pruebas múltiples usando el método Benjamini-Hochberg."],
]
col_widths_rob = [0.7*cm, 4.3*cm, 11.8*cm]
t_rob = Table(rob_data, colWidths=col_widths_rob, repeatRows=1)
t_rob.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  AZUL_OSCURO),
    ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
    ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
    ("FONTSIZE",      (0,0), (-1,0),  9),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, AZUL_CLARO]),
    ("FONTSIZE",      (0,1), (-1,-1), 8.5),
    ("GRID",          (0,0), (-1,-1), 0.4, GRIS_LINEA),
    ("ALIGN",         (0,0), (0,-1),  "CENTER"),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING",    (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
]))
story += [t_rob, spacer(0.4)]

# ── 10. Fase 5 ────────────────────────────────────────────────────────────
story += H1("10. Fase 5 — Generación de tablas y figuras")
story += [
    P("La función <b><font face='Courier'>phase_5_output()</font></b> lee los CSV intermedios y "
      "produce todos los outputs del paper:"),
]
story += H2("Tablas LaTeX")
story += [
    Bullets([
        "<b>Table 1 (summary)</b>: estadísticas descriptivas (media, SD, N) de outcomes y covariables "
        "separadas por tratados vs. control, incluyendo nota con tamaños de muestra dentro del BW.",
        "<b>Table 2 (main results)</b>: estimaciones RDD por especificación y outcome, con SE, IC 95% "
        "y panel de heterogeneidad por SISFOH.",
        "<b>Table 3 (robustness)</b>: paneles de sensibilidad al BW, donut-hole, polinomios y placebos.",
        "<b>Table 4 (covariate balance)</b>: estimaciones RDD con covariables como outcome; "
        "asterisco (*) si el IC excluye cero.",
    ]),
    P("Todas las tablas usan el entorno <font face='Courier'>threeparttable</font> y pasan por "
      "una función de validación que reemplaza <font face='Courier'>nan/NaN/None</font> y celdas "
      "vacías por '---' automáticamente."),
    spacer(0.1),
]
story += H2("Figuras")
story += [
    Bullets([
        "<b>Figure McCrary</b>: histograma de densidad de la running variable a ambos lados del umbral.",
        "<b>Figure 1 (RD plot)</b>: dispersión binada + regresión local a cada lado del corte, "
        "restringida a ±h×2.5 años alrededor de los 65.",
        "<b>Figure 2 (BW sensitivity)</b>: gráfico de puntos con IC para las tres especificaciones "
        "de ancho de banda.",
    ]),
    P("Todas las figuras se guardan en PNG (150 dpi) y PDF (300 dpi) para uso directo en LaTeX."),
    spacer(0.2),
]

# ── 11. Variables clave ───────────────────────────────────────────────────
story += H1("11. Variables clave del análisis")
story += [
    tabla_variables(),
    spacer(0.4),
]

# ── 12. Outputs ───────────────────────────────────────────────────────────
story += H1("12. Archivos de salida")
story += [
    tabla_outputs(),
    spacer(0.4),
]

# ── 13. Cómo ejecutar ─────────────────────────────────────────────────────
story += H1("13. Cómo ejecutar el pipeline")
story += [
    P("Requisitos previos:"),
    Bullets([
        "Python 3.9 o superior.",
        "Conexión a internet (descarga ~38 MB de ZIPs → ~511 MB de CSVs en disco).",
        "Los paquetes se instalan automáticamente si faltan.",
    ]),
    P("Comando de ejecución desde la raíz del repositorio:"),
    Code("python scripts/script_completo/script.py"),
    P("El pipeline completo puede tardar <b>entre 10 y 40 minutos</b> dependiendo de la velocidad "
      "de internet y el hardware. Al finalizar imprime la ruta de todos los outputs generados."),
    spacer(0.2),
]

# ── 14. Notas de diseño ───────────────────────────────────────────────────
story += H1("14. Notas de diseño y decisiones técnicas")
story += [
    Bullets([
        "<b>Portabilidad</b>: todas las rutas son relativas a <font face='Courier'>__file__</font>; "
        "no hay rutas absolutas hard-coded.",
        "<b>Fallback automático</b>: si <font face='Courier'>rdrobust</font> no está disponible "
        "o falla, el script continúa con WLS statsmodels sin interrumpir el pipeline.",
        "<b>Reproducibilidad</b>: <font face='Courier'>np.random.seed(42)</font> y "
        "<font face='Courier'>np.random.default_rng(42)</font> en todas las rutinas estocásticas.",
        "<b>Detección robusta de columnas</b>: cada fase verifica si las columnas existen antes "
        "de operar sobre ellas, evitando errores si la estructura de ENAHO cambia.",
        "<b>Validación de tablas</b>: la función <font face='Courier'>_validate_table()</font> "
        "sanea automáticamente cualquier valor NaN o celda vacía antes de escribir el .tex.",
        "<b>Figuras no-interactivas</b>: se usa <font face='Courier'>matplotlib.use('Agg')</font> "
        "para evitar que se abra una ventana gráfica en entornos sin display.",
    ]),
    spacer(0.3),
]

# ── Pie de página informativo ──────────────────────────────────────────────
story += [
    HRFlowable(width="100%", thickness=1, color=GRIS_LINEA, spaceAfter=8),
    Paragraph(
        "<font color='#888888'>Documento generado automáticamente a partir de "
        "scripts/script_completo/script.py · Proyecto Pensión 65 — RDD Billetera Digital</font>",
        note_style
    ),
]

# ── Build ──────────────────────────────────────────────────────────────────
doc.build(story)
print(f"\nPDF generado exitosamente: {OUTPUT_PDF}")
