"""Informe no vinculante del módulo REBT (RD 842/2002)."""
from core.models import utcnow_iso
from normative_modules.rebt.norm_texts import FUNDAMENTOS
from normative_modules.shared_estancias import resumen_estancias


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    d = results.get("datos", {})
    est = resumen_estancias(results.get("estancias", []))
    sections = [
        {"id": "resumen", "title": "Resumen del cálculo", "type": "metricas",
         "items": results.get("resumen", []), "estado_global": results.get("estado_global")},
        {"id": "objeto", "title": "1. Objeto", "type": "text",
         "body": ("Estudio orientativo del dimensionado de la línea eléctrica de baja tensión conforme "
                  "al Reglamento Electrotécnico para Baja Tensión (RD 842/2002) y sus Instrucciones "
                  "Técnicas Complementarias (ITC-BT). Determina la sección del conductor, las "
                  "protecciones y la puesta a tierra.")},
        {"id": "datos", "title": "2. Datos de la instalación", "type": "keyvalue",
         "rows": [
             {"k": "Expediente", "v": f"{project.get('code', '')} · {project.get('name', '')}"},
             {"k": "Tipo de suministro", "v": "Trifásico 400 V" if d.get("suministro") == "trifasica" else "Monofásico 230 V"},
             {"k": "Potencia prevista", "v": f"{d.get('potencia', 0):,.0f} W"},
             {"k": "Factor de potencia (cos φ)", "v": f"{d.get('cosphi', 0.9)}"},
             {"k": "Longitud de la línea", "v": f"{d.get('longitud', 0):g} m"},
             {"k": "Material del conductor", "v": "Aluminio" if d.get("material") == "Al" else "Cobre"},
             {"k": "Caída de tensión máx. admisible", "v": f"{d.get('caida_max_pct', 3):g} %"},
         ]},
        {"id": "estancias", "title": "3. Cuadro de superficies (ubicación de circuitos)", "type": "estancias_resumen",
         "data": est},
        {"id": "secciones", "title": "4. Verificación y dimensionado", "type": "secciones_modulo",
         "items": results.get("secciones", [])},
        {"id": "observaciones", "title": "5. Observaciones", "type": "observaciones",
         "items": results.get("observaciones", [])},
        {"id": "fundamentos", "title": "6. Fundamentos normativos (extractos del REBT)", "type": "fundamentos",
         "items": FUNDAMENTOS},
    ]
    return {
        "module_code": "REBT",
        "title": "Informe no vinculante — Estudio REBT (baja tensión)",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE. El dimensionado definitivo debe verificar el "
                       "método de instalación, agrupamientos, temperatura y coeficientes de la ITC-BT-19, "
                       "así como la coordinación de protecciones. No sustituye al proyecto eléctrico."),
    }
