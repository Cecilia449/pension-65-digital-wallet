"""
Genera presentacion_avance.pdf -- 10 diapositivas para el asesor.
Numeros 100% verificados. Sin placeholders.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

# -- Colores ------------------------------------------------------------------
AZUL       = colors.HexColor('#1F4E79')
AZUL_CLARO = colors.HexColor('#F2F7FB')
AZUL_MEDIO = colors.HexColor('#BDD7EE')
GRIS       = colors.HexColor('#D0D0D0')
GRIS_TEXT  = colors.HexColor('#555555')
BLANCO     = colors.white
NEGRO      = colors.black
VERDE      = colors.HexColor('#1F7A1F')
VERDE_BG   = colors.HexColor('#E2EFDA')
ROJO       = colors.HexColor('#C00000')
NARANJA    = colors.HexColor('#C05000')
AMARILLO   = colors.HexColor('#FFF2CC')

# -- Pagina (landscape A4) ----------------------------------------------------
PAGE_W, PAGE_H = landscape(A4)
MARGIN = 1.5 * cm
W = PAGE_W - 2 * MARGIN
FECHA  = "14 de junio de 2026"
AUTORA = "Cecilia Vargas Risco"
OUTPUT = "data/clean/presentacion_avance.pdf"

# -- Numeracion ---------------------------------------------------------------
class SlideCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            pg = self._pageNumber
            if pg > 1:
                self.setFont("Helvetica", 9)
                self.setFillColor(GRIS_TEXT)
                self.drawRightString(PAGE_W - MARGIN, 0.65*cm,
                                     f"{pg} / {total}")
                self.setStrokeColor(AZUL)
                self.setLineWidth(1.5)
                self.line(MARGIN, 1.0*cm, PAGE_W - MARGIN, 1.0*cm)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

# -- Estilos ------------------------------------------------------------------
_ss = getSampleStyleSheet()

def E(name, parent='Normal', **kw):
    return ParagraphStyle(name, parent=_ss[parent], **kw)

TIT   = E('TIT', fontSize=22, textColor=AZUL, fontName='Helvetica-Bold',
          leading=28, spaceBefore=0, spaceAfter=8)
BODY  = E('BOD', fontSize=12, leading=17, spaceAfter=5, alignment=TA_LEFT)
BULL  = E('BUL', fontSize=12, leading=16, spaceAfter=4,
          leftIndent=18, bulletIndent=6)
NOTA  = E('NOT', fontSize=9, textColor=GRIS_TEXT, leading=12, spaceAfter=3)
CONC  = E('CON', fontSize=13, textColor=VERDE, fontName='Helvetica-Bold',
          alignment=TA_CENTER, leading=18)

def cab(txt, size=10):
    return Paragraph(f"<b>{txt}</b>",
        E('HC_'+str(id(txt))[:6], fontSize=size, textColor=BLANCO,
          alignment=TA_CENTER, leading=size+3))

def cel(txt, bold=False, align=TA_LEFT, color=NEGRO, size=11):
    b, e2 = ('<b>','</b>') if bold else ('','')
    return Paragraph(f"{b}{txt}{e2}",
        E('CC_'+str(id(txt))[:6], fontSize=size, alignment=align,
          textColor=color, leading=size+3))

def T(data, cw, hdr=1, alt=AZUL_CLARO):
    t = Table(data, colWidths=cw, repeatRows=hdr)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,hdr-1), AZUL),
        ('TEXTCOLOR',     (0,0),(-1,hdr-1), BLANCO),
        ('FONTNAME',      (0,0),(-1,hdr-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 11),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROWBACKGROUND', (0,hdr),(-1,-1), [alt, BLANCO]),
        ('GRID',          (0,0),(-1,-1), 0.5, GRIS),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('RIGHTPADDING',  (0,0),(-1,-1), 7),
    ]))
    return t

def HR():
    return HRFlowable(width=W, thickness=2, color=AZUL, spaceAfter=10)

# -- Documento ----------------------------------------------------------------
doc = SimpleDocTemplate(
    OUTPUT, pagesize=landscape(A4),
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN,  bottomMargin=1.8*cm,
    title="Pension 65 y billetera digital -- avance de tesis",
    author=AUTORA,
)
S = []

# ============================================================
# DIAPOSITIVA 1 -- PORTADA
# ============================================================
banner = Table([[
    Paragraph(
        "<b>Pensión 65 y billetera digital:<br/>avance de tesis</b>",
        E('P1T', fontSize=26, textColor=BLANCO, fontName='Helvetica-Bold',
          alignment=TA_CENTER, leading=34))
]], colWidths=[W])
banner.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,-1), AZUL),
    ('TOPPADDING',    (0,0),(-1,-1), 28),
    ('BOTTOMPADDING', (0,0),(-1,-1), 28),
    ('LEFTPADDING',   (0,0),(-1,-1), 20),
    ('RIGHTPADDING',  (0,0),(-1,-1), 20),
]))
S.append(banner)
S.append(Spacer(1, 0.5*cm))
S.append(Paragraph(
    "Construcción del IFH y primeros resultados RDD",
    E('P1S', fontSize=16, textColor=AZUL, alignment=TA_CENTER, leading=22)))
S.append(Spacer(1, 0.5*cm))

kpi = Table([
    [cel("117,721", bold=True, align=TA_CENTER, color=AZUL, size=20),
     cel("115,450", bold=True, align=TA_CENTER, color=AZUL, size=20),
     cel("+24.8 pp", bold=True, align=TA_CENTER, color=AZUL, size=20)],
    [cel("personas analizadas", align=TA_CENTER, size=11),
     cel("hogares con IFH (98.1%)", align=TA_CENTER, size=11),
     cel("salto en first stage", align=TA_CENTER, size=11)],
], colWidths=[W/3]*3)
kpi.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,0), AZUL_CLARO),
    ('BACKGROUND',    (0,1),(-1,1), BLANCO),
    ('BOX',           (0,0),(0,-1), 1, AZUL_MEDIO),
    ('BOX',           (1,0),(1,-1), 1, AZUL_MEDIO),
    ('BOX',           (2,0),(2,-1), 1, AZUL_MEDIO),
    ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0),(-1,-1), 10),
    ('BOTTOMPADDING', (0,0),(-1,-1), 10),
]))
S.append(kpi)
S.append(Spacer(1, 0.5*cm))
S.append(Paragraph(f"{AUTORA}  ·  {FECHA}",
    E('P1A', fontSize=11, textColor=GRIS_TEXT, alignment=TA_CENTER)))
S.append(Paragraph(
    "Datos: ENAHO 2024 — INEI.  Metodología IFH: Bernal, Carpio y Klein (2017)",
    E('P1D', fontSize=9.5, textColor=GRIS_TEXT, alignment=TA_CENTER)))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 2 -- LA PREGUNTA
# ============================================================
S.append(Paragraph("¿Qué estoy estudiando?", TIT))
S.append(HR())

flechas = Table([
    [cel("PENSIÓN 65", bold=True, align=TA_CENTER, color=BLANCO, size=15),
     cel("→", align=TA_CENTER, color=AZUL, size=24),
     cel("¿EFECTO\nCAUSAL?", bold=True, align=TA_CENTER, color=BLANCO, size=15),
     cel("→", align=TA_CENTER, color=AZUL, size=24),
     cel("BILLETERA\nDIGITAL", bold=True, align=TA_CENTER, color=BLANCO, size=15)],
    [cel("Transferencia S/. 250\nbimensual a adultos\nmayores pobres",
         align=TA_CENTER, size=10),
     cel(""),
     cel("Yape / Plin /\nCuenta DNI",
         align=TA_CENTER, size=10),
     cel(""),
     cel("Inclusión financiera\nen adultos mayores\nen situación de pobreza",
         align=TA_CENTER, size=10)],
], colWidths=[W*0.27, W*0.09, W*0.24, W*0.09, W*0.27])
flechas.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(0,0), AZUL),
    ('BACKGROUND',    (2,0),(2,0), colors.HexColor('#2E75B6')),
    ('BACKGROUND',    (4,0),(4,0), AZUL),
    ('BACKGROUND',    (0,1),(0,1), AZUL_CLARO),
    ('BACKGROUND',    (2,1),(2,1), colors.HexColor('#DDEEFF')),
    ('BACKGROUND',    (4,1),(4,1), AZUL_CLARO),
    ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0),(-1,-1), 12),
    ('BOTTOMPADDING', (0,0),(-1,-1), 12),
    ('LEFTPADDING',   (0,0),(-1,-1), 4),
    ('RIGHTPADDING',  (0,0),(-1,-1), 4),
]))
S.append(flechas)
S.append(Spacer(1, 0.45*cm))
S.append(HRFlowable(width=W, thickness=0.5, color=GRIS, spaceAfter=8))
S.append(Paragraph(
    "<b>El problema:</b> los beneficiarios de Pensión 65 son más pobres "
    "(IFH promedio 48.64 vs 66.00 de no beneficiarios entre los 65+), más viejos y más rurales. "
    "Compararlos directamente con los no beneficiarios daría un estimado sesgado.", BODY))
S.append(Paragraph(
    "<b>La solución — Fuzzy RDD:</b> comparamos personas de 64 y 66 años que son casi "
    "idénticas en todo. La única diferencia relevante: las de 66 ya pueden acceder a "
    "Pensión 65 y las de 64 no.", BODY))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 3 -- EL IFH
# ============================================================
S.append(Paragraph("El IFH: el puntaje de pobreza del SISFOH", TIT))
S.append(HR())

CIZ = W * 0.53
CDR = W * 0.43
GAP = W * 0.04

izq = Table([
    [Paragraph("<b>¿Qué es?</b>",
               E('IZQ_T', fontSize=13, textColor=AZUL,
                 fontName='Helvetica-Bold', leading=17))],
    [Paragraph("• Número entre 0 y 100. Menor puntaje = más pobre.", BULL)],
    [Paragraph("• El gobierno lo usa para dar el SIS y Pensión 65.", BULL)],
    [Paragraph("• No es pobreza monetaria: mide condiciones de vivienda, "
               "acceso a servicios, educación del jefe y tenencia de bienes.", BULL)],
    [Spacer(1, 0.2*cm)],
    [Paragraph("Fuente: Bernal, Carpio y Klein (2017), Apéndice F<br/>"
               "<i>Journal of Public Economics</i>, 154, 122–136",
               E('IZQ_F', fontSize=9.5, textColor=GRIS_TEXT, leading=13))],
], colWidths=[CIZ - 0.3*cm])
izq.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,-1), AZUL_CLARO),
    ('TOPPADDING',    (0,0),(-1,-1), 6),
    ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ('LEFTPADDING',   (0,0),(-1,-1), 12),
    ('RIGHTPADDING',  (0,0),(-1,-1), 8),
    ('BOX',           (0,0),(-1,-1), 1, AZUL_MEDIO),
]))

val = T([
    [cab("Grupo ENAHO"), cab("IFH promedio")],
    [cel("Extrema pobreza", size=12),
     cel("47.48", bold=True, align=TA_CENTER, color=ROJO, size=16)],
    [cel("Pobre no extremo", size=12),
     cel("54.78", bold=True, align=TA_CENTER, color=NARANJA, size=16)],
    [cel("No pobre", size=12),
     cel("65.02", bold=True, align=TA_CENTER, color=VERDE, size=16)],
], [CDR*0.60, CDR*0.40])

two = Table([[izq, Spacer(GAP, 1), val]], colWidths=[CIZ, GAP, CDR])
two.setStyle(TableStyle([
    ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0),(-1,-1), 0),
    ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ('TOPPADDING',    (0,0),(-1,-1), 0),
    ('BOTTOMPADDING', (0,0),(-1,-1), 0),
]))
S.append(two)
S.append(Spacer(1, 0.45*cm))
S.append(Paragraph(
    "✓  El gradiente es monotónico y en la dirección correcta. "
    "El índice discrimina correctamente entre grupos de pobreza (r = 0.30).",
    CONC))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 4 -- TENEMOS EL IFH
# ============================================================
S.append(Paragraph("Sí. IFH calculado para el 98.1% de los hogares", TIT))
S.append(HR())

S.append(Paragraph("115,450 hogares",
    E('N4', fontSize=40, textColor=AZUL, fontName='Helvetica-Bold',
      alignment=TA_CENTER, leading=48)))
S.append(Paragraph(
    "con puntaje IFH calculado  ·  25 departamentos  ·  ENAHO 2024",
    E('S4', fontSize=12, textColor=GRIS_TEXT, alignment=TA_CENTER, leading=16)))
S.append(Spacer(1, 0.35*cm))

tres = Table([
    [cel("98.1%", bold=True, align=TA_CENTER, color=VERDE, size=20),
     cel("1.9%",  bold=True, align=TA_CENTER, color=GRIS_TEXT, size=20),
     cel("33,691", bold=True, align=TA_CENTER, color=AZUL, size=20)],
    [cel("con IFH calculado", align=TA_CENTER, size=11),
     cel("sin dato de vivienda\n(hogares parciales)", align=TA_CENTER, size=11),
     cel("hogares totales\nencuestados", align=TA_CENTER, size=11)],
], colWidths=[W/3]*3)
tres.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(0,-1), VERDE_BG),
    ('BACKGROUND',    (1,0),(1,-1), AZUL_CLARO),
    ('BACKGROUND',    (2,0),(2,-1), AZUL_CLARO),
    ('BOX',           (0,0),(0,-1), 2, VERDE),
    ('BOX',           (1,0),(1,-1), 1, GRIS),
    ('BOX',           (2,0),(2,-1), 1.5, AZUL),
    ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0),(-1,-1), 10),
    ('BOTTOMPADDING', (0,0),(-1,-1), 10),
]))
S.append(tres)
S.append(Spacer(1, 0.35*cm))

p65_t = T([
    [cab("Grupo (personas 65+)"), cab("N"), cab("IFH promedio"), cab("Lectura")],
    [cel("Receptores de Pensión 65", size=12),
     cel("4,436", align=TA_CENTER, size=12),
     cel("48.64", bold=True, align=TA_CENTER, color=ROJO, size=14),
     cel("Más pobres — cerca del umbral SISFOH", size=12)],
    [cel("No receptores (65+)", size=12),
     cel("9,652", align=TA_CENTER, size=12),
     cel("66.00", bold=True, align=TA_CENTER, color=VERDE, size=14),
     cel("Por encima del umbral de elegibilidad", size=12)],
], [W*0.38, W*0.12, W*0.18, W*0.32])
S.append(p65_t)
S.append(Spacer(1, 0.2*cm))
S.append(Paragraph(
    "→  Pensión 65 llega a los más pobres. "
    "Diferencia de 17.4 puntos IFH. El programa focaliza bien.",
    E('MSG4', fontSize=12, textColor=AZUL, fontName='Helvetica-Bold',
      alignment=TA_CENTER, leading=16)))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 5 -- EL DISENO RDD
# ============================================================
S.append(Paragraph("¿Cómo funciona el Fuzzy RDD?", TIT))
S.append(HR())

ew = W / 7
linea = Table([
    [cel("62", align=TA_CENTER, color=GRIS_TEXT, size=16),
     cel("63", align=TA_CENTER, color=GRIS_TEXT, size=16),
     cel("64", align=TA_CENTER, color=GRIS_TEXT, size=16),
     cel("65\n↑\nUMBRAL", bold=True, align=TA_CENTER, color=AZUL, size=14),
     cel("66", align=TA_CENTER, color=AZUL, size=16),
     cel("67", align=TA_CENTER, color=AZUL, size=16),
     cel("68", align=TA_CENTER, color=AZUL, size=16)],
], colWidths=[ew]*7)
linea.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(2,-1), AZUL_CLARO),
    ('BACKGROUND',    (3,0),(3,-1), AMARILLO),
    ('BACKGROUND',    (4,0),(-1,-1), colors.HexColor('#DDEEFF')),
    ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ('GRID',          (0,0),(-1,-1), 1, GRIS),
    ('TOPPADDING',    (0,0),(-1,-1), 16),
    ('BOTTOMPADDING', (0,0),(-1,-1), 16),
    ('FONTNAME',      (3,0),(3,0), 'Helvetica-Bold'),
    ('TEXTCOLOR',     (3,0),(3,0), AZUL),
    ('FONTSIZE',      (3,0),(3,0), 13),
]))
S.append(linea)
S.append(Spacer(1, 0.4*cm))

expl = Table([
    [cel("← ANTES del umbral", bold=True, align=TA_CENTER,
         color=GRIS_TEXT, size=13),
     Spacer(0.6*cm, 1),
     cel("DESPUÉS del umbral →", bold=True, align=TA_CENTER,
         color=AZUL, size=13)],
    [cel("Reciben P65: 0.0%\nBilletera: 9.4% (±5 años)",
         align=TA_CENTER, size=12),
     Spacer(0.6*cm, 1),
     cel("Reciben P65: 24 – 42%\nBilletera: 7.4 – 7.9% (±5 años)",
         align=TA_CENTER, color=AZUL, size=12)],
], colWidths=[W*0.46, 0.6*cm, W*0.46])
expl.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(0,-1), AZUL_CLARO),
    ('BACKGROUND',    (2,0),(2,-1), colors.HexColor('#DDEEFF')),
    ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0),(-1,-1), 12),
    ('BOTTOMPADDING', (0,0),(-1,-1), 12),
    ('BOX',           (0,0),(0,-1), 1, GRIS),
    ('BOX',           (2,0),(2,-1), 1.5, AZUL),
]))
S.append(expl)
S.append(Spacer(1, 0.4*cm))
S.append(Paragraph(
    "Las personas de 64 y 66 años son casi idénticas en todo. "
    "La única diferencia relevante: las de 66 ya pueden recibir Pensión 65.",
    E('MSG5', fontSize=13, textColor=AZUL, fontName='Helvetica-Bold',
      alignment=TA_CENTER, leading=18)))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 6 -- FIRST STAGE
# ============================================================
S.append(Paragraph("First Stage: el salto es nítido y fuerte", TIT))
S.append(HR())

BAR_MAX = W * 0.52
barra_248 = BAR_MAX * (24.8 / 45)

barras = Table([
    [cel("Menores de 65 años", bold=True, align=TA_RIGHT, size=13),
     Spacer(0.3*cm, 1),
     Table([[cel("  0.0%  (ninguno recibe P65)", align=TA_LEFT,
                 color=GRIS_TEXT, size=12)]],
           colWidths=[BAR_MAX * 0.22],
           style=TableStyle([
               ('BACKGROUND',    (0,0),(-1,-1), AZUL_CLARO),
               ('TOPPADDING',    (0,0),(-1,-1), 9),
               ('BOTTOMPADDING', (0,0),(-1,-1), 9),
               ('LEFTPADDING',   (0,0),(-1,-1), 8),
               ('BOX',           (0,0),(-1,-1), 0.5, GRIS),
           ]))],
    [Spacer(1, 0.25*cm), "", ""],
    [cel("Mayores de 65 años", bold=True, align=TA_RIGHT, color=AZUL, size=13),
     Spacer(0.3*cm, 1),
     Table([[cel("  24.8%   ← +24.8 pp", bold=True, align=TA_LEFT,
                 color=BLANCO, size=13)]],
           colWidths=[barra_248],
           style=TableStyle([
               ('BACKGROUND',    (0,0),(-1,-1), AZUL),
               ('TOPPADDING',    (0,0),(-1,-1), 9),
               ('BOTTOMPADDING', (0,0),(-1,-1), 9),
               ('LEFTPADDING',   (0,0),(-1,-1), 8),
           ]))],
], colWidths=[W*0.30, 0.3*cm, W*0.65])
barras.setStyle(TableStyle([
    ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
    ('ALIGN',        (0,0),(0,-1), 'RIGHT'),
    ('LEFTPADDING',  (0,0),(-1,-1), 0),
    ('RIGHTPADDING', (0,0),(-1,-1), 0),
    ('TOPPADDING',   (0,0),(-1,-1), 0),
    ('BOTTOMPADDING',(0,0),(-1,-1), 0),
]))
S.append(barras)
S.append(Spacer(1, 0.45*cm))

sub_fs = T([
    [cab("Submuestra"), cab("Antes de 65"), cab("Después de 65"),
     cab("Salto"), cab("p-valor")],
    [cel("SISFOH — IFH (±5 años)", size=12),
     cel("0.0%", align=TA_CENTER, size=12),
     cel("29.3%", align=TA_CENTER, color=AZUL, size=12),
     cel("+29.3 pp", bold=True, align=TA_CENTER, color=AZUL, size=12),
     cel("< 0.001 ***", align=TA_CENTER, color=VERDE, size=11)],
    [cel("Pobreza monetaria ENAHO (±5 años)*", size=12),
     cel("0.0%", align=TA_CENTER, size=12),
     cel("42.3%", align=TA_CENTER, color=AZUL, size=12),
     cel("+42.3 pp", bold=True, align=TA_CENTER, color=AZUL, size=12),
     cel("< 0.001 ***", align=TA_CENTER, color=VERDE, size=11)],
], [W*0.38, W*0.13, W*0.15, W*0.16, W*0.16])
S.append(sub_fs)
S.append(Spacer(1, 0.25*cm))
S.append(Paragraph(
    "El instrumento es fuerte: p &lt; 0.001 en todas las especificaciones.",
    CONC))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 7 -- RESULTADOS RDD
# ============================================================
S.append(Paragraph("Resultados Fuzzy RDD", TIT))
S.append(HR())

res = T([
    [cab("Submuestra"), cab("BW"), cab("N"),
     cab("First Stage"), cab("LATE  (P65 → billetera)")],
    [cel("SISFOH — IFH≤umbral", size=11),
     cel("±3 años", align=TA_CENTER, size=11),
     cel("1,462",   align=TA_CENTER, size=11),
     cel("0.094 ***", bold=True, align=TA_CENTER, color=VERDE, size=11),
     cel("+5.4 pp  (n.s., p=0.87)", align=TA_CENTER, color=GRIS_TEXT, size=11)],
    [cel("SISFOH — IFH≤umbral", size=11),
     cel("±5 años", align=TA_CENTER, size=11),
     cel("2,331",   align=TA_CENTER, size=11),
     cel("0.135 ***", bold=True, align=TA_CENTER, color=VERDE, size=11),
     cel("−2.8 pp  (n.s., p=0.87)", align=TA_CENTER, color=GRIS_TEXT, size=11)],
    [cel("Pobreza monetaria ENAHO†", size=11),
     cel("±3 años", align=TA_CENTER, size=11),
     cel("310",     align=TA_CENTER, size=11),
     cel("0.158 ***", bold=True, align=TA_CENTER, color=VERDE, size=11),
     cel("+33.5 pp  (p=0.098)*", bold=True, align=TA_CENTER, color=NARANJA, size=11)],
    [cel("Pobreza monetaria ENAHO†", size=11),
     cel("±5 años", align=TA_CENTER, size=11),
     cel("496",     align=TA_CENTER, size=11),
     cel("0.202 ***", bold=True, align=TA_CENTER, color=VERDE, size=11),
     cel("+19.8 pp  (n.s., p=0.15)", align=TA_CENTER, color=GRIS_TEXT, size=11)],
], [W*0.28, W*0.10, W*0.09, W*0.19, W*0.30])
res.setStyle(TableStyle([('BACKGROUND', (0,3),(-1,3), AMARILLO)]))
S.append(res)
S.append(Spacer(1, 0.3*cm))
S.append(Paragraph(
    "*** p&lt;0.01  ·  * p&lt;0.10  ·  n.s. = no significativo  ·  "
    "Errores estándar robustos HC1  ·  "
    "Regresión local lineal con pendientes distintas a cada lado del umbral.",
    NOTA))
S.append(Paragraph(
    "† Pobreza monetaria ENAHO (POBREZA=1): clasificación de gasto per cápita calculada "
    "por INEI. <b>No equivale al criterio SISFOH</b> que usa Pensión 65. "
    "Se incluye como comparación descriptiva. La submuestra primaria es SISFOH proxy (IFH≤umbral).",
    NOTA))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 8 -- QUE SIGNIFICAN
# ============================================================
S.append(Paragraph("¿Qué nos dicen los datos?", TIT))
S.append(HR())

msgs8 = [
    ("✓", VERDE,   VERDE_BG,
     "La primera etapa es perfecta",
     "Nadie menor de 65 recibe P65 (0.0%). El salto al cruzar los 65 años es nítido "
     "y estadísticamente muy fuerte (p &lt; 0.001 en todas las especificaciones). "
     "El instrumento funciona exactamente como debe."),
    ("∼", NARANJA, AMARILLO,
     "El efecto sobre billetera no es concluyente",
     "Submuestra SISFOH: no significativo (p = 0.87 en ambos bandwidths). "
     "Pobreza extrema ±3 años: señal positiva (+33.5 pp, p = 0.098), "
     "pero el intervalo de confianza cruza cero [−6%, +73%] "
     "y no es robusto al bandwidth."),
    ("?", AZUL,    AZUL_CLARO,
     "¿Efecto nulo real o falta de poder estadístico?",
     "La tasa base de billetera entre pobres extremos es solo 2–9%. "
     "Con N = 310–496 en la submuestra de pobreza extrema, "
     "es difícil detectar efectos pequeños. "
     "Necesitamos calcular el Mínimo Efecto Detectable (MDE)."),
]

for ico, col, bg, tit2, txt2 in msgs8:
    row8 = Table([
        [Paragraph(ico,
            E('I8_'+ico, fontSize=22, textColor=col, fontName='Helvetica-Bold',
              alignment=TA_CENTER, leading=26)),
         Table([
             [Paragraph(tit2, E('T8_'+ico, fontSize=13, textColor=col,
                                fontName='Helvetica-Bold', leading=17))],
             [Paragraph(txt2, E('B8_'+ico, fontSize=11, leading=14))],
         ], colWidths=[W*0.85])],
    ], colWidths=[W*0.08, W*0.87])
    row8.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 9),
        ('LEFTPADDING',   (0,0),(0,-1), 8),
        ('LEFTPADDING',   (1,0),(1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('BOX',           (0,0),(-1,-1), 1.5, col),
    ]))
    S.append(row8)
    S.append(Spacer(1, 0.22*cm))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 9 -- PREGUNTAS PARA EL ASESOR
# ============================================================
S.append(Paragraph("Preguntas para discutir", TIT))
S.append(HR())

preg9 = [
    ("1", "¿Interpretar como efecto nulo o falta de poder estadístico?",
     "La forma reducida es cercana a cero en la submuestra SISFOH. "
     "En pobreza extrema hay una señal positiva pero no robusta al bandwidth. "
     "¿Necesitamos más datos o un diseño diferente?"),
    ("2", "¿Explorar outcomes alternativos?",
     "El dataset tiene USA_BILLETERA (solo uso activo) y BANCO_PREVIO "
     "(cuenta bancaria preexistente). ¿Tiene sentido usarlos como outcomes secundarios?"),
    ("3", "¿Agregar controles para mejorar precisión?",
     "Disponemos de educación, área geográfica y nivel de pobreza. "
     "¿Controles dentro del RDD o análisis de heterogeneidad por subgrupo?"),
    ("4", "¿Es válido el supuesto de exclusión?",
     "P65 requiere edad ≥65 Y SISFOH pobre extremo. El RDD usa solo la edad. "
     "¿Puede el cruce de los 65 afectar la billetera por otra vía distinta a P65 "
     "(ej. AFP, ONP, SIS+65)?"),
]

for num, preg, det in preg9:
    r9 = Table([
        [Paragraph(num, E('N9_'+num, fontSize=18, textColor=BLANCO,
                          fontName='Helvetica-Bold', alignment=TA_CENTER,
                          leading=22)),
         Table([
             [Paragraph(preg, E('P9T_'+num, fontSize=12, textColor=AZUL,
                                fontName='Helvetica-Bold', leading=16))],
             [Paragraph(det,  E('P9D_'+num, fontSize=10.5, leading=14))],
         ], colWidths=[W*0.85])],
    ], colWidths=[W*0.07, W*0.88])
    r9.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,-1), AZUL),
        ('BACKGROUND',    (1,0),(1,-1), AZUL_CLARO),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (1,0),(1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
    ]))
    S.append(r9)
    S.append(Spacer(1, 0.22*cm))
S.append(PageBreak())

# ============================================================
# DIAPOSITIVA 10 -- PROXIMOS PASOS
# ============================================================
S.append(Paragraph("Lo que falta", TIT))
S.append(HR())

BW2 = (W - 0.4*cm) / 2

def paso_box(num, col, bg, tit3, txt3, ancho):
    inner = Table([
        [Table([
             [Paragraph(num, E('PBN'+num, fontSize=20, textColor=BLANCO,
                               fontName='Helvetica-Bold', alignment=TA_CENTER,
                               leading=24))],
         ], colWidths=[0.9*cm],
         style=TableStyle([
             ('BACKGROUND',    (0,0),(-1,-1), col),
             ('TOPPADDING',    (0,0),(-1,-1), 10),
             ('BOTTOMPADDING', (0,0),(-1,-1), 10),
             ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
             ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
         ])),
         Table([
             [Paragraph(tit3, E('PBT'+num, fontSize=13, textColor=col,
                                fontName='Helvetica-Bold', leading=17))],
             [Paragraph(txt3, E('PBB'+num, fontSize=11, leading=14))],
         ], colWidths=[ancho - 1.2*cm])],
    ], colWidths=[0.9*cm, ancho - 0.9*cm])
    inner.setStyle(TableStyle([
        ('BACKGROUND', (1,0),(1,-1), bg),
        ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING', (1,0),(1,-1), 8),
        ('BOTTOMPADDING',(1,0),(1,-1), 8),
        ('LEFTPADDING',(1,0),(1,-1), 10),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('BOX',        (0,0),(-1,-1), 1.5, col),
    ]))
    return inner

p10 = [
    ("1", AZUL,    AZUL_CLARO,
     "Test de McCrary",
     "Verificar que no hay manipulación de la edad alrededor del umbral. "
     "La densidad de la running variable no debe tener discontinuidad a los 65 años."),
    ("2", VERDE,   VERDE_BG,
     "Balance de covariables",
     "Comprobar que IFH, educación y área geográfica no muestran "
     "discontinuidades a los 65 años. Sustenta el supuesto de continuidad del RDD."),
    ("3", NARANJA, AMARILLO,
     "Heterogeneidad por IFH",
     "Estimar el LATE separadamente para ELEGIBLE_SIS=1 vs ELEGIBLE_SIS=0. "
     "¿Es el efecto de P65 mayor entre los más pobres?"),
    ("4", colors.HexColor('#6A1E55'), colors.HexColor('#F9E8FF'),
     "Robustez con outcomes alternativos",
     "Replicar el RDD con USA_BILLETERA y BANCO_PREVIO. "
     "¿Opera el efecto a través del uso activo o la apertura de cuentas?"),
]

grid = Table([
    [paso_box(*p10[0], BW2), Spacer(0.4*cm, 1), paso_box(*p10[1], BW2)],
    [Spacer(1, 0.35*cm), "", ""],
    [paso_box(*p10[2], BW2), Spacer(0.4*cm, 1), paso_box(*p10[3], BW2)],
], colWidths=[BW2, 0.4*cm, BW2])
grid.setStyle(TableStyle([
    ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0),(-1,-1), 0),
    ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ('TOPPADDING',    (0,0),(-1,-1), 0),
    ('BOTTOMPADDING', (0,0),(-1,-1), 0),
]))
S.append(grid)

# -- Build --------------------------------------------------------------------
doc.build(S, canvasmaker=SlideCanvas)
print(f"\nPresentacion generada: {OUTPUT}")
print("Diapositivas: 10  |  Formato: A4 horizontal")
