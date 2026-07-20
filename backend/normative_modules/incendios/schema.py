"""Schema del módulo unificado «Incendios».

Expone los sub-esquemas de RSCIEI (establecimientos industriales) y CTE DB-SI
(edificación). El frontend organiza el estudio en «ámbitos», cada uno de tipo
industrial o edificación, y renderiza el sub-esquema correspondiente.
"""
from normative_modules.cte_dbsi import schema as dbsi_schema
from normative_modules.rsciei import schema as rsciei_schema


def get_schema() -> dict:
    return {
        "rsciei": rsciei_schema.get_schema(),
        "dbsi": dbsi_schema.get_schema(),
    }
