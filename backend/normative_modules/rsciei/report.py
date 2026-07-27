"""Non-binding report template for the RSCIEI module (RD 164/2025, multi-sector)."""
from core.models import utcnow_iso
from normative_modules.rsciei.norm_texts import build_fundamentos


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    est = results.get("establecimiento", {})
    resumen_ej = []
    for s in results.get("sectores", []):
        resumen_ej.append({
            "nombre": s.get("nombre"),
            "ambito": "CTE" if s.get("ambito") == "cte" else "RSCIEI",
            "estado": s.get("estado"),
            "qs_mj": s["nivel_riesgo"]["qs_mj"],
            "nivel": s["nivel_riesgo"]["nivel"],
            "categoria": s["nivel_riesgo"]["categoria"],
            "lre": len(s.get("locales_riesgo_especial", [])),
            "escaleras": len(s.get("escaleras_protegidas", [])),
            "dbsi": [{"id": x["id"], "estado": x["estado"]} for x in ((s.get("dbsi") or {}).get("secciones") or [])],
        })
    sections = [
        {
            "id": "resumen_ejecutivo",
            "title": "Resumen ejecutivo",
            "type": "resumen_ejecutivo",
            "estado_global": results.get("estado_global"),
            "filas": resumen_ej,
            "depositos": results.get("depositos", []),
        },
        {
            "id": "objeto",
            "title": "1. Objeto del estudio",
            "type": "text",
            "body": ("El presente estudio tiene por objeto la determinación del nivel de riesgo "
                     "intrínseco, la verificación de la superficie máxima admisible de los sectores "
                     "de incendio y de los requisitos de protección conforme al Reglamento de "
                     "seguridad contra incendios en los establecimientos industriales (RSCIEI, "
                     "RD 164/2025), incorporando el cuadro de superficies y el cálculo de ocupación "
                     "(CTE) del establecimiento."),
        },
        {
            "id": "datos",
            "title": "2. Datos del establecimiento",
            "type": "keyvalue",
            "rows": [
                {"k": "Expediente", "v": f"{project.get('code','')} · {project.get('name','')}"},
                {"k": "Actividad", "v": est.get("actividad", "-")},
                {"k": "Configuración", "v": est.get("config", "-")},
                {"k": "Nº de sectores de incendio", "v": str(len(results.get("sectores", [])))},
                {"k": "Superficie total construida", "v": f"{results['superficies']['total_construida']:.0f} m²"},
                {"k": "Ocupación total", "v": f"{results['ocupacion']['total']} personas"},
            ],
        },
        {
            "id": "superficies",
            "title": "3. Cuadro de superficies",
            "type": "superficies",
            "data": results["superficies"],
        },
        {
            "id": "ocupacion",
            "title": "4. Ocupación (CTE DB-SI)",
            "type": "ocupacion",
            "data": results["ocupacion"],
        },
        {
            "id": "resumen",
            "title": "5. Resumen de sectores de incendio",
            "type": "resumen",
            "filas": results["resumen_sectores"],
        },
        {
            "id": "sectores",
            "title": "6. Cálculo y requisitos por sector (RSCIEI)",
            "type": "sectores",
            "items": results["sectores"],
        },
        {
            "id": "tablas",
            "title": "7. Tablas de referencia (Guía RSCIEI 2025)",
            "type": "tablas",
            "items": results.get("tablas", []),
        },
        {
            "id": "observaciones",
            "title": "8. Observaciones",
            "type": "observaciones",
            "items": results.get("observaciones", []),
        },
        {
            "id": "fundamentos",
            "title": "9. Fundamentos normativos (extractos de la norma)",
            "type": "fundamentos",
            "items": build_fundamentos(results),
        },
    ]

    return {
        "module_code": "RSCIEI",
        "title": "Informe no vinculante — Estudio RSCIEI",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Este informe tiene carácter ORIENTATIVO y NO VINCULANTE. No sustituye al "
                       "proyecto técnico ni a la documentación oficial exigible. Los resultados "
                       "dependen de los datos introducidos por el técnico redactor."),
    }
