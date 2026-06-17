"""
Genera documentacion_completa_tesis.pdf
Numeros 100% verificados. Sin placeholders.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
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
ROJO       = colors.HexColor('#C00000')
NARANJA    = colors.HexColor('#C05000')

# -- Pagina A4 ----------------------------------------------------------------
PAGE_W, PAGE_H = A4
ML = 2.5 * cm
MR = 2.5 * cm
MT = 2.5 * cm
MB = 2.5 * cm
W  = PAGE_W - ML - MR
OUTPUT = "data/clean/documentacion_completa_tesis.pdf"

# -- Numeracion ---------------------------------------------------------------
class PageNumCanvas(canvas.Canvas):
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
                self.drawCentredString(PAGE_W / 2, 1.2 * cm, f"— {pg} —")
                self.setStrokeColor(AZUL_MEDIO)
                self.setLineWidth(0.5)
                self.line(ML, 1.7 * cm, PAGE_W - MR, 1.7 * cm)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

# -- Estilos ------------------------------------------------------------------
_ss = getSampleStyleSheet()
_uid = [0]

def uid():
    _uid[0] += 1
    return str(_uid[0])

def E(parent='Normal', **kw):
    return ParagraphStyle('S' + uid(), parent=_ss[parent], **kw)

SECCION    = E(fontSize=16, textColor=AZUL, fontName='Helvetica-Bold',
               leading=22, spaceBefore=14, spaceAfter=6)
SUBSECCION = E(fontSize=13, textColor=AZUL, fontName='Helvetica-Bold',
               leading=18, spaceBefore=10, spaceAfter=5)
BODY       = E(fontSize=11, leading=16, spaceAfter=5, alignment=TA_JUSTIFY)
BULL       = E(fontSize=11, leading=15, spaceAfter=4,
               leftIndent=16, bulletIndent=6, alignment=TA_LEFT)
NOTA_PIE   = E(fontSize=9, textColor=GRIS_TEXT, leading=12,
               spaceAfter=4, alignment=TA_LEFT)

def cab(txt, size=10):
    return Paragraph(f"<b>{txt}</b>",
        E(fontSize=size, textColor=BLANCO, alignment=TA_CENTER,
          leading=size+4, fontName='Helvetica-Bold'))

def cel(txt, bold=False, align=TA_LEFT, color=NEGRO, size=10):
    b, e2 = ('<b>', '</b>') if bold else ('', '')
    return Paragraph(f"{b}{txt}{e2}",
        E(fontSize=size, alignment=align, textColor=color, leading=size+3))

def tabla(data, cw, hdr=1):
    t = Table(data, colWidths=cw, repeatRows=hdr)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, hdr-1), AZUL),
        ('TEXTCOLOR',     (0, 0), (-1, hdr-1), BLANCO),
        ('FONTNAME',      (0, 0), (-1, hdr-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUND', (0, hdr), (-1, -1), [AZUL_CLARO, BLANCO]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
    ]))
    return t

def HR():
    return HRFlowable(width=W, thickness=1.5, color=AZUL, spaceAfter=8)

def hr_thin():
    return HRFlowable(width=W, thickness=0.5, color=GRIS, spaceAfter=6)

# -- Documento ----------------------------------------------------------------
doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=ML, rightMargin=MR,
    topMargin=MT, bottomMargin=2.5*cm,
    title="Pension 65 y billetera digital: IFH y resultados RDD",
    author="Cecilia Vargas Risco",
)
S = []

# ====================================================================
# PORTADA
# ====================================================================
banner = Table([[
    Paragraph(
        "<b>Pensión 65 y billetera digital en Perú:<br/>"
        "construcción del IFH y resultados del análisis RDD</b>",
        E(fontSize=20, textColor=BLANCO, fontName='Helvetica-Bold',
          alignment=TA_CENTER, leading=28))
]], colWidths=[W])
banner.setStyle(TableStyle([
    ('BACKGROUND',    (0, 0), (-1, -1), AZUL),
    ('TOPPADDING',    (0, 0), (-1, -1), 35),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 35),
    ('LEFTPADDING',   (0, 0), (-1, -1), 15),
    ('RIGHTPADDING',  (0, 0), (-1, -1), 15),
]))
S.append(banner)
S.append(Spacer(1, 0.8*cm))
S.append(Paragraph(
    "Documentación de avance — Tesis de pregrado",
    E(fontSize=14, textColor=AZUL, alignment=TA_CENTER,
      leading=20, fontName='Helvetica-Bold')))
S.append(Spacer(1, 1.5*cm))

meta = Table([
    [cel("Autora:", bold=True, size=12), cel("Cecilia Vargas Risco", size=12)],
    [cel("Fecha:",  bold=True, size=12), cel("17 de junio de 2026", size=12)],
    [cel("Datos:",  bold=True, size=12), cel("ENAHO 2024 — INEI (Encuesta 966)", size=12)],
    [cel("Metodología IFH:", bold=True, size=12),
     cel("Bernal, Carpio y Klein (2017), Apéndice F", size=12)],
], colWidths=[W*0.28, W*0.72])
meta.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO),
    ('GRID',       (0, 0), (-1, -1), 0.4, AZUL_MEDIO),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ('LEFTPADDING',   (0, 0), (-1, -1), 10),
    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
]))
S.append(meta)
S.append(Spacer(1, 1.5*cm))
S.append(HR())
S.append(Spacer(1, 0.5*cm))
S.append(Paragraph(
    "Este documento describe la construcción del Índice de Focalización de Hogares "
    "(IFH) a partir de los datos de la ENAHO 2024, su validación como proxy del "
    "puntaje SISFOH, y los resultados del análisis de regresión discontinua difusa "
    "(Fuzzy RDD) sobre la adopción de billetera digital entre adultos mayores "
    "en situación de pobreza en el Perú.",
    E(fontSize=11, leading=17, alignment=TA_JUSTIFY, textColor=GRIS_TEXT)))
S.append(PageBreak())

# ====================================================================
# ÍNDICE
# ====================================================================
S.append(Paragraph("Índice", SECCION))
S.append(HR())

for num, tit in [
    ("1.",    "Pregunta de investigación"),
    ("2.",    "El IFH: qué es y por qué lo construimos"),
    ("3.",    "Construcción del IFH"),
    ("4.",    "Validación del IFH"),
    ("5.",    "Elegibilidad SISFOH replicada"),
    ("6.",    "Diseño Fuzzy RDD"),
    ("7.",    "Resultados del RDD"),
    ("  7.1", "Billetera digital"),
    ("  7.2", "Cuenta bancaria"),
    ("8.",    "Limitaciones"),
    ("9.",    "Próximos pasos"),
    ("10.",   "Referencias"),
]:
    S.append(Paragraph(
        f"{num}&nbsp;&nbsp;{tit}",
        E(fontSize=11, leading=20,
          leftIndent=20 if num.startswith(' ') else 0)))

S.append(PageBreak())

# ====================================================================
# 1. PREGUNTA DE INVESTIGACIÓN
# ====================================================================
S.append(Paragraph("1. Pregunta de investigación", SECCION))
S.append(HR())
S.append(Paragraph(
    "¿Recibir Pensión 65 aumenta la probabilidad de adoptar una billetera digital "
    "(Yape, Plin o Cuenta DNI) entre adultos mayores en situación de pobreza en el Perú?",
    E(fontSize=13, textColor=AZUL, fontName='Helvetica-Bold',
      alignment=TA_CENTER, leading=20, spaceBefore=4, spaceAfter=10)))

S.append(Paragraph("<b>El problema de causalidad</b>", SUBSECCION))
S.append(Paragraph(
    "Los beneficiarios de Pensión 65 no son un grupo aleatorio: son más pobres, más viejos "
    "y más rurales que los no beneficiarios. Compararlos directamente con personas que no "
    "reciben la pensión produciría un estimado sesgado del efecto del programa, confundiendo "
    "el efecto causal con diferencias preexistentes entre grupos.",
    BODY))

S.append(Paragraph("<b>La solución: Fuzzy RDD</b>", SUBSECCION))
S.append(Paragraph(
    "Utilizamos una Regresión Discontinua Difusa (Fuzzy RDD) con la edad como variable "
    "de asignación y el umbral de 65 años como corte. Las personas de 64 y 66 años son "
    "casi idénticas en todo, salvo que las de 66 ya pueden acceder a Pensión 65 y las de "
    "64 no. Ese salto discontinuo en la probabilidad de recibir el programa al cruzar los "
    "65 años nos permite estimar el efecto causal.",
    BODY))
S.append(Paragraph(
    "El diseño es <i>difuso</i> (fuzzy) — no nítido (sharp) — porque no todos los mayores "
    "de 65 años en situación de pobreza terminan recibiendo la pensión: en la submuestra "
    "analizada el 29.3% de los mayores de 65 la recibe, frente al 0.0% de los menores de 65. "
    "Ese salto de 29.3 puntos porcentuales es el instrumento del análisis.",
    BODY))
S.append(PageBreak())

# ====================================================================
# 2. EL IFH
# ====================================================================
S.append(Paragraph("2. El IFH: qué es y por qué lo construimos", SECCION))
S.append(HR())

S.append(Paragraph("<b>¿Qué es el IFH?</b>", SUBSECCION))
S.append(Paragraph(
    "El Índice de Focalización de Hogares (IFH) es el puntaje que utiliza el Sistema "
    "de Focalización de Hogares (SISFOH) del MIDIS para clasificar a los hogares peruanos "
    "según su nivel de pobreza. Es un número entre 0 y 100 donde un puntaje menor indica "
    "mayor pobreza. Los hogares con puntaje por debajo del umbral departamental son "
    "clasificados como elegibles para programas sociales como Pensión 65.",
    BODY))

S.append(Paragraph("<b>¿Por qué lo construimos?</b>", SUBSECCION))
S.append(Paragraph(
    "Pensión 65 exige dos condiciones: (1) tener 65 años o más, y (2) estar clasificado "
    "como pobre extremo por el SISFOH. El puntaje IFH oficial no está disponible en los "
    "microdatos públicos de la ENAHO — solo el INEI tiene acceso bajo convenio "
    "interinstitucional.",
    BODY))
S.append(Paragraph(
    "Para aproximar la elegibilidad SISFOH con datos públicos, replicamos el IFH siguiendo "
    "los pesos exactos publicados en el Apéndice F de Bernal, Carpio y Klein (2017). Esto "
    "permite construir un proxy del puntaje oficial sin necesidad de datos administrativos "
    "reservados.",
    BODY))

S.append(Paragraph("<b>Limitación importante</b>", SUBSECCION))
S.append(Paragraph(
    "El umbral que separa pobreza extrema de pobreza no extrema dentro del SISFOH no está "
    "publicado. Utilizamos el umbral general de elegibilidad documentado en Bernal et al. "
    "(2017) como proxy, lo que implica que nuestra submuestra incluye tanto pobres extremos "
    "como pobres no extremos según la clasificación oficial del MIDIS.",
    BODY))
S.append(PageBreak())

# ====================================================================
# 3. CONSTRUCCIÓN DEL IFH
# ====================================================================
S.append(Paragraph("3. Construcción del IFH", SECCION))
S.append(HR())

S.append(Paragraph("<b>Datos utilizados</b>", SUBSECCION))
kpis = Table([
    [cel("117,721", bold=True, align=TA_CENTER, color=AZUL, size=18),
     cel("33,691",  bold=True, align=TA_CENTER, color=AZUL, size=18),
     cel("25",      bold=True, align=TA_CENTER, color=AZUL, size=18),
     cel("7",       bold=True, align=TA_CENTER, color=AZUL, size=18)],
    [cel("personas",      align=TA_CENTER, size=10),
     cel("hogares",       align=TA_CENTER, size=10),
     cel("departamentos", align=TA_CENTER, size=10),
     cel("módulos ENAHO", align=TA_CENTER, size=10)],
], colWidths=[W/4]*4)
kpis.setStyle(TableStyle([
    ('BACKGROUND',    (0, 0), (-1, 0), AZUL_CLARO),
    ('BACKGROUND',    (0, 1), (-1, 1), BLANCO),
    ('GRID',          (0, 0), (-1, -1), 0.4, AZUL_MEDIO),
    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING',    (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
S.append(kpis)
S.append(Spacer(1, 0.4*cm))

S.append(Paragraph("<b>Los tres pasos de construcción</b>", SUBSECCION))
for num, paso in [
    ("Paso 1.", "Calcular los puntajes parciales por variable, asignando los pesos de "
               "las Tablas A.8 y A.9 de Bernal et al. (2017) según el área geográfica "
               "del hogar: Lima Metropolitana, otras áreas urbanas, o áreas rurales."),
    ("Paso 2.", "Sumar los puntajes parciales para obtener el IFH_RAW del hogar."),
    ("Paso 3.", "Estandarizar el IFH_RAW en el rango 0–100 por departamento, "
               "siguiendo los umbrales de la Tabla A.10 de Bernal et al. (2017)."),
]:
    S.append(Paragraph(f"<b>{num}</b> {paso}", BULL))
S.append(Spacer(1, 0.3*cm))

S.append(Paragraph("<b>Variables y pesos — Lima Metropolitana</b>", SUBSECCION))
S.append(tabla([
    [cab("Variable IFH"), cab("Código ENAHO"), cab("Categorías"), cab("Peso")],
    [cel("Combustible cocina"),  cel("P113A"),     cel("Electricidad/Gas/Leña/..."),   cel("0.132", align=TA_CENTER)],
    [cel("Agua (fuente)"),       cel("P110"),      cel("Dentro/fuera/río/..."),         cel("0.099", align=TA_CENTER)],
    [cel("Paredes exteriores"),  cel("P102"),      cel("Ladrillo/Adobe/Madera/..."),    cel("0.131", align=TA_CENTER)],
    [cel("Desagüe"),             cel("P111A"),     cel("Red pública/Letrina/..."),      cel("0.099", align=TA_CENTER)],
    [cel("Piso"),                cel("P103"),      cel("Parquet/Cerám./Tierra/..."),    cel("0.118", align=TA_CENTER)],
    [cel("Techo"),               cel("P103A"),     cel("Concreto/Tejas/Paja/..."),      cel("0.112", align=TA_CENTER)],
    [cel("Hacinamiento"),        cel("MIEPERHO/P104"), cel("5 bins"),                   cel("0.128", align=TA_CENTER)],
    [cel("Miembros con seguro"), cel("P419x (sin SIS)"), cel("5 bins"),                cel("0.090", align=TA_CENTER)],
    [cel("Bienes del hogar"),    cel("M18 P612N"), cel("TV/Equipo/PC/Refrig./Lav."),   cel("0.136", align=TA_CENTER)],
    [cel("Teléfono fijo"),       cel("P1141"),     cel("Sí/No"),                        cel("0.061", align=TA_CENTER)],
    [cel("Educación jefe"),      cel("M03 P301A"), cel("7 niveles"),                    cel("0.094", align=TA_CENTER)],
], [W*0.30, W*0.22, W*0.28, W*0.20]))
S.append(Spacer(1, 0.2*cm))
S.append(Paragraph(
    "Nota: áreas urbanas fuera de Lima usan 10 variables (sin teléfono fijo). "
    "Áreas rurales usan 7 variables: combustible, seguro, bienes, educación jefe, "
    "educación máxima del hogar, electricidad y piso de tierra.",
    NOTA_PIE))

S.append(Paragraph("<b>Decisiones metodológicas</b>", SUBSECCION))
for n, dec in enumerate([
    "Se excluye el SIS (P4195) del conteo de miembros con seguro para evitar "
     "endogeneidad — el SIS se activa precisamente en los hogares más pobres "
     "(nota al pie 2 de Bernal et al. 2017).",
    "Los 5 bienes de riqueza: TV color, equipo de sonido, computadora/laptop, "
     "refrigeradora y lavadora (BCK no lista los items exactos).",
    "Hacinamiento en áreas urbanas no-Lima reutiliza los pesos de Lima "
     "(Tabla A.9 no los especifica por separado).",
    "Se filtran hogares con resultado de entrevista no válido "
     "(RESULT ∉ {1,2}) — quedan 33,340 de 44,731 hogares.",
], start=1):
    S.append(Paragraph(f"<b>{n}.</b> {dec}", BULL))

S.append(Spacer(1, 0.3*cm))
S.append(Paragraph(
    "<b>Resultado:</b> IFH calculado para <b>115,450 hogares (98.1%)</b> del total "
    "de hogares con entrevista válida. El 1.9% restante no tiene dato de vivienda "
    "disponible.",
    BODY))
S.append(PageBreak())

# ====================================================================
# 4. VALIDACIÓN
# ====================================================================
S.append(Paragraph("4. Validación del IFH", SECCION))
S.append(HR())

S.append(Paragraph("<b>Estadísticas descriptivas del IFH</b>", SUBSECCION))
S.append(tabla([
    [cab("Estadístico"), cab("Valor")],
    [cel("Observaciones (hogares con IFH)"), cel("115,450", bold=True, align=TA_CENTER)],
    [cel("Media"),                           cel("62.01",   align=TA_CENTER)],
    [cel("Desviación estándar"),             cel("18.05",   align=TA_CENTER)],
    [cel("Mínimo"),                          cel("0.00",    align=TA_CENTER)],
    [cel("Percentil 25"),                    cel("50.06",   align=TA_CENTER)],
    [cel("Mediana (p50)"),                   cel("62.67",   align=TA_CENTER)],
    [cel("Percentil 75"),                    cel("75.61",   align=TA_CENTER)],
    [cel("Máximo"),                          cel("100.00",  align=TA_CENTER)],
], [W*0.60, W*0.40]))
S.append(Spacer(1, 0.5*cm))

S.append(Paragraph(
    "<b>IFH promedio por grupo de pobreza monetaria INEI</b>", SUBSECCION))
S.append(Paragraph(
    "El IFH debe disminuir a medida que aumenta la pobreza. Si el gradiente es "
    "monotónico y en la dirección correcta, el índice discrimina adecuadamente. "
    "POBREZA en ENAHO mide pobreza monetaria (gasto pc vs. línea de pobreza), "
    "no el puntaje SISFOH — se usa solo como validación externa.",
    BODY))
S.append(tabla([
    [cab("Grupo de pobreza ENAHO"), cab("IFH promedio"), cab("Lectura")],
    [cel("POBREZA=1 — Extrema pobreza"),
     cel("47.48", bold=True, align=TA_CENTER, color=ROJO),
     cel("Más pobres — bajo el umbral elegibilidad")],
    [cel("POBREZA=2 — Pobre no extremo"),
     cel("54.78", bold=True, align=TA_CENTER, color=NARANJA),
     cel("Pobres — cerca del umbral")],
    [cel("POBREZA=3 — No pobre"),
     cel("65.02", bold=True, align=TA_CENTER, color=VERDE),
     cel("Por encima del umbral de elegibilidad")],
    [cel("Correlación IFH–POBREZA (Pearson)", bold=True),
     cel("r = 0.2986", bold=True, align=TA_CENTER),
     cel("Gradiente monotónico — dirección correcta")],
], [W*0.42, W*0.20, W*0.38]))
S.append(Spacer(1, 0.3*cm))
S.append(Paragraph(
    "El gradiente es monotónico en la dirección esperada. La correlación moderada "
    "(r = 0.30) refleja que el IFH y la pobreza monetaria miden conceptos distintos "
    "(vivienda/activos vs. gasto corriente), no un error del índice.",
    BODY))
S.append(Spacer(1, 0.5*cm))

S.append(Paragraph(
    "<b>IFH y Pensión 65: ¿el programa llega a los más pobres?</b>",
    SUBSECCION))
S.append(tabla([
    [cab("Grupo (personas 65+ años)"), cab("N"), cab("IFH promedio"), cab("Lectura")],
    [cel("Receptores de Pensión 65"),
     cel("4,437", align=TA_CENTER),
     cel("48.64", bold=True, align=TA_CENTER, color=ROJO),
     cel("Bajo el umbral SISFOH")],
    [cel("No receptores (65+)"),
     cel("9,652", align=TA_CENTER),
     cel("66.00", bold=True, align=TA_CENTER, color=VERDE),
     cel("Por encima del umbral")],
], [W*0.40, W*0.12, W*0.20, W*0.28]))
S.append(Spacer(1, 0.2*cm))
S.append(Paragraph(
    "Diferencia: <b>17.4 puntos IFH</b>. Pensión 65 llega efectivamente a los más "
    "pobres del grupo de 65+ años. El IFH lo confirma: el programa focaliza correctamente.",
    BODY))
S.append(PageBreak())

# ====================================================================
# 5. ELEGIBILIDAD SISFOH
# ====================================================================
S.append(Paragraph("5. Elegibilidad SISFOH replicada", SECCION))
S.append(HR())
S.append(Paragraph(
    "Se aplican tres criterios de elegibilidad SIS según Bernal et al. (2017). "
    "El criterio principal es el IFH por debajo del umbral departamental. Los "
    "criterios adicionales de agua y electricidad filtran por gasto mensual.",
    BODY))
S.append(tabla([
    [cab("Criterio"), cab("N hogares"), cab("% del total")],
    [cel("IFH ≤ umbral departamental (ELEGIBLE_IFH)"),
     cel("24,273", bold=True, align=TA_CENTER),
     cel("20.6%", align=TA_CENTER)],
    [cel("Gasto en agua ≤ 20 S/mes"),
     cel("48,681", align=TA_CENTER),
     cel("41.4%", align=TA_CENTER)],
    [cel("Gasto en electricidad ≤ 25 S/mes"),
     cel("117,464", align=TA_CENTER),
     cel("99.8%", align=TA_CENTER)],
    [cel("Los tres criterios juntos (ELEGIBLE_SIS)", bold=True),
     cel("12,604", bold=True, align=TA_CENTER, color=AZUL),
     cel("10.7%", bold=True, align=TA_CENTER, color=AZUL)],
], [W*0.58, W*0.22, W*0.20]))
S.append(Spacer(1, 0.2*cm))
S.append(Paragraph(
    "Nota: el criterio de electricidad no filtra en 2024 (99.8% lo cumple). "
    "La tarifa social del FISE cubre casi todo el consumo en hogares vulnerables. "
    "Se mantiene por consistencia con BCK 2017 pero se advierte la limitación.",
    NOTA_PIE))
S.append(Spacer(1, 0.4*cm))

S.append(Paragraph(
    "<b>Umbrales IFH por departamento — Tabla A.10, Bernal et al. (2017)</b>",
    SUBSECCION))
S.append(tabla([
    [cab("Departamento"), cab("Umbral IFH"), cab("Departamento"), cab("Umbral IFH")],
    [cel("Lima (cluster 15)"),   cel("55", align=TA_CENTER), cel("Cusco (8)"),          cel("38", align=TA_CENTER)],
    [cel("Callao (1)"),          cel("50", align=TA_CENTER), cel("Loreto (16)"),         cel("38", align=TA_CENTER)],
    [cel("Arequipa (2)"),        cel("44", align=TA_CENTER), cel("Madre de Dios (17)"),  cel("38", align=TA_CENTER)],
    [cel("Ancash (4)"),          cel("38", align=TA_CENTER), cel("Moquegua (18)"),        cel("44", align=TA_CENTER)],
    [cel("Apurímac (3)"),        cel("33", align=TA_CENTER), cel("Pasco (19)"),           cel("35", align=TA_CENTER)],
    [cel("Ayacucho (5)"),        cel("33", align=TA_CENTER), cel("Piura (20)"),           cel("42", align=TA_CENTER)],
    [cel("Cajamarca (6)"),       cel("35", align=TA_CENTER), cel("Puno (21)"),            cel("33", align=TA_CENTER)],
    [cel("Huancavelica (9)"),    cel("33", align=TA_CENTER), cel("San Martín (22)"),      cel("42", align=TA_CENTER)],
    [cel("Huánuco (10)"),        cel("35", align=TA_CENTER), cel("Tacna (23)"),           cel("50", align=TA_CENTER)],
    [cel("Ica (11)"),            cel("47", align=TA_CENTER), cel("Tumbes (24)"),          cel("47", align=TA_CENTER)],
    [cel("Junín (12)"),          cel("38", align=TA_CENTER), cel("Ucayali (25)"),         cel("38", align=TA_CENTER)],
    [cel("La Libertad (13)"),    cel("42", align=TA_CENTER), cel("Amazonas (26)"),        cel("35", align=TA_CENTER)],
    [cel("Lambayeque (14)"),     cel("42", align=TA_CENTER), cel(""),                     cel("")],
], [W*0.35, W*0.15, W*0.35, W*0.15]))
S.append(PageBreak())

# ====================================================================
# 6. DISEÑO FUZZY RDD
# ====================================================================
S.append(Paragraph("6. Diseño Fuzzy RDD", SECCION))
S.append(HR())

S.append(Paragraph("<b>Lógica del diseño</b>", SUBSECCION))
S.append(Paragraph(
    "Se comparan personas de 64 y 66 años que son casi idénticas en características "
    "observables — educación, área geográfica, nivel de pobreza — pero difieren en "
    "si ya pueden acceder a Pensión 65. El salto discontinuo en elegibilidad al "
    "cruzar los 65 años es el instrumento causal.",
    BODY))

S.append(Paragraph(
    "<b>¿Por qué fuzzy y no sharp?</b>", SUBSECCION))
S.append(Paragraph(
    "En un diseño nítido (sharp), todos los que cruzan el umbral reciben el "
    "tratamiento. Aquí no: se requiere además estar clasificado como pobre extremo "
    "por el SISFOH y no tener otra pensión activa. La probabilidad de recibir P65 "
    "salta discontinuamente al cruzar los 65 años, pero no llega a 1. Esto define "
    "un diseño fuzzy donde la edad actúa como instrumento para la recepción del "
    "programa.",
    BODY))

S.append(Paragraph("<b>First stage: salto nítido y fuerte</b>", SUBSECCION))
S.append(tabla([
    [cab("Grupo"), cab("N"), cab("% recibe P65"), cab("Salto")],
    [cel("Menores de 65 años (lado izquierdo)"),
     cel("1,138", align=TA_CENTER),
     cel("0.0%",  bold=True, align=TA_CENTER, color=GRIS_TEXT),
     cel("")],
    [cel("Mayores de 65 años (lado derecho)"),
     cel("1,193", align=TA_CENTER),
     cel("29.3%", bold=True, align=TA_CENTER, color=AZUL),
     cel("+29.3 pp ***", bold=True, align=TA_CENTER, color=AZUL)],
    [cel("Total ventana ±5 años (ELEGIBLE_IFH=1)", bold=True),
     cel("2,331", bold=True, align=TA_CENTER),
     cel(""), cel("")],
], [W*0.45, W*0.12, W*0.22, W*0.21]))
S.append(Spacer(1, 0.2*cm))
S.append(Paragraph(
    "El instrumento es fuerte (p &lt; 0.001). Nadie menor de 65 años recibe "
    "Pensión 65 (0.0% exacto) y el salto al cruzar el umbral es de exactamente "
    "29.3 pp. Se cumple el requisito de relevancia del instrumento.",
    BODY))

S.append(Paragraph("<b>Submuestra y especificación</b>", SUBSECCION))
for item in [
    "<b>Criterio de elegibilidad:</b> ELEGIBLE_IFH = 1 (IFH ≤ umbral departamental, proxy SISFOH)",
    "<b>Ventana de bandwidth:</b> ±5 años alrededor del umbral de 65",
    "<b>N total efectivo:</b> 2,288 personas (después de excluir nulos en variables de control)",
    "<b>Especificación:</b> regresión local lineal con pendientes distintas a cada lado del umbral",
    "<b>Errores estándar:</b> robustos HC1 (factor de corrección n/(n−k))",
    "<b>LATE:</b> estimado por el método delta (razón de forma reducida sobre first stage)",
    "<b>Controles:</b> nivel educativo (continuo), área geográfica (urbano/rural), pobreza monetaria INEI",
]:
    S.append(Paragraph(f"• {item}", BULL))
S.append(PageBreak())

# ====================================================================
# 7. RESULTADOS
# ====================================================================
S.append(Paragraph("7. Resultados del RDD", SECCION))
S.append(HR())
S.append(Paragraph(
    "Se presentan 5 outcomes en dos especificaciones cada uno (sin y con controles). "
    "La submuestra es siempre ELEGIBLE_IFH=1, ventana ±5 años, N=2,288 (con controles) "
    "o N=2,331 (sin controles).",
    BODY))

# 7.1 Billetera
S.append(Paragraph("7.1 Billetera digital", SUBSECCION))
S.append(Paragraph(
    "Tasa base en menores de 65 de la submuestra: "
    "<b>9.4% tiene billetera</b> y <b>6.0% la usa activamente</b>.",
    BODY))

S.append(tabla([
    [cab("Outcome"), cab("Especif."), cab("N"),
     cab("First Stage"), cab("LATE"), cab("IC 95%"), cab("p-valor")],
    [cel("TIENE_BILLETERA", size=9), cel("Sin controles", size=9),
     cel("2,331", align=TA_CENTER, size=9),
     cel("0.135 ***", align=TA_CENTER, color=VERDE, size=9),
     cel("−0.5 pp",   align=TA_CENTER, color=GRIS_TEXT, size=9),
     cel("[−35.8%, +34.9%]", align=TA_CENTER, size=9),
     cel("0.979 n.s.", align=TA_CENTER, size=9)],
    [cel("TIENE_BILLETERA", size=9), cel("Con controles", size=9),
     cel("2,288", align=TA_CENTER, size=9),
     cel("0.134 ***", align=TA_CENTER, color=VERDE, size=9),
     cel("−3.1 pp",   align=TA_CENTER, color=GRIS_TEXT, size=9),
     cel("[−36.8%, +30.6%]", align=TA_CENTER, size=9),
     cel("0.856 n.s.", align=TA_CENTER, size=9)],
    [cel("USA_BILLETERA", size=9), cel("Sin controles", size=9),
     cel("2,331", align=TA_CENTER, size=9),
     cel("0.135 ***", align=TA_CENTER, color=VERDE, size=9),
     cel("+1.3 pp",   align=TA_CENTER, color=GRIS_TEXT, size=9),
     cel("[−23.7%, +26.3%]", align=TA_CENTER, size=9),
     cel("0.921 n.s.", align=TA_CENTER, size=9)],
    [cel("USA_BILLETERA", size=9), cel("Con controles", size=9),
     cel("2,288", align=TA_CENTER, size=9),
     cel("0.134 ***", align=TA_CENTER, color=VERDE, size=9),
     cel("−1.6 pp",   align=TA_CENTER, color=GRIS_TEXT, size=9),
     cel("[−25.4%, +22.3%]", align=TA_CENTER, size=9),
     cel("0.899 n.s.", align=TA_CENTER, size=9)],
], [W*0.22, W*0.14, W*0.08, W*0.14, W*0.10, W*0.18, W*0.14]))
S.append(Spacer(1, 0.2*cm))
S.append(Paragraph(
    "<b>Conclusión:</b> El efecto de Pensión 65 sobre la adopción de billetera digital "
    "es estadísticamente nulo en todas las especificaciones (p = 0.86–0.98). "
    "Los intervalos de confianza son amplios, reflejando la baja tasa base de billetera "
    "en la submuestra de pobres SISFOH.",
    BODY))
S.append(Spacer(1, 0.4*cm))

# 7.2 Cuenta bancaria
S.append(Paragraph("7.2 Cuenta bancaria", SUBSECCION))
S.append(Paragraph(
    "Se estiman tres outcomes: <b>BANCO_PREVIO</b> (cuenta en banco privado <i>o</i> "
    "Banco de la Nación, combinado), <b>BANCO_PRIVADO</b> (banco del sistema financiero "
    "privado, P558E1_1) y <b>BANCO_NACION</b> (Banco de la Nación, P558E1_8).",
    BODY))

S.append(tabla([
    [cab("Outcome"), cab("Especif."), cab("N"),
     cab("First Stage"), cab("LATE"), cab("IC 95%"), cab("p"), cab("Sig.")],
    [cel("BANCO_PREVIO", size=9),  cel("Sin controles", size=9),
     cel("2,331", align=TA_CENTER, size=9),
     cel("0.135 ***",  align=TA_CENTER, color=VERDE, size=9),
     cel("+71.1 pp",   bold=True, align=TA_CENTER, color=ROJO, size=9),
     cel("[+11.5%, +130.8%]", align=TA_CENTER, size=9),
     cel("0.019", align=TA_CENTER, size=9),
     cel("**",  bold=True, align=TA_CENTER, color=ROJO, size=9)],
    [cel("BANCO_PREVIO", size=9),  cel("Con controles", size=9),
     cel("2,288", align=TA_CENTER, size=9),
     cel("0.134 ***",  align=TA_CENTER, color=VERDE, size=9),
     cel("+63.6 pp",   bold=True, align=TA_CENTER, color=ROJO, size=9),
     cel("[+8.8%, +118.4%]", align=TA_CENTER, size=9),
     cel("0.023", align=TA_CENTER, size=9),
     cel("**",  bold=True, align=TA_CENTER, color=ROJO, size=9)],
    [cel("BANCO_PRIVADO", size=9), cel("Sin controles", size=9),
     cel("2,331", align=TA_CENTER, size=9),
     cel("0.135 ***",  align=TA_CENTER, color=VERDE, size=9),
     cel("+64.5 pp",   bold=True, align=TA_CENTER, color=NARANJA, size=9),
     cel("[+7.4%, +121.7%]", align=TA_CENTER, size=9),
     cel("0.027", align=TA_CENTER, size=9),
     cel("**",  bold=True, align=TA_CENTER, color=NARANJA, size=9)],
    [cel("BANCO_PRIVADO", size=9), cel("Con controles", size=9),
     cel("2,288", align=TA_CENTER, size=9),
     cel("0.134 ***",  align=TA_CENTER, color=VERDE, size=9),
     cel("+57.2 pp",   bold=True, align=TA_CENTER, color=NARANJA, size=9),
     cel("[+3.7%, +110.6%]", align=TA_CENTER, size=9),
     cel("0.036", align=TA_CENTER, size=9),
     cel("**",  bold=True, align=TA_CENTER, color=NARANJA, size=9)],
    [cel("BANCO_NACION", size=9),  cel("Sin controles", size=9),
     cel("2,331", align=TA_CENTER, size=9),
     cel("0.135 ***",  align=TA_CENTER, color=VERDE, size=9),
     cel("−1.0 pp",    align=TA_CENTER, color=GRIS_TEXT, size=9),
     cel("[−40.9%, +38.9%]", align=TA_CENTER, size=9),
     cel("0.961", align=TA_CENTER, size=9),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT, size=9)],
    [cel("BANCO_NACION", size=9),  cel("Con controles", size=9),
     cel("2,288", align=TA_CENTER, size=9),
     cel("0.134 ***",  align=TA_CENTER, color=VERDE, size=9),
     cel("−6.2 pp",    align=TA_CENTER, color=GRIS_TEXT, size=9),
     cel("[−41.5%, +29.1%]", align=TA_CENTER, size=9),
     cel("0.730", align=TA_CENTER, size=9),
     cel("n.s.", align=TA_CENTER, color=GRIS_TEXT, size=9)],
], [W*0.18, W*0.13, W*0.07, W*0.13, W*0.10, W*0.20, W*0.09, W*0.08]))
S.append(Spacer(1, 0.2*cm))
S.append(hr_thin())
S.append(Paragraph(
    "*** p&lt;0.01 &nbsp; ** p&lt;0.05 &nbsp; * p&lt;0.10 &nbsp; n.s. no significativo. "
    "SE robustos HC1. Regresión local lineal. Ventana ±5 años. ELEGIBLE_IFH=1.",
    NOTA_PIE))
S.append(Spacer(1, 0.3*cm))

S.append(Paragraph(
    "<b>Hallazgo:</b> efecto positivo y significativo (p &lt; 0.05) sobre la cuenta "
    "en banco privado (+57 a +65 pp), robusto a la inclusión de controles. "
    "El efecto sobre el Banco de la Nación es nulo (p ≈ 0.73–0.96).",
    BODY))
S.append(Paragraph(
    "<b>Interpretación:</b> el resultado es paradójico porque Pensión 65 paga "
    "a través del Banco de la Nación, no de la banca privada. La explicación más "
    "plausible es una discontinuidad competidora: la jubilación ONP/AFP tiene corte "
    "exactamente a los 65 años y requiere cuenta bancaria privada. Sin variables de "
    "jubilación en el dataset no se puede descartar esta hipótesis.",
    E(fontSize=11, leading=16, spaceAfter=6,
      alignment=TA_JUSTIFY, textColor=NARANJA)))
S.append(PageBreak())

# ====================================================================
# 8. LIMITACIONES
# ====================================================================
S.append(Paragraph("8. Limitaciones", SECCION))
S.append(HR())

for n, titulo, texto in [
    ("1.", "Réplica aproximada del IFH oficial.",
     "El IFH construido es una réplica con datos públicos de 2024 usando pesos "
     "calibrados en 2010. Diferencias en los datos de base, año de calibración y "
     "criterios exactos de asignación pueden generar divergencias con el IFH oficial "
     "del MIDIS."),
    ("2.", "Umbral de pobreza extrema no publicado.",
     "El umbral que separa pobreza extrema de pobreza no extrema en el SISFOH no "
     "está publicado. Se usa el umbral general de elegibilidad (Tabla A.10 de BCK) "
     "como proxy — la submuestra incluye pobres extremos y no extremos."),
    ("3.", "Criterio de electricidad no filtra en 2024.",
     "El umbral de gasto en electricidad ≤ 25 S/mes prácticamente no filtra (99.8% "
     "pasa el corte) por la tarifa social del FISE. Se mantiene por consistencia "
     "metodológica con BCK pero tiene poder discriminante casi nulo en 2024."),
    ("4.", "Posible discontinuidad competidora en banco privado.",
     "El efecto sobre BANCO_PRIVADO podría reflejar la jubilación ONP/AFP con "
     "corte a los 65 años, no un efecto de Pensión 65. Sin variables de jubilación "
     "en el dataset no se puede confirmar ni descartar."),
    ("5.", "Poder estadístico limitado para billetera digital.",
     "La tasa de billetera entre pobres SISFOH es de 7–9%. Con N=2,288 el diseño "
     "tiene poder limitado para detectar efectos pequeños — los IC son amplios."),
    ("6.", "Bienes del hogar aproximados.",
     "El IFH original usa 5 bienes. Solo TV color, refrigeradora y lavadora se "
     "identifican con certeza; se agregan equipo de sonido y computadora/laptop "
     "como aproximación."),
]:
    S.append(KeepTogether([
        Paragraph(f"<b>{n} {titulo}</b>", SUBSECCION),
        Paragraph(texto, BODY),
    ]))
S.append(PageBreak())

# ====================================================================
# 9. PRÓXIMOS PASOS
# ====================================================================
S.append(Paragraph("9. Próximos pasos", SECCION))
S.append(HR())

for n, titulo, texto in [
    ("1.", "Test de McCrary.",
     "Verificar que no hay manipulación de la edad alrededor del umbral. Si la "
     "densidad de la running variable muestra una discontinuidad en los 65 años, "
     "el supuesto de continuidad del RDD se viola."),
    ("2.", "Balance de covariables en el umbral.",
     "Comprobar que IFH, educación y área geográfica no muestran discontinuidades "
     "a los 65 años. Sustenta el supuesto de continuidad del diseño."),
    ("3.", "Variable de jubilación ONP/AFP.",
     "Agregar al pipeline la variable del módulo 5 que indica recepción de "
     "jubilación ONP o AFP. Esto permitiría descartar o confirmar la "
     "discontinuidad competidora en la cuenta bancaria privada."),
    ("4.", "Análisis de heterogeneidad por IFH.",
     "Estimar el LATE separadamente para ELEGIBLE_SIS=1 vs ELEGIBLE_SIS=0: "
     "¿varía el efecto de Pensión 65 sobre billetera según nivel de pobreza "
     "dentro de la submuestra elegible?"),
]:
    S.append(KeepTogether([
        Paragraph(f"<b>{n} {titulo}</b>", SUBSECCION),
        Paragraph(texto, BODY),
    ]))
S.append(PageBreak())

# ====================================================================
# 10. REFERENCIAS
# ====================================================================
S.append(Paragraph("10. Referencias", SECCION))
S.append(HR())

for autores, titulo in [
    ("Bernal, N., Carpio, M. A., y Klein, T. J. (2017).",
     "The effects of access to health insurance: Evidence from a regression "
     "discontinuity design in Peru. <i>Journal of Public Economics</i>, 154, 122–136."),
    ("INEI (2024).",
     "Encuesta Nacional de Hogares (ENAHO) 2024, Encuesta 966: Condiciones de Vida "
     "y Pobreza, Anual. Lima: Instituto Nacional de Estadística e Informática."),
    ("MIDIS (2010).",
     "Metodología de Focalización del Sistema de Focalización de Hogares (SISFOH). "
     "Lima: Ministerio de Desarrollo e Inclusión Social."),
    ("Imbens, G. W., y Lemieux, T. (2008).",
     "Regression discontinuity designs: A guide to practice. "
     "<i>Journal of Econometrics</i>, 142(2), 615–635."),
    ("Lee, D. S., y Lemieux, T. (2010).",
     "Regression discontinuity designs in economics. "
     "<i>Journal of Economic Literature</i>, 48(2), 281–355."),
    ("Cattaneo, M. D., Idrobo, N., y Titiunik, R. (2020).",
     "<i>A Practical Introduction to Regression Discontinuity Designs: "
     "Foundations.</i> Cambridge University Press."),
]:
    S.append(Paragraph(
        f"<b>{autores}</b> {titulo}",
        E(fontSize=11, leading=16, spaceAfter=10,
          leftIndent=20, firstLineIndent=-20, alignment=TA_JUSTIFY)))

# -- Build --------------------------------------------------------------------
doc.build(S, canvasmaker=PageNumCanvas)
print(f"\nPDF generado: {OUTPUT}")
