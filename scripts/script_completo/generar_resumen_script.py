"""Genera un PDF con resumen simple de lo que hace script.py."""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "..", "paper", "resumen_script.pdf")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

AZUL        = colors.HexColor("#1a4f8a")
AZUL_C      = colors.HexColor("#dce8f5")
VERDE       = colors.HexColor("#1a7a4a")
VERDE_C     = colors.HexColor("#d4edda")
NARANJA     = colors.HexColor("#c05c00")
NARANJA_C   = colors.HexColor("#fde8d0")
GRIS        = colors.HexColor("#f4f4f4")
GRIS_M      = colors.HexColor("#cccccc")

doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2.0*cm, bottomMargin=2.0*cm)
styles = getSampleStyleSheet()

def S(name, parent="Normal", **kw):
    return ParagraphStyle(name, parent=styles[parent], **kw)

TITULO = S("T", fontSize=19, textColor=AZUL, alignment=TA_CENTER,
           fontName="Helvetica-Bold", spaceAfter=3, leading=24)
SUBTIT = S("Sub", fontSize=11, textColor=colors.HexColor("#444"),
           alignment=TA_CENTER, spaceAfter=10, leading=15)
H1     = S("H1", fontSize=13, textColor=AZUL, fontName="Helvetica-Bold",
           spaceBefore=12, spaceAfter=4)
H2     = S("H2", fontSize=10.5, textColor=VERDE, fontName="Helvetica-Bold",
           spaceBefore=7, spaceAfter=3)
NORM   = S("N",  fontSize=9.5, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
BULL   = S("B",  fontSize=9.5, leading=14, spaceAfter=3, leftIndent=14)
MONO   = S("M",  fontSize=8.5, fontName="Courier", textColor=colors.HexColor("#333"),
           leading=13, spaceAfter=2, leftIndent=10)
PIE    = S("P",  fontSize=7.5, textColor=colors.HexColor("#888"), alignment=TA_CENTER)

story = []

# ── Portada ────────────────────────────────────────────────────────────────
story.append(Spacer(1, 1*cm))
story.append(Paragraph("script.py — ¿Qué hace este código?", TITULO))
story.append(Paragraph(
    "Resumen en lenguaje simple del pipeline completo de análisis estadístico",
    SUBTIT))
story.append(HRFlowable(width="100%", thickness=2, color=AZUL))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "El archivo <b>script.py</b> es un programa en Python que descarga datos del "
    "gobierno peruano, los procesa, aplica técnicas estadísticas avanzadas, y genera "
    "automáticamente las tablas y figuras de un paper académico. Todo en un solo "
    "archivo que cualquiera puede ejecutar. A continuación se explica cada parte.",
    NORM))

# ── Sección 1 ──────────────────────────────────────────────────────────────
story.append(Paragraph("1. ¿Cuál es el objetivo general?", H1))
story.append(Paragraph(
    "El script investiga si recibir <b>Pensión 65</b> — el programa del Estado que "
    "paga S/250 cada dos meses a adultos mayores en extrema pobreza — hace que esas "
    "personas adopten <b>billeteras digitales</b> (Yape, Plin, Cuenta DNI). "
    "Para eso usa datos de la Encuesta ENAHO 2024 del INEI y aplica un método "
    "estadístico llamado <i>Regresión Discontinua</i> que aprovecha el corte de "
    "edad en 65 años como experimento natural.",
    NORM))

# ── Sección 2 — Fases ──────────────────────────────────────────────────────
story.append(Paragraph("2. Las 5 fases del pipeline", H1))

fases = [
    ["Fase", "Nombre", "¿Qué hace?", "Output principal"],
    ["0", "Descarga",
     "Baja automáticamente 6 archivos de datos del INEI (~511 MB). "
     "Son los módulos de la encuesta ENAHO 2024.",
     "6 archivos CSV en data/clean/_raw_extracted/"],
    ["1", "Preprocesamiento",
     "Une los 6 módulos en una sola tabla por persona (117,721 personas). "
     "Construye las variables clave: billetera digital, hacinamiento, "
     "refrigerador, TV, área urbano/rural.",
     "enaho_2024_clean.csv (17 MB)"],
    ["2", "Limpieza RDD",
     "Centra la variable de edad en el corte de 65 años. Crea dos "
     "muestras: df_full (todos) y df_main (solo pobres extremos, N=6,717).",
     "enaho_rdd_full.csv\nenaho_rdd_main.csv"],
    ["3", "Estimación\nprincipal",
     "Corre el RDD principal (4 especificaciones) + BLOQUE F (RDD2 con "
     "índice SISFOH como variable de corte). Calcula la dilución ITT→LATE.",
     "main_results.csv\nrdd2_results.csv"],
    ["4", "Robustez",
     "Verifica que el resultado sea robusto: cambia el ancho de ventana, "
     "excluye datos cerca del corte (donut), prueba otros cortes de edad, "
     "corre 500 permutaciones aleatorias.",
     "robustness_results.csv"],
    ["5", "Tablas\ny figuras",
     "Genera automáticamente todas las tablas en formato LaTeX y las "
     "figuras en PNG/PDF listas para el paper.",
     "8 tablas .tex\n4 figuras .png/.pdf"],
]

tf = Table(fases, colWidths=[1.0*cm, 2.2*cm, 8.5*cm, 4.8*cm])
tf.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_C]),
    ("GRID", (0,0), (-1,-1), 0.4, GRIS_M),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,0), 9),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTSIZE", (0,1), (-1,-1), 8.5),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("ALIGN", (0,0), (1,-1), "CENTER"),
]))
story.append(tf)

# ── Sección 3 — Variables ──────────────────────────────────────────────────
story.append(Paragraph("3. Variables principales que construye el script", H1))

vars_tbl = [
    [Paragraph("<b>Variable</b>", S("vh", fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")),
     Paragraph("<b>¿Qué mide?</b>", S("vh2", fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")),
     Paragraph("<b>Fuente ENAHO</b>", S("vh3", fontSize=9, textColor=colors.white, fontName="Helvetica-Bold"))],
    [Paragraph("TIENE_BILLETERA", MONO),
     Paragraph("1 si tiene O usa billetera digital (Yape, Plin, Cuenta DNI)", S("cv", fontSize=9, leading=13)),
     Paragraph("Módulo 05 P558E1 y P558H", S("cv2", fontSize=9, leading=13))],
    [Paragraph("USA_BILLETERA", MONO),
     Paragraph("1 si usó billetera como medio de pago en alguna compra", S("cv", fontSize=9, leading=13)),
     Paragraph("Módulo 05 P558H", S("cv2", fontSize=9, leading=13))],
    [Paragraph("running_centered", MONO),
     Paragraph("Edad de la persona menos 65 (cero = exactamente en el corte)", S("cv", fontSize=9, leading=13)),
     Paragraph("Módulo 02 P208A", S("cv2", fontSize=9, leading=13))],
    [Paragraph("POBREZA", MONO),
     Paragraph("Clasificación SISFOH: 1=extrema pobreza, 2=no extrema, 3=no pobre", S("cv", fontSize=9, leading=13)),
     Paragraph("Sumaria", S("cv2", fontSize=9, leading=13))],
    [Paragraph("SISFOH_PROXY", MONO),
     Paragraph("Índice construido con PCA sobre 8 variables del hogar. Más alto = más pobre.", S("cv", fontSize=9, leading=13)),
     Paragraph("Módulos 01, 18, Sumaria", S("cv2", fontSize=9, leading=13))],
    [Paragraph("AREA", MONO),
     Paragraph("1=urbano, 2=rural (derivado de DOMINIO)", S("cv", fontSize=9, leading=13)),
     Paragraph("Módulo 01 DOMINIO", S("cv2", fontSize=9, leading=13))],
    [Paragraph("HACINAMIENTO", MONO),
     Paragraph("Personas del hogar dividido entre número de cuartos", S("cv", fontSize=9, leading=13)),
     Paragraph("Módulos 01+02", S("cv2", fontSize=9, leading=13))],
]

tv = Table(vars_tbl, colWidths=[3.5*cm, 8.5*cm, 4.5*cm])
tv.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), VERDE),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, VERDE_C]),
    ("GRID", (0,0), (-1,-1), 0.4, GRIS_M),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
]))
story.append(tv)

# ── Sección 4 — Los dos RDD ────────────────────────────────────────────────
story.append(Paragraph("4. Los dos diseños estadísticos (RDD1 y RDD2)", H1))

story.append(Paragraph("RDD1 — Corte de edad en 65 años (diseño principal)", H2))
story.append(Paragraph(
    "Compara personas que están justo antes de cumplir 65 años con las que acaban de "
    "cumplirlos, <b>dentro de la muestra de pobres extremos</b>. La idea es que "
    "el único cambio relevante al cruzar esa edad es volverse elegible para Pensión 65. "
    "Si hay un salto en el uso de billeteras justo en los 65, eso se atribuye al programa.",
    NORM))

rdd1_data = [
    ["Muestra", "Solo POBREZA=1 (N=6,717)"],
    ["Variable de corte (running variable)", "Edad centrada en 65 años"],
    ["Ventana óptima (bandwidth)", "±13.95 años"],
    ["N efectivo dentro de ventana", "1,144 personas"],
    ["Resultado principal", "+2.7 pp (SE=2.2 pp) — positivo, no significativo"],
    ["Prueba de aleatoriedad (p-value)", "0.60 — no se rechaza la hipótesis nula"],
    ["Problema principal", "Solo el 5% de personas cerca del corte son elegibles"],
]
t1 = Table(rdd1_data, colWidths=[6*cm, 10.5*cm])
t1.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,-1), AZUL_C),
    ("GRID", (0,0), (-1,-1), 0.4, GRIS_M),
    ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(t1)
story.append(Spacer(1, 0.25*cm))

story.append(Paragraph("RDD2 — Índice de bienestar SISFOH como corte (BLOQUE F)", H2))
story.append(Paragraph(
    "En lugar de usar la edad como variable de corte, construye un <b>índice de "
    "pobreza</b> con técnicas de reducción de dimensiones (PCA) a partir de "
    "características del hogar (paredes, piso, agua, smartphone, refrigerador, TV, "
    "ingreso, hacinamiento). El corte se define donde el índice separa a los "
    "clasificados como pobres extremos de los que no lo son. Diseño basado en "
    "Bando, Galiani y Gertler (2020).",
    NORM))

rdd2_data = [
    ["Muestra", "Todos los adultos ≥65 años (N=14,088)"],
    ["Variable de corte", "Índice PCA de bienestar (SISFOH_PROXY)"],
    ["Varianza explicada por PC1", "32.2%"],
    ["Ventana óptima (bandwidth)", "0.765 unidades del índice"],
    ["N efectivo dentro de ventana", "3,201 personas (~2.8× más que RDD1)"],
    ["Resultado principal", "+0.4 pp (SE=1.5 pp) — prácticamente cero"],
    ["Balance de covariables", "Todos balanceados (CIs incluyen cero) ✓"],
    ["Ventaja vs. RDD1", "Más poder estadístico y mejor balance de covariables"],
]
t2 = Table(rdd2_data, colWidths=[6*cm, 10.5*cm])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,-1), VERDE_C),
    ("GRID", (0,0), (-1,-1), 0.4, GRIS_M),
    ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(t2)

# ── Sección 5 — Robustez ───────────────────────────────────────────────────
story.append(Paragraph("5. Pruebas de robustez que corre el script", H1))

robust_items = [
    ("Sensibilidad al bandwidth", "Repite el análisis con ventanas de ±7 años y ±28 años. "
     "El resultado positivo se mantiene en todos los casos."),
    ("Donut hole", "Excluye a las personas con exactamente 65, 64 o 63 años para "
     "asegurarse de que el resultado no depende de quienes están justo en el corte."),
    ("Orden del polinomio", "Prueba ajuste cuadrático en vez de lineal. "
     "El resultado es muy similar."),
    ("Cortes placebo", "Repite el análisis en edades donde NO debería haber efecto "
     "(ej. 46 años, 10 años antes del corte real). Si aparece un 'efecto' ahí, "
     "el diseño estaría capturando algo diferente al programa."),
    ("Permutaciones aleatorias (500)", "Asigna el corte al azar 500 veces y compara "
     "con el efecto real. El p-value resultante es 0.60 (no significativo)."),
    ("Balance de covariables", "Verifica que variables como internet o smartphone "
     "no cambien de golpe en los 65 años. Si cambian, algo más está pasando. "
     "Hallazgo: internet sí cambia en el RDD1 (limitación del diseño)."),
    ("Corrección por múltiples pruebas (BH)", "Ajusta los p-values para tener en "
     "cuenta que se están probando muchas hipótesis a la vez."),
]

for nombre, desc in robust_items:
    story.append(Paragraph(f"<b>• {nombre}:</b> {desc}", BULL))

# ── Sección 6 — Outputs ────────────────────────────────────────────────────
story.append(Paragraph("6. Archivos que genera el script", H1))

out_data = [
    [Paragraph("<b>Archivo</b>", S("oh", fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")),
     Paragraph("<b>¿Para qué sirve?</b>", S("oh2", fontSize=9, textColor=colors.white, fontName="Helvetica-Bold"))],
    [Paragraph("main_results.csv", MONO), Paragraph("Resultados de todos los RDD principales (9 filas)", S("oc", fontSize=9, leading=13))],
    [Paragraph("rdd2_results.csv", MONO), Paragraph("Resultados del BLOQUE F (RDD2 con índice SISFOH)", S("oc", fontSize=9, leading=13))],
    [Paragraph("robustness_results.csv", MONO), Paragraph("20 pruebas de robustez con sus estadísticos", S("oc", fontSize=9, leading=13))],
    [Paragraph("dilution_calc.json", MONO), Paragraph("Cálculo de dilución ITT→LATE (frac_ep=5%, τ_LATE=0.719)", S("oc", fontSize=9, leading=13))],
    [Paragraph("table_2_main_results.tex", MONO), Paragraph("Tabla LaTeX: resultados RDD1 (EP baseline + covariables)", S("oc", fontSize=9, leading=13))],
    [Paragraph("table_2b_dpto_fe.tex", MONO), Paragraph("Tabla LaTeX: efectos fijos por departamento", S("oc", fontSize=9, leading=13))],
    [Paragraph("table_3_heterogeneity.tex", MONO), Paragraph("Tabla LaTeX: heterogeneidad urbano/rural", S("oc", fontSize=9, leading=13))],
    [Paragraph("table_4_rdd2_sisfoh.tex", MONO), Paragraph("Tabla LaTeX: resultados RDD2 (BLOQUE F)", S("oc", fontSize=9, leading=13))],
    [Paragraph("figure_1_rdplot.png", MONO), Paragraph("Gráfico RDD1: adopción por edad (dispersión binada)", S("oc", fontSize=9, leading=13))],
    [Paragraph("figure_rdd2_rdplot.png", MONO), Paragraph("Gráfico RDD2: adopción por índice SISFOH", S("oc", fontSize=9, leading=13))],
    [Paragraph("figure_rdd2_density.png", MONO), Paragraph("Histograma de densidad del índice SISFOH en el corte", S("oc", fontSize=9, leading=13))],
]

to = Table(out_data, colWidths=[5.5*cm, 11.0*cm])
to.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), NARANJA),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, NARANJA_C]),
    ("GRID", (0,0), (-1,-1), 0.4, GRIS_M),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(to)

# ── Conclusión ─────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.3*cm))
story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL))
story.append(Spacer(1, 0.15*cm))

box_data = [[Paragraph(
    "RESUMEN EN UNA ORACIÓN\n\n"
    "El script descarga datos del INEI, construye indicadores de billetera digital "
    "y pobreza, aplica dos diseños de regresión discontinua (uno por edad y otro "
    "por índice de bienestar), corre 7 pruebas de robustez, y genera todas las "
    "tablas y figuras del paper académico de forma automática.",
    S("box", fontSize=10, leading=15, textColor=AZUL,
      fontName="Helvetica-Bold", alignment=TA_CENTER))]]
box = Table(box_data, colWidths=[16.3*cm])
box.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), AZUL_C),
    ("BOX", (0,0), (-1,-1), 1.5, AZUL),
    ("TOPPADDING", (0,0), (-1,-1), 14),
    ("BOTTOMPADDING", (0,0), (-1,-1), 14),
    ("LEFTPADDING", (0,0), (-1,-1), 14),
    ("RIGHTPADDING", (0,0), (-1,-1), 14),
]))
story.append(box)
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("Generado automáticamente — Pipeline Pensión 65 RDD, Mayo 2026.", PIE))

doc.build(story)
print(f"PDF generado: {os.path.abspath(OUTPUT)}")
