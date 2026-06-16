"""
Genera documentacion_ifh_2024.pdf — versión completa (IFH + diseño RDD).
Números verificados en Paso 1. NO inventar ningún número.
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

# ── Colores ──────────────────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor('#1F4E79')
AZUL_CLARO   = colors.HexColor('#F2F7FB')
AZUL_MEDIO   = colors.HexColor('#BDD7EE')
GRIS_LINEA   = colors.HexColor('#D0D0D0')
BLANCO       = colors.white
NEGRO        = colors.black
ROJO         = colors.HexColor('#C00000')
VERDE_OSC    = colors.HexColor('#1F7A1F')

# ── Números verificados (Paso 1) ─────────────────────────────────────────────
N_PERSONAS        = 117_721
N_HOGARES         = 33_691
N_DPTOS           = 25
N_IFH_OK          = 115_450
N_IFH_NULOS       = 2_271
PCT_IFH_OK        = 98.1
PCT_IFH_NULL      = 1.9
IFH_MEDIA         = 62.013
IFH_STD           = 18.051
IFH_MEDIANA       = 62.667
IFH_P25           = 50.056
IFH_P75           = 75.610
IFH_MIN           = 0.0
IFH_MAX           = 100.0
IFH_RAW_MEDIA     = 1.056
IFH_RAW_STD       = 1.434
IFH_RAW_MIN       = -5.200
IFH_RAW_MAX       = 4.810
IFH_POB1          = 47.48
IFH_POB2          = 54.78
IFH_POB3          = 65.02
CORR_POB          = 0.2986
ELEG_IFH          = 24_273
ELEG_IFH_PCT      = 20.6
ELEG_AGUA         = 48_681
ELEG_AGUA_PCT     = 41.4
ELEG_ELECTR       = 117_464
ELEG_ELEC_PCT     = 99.8
ELEG_SIS          = 12_604
ELEG_SIS_PCT      = 10.7
N_RURAL           = 60_640
N_URBANO          = 42_986
N_LIMA            = 14_095
N_65MAS           = 14_088
N_P65_65MAS       = 4_436
PCT_P65_65MAS     = 32.2
N_BILL_65MAS      = 1_107
PCT_BILL_65MAS    = 7.9
N_POB1_65MAS      = 758
N_POB2_65MAS      = 2_182
N_POB3_65MAS      = 11_148
FS_MENOR65        = 0.0
FS_MAYOR65        = 24.8
FS_SALTO          = 24.8
N_REC_P65         = 4_436
N_NO_REC_65       = 9_652
IFH_REC           = 48.64
IFH_NOREC         = 66.00
IFH_DIFF          = 17.4
V5_N              = 10_889
V5_BILL_MEN       = 17.1
V5_BILL_MAY       = 12.2
V5_N_BILL         = 1_596
V5_N_P65          = 973
V10_N             = 20_493
V10_BILL_MEN      = 19.5
V10_BILL_MAY      = 10.6
V10_N_BILL        = 3_211
V10_N_P65         = 2_126
V15_N             = 29_668
V15_BILL_MEN      = 22.2
V15_BILL_MAY      = 9.3
V15_N_BILL        = 5_151
V15_N_P65         = 3_120

FECHA = "14 de junio de 2026"
OUTPUT = "data/clean/documentacion_ifh_2024.pdf"

# ── Numeración de páginas ─────────────────────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page = self._pageNumber
        if page <= 2:
            return
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor('#555555'))
        self.drawCentredString(A4[0]/2, 1.4*cm, f"{page} de {page_count}")
        self.setStrokeColor(GRIS_LINEA)
        self.setLineWidth(0.5)
        self.line(2.5*cm, 1.8*cm, A4[0]-2.5*cm, 1.8*cm)

# ── Estilos ───────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def E(nombre, padre='Normal', **kw):
    return ParagraphStyle(nombre, parent=styles[padre], **kw)

TITULO_PORT = E('TP', fontSize=20, textColor=BLANCO,
                alignment=TA_CENTER, leading=26, spaceBefore=0)
SUBT_PORT   = E('SP', fontSize=13, textColor=AZUL_CLARO,
                alignment=TA_CENTER, spaceAfter=6)
FECHA_PORT  = E('FP', fontSize=10, textColor=AZUL_CLARO,
                alignment=TA_CENTER)
SEC_TIT     = E('ST', 'Heading1', fontSize=13, textColor=AZUL_OSCURO,
                spaceBefore=14, spaceAfter=6, leading=16)
SEC_SUB     = E('SS', 'Heading2', fontSize=10.5, textColor=AZUL_OSCURO,
                spaceBefore=9, spaceAfter=5, leading=13)
CUERPO      = E('CB', fontSize=10, leading=15, spaceAfter=6,
                alignment=TA_JUSTIFY)
BULLET      = E('BL', fontSize=10, leading=14, spaceAfter=4,
                leftIndent=16, bulletIndent=4, alignment=TA_JUSTIFY)
NOTA        = E('NT', fontSize=8.5, textColor=colors.HexColor('#555555'),
                leading=12, spaceAfter=4, alignment=TA_JUSTIFY)
RESP        = E('RS', fontSize=12, textColor=AZUL_OSCURO, leading=17,
                spaceBefore=6, spaceAfter=6, alignment=TA_CENTER)

def cab(txt):
    return Paragraph(f"<b>{txt}</b>",
        E('HC', fontSize=9, textColor=BLANCO, alignment=TA_CENTER, leading=12))

def cel(txt, bold=False, align=TA_LEFT, color=NEGRO, size=9):
    b, e = ('<b>', '</b>') if bold else ('', '')
    return Paragraph(f"{b}{txt}{e}",
        E('CC', fontSize=size, alignment=align, textColor=color, leading=12))

def tabla(data, cw, hdr=1):
    t = Table(data, colWidths=cw, repeatRows=hdr)
    cmds = [
        ('BACKGROUND',   (0,0),(-1,hdr-1), AZUL_OSCURO),
        ('TEXTCOLOR',    (0,0),(-1,hdr-1), BLANCO),
        ('FONTNAME',     (0,0),(-1,hdr-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0),(-1,-1), 9),
        ('ALIGN',        (0,0),(-1,-1), 'LEFT'),
        ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
        ('ROWBACKGROUND',(0,hdr),(-1,-1), [AZUL_CLARO, BLANCO]),
        ('GRID',         (0,0),(-1,-1), 0.4, GRIS_LINEA),
        ('LEFTPADDING',  (0,0),(-1,-1), 6),
        ('RIGHTPADDING', (0,0),(-1,-1), 6),
        ('TOPPADDING',   (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]
    t.setStyle(TableStyle(cmds))
    return t

def hr():
    return HRFlowable(width=W, thickness=1.5, color=AZUL_OSCURO, spaceAfter=8)

def sec(n, titulo):
    story.append(Paragraph(f"{n}. {titulo}", SEC_TIT))
    story.append(hr())

def sub(titulo):
    story.append(Paragraph(titulo, SEC_SUB))

# ── Documento ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2.5*cm, rightMargin=2.5*cm,
    topMargin=2.5*cm,  bottomMargin=2.5*cm,
    title="IFH, Pensión 65 y billetera digital — documentación de avance",
    author="Cecilia Vargas Risco",
)
story = []
W = A4[0] - 5*cm

# ══════════════════════════════════════════════════════════════════════════════
# PORTADA
# ══════════════════════════════════════════════════════════════════════════════
port = Table([
    [Paragraph("<br/><br/>", TITULO_PORT)],
    [Paragraph(
        "<b>IFH, Pensión 65 y billetera digital:<br/>"
        "construcción del índice y diseño empírico</b>",
        E('TP2', fontSize=20, textColor=BLANCO, alignment=TA_CENTER,
          leading=27, spaceBefore=0))],
    [Spacer(1, 0.5*cm)],
    [Paragraph("Documentación de avance de tesis", SUBT_PORT)],
    [Spacer(1, 1.2*cm)],
    [Paragraph("Cecilia Vargas Risco", E('TP3', fontSize=12, textColor=BLANCO,
               alignment=TA_CENTER))],
    [Paragraph(FECHA, FECHA_PORT)],
    [Spacer(1, 1.5*cm)],
    [Paragraph(
        "Datos: ENAHO 2024 — INEI (Encuesta 966)<br/>"
        "Metodología IFH: Bernal, Carpio y Klein (2017), Apéndice F",
        E('TP4', fontSize=9.5, textColor=AZUL_CLARO, alignment=TA_CENTER,
          leading=14))],
    [Spacer(1, 0.5*cm)],
], colWidths=[W])
port.setStyle(TableStyle([
    ('BACKGROUND',   (0,0),(-1,-1), AZUL_OSCURO),
    ('TOPPADDING',   (0,0),(-1,-1), 3),
    ('BOTTOMPADDING',(0,0),(-1,-1), 3),
    ('LEFTPADDING',  (0,0),(-1,-1), 1*cm),
    ('RIGHTPADDING', (0,0),(-1,-1), 1*cm),
]))
story.append(port)
story.append(Spacer(1, 0.8*cm))

# Recuadro cifras clave en portada
cport = [
    [cab("Personas analizadas"), cab("Hogares con IFH"),
     cab("Receptores P65 (65+)"), cab("First stage")],
    [cel(f"{N_PERSONAS:,}", bold=True, align=TA_CENTER,
         color=AZUL_OSCURO, size=13),
     cel(f"{N_IFH_OK:,}", bold=True, align=TA_CENTER,
         color=AZUL_OSCURO, size=13),
     cel(f"{N_P65_65MAS:,}", bold=True, align=TA_CENTER,
         color=AZUL_OSCURO, size=13),
     cel(f"+{FS_SALTO} pp", bold=True, align=TA_CENTER,
         color=AZUL_OSCURO, size=13)],
    [cel(f"en {N_HOGARES:,} hogares", align=TA_CENTER, size=8),
     cel(f"({PCT_IFH_OK}% de la muestra)", align=TA_CENTER, size=8),
     cel(f"({PCT_P65_65MAS}% de los 65+)", align=TA_CENTER, size=8),
     cel("salto en umbral de 65 años", align=TA_CENTER, size=8)],
]
tc = Table(cport, colWidths=[W/4]*4)
tc.setStyle(TableStyle([
    ('BACKGROUND',   (0,0),(-1,0), AZUL_OSCURO),
    ('BACKGROUND',   (0,1),(-1,1), AZUL_CLARO),
    ('BACKGROUND',   (0,2),(-1,2), BLANCO),
    ('GRID',         (0,0),(-1,-1), 0.5, AZUL_MEDIO),
    ('ALIGN',        (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
    ('TOPPADDING',   (0,0),(-1,-1), 7),
    ('BOTTOMPADDING',(0,0),(-1,-1), 7),
]))
story.append(tc)
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# ÍNDICE
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("Contenido", SEC_TIT))
story.append(hr())
toc_items = [
    ("1.", "La pregunta de investigación"),
    ("2.", "El diseño Fuzzy RDD"),
    ("   2.1", "¿Qué es un Fuzzy RDD?"),
    ("   2.2", "Los componentes del diseño"),
    ("   2.3", "El patrón observado en el outcome"),
    ("   2.4", "El papel del IFH en el diseño"),
    ("3.", "¿Qué es el IFH?"),
    ("4.", "Cómo construimos el IFH"),
    ("   4.1", "Los datos: ENAHO 2024"),
    ("   4.2", "Auditoría de variables"),
    ("   4.3", "Los tres pasos de construcción"),
    ("   4.4", "Cinco decisiones metodológicas"),
    ("5.", "Resultados: ¿tenemos el IFH?"),
    ("6.", "Elegibilidad SISFOH replicada"),
    ("7.", "Conexión IFH y Pensión 65"),
    ("8.", "Limitaciones"),
    ("9.", "Próximos pasos"),
    ("10.", "Referencias"),
]
for num, titulo in toc_items:
    es_sub = num.startswith(" ")
    story.append(Paragraph(
        f"{num}&nbsp;&nbsp;&nbsp;{titulo}",
        E('TL2', fontSize=10 if not es_sub else 9,
          leading=16, leftIndent=12 if es_sub else 0,
          textColor=AZUL_OSCURO if not es_sub else NEGRO,
          fontName='Helvetica-Bold' if not es_sub else 'Helvetica')))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — La pregunta de investigación
# ══════════════════════════════════════════════════════════════════════════════
sec(1, "La pregunta de investigación")

story.append(Paragraph(
    "Esta tesis pregunta si <b>recibir Pensión 65 aumenta la probabilidad de que "
    "un adulto mayor pobre adopte una billetera digital</b> (Yape, Plin o Cuenta DNI) "
    "en el Perú. Pensión 65 es el programa de transferencias monetarias del gobierno "
    "peruano para personas mayores de 65 años en condición de pobreza extrema. Desde "
    "2021, el pago de S/. 250 bimensuales se hace a través de cuentas bancarias o "
    "billeteras digitales, lo que crea un vínculo directo entre la recepción del "
    "beneficio y la inclusión financiera.", CUERPO))

story.append(Paragraph(
    "El problema de identificación causal es que los beneficiarios de Pensión 65 "
    "son sistemáticamente distintos de los no beneficiarios. En la ENAHO 2024, "
    "los receptores de Pensión 65 entre los mayores de 65 años tienen un IFH "
    f"promedio de <b>{IFH_REC}</b>, significativamente por debajo del IFH promedio "
    f"de los no receptores (<b>{IFH_NOREC}</b>), lo que confirma que el programa llega "
    "a hogares más pobres. Pero eso también significa que comparar directamente "
    "receptores con no receptores daría un estimado sesgado del efecto del programa: "
    "los receptores adoptan menos la billetera no porque la pensión no sirva, sino "
    "porque son más pobres, más rurales y tienen menor educación.", CUERPO))

story.append(Paragraph(
    "La solución es un <b>Fuzzy RDD</b> (Regression Discontinuity Design difuso). "
    "La idea intuitiva es comparar personas de 64 y 66 años que son casi idénticas "
    "en todo — misma condición socioeconómica, misma región, misma historia "
    "de vida — pero se diferencian en que las de 66 ya cruzaron el umbral de "
    "elegibilidad de Pensión 65 y las de 64 todavía no. Si se observa un salto "
    "en la adopción de billetera justo en los 65 años que no puede explicarse "
    "por la tendencia de edad, ese salto es atribuible al efecto del programa.",
    CUERPO))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — El diseño Fuzzy RDD
# ══════════════════════════════════════════════════════════════════════════════
sec(2, "El diseño Fuzzy RDD")

sub("2.1 ¿Qué es un Fuzzy RDD?")
story.append(Paragraph(
    "Un <b>Regression Discontinuity Design (RDD)</b> aprovecha que muchos programas "
    "sociales tienen una <i>regla de corte arbitraria</i>: quien supera el umbral "
    "recibe el beneficio; quien no lo supera, no. Justo alrededor del umbral, quienes "
    "están justo por encima y justo por debajo son casi indistinguibles. La única "
    "diferencia relevante es que los de un lado cumplen la regla y los del otro no. "
    "Eso es lo que hace al diseño creíble como estrategia de identificación causal.", CUERPO))

story.append(Paragraph(
    "El diseño es <b>«Fuzzy» (difuso)</b> cuando cruzar el umbral no garantiza "
    "recibir el tratamiento, sino que solo aumenta la probabilidad de recibirlo. "
    "En el caso de Pensión 65, tener 65 años o más es necesario pero no suficiente: "
    "también se requiere ser clasificado como pobre extremo por el SISFOH. "
    "En los datos, esto se verifica: entre los menores de 65 la tasa de recepción "
    f"de Pensión 65 es exactamente <b>{FS_MENOR65}%</b>, mientras que entre los "
    f"mayores de 65 es <b>{FS_MAYOR65}%</b>. El salto de <b>{FS_SALTO} puntos "
    "porcentuales</b> en el umbral es el «primer estadio» del diseño.", CUERPO))

sub("2.2 Los componentes del diseño")

comp = [
    [cab("Componente"), cab("Variable"), cab("Descripción")],
    [cel("Running variable", bold=True), cel("EDAD"),
     cel("Edad en años. Umbral = 65.")],
    [cel("Tratamiento endógeno", bold=True), cel("RECIBE_P65_PERSONA (P5567A)"),
     cel("=1 si la persona reporta recibir Pensión 65 en el módulo de empleo de la ENAHO.")],
    [cel("Instrumento", bold=True), cel("1(EDAD ≥ 65)"),
     cel("Indicador de haber cruzado el umbral de edad. Genera el salto en la "
         "probabilidad de recepción, pero no afecta directamente a la billetera "
         "por ninguna otra vía (supuesto de exclusión).")],
    [cel("Outcome", bold=True), cel("TIENE_BILLETERA"),
     cel("=1 si la persona tiene O usa una billetera digital (Yape, Plin o Cuenta DNI). "
         "Combina tenencia (P558E1_9) y uso activo (P558Hk_7, k=1..12).")],
]
story.append(tabla(comp, [3.5*cm, 4*cm, W-7.5*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("Primer estadio (First Stage):", SEC_SUB))
story.append(Paragraph(
    "El salto en la recepción de Pensión 65 al cruzar los 65 años es nítido y "
    "grande, confirmando que el instrumento es poderoso:", CUERPO))

fs_data = [
    [cab("Grupo de edad"), cab("Observaciones"), cab("% recibe P65"),
     cab("Interpretación")],
    [cel("55 a 64 años (debajo del umbral)"),
     cel("—"),
     cel(f"{FS_MENOR65}%", bold=True, color=ROJO),
     cel("Ninguno recibe Pensión 65 antes de los 65")],
    [cel("65 a 75 años (sobre el umbral)"),
     cel(f"{N_P65_65MAS:,} receptores en los 65+"),
     cel(f"{FS_MAYOR65}%", bold=True, color=VERDE_OSC),
     cel("Salto discreto al cruzar la edad de elegibilidad")],
    [cel("Salto en el umbral (first stage)", bold=True),
     cel("—"),
     cel(f"+{FS_SALTO} pp", bold=True, color=AZUL_OSCURO),
     cel("Efecto causal de cruzar los 65 sobre la recepción del beneficio")],
]
story.append(tabla(fs_data, [5*cm, 4*cm, 2.5*cm, W-11.5*cm]))
story.append(Spacer(1, 0.3*cm))

sub("2.3 El patrón observado en el outcome")
story.append(Paragraph(
    f"La tasa de adopción de billetera digital entre los mayores de 65 años es "
    f"<b>{PCT_BILL_65MAS}%</b> ({N_BILL_65MAS:,} personas). Esto contrasta con "
    "tasas más altas entre los grupos de edad menores, lo que refleja la brecha "
    "digital generacional. La siguiente tabla muestra el patrón por ventana "
    "de bandwidth alrededor del umbral de 65:", CUERPO))

bill_data = [
    [cab("Ventana"), cab("N total"), cab("Billetera < 65"),
     cab("Billetera ≥ 65"), cab("N billetera"), cab("N recibe P65")],
    [cel("±5 años"),
     cel(f"{V5_N:,}"),
     cel(f"{V5_BILL_MEN}%"),
     cel(f"{V5_BILL_MAY}%"),
     cel(f"{V5_N_BILL:,}"),
     cel(f"{V5_N_P65:,}")],
    [cel("±10 años"),
     cel(f"{V10_N:,}"),
     cel(f"{V10_BILL_MEN}%"),
     cel(f"{V10_BILL_MAY}%"),
     cel(f"{V10_N_BILL:,}"),
     cel(f"{V10_N_P65:,}")],
    [cel("±15 años"),
     cel(f"{V15_N:,}"),
     cel(f"{V15_BILL_MEN}%"),
     cel(f"{V15_BILL_MAY}%"),
     cel(f"{V15_N_BILL:,}"),
     cel(f"{V15_N_P65:,}")],
]
story.append(tabla(bill_data, [2*cm, 2.2*cm, 3.2*cm, 3.2*cm, 2.5*cm, 2.9*cm]))
story.append(Paragraph(
    "La caída en la tasa de billetera al cruzar los 65 refleja la tendencia natural "
    "de menor adopción digital entre adultos mayores. El objetivo del Fuzzy RDD es "
    "aislar, dentro de esa tendencia, el efecto específico de recibir Pensión 65 "
    "sobre la adopción de billetera.", NOTA))
story.append(Spacer(1, 0.3*cm))

sub("2.4 El papel del IFH en el diseño")
story.append(Paragraph(
    "El diseño RDD usa la edad como única running variable. El IFH cumple tres "
    "funciones complementarias:", CUERPO))
for b in [
    f"<b>(1) Caracterización de la muestra:</b> el IFH permite describir el perfil "
    f"de pobreza de quienes están cerca del umbral de edad. El IFH promedio de los "
    f"receptores de Pensión 65 entre los 65+ es {IFH_REC}, frente a {IFH_NOREC} de "
    f"los no receptores — diferencia de {IFH_DIFF} puntos.",
    "<b>(2) Verificación de focalización:</b> el gradiente de IFH confirma que el "
    "programa llega a los más pobres dentro del grupo de elegibles por edad, lo que "
    "valida el primer estadio en términos sustantivos.",
    "<b>(3) Análisis de heterogeneidad:</b> una vez estimado el efecto promedio, "
    "se puede preguntar si el efecto de Pensión 65 sobre la adopción de billetera "
    "es mayor entre los hogares con IFH más bajo (más pobres, para quienes la "
    "pensión puede ser más determinante de la inclusión financiera).",
]:
    story.append(Paragraph(b, BULLET))

story.append(Paragraph(
    "<b>Nota sobre POBREZA vs. SISFOH:</b> La variable POBREZA de la ENAHO mide "
    "pobreza <i>monetaria</i> (gasto per cápita vs. línea de pobreza INEI), no la "
    "clasificación SISFOH que usa Pensión 65. El análisis primario usa la muestra "
    "completa sin restricción por POBREZA. El IFH es el proxy correcto para aproximar "
    "la elegibilidad SISFOH.", NOTA))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — ¿Qué es el IFH?
# ══════════════════════════════════════════════════════════════════════════════
sec(3, "¿Qué es el IFH?")

story.append(Paragraph(
    "El <b>SISFOH</b> (Sistema de Focalización de Hogares) es el mecanismo del "
    "Estado peruano para determinar qué hogares son suficientemente pobres para "
    "recibir beneficios sociales. Para cada hogar, el SISFOH calcula el "
    "<b>Índice de Focalización de Hogares (IFH)</b>: un puntaje numérico donde "
    "un valor bajo indica mayor pobreza y un valor alto indica mejor situación "
    "socioeconómica. Los programas sociales — entre ellos Pensión 65 y el "
    "Seguro Integral de Salud (SIS) — comparan el IFH de cada hogar con un "
    "umbral para decidir quiénes son elegibles.", CUERPO))

story.append(Paragraph(
    "<b>Por qué lo construimos:</b> el puntaje IFH oficial del MIDIS no es "
    "público. Los investigadores que estudian programas focalizados por el SISFOH "
    "con datos ENAHO construyen una réplica del índice a partir de las variables "
    "de vivienda y bienestar disponibles en la encuesta. La réplica permite "
    "aproximar la elegibilidad SISFOH de cada hogar sin necesitar acceso a la "
    "base de datos administrativa.", CUERPO))

story.append(Paragraph(
    "<b>Fuente metodológica:</b> seguimos el <b>Apéndice F</b> de Bernal, Carpio "
    "y Klein (2017), «<i>The effects of access to health insurance: Evidence from "
    "a regression discontinuity design in Peru</i>» (<i>Journal of Public "
    "Economics</i>, 154, 122–136). Es el único trabajo académico que publica los "
    "pesos numéricos del IFH tal como los calcula el MIDIS, basándose en "
    "microdatos del SISFOH que los autores obtuvieron directamente del gobierno "
    "peruano. Las Tablas A.8 y A.9 contienen los pesos por variable y área "
    "geográfica; la Tabla A.10, los umbrales de elegibilidad por departamento.",
    CUERPO))

story.append(Paragraph(
    "A diferencia de la pobreza monetaria, el IFH se basa en características "
    "<i>estructurales y observables</i> del hogar: materiales de la vivienda, "
    "acceso a servicios básicos, nivel educativo del jefe, tenencia de bienes "
    "durables y cobertura de seguro de salud. Estas características cambian "
    "lentamente y son más difíciles de manipular que el ingreso o gasto corriente.",
    CUERPO))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — Cómo construimos el IFH
# ══════════════════════════════════════════════════════════════════════════════
sec(4, "Cómo construimos el IFH")

sub("4.1 Los datos: ENAHO 2024")
story.append(Paragraph(
    f"La <b>Encuesta Nacional de Hogares (ENAHO) 2024</b> (código 966, INEI) "
    f"cubre los {N_DPTOS} departamentos del Perú. Analizamos <b>{N_PERSONAS:,} "
    f"personas</b> en <b>{N_HOGARES:,} hogares</b>. La construcción del IFH "
    f"requirió siete módulos:", CUERPO))

mod_data = [
    [cab("Módulo"), cab("Nombre"), cab("Aporte al IFH")],
    [cel("100 (M01)"), cel("Características de la vivienda"),
     cel("Techo (P101), paredes (P102), piso (P103), agua (P110), "
         "desagüe (P111A), electricidad (P112A), combustible (P113A), cuartos (P104)")],
    [cel("200 (M02)"), cel("Características del hogar"),
     cel("Número de miembros del hogar (MIEPERHO) para cálculo de hacinamiento")],
    [cel("300 (M03)"), cel("Educación"),
     cel("Nivel educativo máximo en el hogar (MAX_EDUC_HOGAR)")],
    [cel("400 (M04)*"), cel("Salud"),
     cel("Tipo de seguro de salud (P4191–P4194 = no-SIS); "
         "parentesco (P203) para identificar al jefe de hogar")],
    [cel("612 (M18)"), cel("Bienes del hogar"),
     cel("Tenencia de refrigeradora, TV color y smartphone")],
    [cel("Sumaria"), cel("Variables agregadas del hogar"),
     cel("Gasto en agua (GRU51HD), electricidad (GRU52HD1), "
         "pobreza monetaria (POBREZA), ingresos del hogar")],
]
story.append(tabla(mod_data, [2.2*cm, 4.2*cm, W-6.4*cm]))
story.append(Paragraph(
    "* El módulo 400 fue descargado adicionalmente (199 MB), ya que no estaba "
    "incluido en el pipeline original de la tesis.", NOTA))
story.append(Spacer(1, 0.4*cm))

sub("4.2 Auditoría de variables")
story.append(Paragraph(
    "Antes de construir el índice auditamos la disponibilidad y calidad de las "
    "18 variables requeridas por el Apéndice F. Todas quedaron disponibles "
    "tras resolver 5 problemas:", CUERPO))

prob_data = [
    [cab("#"), cab("Problema detectado"), cab("Solución aplicada")],
    [cel("1", align=TA_CENTER),
     cel("P101 (techo) faltaba — el pipeline original guardaba P102 "
         "para paredes y techo como si fueran la misma variable."),
     cel("Se extrajo P101 directamente del módulo crudo "
         "Enaho01-2024-100.csv y se agregó como columna TECHO.")],
    [cel("2", align=TA_CENTER),
     cel("El módulo 400 (salud) no estaba en el pipeline. Sin él "
         "era imposible construir el conteo de seguros no-SIS ni "
         "identificar al jefe del hogar por parentesco."),
     cel("Se descargó el módulo 400 del repositorio INEI y se "
         "fusionó con el dataset principal.")],
    [cel("3", align=TA_CENTER),
     cel("Gasto en agua y electricidad no estaban en el dataset "
         "limpio — solo existía el gasto total del hogar (GASHOG2D)."),
     cel("Se extrajo GRU51HD (agua, anual) y GRU52HD1 (electricidad, "
         "anual) de Sumaria y se dividió entre 12 para valores mensuales.")],
    [cel("4", align=TA_CENTER),
     cel("AREA (urbano/rural) tenía 12% de nulos: los 14,095 registros "
         "de Lima Metropolitana (DOMINIO=8) no tenían AREA asignada."),
     cel("Se imputó AREA=1 (urbano) para DOMINIO=8 y se creó "
         "AREA_SISFOH con tres categorías: 'lima', 'urbano', 'rural'.")],
    [cel("5", align=TA_CENTER),
     cel("ALUMBRADO tenía 6.4% de nulos, concentrados en área rural "
         "(83% de los nulos)."),
     cel("Se imputó ALUMBRADO=3 (sin red eléctrica) — imputación "
         "conservadora que evita sobrestimar el IFH de hogares rurales pobres.")],
]
story.append(tabla(prob_data, [0.7*cm, 6.8*cm, W-7.5*cm]))
story.append(Spacer(1, 0.4*cm))

sub("4.3 Los tres pasos de construcción")

pasos_data = [
    [cab("Paso"), cab("Operación"), cab("Resultado")],
    [cel("1", align=TA_CENTER),
     cel("Asignar pesos a cada categoría de cada variable, diferenciados "
         "por área geográfica (Lima / urbano / rural) según Tablas A.8 y A.9 "
         "de Bernal et al. (2017). Pesos negativos = condición desfavorable; "
         "pesos positivos = condición favorable."),
     cel("12 columnas de pesos: w_combustible, w_agua, w_paredes, w_techo, "
         "w_piso, w_desague, w_seguro, w_bienes, w_educ_jefe "
         "(más w_hacinamiento y w_max_educ solo para Lima; "
         "w_electricidad solo para rural).")],
    [cel("2", align=TA_CENTER),
     cel("Sumar todos los pesos del hogar para obtener el IFH crudo (IFH_RAW). "
         "Los hogares más pobres acumulan pesos negativos; los más ricos, positivos."),
     cel(f"IFH_RAW: media={IFH_RAW_MEDIA}, std={IFH_RAW_STD}, "
         f"rango [{IFH_RAW_MIN}, {IFH_RAW_MAX}].")],
    [cel("3", align=TA_CENTER),
     cel("Estandarizar dentro de cada departamento al rango 0–100: "
         "IFH = 100 × (IFH_RAW − mín_dpto) / (máx_dpto − mín_dpto). "
         "El hogar más pobre del departamento recibe IFH=0; el más rico, IFH=100."),
     cel(f"IFH: media={IFH_MEDIA}, std={IFH_STD}, "
         f"mediana={IFH_MEDIANA}, rango [{IFH_MIN}, {IFH_MAX}].")],
]
story.append(tabla(pasos_data, [1*cm, 7.5*cm, W-8.5*cm]))
story.append(Spacer(1, 0.4*cm))

sub("4.4 Cinco decisiones metodológicas")

dec_data = [
    [cab("#"), cab("Decisión"), cab("Justificación")],
    [cel("1", align=TA_CENTER),
     cel("COMBUSTIBLE=9 reclasificado como 7 («No cocina»)."),
     cel("El código 9 no figura en BCK 2017. En ENAHO 2024 significa "
         "«No aplica», funcionalmente equivalente a «No cocina» (código 7). "
         "Se reclasificaron 1,997 registros.")],
    [cel("2", align=TA_CENTER),
     cel("Seguro no-SIS: conteo de miembros con P4191=1, P4192=1, "
         "P4193=1 o P4194=1. Excluye P4195 (SIS)."),
     cel("Coincide con la nota al pie 2 de BCK 2017: «We exclude SIS from "
         "the count of insured members». Los seguros incluidos son EsSalud, "
         "FF.AA./Policía, EPS privado y seguro universitario.")],
    [cel("3", align=TA_CENTER),
     cel("Nulos de ALUMBRADO (6.4%) imputados como 3 (sin red eléctrica)."),
     cel("Nulos concentrados en rural (83%). La imputación conservadora "
         "evita sobrestimar el bienestar de hogares que probablemente "
         "no tienen acceso a la red eléctrica.")],
    [cel("4", align=TA_CENTER),
     cel("Índice de bienes usa 3 bienes (refrigeradora, TV, smartphone) "
         "en lugar de 5 del paper original."),
     cel("Equipo de sonido y lavadora no estaban en el pipeline. "
         "Con 3 bienes el índice tiene rango {0,1,2,3}, mapeado "
         "a los primeros 4 valores de la tabla del Apéndice F.")],
    [cel("5", align=TA_CENTER),
     cel("Umbrales de elegibilidad diferenciados por departamento "
         "(Tabla A.10): rango 33–55, no un umbral uniforme."),
     cel(f"Con umbral uniforme 55: 32.5% elegibles. Con umbrales "
         f"correctos: {ELEG_IFH_PCT}% elegibles. La diferencia es "
         "sustancial porque Lima tiene el umbral más alto (55) y varios "
         "departamentos tienen umbrales muy bajos (33–36).")],
]
story.append(tabla(dec_data, [0.7*cm, 5.8*cm, W-6.5*cm]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — Resultados: ¿tenemos el IFH?
# ══════════════════════════════════════════════════════════════════════════════
sec(5, "Resultados: ¿tenemos el IFH?")

story.append(Paragraph(
    f"<b>Sí.</b> El IFH está calculado para <b>{N_IFH_OK:,} hogares</b> "
    f"({PCT_IFH_OK}% de la muestra). El {PCT_IFH_NULL}% restante ({N_IFH_NULOS:,} "
    "hogares) carece de datos de vivienda en el módulo 100 y no tiene IFH. "
    "El puntaje está disponible tanto a nivel de hogar como de persona: "
    "cada individuo hereda el IFH de su hogar.", RESP))

sub("5.1 Estadísticas descriptivas")

desc_data = [
    [cab("Estadístico"), cab("IFH crudo (IFH_RAW)"), cab("IFH estandarizado (0–100)")],
    [cel("Hogares con valor"), cel(f"{N_IFH_OK:,}"),    cel(f"{N_IFH_OK:,}")],
    [cel("Media"),             cel(f"{IFH_RAW_MEDIA}"), cel(f"{IFH_MEDIA}")],
    [cel("Desv. estándar"),    cel(f"{IFH_RAW_STD}"),   cel(f"{IFH_STD}")],
    [cel("Mínimo"),            cel(f"{IFH_RAW_MIN}"),   cel(f"{IFH_MIN}")],
    [cel("Percentil 25"),      cel("—"),                cel(f"{IFH_P25}")],
    [cel("Mediana (p50)"),     cel("—"),                cel(f"{IFH_MEDIANA}")],
    [cel("Percentil 75"),      cel("—"),                cel(f"{IFH_P75}")],
    [cel("Máximo"),            cel(f"{IFH_RAW_MAX}"),   cel(f"{IFH_MAX}")],
    [cel("Hogares sin IFH"),   cel(f"{N_IFH_NULOS:,}"), cel(f"{N_IFH_NULOS:,}")],
]
story.append(tabla(desc_data, [5.5*cm, 5*cm, 5*cm]))
story.append(Spacer(1, 0.3*cm))

sub("5.2 Validación: gradiente con la pobreza monetaria")
story.append(Paragraph(
    "Un índice de bienestar es válido si asigna puntajes más bajos a los hogares "
    "más pobres. Cruzamos el IFH con la clasificación de pobreza monetaria de la "
    "ENAHO (variable POBREZA, construida por INEI según gasto per cápita):", CUERPO))

valid_data = [
    [cab("Grupo (POBREZA ENAHO)"), cab("N entre 65+"),
     cab("IFH promedio"), cab("Resultado")],
    [cel("Extrema pobreza (POBREZA=1)"),
     cel(f"{N_POB1_65MAS:,}"),
     cel(f"{IFH_POB1}", bold=True, color=ROJO),
     cel("El más bajo → correcto")],
    [cel("Pobre no extremo (POBREZA=2)"),
     cel(f"{N_POB2_65MAS:,}"),
     cel(f"{IFH_POB2}", bold=True, color=colors.HexColor('#C05000')),
     cel("Intermedio → correcto")],
    [cel("No pobre (POBREZA=3)"),
     cel(f"{N_POB3_65MAS:,}"),
     cel(f"{IFH_POB3}", bold=True, color=VERDE_OSC),
     cel("El más alto → correcto")],
]
story.append(tabla(valid_data, [5*cm, 2.5*cm, 3*cm, W-10.5*cm]))

story.append(Paragraph(
    f"El gradiente es monotónico y en la dirección correcta: extrema pobreza "
    f"→ IFH {IFH_POB1}; pobre no extremo → {IFH_POB2}; no pobre → {IFH_POB3}. "
    f"La correlación entre el IFH y la variable de pobreza monetaria es "
    f"<b>r = {CORR_POB}</b>. Esta correlación moderada es esperada: el IFH mide "
    "condiciones estructurales de vivienda y bienes, mientras que POBREZA mide "
    "gasto corriente. Son dimensiones distintas pero relacionadas del bienestar.", CUERPO))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — Elegibilidad SISFOH replicada
# ══════════════════════════════════════════════════════════════════════════════
sec(6, "Elegibilidad SISFOH replicada")

story.append(Paragraph(
    "El SISFOH clasifica un hogar como elegible para el SIS si cumple "
    "<b>los tres criterios simultáneamente</b>:", CUERPO))
for b in [
    f"<b>Criterio 1 — IFH:</b> el puntaje IFH del hogar es ≤ al umbral "
    f"de su departamento (varía entre 33 y 55 según la Tabla A.10 de BCK 2017).",
    "<b>Criterio 2 — Gasto en agua:</b> el gasto mensual del hogar en agua "
    "potable es ≤ 20 soles.",
    "<b>Criterio 3 — Gasto en electricidad:</b> el gasto mensual del hogar "
    "en electricidad de red es ≤ 25 soles.",
]:
    story.append(Paragraph(b, BULLET))

story.append(Spacer(1, 0.3*cm))
eleg_data = [
    [cab("Criterio"), cab("Umbral"), cab("Elegibles"),
     cab("Porcentaje"), cab("Nota")],
    [cel("IFH ≤ umbral departamental"),
     cel("33–55 según dpto."),
     cel(f"{ELEG_IFH:,}", bold=True),
     cel(f"{ELEG_IFH_PCT}%"),
     cel("Diferenciado por los 25 departamentos")],
    [cel("Gasto agua ≤ 20 S/mes"),
     cel("20 soles"),
     cel(f"{ELEG_AGUA:,}", bold=True),
     cel(f"{ELEG_AGUA_PCT}%"),
     cel("GRU51HD anual / 12")],
    [cel("Gasto electricidad ≤ 25 S/mes"),
     cel("25 soles"),
     cel(f"{ELEG_ELECTR:,}", bold=True),
     cel(f"{ELEG_ELEC_PCT}%"),
     cel("Ver nota †")],
    [cel("ELEGIBLE SIS (los 3 criterios)", bold=True),
     cel("Todos"),
     cel(f"{ELEG_SIS:,}", bold=True, color=AZUL_OSCURO),
     cel(f"{ELEG_SIS_PCT}%", bold=True, color=AZUL_OSCURO),
     cel("Criterio restrictivo: requiere los tres")],
]
story.append(tabla(eleg_data, [5*cm, 2.2*cm, 2.8*cm, 2*cm, W-12*cm]))
story.append(Paragraph(
    "† En la ENAHO 2024 el 99.8% de hogares tiene gasto en electricidad "
    "≤ 25 S/mes porque GRU52HD1 captura solo el pago a la red pública. "
    "Los hogares con generador o paneles solares no aparecen en esta variable. "
    "El criterio de electricidad prácticamente no filtra en 2024, por lo que "
    f"la elegibilidad SIS final ({ELEG_SIS_PCT}%) está determinada "
    "principalmente por los criterios de IFH y gasto en agua.", NOTA))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("Umbrales de elegibilidad por departamento (Tabla A.10, BCK 2017):",
                        SEC_SUB))

umb_data = [
    [cab("Cód."), cab("Departamento"), cab("Umbral"),
     cab("Cód."), cab("Departamento"), cab("Umbral")],
    [cel("1"),  cel("Amazonas"),       cel("50"), cel("14"), cel("Lambayeque"),    cel("43")],
    [cel("2"),  cel("Ancash"),         cel("44"), cel("15"), cel("Lima"),          cel("55", bold=True)],
    [cel("3"),  cel("Apurímac"),       cel("44"), cel("16"), cel("Loreto"),        cel("43")],
    [cel("4"),  cel("Arequipa"),       cel("44"), cel("17"), cel("Madre de Dios"), cel("43")],
    [cel("5"),  cel("Ayacucho"),       cel("50"), cel("18"), cel("Moquegua"),      cel("38")],
    [cel("6"),  cel("Cajamarca"),      cel("52"), cel("19"), cel("Pasco"),         cel("35")],
    [cel("7"),  cel("Callao"),         cel("52"), cel("20"), cel("Piura"),         cel("36")],
    [cel("8"),  cel("Cusco"),          cel("42"), cel("21"), cel("Puno"),          cel("34")],
    [cel("9"),  cel("Huancavelica"),   cel("44"), cel("22"), cel("San Martín"),    cel("52")],
    [cel("10"), cel("Huánuco"),        cel("44"), cel("23"), cel("Tacna"),         cel("33")],
    [cel("11"), cel("Ica"),            cel("50"), cel("24"), cel("Tumbes"),        cel("34")],
    [cel("12"), cel("Junín"),          cel("42"), cel("25"), cel("Ucayali"),       cel("36")],
    [cel("13"), cel("La Libertad"),    cel("52"), cel(""),   cel(""),              cel("")],
]
story.append(tabla(umb_data, [1.2*cm, 4*cm, 1.8*cm, 1.2*cm, 4*cm, 1.8*cm]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — Conexión IFH y Pensión 65
# ══════════════════════════════════════════════════════════════════════════════
sec(7, "Conexión IFH y Pensión 65")

ifh_p65_data = [
    [cab("Grupo (personas de 65+ años)"), cab("N"),
     cab("IFH promedio"), cab("Diferencia")],
    [cel("Receptores de Pensión 65", bold=True),
     cel(f"{N_REC_P65:,}"),
     cel(f"{IFH_REC}", bold=True, color=ROJO),
     cel(f"−{IFH_DIFF} pp vs no receptores", bold=True, color=ROJO)],
    [cel("No receptores de Pensión 65"),
     cel(f"{N_NO_REC_65:,}"),
     cel(f"{IFH_NOREC}"),
     cel("—")],
    [cel("Referencia: promedio nacional (toda la muestra)"),
     cel(f"{N_IFH_OK:,}"),
     cel(f"{IFH_MEDIA}"),
     cel("—")],
]
story.append(tabla(ifh_p65_data, [7*cm, 2.5*cm, 2.8*cm, W-12.3*cm]))

story.append(Paragraph(
    f"El IFH promedio de los receptores de Pensión 65 entre los mayores de 65 años "
    f"es <b>{IFH_REC}</b> — significativamente por debajo del promedio de los "
    f"no receptores ({IFH_NOREC}) y cercano al IFH de los hogares en extrema pobreza "
    f"monetaria ({IFH_POB1}). Esto confirma dos cosas: primero, que el IFH "
    f"identifica correctamente a los hogares más pobres. Segundo, que Pensión 65 "
    f"llega efectivamente a ese grupo dentro de la población de 65 años o más, "
    f"lo que valida el diseño del programa en términos de focalización.", CUERPO))

story.append(Paragraph(
    "Para el análisis de heterogeneidad planificado, se dividirá a la población "
    "de 65+ en dos grupos según el IFH: los que están por debajo del umbral de "
    "elegibilidad de su departamento (ELEGIBLE_SIS=1) y los que están por encima. "
    "La hipótesis es que el efecto de Pensión 65 sobre la adopción de billetera "
    "debería ser mayor en el grupo con IFH bajo, porque para ellos la pensión "
    "puede ser el primer vínculo con el sistema financiero formal.", CUERPO))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — Limitaciones
# ══════════════════════════════════════════════════════════════════════════════
sec(8, "Limitaciones")

lims = [
    ("8.1 IFH aproximado, no oficial",
     "El IFH que construimos replica el índice oficial pero no es el puntaje "
     "que el MIDIS asigna a cada hogar. El puntaje oficial usa información "
     "adicional recopilada por las Unidades Locales de Empadronamiento durante "
     "visitas presenciales, y no está disponible públicamente."),
    ("8.2 Índice de bienes incompleto",
     "El Apéndice F de BCK 2017 incluye 5 bienes durables. Solo disponemos "
     "de 3 (refrigeradora, TV y smartphone). La exclusión de equipo de sonido "
     "y lavadora puede subestimar levemente el IFH de hogares de clase media."),
    ("8.3 Criterio de electricidad inoperante en 2024",
     f"El {ELEG_ELEC_PCT}% de hogares queda por debajo del umbral de 25 S/mes "
     "en electricidad porque GRU52HD1 solo captura el pago a la red pública. "
     "El criterio de electricidad prácticamente no discrimina en 2024."),
    ("8.4 Umbrales de 2009 aplicados a datos de 2024",
     "Los umbrales de la Tabla A.10 fueron estimados con datos del SISFOH "
     "de 2009-2010. Entre 2010 y 2024 los niveles de vida mejoraron "
     "considerablemente. Es posible que los umbrales de 2009 sobreestimen "
     "la elegibilidad en 2024."),
    ("8.5 Poder estadístico del RDD",
     f"La muestra de mayores de 65 años con billetera digital es de "
     f"{N_BILL_65MAS:,} personas ({PCT_BILL_65MAS}% de los 65+). En las "
     f"ventanas estrechas alrededor del umbral (ventana ±5: N={V5_N:,}, "
     f"N_billetera={V5_N_BILL:,}), el número de observaciones puede limitar "
     "el poder estadístico del RDD. Se reportará el bandwidth óptimo de "
     "rdrobust y los intervalos de confianza honestos (Kolesar-Rothe 2018) "
     "para evaluar la precisión de la estimación."),
]
for titulo, texto in lims:
    story.append(KeepTogether([
        Paragraph(titulo, SEC_SUB),
        Paragraph(texto, CUERPO),
        Spacer(1, 0.15*cm),
    ]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — Próximos pasos
# ══════════════════════════════════════════════════════════════════════════════
sec(9, "Próximos pasos")

story.append(Paragraph(
    "Con el IFH construido y el diseño empírico caracterizado, los siguientes "
    "pasos para completar la tesis son:", CUERPO))

pasos = [
    ("<b>1. Estimar el Fuzzy RDD con rdrobust.</b> Correr el primer estadio "
     "(efecto de EDAD≥65 sobre RECIBE_P65_PERSONA), la forma reducida "
     "(efecto de EDAD≥65 sobre TIENE_BILLETERA) y el LATE = forma reducida / "
     "primer estadio. Reportar bandwidth óptimo, intervalos de confianza honestos "
     "(Kolesar-Rothe 2018) y estadístico F del primer estadio."),
    ("<b>2. Test de McCrary de no manipulación de la edad.</b> Verificar que "
     "no hay densidad discontinua en la running variable alrededor de los 65 años. "
     "Formalizar el test con la distribución de edades 60–70 ya observada."),
    ("<b>3. Balance de covariables en el umbral.</b> Verificar que el IFH, "
     "el sexo, la educación y otras características preexistentes no muestran "
     "discontinuidades a los 65 años. Esto sustenta el supuesto de continuidad "
     "del RDD."),
    ("<b>4. Análisis de heterogeneidad por IFH.</b> Estimar el LATE "
     "separadamente para la submuestra con IFH bajo (ELEGIBLE_SIS=1) y "
     "con IFH alto (ELEGIBLE_SIS=0). Reportar si el efecto de Pensión 65 "
     "sobre la billetera varía según el nivel de pobreza del hogar."),
]
for b in pasos:
    story.append(Paragraph(b, BULLET))
    story.append(Spacer(1, 0.2*cm))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 10 — Referencias
# ══════════════════════════════════════════════════════════════════════════════
sec(10, "Referencias")

refs_style = E('Ref', fontSize=10, leading=15, spaceAfter=12,
               alignment=TA_JUSTIFY, leftIndent=20, firstLineIndent=-20)

refs = [
    "Bernal, N., Carpio, M. A., y Klein, T. J. (2017). The effects of access to "
    "health insurance: Evidence from a regression discontinuity design in Peru. "
    "<i>Journal of Public Economics</i>, 154, 122–136. "
    "https://doi.org/10.1016/j.jpubeco.2017.08.008",

    "INEI — Instituto Nacional de Estadística e Informática (2024). "
    "<i>Encuesta Nacional de Hogares sobre Condiciones de Vida y Pobreza, 2024</i> "
    "(Código de encuesta: 966). Lima: INEI. Recuperado del repositorio público "
    "de microdatos: https://proyectos.inei.gob.pe/iinei/srienaho/",

    "MIDIS — Ministerio de Desarrollo e Inclusión Social (2010). "
    "<i>Metodología de Focalización del Sistema de Focalización de Hogares (SISFOH)</i>. "
    "Lima: MIDIS. [Pesos del índice publicados en Bernal et al., 2017, Apéndice F]",
]
for ref in refs:
    story.append(Paragraph(ref, refs_style))

story.append(Spacer(1, 1*cm))
story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_LINEA, spaceAfter=8))
story.append(Paragraph(
    f"Documento generado automáticamente a partir del pipeline de datos de la tesis. "
    f"Código fuente: construir_ifh.py — repositorio del proyecto. "
    f"Fecha de generación: {FECHA}.",
    E('Pie', fontSize=8, textColor=colors.HexColor('#888888'),
      alignment=TA_CENTER)))

# ── Generar ───────────────────────────────────────────────────────────────────
doc.build(story, canvasmaker=NumberedCanvas)
print(f"\nPDF generado: {OUTPUT}")
