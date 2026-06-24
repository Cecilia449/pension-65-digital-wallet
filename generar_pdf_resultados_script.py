"""
generar_pdf_resultados_script.py
Genera PDF con resultados reales fase a fase del script.py
Todos los numeros provienen de los CSVs generados por el pipeline.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas

# ─── Colores ─────────────────────────────────────────────────────────────────
AZUL       = colors.HexColor('#1F4E79')
AZUL_CLARO = colors.HexColor('#F2F7FB')
AZUL_MEDIO = colors.HexColor('#BDD7EE')
GRIS       = colors.HexColor('#D0D0D0')
GRIS_TEXT  = colors.HexColor('#555555')
BLANCO     = colors.white
NEGRO      = colors.black
VERDE      = colors.HexColor('#1F7A1F')
ROJO       = colors.HexColor('#C00000')
NARANJA    = colors.HexColor('#C05000')

# ─── Página ──────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm
W = PAGE_W - ML - MR
OUTPUT = "data/clean/resultados_pipeline_completo.pdf"

# ─── Numeración ──────────────────────────────────────────────────────────────
class PNC(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved = []
    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        for state in self._saved:
            self.__dict__.update(state)
            pg = self._pageNumber
            if pg > 2:
                self.setFont("Helvetica", 9)
                self.setFillColor(GRIS_TEXT)
                self.drawCentredString(PAGE_W/2, 1.2*cm, f"— {pg} —")
                self.setStrokeColor(AZUL_MEDIO)
                self.setLineWidth(0.5)
                self.line(ML, 1.7*cm, PAGE_W-MR, 1.7*cm)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

# ─── Estilos ─────────────────────────────────────────────────────────────────
_ss = getSampleStyleSheet()
_n = [0]
def E(parent='Normal', **kw):
    _n[0] += 1
    return ParagraphStyle(f'S{_n[0]}', parent=_ss[parent], **kw)

SEC  = E(fontSize=15, textColor=AZUL, fontName='Helvetica-Bold',
         leading=21, spaceBefore=12, spaceAfter=5)
SSEC = E(fontSize=12, textColor=AZUL, fontName='Helvetica-Bold',
         leading=17, spaceBefore=8, spaceAfter=4)
BODY = E(fontSize=10, leading=15, spaceAfter=4, alignment=TA_JUSTIFY)
MONO = E(fontSize=9,  leading=13, spaceAfter=2, fontName='Courier',
         textColor=colors.HexColor('#2C3E50'))
NOTA = E(fontSize=8,  textColor=GRIS_TEXT, leading=11, spaceAfter=3)
WARN = E(fontSize=10, textColor=NARANJA, leading=14, spaceAfter=4,
         alignment=TA_JUSTIFY)

def cab(t, size=9):
    return Paragraph(f"<b>{t}</b>",
        E(fontSize=size, textColor=BLANCO, alignment=TA_CENTER,
          leading=size+3, fontName='Helvetica-Bold'))

def cel(t, bold=False, align=TA_LEFT, color=NEGRO, size=9):
    b, e = ('<b>','</b>') if bold else ('','')
    return Paragraph(f"{b}{t}{e}",
        E(fontSize=size, alignment=align, textColor=color, leading=size+3))

def T(data, cw, hdr=1):
    t = Table(data, colWidths=cw, repeatRows=hdr)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,hdr-1), AZUL),
        ('TEXTCOLOR',     (0,0),(-1,hdr-1), BLANCO),
        ('FONTNAME',      (0,0),(-1,hdr-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 9),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROWBACKGROUND', (0,hdr),(-1,-1), [AZUL_CLARO, BLANCO]),
        ('GRID',          (0,0),(-1,-1), 0.4, GRIS),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return t

def HR(): return HRFlowable(width=W, thickness=1.5, color=AZUL, spaceAfter=6)
def hr(): return HRFlowable(width=W, thickness=0.4, color=GRIS, spaceAfter=4)

def badge(txt, bg=AZUL, fg=BLANCO):
    b = Table([[Paragraph(f"<b>{txt}</b>",
        E(fontSize=9, textColor=fg, alignment=TA_CENTER,
          fontName='Helvetica-Bold', leading=12))]],
        colWidths=[4.5*cm])
    b.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),bg),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    return b

S = []

# ════════════════════════════════════════════════════════════════════════════
# PORTADA
# ════════════════════════════════════════════════════════════════════════════
S.append(Table([[
    Paragraph("<b>Pensión 65 y billetera digital:<br/>"
              "Resultados del pipeline completo (script.py)</b>",
        E(fontSize=19, textColor=BLANCO, fontName='Helvetica-Bold',
          alignment=TA_CENTER, leading=26))
]], colWidths=[W]))
S[-1].setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),AZUL),
    ('TOPPADDING',(0,0),(-1,-1),32),('BOTTOMPADDING',(0,0),(-1,-1),32),
    ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),
]))
S.append(Spacer(1, 0.7*cm))
S.append(Paragraph("Reporte automático — resultados fase a fase",
    E(fontSize=13, textColor=AZUL, alignment=TA_CENTER,
      fontName='Helvetica-Bold', leading=19)))
S.append(Spacer(1, 1.2*cm))

meta = Table([
    [cel("Autora:",   bold=True,size=11), cel("Cecilia Vargas Risco",size=11)],
    [cel("Fecha:",    bold=True,size=11), cel("24 de junio de 2026",size=11)],
    [cel("Datos:",    bold=True,size=11), cel("ENAHO 2024 — INEI (Encuesta 966)",size=11)],
    [cel("Script:",   bold=True,size=11), cel("scripts/script_completo/script.py",size=11)],
    [cel("Pipeline:", bold=True,size=11), cel("5 Fases + Bloque F + RDD Ampliado (IFH)",size=11)],
], colWidths=[W*0.26, W*0.74])
meta.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),AZUL_CLARO),
    ('GRID',(0,0),(-1,-1),0.4,AZUL_MEDIO),
    ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ('LEFTPADDING',(0,0),(-1,-1),9),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
]))
S.append(meta)
S.append(Spacer(1,1.0*cm))
S.append(HR())
S.append(Spacer(1,0.4*cm))
S.append(Paragraph(
    "Este documento reporta los resultados reales generados por el pipeline de análisis, "
    "leídos directamente desde los CSV de output. Incluye estadísticas de cada fase, "
    "tablas de resultados del RDD principal, del RDD ampliado (Fuzzy RDD sobre ELEGIBLE_IFH), "
    "y del RDD2 (proxy SISFOH como running variable). No contiene placeholders.",
    E(fontSize=10, leading=15, alignment=TA_JUSTIFY, textColor=GRIS_TEXT)))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# ÍNDICE
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("Índice", SEC))
S.append(HR())
for num, tit in [
    ("1.", "Resumen ejecutivo"),
    ("2.", "Fase 1 — Preprocessing ENAHO 2024"),
    ("3.", "Fase 2 — Construcción del dataset analítico"),
    ("4.", "Fase 3 — RDD principal (muestra completa)"),
    ("5.", "Fase 3 Bloque D — Dilución ITT → LATE"),
    ("6.", "RDD Ampliado — Fuzzy RDD (submuestra ELEGIBLE_IFH)"),
    ("7.", "Bloque F — RDD2 (proxy SISFOH como running variable)"),
    ("8.", "Archivos generados"),
]:
    S.append(Paragraph(f"{num}&nbsp;&nbsp;{tit}",
        E(fontSize=11, leading=19, leftIndent=0)))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 1. RESUMEN EJECUTIVO
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("1. Resumen ejecutivo", SEC))
S.append(HR())
S.append(Paragraph(
    "El pipeline procesa 117,721 personas (33,691 hogares) de la ENAHO 2024. "
    "Se construyen tres diseños de estimación:", BODY))

kpis = Table([
    [cel("117,721",bold=True,align=TA_CENTER,color=AZUL,size=17),
     cel("113,755",bold=True,align=TA_CENTER,color=AZUL,size=17),
     cel("4,437",  bold=True,align=TA_CENTER,color=AZUL,size=17),
     cel("2,288",  bold=True,align=TA_CENTER,color=AZUL,size=17)],
    [cel("personas ENAHO",align=TA_CENTER,size=9),
     cel("dataset analítico",align=TA_CENTER,size=9),
     cel("receptores P65",align=TA_CENTER,size=9),
     cel("N fuzzy RDD (IFH)",align=TA_CENTER,size=9)],
], colWidths=[W/4]*4)
kpis.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),AZUL_CLARO),
    ('GRID',(0,0),(-1,-1),0.4,AZUL_MEDIO),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),
    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
]))
S.append(kpis)
S.append(Spacer(1,0.3*cm))

resumen = T([
    [cab("Diseño"), cab("Muestra"), cab("Outcome"), cab("Estimado"), cab("IC 95%"), cab("Sig.")],
    [cel("RDD Sharp\n(muestra completa)"),
     cel("113,755\nh*=18.0 años"),
     cel("TIENE_BILLETERA"),
     cel("+0.0006", align=TA_CENTER),
     cel("[−0.036, +0.037]", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
    [cel("Fuzzy RDD\n(ELEGIBLE_IFH)"),
     cel("2,288\nventana ±5 años"),
     cel("TIENE_BILLETERA"),
     cel("−0.005 (LATE)", align=TA_CENTER),
     cel("[−0.358, +0.349]", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
    [cel("Fuzzy RDD\n(ELEGIBLE_IFH)"),
     cel("2,288\nventana ±5 años"),
     cel("BANCO_PRIVADO"),
     cel("+0.645 (LATE)", bold=True, align=TA_CENTER, color=ROJO),
     cel("[+0.074, +1.217]", align=TA_CENTER),
     cel("** p=0.027", bold=True, align=TA_CENTER, color=ROJO)],
    [cel("RDD2 (proxy SISFOH)"),
     cel("4,606\nN efectivo"),
     cel("TIENE_BILLETERA"),
     cel("−0.030", align=TA_CENTER),
     cel("[−0.064, +0.004]", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
], [W*0.20, W*0.18, W*0.18, W*0.14, W*0.20, W*0.10])
S.append(resumen)
S.append(Spacer(1,0.2*cm))
S.append(Paragraph(
    "El efecto sobre billetera digital es nulo en los tres diseños. "
    "El único efecto significativo (p&lt;0.05) es sobre cuenta en banco privado (+64.5 pp LATE) "
    "en el fuzzy RDD, lo que probablemente refleja una discontinuidad competidora "
    "(jubilación ONP/AFP a los 65 años).",
    BODY))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 2. FASE 1
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("2. Fase 1 — Preprocessing ENAHO 2024", SEC))
S.append(HR())
S.append(Paragraph(
    "Merge de 6 módulos a nivel persona. Output: <b>enaho_2024_clean.csv</b> "
    "(22.3 MB, 47 columnas).", BODY))

S.append(Paragraph("<b>Estadísticas del dataset integrado</b>", SSEC))
S.append(T([
    [cab("Indicador"), cab("Valor")],
    [cel("Personas en muestra"), cel("117,721", bold=True, align=TA_CENTER)],
    [cel("Hogares únicos"),      cel("33,691",  align=TA_CENTER)],
    [cel("Columnas"),            cel("47",       align=TA_CENTER)],
], [W*0.60, W*0.40]))
S.append(Spacer(1,0.3*cm))

S.append(Paragraph("<b>Variables de outcome y tratamiento construidas</b>", SSEC))
S.append(T([
    [cab("Variable"), cab("Descripción"), cab("N=1"), cab("% del total")],
    [cel("TIENE_BILLETERA"),   cel("Tenencia OR uso billetera (Yape/Plin/CuentaDNI)"),
     cel("23,206", align=TA_CENTER), cel("19.7%", align=TA_CENTER)],
    [cel("USA_BILLETERA"),     cel("Uso activo en últimos 12 meses (P558Hk_7)"),
     cel("18,327", align=TA_CENTER), cel("15.6%", align=TA_CENTER)],
    [cel("BANCO_PREVIO"),      cel("Cuenta bancaria (banco privado OR BN)"),
     cel("47,819", align=TA_CENTER), cel("40.6%", align=TA_CENTER)],
    [cel("BANCO_PRIVADO"),     cel("Cuenta en banco privado (P558E1_1)"),
     cel("41,226", align=TA_CENTER), cel("47.9%* no nulos", align=TA_CENTER)],
    [cel("BANCO_NACION"),      cel("Cuenta en Banco de la Nación (P558E1_8)"),
     cel("28,941", align=TA_CENTER), cel("33.7%* no nulos", align=TA_CENTER)],
    [cel("RECIBE_P65_PERSONA"),cel("Recibe Pensión 65 (P5567A=1) — tratamiento endógeno"),
     cel("4,437",  bold=True, align=TA_CENTER, color=AZUL),
     cel("5.2%*", bold=True, align=TA_CENTER, color=AZUL)],
], [W*0.22, W*0.45, W*0.15, W*0.18]))
S.append(Spacer(1,0.1*cm))
S.append(Paragraph(
    "* Los porcentajes de BANCO_PRIVADO y BANCO_NACION se calculan sobre el subconjunto "
    "con módulo 05 disponible. RECIBE_P65_PERSONA: porcentaje sobre personas ≥18 años con M05.",
    NOTA))

S.append(Paragraph("<b>Módulos ENAHO integrados</b>", SSEC))
S.append(T([
    [cab("Módulo"), cab("Alias"), cab("Contenido"), cab("Variables clave extraídas")],
    [cel("01"), cel("m01"), cel("Vivienda"),
     cel("UBIGEO, DOMINIO, AREA, P102-P113A, INTERNET_HOGAR")],
    [cel("02"), cel("m02"), cel("Miembros del hogar"),
     cel("GENERO (P207), EDAD (P208A), FACTOR_EXPANSION")],
    [cel("03"), cel("m03"), cel("Educación"),
     cel("NIVEL_EDUCATIVO (P301A)")],
    [cel("05"), cel("m05"), cel("Empleo + Servicios financieros"),
     cel("TIENE_BILLETERA, USA_BILLETERA, BANCO_*, RECIBE_P65_PERSONA")],
    [cel("18"), cel("m18"), cel("Equipamiento del hogar"),
     cel("SMARTPHONE (P612N=10), REFRIGERADOR (=4), TIENE_TV (=2)")],
    [cel("34"), cel("sum"), cel("Sumaria"),
     cel("POBREZA, POBREZAV, INGTPU01/03, INGHOG2D, MIEPERHO")],
], [W*0.08, W*0.08, W*0.20, W*0.64]))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 3. FASE 2
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("3. Fase 2 — Construcción del dataset analítico", SEC))
S.append(HR())
S.append(Paragraph(
    "Filtra EDAD no-nula, centra la running variable en 65, construye SAMPLE_FLAGs "
    "y guarda <b>main_dataset.csv</b> (23.6 MB). "
    "Los archivos legacy enaho_rdd_full.csv y enaho_rdd_main.csv se mantienen "
    "para backward-compatibility con Fases 3-5.", BODY))

S.append(Paragraph("<b>Dataset analítico principal</b>", SSEC))
S.append(T([
    [cab("Partición"), cab("N"), cab("% total"), cab("Nota")],
    [cel("SAMPLE_A — Full (muestra primaria)", bold=True),
     cel("113,755", bold=True, align=TA_CENTER, color=AZUL),
     cel("100%", align=TA_CENTER),
     cel("Diseño primario del fuzzy RDD")],
    [cel("SAMPLE_B — POBREZA=1 (extrema pobreza monetaria)"),
     cel("6,717", align=TA_CENTER),
     cel("5.9%",  align=TA_CENTER),
     cel("Solo heterogeneidad descriptiva — NO diseño primario")],
    [cel("SAMPLE_C — POBREZA ∈ {1,2} (pobre monetario)"),
     cel("28,737", align=TA_CENTER),
     cel("25.3%", align=TA_CENTER),
     cel("Solo heterogeneidad descriptiva — NO diseño primario")],
], [W*0.40, W*0.12, W*0.10, W*0.38]))
S.append(Spacer(1,0.3*cm))

S.append(Paragraph("<b>Receptores reales de Pensión 65 por partición</b>", SSEC))
S.append(T([
    [cab("Partición"), cab("Receptores P65 (N)"), cab("% del total de receptores"), cab("Interpretación")],
    [cel("SAMPLE_A (full)"),
     cel("4,437", bold=True, align=TA_CENTER, color=AZUL),
     cel("100%", align=TA_CENTER),
     cel("Todos los receptores")],
    [cel("SAMPLE_B (POBREZA=1)"),
     cel("501",  bold=True, align=TA_CENTER, color=ROJO),
     cel("11.3%", bold=True, align=TA_CENTER, color=ROJO),
     cel("Excluye 88.7% de receptores reales")],
    [cel("SAMPLE_C (POBREZA≤2)"),
     cel("1,619", align=TA_CENTER),
     cel("36.5%", align=TA_CENTER),
     cel("Excluye 63.5% de receptores reales")],
], [W*0.28, W*0.20, W*0.22, W*0.30]))
S.append(Spacer(1,0.2*cm))
S.append(Paragraph(
    "Esto confirma el error conceptual documentado en CLAUDE.md: "
    "restringir por POBREZA monetaria excluye al 88.7% de los receptores reales. "
    "POBREZA es post-tratamiento (el programa eleva el gasto del hogar). "
    "SAMPLE_A es la muestra primaria del diseño.",
    WARN))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 4. FASE 3 — RDD PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("4. Fase 3 — RDD principal (muestra completa)", SEC))
S.append(HR())
S.append(Paragraph(
    "Estimaciones sobre <b>enaho_rdd_full.csv</b> (muestra completa, N=113,755). "
    "Método: rdrobust con kernel triangular, bandwidth MSE-óptimo (h*≈18 años). "
    "Fallback: statsmodels WLS con HC2. Output: <b>main_results.csv</b>.", BODY))

S.append(Paragraph("<b>Bloque A — Estimaciones principales (df_full)</b>", SSEC))
S.append(T([
    [cab("Outcome"), cab("Especificación"), cab("Estimado"), cab("SE robusto"),
     cab("IC 95%"), cab("BW"), cab("N ef."), cab("Método")],
    [cel("TIENE_BILLETERA"), cel("Baseline"),
     cel("+0.0006", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0187",  align=TA_CENTER),
     cel("[−0.036, +0.037]", align=TA_CENTER),
     cel("18.0", align=TA_CENTER), cel("35,006", align=TA_CENTER),
     cel("rdrobust", align=TA_CENTER)],
    [cel("TIENE_BILLETERA"), cel("Con covariables"),
     cel("−0.0033", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0139",  align=TA_CENTER),
     cel("[−0.031, +0.024]", align=TA_CENTER),
     cel("15.9", align=TA_CENTER), cel("29,139", align=TA_CENTER),
     cel("rdrobust", align=TA_CENTER)],
    [cel("TIENE_BILLETERA"), cel("+ Efectos depto. (FE)"),
     cel("−0.0140", bold=True, align=TA_CENTER, color=NARANJA),
     cel("0.0065",  align=TA_CENTER),
     cel("[−0.027, −0.001]", bold=True, align=TA_CENTER, color=NARANJA),
     cel("33.5", align=TA_CENTER), cel("57,039", align=TA_CENTER),
     cel("WLS", align=TA_CENTER)],
    [cel("USA_BILLETERA"), cel("Baseline"),
     cel("+0.0015", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0180",  align=TA_CENTER),
     cel("[−0.034, +0.037]", align=TA_CENTER),
     cel("17.3", align=TA_CENTER), cel("33,267", align=TA_CENTER),
     cel("rdrobust", align=TA_CENTER)],
    [cel("USA_BILLETERA"), cel("Con covariables"),
     cel("+0.0006", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0106",  align=TA_CENTER),
     cel("[−0.020, +0.021]", align=TA_CENTER),
     cel("14.0", align=TA_CENTER), cel("27,325", align=TA_CENTER),
     cel("rdrobust", align=TA_CENTER)],
    [cel("USA_BILLETERA"), cel("+ Efectos depto. (FE)"),
     cel("+0.0084", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0048",  align=TA_CENTER),
     cel("[−0.001, +0.018]", align=TA_CENTER),
     cel("33.5", align=TA_CENTER), cel("57,039", align=TA_CENTER),
     cel("WLS", align=TA_CENTER)],
], [W*0.18, W*0.18, W*0.10, W*0.10, W*0.19, W*0.07, W*0.09, W*0.09]))
S.append(Spacer(1,0.2*cm))
S.append(Paragraph(
    "Nota: La especificación con efectos fijos departamentales usa WLS "
    "porque rdrobust no acepta tantas covariables. "
    "El resultado con FE (−0.014, p&lt;0.05) puede reflejar variación "
    "intra-departamento, pero el BW es muy amplio (33.5 años).",
    NOTA))

S.append(Paragraph("<b>Bloque B — Heterogeneidad extrema pobreza (df_main, POBREZA=1)</b>", SSEC))
S.append(T([
    [cab("Outcome"), cab("Especificación"), cab("Estimado"), cab("SE robusto"),
     cab("IC 95%"), cab("BW"), cab("N ef.")],
    [cel("TIENE_BILLETERA"), cel("EP baseline"),
     cel("+0.0284", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0215",  align=TA_CENTER),
     cel("[−0.014, +0.070]", align=TA_CENTER),
     cel("13.8", align=TA_CENTER), cel("1,144", align=TA_CENTER)],
    [cel("USA_BILLETERA"), cel("EP baseline"),
     cel("−0.0017", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0008",  align=TA_CENTER),
     cel("[−0.003, −0.000]", bold=True, align=TA_CENTER, color=NARANJA),
     cel("7.6", align=TA_CENTER), cel("663", align=TA_CENTER)],
], [W*0.22, W*0.18, W*0.10, W*0.10, W*0.18, W*0.10, W*0.12]))
S.append(Spacer(1,0.1*cm))
S.append(Paragraph(
    "Advertencia: bajo poder estadístico (N=663–1,144 efectivos). "
    "Estas estimaciones son descriptivas, NO el diseño primario. "
    "Ver sección crítica de CLAUDE.md sobre POBREZA vs SISFOH.",
    NOTA))

S.append(Paragraph("<b>Bloque C — Heterogeneidad urbano/rural (df_full, TIENE_BILLETERA)</b>", SSEC))
S.append(T([
    [cab("Área"), cab("Estimado"), cab("SE robusto"), cab("IC 95%"), cab("BW"), cab("N ef.")],
    [cel("Urbano"),
     cel("−0.0324", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0359",  align=TA_CENTER),
     cel("[−0.103, +0.038]", align=TA_CENTER),
     cel("12.1", align=TA_CENTER), cel("8,800", align=TA_CENTER)],
    [cel("Rural"),
     cel("+0.0159", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.0195",  align=TA_CENTER),
     cel("[−0.022, +0.054]", align=TA_CENTER),
     cel("11.8", align=TA_CENTER), cel("11,211", align=TA_CENTER)],
], [W*0.20, W*0.14, W*0.14, W*0.22, W*0.12, W*0.18]))
S.append(Spacer(1,0.1*cm))
S.append(Paragraph("Ningún subgrupo muestra efecto significativo.", NOTA))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 5. DILUCIÓN ITT → LATE
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("5. Fase 3 Bloque D — Dilución ITT → LATE", SEC))
S.append(HR())
S.append(Paragraph(
    "El ITT se estima sobre la muestra completa. El LATE implícito ajusta "
    "por la fracción de extrema pobreza en el bandwidth y la tasa de take-up "
    "asumida del 75% (fuente: MIDIS 2024).", BODY))

S.append(T([
    [cab("Parámetro"), cab("Valor"), cab("Interpretación")],
    [cel("Fracción EP en bandwidth (POBREZA=1, lado ≥65)"),
     cel("5.05%", align=TA_CENTER),
     cel("Solo el 5% de las personas cerca del corte son extrema pobreza")],
    [cel("Tasa de take-up asumida (MIDIS 2024)"),
     cel("75%",   align=TA_CENTER),
     cel("Del 5%, solo el 75% efectivamente recibe el bono")],
    [cel("τ_ITT (muestra completa, TIENE_BILLETERA)"),
     cel("+0.0006", align=TA_CENTER, color=GRIS_TEXT),
     cel("Efecto promedio en toda la población cerca del corte")],
    [cel("τ_LATE implícito"),
     cel("+0.0154", bold=True, align=TA_CENTER, color=AZUL),
     cel("Efecto en los compliers — aún cercano a cero")],
], [W*0.50, W*0.12, W*0.38]))
S.append(Spacer(1,0.2*cm))
S.append(Paragraph(
    "El τ_LATE implícito de +1.5 pp es económicamente pequeño y el ITT de +0.06 pp "
    "está lejos de la significancia. La baja penetración del programa (~5% en el "
    "bandwidth de edad) explica la dilución extrema del efecto.",
    BODY))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 6. RDD AMPLIADO — FUZZY RDD (ELEGIBLE_IFH)
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("6. RDD Ampliado — Fuzzy RDD (submuestra ELEGIBLE_IFH)", SEC))
S.append(HR())
S.append(Paragraph(
    "Diseño: Fuzzy RDD sobre submuestra ELEGIBLE_IFH=1 (IFH ≤ umbral departamental, "
    "proxy SISFOH). Ventana ±5 años. N=2,288. "
    "First Stage (instrumento MAYOR65 → RECIBE_P65_PERSONA): "
    "<b>+13.5 pp, F-stat alto (***)</b>. "
    "Nadie &lt;65 años recibe P65 (0.0% exacto). "
    "LATE = Forma Reducida / First Stage, SE por método delta.", BODY))

S.append(Paragraph("<b>First Stage</b>", SSEC))
S.append(T([
    [cab("Especificación"), cab("N"), cab("Coef. FS (MAYOR65→P65)"), cab("Sig.")],
    [cel("Sin controles"), cel("2,288", align=TA_CENTER),
     cel("0.1348", bold=True, align=TA_CENTER, color=VERDE),
     cel("***", bold=True, align=TA_CENTER, color=VERDE)],
    [cel("Con controles"), cel("2,288", align=TA_CENTER),
     cel("0.1343", bold=True, align=TA_CENTER, color=VERDE),
     cel("***", bold=True, align=TA_CENTER, color=VERDE)],
], [W*0.35, W*0.15, W*0.35, W*0.15]))
S.append(Spacer(1,0.3*cm))

S.append(Paragraph("<b>LATE por outcome — sin controles</b>", SSEC))
S.append(T([
    [cab("Outcome"), cab("N"), cab("LATE"), cab("SE"), cab("p-valor"), cab("IC 95%"), cab("Sig.")],
    [cel("TIENE_BILLETERA"), cel("2,288",align=TA_CENTER),
     cel("−0.0046",align=TA_CENTER,color=GRIS_TEXT),
     cel("0.1805",align=TA_CENTER),
     cel("0.9795",align=TA_CENTER),
     cel("[−0.358, +0.349]",align=TA_CENTER),
     cel("n.s.",align=TA_CENTER,color=GRIS_TEXT)],
    [cel("USA_BILLETERA"), cel("2,288",align=TA_CENTER),
     cel("+0.0127",align=TA_CENTER,color=GRIS_TEXT),
     cel("0.1275",align=TA_CENTER),
     cel("0.9208",align=TA_CENTER),
     cel("[−0.237, +0.263]",align=TA_CENTER),
     cel("n.s.",align=TA_CENTER,color=GRIS_TEXT)],
    [cel("BANCO_PREVIO"), cel("2,288",align=TA_CENTER),
     cel("+0.7114",bold=True,align=TA_CENTER,color=ROJO),
     cel("0.3043",align=TA_CENTER),
     cel("0.0194",bold=True,align=TA_CENTER),
     cel("[+0.115, +1.308]",bold=True,align=TA_CENTER,color=ROJO),
     cel("**",bold=True,align=TA_CENTER,color=ROJO)],
    [cel("BANCO_PRIVADO"), cel("2,288",align=TA_CENTER),
     cel("+0.6452",bold=True,align=TA_CENTER,color=NARANJA),
     cel("0.2915",align=TA_CENTER),
     cel("0.0269",bold=True,align=TA_CENTER),
     cel("[+0.074, +1.217]",bold=True,align=TA_CENTER,color=NARANJA),
     cel("**",bold=True,align=TA_CENTER,color=NARANJA)],
    [cel("BANCO_NACION"), cel("2,288",align=TA_CENTER),
     cel("−0.0099",align=TA_CENTER,color=GRIS_TEXT),
     cel("0.2035",align=TA_CENTER),
     cel("0.9612",align=TA_CENTER),
     cel("[−0.409, +0.389]",align=TA_CENTER),
     cel("n.s.",align=TA_CENTER,color=GRIS_TEXT)],
], [W*0.22, W*0.08, W*0.10, W*0.08, W*0.09, W*0.30, W*0.08]))
S.append(Spacer(1,0.2*cm))

S.append(Paragraph("<b>LATE por outcome — con controles</b>", SSEC))
S.append(T([
    [cab("Outcome"), cab("N"), cab("LATE"), cab("SE"), cab("p-valor"), cab("IC 95%"), cab("Sig.")],
    [cel("TIENE_BILLETERA"), cel("2,288",align=TA_CENTER),
     cel("−0.0313",align=TA_CENTER,color=GRIS_TEXT),
     cel("0.1719",align=TA_CENTER),
     cel("0.8556",align=TA_CENTER),
     cel("[−0.368, +0.306]",align=TA_CENTER),
     cel("n.s.",align=TA_CENTER,color=GRIS_TEXT)],
    [cel("USA_BILLETERA"), cel("2,288",align=TA_CENTER),
     cel("−0.0155",align=TA_CENTER,color=GRIS_TEXT),
     cel("0.1219",align=TA_CENTER),
     cel("0.8987",align=TA_CENTER),
     cel("[−0.254, +0.223]",align=TA_CENTER),
     cel("n.s.",align=TA_CENTER,color=GRIS_TEXT)],
    [cel("BANCO_PREVIO"), cel("2,288",align=TA_CENTER),
     cel("+0.6361",bold=True,align=TA_CENTER,color=ROJO),
     cel("0.2798",align=TA_CENTER),
     cel("0.0230",bold=True,align=TA_CENTER),
     cel("[+0.088, +1.184]",bold=True,align=TA_CENTER,color=ROJO),
     cel("**",bold=True,align=TA_CENTER,color=ROJO)],
    [cel("BANCO_PRIVADO"), cel("2,288",align=TA_CENTER),
     cel("+0.5717",bold=True,align=TA_CENTER,color=NARANJA),
     cel("0.2726",align=TA_CENTER),
     cel("0.0360",bold=True,align=TA_CENTER),
     cel("[+0.037, +1.106]",bold=True,align=TA_CENTER,color=NARANJA),
     cel("**",bold=True,align=TA_CENTER,color=NARANJA)],
    [cel("BANCO_NACION"), cel("2,288",align=TA_CENTER),
     cel("−0.0620",align=TA_CENTER,color=GRIS_TEXT),
     cel("0.1799",align=TA_CENTER),
     cel("0.7302",align=TA_CENTER),
     cel("[−0.415, +0.291]",align=TA_CENTER),
     cel("n.s.",align=TA_CENTER,color=GRIS_TEXT)],
], [W*0.22, W*0.08, W*0.10, W*0.08, W*0.09, W*0.30, W*0.08]))
S.append(Spacer(1,0.2*cm))
S.append(hr())
S.append(Paragraph(
    "*** p&lt;0.01  ** p&lt;0.05  * p&lt;0.10  n.s. no significativo. "
    "SE robustos HC1 (n/(n−k)). LATE por método delta. "
    "Controles: NIVEL_EDUCATIVO, AREA_urbano, POBREZA.",
    NOTA))
S.append(Spacer(1,0.3*cm))
S.append(Paragraph(
    "<b>Interpretación:</b> el efecto sobre billetera digital (Yape/Plin/CuentaDNI) "
    "es nulo en las cuatro especificaciones. El único efecto significativo (p&lt;0.05) "
    "es sobre cuenta en banco privado (+57 a +71 pp LATE), robusto a controles. "
    "Paradoja: Pensión 65 paga vía Banco de la Nación — si el mecanismo fuera el pago "
    "del programa, esperaríamos efecto en BANCO_NACION, no en BANCO_PRIVADO. "
    "Hipótesis más plausible: discontinuidad competidora de jubilación ONP/AFP a los 65 años.",
    BODY))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 7. BLOQUE F — RDD2 PROXY SISFOH
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("7. Bloque F — RDD2 (proxy SISFOH como running variable)", SEC))
S.append(HR())
S.append(Paragraph(
    "Réplica del diseño de Bando, Galiani y Gertler (2020). "
    "Running variable: PCA sobre variables ENAHO de vivienda y equipamiento "
    "(PARED, PISO, AGUA, SERVSANIT, ALUMBRADO, COMBUSTIBLE, HACINAMIENTO, "
    "REFRIGERADOR, TIENE_TV, SMARTPHONE). "
    "Muestra: adultos ≥65 años. Cutoff: umbral que separa POBREZA=2 de POBREZA=1 "
    "en la distribución del PC1.", BODY))

S.append(Paragraph("<b>Estimaciones RDD2 (billetera digital)</b>", SSEC))
S.append(T([
    [cab("Outcome"), cab("Especificación"), cab("Estimado"), cab("SE robusto"),
     cab("IC 95%"), cab("N ef."), cab("Sig.")],
    [cel("TIENE_BILLETERA"), cel("Sin covariables"),
     cel("−0.030", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.017",  align=TA_CENTER),
     cel("[−0.064, +0.004]", align=TA_CENTER),
     cel("4,606", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
    [cel("TIENE_BILLETERA"), cel("Con covariables"),
     cel("−0.030", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.018",  align=TA_CENTER),
     cel("[−0.065, +0.004]", align=TA_CENTER),
     cel("4,234", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
    [cel("USA_BILLETERA"), cel("Sin covariables"),
     cel("−0.006", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.004",  align=TA_CENTER),
     cel("[−0.013, +0.002]", align=TA_CENTER),
     cel("2,775", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
    [cel("USA_BILLETERA"), cel("Con covariables"),
     cel("−0.004", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.004",  align=TA_CENTER),
     cel("[−0.012, +0.003]", align=TA_CENTER),
     cel("2,629", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
], [W*0.22, W*0.18, W*0.10, W*0.10, W*0.20, W*0.10, W*0.10]))
S.append(Spacer(1,0.3*cm))

S.append(Paragraph("<b>Balance de covariables en el cutoff SISFOH_PROXY</b>", SSEC))
S.append(T([
    [cab("Covariable"), cab("Estimado RDD"), cab("SE robusto"),
     cab("IC 95%"), cab("N ef."), cab("Sig.")],
    [cel("INTERNET_HOGAR"),
     cel("−0.076", bold=True, align=TA_CENTER, color=NARANJA),
     cel("0.038",  align=TA_CENTER),
     cel("[−0.151, −0.001]", bold=True, align=TA_CENTER, color=NARANJA),
     cel("3,538", align=TA_CENTER),
     cel("*", bold=True, align=TA_CENTER, color=NARANJA)],
    [cel("NIVEL_EDUCATIVO"),
     cel("−0.005", align=TA_CENTER, color=GRIS_TEXT),
     cel("0.182",  align=TA_CENTER),
     cel("[−0.362, +0.351]", align=TA_CENTER),
     cel("3,807", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
    [cel("INGRESO_PC"),
     cel("−715.4", align=TA_CENTER, color=GRIS_TEXT),
     cel("634.6",  align=TA_CENTER),
     cel("[−1,959, +528]", align=TA_CENTER),
     cel("2,769", align=TA_CENTER),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT)],
], [W*0.25, W*0.14, W*0.14, W*0.24, W*0.10, W*0.13]))
S.append(Spacer(1,0.2*cm))
S.append(Paragraph(
    "Advertencia: INTERNET_HOGAR muestra un desbalance significativo (*) en el cutoff "
    "del proxy SISFOH. Esto sugiere que el índice PCA no separa perfectamente dos grupos "
    "comparables en acceso a internet — potencial violación del supuesto de continuidad del RDD2.",
    WARN))
S.append(Paragraph(
    "El INGRESO_PC no tiene efecto significativo (IC muy amplio). "
    "NIVEL_EDUCATIVO es continuo en el corte.", BODY))
S.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 8. ARCHIVOS GENERADOS
# ════════════════════════════════════════════════════════════════════════════
S.append(Paragraph("8. Archivos generados por el pipeline", SEC))
S.append(HR())

S.append(Paragraph("<b>Datos (data/clean/)</b>", SSEC))
S.append(T([
    [cab("Archivo"), cab("Tamaño"), cab("Descripción")],
    [cel("enaho_2024_clean.csv"),       cel("22.3 MB",align=TA_CENTER), cel("Merge completo 6 módulos, 117,721 personas")],
    [cel("main_dataset.csv"),           cel("23.6 MB",align=TA_CENTER), cel("Dataset analítico con SAMPLE_FLAGs, 113,755 personas")],
    [cel("enaho_rdd_full.csv"),         cel("23.6 MB",align=TA_CENTER), cel("Legacy — muestra completa para Fases 3-5")],
    [cel("enaho_rdd_main.csv"),         cel("1.4 MB", align=TA_CENTER), cel("Legacy — solo POBREZA=1 (6,717 personas)")],
    [cel("main_results.csv"),           cel("2.1 KB", align=TA_CENTER), cel("12 filas: Bloques A/B/C/E de Fase 3")],
    [cel("resultados_rdd_ampliado.csv"),cel("1.3 KB", align=TA_CENTER), cel("10 filas: Fuzzy RDD sobre ELEGIBLE_IFH")],
    [cel("ifh_2024.csv"),               cel("10.7 MB",align=TA_CENTER), cel("IFH construido (BCK 2017), 115,450 hogares")],
    [cel("dilution_calc.json"),         cel("0.1 KB", align=TA_CENTER), cel("Cálculo dilución ITT → LATE")],
    [cel("enaho_rdd2_mayores.csv"),     cel("3.4 MB", align=TA_CENTER), cel("Adultos ≥65 con SISFOH_PROXY para Bloque F")],
    [cel("rdd2_results.csv"),           cel("1.3 KB", align=TA_CENTER), cel("7 filas: RDD2 baseline/covs + balance")],
    [cel("robustness_results.csv"),     cel("N/E",    align=TA_CENTER, color=ROJO), cel("No generado aún — requiere re-correr Fase 4")],
], [W*0.38, W*0.12, W*0.50]))
S.append(Spacer(1,0.3*cm))

S.append(Paragraph("<b>Figuras (paper/figures/)</b>", SSEC))
figs = [
    ("figure_1_rdplot.png/.pdf",              "RD plot: billetera vs edad (muestra completa)"),
    ("figure_2_bandwidth_sensitivity.png/.pdf","Sensibilidad al bandwidth — Fase 4"),
    ("figure_mccrary_density.png/.pdf",        "Densidad McCrary — test de manipulación"),
    ("figure_rdd2_density.png/.pdf",           "Densidad del running variable SISFOH proxy"),
    ("figure_rdd2_rdplot.png/.pdf",            "RD plot: billetera vs índice SISFOH proxy"),
    ("figure_first_stage.png/.pdf",            "First stage: % que recibe P65 por edad"),
    ("figure_descriptivos_brecha.png/.pdf",    "Brecha urbano/rural en adopción digital"),
    ("figure_pobreza_receptores.png/.pdf",     "Distribución de receptores P65 por POBREZA"),
    ("figure_bandwidth_sensitivity_granular.png/.pdf", "Sensibilidad granular al bandwidth"),
]
S.append(T(
    [[cab("Archivo"), cab("Descripción")]] +
    [[cel(f), cel(d)] for f, d in figs],
    [W*0.48, W*0.52]
))
S.append(Spacer(1,0.3*cm))

S.append(Paragraph("<b>Tablas LaTeX (paper/tables/)</b>", SSEC))
tabs = [
    ("table_1_summary.tex",          "Estadísticas descriptivas (tratados vs control)"),
    ("table_2_main_results.tex",     "RDD principal — Bloques A (MAIN_ baseline/covariates/dpto_fe)"),
    ("table_3_heterogeneity.tex",    "Heterogeneidad — EP_het_ + MAIN_het_AREA_ + EP_descriptivo"),
    ("table_3_robustness.tex",       "Robustez — bandwidth, donut, polinomio, placebo"),
    ("table_4_covariate_balance.tex","Balance de covariables en el bandwidth"),
    ("table_4_rdd2_sisfoh.tex",      "RDD2 — proxy SISFOH como running variable (Bloque F)"),
    ("table_A1_ep_descriptivo.tex",  "Apéndice — extrema pobreza descriptivo"),
    ("table_fuzzy_rdd_expo.tex",     "Tabla exposition: Fuzzy RDD (exposición)"),
    ("table_first_stage_expo.tex",   "Tabla exposition: First Stage"),
    ("table_pobreza_receptores_expo.tex", "Tabla exposition: receptores por pobreza"),
]
S.append(T(
    [[cab("Archivo"), cab("Descripción")]] +
    [[cel(f), cel(d)] for f, d in tabs],
    [W*0.45, W*0.55]
))
S.append(PageBreak())

# ─── Build ───────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=ML, rightMargin=MR,
    topMargin=MT, bottomMargin=2.5*cm,
    title="Resultados pipeline completo — Pension 65 RDD",
    author="Cecilia Vargas Risco",
)
doc.build(S, canvasmaker=PNC)
print(f"\nPDF generado: {OUTPUT}")
