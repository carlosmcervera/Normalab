from normative_modules.base import NormativeModule
from normative_modules.rebt_linea import engine, report, schema


class RebtLineaModule(NormativeModule):
    code = "REBT_LINEA"
    name = "REBT · Comprobación de una línea"
    short_name = "Línea BT"
    description = ("Comprueba el cumplimiento de una única línea de baja tensión: intensidad de diseño, "
                   "intensidad admisible con factor de agrupamiento por circuitos en la misma canalización "
                   "(UNE-HD 60364-5-52, Tabla B.52.17), caída de tensión y cortocircuito (ITC-BT-22).")
    category = "Instalaciones"
    status = "operativo"
    version = "1.0.0"
    legal_reference = "RD 842/2002 (REBT), ITC-BT-19/22; UNE-HD 60364-5-52"
    icon = "cable"
    accent = "amber"

    def get_schema(self) -> dict:
        return schema.get_schema()

    def compute(self, data: dict) -> dict:
        return engine.compute(data)

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        return report.build_report(project, study, data, results)
