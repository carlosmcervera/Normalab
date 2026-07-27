"""Catálogo RSCIEI (RD 164/2025): tipos de configuración (con imágenes), tabla de
coeficiente de combustibilidad Ci, densidades de ocupación (CTE) y catálogo
jerárquico de actividades según la Tabla 1.3.5 del RSCIEI (BOE-A-2025-7190).

La Tabla 1.3.5 se transcribe LITERALMENTE por categorías (A. OFICINAS, B. CARTÓN,
PAPEL, …). Cada subactividad incluye: name (texto literal, con su grupo cuando
procede), modo (produccion|almacenamiento), qsi (MJ/m² · producción) o qvi (MJ/m³ ·
almacenamiento bruto) con qvi_neto (MJ/m³ · almacenamiento neto, si la tabla lo da),
ci (coef. de combustibilidad) y rmin (valor mínimo de R según la nota 3). ra es el
valor por defecto (= rmin en producción; 1,0 en almacenamiento, a ajustar con la
Tabla 1.3.4). Los valores dados como rango en la tabla usan el valor propuesto entre
paréntesis (nota 6) o el más conservador, y son editables por el técnico.
"""

IMG = "https://static.prod-images.emergentagent.com/jobs/5eb931c9-6038-47bc-82ba-0518add2fe79/images"

CONFIG_TYPES = [
    {"value": "AV", "label": "Tipo A · separación vertical",
     "description": "El establecimiento ocupa parte de un edificio con otros establecimientos, separado verticalmente (por plantas).",
     "image": f"{IMG}/72afaaa0769d5173e0cd16ec80ce7a06d75d402fa77c11ebe55badc7f3376fd9.png"},
    {"value": "AH", "label": "Tipo A · separación horizontal",
     "description": "El establecimiento ocupa parte de un edificio con otros establecimientos, separado horizontalmente (lado a lado).",
     "image": f"{IMG}/02758f6ef1223ecfd2090627772db7e75ac62f480279eb1a4b11117a2ecdc9b1.png"},
    {"value": "B", "label": "Tipo B · edificio propio adosado",
     "description": "Ocupa un edificio propio adosado a otros o a distancia ≤ 3 m de edificios de otros establecimientos.",
     "image": f"{IMG}/5166c9780d27335a37ddf151473821e2a47aaf4f6e28da2cb0b7916864e70a11.png"},
    {"value": "C", "label": "Tipo C · edificio aislado",
     "description": "Ocupa uno o varios edificios a distancia > 3 m de los edificios más próximos de otros establecimientos.",
     "image": f"{IMG}/20eb765073b37c606cae592f818b9bc799246bf8b46af886e0a2e5d698971919.png"},
    {"value": "D", "label": "Tipo D · espacio abierto",
     "description": "El establecimiento ocupa un espacio abierto que puede estar total o parcialmente cubierto, siempre que el porcentaje de superficie ocupada por la construcción y el material combustible cumpla los límites del Anexo I.",
     "image": f"{IMG}/1e88e13a9097ec172b9858beb61e2d1988b21181c13b4a0baa508c8c38ad3332.png"},
]

# Tabla 1.3.2 · coeficiente adimensional de peligrosidad por combustibilidad (Ci)
CI_TABLE = [
    {"grado": "Alta", "ci": 1.60, "descripcion": "Productos de alta combustibilidad (líquidos y sólidos que se inflaman con facilidad)."},
    {"grado": "Media", "ci": 1.40, "descripcion": "Productos de combustibilidad media."},
    {"grado": "Baja", "ci": 1.20, "descripcion": "Productos de baja combustibilidad."},
    {"grado": "Baja / incombustible", "ci": 1.00, "descripcion": "Productos que no arden o combustibilidad muy baja."},
    {"grado": "Alta + humígeno", "ci": 1.92, "descripcion": "Alta combustibilidad con productos muy fumígenos (+20%)."},
    {"grado": "Media + humígeno", "ci": 1.68, "descripcion": "Combustibilidad media con productos muy fumígenos (+20%)."},
    {"grado": "Baja + humígeno", "ci": 1.44, "descripcion": "Baja combustibilidad con productos muy fumígenos (+20%)."},
]


def _p(name, qsi, ci, rmin=1.0):
    """Actividad de producción: qs en MJ/m². ra por defecto = rmin (nota 3)."""
    return {"name": name, "modo": "produccion", "qsi": qsi, "ci": ci, "ra": rmin, "rmin": rmin}


def _a(name, qvi, ci, neto=None):
    """Actividad de almacenamiento: qv en MJ/m³ (bruto) y neto opcional. ra por defecto 1,0."""
    return {"name": name, "modo": "almacenamiento", "qvi": qvi, "qvi_neto": neto,
            "ci": ci, "ra": 1.0, "rmin": 1.0}


# ── Tabla 1.3.5 (RSCIEI RD 164/2025) · texto literal por categorías ──────────────
ACTIVITY_CATALOG = [
    {"category": "A. OFICINAS", "subactivities": [
        _p("Oficinas", 700, 1.44, 1.0),
        _p("Salas de reuniones, salas de conferencias", 300, 1.44, 1.0),
        _a("Archivos", 1600, 1.20, 2100),
    ]},
    {"category": "B. CARTÓN, PAPEL", "subactivities": [
        _a("Fábrica de cartón/cartón ondulado: Almacenamiento de materias primas", 1700, 1.20, 2200),
        _a("Fábrica de cartón/cartón ondulado: Almacenamiento en bobinas", 3700, 1.20, 14700),
        _p("Fábrica de cartón/cartón ondulado: Producción, transformación", 1500, 1.20, 1.0),
        _a("Fábrica de papel: Almacenamiento de materias primas (celulosa)", 20000, 1.00, 22000),
        _a("Fábrica de papel: Almacenamiento a granel (papel viejo, prensado)", 6900, 1.20, 8600),
        _a("Fábrica de papel: Almacenamiento a granel (papel viejo, suelto)", 2800, 1.40, 4000),
        _p("Fábrica de papel: Producción, transformación (de 200 a 1.200)", 700, 1.20, 1.0),
        _a("Fábrica de papel: Almacenamiento de producto acabado", 2800, 1.20, 5100),
        _a("Imprenta: Almacenamiento de papel en bobinas", 4200, 1.20, 6200),
        _p("Imprenta: Producción", 500, 1.68, 1.4),
        _p("Imprenta: Producción con local para desenrollado del papel", 2100, 1.68, 1.4),
        _p("Imprenta: Expedición, embalaje (de 200 a 2.400)", 1800, 1.20, 1.0),
        _a("Imprenta: Expedición, embalaje · almacenamiento (de 300 a 3.000)", 2500, 1.20),
        _p("Encuadernación", 2400, 1.20, 1.0),
    ]},
    {"category": "C. INDUSTRIA ALIMENTARIA", "subactivities": [
        _p("Bebidas sin alcohol (o de baja graduación): Relleno", 350, 1.20, 1.0),
        _a("Bebidas sin alcohol (o de baja graduación): Almacenamiento", 600, 1.20, 900),
        _p("Otras bebidas específicas: Bodegas (vinos)", 80, 1.00, 1.0),
        _p("Otras bebidas específicas: Bebidas alcohólicas (licores)", 700, 1.40, 1.0),
        _a("Otras bebidas específicas: Bebidas alcohólicas, almacenamiento", 800, 1.40),
        _a("Chocolate: Almacenamiento de materias primas (incluyendo embalaje)", 5200, 1.44, 8200),
        _p("Chocolate: Producción, conchado", 1200, 1.20, 1.0),
        _a("Chocolate: Alm. de producto acabado, expedición", 1800, 1.44, 2900),
        _a("Comercio alimentario: Almacenamiento de productos frescos, expedición", 900, 1.20, 1800),
        _a("Comercio alimentario: Almacenamiento de envases", 1800, 1.20, 2400),
        _p("Comercio alimentario: Envasado, despiece de carnes", 1900, 1.20, 1.0),
        _p("Fabricación de productos lácteos: Producción de queso", 300, 1.00, 1.0),
        _a("Fabricación de productos lácteos: Almacenamiento de queso", 1100, 1.00, 1600),
        _a("Granos (harinera): Almacenamiento de harina", 3900, 1.20, 5300),
        _p("Granos (harinera): Producción de harina", 1100, 1.20, 1.4),
        _p("Grasas, aceites, mantequilla: Producción de grasas, aceites", 8500, 1.68, 1.4),
        _a("Grasas, aceites, mantequilla: Almacenamiento de grasas, aceites, mantequilla", 5300, 1.68, 7900),
        _p("Pastas alimenticias: Producción de pastas alimenticias", 700, 1.20, 1.4),
        _a("Pastas alimenticias: Almacenamiento de pastas alimenticias", 1800, 1.20, 2700),
        _a("Productos de panadería y pastelería: Almacenamiento de materias primas", 1500, 1.20, 2800),
        _p("Productos de panadería y pastelería: Producción", 500, 1.44, 1.4),
        _a("Productos de panadería y pastelería: Almacenamiento de producto acabado, expedición", 2000, 1.44, 2200),
        _p("Azúcar: Producción, embalaje", 200, 1.20, 1.0),
        _a("Azúcar: Almacenamiento", 4600, 1.20, 6300),
        _p("Congelados: Producción", 800, 1.00, 1.4),
        _a("Congelados: Almacén", 375, 1.00),
    ]},
    {"category": "D. INDUSTRIA QUÍMICA", "subactivities": [
        _p("Industria química general: Producción (de 500 a 7.800 · estudiar cada caso)", 500, 1.68, 1.4),
        _a("Industria química general: Almacenamiento, disolventes (de 1.800 a 6.800)", 6800, 1.92),
        _a("Industria química general: Almacenamiento, resina epoxi", 3800, 1.44, 5000),
        _p("Productos farmacéuticos: Producción", 900, 1.68, 1.4),
        _a("Productos farmacéuticos: Almacenamiento", 1800, 1.68, 2500),
    ]},
    {"category": "E. LOGÍSTICA", "subactivities": [
        _a("Centros de distribución: Almacenamiento multiproducto (genérico) (de 300 a 8.100)", 8100, 1.44, 16200),
        _a("Centros de distribución: Almacenamiento de productos de jardín", 1500, 1.44, 3100),
        _a("Centros de distribución: Almacenamiento de aparatos eléctricos", 1000, 1.44, 1600),
        _a("Centros de distribución: Almacenamiento de muebles (excepto metálicos)", 1800, 1.44, 2800),
    ]},
    {"category": "F. MATERIAS Y MERCANCÍAS DIVERSAS", "subactivities": [
        _a("Accesorios de automóviles: Almacén de recambios", 800, 1.44, 1300),
        _a("Accesorios de automóviles: Almacenamiento de líquidos (aceites, limpiadores, disolventes)", 1200, 1.68, 3000),
        _a("Accesorios de automóviles: Almacén de neumáticos", 1000, 1.44, 1500),
        _p("Forraje: Producción de alimentos compuestos", 1400, 1.20, 1.4),
        _a("Forraje: Almacenamiento de alimentos compuestos", 1300, 1.20, 2000),
        _p("Electrodomésticos: Producción y embalaje", 150, 1.44, 1.0),
        _a("Electrodomésticos: Almacenamiento", 1000, 1.44, 1600),
        _a("Reciclaje de residuos: Residuos especiales (pinturas, disolventes)", 2500, 1.68, 6100),
        _a("Reciclaje de residuos: Residuos especiales (ácidos)", 1300, 1.20, 2800),
        _a("Reciclaje de residuos: Reciclaje de plásticos, almacén", 3800, 1.44, 6000),
        _p("Reciclaje de residuos: Reciclaje de plásticos, producción", 1200, 1.44, 1.0),
        _a("Reciclaje de residuos: Astillas y recortes de madera", 1500, 1.20, 2100),
        _p("Materiales de construcción: Ladrillos silicocalcáreos", 350, 1.00, 1.0),
        _p("Materiales de construcción: Hormigón", 300, 1.00, 1.0),
        _a("Materiales de construcción: Madera", 1600, 1.20, 3200),
        _a("Materiales de construcción: Materiales de aislamiento sintéticos: poliestireno espumado (EPS y XPS)", 600, 1.44, 700),
        _a("Materiales de construcción: Venta de artículos de construcción", 900, 1.44, 1500),
        _p("Producción de vidrio: Embalaje", 350, 1.20, 1.0),
        _a("Producción de vidrio: Almacenamiento", 150, 1.20, 200),
        _p("Productos de tabaco: Producción", 500, 1.44, 1.0),
        _a("Productos de tabaco: Almacenamiento (tabaco, fábrica de cigarrillos)", 1400, 1.44, 1900),
    ]},
    {"category": "G. TEXTILES", "subactivities": [
        _a("Telas para confección y tapizado, prendas de vestir: Almacenamiento", 400, 1.44, 800),
        _p("Fábrica de alfombras: Producción", 2500, 1.44, 1.0),
        _p("Fábrica de alfombras: Producción, teñido", 300, 1.20, 1.0),
        _a("Fábrica de alfombras: Almacenamiento", 1100, 1.44, 1800),
        _p("Hilado: Producción", 600, 1.44, 1.0),
        _a("Hilado: Almacenamiento", 3200, 1.44, 4300),
        _p("Tejidos: Producción", 250, 1.20, 1.0),
        _a("Tejidos: Almacenamiento", 1100, 1.20, 1400),
    ]},
    {"category": "H. TRANSFORMACIÓN DE METALES", "subactivities": [
        _p("Construcción de automóviles: Producción: Automóviles, guarnición", 700, 1.44, 1.0),
        _p("Construcción de automóviles: Producción: Automóviles, montaje", 300, 1.44, 1.0),
        _p("Construcción de automóviles: Producción: Automóviles, pintura", 500, 1.44, 1.0),
        _p("Construcción de automóviles: Producción de vehículos especiales (limpieza o blindados)", 400, 1.44, 1.0),
        _a("Construcción de automóviles: Almacenamiento", 600, 1.44, 900),
        _a("Construcción metálica: Almacenamiento de pinturas, recubrimientos en polvo", 1800, 1.68, 3300),
        _p("Construcción metálica: Pintura con pistola", 100, 1.92, 1.4),
        _p("Construcción metálica: Producción, galvanizado", 250, 1.00, 1.0),
        _a("Construcción metálica: Almacenamiento", 150, 1.00, 200),
        _p("Fabricación de máquinas: Trabajo en metal", 250, 1.00, 1.0),
        _a("Fabricación de máquinas: Almacenamiento, expedición", 100, 1.20, 150),
        _p("Relojes: Producción", 300, 1.00, 1.0),
    ]},
    {"category": "I. TRANSFORMACIÓN DE PLÁSTICOS", "subactivities": [
        _p("Fábrica de cables: Producción", 1000, 1.44, 1.0),
        _a("Fábrica de cables: Alm. de producto acabado", 3000, 1.44, 6200),
        _p("Fábrica de láminas y lonas: Producción", 1300, 1.44, 1.0),
        _a("Fábrica de láminas y lonas: Almacenamiento de producto acabado", 1600, 1.44, 2400),
        _a("Materias sintéticas: Almacenamiento de materias primas (gránulos)", 4700, 1.44, 8000),
        _p("Materias sintéticas: Botellas de PET, moldeo por inyección", 800, 1.44, 1.0),
        _a("Materias sintéticas: Botellas de PET, almacenamiento", 700, 1.44, 1300),
        _p("Materias sintéticas: Poliestireno, corte", 300, 1.44, 1.0),
        _a("Materias sintéticas: Poliestireno, almacenamiento", 300, 1.44, 450),
        _a("Materias sintéticas: Almacenamiento de espumas (acolchado, colchones)", 400, 1.44, 700),
        _p("Moldeo por inyección: Producción", 1000, 1.44, 1.0),
        _a("Moldeo por inyección: Almacenamiento de producto acabado", 1700, 1.44, 2100),
        _p("Paneles rígidos de espuma: Producción", 1600, 1.44, 1.0),
        _a("Paneles rígidos de espuma: Almacenamiento de producto acabado", 1700, 1.44, 3100),
        _p("Tuberías, conductos: Producción", 1000, 1.44, 1.0),
        _a("Tuberías, conductos: Almacenamiento de producto acabado", 2200, 1.44, 3500),
    ]},
    {"category": "J. ARTÍCULOS DE MADERA", "subactivities": [
        _p("Carpintería: Producción pura", 900, 1.20, 1.0),
        _p("Carpintería: Sala de producción con depósito intermedio", 1700, 1.20, 1.0),
        _a("Carpintería: Almacenamiento", 2200, 1.20, 3200),
        _p("Venta de artículos de madera: Desechos", 5000, 1.20, 1.0),
        _a("Venta de artículos de madera: Almacenamiento", 1900, 1.20, 5300),
        _a("Briquetas (pellet): Almacenamiento", 11600, 1.20, 16600),
        _p("Tableros de partículas: Producción de paneles de partículas", 1200, 1.20, 1.0),
        _a("Tableros de partículas: Almacenamiento", 5600, 1.20, 9000),
        _p("Carpintería de construcción e interior: Producción pura", 900, 1.20, 1.0),
        _p("Carpintería de construcción e interior: Producción con depósito intermedio", 1800, 1.20, 1.0),
        _a("Carpintería de construcción e interior: Almacenamiento", 1800, 1.20, 2800),
        _p("Fabricación de muebles tapizados", 550, 1.44, 1.4),
        _p("Lacado de muebles", 550, 1.92, 1.4),
        _p("Aserradero", 1500, 1.20, 1.0),
        _a("Aserradero: Almacén de madera aserrada", 2400, 1.20, 4900),
    ]},
    {"category": "K. OTROS", "subactivities": [
        _p("Talleres de reparación", 400, 1.44, 1.0),
        _p("Cine", 300, 1.00, 1.0),
        _p("Farmacia (incluso almacén)", 800, 1.40, 1.0),
        _p("Joyería (venta)", 300, 1.20, 1.0),
        _p("Juguetería (venta)", 500, 1.44, 1.0),
        _p("Lavandería", 200, 1.20, 1.0),
        _p("Librería (venta)", 1000, 1.20, 1.0),
        _p("Panadería (venta)", 300, 1.20, 1.0),
        _p("Papelería (venta)", 700, 1.20, 1.0),
        _p("Perfumería (venta)", 400, 1.20, 1.0),
        _p("Restaurante", 300, 1.20, 1.0),
        _p("Tintorería", 500, 1.44, 1.0),
        _p("Aparatos eléctricos o electrónicos (venta)", 400, 1.20, 1.0),
        _p("Artículos deportivos (venta)", 800, 1.44, 1.0),
        _p("Cochecitos de bebé (venta)", 300, 1.20, 1.0),
        _p("Caramelos y dulces (venta)", 400, 1.00, 1.0),
        _p("Electrodomésticos (venta)", 300, 1.44, 1.0),
        _p("Muebles (exposición y venta) (de 400 a 600)", 600, 1.44, 1.0),
        _p("Prendas de vestir (venta)", 600, 1.20, 1.0),
        _p("Zapatería (venta)", 500, 1.44, 1.0),
        _a("Artículos de papelería", 1100, 1.20),
        _a("Artículos de perfumería", 500, 1.20),
        _a("Artículos de caucho", 5000, 1.44),
        _a("Biblioteca (depósito de libros)", 2000, 1.00),
        _a("Calzado", 400, 1.44),
        _a("Caramelos y dulces", 1500, 1.20),
        _a("Cartonaje", 2500, 1.20),
        _a("Conservas", 375, 1.00),
        _a("Cosméticos", 500, 1.20),
        _a("Discos compactos y similares", 3400, 1.20),
        _a("Flores artificiales", 200, 1.44),
        _a("Juguetes", 800, 1.44),
        _a("Material de oficina", 1300, 1.44),
    ]},
]

ACTIVITY_TYPES = [c["category"] for c in ACTIVITY_CATALOG]

# Densidades de ocupación (CTE DB-SI, Tabla 2.1). m²/persona; None = sin ocupación.
OCCUPANCY_DENSITIES = [
    {"uso": "Sin ocupación (mantenimiento/instalaciones)", "densidad": None},
    {"uso": "Almacén / archivo (uso ocasional)", "densidad": 40},
    {"uso": "Aparcamiento de vehículos", "densidad": 40},
    {"uso": "Reserva / trastero", "densidad": 40},
    {"uso": "Oficinas / administrativo", "densidad": 10},
    {"uso": "Despacho", "densidad": 10},
    {"uso": "Zona de servicio (cocinas)", "densidad": 10},
    {"uso": "Taller / laboratorio", "densidad": 5},
    {"uso": "Vestíbulo / probador / caja", "densidad": 5},
    {"uso": "Aseos de planta", "densidad": 3},
    {"uso": "Vestuarios", "densidad": 3},
    {"uso": "Zona de ventas (comercial)", "densidad": 2},
    {"uso": "Zona de público (sentado)", "densidad": 1.5},
    {"uso": "Zona de público (de pie)", "densidad": 1},
]

# Tabla 1.3.4 · Criterios para determinar el coeficiente de activación (Ra / R)
RA_TABLE = [
    {"ra": 0.8, "grado": "Reducido",
     "criterio": "Sector dedicado exclusivamente a almacenamiento de baja altura (≤ 2,50 m) y superficie en planta < 50 m². No aplicable si la Tabla 1.3.5 (Rmin) exige un valor superior."},
    {"ra": 1.0, "grado": "Normal (por defecto)",
     "criterio": "Valor por defecto cuando no concurren las casuísticas de un valor distinto (debe justificarse debidamente)."},
    {"ra": 1.4, "grado": "Alto",
     "criterio": "Aumento significativo de la probabilidad de inicio del incendio por fuentes térmicas, químicas o equivalentes (p. ej. trabajos habituales con chispas o llamas abiertas), o actividad marcada como tal en la Tabla 1.3.5."},
    {"ra": 1.8, "grado": "Muy alto",
     "criterio": "Se cumplen SIMULTÁNEAMENTE las dos situaciones de R = 1,4 (p. ej. zona de trabajos con llama + zona de almacenamiento de propagación rápida)."},
]
