"""Informe no vinculante del módulo «REBT · Comprobación de una línea»."""
from core.models import utcnow_iso

_OK = {True: "Cumple ✓", False: "No cumple ✗"}


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    ent = results.get("entradas", {}) or {}
    ag = results.get("agrupamiento", {}) or {}
    comp = results.get("comprobaciones", []) or []
    sections = [
        {"id": "resumen", "title": "Resultado de la comprobación", "type": "metricas",
         "items": results.get("resumen", []), "estado_global": results.get("estado_global")},
        {"id": "objeto", "title": "1. Objeto", "type": "text",
         "body": ("Comprobación orientativa del cumplimiento de una línea de baja tensión conforme al REBT "
                  "(RD 842/2002, ITC-BT-19 e ITC-BT-22) y a la UNE-HD 60364-5-52, incluyendo el factor de "
                  "reducción por agrupamiento de circuitos en la misma canalización.")},
        {"id": "entradas", "title": "2. Datos de la línea", "type": "keyvalue",
         "rows": [
             {"k": "Potencia", "v": f"{ent.get('potencia', '')} W"},
             {"k": "Longitud", "v": f"{ent.get('longitud', '')} m"},
             {"k": "Suministro", "v": f"{ent.get('suministro', '')} · {ent.get('tension', '')} V"},
             {"k": "cos φ", "v": ent.get("cosphi", "")},
             {"k": "Uso", "v": ent.get("uso", "")},
             {"k": "Conductor", "v": f"{ent.get('material', '')} / {ent.get('aislamiento', '')}"},
             {"k": "Método de instalación", "v": ent.get("metodo_label", "")},
         ]},
        {"id": "agrupamiento", "title": "3. Agrupamiento (UNE-HD 60364-5-52, Tabla B.52.17)", "type": "keyvalue",
         "rows": [
             {"k": "Disposición", "v": ag.get("disposicion_label", "")},
             {"k": "Nº de circuitos en la canalización", "v": ag.get("n_circuitos", "")},
             {"k": "Factor de reducción", "v": ag.get("factor", "")},
             {"k": "Iz base (sin agrupar)", "v": f"{ag.get('iz_base', '')} A"},
             {"k": "Iz corregida", "v": f"{ag.get('iz_corregida', '')} A"},
         ]},
        {"id": "comprobaciones", "title": "4. Comprobaciones normativas", "type": "keyvalue",
         "rows": [{"k": c.get("nombre", ""), "v": f"{_OK.get(bool(c.get('ok')))} — {c.get('detalle', '')}"} for c in comp]},
        {"id": "observaciones", "title": "5. Observaciones", "type": "observaciones",
         "items": results.get("observaciones", [])},
    ]
    return {
        "module_code": "REBT_LINEA",
        "title": "Informe no vinculante — Comprobación de una línea (REBT)",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE. Debe verificarse el método de instalación, los "
                       "agrupamientos, la temperatura, los coeficientes de la ITC-BT-19/UNE-HD 60364-5-52 y las "
                       "intensidades de cortocircuito reales. No sustituye al proyecto eléctrico."),
    }
