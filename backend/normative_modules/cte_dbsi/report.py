"""Informe no vinculante del módulo CTE DB-SI (secciones SI 1 a SI 6)."""
from core.models import utcnow_iso


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    sections = [
        {"id": "objeto", "title": "1. Objeto del estudio", "type": "text",
         "body": ("Estudio orientativo de las condiciones de seguridad en caso de incendio conforme al "
                  "Documento Básico DB-SI del CTE (SI 1 a SI 6): compartimentación, propagación exterior, "
                  "evacuación de ocupantes, instalaciones de protección, intervención de bomberos y "
                  "resistencia al fuego de la estructura.")},
        {"id": "datos", "title": "2. Datos del edificio", "type": "keyvalue", "rows": [
            {"k": "Expediente", "v": f"{project.get('code','')} · {project.get('name','')}"},
            {"k": "Uso previsto", "v": results["uso"]},
            {"k": "Superficie construida", "v": f"{results['superficie']:.0f} m²"},
            {"k": "Altura de evacuación", "v": f"{results['altura']:.1f} m"},
            {"k": "Ocupación total", "v": f"{results['ocupacion']['total']} personas"},
        ]},
        {"id": "ocupacion", "title": "3. Ocupación (DB-SI, Tabla 2.1)", "type": "ocupacion", "data": results["ocupacion"]},
    ]
    n = 4
    for s in results.get("secciones", []):
        if s.get("filas"):
            sections.append({"id": f"{s['id']}_kv", "title": f"{n}. {s['titulo']}", "type": "keyvalue", "rows": s["filas"]})
            n += 1
        if s.get("instalaciones"):
            sections.append({"id": f"{s['id']}_inst", "title": f"{n}. {s['titulo']}", "type": "instalaciones", "items": s["instalaciones"]})
            n += 1
    sections.append({"id": "tablas", "title": f"{n}. Tablas de referencia (DB-SI)", "type": "tablas", "items": results.get("tablas", [])})
    sections.append({"id": "observaciones", "title": f"{n+1}. Observaciones", "type": "observaciones", "items": results.get("observaciones", [])})

    return {
        "module_code": "CTE",
        "title": "Informe no vinculante — Estudio CTE DB-SI",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE. No sustituye al proyecto técnico ni a la "
                       "documentación oficial exigible. Los resultados dependen de los datos introducidos."),
    }
