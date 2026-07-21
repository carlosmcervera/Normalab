"""Informe del módulo unificado «Incendios» (agrega los sub-informes por ámbito)."""
from core.models import utcnow_iso
from normative_modules.cte_dbsi import report as dbsi_report
from normative_modules.rsciei import report as rsciei_report

LABEL = {
    "industrial": "Establecimiento industrial · RSCIEI (RD 164/2025)",
    "edificacion": "Edificación · CTE DB-SI",
}


def build_report(project: dict, study: dict, data: dict, results: dict) -> dict:
    if not data.get("ambitos"):
        # Flujo sector-céntrico: se delega en el informe RSCIEI (que ya incluye
        # cuadro de superficies, sectores, LRE y ámbitos CTE).
        rep = rsciei_report.build_report(project, study, data, results)
        rep["module_code"] = "INCENDIOS"
        rep["title"] = "Informe no vinculante — Estudio de Incendios"
        return rep

    ambitos_data = {a.get("id"): a for a in (data.get("ambitos") or [])}
    sections = [{
        "id": "objeto_general", "title": "1. Objeto del estudio", "type": "text",
        "body": ("Estudio integral de seguridad contra incendios del proyecto, que abarca tanto los "
                 "establecimientos industriales conforme al RSCIEI (RD 164/2025) como las zonas de "
                 "edificación de uso no industrial conforme al Documento Básico DB-SI del CTE. "
                 "Cada ámbito se evalúa con la reglamentación que le corresponde."),
    }]

    for a_res in results.get("ambitos", []):
        a = ambitos_data.get(a_res["id"], {})
        if a_res["tipo"] == "industrial":
            sub = rsciei_report.build_report(project, study, a, a_res["results"])
        else:
            sub = dbsi_report.build_report(project, study, a, a_res["results"])
        sections.append({"id": f"{a_res['id']}_hdr", "type": "ambito_header",
                         "title": a_res["nombre"], "tipo": LABEL.get(a_res["tipo"], a_res["tipo"])})
        for s in sub["sections"]:
            s = dict(s)
            s["id"] = f"{a_res['id']}_{s['id']}"
            sections.append(s)

    return {
        "module_code": "INCENDIOS",
        "title": "Informe no vinculante — Estudio de Incendios",
        "generated_at": utcnow_iso(),
        "estado_global": results.get("estado_global"),
        "sections": sections,
        "disclaimer": ("Informe ORIENTATIVO y NO VINCULANTE que integra RSCIEI y CTE DB-SI. No sustituye "
                       "al proyecto técnico ni a la documentación oficial exigible. Los resultados dependen "
                       "de los datos introducidos por el técnico redactor."),
    }
