"""Non-binding report template for the RSCIEI module (RD 164/2025, multi-sector)."""
from core.models import utcnow_iso


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    est = results.get("establecimiento", {})
    sections = [
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
