"""Schema del módulo unificado «Incendios» (flujo a nivel de PROYECTO).

Un estudio se organiza en «ámbitos» (establecimientos industriales RSCIEI y/o
zonas de edificación CTE DB-SI). Las SUPERFICIES son únicas de proyecto: un solo
cuadro de dependencias (útil y construida) agrupadas por sectores de incendio, y
cada sector se asigna a un ámbito. Los catálogos de RSCIEI/DB-SI se exponen a
nivel superior para los pasos compartidos (carga de fuego, ocupación, evacuación).
"""
from normative_modules.cte_dbsi import schema as dbsi_schema
from normative_modules.rsciei import schema as rsciei_schema


def get_schema() -> dict:
    rs = rsciei_schema.get_schema()
    db = dbsi_schema.get_schema()
    edificio_fields = [f for f in db["steps"][0]["fields"] if f["name"] != "superficie_construida"]
    return {
        "config_types": rs["config_types"],
        "ci_table": rs["ci_table"],
        "ra_table": rs["ra_table"],
        "activity_catalog": rs["activity_catalog"],
        "activity_types": rs["activity_types"],
        "occupancy_densities": rs["occupancy_densities"],
        "dbsi_uses": db.get("uses", []),
        # Campos de configuración por ámbito (sin superficie: la aporta el cuadro único).
        "industrial_config_fields": rs["steps"][0]["fields"],
        "edificacion_config_fields": edificio_fields,
        "steps": [
            {"id": "ambitos", "type": "ambitos", "title": "Ámbitos del proyecto",
             "description": "Define los ámbitos (establecimientos industriales RSCIEI y/o edificación CTE DB-SI) y la configuración de cada uno."},
            {"id": "superficies", "type": "superficies_proyecto", "title": "Cuadro de superficies",
             "description": "Cuadro único de superficies (útil y construida) de todas las dependencias del proyecto, agrupadas por sectores de incendio y asignadas a su ámbito."},
            {"id": "carga_fuego", "type": "carga_fuego", "title": "Carga de fuego",
             "description": "Defina la carga de fuego de las dependencias de los sectores industriales (RSCIEI)."},
            {"id": "ocupacion", "type": "ocupacion", "title": "Ocupación (CTE)",
             "description": "Asigne la densidad de ocupación (m²/persona) a cada dependencia según el CTE DB-SI (Tabla 2.1)."},
            {"id": "evacuacion", "type": "evacuacion", "title": "Evacuación",
             "description": "Recorridos reales de evacuación de los sectores industriales (RSCIEI, Tabla 2.3.1)."},
        ],
    }
