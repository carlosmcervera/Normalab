from normative_modules.base import NormativeModule
from normative_modules.incendios import engine, report, schema


class IncendiosModule(NormativeModule):
    code = "INCENDIOS"
    name = "Incendios · RSCIEI + CTE DB-SI"
    short_name = "Incendios"
    description = ("Módulo integral de seguridad contra incendios. Evalúa establecimientos industriales "
                   "(RSCIEI, RD 164/2025) y edificación de uso no industrial (CTE DB-SI), admitiendo "
                   "proyectos mixtos con varios ámbitos.")
    category = "Protección contra incendios"
    status = "operativo"
    version = "1.0.0"
    legal_reference = "RD 164/2025 (RSCIEI) + CTE DB-SI (RD 314/2006)"
    icon = "flame"
    accent = "orange"

    def get_schema(self) -> dict:
        return schema.get_schema()

    def compute(self, data: dict) -> dict:
        return engine.compute(data)

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        return report.build_report(project, study, data, results)
