"""Informe no vinculante del módulo REBT v2 (cuadro eléctrico)."""
from core.models import utcnow_iso
from normative_modules.rebt.norm_texts import FUNDAMENTOS
from normative_modules.shared_estancias import resumen_estancias

_TIPO = {"alumbrado": "Alumbrado", "tomas": "Tomas de corriente", "fuerza": "Fuerza",
         "motor": "Motor", "clima": "Climatización", "otros": "Otros"}


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    d = results.get("datos", {})
    est = resumen_estancias(results.get("estancias", []))
    sections = [
        {"id": "resumen", "title": "Resumen del cuadro", "type": "metricas",
         "items": results.get("resumen", []), "estado_global": results.get("estado_global")},
        {"id": "objeto", "title": "1. Objeto", "type": "text",
         "body": ("Estudio orientativo del cuadro eléctrico de baja tensión (esquema unifilar) conforme al "
                  "REBT (RD 842/2002) y sus ITC-BT. Incluye el cuadro de potencias, las protecciones de "
                  "cabecera (IGA y diferencial general), los diferenciales y magnetotérmicos de cada "
                  "circuito, los subcuadros y el dimensionado de todas las líneas.")},
        {"id": "datos", "title": "2. Datos generales", "type": "keyvalue",
         "rows": [
             {"k": "Expediente", "v": f"{project.get('code', '')} · {project.get('name', '')}"},
             {"k": "Tipo de suministro", "v": "Trifásico 400 V" if d.get("suministro") == "trifasica" else "Monofásico 230 V"},
             {"k": "Material del conductor", "v": "Aluminio" if d.get("material") == "Al" else "Cobre"},
             {"k": "Potencia total instalada", "v": f"{d.get('potencia_instalada', 0):,.0f} W"},
             {"k": "Potencia de cálculo (con simultaneidad)", "v": f"{d.get('potencia_demandada', 0):,.0f} W"},
             {"k": "Corriente de diseño general (Ib)", "v": f"{d.get('Ib', 0):.1f} A"},
             {"k": "IGA de cabecera", "v": f"{d.get('iga', 0)} A"},
             {"k": "Nº total de líneas", "v": f"{d.get('num_lineas', 0)}"},
         ]},
        {"id": "cuadro_potencias", "title": "3. Cuadro de potencias", "type": "rebt_potencias",
         "items": results.get("cuadro_potencias", []),
         "total_instalada": d.get("potencia_instalada", 0), "total_calculo": d.get("potencia_demandada", 0)},
        {"id": "esquema", "title": "4. Esquema unifilar", "type": "rebt_esquema", "arbol": results.get("arbol")},
        {"id": "lineas", "title": "5. Dimensionado y comprobación de líneas", "type": "rebt_lineas",
         "items": results.get("lineas", [])},
        {"id": "cortocircuito", "title": "6. Comprobación frente a cortocircuitos (ITC-BT-22)", "type": "rebt_cortocircuito",
         "items": [l for l in results.get("lineas", []) if l.get("cortocircuito")]},
        {"id": "estancias", "title": "7. Cuadro de superficies (ubicación)", "type": "estancias_resumen", "data": est},
        {"id": "observaciones", "title": "8. Observaciones", "type": "observaciones",
         "items": results.get("observaciones", [])},
        {"id": "fundamentos", "title": "9. Fundamentos normativos (extractos del REBT)", "type": "fundamentos",
         "items": FUNDAMENTOS},
    ]
    return {
        "module_code": "REBT",
        "title": "Informe no vinculante — Cuadro eléctrico REBT (esquema unifilar)",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE. El dimensionado definitivo debe verificar el "
                       "método de instalación, agrupamientos, temperatura, coeficientes de la ITC-BT-19, la "
                       "selectividad y coordinación de protecciones, y las intensidades de cortocircuito. No "
                       "sustituye al proyecto eléctrico."),
    }
