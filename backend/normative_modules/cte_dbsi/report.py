"""Informe no vinculante del módulo CTE DB-SI."""
from core.models import utcnow_iso


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    si1, si3, si4, si6 = results["si1"], results["si3"], results["si4"], results["si6"]
    sections = [
        {"id": "objeto", "title": "1. Objeto del estudio", "type": "text",
         "body": ("Estudio orientativo de las condiciones de seguridad en caso de incendio conforme al "
                  "Documento Básico DB-SI del Código Técnico de la Edificación (RD 314/2006): "
                  "compartimentación (SI 1), evacuación (SI 3), instalaciones (SI 4) y resistencia al "
                  "fuego de la estructura (SI 6).")},
        {"id": "datos", "title": "2. Datos del edificio", "type": "keyvalue", "rows": [
            {"k": "Expediente", "v": f"{project.get('code','')} · {project.get('name','')}"},
            {"k": "Uso previsto", "v": results["uso"]},
            {"k": "Superficie construida", "v": f"{results['superficie']:.0f} m²"},
            {"k": "Altura de evacuación", "v": f"{results['altura']:.1f} m"},
            {"k": "Ocupación total", "v": f"{results['ocupacion']['total']} personas"},
        ]},
        {"id": "ocupacion", "title": "3. Ocupación (DB-SI, Tabla 2.1)", "type": "ocupacion", "data": results["ocupacion"]},
        {"id": "si1", "title": "4. SI 1 · Compartimentación en sectores", "type": "keyvalue", "rows": [
            {"k": "Superficie construida", "v": f"{si1['superficie']:.0f} m²"},
            {"k": "Máximo por sector", "v": ("Sin límite" if si1["max_sector"] is None else f"{si1['max_sector']:.0f} m²")},
            {"k": "Resultado", "v": ("Cumple" if si1["cumple"] else "Requiere sectorizar")},
            {"k": "Observación", "v": si1["mensaje"]},
        ]},
        {"id": "si3", "title": "5. SI 3 · Evacuación de ocupantes", "type": "keyvalue", "rows": [
            {"k": "Salidas requeridas / proyectadas", "v": f"{si3['salidas_requeridas']} / {si3['salidas_proyectadas']}"},
            {"k": "Recorrido máximo admisible", "v": f"{si3['recorrido_max_permitido']} m"},
            {"k": "Recorrido real", "v": (f"{si3['recorrido_real']:.1f} m" if si3["recorrido_real"] else "—")},
            {"k": "Ancho de salida (A ≥ P/200)", "v": f"{si3['ancho_calculado']:.2f} m (mín. {si3['ancho_minimo']:.2f} m)"},
        ]},
        {"id": "si6", "title": "6. SI 6 · Resistencia al fuego de la estructura", "type": "keyvalue", "rows": [
            {"k": "Estabilidad exigida", "v": si6["estabilidad"]},
            {"k": "Justificación", "v": si6["detalle"]},
        ]},
        {"id": "si4", "title": "7. SI 4 · Instalaciones de protección contra incendios",
         "type": "instalaciones", "items": si4["instalaciones"]},
        {"id": "tablas", "title": "8. Tablas de referencia (DB-SI)", "type": "tablas", "items": results.get("tablas", [])},
        {"id": "observaciones", "title": "9. Observaciones", "type": "observaciones", "items": results.get("observaciones", [])},
    ]
    return {
        "module_code": "CTE",
        "title": "Informe no vinculante — Estudio CTE DB-SI",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE. No sustituye al proyecto técnico ni a la "
                       "documentación oficial exigible. Los resultados dependen de los datos introducidos."),
    }
