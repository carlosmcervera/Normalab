"""Motor del módulo unificado «Incendios».

Un estudio se compone de uno o varios «ámbitos». Cada ámbito es de tipo
`industrial` (evaluado con el motor RSCIEI, RD 164/2025) o `edificacion`
(evaluado con el motor CTE DB-SI). Permite proyectos mixtos.

Las superficies son ÚNICAS de proyecto: `data.sectores` (cada uno con
`ambito_id`) y `data.dependencias` (cada una con `sector_id`). El motor reparte
sectores y dependencias en su ámbito y enruta cada uno a su sub-motor. Se
mantiene compatibilidad con estudios antiguos que anidaban sectores/dependencias
dentro de cada ámbito.
"""
from normative_modules.cte_dbsi import engine as dbsi_engine
from normative_modules.rsciei import engine as rsciei_engine


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _split_by_ambito(data: dict) -> list:
    """Reparte sectores/dependencias de proyecto dentro de cada ámbito."""
    ambitos = data.get("ambitos") or []
    sectores = data.get("sectores") or []
    deps = data.get("dependencias") or []
    by = {a.get("id"): {**a, "sectores": [], "dependencias": []} for a in ambitos}
    sec_amb = {}
    for s in sectores:
        aid = s.get("ambito_id")
        if aid in by:
            by[aid]["sectores"].append(s)
            sec_amb[s.get("id")] = aid
    for d in deps:
        aid = sec_amb.get(d.get("sector_id"))
        if aid in by:
            by[aid]["dependencias"].append(d)
    return [by[a.get("id")] for a in ambitos]


def _to_dbsi_input(a: dict) -> dict:
    """Adapta un ámbito de edificación al formato esperado por el motor DB-SI.

    Cuando las dependencias provienen del cuadro único de proyecto (llevan
    `sup_util`/`sup_construida`), se mapean a `superficie` de ocupación y la
    superficie construida del edificio se deriva sumando las dependencias.
    """
    deps = a.get("dependencias") or []
    if deps and ("sup_construida" in deps[0] or "sup_util" in deps[0]):
        mapped = [{"id": d.get("id"), "nombre": d.get("nombre"),
                   "superficie": _num(d.get("sup_util")) or _num(d.get("sup_construida")),
                   "densidad": d.get("densidad"), "sin_ocupacion": d.get("sin_ocupacion"),
                   "uso_ocupacion": d.get("uso_ocupacion")} for d in deps]
        sup = _num(a.get("superficie_construida")) or sum(_num(d.get("sup_construida")) for d in deps)
        return {**a, "superficie_construida": sup, "dependencias": mapped}
    return a


def compute(data: dict) -> dict:
    ambitos = data.get("ambitos") or []
    if not ambitos:
        raise ValueError("Añada al menos un ámbito (establecimiento industrial o edificación).")

    project_level = bool(data.get("sectores") or data.get("dependencias"))
    ambito_dicts = _split_by_ambito(data) if project_level else ambitos

    resultados = []
    for a in ambito_dicts:
        tipo = a.get("tipo")
        nombre = a.get("nombre") or "Ámbito"
        try:
            if tipo == "industrial":
                r = rsciei_engine.compute(a)
            elif tipo == "edificacion":
                r = dbsi_engine.compute(_to_dbsi_input(a))
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
