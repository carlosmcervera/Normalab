"""Catálogo RSCIEI (RD 164/2025): tipos de configuración (con imágenes), tabla de
coeficiente de combustibilidad Ci, densidades de ocupación (CTE) y catálogo
jerárquico de actividades según la Tabla 1.3.5 de la Guía RSCIEI 2025.

Cada subactividad incluye: name, modo (produccion|almacenamiento), qsi (MJ/m²) o
qvi (MJ/m³), ci (coef. combustibilidad orientativo, ajustable por el técnico), ra
(coef. de activación por defecto) y rmin (valor mínimo de Ra según Tabla 1.3.5).
El modo se asigna por la unidad: MJ/m² → producción; MJ/m³ → almacenamiento.
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


def _p(name, qsi, ci, ra, rmin):
    return {"name": name, "modo": "produccion", "qsi": qsi, "ci": ci, "ra": ra, "rmin": rmin}


def _a(name, qvi, ci, ra, rmin):
    return {"name": name, "modo": "almacenamiento", "qvi": qvi, "ci": ci, "ra": ra, "rmin": rmin}


# Catálogo jerárquico completo (Tabla 1.3.5, Guía RSCIEI 2025)
ACTIVITY_CATALOG = [
    {"category": "Oficinas y administrativo", "subactivities": [
        _p("Oficinas", 700, 1.20, 1.0, 1.0),
        _p("Salas de reuniones / conferencias", 300, 1.20, 1.0, 1.0),
        _a("Archivos", 1600, 1.20, 1.2, 1.2),
        _a("Biblioteca (depósito de libros)", 2000, 1.20, 1.0, 1.0),
        _a("Material de oficina · almacenamiento", 1300, 1.44, 1.44, 1.44),
    ]},
    {"category": "Papel y cartón", "subactivities": [
        _p("Cartón ondulado · producción/transformación", 1500, 1.20, 1.0, 1.0),
        _a("Papel · almacén de materias primas (celulosa)", 20000, 1.20, 1.0, 1.0),
        _a("Papel · almacén de producto acabado", 2800, 1.20, 1.2, 1.2),
        _a("Papel · almacén en bobinas", 4200, 1.20, 1.2, 1.2),
        _a("Papel viejo prensado · almacenamiento a granel", 6900, 1.40, 1.2, 1.2),
        _a("Papel viejo suelto · almacenamiento a granel", 2800, 1.40, 1.4, 1.4),
        _a("Cartonaje · almacenamiento", 2500, 1.20, 1.2, 1.2),
    ]},
    {"category": "Artes gráficas / imprenta", "subactivities": [
        _p("Imprenta · producción", 500, 1.44, 1.4, 1.4),
        _p("Imprenta · producción con desenrollado de papel", 2100, 1.44, 1.4, 1.4),
        _p("Imprenta · expedición/embalaje", 2400, 1.20, 1.0, 1.0),
        _p("Encuadernación", 2400, 1.44, 1.0, 1.0),
    ]},
    {"category": "Alimentación y bebidas", "subactivities": [
        _p("Bebidas sin alcohol · relleno/envasado", 350, 1.20, 1.0, 1.0),
        _a("Bebidas sin alcohol · almacenamiento", 900, 1.20, 1.2, 1.2),
        _a("Bodegas (vinos) · almacenamiento", 80, 1.00, 1.0, 1.0),
        _p("Bebidas alcohólicas (licores) · producción", 700, 1.20, 1.0, 1.0),
        _a("Bebidas alcohólicas (licores) · almacenamiento", 800, 1.40, 1.4, 1.4),
        _a("Chocolate · almacén de materias primas", 5200, 1.44, 1.44, 1.44),
        _p("Chocolate · producción/conchado", 1200, 1.20, 1.0, 1.0),
        _p("Chocolate · producto acabado/expedición", 1800, 1.44, 1.44, 1.44),
        _p("Carne · envasado/despiece", 1900, 1.00, 1.0, 1.0),
        _a("Productos frescos · almacenamiento/expedición", 1800, 1.20, 1.2, 1.2),
        _a("Envases · almacenamiento", 2400, 1.20, 1.2, 1.2),
        _p("Queso · producción", 300, 1.00, 1.0, 1.0),
        _a("Queso · almacenamiento", 1600, 1.00, 1.0, 1.0),
        _p("Harina · producción", 1100, 1.20, 1.4, 1.4),
        _a("Harina · almacenamiento", 5300, 1.20, 1.2, 1.2),
        _p("Grasas y aceites · producción", 8500, 1.68, 1.4, 1.4),
        _a("Grasas, aceites, mantequilla · almacenamiento", 7900, 1.68, 1.68, 1.68),
        _p("Pastas alimenticias · producción", 700, 1.20, 1.4, 1.4),
        _a("Pastas alimenticias · almacenamiento", 2700, 1.20, 1.2, 1.2),
        _a("Panadería/pastelería · almacén de materias primas", 2800, 1.20, 1.2, 1.2),
        _p("Panadería/pastelería · producción", 500, 1.44, 1.4, 1.4),
        _a("Panadería/pastelería · producto acabado/expedición", 2200, 1.44, 1.44, 1.44),
        _p("Azúcar · producción/embalaje", 200, 1.00, 1.0, 1.0),
        _a("Azúcar · almacenamiento", 6300, 1.20, 1.2, 1.2),
        _p("Congelados · producción", 800, 1.44, 1.4, 1.4),
        _a("Congelados · almacén", 375, 1.00, 1.0, 1.0),
        _a("Conservas · almacenamiento", 375, 1.00, 1.0, 1.0),
        _a("Forraje · almacenamiento", 4900, 1.20, 1.2, 1.2),
        _a("Caramelos y dulces · almacenamiento", 5300, 1.20, 1.2, 1.2),
    ]},
    {"category": "Industria química, farmacia y pinturas", "subactivities": [
        _p("Química general · producción", 500, 1.68, 1.4, 1.4),
        _a("Química · almacén de disolventes", 6800, 1.92, 1.92, 1.92),
        _a("Química · almacén de resina epoxi", 5000, 1.44, 1.44, 1.44),
        _p("Productos farmacéuticos · producción", 900, 1.68, 1.4, 1.4),
        _a("Productos farmacéuticos · almacenamiento", 2500, 1.68, 1.68, 1.68),
        _a("Pinturas / recubrimientos en polvo · almacenamiento", 3300, 1.68, 1.0, 1.0),
        _p("Pintura con pistola / cabina", 100, 1.92, 1.4, 1.4),
        _a("Cosméticos · almacenamiento", 500, 1.20, 1.2, 1.2),
        _a("Artículos de caucho · almacenamiento", 5000, 1.44, 1.44, 1.44),
    ]},
    {"category": "Textil, confección y calzado", "subactivities": [
        _p("Tejidos · producción", 250, 1.20, 1.0, 1.0),
        _a("Tejidos · almacenamiento", 1400, 1.20, 1.2, 1.2),
        _p("Prendas de vestir · venta", 600, 1.44, 1.0, 1.0),
        _a("Calzado · almacenamiento", 400, 1.44, 1.44, 1.44),
        _p("Zapatería · venta", 500, 1.44, 1.0, 1.0),
    ]},
    {"category": "Madera y muebles", "subactivities": [
        _p("Carpintería · producción pura", 900, 1.20, 1.0, 1.0),
        _p("Carpintería · producción con depósito intermedio", 1700, 1.20, 1.0, 1.0),
        _a("Carpintería · almacenamiento", 3200, 1.20, 1.2, 1.2),
        _p("Carpintería construcción/interior · producción pura", 900, 1.20, 1.0, 1.0),
        _p("Carpintería construcción/interior · con depósito intermedio", 1800, 1.20, 1.0, 1.0),
        _a("Carpintería construcción/interior · almacenamiento", 2800, 1.20, 1.2, 1.2),
        _p("Aserradero", 1500, 1.20, 1.0, 1.0),
        _a("Madera aserrada · almacén", 4900, 1.20, 1.2, 1.2),
        _p("Venta de artículos de madera", 5000, 1.20, 1.0, 1.0),
        _a("Artículos de madera · almacenamiento", 5300, 1.20, 1.2, 1.2),
        _p("Tableros de partículas · producción", 1200, 1.20, 1.0, 1.0),
        _a("Tableros de partículas · almacenamiento", 9000, 1.20, 1.2, 1.2),
        _p("Muebles tapizados · fabricación", 550, 1.44, 1.4, 1.4),
        _p("Lacado de muebles", 550, 1.92, 1.4, 1.4),
        _p("Muebles · exposición y venta", 600, 1.44, 1.0, 1.0),
        _a("Muebles (excepto metálicos) · almacenamiento", 2800, 1.44, 1.44, 1.44),
        _a("Briquetas / pellet · almacenamiento", 16600, 1.20, 1.2, 1.2),
    ]},
    {"category": "Caucho y plásticos", "subactivities": [
        _a("Materias sintéticas (gránulos) · almacenamiento", 8000, 1.44, 1.44, 1.44),
        _p("Botellas PET · moldeo por inyección", 800, 1.44, 1.0, 1.0),
        _a("Botellas PET · almacenamiento", 1300, 1.44, 1.44, 1.44),
        _p("Poliestireno · corte", 300, 1.44, 1.0, 1.0),
        _a("Poliestireno · almacenamiento", 450, 1.44, 1.44, 1.44),
        _a("Espumas / colchones · almacenamiento", 700, 1.44, 1.44, 1.44),
        _p("Moldeo por inyección · producción", 1000, 1.44, 1.0, 1.0),
        _a("Moldeo por inyección · producto acabado", 2100, 1.44, 1.44, 1.44),
        _p("Paneles rígidos de espuma · producción", 1600, 1.44, 1.0, 1.0),
        _a("Paneles rígidos de espuma · almacenamiento", 3100, 1.44, 1.44, 1.44),
        _p("Tuberías y conductos · producción", 1000, 1.44, 1.0, 1.0),
        _a("Tuberías y conductos · almacenamiento", 3500, 1.44, 1.44, 1.44),
        _p("Láminas y lonas · producción", 1300, 1.44, 1.0, 1.0),
        _a("Láminas y lonas · almacenamiento", 2400, 1.44, 1.44, 1.44),
    ]},
    {"category": "Metal y mecánica", "subactivities": [
        _p("Construcción metálica · producción/galvanizado", 250, 1.00, 1.0, 1.0),
        _a("Construcción metálica · almacenamiento", 200, 1.00, 1.0, 1.0),
        _p("Fabricación de máquinas · trabajo en metal", 250, 1.00, 1.0, 1.0),
        _a("Fabricación de máquinas · almacén/expedición", 150, 1.20, 1.2, 1.2),
        _p("Fábrica de cables · producción", 1000, 1.44, 1.0, 1.0),
        _a("Fábrica de cables · almacén producto acabado", 6200, 1.44, 1.44, 1.44),
        _p("Relojes · producción", 300, 1.00, 1.0, 1.0),
    ]},
    {"category": "Automoción", "subactivities": [
        _p("Automóviles · guarnición", 700, 1.44, 1.0, 1.0),
        _p("Automóviles · montaje", 300, 1.44, 1.0, 1.0),
        _p("Automóviles · pintura", 500, 1.92, 1.0, 1.0),
        _p("Vehículos especiales · producción", 400, 1.44, 1.0, 1.0),
        _a("Automóviles · almacenamiento", 900, 1.44, 1.44, 1.44),
        _a("Recambios · almacenamiento", 1300, 1.44, 1.44, 1.44),
        _a("Neumáticos · almacenamiento", 1500, 1.44, 1.44, 1.44),
        _a("Aceites/limpiadores/disolventes · almacenamiento", 3000, 1.68, 1.0, 1.0),
    ]},
    {"category": "Centros de distribución / logística", "subactivities": [
        _a("Almacén multiproducto (genérico)", 8100, 1.44, 1.44, 1.44),
        _a("Almacén de productos de jardín", 3100, 1.44, 1.44, 1.44),
        _a("Almacén de aparatos eléctricos", 1600, 1.44, 1.44, 1.44),
    ]},
    {"category": "Comercio y servicios", "subactivities": [
        _p("Cine", 300, 1.20, 1.0, 1.0),
        _p("Farmacia (incluido almacén)", 800, 1.44, 1.0, 1.0),
        _p("Joyería · venta", 300, 1.20, 1.0, 1.0),
        _p("Juguetería · venta", 500, 1.44, 1.0, 1.0),
        _p("Lavandería", 200, 1.20, 1.0, 1.0),
        _p("Librería · venta", 1000, 1.44, 1.0, 1.0),
        _p("Panadería · venta", 300, 1.44, 1.0, 1.0),
        _p("Papelería · venta", 700, 1.44, 1.0, 1.0),
        _p("Perfumería · venta", 400, 1.44, 1.0, 1.0),
        _p("Restaurante", 300, 1.20, 1.0, 1.0),
        _p("Tintorería", 500, 1.44, 1.0, 1.0),
        _p("Aparatos eléctricos/electrónicos · venta", 400, 1.44, 1.0, 1.0),
        _p("Artículos deportivos · venta", 800, 1.44, 1.0, 1.0),
        _p("Cochecitos de bebé · venta", 300, 1.44, 1.0, 1.0),
        _p("Caramelos y dulces · venta", 400, 1.20, 1.0, 1.0),
        _p("Electrodomésticos · venta", 300, 1.44, 1.0, 1.0),
        _p("Talleres de reparación", 400, 1.44, 1.0, 1.0),
        _a("Artículos de papelería · almacenamiento", 1100, 1.20, 1.2, 1.2),
        _a("Artículos de perfumería · almacenamiento", 500, 1.20, 1.2, 1.2),
        _a("Discos compactos y similares · almacenamiento", 3400, 1.20, 1.2, 1.2),
        _a("Flores artificiales · almacenamiento", 200, 1.44, 1.44, 1.44),
        _a("Juguetes · almacenamiento", 800, 1.44, 1.44, 1.44),
        _a("Electrodomésticos · almacenamiento", 1600, 1.44, 1.44, 1.44),
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
