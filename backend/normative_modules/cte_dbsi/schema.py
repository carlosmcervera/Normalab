from normative_modules.cte_dbsi.catalog import OCCUPANCY_DENSITIES, USOS


def get_schema() -> dict:
    return {
        "occupancy_densities": OCCUPANCY_DENSITIES,
        "uses": USOS,
        "steps": [
            {
                "id": "edificio",
                "title": "Datos del edificio",
                "description": "Uso previsto, superficie y condiciones generales del edificio o zona (CTE DB-SI).",
                "fields": [
                    {"name": "uso", "label": "Uso previsto principal", "type": "select", "required": True,
                     "options": [{"value": u, "label": u} for u in USOS]},
                    {"name": "superficie_construida", "label": "Superficie construida (m²)", "type": "number",
                     "required": True, "min": 1, "step": 1},
                    {"name": "altura_evacuacion", "label": "Altura de evacuación (m)", "type": "number",
                     "min": 0, "step": 0.5, "default": 0,
                     "help": "Altura de evacuación descendente del edificio (para SI 6 y columna seca)."},
                    {"name": "num_salidas", "label": "Nº de salidas de planta proyectadas", "type": "number",
                     "min": 1, "step": 1, "default": 2},
                    {"name": "recorrido_max_real", "label": "Recorrido de evacuación real máximo (m)", "type": "number",
                     "min": 0, "step": 0.5, "help": "Distancia máxima medida desde el origen de evacuación hasta la salida."},
                    {"name": "bajo_rasante", "label": "Zona bajo rasante (sótano)", "type": "boolean",
                     "help": "Afecta a la resistencia al fuego exigida a la estructura (SI 6)."},
                ],
            },
            {"id": "ocupacion", "title": "Ocupación", "type": "dbsi_ocupacion",
             "description": "Introduzca las zonas del edificio y su densidad de ocupación (CTE DB-SI, Tabla 2.1)."},
        ],
    }
