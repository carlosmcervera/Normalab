"""Catálogo y tablas del módulo CTE DB-SI (Seguridad en caso de incendio)."""

# Usos previstos (CTE)
USOS = [
    "Residencial Vivienda", "Administrativo", "Docente", "Comercial",
    "Pública concurrencia", "Hospitalario", "Aparcamiento", "Residencial Público",
]

# Densidades de ocupación (CTE DB-SI/SUA, Tabla 2.1). m²/persona; None = sin ocupación.
OCCUPANCY_DENSITIES = [
    {"uso": "Sin ocupación (mantenimiento/instalaciones)", "densidad": None},
    {"uso": "Aparcamiento (vehículos)", "densidad": 40},
    {"uso": "Almacenamiento / archivo", "densidad": 40},
    {"uso": "Residencial Vivienda (plantas)", "densidad": 20},
    {"uso": "Administrativo / oficinas", "densidad": 10},
    {"uso": "Docente (aulas, seminarios)", "densidad": 1.5},
    {"uso": "Hospitalario (hospitalización)", "densidad": 15},
    {"uso": "Comercial (público, general)", "densidad": 2},
    {"uso": "Comercial (público, plantas alejadas del acceso)", "densidad": 3},
    {"uso": "Pública concurrencia (de pie)", "densidad": 1},
    {"uso": "Pública concurrencia (sentado)", "densidad": 1.5},
    {"uso": "Zonas de servicio (cocinas)", "densidad": 10},
    {"uso": "Aseos de planta", "densidad": 3},
    {"uso": "Vestíbulos generales / público", "densidad": 2},
]

# SI 1 · Superficie construida máxima por sector de incendio (m²). None = sin límite/especial.
SI1_MAX_SECTOR = {
    "Residencial Vivienda": 2500, "Administrativo": 2500, "Docente": 4000,
    "Comercial": 2500, "Pública concurrencia": 2500, "Hospitalario": 1500,
    "Aparcamiento": None, "Residencial Público": 2500,
}

# SI 3 · Longitud máxima del recorrido de evacuación (m)
SI3_RECORRIDO = {"una": 25, "varias": 50}
SI3_RECORRIDO_ESPECIAL = {  # usos con distancia reducida
    "Hospitalario": {"una": 25, "varias": 35},
    "Aparcamiento": {"una": 35, "varias": 50},
}

# SI 6 · Resistencia al fuego de la estructura (Tabla 3.1 DB-SI)
# grupo 1: residencial/administrativo/docente/residencial público
# grupo 2: comercial/pública concurrencia/hospitalario
SI6_GRUPO2 = {"Comercial", "Pública concurrencia", "Hospitalario"}
