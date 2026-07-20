"""Tabla maestra de valores oficiales del CTE DB-SI (Seguridad en caso de incendio).

ÚNICA FUENTE DE VERDAD para el módulo DB-SI. Todos los valores proceden del
Documento Básico DB-SI del CTE (articulado). El motor y el test integral se
apoyan exclusivamente en estas constantes para blindar la precisión normativa.
"""

# --- SI 1 · Compartimentación ----------------------------------------------

# Tabla 1.1 · superficie construida máxima de un sector de incendio (m²).
# None = un sector por planta / sin límite general (condiciones específicas).
SI1_SECTOR_MAX = {
    "Residencial Vivienda": 2500,
    "Administrativo": 2500,
    "Docente": 4000,
    "Comercial": 2500,
    "Pública concurrencia": 2500,
    "Hospitalario": 1500,
    "Aparcamiento": None,
    "Residencial Público": 2500,
}


def si1_delimitador_ei(altura_evacuacion: float, bajo_rasante: bool) -> str:
    """Tabla 1.2 · resistencia al fuego de paredes/techos que delimitan sector."""
    if bajo_rasante:
        return "EI 120"
    if altura_evacuacion <= 15:
        return "EI 60"
    if altura_evacuacion <= 28:
        return "EI 90"
    return "EI 120"


# Tabla 2.2 · condiciones de los locales y zonas de riesgo especial.
SI1_RIESGO_ESPECIAL = {
    "bajo": {"R": "R 90", "EI": "EI 90", "vestibulo": False, "puerta": "EI2 45-C5", "recorrido": 25},
    "medio": {"R": "R 120", "EI": "EI 120", "vestibulo": True, "puerta": "2 × EI2 30-C5", "recorrido": 25},
    "alto": {"R": "R 180", "EI": "EI 180", "vestibulo": True, "puerta": "2 × EI2 45-C5", "recorrido": 25},
}

# Reacción al fuego de revestimientos (Tabla 4.1, recorridos de evacuación).
SI1_REACCION = "Techos y paredes C-s2,d0 · suelos EFL (recorridos generales de evacuación)"


# --- SI 2 · Propagación exterior -------------------------------------------

SI2_MEDIANERIA = "EI 120"
SI2_FACHADA = "EI 60 en franja ≥ 1 m; separación entre huecos de sectores distintos según el ángulo (Fig. 1.1)"
SI2_CUBIERTA = "REI 60 en franja de 0,50 m desde el encuentro con sector/edificio de mayor riesgo"
SI2_DIST_MIN = 3.0  # m · separación mínima sin protección adicional de huecos entre edificios


# --- SI 3 · Evacuación de ocupantes ----------------------------------------

# Tabla 3.1 · longitud máxima del recorrido de evacuación (m).
SI3_RECORRIDO = {"una": 25, "varias": 50}
SI3_RECORRIDO_ESPECIAL = {
    "Hospitalario": {"una": 25, "varias": 35},
    "Aparcamiento": {"una": 35, "varias": 50},
}

# Tabla 4.1 · anchura mínima de los elementos de evacuación (m).
SI3_ANCHO_MIN = {"puerta": 0.80, "pasillo": 1.00, "escalera": 1.00}
SI3_MODULO = 200  # A ≥ P / 200 (puertas, pasos y pasillos)


def si3_proteccion_escalera(altura_evacuacion: float, sentido: str = "descendente") -> str:
    """Tabla 5.1 · condición de protección exigida a las escaleras de evacuación."""
    if sentido == "ascendente":
        if altura_evacuacion <= 2.8:
            return "No protegida"
        if altura_evacuacion <= 6:
            return "Protegida"
        return "Especialmente protegida"
    if altura_evacuacion <= 14:
        return "No protegida"
    if altura_evacuacion <= 28:
        return "Protegida"
    return "Especialmente protegida"


# --- SI 5 · Intervención de los bomberos ------------------------------------

SI5_VIAL = {"anchura": 3.5, "altura_libre": 4.5, "capacidad_portante": 20.0}  # m, m, kN/m²
SI5_ALTURA_ESPACIO_MANIOBRA = 9.0  # m · altura de evacuación a partir de la que se exige espacio de maniobra


# --- SI 6 · Resistencia al fuego de la estructura ---------------------------

SI6_GRUPO2 = {"Comercial", "Pública concurrencia", "Hospitalario"}


def si6_estructura(uso: str, altura_evacuacion: float, bajo_rasante: bool) -> str:
    """Tabla 3.1 · resistencia al fuego suficiente de la estructura portante."""
    if uso == "Aparcamiento":
        return "R 90"
    g2 = uso in SI6_GRUPO2
    if bajo_rasante:
        return "R 180" if g2 else "R 120"
    if altura_evacuacion <= 15:
        return "R 90" if g2 else "R 60"
    if altura_evacuacion <= 28:
        return "R 120" if g2 else "R 90"
    return "R 180" if g2 else "R 120"


SI6_RIESGO_ESPECIAL_R = {"bajo": "R 90", "medio": "R 120", "alto": "R 180"}  # Tabla 3.2
