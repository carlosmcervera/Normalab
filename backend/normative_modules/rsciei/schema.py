"""Wizard schema for the RSCIEI module (RD 164/2025, multi-sector flow).

Flujo: 1) Establecimiento → 2) Cuadro de superficies + sectores → 3) Ocupación
(CTE) → 4) Carga de fuego → 5) Resultados. Los pasos 2-4 se renderizan con
componentes personalizados en el frontend; el schema aporta los catálogos.
"""
from normative_modules.rsciei.catalog import (
    ACTIVITY_CATALOG, ACTIVITY_TYPES, CI_TABLE, CONFIG_TYPES,
    OCCUPANCY_DENSITIES, RA_TABLE,
)


def get_schema() -> dict:
    return {
        "config_types": CONFIG_TYPES,
        "ci_table": CI_TABLE,
        "ra_table": RA_TABLE,
        "activity_catalog": ACTIVITY_CATALOG,
        "activity_types": ACTIVITY_TYPES,
        "occupancy_densities": OCCUPANCY_DENSITIES,
        "steps": [
            {
                "id": "establecimiento",
                "title": "Establecimiento",
                "description": "Identificación de la actividad y configuración general del establecimiento (Anexo I).",
                "fields": [
                    {"name": "actividad", "label": "Actividad / denominación del establecimiento",
                     "type": "activity_combobox", "required": True, "target": "establecimiento",
                     "placeholder": "Selecciona o escribe una actividad"},
                    {"name": "config", "label": "Tipo de configuración (Anexo I)",
                     "type": "config_selector", "required": True, "target": "establecimiento"},
                ],
            },
            {"id": "superficies", "title": "Superficies y sectores", "type": "superficies",
             "description": "Introduzca el cuadro de superficies (útil y construida) de cada dependencia y agrúpelas por sectores de incendio."},
            {"id": "ocupacion", "title": "Ocupación (CTE)", "type": "ocupacion",
             "description": "Asigne la densidad de ocupación (m²/persona) a cada dependencia según el CTE para obtener la ocupación."},
            {"id": "carga_fuego", "title": "Carga de fuego", "type": "carga_fuego",
             "description": "Defina para cada dependencia la carga de fuego (producción o almacenamiento) y los parámetros de cada sector."},
        ],
    }
