# Pensión 65 → Adopción de billetera digital — Notas de trabajo

Documento de continuidad entre Alexander, su coautora, y Claude Code.
Última actualización: 2026-05-21.

---

## ⚠️ ACTUALIZACIÓN CRÍTICA (2026-05-21) — Leer ANTES de tocar nada

**Descubrimos un error conceptual que afecta el diseño del paper y la
limpieza de datos.**

### El error

El paper actual (y el script `script_completo/script.py`) trata a
`POBREZA=1` como si fuera la categoría SISFOH de Pensión 65. **No lo es.**

| Variable | Qué mide en realidad |
|---|---|
| `POBREZA` (Sumaria) | Pobreza **monetaria** — gasto pc vs línea de pobreza alimentaria/total. Calculada por INEI dentro de ENAHO, *ex post*. |
| `POBREZAV` (Sumaria) | Igual que POBREZA + categoría "vulnerable". 4 categorías. |
| **SISFOH CSE** | Proxy means test de MIDIS para elegibilidad social. **NO está en ENAHO**. |

### Evidencia empírica del problema

De los 4,419 receptores reales de Pensión 65 ≥65 años en ENAHO 2024:

| | Receptores | % del total |
|---|---|---|
| POBREZA=1 (extremo monetario) | 502 | **11.3%** |
| POBREZA=2 (pobre monetario) | 1,113 | 25.2% |
| POBREZA=3 (no pobre monetario) | **2,805** | **63.5%** |

Restringir el análisis a POBREZA=1 (como hace el `df_main` actual) **excluye
al 88.7% de los receptores reales**. Tres razones plausibles:

1. **Reverse causality / post-tratamiento**: recibir S/250/mes durante años
   eleva el gasto del hogar → el receptor sube de POBREZA=1 a 2 o 3.
2. **SISFOH ≠ pobreza monetaria**: el proxy means test de MIDIS se basa
   en características de vivienda y activos, no en gasto corriente.
3. **Misclassification** en ambos sistemas.

### Decisión tomada

**El "main dataset" del análisis NO se restringe por POBREZA.** Usamos la
muestra completa con fuzzy RDD usando `P5567A` (recepción a nivel persona)
como tratamiento endógeno y `1(EDAD≥65)` como instrumento.

La variable `POBREZA` (o mejor, un proxy SISFOH PCA con variables
**predeterminadas** de vivienda) entra como **heterogeneidad descriptiva**,
no como restricción primaria del estimand.

### Qué hay que cambiar en el código

Resumen — instrucciones detalladas al final de este documento (sección 12).

1. **`scripts/script_completo/script.py`**: dejar de construir
   `df_main = df_rdd[df_rdd["POBREZA"]==1]`. Construir en su lugar un único
   dataset analítico con todas las variables nuevas (`RECIBE_P65_PERSONA`,
   `RECIBE_P65_HOGAR`, `RECIBE_JUNTOS_HOGAR`, `INGTPU03`).
2. **`paper/main.tex`**: corregir cada mención de "SISFOH extreme-poor
   (POBREZA=1)" — POBREZA es monetaria, no SISFOH. Reescribir abstract,
   sección 3.2 (Sample Construction), sección 4.1 (Identification), sección
   5.2 (Subgroup Analysis).
3. **Tablas**: rehacer Table 2 (Main RDD), Table 3 (Heterogeneidad).

---

## 1. ¿De qué va el paper?

RDD sobre la elegibilidad de Pensión 65 (corte de edad 65 años) y la adopción
de billetera digital (Yape/Plin/Cuenta DNI), usando ENAHO 2024.

- **Outcome principal**: `TIENE_BILLETERA` (tenencia OR uso; combina
  `P558E1_9` y `P558Hk_7` para k=1..12 del módulo 5).
- **Running variable**: edad en años (`EDAD`).
- **Cutoff**: 65.
- **Datos**: ENAHO 2024 — módulos 01, 02, 03, 05, 18, 34 (Sumaria).
- **Estado actual del PDF**: `paper/paper_actualizado.pdf` (round 4 del
  pipeline de revisión). Reviewers piden MAJOR_REVISIONS — ver
  `reviews/editorial_decision_r4.md`.

---

## 2. El problema central que estamos resolviendo

**"Cómo crear el grupo de análisis."** Lo que hace el paper actual:

| Muestra | Diseño | Resultado |
|---|---|---|
| `df_full` (113,755) | Sharp RDD edad 65 sobre todo ENAHO | ITT = −0.002 (null) |
| `df_main` (POBREZA=1, 6,717) | Heterogeneidad (mal etiquetado como SISFOH) | ITT = +0.027 (NS) |
| RDD2 (≥65, 14,088) | Sharp RDD sobre proxy PCA del SISFOH | +0.004 (null) |

**Por qué este diseño falla**:

1. El diseño es **fuzzy**, no sharp (edad ≥65 *y* SISFOH extrema pobreza).
2. No tenía first-stage explícito (qué % efectivamente recibe el bono).
3. **Restringir por POBREZA=1 es post-tratamiento** — excluye al 88.7% de
   receptores. Ver actualización crítica arriba.
4. Confound de cohorte: en cross-section, edad 64 vs 66 = años de nacimiento
   distintos → adopción digital distinta por exposición vital.
5. Discontinuidades competidoras a los 65: AFP, ONP, SIS+65.

**El Google Sheet de la coautora** muestra que ninguno de los 4 estudios
peruanos relevantes (Inquilla & Pelayo 2020, Bando-Galiani-Gertler 2020,
Torres & Salinas 2016, Oscco 2024) usa "ENAHO completo + RDD edad" como
muestra primaria. Restringen por elegibilidad **observada** (recepción
autorreportada) o usan SISFOH real como running variable.

---

## 3. Lo que se descubrió en el Paso 0

**ENAHO 2024 SÍ identifica beneficiarios de Pensión 65.** Dos variables:

| Variable | Módulo | Nivel | Valor |
|---|---|---|---|
| `INGTPU03` | 34 (Sumaria) | Hogar | Ingreso anual por Pensión 65; >0 si receptor |
| `P5567A` | 05 (Empleo) | **Persona** | =1 si la persona recibe Pensión 65 |

Validación: 3,564 hogares receptores en muestra → 902K expandido a población
(comparado con 750K oficiales MIDIS). Monto mediano S/. 1,506/año = S/.
251/mes ≈ S/. 250 del diseño del programa. ✓

**First stage a nivel persona** (% que recibe Pensión 65):

```
Edad   N       % recibe
63     1032    0.0%
64     1070    0.0%
─────────────────── ← cutoff
65     1023    3.8%
66      887   16.0%   ← salto real
70      805   26.6%
80      379   45.9%
```

El first-stage es nítido a nivel persona (a nivel hogar está más diluido
por miembros menores de 65).

---

## 4. Lo que se hizo en el Paso 1

Script: **`scripts/paso1_fuzzy_rdd.py`** — comparación de 3 candidatos de
grupo de análisis con first-stage explícito.

Output: `data/clean/paso1_comparacion_candidatos.csv`.

### Resultados (h=14, kernel triangular, HC1 SE)

| | A — Full | B — POBREZA=1 | C — POBREZA in {1,2} |
|---|---|---|---|
| N en bandwidth | 27,214 | 1,213 | 5,119 |
| First stage | +0.104 | +0.258 | +0.202 |
| First-stage F | ~300 | ~50 | ~138 |
| Reduced form | +0.0015 | +0.0285 | +0.0194 |
| RF CI | [−0.02, +0.02] | [−0.01, +0.06] | [−0.01, +0.04] |
| LATE | +0.014 | +0.111 | +0.096 |
| LATE CI | [−0.17, +0.20] | [−0.03, +0.25] | [−0.03, +0.22] |

### Validaciones

- **Placebo Juntos** (`INGTPU01`, no depende de edad ≥65): salto en el corte
  = +0.009 (CI [−0.003, +0.021]). ✓ El corte de edad no genera
  discontinuidades espurias.
- **Sensibilidad de bandwidth** (Candidato B): tau estable entre +0.022 y
  +0.038 para h ∈ {7,10,14,18,24}.

### Recomendación CORREGIDA del grupo de análisis

**Candidato A (Full sample) como muestra primaria del fuzzy RDD.** El LATE
de +0.014 es interpretable como el efecto del programa entre compliers en
la población general — null real, no diluido, porque el first-stage es
masivo (F~300) y el reduced form sigue siendo ~0.

B y C **NO son** restricciones de elegibilidad — son cortes post-tratamiento
sesgados (ver sección crítica arriba). Pasan a ser **análisis de
heterogeneidad descriptivos**, no especificaciones primarias.

---

## 4.5. Nueva línea de trabajo: replicar SISFOH IFH (Bernal-Carpio-Klein 2017)

**Motivación**: el problema POBREZA monetaria ≠ SISFOH se resuelve si
construimos nuestro propio puntaje SISFOH a partir de características
predeterminadas de vivienda. Bernal, Carpio y Klein (2017, JPubE Online
Appendix F, Tablas A.8/A.9/A.10) publicaron **los pesos exactos del IFH**
(Índice de Focalización de Hogares) usados por SISFOH 2010. Eso nos
permite replicar el score sin pedir nada a INEI.

PDF de referencia (no commiteado por copyright):
  `lit_review/1-s2.0-S0047272717301299-mmc1.pdf`

### Estructura del IFH (BCK 2017, Apéndice F)

- 7-11 variables categóricas de vivienda, servicios, activos y educación
- 3 conjuntos de pesos según área: Lima Metropolitana / otras áreas
  urbanas / áreas rurales
- IFH raw = suma ponderada de las dummies de cada categoría
- IFH estandarizado en [0, 100] por **cluster** (15 clusters definidos por
  SISFOH-2010 agrupando áreas con pobreza monetaria similar en 2009)
- Hogar es SIS-elegible si IFH_std ≤ threshold (Tabla A.10)
- Lima threshold = 55, rurales típicos 33-38, urbanos típicos 42-52

### Plan (7 pasos)

| Paso | Estado | Output |
|---|---|---|
| 1. Transcribir pesos Tablas A.8/A.9/A.10 | ✅ HECHO | `scripts/ifh_weights.py` |
| 2. Extraer variables crudas ENAHO 2024 | ✅ HECHO | `data/clean/ifh_raw_variables.csv` (regenerable) |
| 3. Asignar cluster geográfico (1-15) | PENDING | requiere mapeo ubigeo → cluster (pedir a INEI o aproximar con DOMINIO × AREA) |
| 4. Computar IFH_RAW e IFH_STD | PENDING | `data/clean/ifh_2024.csv` |
| 5. Aplicar umbrales por cluster | PENDING | flag `ELIGIBLE_SIS` |
| 6. Validar contra POBREZA y receptores P65 | PENDING | `data/clean/ifh_validation.md` |
| 7. Integrar como running variable RDD (Bando-style) o restricción de muestra | PENDING | tablas nuevas en paper |

### Paso 1 hecho — pesos transcritos

`scripts/ifh_weights.py` contiene:
- `WEIGHTS_LIMA` (11 variables: combustible, agua, paredes, desagüe,
  miembros con seguro, bienes, **teléfono fijo**, techo, educación jefe,
  piso, hacinamiento)
- `WEIGHTS_URBAN` (10 variables: igual que Lima sin teléfono fijo)
- `WEIGHTS_RURAL` (7 variables: combustible, miembros seguro, bienes,
  educación jefe, **educación máx hogar**, **electricidad**, **piso de
  tierra**)
- `THRESHOLDS_BY_CLUSTER` (15 clusters, Tabla A.10)
- `CLUSTER_AREA` (provisional cluster → lima/urban/rural)
- `VARS_BY_AREA` (qué variables aplican a cada área)

Validación al importar el módulo: cada area tiene todas sus variables
declaradas con pesos completos.

Notas honestas:
- Hacinamiento en URBAN reusa pesos de Lima (Tabla A.9 no especifica
  pesos urbanos separados). Conservador.
- `bienes_riqueza`: BCK no lista los 5 items canónicos; usamos TV color,
  equipo de sonido, computadora/laptop, refrigeradora, lavadora.
- `CLUSTER_AREA` es provisional; confirmar con SISFOH (2010) o INEI.

### Paso 2 hecho — variables IFH extraídas

`scripts/paso2_build_ifh.py` produce `data/clean/ifh_raw_variables.csv`
(33,340 hogares × 27 columnas). Mapea cada variable BCK a su código
ENAHO 2024:

| Variable BCK | Código ENAHO | Categorías |
|---|---|---|
| Paredes | P102 | 9 → 8 BCK |
| Piso | P103 | 7 → 7 BCK (parquet/vinílico/.../tierra) |
| Techo | P103A | 8 → 7 BCK (concreto/tejas/.../paja) |
| Agua | P110 | 8 → 7 BCK (dentro/fuera/río/...) |
| Desagüe | P111A | 7 → 6 BCK |
| Combustible | P113A | 8 → 6 BCK (electricidad/gas/leña/...) |
| Electricidad | P1121 | 0/1 → sí/no |
| Teléfono fijo | P1141 | 0/1 → sí/no |
| Hacinamiento | MIEPERHO / P104 | continuo → 5 bins BCK |
| Educación jefe | M03 P301A, filtrado a P203==1 | 12 → 7 BCK |
| Educación max | M03 P301A, max por hogar | 12 → 5 BCK (rural variant) |
| Miembros con seguro | M04 P4191-P4198 **excluyendo P4195 (SIS)** | conteo → 5 bins |
| Bienes riqueza | M18 P612N ∈ {2,4,7,12,13} | conteo → 6 bins |
| Piso tierra | P103==6 | 0/1 → sí/no |

**Filtro crítico**: M01 trae 44,731 hogares pero ~11K son fantasma
(RESULT in {3,4,5,6,7} = rechazo/ausente/etc.). Filtramos a 33,340 con
entrevista válida (RESULT in {1,2} y P102 no-blank).

**Filtro SISFOH crítico** (footnote 2 de BCK 2017): al contar miembros
con seguro, SE EXCLUYE el SIS (P4195). Esto se respeta en
`load_m04_seguro()`. Razón: si incluyéramos SIS, la variable IFH se
volvería endógena a la propia política de aseguramiento que dispara
SIS en hogares pobres.

### Próximo paso: 3

Asignar cluster geográfico (1-15) a cada hogar. Opciones:
1. Pedirla a INEI vía contacto de Alexander (1 línea adicional al
   pedido SISFOH ya pendiente).
2. Aproximarla con `DOMINIO × AREA` derivado de ENAHO (8 DOMINIOs × 2
   áreas ≈ 16 grupos, no idéntico pero cercano).
3. Reconstruirla del documento SISFOH (2010) si está accesible.

Una vez resuelto Paso 3, Paso 4 (calcular IFH) es trivial: tomar las
categorías ya construidas en Paso 2, mapearlas a pesos según área del
cluster, sumar, estandarizar a [0, 100] por cluster.

---

## 5. Qué falta hacer (en orden recomendado)

### Paso 2 — Limpieza de datos corregida [PRIORITY — para coautora]

Ver sección 12 al final con instrucciones concretas.

Resumen: actualizar `scripts/script_completo/script.py` para que:
- Extraiga `INGTPU03` de Sumaria y `P5567A` de Módulo 5.
- Construya `RECIBE_P65_PERSONA`, `RECIBE_P65_HOGAR`, `RECIBE_JUNTOS_HOGAR`.
- Persista UN SOLO `main_dataset.csv` con `SAMPLE_FLAG` para A/B/C en lugar
  de dos archivos (`df_full`, `df_main`).
- No re-tratar POBREZA=1 como "SISFOH eligible".

### Paso 3 — Auditar competing discontinuities a los 65 [PENDING]

AFP / ONP / SIS+65 / otros programas con corte exactamente en 65.
Riesgo: si existen, el salto en TIENE_BILLETERA puede no ser atribuible
solo a Pensión 65 → viola exclusión.

Acción concreta:
- Estimar RDD sobre RECIBE_JUNTOS (placebo, ya hecho — pasa), pero también
  sobre indicadores de AFP/ONP. Si encuentras saltos a los 65, agregarlos
  como controles o como caveat en Limitations.

### Paso 4 — Integrar al paper [PENDING]

Una vez la limpieza de datos esté actualizada:

1. **Tabla 2 nueva** con tres filas: First stage (FS) + Reduced form (RF) +
   LATE = RF/FS. Para la muestra A (primaria).
2. **Abstract** reescrito: pasa de "null precisamente estimado" a "fuzzy
   RDD con first-stage F~300 entrega LATE +0.014 (CI [−0.17, +0.20]) —
   no rechazamos nulo; cota superior excluye efectos >+20pp en compliers".
3. **Sección 3.2 (Sample Construction)**: eliminar lenguaje de "SISFOH
   extreme-poor" cuando refiere a POBREZA=1. Reemplazar `df_full`/`df_main`
   por descripción del nuevo `main_dataset.csv` con SAMPLE_FLAG.
4. **Sección 4 (Strategy)**: re-especificar como fuzzy RDD. Agregar
   primera-etapa explícita.
5. **Sección 5 (Results)**: reportar A como primaria; B y C como
   heterogeneidad post-tratamiento (con caveat).
6. **Sección 6 (Discussion)**: re-enmarcar el null como "underpowered
   detection" considerando que el RF es ~0 en la muestra completa con
   first-stage masivo.

### Paso 5 — Placebo pre-rollout (ENAHO 2018) [PENDING]

Confound de cohorte. Bajar Sumaria-2018 + módulo 5 de 2018 desde INEI,
correr exactamente el mismo RDD. Si hay salto significativo en 2018 (cuando
Yape/Plin todavía no era masivo), es cohorte y el null se vuelve real.

### Paso 6 — Atender los puntos MUST del editor [PENDING]

Lista completa en `reviews/editorial_decision_r4.md`. Los críticos son:
- Kolesar-Rothe (2018) honest CI por running variable discreta
- Minimum detectable effect (MDE) a 80% power
- Inconsistencias de bandwidth/CI entre Table 3 y Table 4
- Causal overclaiming en abstract y discussion

---

## 6. Archivos clave del proyecto

```
.
├── CLAUDE.md                          ← este archivo (auto-cargado por Claude Code)
├── README.md                          (vacío, no tocar todavía)
├── paper/
│   ├── main.tex                       ← el paper (necesita reescritura sección 3-6)
│   ├── main.pdf, paper_actualizado.pdf
│   ├── tables/                        ← tablas LaTeX (necesitan regenerarse)
│   └── figures/                       ← rdplot, mccrary, etc.
├── scripts/
│   ├── script_completo/script.py      ← pipeline original (necesita actualización — ver §12)
│   └── paso1_fuzzy_rdd.py             ← NUEVO (Paso 1, fuzzy RDD comparativo)
├── data/clean/
│   ├── results_summary.md             ← resumen numérico del paper actual (a actualizar)
│   └── paso1_comparacion_candidatos.csv  ← NUEVO (output Paso 1)
├── reviews/                           ← 4 rondas de reviews
├── strategy/                          ← memos metodológicos
└── evaluation/                        ← evaluaciones del diseño inicial
```

### Datos crudos de ENAHO

El script de Alexander los descarga a `data/clean/_raw_extracted/`. Para
re-ejecutar Paso 1 sin re-descargar todo, `paso1_fuzzy_rdd.py` apunta a
`C:\Users\Alexander\AppData\Local\Temp\enaho2024_check\`.

**Si abrís el proyecto en otra máquina**, ajustá `RAW_DIR` en la línea 23
de `scripts/paso1_fuzzy_rdd.py`, o re-descargá con:

```bash
mkdir -p /tmp/enaho2024_check && cd /tmp/enaho2024_check
for mod in 01 02 05 34; do
  curl -sS -L -A "Mozilla/5.0" -o m${mod}.zip \
    "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV/966-Modulo${mod}.zip"
  unzip -o -q m${mod}.zip
done
```

---

## 7. Cómo continuar el trabajo (instrucciones para Claude Code)

Si abrís este proyecto en una sesión nueva de Claude Code, empezá por:

1. **Leer este archivo completo** (auto-cargado por Claude Code al abrir el repo).
2. **Mirar la sección crítica al inicio** sobre POBREZA vs SISFOH.
3. **Revisar la sección 12** si el plan es actualizar la limpieza de datos.
4. **No re-correr `scripts/script_completo/script.py`** salvo que sea para
   regenerar con las correcciones de §12.
5. **Sí podés correr `scripts/paso1_fuzzy_rdd.py`** — es focalizado y rápido
   (~2 min con los datos ya descargados).

### Variables clave del análisis (referencia rápida)

| Variable | Origen | Significado |
|---|---|---|
| `EDAD` | M02 / P208A | Edad en años (running variable) |
| `running_centered` | derivada | `EDAD - 65` |
| `RECIBE_P65_PERSONA` | **M05 / P5567A** | =1 si persona recibe Pensión 65 |
| `RECIBE_P65_HOGAR` | **Sumaria / INGTPU03** | =1 si hogar recibe Pensión 65 |
| `RECIBE_JUNTOS_HOGAR` | Sumaria / INGTPU01 | Placebo (no edad-dependiente) |
| `TIENE_BILLETERA` | M05 / P558E1_9 ∨ P558Hk_7 | Outcome combinado (tenencia OR uso) |
| `USA_BILLETERA` | M05 / P558Hk_7 | Solo uso activo |
| `POBREZA` | Sumaria | **MONETARIA** — 1=ext pobre, 2=pobre, 3=no pobre. NO es SISFOH. |
| `POBREZAV` | Sumaria | + vulnerabilidad — 1=ext pobre, 2=pobre, 3=no pobre vulnerable, 4=no pobre no vulnerable |
| `INGRESO_PC` | Sumaria | `INGHOG2D / MIEPERHO` |
| `FACTOR07` | Sumaria | Factor de expansión población |

### Convenciones

- Kernel triangular siempre.
- Local-linear como baseline; quadrático solo robustness.
- SE: HC1 en local-linear; rdrobust con bias-corrected CI cuando esté
  disponible (en máquinas con numba/numpy compatibles).
- Bandwidth: `h*=14.24` del paper actual; replicamos con h=14 en Paso 1.

---

## 8. Decisiones tomadas (para no re-discutir)

- **Outcome primario**: `TIENE_BILLETERA` combinado (tenencia OR uso).
  Decisión del paper actual, la mantenemos. Justificación: el BCRP/INEI
  2024 reporta ~46% adopción combinada, lo que requiere ambas dimensiones.
- **Diseño primario REVISADO**: fuzzy RDD edad con `P5567A` como
  tratamiento endógeno, sobre **muestra completa** (sin restricción por
  POBREZA monetaria, que es post-tratamiento).
- **POBREZA como heterogeneidad descriptiva**, no como restricción de
  estimand. Reportar tabla por categoría POBREZA pero advertir que es
  partición ex-post.
- **El RDD2 (proxy PCA del SISFOH) queda como complemento**, no como
  primario. El proxy explica solo 32% de varianza del SISFOH real; Bando
  et al. usaron el puntaje SISFOH oficial que INEI les dio.
- **df_main del paper actual se elimina** — el `main_dataset.csv` nuevo
  usa SAMPLE_FLAG para distinguir las particiones, no archivos separados.

---

## 9. Cosas que NO hay que hacer

- No re-introducir `df_main = df_rdd[df_rdd["POBREZA"]==1]` con la etiqueta
  "SISFOH extreme-poor". Es incorrecto conceptualmente.
- No correr `rdrobust` en este entorno (numba incompatible). Usar el
  fallback local-linear con statsmodels que ya está en `paso1_fuzzy_rdd.py`.
- No modificar `paper/main.tex` sin actualizar antes los CSV en
  `data/clean/`. El paper consume números desde ahí.
- No re-correr `scripts/script_completo/script.py` con descarga automática
  si no hay buena conexión — son ~600 MB y el script aborta sin caché.
- No commitear los CSV crudos de ENAHO (están en `.gitignore`).

---

## 10. Resumen ejecutivo para la coautora

Si solo lees una sección, lee esta:

1. **El paper actual tiene un error**: trata `POBREZA=1` como si fuera
   SISFOH (elegibilidad Pensión 65). Es pobreza monetaria, no SISFOH.
2. **Restringir a POBREZA=1 excluye 88.7% de receptores reales** — es
   post-tratamiento porque el programa eleva el gasto del hogar.
3. **Decisión nueva**: usar muestra completa (sin restringir por POBREZA)
   con fuzzy RDD usando `P5567A` (recepción individual) como tratamiento
   endógeno. LATE estimado = +0.014 (NS), CI [−0.17, +0.20].
4. **Próximo paso de codificación**: actualizar
   `scripts/script_completo/script.py` para extraer las nuevas variables
   y construir un único `main_dataset.csv`. Instrucciones detalladas en §12.
5. **Próximo paso del paper**: reescribir secciones 3-6 de `main.tex`
   eliminando "SISFOH extreme-poor (POBREZA=1)" y rehaciendo Table 2 con
   first-stage + reduced form + LATE.

---

## 11. Cómo usar Claude Code para los próximos pasos

Pegar exactamente esto en Claude Code al abrir el proyecto:

> Leí CLAUDE.md. Quiero ejecutar el Paso 2 (limpieza de datos corregida).
> Por favor seguí las instrucciones de la sección 12 al pie de la letra:
> actualizar `scripts/script_completo/script.py` para que extraiga
> `INGTPU03`, `P5567A`, `POBREZAV`, construya `RECIBE_P65_PERSONA` etc., y
> persista un único `main_dataset.csv` con `SAMPLE_FLAG`. Después correr
> `scripts/paso1_fuzzy_rdd.py` con los datos nuevos para verificar que los
> resultados se mantienen.

Para integrar al paper después:

> Leí CLAUDE.md. La limpieza de datos ya está actualizada (Paso 2 hecho).
> Ahora ejecutar el Paso 4 (integrar al paper). Reescribir abstract,
> sección 3.2, sección 4.1, sección 5.2 de `paper/main.tex` eliminando
> las menciones erradas de "SISFOH extreme-poor (POBREZA=1)". Rehacer
> Table 2 con first-stage + reduced form + LATE de la muestra A (full).
> Las nuevas cifras vienen de `data/clean/paso1_comparacion_candidatos.csv`.

---

## 12. INSTRUCCIONES DETALLADAS — Actualización de limpieza de datos

Esta sección es la que tu coautora puede entregar a Claude Code para que
actualice automáticamente el pipeline de limpieza.

### 12.1 Archivos a modificar

| Archivo | Cambios |
|---|---|
| `scripts/script_completo/script.py` | Agregar extracción de INGTPU03, P5567A; nuevo dataset único |
| `data/clean/results_summary.md` | Actualizar tras regenerar resultados |
| `paper/main.tex` | Reescribir secciones 3-6 (paso separado, ver §11) |

### 12.2 Cambios concretos a `script.py`

**Cambio 1 — Sumaria (líneas ~410-418): añadir INGTPU03 y POBREZAV**

Reemplazar:
```python
sum_keep = [c for c in (KEYS_HOUSEHOLD + ["INGHOG2D", "GASHOG2D", "MIEPERHO", "POBREZA"])
            if c in sumaria.columns]
sum_h = sumaria[sum_keep].drop_duplicates(subset=KEYS_HOUSEHOLD, keep="first")
sum_h["INGRESO_PC"] = (
    pd.to_numeric(sum_h["INGHOG2D"], errors="coerce") /
    pd.to_numeric(sum_h["MIEPERHO"], errors="coerce").replace(0, np.nan)
)
```

Por:
```python
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
# Recepción de transferencias (a nivel hogar)
sum_h["RECIBE_P65_HOGAR"] = (
    pd.to_numeric(sum_h["INGTPU03"], errors="coerce") > 0
).astype(int)
sum_h["RECIBE_JUNTOS_HOGAR"] = (
    pd.to_numeric(sum_h["INGTPU01"], errors="coerce") > 0
).astype(int)
```

**Cambio 2 — Módulo 05 (alrededor de líneas 255-325 donde se procesa m05):
agregar extracción de P5567A**

Encontrar el bloque que define el outcome `TIENE_BILLETERA` (alrededor de
la línea 258 donde aparece `col = f"P558E1_{BILLETERA_E1_CODE}"`). Justo
después de construir los outcomes de billetera, agregar:

```python
# Recepción individual de Pensión 65 (P5567A == 1)
# Esta es la variable de tratamiento endógeno del fuzzy RDD.
# i=7 en P556iA identifica Pensión 65 (ver Diccionario Sumaria-2024.pdf p.17).
if "P5567A" in m05.columns:
    m05["RECIBE_P65_PERSONA"] = (
        pd.to_numeric(m05["P5567A"], errors="coerce") == 1
    ).astype(int)
    print(f"  RECIBE_P65_PERSONA: {m05['RECIBE_P65_PERSONA'].sum():,} receptores")
else:
    print("  ADVERTENCIA: P5567A no encontrada en módulo 5.")
    m05["RECIBE_P65_PERSONA"] = 0
```

**Cambio 3 — Construcción de datasets analíticos (líneas ~548-577):
eliminar df_main, crear main_dataset único con SAMPLE_FLAG**

Reemplazar el bloque actual:
```python
# CAMBIO 2: df_main = solo extrema pobreza (POBREZA==1), población
# objetivo del programa.
df_full = df_rdd.copy()
if "POBREZA" in df_rdd.columns:
    df_main = df_rdd[df_rdd["POBREZA"] == 1].copy()
else:
    df_main = df_full.copy()

# ... (guardar df_full.csv y df_main.csv)
```

Por:
```python
# Diseño corregido (2026-05-21): NO restringimos por POBREZA porque
# POBREZA es la clasificación monetaria de ENAHO, NO la categoría SISFOH
# que usa Pensión 65. Restringir por POBREZA=1 excluye al 88.7% de los
# receptores reales (verificable con INGTPU03>0 en Sumaria 2024).
#
# El estimand primario es un fuzzy RDD sobre la muestra completa, usando
# RECIBE_P65_PERSONA (P5567A) como tratamiento endógeno y 1(EDAD>=65)
# como instrumento. POBREZA y POBREZAV entran como variables de
# heterogeneidad descriptiva, no como restricciones de muestra.
main_dataset = df_rdd.copy()

# SAMPLE_FLAG permite recuperar las particiones legacy del paper para
# fines de comparación, sin tratarlas como diseños primarios separados.
main_dataset["SAMPLE_FLAG_A_FULL"] = 1
main_dataset["SAMPLE_FLAG_B_POBREZA_EXT"] = (
    pd.to_numeric(main_dataset["POBREZA"], errors="coerce") == 1
).astype(int)
main_dataset["SAMPLE_FLAG_C_POBREZA_POOR"] = (
    pd.to_numeric(main_dataset["POBREZA"], errors="coerce").isin([1, 2])
).astype(int)

print(f"\nmain_dataset: N = {len(main_dataset):,}")
print(f"  SAMPLE A (full):              {main_dataset['SAMPLE_FLAG_A_FULL'].sum():,}")
print(f"  SAMPLE B (POBREZA=1):         {main_dataset['SAMPLE_FLAG_B_POBREZA_EXT'].sum():,}")
print(f"  SAMPLE C (POBREZA in {{1,2}}): {main_dataset['SAMPLE_FLAG_C_POBREZA_POOR'].sum():,}")

# Verificación crítica: ¿cuántos receptores reales caen en cada sample?
if "RECIBE_P65_PERSONA" in main_dataset.columns:
    recep_total = main_dataset["RECIBE_P65_PERSONA"].sum()
    recep_B = ((main_dataset["RECIBE_P65_PERSONA"] == 1) &
               (main_dataset["SAMPLE_FLAG_B_POBREZA_EXT"] == 1)).sum()
    recep_C = ((main_dataset["RECIBE_P65_PERSONA"] == 1) &
               (main_dataset["SAMPLE_FLAG_C_POBREZA_POOR"] == 1)).sum()
    print(f"\n  Receptores P65 totales:      {recep_total:,}")
    print(f"    en SAMPLE B (POBREZA=1):  {recep_B:,} ({recep_B/recep_total*100:.1f}%)")
    print(f"    en SAMPLE C (POBREZA<=2): {recep_C:,} ({recep_C/recep_total*100:.1f}%)")

main_dataset.to_csv(PATHS["main_dataset"], index=False)
print(f"\nSaved: {PATHS['main_dataset']}")
```

**Cambio 4 — Actualizar PATHS (líneas ~72-81)**

Agregar al diccionario `PATHS`:
```python
"main_dataset":     DATA_DIR / "main_dataset.csv",
```

Y eliminar (o comentar) las entradas legacy:
```python
# "clean_data_full":  DATA_DIR / "enaho_rdd_full.csv",   # DEPRECATED 2026-05-21
# "clean_data_main":  DATA_DIR / "enaho_rdd_main.csv",   # DEPRECATED 2026-05-21
```

**Cambio 5 — Actualizar todos los `pd.read_csv` posteriores**

Donde el script lee `df_main` y `df_full` (líneas ~740-742, ~920), reemplazar
por:
```python
main_dataset = pd.read_csv(PATHS["main_dataset"])
# Submuestras (para análisis de heterogeneidad, NO para diseño primario):
df_sample_A = main_dataset.copy()
df_sample_B = main_dataset[main_dataset["SAMPLE_FLAG_B_POBREZA_EXT"] == 1].copy()
df_sample_C = main_dataset[main_dataset["SAMPLE_FLAG_C_POBREZA_POOR"] == 1].copy()
```

### 12.3 Cómo verificar que la actualización funcionó

Después de correr `python scripts/script_completo/script.py`:

```bash
# 1. El nuevo dataset existe
ls -lh data/clean/main_dataset.csv

# 2. Tiene las variables nuevas
python -c "
import pandas as pd
df = pd.read_csv('data/clean/main_dataset.csv')
print('Columnas nuevas:', [c for c in df.columns if c in
      ['RECIBE_P65_PERSONA','RECIBE_P65_HOGAR','RECIBE_JUNTOS_HOGAR',
       'INGTPU03','POBREZAV','SAMPLE_FLAG_A_FULL']])
print(f'N total: {len(df):,}')
print(f'Receptores P65 persona: {df[\"RECIBE_P65_PERSONA\"].sum():,}')
print(f'Receptores P65 hogar:   {df[\"RECIBE_P65_HOGAR\"].sum():,}')
"

# 3. Re-correr Paso 1 contra el nuevo dataset (cuando paso1_fuzzy_rdd.py
#    se actualice para leer de main_dataset.csv en vez de los CSV crudos)
python scripts/paso1_fuzzy_rdd.py
```

Resultados esperados (con datos ENAHO 2024):
- N total main_dataset: ~85,000 personas (después del inner join con m05)
- Receptores P65 persona: ~4,400
- Receptores P65 hogar:   ~3,500 (menor porque cuenta hogar único)
- LATE en SAMPLE A (full): +0.014 (NS), CI [-0.17, +0.20]

Si los números no coinciden razonablemente con los reportados en
`data/clean/paso1_comparacion_candidatos.csv`, algo se rompió en la
extracción — revisar logs del script.

### 12.4 Después de la limpieza

Una vez la limpieza esté hecha y verificada:

1. Actualizar `scripts/paso1_fuzzy_rdd.py` para que lea de
   `data/clean/main_dataset.csv` en vez de los CSV crudos en `/tmp/`.
2. Marcar como completado este Paso 2 en CLAUDE.md.
3. Pasar al Paso 4 (integración al paper) usando el prompt sugerido en §11.
