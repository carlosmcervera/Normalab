"""Datos normalizados del RITE (RD 1027/2007) e IT complementarias."""

TIPOS_INSTALACION = [
    {"value": "calefaccion", "label": "Calefacción"},
    {"value": "refrigeracion", "label": "Refrigeración"},
    {"value": "climatizacion", "label": "Climatización (calor + frío)"},
    {"value": "acs", "label": "Agua caliente sanitaria (ACS)"},
    {"value": "mixta", "label": "Climatización + ACS"},
]

USOS_EDIFICIO = [
    {"value": "vivienda", "label": "Residencial vivienda"},
    {"value": "oficinas", "label": "Administrativo / oficinas"},
    {"value": "comercial", "label": "Comercial"},
    {"value": "docente", "label": "Docente"},
    {"value": "hospitalario", "label": "Hospitalario"},
    {"value": "publica_concurrencia", "label": "Pública concurrencia"},
    {"value": "hotelero", "label": "Hotelero"},
]

ZONAS_CLIMATICAS = [
    {"value": "A", "label": "Zona A (muy cálida)"},
    {"value": "B", "label": "Zona B"},
    {"value": "C", "label": "Zona C"},
    {"value": "D", "label": "Zona D"},
    {"value": "E", "label": "Zona E (muy fría)"},
]

# Demanda térmica orientativa de calefacción (W/m²) por zona climática (estimación no vinculante).
DEMANDA_WM2 = {"A": 50, "B": 60, "C": 75, "D": 95, "E": 115}

TIPOS_GENERADOR = [
    {"value": "caldera_condensacion", "label": "Caldera de gas de condensación", "rend_min": 92},
    {"value": "caldera_estandar", "label": "Caldera estándar", "rend_min": 90},
    {"value": "bomba_calor", "label": "Bomba de calor", "rend_min": 100},
    {"value": "biomasa", "label": "Caldera de biomasa", "rend_min": 85},
    {"value": "otro", "label": "Otro", "rend_min": 90},
]

# Caudal mínimo de aire exterior por persona (dm³/s·persona) según categoría de calidad
# del aire interior (RITE IT 1.1.4.2.3, método indirecto por persona).
IDA_CAUDAL = {"IDA1": 20.0, "IDA2": 12.5, "IDA3": 8.0, "IDA4": 5.0}
IDA_OPTS = [
    {"value": "IDA1", "label": "IDA 1 · aire óptimo (hospitales, laboratorios)"},
    {"value": "IDA2", "label": "IDA 2 · buena calidad (oficinas, aulas)"},
    {"value": "IDA3", "label": "IDA 3 · calidad media (comercial, restaurantes)"},
    {"value": "IDA4", "label": "IDA 4 · calidad baja"},
]

# Consumo unitario de ACS a 60 °C (litros/persona·día), orientativo (CTE DB-HE4 / RITE).
ACS_CONSUMO = {"vivienda": 28, "oficinas": 3, "comercial": 4, "docente": 4,
               "hospitalario": 55, "publica_concurrencia": 15, "hotelero": 40}

# Espesor mínimo de aislamiento de tuberías (mm), interior, fluido caliente 40–60 °C
# (RITE IT 1.2.4.2.1, tabla 1.2.4.2.1). Valores orientativos.
AISLAMIENTO_TUBERIAS = [
    {"diametro": "D ≤ 35", "espesor": 25},
    {"diametro": "35 < D ≤ 60", "espesor": 30},
    {"diametro": "60 < D ≤ 90", "espesor": 30},
    {"diametro": "90 < D ≤ 140", "espesor": 40},
    {"diametro": "D > 140", "espesor": 40},
]

# Umbral de fraccionamiento de potencia (kW): por encima se exigen ≥2 generadores.
FRACCIONAMIENTO_KW = 400
# Umbral de recuperación de calor del aire de extracción (m³/s).
RECUPERACION_M3S = 0.5
