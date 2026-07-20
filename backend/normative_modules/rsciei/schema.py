"""Wizard schema for the RSCIEI module (dynamic, module-driven rendering)."""
from normative_modules.rsciei.catalog import (
    ACTIVITY_CATALOG, ACTIVITY_TYPES, CI_TABLE, CONFIG_TYPES,
)


def get_schema() -> dict:
    return {
        "config_types": CONFIG_TYPES,
        "ci_table": CI_TABLE,
        "activity_catalog": ACTIVITY_CATALOG,
        "activity_types": ACTIVITY_TYPES,
        "steps": [
            {
                "id": "establecimiento",
                "title": "Datos del establecimiento",
                "description": "Identificación de la actividad y configuración del sector de incendio.",
                "fields": [
                    {"name": "actividad", "label": "Tipo de actividad", "type": "activity_combobox",
                     "required": True, "placeholder": "Selecciona o escribe una actividad"},
                    {"name": "tipo_configuracion", "label": "Tipo de configuración (Anexo I)",
                     "type": "config_selector", "required": True},
                    {"name": "superficie_sector", "label": "Superficie construida del sector, A (m²)",
                     "type": "number", "required": True, "min": 1, "step": 1},
                    {"name": "ra", "label": "Coef. de peligrosidad por activación (Ra)", "type": "number",
                     "required": True, "min": 0.1, "step": 0.1, "default": 1.0,
                     "help": "Se sugiere automáticamente el Ra máximo de las actividades añadidas al sector."},
                    {"name": "fachada_accesible", "label": "Fachada accesible ≥ 50% del perímetro",
                     "type": "boolean", "help": "Nota 2, Tabla 2.1: incrementa la superficie máxima ×1,25."},
                    {"name": "rociadores", "label": "Rociadores automáticos en todo el sector",
                     "type": "boolean", "help": "Nota 3, Tabla 2.1: incrementa la superficie máxima ×2."},
                    {"name": "situacion", "label": "Situación del sector", "type": "select",
                     "options": [
                         {"value": "sobre_rasante", "label": "Planta sobre rasante"},
                         {"value": "bajo_rasante", "label": "Planta bajo rasante (sótano)"},
                     ], "default": "sobre_rasante"},
                    {"name": "altura_evacuacion", "label": "Altura de evacuación (m)", "type": "number",
                     "min": 0, "step": 0.5, "default": 0, "help": "Para columna seca (obligatoria si ≥ 15 m)."},
                    {"name": "superficie_establecimiento", "label": "Superficie total del establecimiento (m²)",
                     "type": "number", "min": 0, "step": 1,
                     "help": "Para hidrantes exteriores. Si se deja vacío se usa la superficie del sector."},
                    {"name": "cubierta_ligera", "label": "Cubierta ligera (no para evacuación, < 100 kg/m²)",
                     "type": "boolean"},
                ],
            },
            {
                "id": "zonas",
                "title": "Actividades del sector de incendio",
                "description": ("Añada las actividades presentes en el sector. Cada actividad aporta carga "
                                "de fuego; en almacenamiento se considera además la altura."),
                "type": "activities",
            },
        ],
    }
