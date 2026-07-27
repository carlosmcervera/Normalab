"""Schema del asistente REBT."""
from normative_modules.rebt.catalog import SUMINISTROS, MATERIALES, TIPOS_INSTALACION


def get_schema() -> dict:
    return {
        "steps": [
            {"id": "superficies", "type": "estancias_compartidas",
             "title": "Cuadro de superficies y ocupación",
             "description": "Inventario compartido del expediente (editable desde cualquier módulo). Sirve para ubicar los circuitos por estancia."},
            {"id": "datos", "title": "Datos de la línea",
             "description": "Introduce los datos de la línea eléctrica a dimensionar (ITC-BT-19).",
             "fields": [
                 {"name": "suministro", "label": "Tipo de suministro", "type": "select", "required": True,
                  "options": SUMINISTROS, "default": "monofasica"},
                 {"name": "potencia", "label": "Potencia prevista (W)", "type": "number", "required": True, "min": 1,
                  "help": "Potencia de cálculo de la línea (W)."},
                 {"name": "cosphi", "label": "Factor de potencia (cos φ)", "type": "number", "min": 0, "default": 0.9},
                 {"name": "longitud", "label": "Longitud de la línea (m)", "type": "number", "required": True, "min": 0.1},
                 {"name": "material", "label": "Material del conductor", "type": "select", "options": MATERIALES, "default": "Cu"},
                 {"name": "caida_max_pct", "label": "Caída de tensión máx. admisible (%)", "type": "number", "min": 0.1, "default": 3,
                  "help": "3 % alumbrado / 5 % otros usos; 1–1,5 % derivación individual (ITC-BT-19)."},
                 {"name": "tipo_instalacion", "label": "Tipo de instalación / local", "type": "select",
                  "options": TIPOS_INSTALACION, "default": "otro", "full": True},
             ]},
        ],
    }
