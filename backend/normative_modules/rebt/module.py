from normative_modules.base import NormativeModule
from normative_modules.rebt import engine, report, schema


class RebtModule(NormativeModule):
    code = "REBT"
    name = "Reglamento Electrotécnico para Baja Tensión"
    short_name = "REBT"
    description = ("Dimensionado de líneas de baja tensión: corriente de diseño, sección por caída de "
                   "tensión y por calentamiento (ITC-BT-19), protecciones, puesta a tierra y grado de "
                   "electrificación. Módulo operativo.")
    category = "Instalaciones"
    status = "operativo"
    version = "1.0.0"
    legal_reference = "RD 842/2002 (REBT) e ITC-BT"
    icon = "zap"
    accent = "amber"

    def get_schema(self) -> dict:
        return schema.get_schema()

    def compute(self, data: dict) -> dict:
        return engine.compute(data)

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        return report.build_report(project, study, data, results)
