"""Non-binding report template for the RSCIEI module."""
from core.models import utcnow_iso


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    calc = results["calculo"]
    nri = results["nivel_riesgo"]
    sector = results["sectorizacion"]

    sections = [
        {
            "id": "objeto",
            "title": "1. Objeto del estudio",
            "type": "text",
            "body": ("El presente estudio tiene por objeto la determinación del nivel de riesgo "
                     "intrínseco y la verificación de la superficie máxima admisible del sector de "
                     "incendio conforme al Reglamento de seguridad contra incendios en los "
                     "establecimientos industriales (RSCIEI, RD 2267/2004)."),
        },
        {
            "id": "datos",
            "title": "2. Datos del establecimiento",
            "type": "keyvalue",
            "rows": [
                {"k": "Expediente", "v": f"{project.get('code','')} · {project.get('name','')}"},
                {"k": "Actividad", "v": data.get("actividad", "-")},
                {"k": "Configuración", "v": sector.get("config_label", "-")},
                {"k": "Superficie del sector (A)", "v": f"{calc['A']:.0f} m²"},
                {"k": "Coef. de activación (Ra)", "v": f"{calc['ra']:.2f}"},
            ],
        },
        {
            "id": "calculo",
            "title": "3. Cálculo de la densidad de carga de fuego (Qs)",
            "type": "zonas",
            "zonas": calc["zonas"],
            "resumen": {
                "numerador": calc["numerador"],
                "A": calc["A"],
                "ra": calc["ra"],
                "qs_mj": calc["qs_mj"],
                "qs_mcal": calc["qs_mcal"],
            },
        },
        {
            "id": "nri",
            "title": "4. Nivel de riesgo intrínseco",
            "type": "nri",
            "nivel": nri["nivel"],
            "categoria": nri["categoria"],
            "qs_mj": nri["qs_mj"],
            "qs_mcal": nri["qs_mcal"],
        },
        {
            "id": "sectorizacion",
            "title": "5. Sectorización — superficie máxima admisible",
            "type": "text",
            "body": sector.get("mensaje", "-"),
        },
        {
            "id": "observaciones",
            "title": "6. Observaciones",
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
