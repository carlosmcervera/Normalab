from normative_modules.cte_dbsi.catalog import OCCUPANCY_DENSITIES, USOS


def get_schema() -> dict:
    return {
        "occupancy_densities": OCCUPANCY_DENSITIES,
        "uses": USOS,
        "steps": [
            {
                "id": "edificio",
                "title": "Datos del edificio",
                "description": "Uso previsto, superficie y condiciones generales del edificio o zona (CTE DB-SI, SI 1 a SI 6).",
                "fields": [
                    {"name": "uso", "label": "Uso previsto principal", "type": "select", "required": True,
                     "options": [{"value": u, "label": u} for u in USOS]},
                    {"name": "superficie_construida", "label": "Superficie construida (m²)", "type": "number", "required": True, "min": 1, "step": 1},
                    {"name": "num_plantas", "label": "Nº de plantas", "type": "number", "min": 1, "step": 1, "default": 1,
                     "help": "La dotación de SI 4 se evalúa por planta."},
                    {"name": "altura_evacuacion", "label": "Altura de evacuación (m)", "type": "number", "min": 0, "step": 0.5, "default": 0,
                     "help": "Máxima altura de evacuación (para SI 3, SI 5 y SI 6)."},
                    {"name": "sentido_evacuacion", "label": "Sentido de evacuación", "type": "select",
                     "options": [{"value": "descendente", "label": "Descendente"}, {"value": "ascendente", "label": "Ascendente"}]},
                    {"name": "num_salidas", "label": "Nº de salidas de planta proyectadas", "type": "number", "min": 1, "step": 1, "default": 2},
                    {"name": "ancho_salidas_proyectado", "label": "Ancho total de salidas proyectado (m)", "type": "number", "min": 0, "step": 0.05,
                     "help": "Suma de anchos de las puertas/salidas (SI 3, A ≥ P/200)."},
                    {"name": "recorrido_max_real", "label": "Recorrido de evacuación real máximo (m)", "type": "number", "min": 0, "step": 0.5},
                    {"name": "distancia_colindantes", "label": "Separación a edificios/linderos colindantes (m)", "type": "number", "min": 0, "step": 0.5,
                     "help": "Para SI 2 (propagación exterior). Déjelo vacío si no aplica."},
                    {"name": "angulo_fachadas", "label": "Ángulo entre planos de fachada (°)", "type": "number", "min": 0, "max": 180, "step": 5,
                     "help": "SI 2 · separación mínima entre huecos según el ángulo (0°=3,00 m … 180°=0,50 m). Déjelo vacío si no aplica."},
                    {"name": "distancia_huecos", "label": "Distancia entre huecos proyectada (m)", "type": "number", "min": 0, "step": 0.05,
                     "help": "Distancia real entre huecos de sectores/edificios distintos (proyección horizontal)."},
                    {"name": "huecos_ei60", "label": "Los huecos enfrentados son EI 60", "type": "boolean",
                     "help": "Si los huecos tienen EI 60 no se exige separación mínima (SI 2)."},
                    {"name": "edificio_colindante", "label": "Huecos hacia edificio colindante distinto", "type": "boolean",
                     "help": "Cada fachada cumple el 50 % de la distancia (medida a la bisectriz)."},
                    {"name": "local_riesgo_especial", "label": "Local/zona de riesgo especial", "type": "select",
                     "options": [{"value": "ninguno", "label": "Ninguno"}, {"value": "bajo", "label": "Riesgo bajo"},
                                 {"value": "medio", "label": "Riesgo medio"}, {"value": "alto", "label": "Riesgo alto"}]},
                    {"name": "bajo_rasante", "label": "Zona bajo rasante (sótano)", "type": "boolean", "help": "Afecta a SI 1 y SI 6."},
                    {"name": "vial_aproximacion_ok", "label": "El vial de aproximación cumple SI 5", "type": "boolean"},
                ],
            },
            {"id": "ocupacion", "title": "Ocupación", "type": "dbsi_ocupacion",
             "description": "Introduzca las zonas del edificio y su densidad de ocupación (CTE DB-SI, Tabla 2.1)."},
        ],
    }
