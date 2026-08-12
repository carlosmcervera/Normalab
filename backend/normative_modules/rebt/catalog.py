"""Datos normalizados del REBT (RD 842/2002) para el dimensionado de líneas."""

# Tensiones nominales (V)
TENSION = {"monofasica": 230, "trifasica": 400}

# Conductividad del conductor γ (m/(Ω·mm²)) a temperatura de servicio (orientativa).
CONDUCTIVIDAD = {"Cu": 56.0, "Al": 35.0}

# Secciones comerciales normalizadas (mm²).
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Intensidad máxima admisible orientativa (A) para conductor de COBRE, aislamiento
# PVC — columna representativa de la Tabla 1 de la ITC-BT-19. Para ALUMINIO se aplica
# el factor 0,78. (Valores para estudio no vinculante; contrastar método de instalación.)
AMPACIDAD_CU = {
    1.5: 15, 2.5: 21, 4: 27, 6: 36, 10: 50, 16: 66, 25: 84, 35: 104,
    50: 125, 70: 160, 95: 194, 120: 225, 150: 260, 185: 297, 240: 350,
}
FACTOR_AL = 0.78

# Calibres normalizados de interruptor automático magnetotérmico (A). Se incluyen calibres
# de caja moldeada/regulados (>400 A) para líneas de gran potencia con conductores en paralelo.
MAGNETOS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400,
            500, 630, 800, 1000, 1250, 1600]

# Tipos de instalación / local (para caída de tensión recomendada y grado eléctrico).
TIPOS_INSTALACION = [
    {"value": "vivienda_basica", "label": "Vivienda · electrificación básica"},
    {"value": "vivienda_elevada", "label": "Vivienda · electrificación elevada"},
    {"value": "local_comercial", "label": "Local comercial / oficinas"},
    {"value": "industrial", "label": "Industrial"},
    {"value": "publica_concurrencia", "label": "Pública concurrencia"},
    {"value": "garaje", "label": "Garaje / aparcamiento"},
    {"value": "otro", "label": "Otro"},
]

# Grado de electrificación en viviendas (ITC-BT-10 / ITC-BT-25).
GRADOS_VIVIENDA = {
    "vivienda_basica": {"potencia_min": 5750, "circuitos": 5,
                        "descripcion": "C1 alumbrado, C2 tomas uso general, C3 cocina/horno, C4 lavadora/lavavajillas/termo, C5 tomas baño y cocina"},
    "vivienda_elevada": {"potencia_min": 9200, "circuitos": 7,
                         "descripcion": "Circuitos básicos C1–C5 más C8 calefacción, C9 aire acondicionado, C10 secadora, C11 automatización, C12 (según previsión)"},
}

MATERIALES = [{"value": "Cu", "label": "Cobre (Cu)"}, {"value": "Al", "label": "Aluminio (Al)"}]
SUMINISTROS = [{"value": "monofasica", "label": "Monofásica 230 V"},
               {"value": "trifasica", "label": "Trifásica 400 V"}]

# Métodos de instalación de referencia (ITC-BT-19, Tabla 1). La AMPACIDAD_CU base corresponde
# al método B1 (bajo tubo empotrado en pared/obra); para el resto se aplica un factor derivado
# de las relaciones de la Tabla 1 (estudio orientativo, no vinculante).
METODOS_INSTALACION = [
    {"value": "b1", "label": "Bajo tubo empotrado en pared (B1)"},
    {"value": "b2", "label": "Bajo tubo en superficie (B2)"},
    {"value": "c", "label": "Directamente sobre pared / bandeja no perforada (C)"},
    {"value": "e", "label": "Bandeja perforada (E/F)"},
    {"value": "d", "label": "Enterrado bajo tubo (D)"},
]
METODO_FACTOR = {"b1": 1.0, "b2": 0.92, "c": 1.13, "e": 1.27, "d": 1.21}


def ampacidad(seccion: float, material: str, metodo: str = "b1") -> float:
    base = AMPACIDAD_CU.get(seccion, 0)
    base *= (FACTOR_AL if material == "Al" else 1.0)
    return base * METODO_FACTOR.get((metodo or "b1"), 1.0)


def seccion_tierra(s_fase: float) -> float:
    """Sección del conductor de protección (ITC-BT-18, Tabla 2)."""
    if s_fase <= 16:
        return s_fase
    if s_fase <= 35:
        return 16
    return s_fase / 2
