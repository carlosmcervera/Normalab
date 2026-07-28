"""Schema del asistente REBT v2 (cuadro eléctrico con subcuadros)."""
from normative_modules.rebt.catalog import SUMINISTROS, MATERIALES, TIPOS_INSTALACION


def get_schema() -> dict:
    return {
        "steps": [
            {"id": "superficies", "type": "estancias_compartidas",
             "title": "Cuadro de superficies y ocupación",
             "description": "Inventario compartido del expediente. Sirve para ubicar los circuitos por estancia."},
            {"id": "generales", "title": "Datos generales del cuadro",
             "description": "Condiciones de la instalación (ITC-BT-19).",
             "fields": [
                 {"name": "suministro", "label": "Tipo de suministro", "type": "select", "required": True,
                  "options": SUMINISTROS, "default": "trifasica"},
                 {"name": "material", "label": "Material del conductor", "type": "select", "options": MATERIALES, "default": "Cu"},
                 {"name": "tipo_instalacion", "label": "Tipo de instalación / local", "type": "select",
                  "options": TIPOS_INSTALACION, "default": "otro"},
                 {"name": "caida_max_di", "label": "Caída máx. derivación individual (%)", "type": "number", "min": 0.1, "default": 1.5},
                 {"name": "caida_max_circuito", "label": "Caída máx. por circuito (%)", "type": "number", "min": 0.1, "default": 3},
                 {"name": "caida_max_total_alumbrado", "label": "Caída máx. total alumbrado (%)", "type": "number", "min": 0.1, "default": 4.5},
                 {"name": "caida_max_total_otros", "label": "Caída máx. total otros usos (%)", "type": "number", "min": 0.1, "default": 6.5},
             ]},
            {"id": "cuadro", "type": "rebt_cuadro", "title": "Cargas y esquema del cuadro",
             "description": "Define las cargas, agrúpalas por diferenciales y crea subcuadros. Se calcula el cuadro de potencias y todas las líneas."},
        ],
    }
