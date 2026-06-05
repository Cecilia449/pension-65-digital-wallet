"""
Pesos del Indice de Focalizacion de Hogares (IFH) / SISFOH.

Transcripcion literal de las Tablas A.8 y A.9 del Online Appendix de:

    Bernal, N., Carpio, M. A., & Klein, T. J. (2017).
    "The Effects of Access to Health Insurance: Evidence from a
    Regression Discontinuity Design in Peru."
    Journal of Public Economics, 154, 122-136.
    Online Appendix Tablas A.8, A.9, A.10 (paginas A12-A14).

PDF en el repo:
    lit_review/1-s2.0-S0047272717301299-mmc1.pdf

Los pesos provienen de SISFOH (2010), recalibrados con ENAHO 2009.
El IFH se construye como combinacion lineal de las variables con
los pesos correspondientes al cluster geografico, luego se estandariza
a [0, 100] por cluster (ver Apendice F.1).

Tres conjuntos de pesos por area geografica:
  - LIMA:  Lima Metropolitana (cluster 15 en Tabla A.10)
  - URBAN: Otras areas urbanas
  - RURAL: Areas rurales

Convencion para las categorias:
  - Cada variable contribuye SOLO con UN peso al IFH del hogar
    (la categoria que aplique al hogar).
  - Las claves de los dicts son los nombres canonicos que usaremos
    al construir las dummies desde ENAHO 2024 (ver Paso 2).
"""

# ============================================================================
# LIMA METROPOLITANA  (Tabla A.8 + A.9, columna "Metropolitan Lima")
# ============================================================================
WEIGHTS_LIMA = {
    # ---- Combustible usado para cocinar (Fuel used to cook) ----
    "combustible_cocina": {
        "no_cocina":    -0.49,
        "otro":         -0.40,
        "lena":         -0.37,
        "carbon":       -0.33,
        "kerosene":     -0.29,
        "gas":           0.02,
        "electricidad":  0.43,
    },
    # ---- Agua en la vivienda (Water supply in the home) ----
    "agua": {
        "otro":          -0.78,
        "rio":           -0.65,
        "pozo":          -0.62,
        "cisterna":      -0.51,
        "tuberia":       -0.41,   # "Pipe" en A.8 (red publica con tuberia)
        "fuera":         -0.35,   # "Outside" (fuera de la vivienda)
        "dentro":         0.10,   # "Inside" (red dentro de la vivienda)
    },
    # ---- Material de las paredes (Wall material) ----
    "paredes": {
        "otro":                 -0.70,
        "madera_estera":        -0.48,   # "Wood or mat"
        "piedra_con_barro":     -0.44,   # "Stone with mud"
        "quincha_barro":        -0.41,   # "Rushes covered with mud"
        "barro":                -0.39,   # "Clay"
        "adobe":                -0.37,   # "Sun-dried brick or adobe"
        "piedra_concreto":      -0.33,   # "Stones, lime or concrete"
        "ladrillo":              0.10,   # "Brick"
    },
    # ---- Tipo de desague (Type of drainage) ----
    "desague": {
        "ninguno":            -0.89,
        "rio":                -0.75,
        "pozo_ciego":         -0.59,   # "Sinkhole"
        "pozo_septico":       -0.46,   # "Septic tank"
        "fuera_vivienda":     -0.39,   # "Drainage system outside the house"
        "dentro_vivienda":     0.10,   # "Drainage system inside the house"
    },
    # ---- Numero de miembros con seguro de salud ----
    # IMPORTANTE: SISFOH excluye a los que tienen SIS al contar miembros
    # con seguro (footnote 2 pag A11 del paper). Aplicamos misma regla.
    "miembros_con_seguro": {
        "ninguno":      -0.26,
        "uno":          -0.04,
        "dos":           0.06,
        "tres":          0.14,
        "mas_de_tres":   0.32,
    },
    # ---- Bienes que identifican riqueza del hogar (5 items) ----
    # SISFOH no lista los items exactos en BCK 2017; ver Paso 2 para la
    # construccion canonica (probablemente TV color, refrigeradora,
    # lavadora, equipo de sonido, computadora, segun ENAHO M18 / P612).
    "bienes_riqueza": {
        "ninguno":  -0.47,
        "uno":      -0.17,
        "dos":       0.02,
        "tres":      0.15,
        "cuatro":    0.25,
        "cinco":     0.47,
    },
    # ---- Telefono fijo (solo Lima) ----
    "telefono_fijo": {
        "si":  -0.32,
        "no":   0.20,
    },
    # ---- Material del techo (Roof material) ----
    "techo": {
        "otro":         -0.86,
        "paja":         -0.74,   # "Straw"
        "estera":       -0.67,   # "Mat"
        "carrizo":      -0.38,   # "Woven cane"
        "tejas":        -0.23,   # "Tiles"
        "madera_estera":-0.21,   # "Wood or mat"
        "concreto":      0.17,   # "Concrete"
    },
    # ---- Educacion del jefe de hogar ----
    "educacion_jefe": {
        "ninguno":      -0.51,
        "preescolar":   -0.43,
        "primaria":     -0.28,
        "secundaria":   -0.06,
        "tecnico":       0.10,   # "Vocational education (VET)"
        "universitario": 0.22,
        "postgrado":     0.40,
    },
    # ---- Material del piso (Floor material) ----
    "piso": {
        "otro":      -0.97,
        "tierra":    -0.60,   # "Land"
        "cemento":   -0.16,   # "Concrete"
        "madera":     0.08,
        "losetas":    0.16,   # "Tiles"
        "vinilico":   0.28,   # "Vinyl sheets"
        "parquet":    0.51,
    },
    # ---- Hacinamiento (miembros del hogar / numero de cuartos) ----
    "hacinamiento": {
        "mas_de_seis":    -0.68,   # "More than six"
        "entre_4_y_6":    -0.51,   # "Between four and six"
        "entre_2_y_4":    -0.31,   # "Between two and four"
        "entre_1_y_2":    -0.07,   # "Between one and two"
        "menos_de_1":      0.24,   # "Less than one"
    },
}


# ============================================================================
# OTRAS AREAS URBANAS  (Tabla A.8 + A.9, columna "remaining urban areas")
# ============================================================================
WEIGHTS_URBAN = {
    "combustible_cocina": {
        "no_cocina":    -0.67,
        "otro":         -0.50,
        "lena":         -0.33,
        "carbon":       -0.22,
        "kerosene":     -0.19,
        "gas":           0.12,
        "electricidad":  0.69,
    },
    "agua": {
        "otro":          -0.58,
        "rio":           -0.42,
        "pozo":          -0.37,
        "cisterna":      -0.34,
        "tuberia":       -0.32,
        "fuera":         -0.25,
        "dentro":         0.12,
    },
    "paredes": {
        "otro":                 -0.80,
        "madera_estera":        -0.55,
        "piedra_con_barro":     -0.46,
        "quincha_barro":        -0.43,
        "barro":                -0.38,
        "adobe":                -0.20,
        "piedra_concreto":      -0.07,
        "ladrillo":              0.25,
    },
    "desague": {
        "ninguno":            -0.68,
        "rio":                -0.49,
        "pozo_ciego":         -0.40,
        "pozo_septico":       -0.30,
        "fuera_vivienda":     -0.21,
        "dentro_vivienda":     0.20,
    },
    "miembros_con_seguro": {
        "ninguno":      -0.25,
        "uno":           0.06,
        "dos":           0.17,
        "tres":          0.27,
        "mas_de_tres":   0.48,
    },
    "bienes_riqueza": {
        "ninguno":  -0.35,
        "uno":       0.05,
        "dos":       0.25,
        "tres":      0.40,
        "cuatro":    0.52,
        "cinco":     0.75,
    },
    # ---- Techo (urbano) ----
    "techo": {
        "otro":         -0.90,
        "paja":         -0.72,
        "estera":       -0.62,
        "carrizo":      -0.23,
        "tejas":         0.03,
        "madera_estera": 0.07,
        "concreto":      0.32,
    },
    "educacion_jefe": {
        "ninguno":      -0.57,
        "preescolar":   -0.25,
        "primaria":      0.01,
        "secundaria":    0.19,
        "tecnico":       0.33,
        "universitario": 0.55,
        "postgrado":     0.55,
    },
    "piso": {
        "otro":      -1.12,
        "tierra":    -0.47,
        "cemento":   -0.01,
        "madera":     0.30,
        "losetas":    0.40,
        "vinilico":   0.51,
        "parquet":    0.71,
    },
    "hacinamiento": {
        "mas_de_seis":    -0.68,   # ver nota abajo
        "entre_4_y_6":    -0.51,
        "entre_2_y_4":    -0.31,
        "entre_1_y_2":    -0.07,
        "menos_de_1":      0.24,
    },
    # NOTA: la Tabla A.9 solo muestra valores de Hacinamiento para Lima.
    # Re-usamos los mismos en URBAN como aproximacion conservadora; conviene
    # verificar contra SISFOH (2010) si esto cambia entre Lima y otras urbanas.
}


# ============================================================================
# AREAS RURALES  (Tabla A.8 + A.9, columna "rural areas")
# ============================================================================
# NOTA: el set rural es estructuralmente distinto. Tabla A.8 muestra que en
# rural NO entran "Water supply", "Wall material" (no se reportan pesos en
# Tabla A.8 col 3), "Type of drainage", "Has fixed phone", "Floor material",
# ni "Overcrowding". En su lugar entran:
#   - "Highest level of education in the house"
#   - "Electricity" (Si/No)
#   - "Floor made of earth" (Si/No)
# Mantenemos en cero los pesos de las variables no incluidas en rural para
# que la combinacion lineal funcione uniforme; el codigo de Paso 2 debe
# detectar el cluster y aplicar el dict correspondiente.
WEIGHTS_RURAL = {
    "combustible_cocina": {
        "no_cocina":    -0.76,
        "otro":         -0.38,
        "lena":          0.05,
        "carbon":        0.36,
        "kerosene":      0.37,
        "gas":           0.52,
        "electricidad":  0.52,
    },
    "miembros_con_seguro": {
        "ninguno":      -0.10,
        "uno":           0.50,
        "dos":           0.59,
        "tres":          0.66,
        "mas_de_tres":   0.86,
    },
    "bienes_riqueza": {
        "ninguno":  -0.11,
        "uno":       0.64,
        "dos":       0.83,
        "tres":      0.90,
        "cuatro":    1.09,
        "cinco":     1.09,
    },
    # ---- Educacion del jefe (rural) ----
    "educacion_jefe": {
        "ninguno":      -0.59,
        "preescolar":   -0.08,
        "primaria":      0.35,
        "secundaria":    0.59,
        "tecnico":       0.68,
        "universitario": 0.88,
        "postgrado":     0.88,
    },
    # ---- Variables propias del set rural ----
    "educacion_max_hogar": {        # "Highest level of education in the house"
        "ninguno":      -0.35,
        "primaria":      0.11,
        "secundaria":    0.41,
        "tecnico":       0.62,
        "universitario": 0.83,
    },
    "electricidad": {
        "no":  -0.29,
        "si":   0.22,
    },
    "piso_tierra": {                # "Floor made of earth"
        "si":  -0.17,
        "no":   0.47,
    },
}


# ============================================================================
# UMBRALES DE ELEGIBILIDAD POR CLUSTER  (Tabla A.10)
# ============================================================================
# IFH estandarizado [0, 100]. Hogar es SIS-elegible si IFH_std <= threshold.
# Los 15 clusters fueron definidos por SISFOH (2010) agrupando areas con
# pobreza monetaria similar en 2009. Por ahora SOLO tenemos el threshold;
# la asignacion departamento/distrito -> cluster es lo unico que falta
# (ver Paso 3 — pedir a INEI o reconstruir desde SISFOH 2010).
THRESHOLDS_BY_CLUSTER = {
    1:  33,
    2:  36,
    3:  34,
    4:  38,
    5:  35,
    6:  34,
    7:  52,
    8:  42,
    9:  44,
    10: 50,
    11: 44,
    12: 43,
    13: 43,
    14: 33,
    15: 55,   # Lima Metropolitana
}

# Promedio nacional reportado en Tabla A.10 (para sanity check):
# Per capita income S/. 5,793 ; per capita spending S/. 4,501 ;
# poverty status 27.64%. Poblacion total 30,208,831.

# ============================================================================
# Mapeo cluster -> area geografica (para elegir WEIGHTS_*)
# ============================================================================
# Cluster 15 es Lima (urbano metropolitano). Cluster 14 es selva urbana
# (Madre de Dios). El resto se asigna a urbano u rural segun la nota del
# paper: "el 15 cluster fueron definidos por SISFOH agrupando areas con
# pobreza similar... cluster 2 incluye areas rurales de Ayacucho, Junin,
# Loreto, Puno, San Martin, Ucayali y sierra norte de Cajamarca y Lambayeque".
#
# Reconstruccion preliminar basada en pistas del paper (Apendice F.2):
CLUSTER_AREA = {
    1:  "rural",  # rural sierra centro/sur (aprox)
    2:  "rural",  # rural selva + sierra norte
    3:  "rural",
    4:  "rural",
    5:  "rural",
    6:  "rural",   # cluster 6 tiene umbral 34, ingreso pc 5,941 — perfil mixto
    7:  "urban",   # urbano provincial alto ingreso (5,141 pc)
    8:  "urban",
    9:  "urban",
    10: "urban",
    11: "urban",
    12: "urban",
    13: "urban",
    14: "urban",   # selva urbana Madre de Dios — el paper lo destaca
    15: "lima",    # Lima Metropolitana
}
# IMPORTANTE: esta asignacion es PROVISIONAL. Confirmar con SISFOH (2010)
# o pedir a INEI el listado oficial cluster -> ubigeo.


# ============================================================================
# Conjunto canonico de variables que usa cada cluster-area
# ============================================================================
VARS_BY_AREA = {
    "lima": [
        "combustible_cocina", "agua", "paredes", "desague",
        "miembros_con_seguro", "bienes_riqueza", "telefono_fijo",
        "techo", "educacion_jefe", "piso", "hacinamiento",
    ],
    "urban": [
        "combustible_cocina", "agua", "paredes", "desague",
        "miembros_con_seguro", "bienes_riqueza",
        "techo", "educacion_jefe", "piso", "hacinamiento",
    ],
    "rural": [
        "combustible_cocina", "miembros_con_seguro", "bienes_riqueza",
        "educacion_jefe", "educacion_max_hogar",
        "electricidad", "piso_tierra",
    ],
}

WEIGHTS_BY_AREA = {
    "lima":  WEIGHTS_LIMA,
    "urban": WEIGHTS_URBAN,
    "rural": WEIGHTS_RURAL,
}


# ============================================================================
# Sanity check al importar el modulo
# ============================================================================
def _validate_weights():
    """Verifica que cada conjunto de pesos tenga todas las variables
    declaradas en VARS_BY_AREA.
    """
    for area, vars_list in VARS_BY_AREA.items():
        w = WEIGHTS_BY_AREA[area]
        for v in vars_list:
            assert v in w, f"[ifh_weights] {area}: falta variable '{v}'"
            assert isinstance(w[v], dict) and len(w[v]) > 0, \
                f"[ifh_weights] {area}/{v}: dict vacio"


_validate_weights()


if __name__ == "__main__":
    # Imprime un resumen rapido al correr `python scripts/ifh_weights.py`
    print("=" * 70)
    print("Pesos IFH (Bernal-Carpio-Klein 2017, Tablas A.8/A.9)")
    print("=" * 70)
    for area in ["lima", "urban", "rural"]:
        w = WEIGHTS_BY_AREA[area]
        vars_list = VARS_BY_AREA[area]
        print(f"\n[{area.upper()}] {len(vars_list)} variables")
        for v in vars_list:
            cats = list(w[v].keys())
            rango = (min(w[v].values()), max(w[v].values()))
            print(f"  {v:22s} {len(cats):>2d} categorias   "
                  f"rango=[{rango[0]:+.2f}, {rango[1]:+.2f}]")
    print(f"\nUmbrales por cluster (Tabla A.10):")
    for c, t in THRESHOLDS_BY_CLUSTER.items():
        area = CLUSTER_AREA[c]
        print(f"  cluster {c:2d} ({area:5s}): threshold = {t}")
