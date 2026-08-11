"""Schema del asistente «REBT · Comprobación de una línea»."""
from normative_modules.rebt.catalog import SUMINISTROS, MATERIALES, METODOS_INSTALACION

_DISPOSICIONES = [
    {"value": "haz", "label": "En haz / bajo tubo o canaleta (empotrado o superficie)"},
    {"value": "capa_pared", "label": "Capa única sobre pared/suelo o bandeja sin perforar"},
    {"value": "capa_perf", "label": "Capa única sobre bandeja perforada"},
    {"value": "capa_esc", "label": "Capa única sobre bandeja de escalera/soportes"},
]
_AISLAMIENTOS = [{"value": "PVC", "label": "PVC (termoplástico)"}, {"value": "XLPE", "label": "XLPE/EPR (termoestable)"}]
_CURVAS = [{"value": "B", "label": "Curva B"}, {"value": "C", "label": "Curva C"}, {"value": "D", "label": "Curva D"}]
_USOS = [{"value": "otros", "label": "Otros usos (fuerza/tomas)"}, {"value": "alumbrado", "label": "Alumbrado"}]


def get_schema() -> dict:
    return {
        "steps": [
            {"id": "linea", "title": "Datos de la línea",
             "description": "Introduce la potencia, la longitud y cómo está instalada. Indica cuántos circuitos comparten la misma canalización: el agrupamiento reduce la intensidad admisible (Iz) según la Tabla B.52.17 de la UNE-HD 60364-5-52.",
             "fields": [
                 {"name": "potencia", "label": "Potencia (W)", "type": "number", "min": 0, "required": True},
                 {"name": "longitud", "label": "Longitud (m)", "type": "number", "min": 0, "required": True},
                 {"name": "suministro", "label": "Suministro", "type": "select", "options": SUMINISTROS, "default": "monofasica"},
                 {"name": "cosphi", "label": "Factor de potencia (cos φ)", "type": "number", "min": 0, "max": 1, "default": 0.9},
                 {"name": "tipo_uso", "label": "Uso del circuito", "type": "select", "options": _USOS, "default": "otros"},
                 {"name": "material", "label": "Material del conductor", "type": "select", "options": MATERIALES, "default": "Cu"},
                 {"name": "aislamiento", "label": "Aislamiento", "type": "select", "options": _AISLAMIENTOS, "default": "PVC"},
                 {"name": "metodo_instalacion", "label": "Método de instalación (ITC-BT-19)", "type": "select",
                  "options": METODOS_INSTALACION, "default": "b1", "full": True},
                 {"name": "disposicion", "label": "Disposición para el agrupamiento", "type": "select",
                  "options": _DISPOSICIONES, "default": "haz", "full": True},
                 {"name": "n_circuitos", "label": "Nº de circuitos en la misma canalización (incluida esta)", "type": "number", "min": 1, "default": 1},
                 {"name": "n_conductores", "label": "Conductores por fase (paralelo)", "type": "number", "min": 1, "default": 1},
                 {"name": "caida_max", "label": "Caída de tensión máx. (%)", "type": "number", "min": 0.1},
                 {"name": "curva", "label": "Curva del magnetotérmico", "type": "select", "options": _CURVAS, "default": "C"},
                 {"name": "icc_origen_a", "label": "Icc presunta en origen (A)", "type": "number", "min": 0, "default": 6000},
                 {"name": "poder_corte_ka", "label": "Poder de corte (kA)", "type": "number", "min": 0, "default": 6},
                 {"name": "seccion_manual", "label": "Forzar sección (mm², opcional)", "type": "number", "min": 0},
             ]},
        ],
    }
