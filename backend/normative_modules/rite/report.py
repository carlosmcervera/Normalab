"""Informe no vinculante del módulo RITE (RD 1027/2007)."""
from core.models import utcnow_iso
from normative_modules.rite.norm_texts import FUNDAMENTOS
from normative_modules.shared_estancias import resumen_estancias

_TIPO = {"calefaccion": "Calefacción", "refrigeracion": "Refrigeración",
         "climatizacion": "Climatización", "acs": "ACS", "mixta": "Climatización + ACS"}


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    d = results.get("datos", {})
    est = resumen_estancias(results.get("estancias", []))
    sections = [
        {"id": "resumen", "title": "Resumen del cálculo", "type": "metricas",
         "items": results.get("resumen", []), "estado_global": results.get("estado_global")},
        {"id": "objeto", "title": "1. Objeto", "type": "text",
         "body": ("Estudio orientativo de la instalación térmica del edificio conforme al Reglamento de "
                  "Instalaciones Térmicas en los Edificios (RD 1027/2007) y sus Instrucciones Técnicas "
                  "(IT). Verifica el bienestar (IT 1.1), la eficiencia energética (IT 1.2) y las "
                  "exigencias de ventilación, recuperación de calor y aislamiento.")},
        {"id": "datos", "title": "2. Datos de la instalación", "type": "keyvalue",
         "rows": [
             {"k": "Expediente", "v": f"{project.get('code', '')} · {project.get('name', '')}"},
             {"k": "Tipo de instalación", "v": _TIPO.get(d.get("tipo"), d.get("tipo", "-"))},
             {"k": "Uso del edificio", "v": d.get("uso", "-")},
             {"k": "Zona climática", "v": d.get("zona", "-")},
             {"k": "Potencia térmica instalada", "v": f"{d.get('potencia_kw', 0):g} kW"},
             {"k": "Superficie útil (expediente)", "v": f"{d.get('sup_util', 0):g} m²"},
             {"k": "Ocupación (expediente)", "v": f"{d.get('ocupantes', 0)} personas"},
         ]},
        {"id": "estancias", "title": "3. Cuadro de superficies y ocupación (base de ventilación)", "type": "estancias_resumen",
         "data": est},
        {"id": "secciones", "title": "4. Verificación de exigencias", "type": "secciones_modulo",
         "items": results.get("secciones", [])},
        {"id": "observaciones", "title": "5. Observaciones", "type": "observaciones",
         "items": results.get("observaciones", [])},
        {"id": "fundamentos", "title": "6. Fundamentos normativos (extractos del RITE)", "type": "fundamentos",
         "items": FUNDAMENTOS},
    ]
    return {
        "module_code": "RITE",
        "title": "Informe no vinculante — Estudio RITE (instalación térmica)",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE. Las estimaciones de demanda y ventilación "
                       "son aproximadas; el diseño definitivo requiere el cálculo de cargas térmicas y la "
                       "justificación completa del RITE. No sustituye al proyecto de la instalación térmica."),
    }
