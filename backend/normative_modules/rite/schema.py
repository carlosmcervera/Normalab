"""Schema del asistente RITE."""
from normative_modules.rite.catalog import (
    TIPOS_INSTALACION, USOS_EDIFICIO, ZONAS_CLIMATICAS, TIPOS_GENERADOR, IDA_OPTS,
)


def get_schema() -> dict:
    return {
        "steps": [
            {"id": "superficies", "type": "estancias_compartidas",
             "title": "Cuadro de superficies y ocupación",
             "description": "Inventario compartido del expediente. La superficie y la ocupación se usan para estimar la demanda térmica y el caudal de ventilación (renovaciones)."},
            {"id": "datos", "title": "Datos de la instalación térmica",
             "description": "Introduce los datos de la instalación (RITE IT 1.1 y IT 1.2).",
             "fields": [
                 {"name": "tipo_instalacion", "label": "Tipo de instalación", "type": "select", "required": True,
                  "options": TIPOS_INSTALACION, "default": "climatizacion"},
                 {"name": "uso_edificio", "label": "Uso del edificio", "type": "select", "options": USOS_EDIFICIO, "default": "oficinas"},
                 {"name": "zona_climatica", "label": "Zona climática", "type": "select", "options": ZONAS_CLIMATICAS, "default": "C"},
                 {"name": "potencia_termica_kw", "label": "Potencia térmica instalada (kW)", "type": "number", "min": 0,
                  "help": "Potencia nominal del/los generador(es)."},
                 {"name": "tipo_generador", "label": "Tipo de generador", "type": "select",
                  "options": [{"value": g["value"], "label": g["label"]} for g in TIPOS_GENERADOR], "default": "caldera_condensacion"},
                 {"name": "rendimiento_pct", "label": "Rendimiento del generador (%)", "type": "number", "min": 0, "default": 92},
                 {"name": "categoria_ida", "label": "Calidad del aire interior (IDA)", "type": "select", "options": IDA_OPTS, "default": "IDA2"},
                 {"name": "caudal_expulsado_m3s", "label": "Caudal de aire expulsado (m³/s)", "type": "number", "min": 0, "default": 0,
                  "help": "Para la exigencia de recuperación de calor (IT 1.2.4.5.2)."},
                 {"name": "consumo_acs_persona", "label": "Consumo de ACS (l/persona·día)", "type": "number", "min": 0,
                  "help": "Déjalo vacío para usar el valor orientativo según el uso."},
                 {"name": "ocupantes_override", "label": "Ocupación (override manual)", "type": "number", "min": 0,
                  "help": "Déjalo vacío para usar la ocupación del cuadro compartido del expediente."},
             ]},
        ],
    }
