"""Motor del módulo unificado «Incendios».

Un estudio se compone de uno o varios «ámbitos». Cada ámbito es de tipo
`industrial` (evaluado con el motor RSCIEI, RD 164/2025) o `edificacion`
(evaluado con el motor CTE DB-SI). Permite proyectos mixtos.
"""
from normative_modules.cte_dbsi import engine as dbsi_engine
from normative_modules.rsciei import engine as rsciei_engine


def compute(data: dict) -> dict:
    ambitos = data.get("ambitos") or []
    if not ambitos:
        raise ValueError("Añada al menos un ámbito (establecimiento industrial o edificación).")

    resultados = []
    for a in ambitos:
        tipo = a.get("tipo")
        nombre = a.get("nombre") or "Ámbito"
        try:
            if tipo == "industrial":
                r = rsciei_engine.compute(a)
            elif tipo == "edificacion":
                r = dbsi_engine.compute(a)
            else:
                raise ValueError("tipo de ámbito desconocido.")
        except ValueError as e:
            raise ValueError(f"Ámbito «{nombre}»: {e}")
        resultados.append({"id": a.get("id"), "nombre": nombre, "tipo": tipo, "results": r})

    estados = [x["results"].get("estado_global") for x in resultados]
    if "no_cumple" in estados:
        estado_global = "no_cumple"
    elif "observaciones" in estados:
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    return {"ambitos": resultados, "estado_global": estado_global}
