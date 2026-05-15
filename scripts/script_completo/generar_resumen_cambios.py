"""
Genera un PDF con resumen de cambios: antes vs. después del pipeline actualizado.
Lenguaje sencillo, sin jerga técnica.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

OUTPUT = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "paper", "resumen_hallazgos.pdf"
)
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ── Colores ───────────────────────────────────────────────────────────────────
AZUL       = colors.HexColor("#1a4f8a")
AZUL_CLARO = colors.HexColor("#dce8f5")
VERDE      = colors.HexColor("#1a7a4a")
VERDE_CLARO= colors.HexColor("#d4edda")
NARANJA    = colors.HexColor("#c05c00")
NARANJA_C  = colors.HexColor("#fde8d0")
GRIS       = colors.HexColor("#f2f2f2")
ROJO       = colors.HexColor("#a00000")

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2.0*cm, bottomMargin=2.0*cm
)

styles = getSampleStyleSheet()

def estilo(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=styles[parent], **kw)
    return s

TITULO   = estilo("Titulo",   fontSize=20, textColor=AZUL,
                  spaceAfter=4, alignment=TA_CENTER, leading=26, fontName="Helvetica-Bold")
SUBTIT   = estilo("Subtit",   fontSize=12, textColor=colors.HexColor("#444444"),
                  spaceAfter=10, alignment=TA_CENTER, leading=16)
H1       = estilo("H1",       fontSize=14, textColor=AZUL,
                  spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold")
H2       = estilo("H2",       fontSize=11, textColor=VERDE,
                  spaceBefore=8,  spaceAfter=3, fontName="Helvetica-Bold")
NORMAL   = estilo("Normal2",  fontSize=9.5, leading=14, spaceAfter=4,
                  alignment=TA_JUSTIFY)
BULLET   = estilo("Bullet2",  fontSize=9.5, leading=14, spaceAfter=3,
                  leftIndent=14, bulletIndent=4)
NOTA     = estilo("Nota",     fontSize=8.5, textColor=colors.HexColor("#555555"),
                  leading=12, spaceAfter=3, leftIndent=10)
CELDA_H  = estilo("CeldaH",   fontSize=9,   fontName="Helvetica-Bold",
                  textColor=colors.white,  alignment=TA_CENTER)
CELDA_B  = estilo("CeldaB",   fontSize=9,   leading=13,
                  alignment=TA_CENTER)
CELDA_L  = estilo("CeldaL",   fontSize=9,   leading=13,
                  alignment=TA_LEFT)

story = []

# ══════════════════════════════════════════════════════════════════════════════
# PORTADA
# ══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 1.5*cm))
story.append(Paragraph("Pensión 65 y Billeteras Digitales", TITULO))
story.append(Paragraph("Resumen de hallazgos: antes y después del análisis", SUBTIT))
story.append(HRFlowable(width="100%", thickness=2, color=AZUL))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph(
    "Este documento resume en lenguaje sencillo qué encontró el análisis estadístico "
    "sobre si recibir Pensión 65 hace que las personas mayores adopten billeteras digitales "
    "(como Yape o la Cuenta DNI). Se compara la versión preliminar del estudio con los "
    "resultados reales obtenidos al correr el código con los datos ENAHO 2024.",
    NORMAL
))
story.append(Spacer(1, 0.3*cm))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — ¿DE QUÉ TRATA EL ESTUDIO?
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("1. ¿De qué trata el estudio?", H1))
story.append(Paragraph(
    "Pensión 65 es un programa del Estado peruano que paga S/250 cada dos meses a personas "
    "mayores de 65 años que están en situación de <b>pobreza extrema</b> (clasificadas así "
    "por el sistema SISFOH). Desde 2023, ese pago llega a través de la <b>Cuenta DNI</b> "
    "de Banco de la Nación, que es una billetera digital.",
    NORMAL
))
story.append(Paragraph(
    "La pregunta del estudio es: ¿el simple hecho de <b>cumplir 65 años</b> "
    "(y así volverse elegible para el programa) <b>aumenta la probabilidad de tener "
    "una billetera digital</b>? Para responderla se usó una técnica estadística llamada "
    "<i>Regresión Discontinua</i>, que compara personas justo antes y justo después de "
    "los 65 años.",
    NORMAL
))
story.append(Spacer(1, 0.2*cm))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — LOS DATOS
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("2. Los datos", H1))

datos_tbl = [
    [Paragraph("Dato", CELDA_H), Paragraph("Valor", CELDA_H)],
    [Paragraph("Fuente", CELDA_L), Paragraph("Encuesta ENAHO 2024 (INEI)", CELDA_L)],
    [Paragraph("Total de personas en la encuesta", CELDA_L), Paragraph("117,721", CELDA_L)],
    [Paragraph("Personas con edad válida (muestra completa)", CELDA_L), Paragraph("113,755", CELDA_L)],
    [Paragraph("Personas en pobreza extrema — SISFOH=1 (muestra principal)", CELDA_L), Paragraph("6,717", CELDA_L)],
    [Paragraph("Personas en pobreza extrema cerca de los 65 años (±14 años)", CELDA_L), Paragraph("~1,144", CELDA_L)],
    [Paragraph("¿Qué mide la variable principal?", CELDA_L),
     Paragraph("Si la persona tiene O usa billetera digital (Yape, Plin, Cuenta DNI)", CELDA_L)],
]
t = Table(datos_tbl, colWidths=[9*cm, 7.5*cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("BACKGROUND", (0,1), (-1,-1), GRIS),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, GRIS]),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 7),
]))
story.append(t)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "<b>Nota importante:</b> El estudio se enfoca principalmente en las personas "
    "en <b>pobreza extrema</b> (6,717 personas) porque son las únicas que pueden "
    "recibir Pensión 65. Analizar a toda la población mezclaría el efecto real del "
    "programa con el comportamiento de personas que ni siquiera son elegibles.",
    NOTA
))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — COMPARATIVO ANTES / DESPUÉS
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("3. Antes vs. Después: los números que cambiaron", H1))
story.append(Paragraph(
    "La primera versión del paper usaba estimaciones preliminares como referencia. "
    "Al correr el código completo con los datos reales de ENAHO 2024, los números "
    "cambiaron. Esta tabla resume las diferencias:",
    NORMAL
))
story.append(Spacer(1, 0.15*cm))

comp = [
    [Paragraph("¿Qué número?", CELDA_H),
     Paragraph("Antes (estimación previa)", CELDA_H),
     Paragraph("Después (resultado real)", CELDA_H),
     Paragraph("¿Cambió mucho?", CELDA_H)],

    [Paragraph("Efecto estimado del programa\n(puntos porcentuales)", CELDA_L),
     Paragraph("+2.5 pp", CELDA_B),
     Paragraph("+2.7 pp", CELDA_B),
     Paragraph("Casi igual ✓", CELDA_B)],

    [Paragraph("Error estándar\n(incertidumbre)", CELDA_L),
     Paragraph("±1.8 pp", CELDA_B),
     Paragraph("±2.2 pp", CELDA_B),
     Paragraph("Un poco más\nimpreciso", CELDA_B)],

    [Paragraph("Intervalo de confianza 95%", CELDA_L),
     Paragraph("[-1.0%, +6.0%]", CELDA_B),
     Paragraph("[-2.6%, +6.4%]", CELDA_B),
     Paragraph("Ligeramente\nmás amplio", CELDA_B)],

    [Paragraph("Personas cerca del corte\n(tamaño efectivo)", CELDA_L),
     Paragraph("~1,229", CELDA_B),
     Paragraph("~1,144", CELDA_B),
     Paragraph("Casi igual ✓", CELDA_B)],

    [Paragraph("Ventana de edad analizada\n(bandwidth óptimo)", CELDA_L),
     Paragraph("±14.5 años", CELDA_B),
     Paragraph("±13.95 años", CELDA_B),
     Paragraph("Casi igual ✓", CELDA_B)],

    [Paragraph("% de personas elegibles\ncerca de los 65 años", CELDA_L),
     Paragraph("~22.5%", CELDA_B),
     Paragraph("~5%", CELDA_B),
     Paragraph("¡Cambio grande!\nSolo 1 de cada 20", CELDA_B)],

    [Paragraph("Efecto 'real' estimado\nsobre beneficiarios\n(LATE implícito)", CELDA_L),
     Paragraph("+14.8 pp", CELDA_B),
     Paragraph("+71.9 pp", CELDA_B),
     Paragraph("Número muy alto,\nver explicación §4", CELDA_B)],

    [Paragraph("¿El resultado pasa la\nprueba de aleatoriedad?", CELDA_L),
     Paragraph("p = 0.43", CELDA_B),
     Paragraph("p = 0.60", CELDA_B),
     Paragraph("No significativo\nen ningún caso", CELDA_B)],

    [Paragraph("Estimación en muestra\ncompleta (todos)", CELDA_L),
     Paragraph("-0.6 pp", CELDA_B),
     Paragraph("-0.2 pp", CELDA_B),
     Paragraph("Cerca de cero\nen ambos casos", CELDA_B)],
]

tc = Table(comp, colWidths=[5.2*cm, 3.3*cm, 3.3*cm, 4.7*cm])
tc.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#bbbbbb")),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    # Fila del % elegibles — destacar
    ("BACKGROUND", (0,6), (-1,6), NARANJA_C),
    # Fila del LATE — destacar
    ("BACKGROUND", (0,7), (-1,7), colors.HexColor("#fff0c0")),
]))
story.append(tc)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — EL HALLAZGO MÁS IMPORTANTE
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("4. El hallazgo más importante: solo el 5% son elegibles", H1))
story.append(Paragraph(
    "Este es el resultado más relevante del análisis y explica por qué el estudio "
    "tiene una limitación seria:",
    NORMAL
))

box_data = [[Paragraph(
    "De cada 100 personas mayores de 65 años que aparecen en la encuesta ENAHO "
    "cerca del corte de edad, <b>solo 5 están clasificadas como pobreza extrema "
    "(SISFOH=1)</b>. Las otras 95 no son elegibles para Pensión 65.",
    estilo("BoxText", fontSize=10, leading=15, textColor=AZUL,
           fontName="Helvetica-Bold", alignment=TA_CENTER)
)]]
box = Table(box_data, colWidths=[16.3*cm])
box.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), AZUL_CLARO),
    ("BOX", (0,0), (-1,-1), 1.5, AZUL),
    ("TOPPADDING", (0,0), (-1,-1), 12),
    ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ("LEFTPADDING", (0,0), (-1,-1), 14),
    ("RIGHTPADDING", (0,0), (-1,-1), 14),
]))
story.append(Spacer(1, 0.15*cm))
story.append(box)
story.append(Spacer(1, 0.2*cm))

story.append(Paragraph(
    "¿Por qué esto es un problema? Imagina que intentas detectar si un medicamento "
    "funciona, pero en tu estudio el 95% de los pacientes no tomó ese medicamento. "
    "El efecto real del medicamento quedaría diluido y sería casi invisible en los datos. "
    "Eso es exactamente lo que pasa aquí.",
    NORMAL
))
story.append(Paragraph(
    "La versión preliminar del paper asumía que el 22.5% de las personas cerca del "
    "corte eran elegibles. El dato real es 5%. Esta diferencia hace que el número "
    "llamado 'LATE' (efecto sobre los beneficiarios reales) suba de 14.8 pp a 71.9 pp. "
    "Ese número tan alto <b>no significa que el programa sea mágico</b> — significa que "
    "la encuesta ENAHO no tiene suficientes personas elegibles cerca de los 65 años "
    "como para detectar el efecto con este método.",
    NORMAL
))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — ¿QUÉ ENCONTRÓ EL ANÁLISIS?
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("5. ¿Qué encontró el análisis en términos simples?", H1))

hallazgos = [
    [Paragraph("Hallazgo", CELDA_H), Paragraph("En palabras sencillas", CELDA_H)],

    [Paragraph("Efecto positivo\npero no confirmado\nestadísticamente", CELDA_L),
     Paragraph(
         "Las personas en pobreza extrema que cumplen 65 años tienen una probabilidad "
         "2.7 puntos porcentuales más alta de tener billetera digital que las que están "
         "justo por debajo de los 65. Pero el margen de error es tan grande (±4 pp) que "
         "no podemos descartar que sea pura casualidad.",
         CELDA_L)],

    [Paragraph("Uso activo de\nbilletera: cero", CELDA_L),
     Paragraph(
         "Casi ninguna persona en pobreza extrema mayor de 65 años reportó "
         "usar activamente una billetera para pagar. Tienen la cuenta, pero no la usan. "
         "El programa llega al 'alta' pero no al 'uso habitual'.",
         CELDA_L)],

    [Paragraph("Zona urbana vs.\nzona rural", CELDA_L),
     Paragraph(
         "Sorprendentemente, el efecto estimado en zonas rurales (+3.2 pp) es "
         "numéricamente mayor que en zonas urbanas (+1.9 pp). Pero ambos tienen "
         "márgenes de error tan grandes que no se puede concluir nada con certeza. "
         "Se necesitan más datos.",
         CELDA_L)],

    [Paragraph("Muestra completa\n(toda la encuesta)", CELDA_L),
     Paragraph(
         "Si se analiza a toda la población (no solo a los pobres extremos), "
         "el efecto es prácticamente cero (-0.2 pp). Esto era esperado: la mayoría "
         "de la gente en la encuesta no recibe ni puede recibir Pensión 65, "
         "entonces su comportamiento 'aplana' el efecto real.",
         CELDA_L)],

    [Paragraph("Departamentos\n(efecto por región)", CELDA_L),
     Paragraph(
         "Al controlar por diferencias entre departamentos, el efecto estimado "
         "es +1.6 pp. Sigue siendo positivo pero tampoco alcanza significancia "
         "estadística.",
         CELDA_L)],
]

th = Table(hallazgos, colWidths=[4.5*cm, 12.3*cm])
th.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), VERDE),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, VERDE_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#bbbbbb")),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 7),
]))
story.append(th)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — SEÑAL DE ALERTA
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("6. Una señal de alerta en los datos", H1))
story.append(Paragraph(
    "El análisis encontró algo inesperado al verificar que los grupos (mayores y "
    "menores de 65 años) fueran comparables:",
    NORMAL
))

alerta_data = [[Paragraph(
    "⚠  Los hogares con personas mayores de 65 años en pobreza extrema tienen "
    "<b>12.5 puntos porcentuales más de acceso a internet</b> que los hogares "
    "con personas menores de 65 en pobreza extrema.\n\n"
    "Esto no es señal de trampa o error, pero sí una limitación: probablemente "
    "los hogares con abuelos tienen también hijos adultos que pagan el internet. "
    "Significa que 'acceso a internet' no es una variable neutral en este análisis, "
    "y los resultados que incluyen esa variable como control deben leerse con cuidado.",
    estilo("AlertText", fontSize=9.5, leading=14, textColor=ROJO,
           alignment=TA_JUSTIFY)
)]]
alerta = Table(alerta_data, colWidths=[16.3*cm])
alerta.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#fff5f5")),
    ("BOX", (0,0), (-1,-1), 1.5, ROJO),
    ("TOPPADDING", (0,0), (-1,-1), 10),
    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ("LEFTPADDING", (0,0), (-1,-1), 12),
    ("RIGHTPADDING", (0,0), (-1,-1), 12),
]))
story.append(alerta)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — ¿QUÉ SIGNIFICA TODO ESTO?
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("7. ¿Qué significa todo esto?", H1))

story.append(Paragraph(
    "<b>Lo que SÍ podemos decir:</b>", H2
))
for txt in [
    "El efecto estimado es <b>positivo</b>: cruzar los 65 años en pobreza extrema "
    "parece estar asociado con mayor probabilidad de tener billetera digital.",
    "Ese efecto es coherente con la idea de que el pago digital de Pensión 65 "
    "genera una cuenta activa (la Cuenta DNI) que el beneficiario registra como "
    "billetera.",
    "El análisis con datos reales confirma la dirección del efecto que la versión "
    "preliminar anticipaba.",
    "La calidad del diseño estadístico (discontinuidad de edad) es válida: no hay "
    "evidencia de manipulación de las edades reportadas.",
]:
    story.append(Paragraph(f"• {txt}", BULLET))

story.append(Spacer(1, 0.15*cm))
story.append(Paragraph(
    "<b>Lo que NO podemos decir (todavía):</b>", H2
))
for txt in [
    "No podemos confirmar que el efecto sea <b>estadísticamente significativo</b>: "
    "el margen de error es demasiado grande para descartar que sea casualidad.",
    "No sabemos si el efecto es grande o pequeño para los beneficiarios reales, "
    "porque la encuesta ENAHO tiene muy pocas personas elegibles cerca del corte (5%).",
    "No podemos distinguir con certeza si el efecto es mayor en ciudades o en zonas "
    "rurales: ambos grupos tienen muestras insuficientes.",
    "No podemos decir que la gente <b>use</b> la billetera: el uso activo es "
    "prácticamente cero en este grupo.",
]:
    story.append(Paragraph(f"• {txt}", BULLET))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — ¿QUÉ HACER A CONTINUACIÓN?
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("8. ¿Qué se recomienda hacer a continuación?", H1))

recom = [
    [Paragraph("Recomendación", CELDA_H), Paragraph("Por qué", CELDA_H)],
    [Paragraph("Combinar los datos de\nENAHO con el registro\nde beneficiarios de MIDIS",
               CELDA_L),
     Paragraph("El problema principal es que la encuesta no identifica quién "
               "realmente recibe el pago. Si se cruzan los datos, se puede "
               "estimar el efecto directamente sobre los beneficiarios reales.",
               CELDA_L)],
    [Paragraph("Juntar varias rondas\nde ENAHO (2022-2024)",
               CELDA_L),
     Paragraph("Más años = más personas pobres extremas cerca del corte = "
               "resultados más precisos. Con 3 años se podría triplicar el "
               "tamaño de la muestra útil.",
               CELDA_L)],
    [Paragraph("Recoger datos sobre\n¿cuánto usan la billetera?",
               CELDA_L),
     Paragraph("Actualmente la encuesta solo dice si tienen la billetera, "
               "no si la usan frecuentemente. Un módulo específico sobre "
               "transacciones digitales en ENAHO daría información mucho más rica.",
               CELDA_L)],
    [Paragraph("Estudio específico\nen zonas rurales",
               CELDA_L),
     Paragraph("El posible efecto rural merece atención porque el programa "
               "llega a zonas donde casi no había bancos. Una evaluación "
               "enfocada en comunidades rurales con y sin cobertura de agentes "
               "bancarios sería muy valiosa.",
               CELDA_L)],
]
tr = Table(recom, colWidths=[4.8*cm, 12.0*cm])
tr.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), NARANJA),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, NARANJA_C]),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 7),
]))
story.append(tr)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — RESUMEN EN UNA FRASE
# ══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 0.3*cm))
story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL))
story.append(Spacer(1, 0.2*cm))

resumen_data = [[Paragraph(
    "CONCLUSIÓN EN UNA FRASE\n\n"
    "El análisis sugiere que Pensión 65 tiene un efecto positivo en la adopción "
    "de billeteras digitales entre los pobres extremos, pero los datos de ENAHO "
    "no son suficientes para confirmarlo: de cada 100 personas mayores de 65 en "
    "la encuesta, solo 5 son elegibles para el programa, lo que hace que el "
    "efecto sea casi invisible en la muestra disponible.",
    estilo("ResText", fontSize=10.5, leading=16, textColor=AZUL,
           fontName="Helvetica-Bold", alignment=TA_CENTER)
)]]
res_tbl = Table(resumen_data, colWidths=[16.3*cm])
res_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), AZUL_CLARO),
    ("BOX", (0,0), (-1,-1), 2, AZUL),
    ("TOPPADDING", (0,0), (-1,-1), 16),
    ("BOTTOMPADDING", (0,0), (-1,-1), 16),
    ("LEFTPADDING", (0,0), (-1,-1), 16),
    ("RIGHTPADDING", (0,0), (-1,-1), 16),
]))
story.append(res_tbl)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "Documento generado automáticamente a partir de los resultados del pipeline "
    "ENAHO 2024 — Pensión 65 RDD. Mayo 2026.",
    estilo("Pie", fontSize=7.5, textColor=colors.HexColor("#888888"),
           alignment=TA_CENTER)
))

# ── Build ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"PDF generado: {os.path.abspath(OUTPUT)}")
