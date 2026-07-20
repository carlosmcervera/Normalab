"""Catálogo RSCIEI: tipos de configuración (con imágenes), tabla de coeficiente
de combustibilidad Ci y catálogo jerárquico de actividades (Tabla 1.3 - valores
representativos de densidad de carga de fuego media y coeficientes)."""

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

# Tabla del coeficiente adimensional de peligrosidad por combustibilidad (Ci)
CI_TABLE = [
    {"grado": "Alta", "ci": 1.60, "descripcion": "Productos de alta combustibilidad (líquidos y sólidos que se inflaman con facilidad)."},
    {"grado": "Media", "ci": 1.40, "descripcion": "Productos de combustibilidad media."},
    {"grado": "Baja", "ci": 1.20, "descripcion": "Productos de baja combustibilidad."},
    {"grado": "Baja / incombustible", "ci": 1.00, "descripcion": "Productos que no arden o combustibilidad muy baja."},
    {"grado": "Alta + humígeno", "ci": 1.92, "descripcion": "Alta combustibilidad con productos muy fumígenos (+20%)."},
    {"grado": "Media + humígeno", "ci": 1.68, "descripcion": "Combustibilidad media con productos muy fumígenos (+20%)."},
    {"grado": "Baja + humígeno", "ci": 1.44, "descripcion": "Baja combustibilidad con productos muy fumígenos (+20%)."},
]

# Catálogo jerárquico de actividades (valores representativos de la Tabla 1.3)
# Cada subactividad: name, modo (produccion|almacenamiento), qsi (MJ/m²) o qvi (MJ/m³), ci, ra
ACTIVITY_CATALOG = [
    {"category": "Oficinas", "subactivities": [
        {"name": "Oficinas", "modo": "produccion", "qsi": 700, "ci": 1.44, "ra": 1.0},
        {"name": "Salas de reuniones / conferencias", "modo": "produccion", "qsi": 300, "ci": 1.44, "ra": 1.0},
        {"name": "Archivo de documentación", "modo": "almacenamiento", "qvi": 2100, "ci": 1.20, "ra": 1.0},
    ]},
    {"category": "Alimentación y bebidas", "subactivities": [
        {"name": "Bebidas sin alcohol · relleno/envasado", "modo": "produccion", "qsi": 350, "ci": 1.20, "ra": 1.0},
        {"name": "Bebidas sin alcohol · almacenamiento", "modo": "almacenamiento", "qvi": 900, "ci": 1.20, "ra": 1.0},
        {"name": "Bodegas (vinos) · almacenamiento", "modo": "almacenamiento", "qvi": 80, "ci": 1.00, "ra": 1.0},
        {"name": "Bebidas alcohólicas (licores) · almacenamiento", "modo": "almacenamiento", "qvi": 800, "ci": 1.40, "ra": 1.0},
        {"name": "Chocolate · producción/conchado", "modo": "produccion", "qsi": 1200, "ci": 1.20, "ra": 1.0},
        {"name": "Chocolate · almacén materias primas", "modo": "almacenamiento", "qvi": 5200, "ci": 1.44, "ra": 1.0},
        {"name": "Grasas y aceites · producción", "modo": "produccion", "qsi": 8500, "ci": 1.68, "ra": 1.4},
        {"name": "Grasas y aceites · almacenamiento", "modo": "almacenamiento", "qvi": 7900, "ci": 1.68, "ra": 1.0},
        {"name": "Harinera · producción de harina", "modo": "produccion", "qsi": 1100, "ci": 1.20, "ra": 1.4},
        {"name": "Harinera · almacén de harina", "modo": "almacenamiento", "qvi": 5300, "ci": 1.20, "ra": 1.0},
        {"name": "Azúcar · almacenamiento", "modo": "almacenamiento", "qvi": 6300, "ci": 1.20, "ra": 1.0},
        {"name": "Panadería/pastelería · producción", "modo": "produccion", "qsi": 500, "ci": 1.44, "ra": 1.4},
    ]},
    {"category": "Cartón y papel", "subactivities": [
        {"name": "Fábrica de cartón ondulado · producción", "modo": "produccion", "qsi": 1500, "ci": 1.20, "ra": 1.0},
        {"name": "Cartón · almacén de materias primas", "modo": "almacenamiento", "qvi": 2200, "ci": 1.20, "ra": 1.0},
        {"name": "Cartón/papel · almacén en bobinas", "modo": "almacenamiento", "qvi": 14700, "ci": 1.20, "ra": 1.0},
        {"name": "Fábrica de papel · producción", "modo": "produccion", "qsi": 2800, "ci": 1.20, "ra": 1.0},
        {"name": "Papel · almacén de producto acabado", "modo": "almacenamiento", "qvi": 5100, "ci": 1.20, "ra": 1.0},
        {"name": "Papel viejo (suelto) · almacenamiento a granel", "modo": "almacenamiento", "qvi": 4000, "ci": 1.40, "ra": 1.0},
    ]},
    {"category": "Artes gráficas / imprenta", "subactivities": [
        {"name": "Imprenta · almacén de papel en bobinas", "modo": "almacenamiento", "qvi": 6200, "ci": 1.20, "ra": 1.0},
        {"name": "Imprenta · producción", "modo": "produccion", "qsi": 500, "ci": 1.68, "ra": 1.4},
        {"name": "Imprenta · desenrollado de papel", "modo": "produccion", "qsi": 2100, "ci": 1.68, "ra": 1.4},
        {"name": "Imprenta · expedición/embalaje", "modo": "produccion", "qsi": 2400, "ci": 1.20, "ra": 1.0},
    ]},
    {"category": "Madera y muebles", "subactivities": [
        {"name": "Carpintería · producción pura", "modo": "produccion", "qsi": 900, "ci": 1.20, "ra": 1.0},
        {"name": "Carpintería · producción con depósito intermedio", "modo": "produccion", "qsi": 1700, "ci": 1.20, "ra": 1.0},
        {"name": "Carpintería · almacenamiento", "modo": "almacenamiento", "qvi": 3200, "ci": 1.20, "ra": 1.0},
        {"name": "Tableros de partículas · producción", "modo": "produccion", "qsi": 1200, "ci": 1.20, "ra": 1.0},
        {"name": "Tableros de partículas · almacenamiento", "modo": "almacenamiento", "qvi": 9000, "ci": 1.20, "ra": 1.0},
        {"name": "Muebles tapizados · fabricación", "modo": "produccion", "qsi": 550, "ci": 1.44, "ra": 1.4},
        {"name": "Lacado de muebles", "modo": "produccion", "qsi": 550, "ci": 1.92, "ra": 1.4},
        {"name": "Briquetas / pellet · almacenamiento", "modo": "almacenamiento", "qvi": 16600, "ci": 1.20, "ra": 1.0},
    ]},
    {"category": "Textil y confección", "subactivities": [
        {"name": "Telas / prendas · almacenamiento", "modo": "almacenamiento", "qvi": 800, "ci": 1.44, "ra": 1.0},
        {"name": "Fábrica de alfombras · producción", "modo": "produccion", "qsi": 2500, "ci": 1.44, "ra": 1.0},
        {"name": "Hilado · producción", "modo": "produccion", "qsi": 600, "ci": 1.44, "ra": 1.0},
        {"name": "Hilado · almacenamiento", "modo": "almacenamiento", "qvi": 4300, "ci": 1.44, "ra": 1.0},
        {"name": "Tejidos · producción", "modo": "produccion", "qsi": 250, "ci": 1.20, "ra": 1.0},
        {"name": "Tejidos · almacenamiento", "modo": "almacenamiento", "qvi": 1400, "ci": 1.20, "ra": 1.0},
    ]},
    {"category": "Caucho y plásticos", "subactivities": [
        {"name": "Fábrica de cables · producción", "modo": "produccion", "qsi": 1000, "ci": 1.44, "ra": 1.0},
        {"name": "Materias sintéticas (gránulos) · almacenamiento", "modo": "almacenamiento", "qvi": 8000, "ci": 1.44, "ra": 1.0},
        {"name": "Moldeo por inyección · producción", "modo": "produccion", "qsi": 1000, "ci": 1.44, "ra": 1.0},
        {"name": "Moldeo por inyección · producto acabado", "modo": "almacenamiento", "qvi": 2100, "ci": 1.44, "ra": 1.0},
        {"name": "Botellas PET · almacenamiento", "modo": "almacenamiento", "qvi": 1300, "ci": 1.44, "ra": 1.0},
        {"name": "Espumas / colchones · almacenamiento", "modo": "almacenamiento", "qvi": 700, "ci": 1.44, "ra": 1.0},
        {"name": "Tuberías y conductos · producto acabado", "modo": "almacenamiento", "qvi": 3500, "ci": 1.44, "ra": 1.0},
    ]},
    {"category": "Industria química", "subactivities": [
        {"name": "Química general · producción", "modo": "produccion", "qsi": 7800, "ci": 1.68, "ra": 1.4},
        {"name": "Química · almacén de disolventes", "modo": "almacenamiento", "qvi": 6800, "ci": 1.92, "ra": 1.0},
        {"name": "Química · almacén resina epoxi", "modo": "almacenamiento", "qvi": 5000, "ci": 1.44, "ra": 1.0},
        {"name": "Productos farmacéuticos · producción", "modo": "produccion", "qsi": 900, "ci": 1.68, "ra": 1.4},
        {"name": "Productos farmacéuticos · almacenamiento", "modo": "almacenamiento", "qvi": 2500, "ci": 1.68, "ra": 1.0},
    ]},
    {"category": "Pinturas y barnices", "subactivities": [
        {"name": "Almacén de pinturas / recubrimientos en polvo", "modo": "almacenamiento", "qvi": 1800, "ci": 1.68, "ra": 1.0},
        {"name": "Pintura con pistola / cabina", "modo": "produccion", "qsi": 100, "ci": 1.92, "ra": 1.4},
    ]},
    {"category": "Metal y mecánica", "subactivities": [
        {"name": "Construcción metálica · producción/galvanizado", "modo": "produccion", "qsi": 250, "ci": 1.00, "ra": 1.0},
        {"name": "Construcción metálica · almacenamiento", "modo": "almacenamiento", "qvi": 200, "ci": 1.00, "ra": 1.0},
        {"name": "Fabricación de máquinas · trabajo en metal", "modo": "produccion", "qsi": 250, "ci": 1.00, "ra": 1.0},
        {"name": "Fabricación de máquinas · almacén/expedición", "modo": "almacenamiento", "qvi": 150, "ci": 1.20, "ra": 1.0},
    ]},
    {"category": "Automoción", "subactivities": [
        {"name": "Automóviles · guarnición", "modo": "produccion", "qsi": 700, "ci": 1.44, "ra": 1.0},
        {"name": "Automóviles · montaje", "modo": "produccion", "qsi": 300, "ci": 1.44, "ra": 1.0},
        {"name": "Automóviles · almacenamiento", "modo": "almacenamiento", "qvi": 900, "ci": 1.44, "ra": 1.0},
        {"name": "Recambios · almacenamiento", "modo": "almacenamiento", "qvi": 1300, "ci": 1.44, "ra": 1.0},
        {"name": "Neumáticos · almacenamiento", "modo": "almacenamiento", "qvi": 1500, "ci": 1.44, "ra": 1.0},
        {"name": "Aceites/limpiadores/disolventes · almacenamiento", "modo": "almacenamiento", "qvi": 3000, "ci": 1.68, "ra": 1.0},
    ]},
    {"category": "Electrónica y electrodomésticos", "subactivities": [
        {"name": "Electrodomésticos · producción/embalaje", "modo": "produccion", "qsi": 150, "ci": 1.44, "ra": 1.0},
        {"name": "Electrodomésticos · almacenamiento", "modo": "almacenamiento", "qvi": 1600, "ci": 1.44, "ra": 1.0},
    ]},
    {"category": "Materiales de construcción", "subactivities": [
        {"name": "Hormigón · producción", "modo": "produccion", "qsi": 300, "ci": 1.00, "ra": 1.0},
        {"name": "Ladrillos silicocalcáreos · producción", "modo": "produccion", "qsi": 350, "ci": 1.00, "ra": 1.0},
        {"name": "Madera de construcción · almacenamiento", "modo": "almacenamiento", "qvi": 3200, "ci": 1.20, "ra": 1.0},
        {"name": "Aislamiento EPS/XPS · producción", "modo": "produccion", "qsi": 700, "ci": 1.44, "ra": 1.0},
        {"name": "Venta de artículos de construcción", "modo": "produccion", "qsi": 1500, "ci": 1.44, "ra": 1.0},
    ]},
]

ACTIVITY_TYPES = [c["category"] for c in ACTIVITY_CATALOG]

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
