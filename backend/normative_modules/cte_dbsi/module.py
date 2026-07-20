from normative_modules.base import NormativeModule
from normative_modules.cte_dbsi import engine, report, schema


class CteDbsiModule(NormativeModule):
    code = "CTE"
    name = "CTE DB-SI · Seguridad en caso de incendio"
    short_name = "CTE DB-SI"
    description = ("Compartimentación (SI 1), evacuación de ocupantes (SI 3), instalaciones de "
                   "protección (SI 4) y resistencia al fuego de la estructura (SI 6). Módulo operativo.")
    category = "Edificación"
    status = "operativo"
    version = "1.0.0"
    legal_reference = "CTE DB-SI (RD 314/2006)"
    icon = "building-2"
    accent = "blue"

    def get_schema(self) -> dict:
        return schema.get_schema()

    def compute(self, data: dict) -> dict:
        return engine.compute(data)

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        return report.build_report(project, study, data, results)
