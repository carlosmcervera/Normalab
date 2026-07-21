"""Schema del módulo unificado «Incendios» (flujo sector-céntrico).

Flujo profesional (como el Excel KION):
  1) Cuadro de superficies: inventario de estancias/dependencias (útil + construida).
  2) Sectores de incendio: se crean los sectores, se asigna cada estancia a un
     sector, se marcan los locales de riesgo especial (LRE) y se define la carga
     de fuego por estancia. Cada sector es industrial (RSCIEI) o CTE (que también
     calcula la carga de fuego).
  3) Ocupación (CTE) y 4) Evacuación (RSCIEI, Tabla 2.3.1).
"""
from normative_modules.rsciei import schema as rsciei_schema
from normative_modules.cte_dbsi import schema as dbsi_schema


def get_schema() -> dict:
    rs = rsciei_schema.get_schema()
    db = dbsi_schema.get_schema()
    return {
        "config_types": rs["config_types"],
        "ci_table": rs["ci_table"],
        "ra_table": rs["ra_table"],
        "activity_catalog": rs["activity_catalog"],
        "activity_types": rs["activity_types"],
        "occupancy_densities": rs["occupancy_densities"],
        "dbsi_uses": db.get("uses", []),
        "steps": [
            {"id": "superficies", "type": "superficies_proyecto", "title": "Cuadro de superficies",
             "description": "Inventario de estancias/dependencias del proyecto con su superficie útil y construida."},
            {"id": "sectores", "type": "sectores_incendio", "title": "Sectores de incendio",
             "description": "Crea los sectores, asigna cada estancia a un sector, marca los locales de riesgo especial y define la carga de fuego. Los sectores CTE también calculan la carga de fuego."},
            {"id": "ocupacion", "type": "ocupacion", "title": "Ocupación (CTE)",
             "description": "Asigna la densidad de ocupación (m²/persona) a cada estancia según el CTE DB-SI (Tabla 2.1)."},
            {"id": "evacuacion", "type": "evacuacion", "title": "Evacuación",
             "description": "Recorridos reales de evacuación por sector (RSCIEI, Tabla 2.3.1)."},
        ],
    }
