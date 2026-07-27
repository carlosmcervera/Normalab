from normative_modules.base import NormativeModule
from normative_modules.rite import engine, report, schema


class RiteModule(NormativeModule):
    code = "RITE"
    name = "Reglamento de Instalaciones Térmicas en los Edificios"
    short_name = "RITE"
    description = ("Comprobación de instalaciones térmicas: bienestar (IT 1.1), eficiencia energética "
                   "(IT 1.2), ventilación y renovaciones, recuperación de calor, aislamiento de "
                   "tuberías y demanda de ACS. Módulo operativo.")
    category = "Instalaciones"
    status = "operativo"
    version = "1.0.0"
    legal_reference = "RD 1027/2007 (RITE) e IT"
    icon = "thermometer"
    accent = "rose"

    def get_schema(self) -> dict:
        return schema.get_schema()

    def compute(self, data: dict) -> dict:
        return engine.compute(data)

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        return report.build_report(project, study, data, results)
