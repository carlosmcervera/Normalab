"""Wizard schema for the RSCIEI module (dynamic, module-driven rendering)."""

CONFIG_OPTIONS = [
    {"value": "AV", "label": "Tipo A · separación vertical (AV)"},
    {"value": "AH", "label": "Tipo A · separación horizontal (AH)"},
    {"value": "B", "label": "Tipo B · edificio propio adosado (< 3 m)"},
    {"value": "C", "label": "Tipo C · edificio propio aislado (> 3 m)"},
    {"value": "D", "label": "Tipo D · espacio abierto"},
    {"value": "E", "label": "Tipo E · espacio abierto cubierto"},
]

# Presets orientativos (Tabla 1.3): actividad -> valores por defecto
ACTIVITY_PRESETS = [
    {"label": "Oficinas", "modo": "produccion", "qsi": 700, "ci": 1.44, "ra": 1.0},
    {"label": "Salas de reuniones / conferencias", "modo": "produccion", "qsi": 300, "ci": 1.44, "ra": 1.0},
    {"label": "Archivo de documentación", "modo": "almacenamiento", "qvi": 1600, "ci": 1.20, "ra": 1.0},
    {"label": "Fábrica de papel · producción", "modo": "produccion", "qsi": 1200, "ci": 1.20, "ra": 1.0},
    {"label": "Almacén de papel en bobinas", "modo": "almacenamiento", "qvi": 4200, "ci": 1.20, "ra": 1.0},
    {"label": "Imprenta · producción", "modo": "produccion", "qsi": 500, "ci": 1.68, "ra": 1.4},
    {"label": "Chocolate · producción", "modo": "produccion", "qsi": 1200, "ci": 1.20, "ra": 1.0},
    {"label": "Bodega de vinos", "modo": "almacenamiento", "qvi": 80, "ci": 1.00, "ra": 1.0},
    {"label": "Bebidas alcohólicas · almacenamiento", "modo": "almacenamiento", "qvi": 800, "ci": 1.00, "ra": 1.0},
]

CI_HELP = [
    {"grado": "Alta combustibilidad", "ci": 1.6},
    {"grado": "Media combustibilidad", "ci": 1.4},
    {"grado": "Baja combustibilidad", "ci": 1.2},
    {"grado": "Baja / incombustible", "ci": 1.0},
]


def get_schema() -> dict:
    return {
        "presets": ACTIVITY_PRESETS,
        "ci_help": CI_HELP,
        "steps": [
            {
                "id": "establecimiento",
                "title": "Datos del establecimiento",
                "description": "Identificación de la actividad y configuración del sector de incendio.",
                "fields": [
                    {"name": "actividad", "label": "Actividad / uso industrial", "type": "text", "required": True,
                     "placeholder": "Ej. Nave de fabricación de mobiliario"},
                    {"name": "tipo_configuracion", "label": "Tipo de configuración (Anexo I)", "type": "select",
                     "options": CONFIG_OPTIONS, "required": True},
                    {"name": "superficie_sector", "label": "Superficie construida del sector, A (m²)",
                     "type": "number", "required": True, "min": 1, "step": 1},
                    {"name": "ra", "label": "Coef. de peligrosidad por activación (Ra)", "type": "number",
                     "required": True, "min": 0.1, "step": 0.1, "default": 1.0,
                     "help": "Según Tabla 1.3. Use el valor de la actividad más desfavorable del sector."},
                    {"name": "fachada_accesible", "label": "Fachada accesible ≥ 50% del perímetro",
                     "type": "boolean", "help": "Nota 2, Tabla 2.1: incrementa la superficie máxima ×1,25."},
                    {"name": "rociadores", "label": "Rociadores automáticos en todo el sector",
                     "type": "boolean", "help": "Nota 3, Tabla 2.1: incrementa la superficie máxima ×2."},
                ],
            },
            {
                "id": "zonas",
                "title": "Zonas y actividades del sector",
                "description": "Añada cada zona con su carga de fuego. Qs se pondera por superficie.",
                "type": "repeater",
                "item_label": "Zona",
                "fields": [
                    {"name": "descripcion", "label": "Descripción", "type": "text", "required": True,
                     "placeholder": "Ej. Zona de producción"},
                    {"name": "modo", "label": "Tipo", "type": "select", "required": True,
                     "options": [
                         {"value": "produccion", "label": "Producción / transformación"},
                         {"value": "almacenamiento", "label": "Almacenamiento"},
                     ]},
                    {"name": "qsi", "label": "qsi (MJ/m²)", "type": "number", "min": 0, "step": 1,
                     "show_if": {"modo": "produccion"}},
                    {"name": "qvi", "label": "qvi (MJ/m³)", "type": "number", "min": 0, "step": 1,
                     "show_if": {"modo": "almacenamiento"}},
                    {"name": "hi", "label": "Altura almac. hi (m)", "type": "number", "min": 0, "step": 0.1,
                     "show_if": {"modo": "almacenamiento"}},
                    {"name": "superficie", "label": "Superficie Si (m²)", "type": "number", "min": 0, "step": 1,
                     "required": True},
                    {"name": "ci", "label": "Ci", "type": "number", "min": 0, "step": 0.01, "default": 1.0,
                     "required": True},
                ],
            },
        ],
    }
