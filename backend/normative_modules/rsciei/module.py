from normative_modules.base import NormativeModule
from normative_modules.rsciei import engine, report, schema


class RscieiModule(NormativeModule):
    code = "RSCIEI"
    name = "Seguridad contra incendios en establecimientos industriales"
    short_name = "RSCIEI"
    description = ("Determinación del nivel de riesgo intrínseco (Qs), sectorización y "
                   "verificación de superficies máximas admisibles. Módulo operativo.")
    category = "Protección contra incendios"
    status = "operativo"
    version = "2.0.0"
    legal_reference = "RD 164/2025 (RSCIEI)"
    icon = "flame"
    accent = "orange"

    def get_schema(self) -> dict:
        return schema.get_schema()

    def compute(self, data: dict) -> dict:
        return engine.compute(data)

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        return report.build_report(project, study, data, results)
