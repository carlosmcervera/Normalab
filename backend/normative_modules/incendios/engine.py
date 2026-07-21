"""Motor del módulo unificado «Incendios» (sector-céntrico).

Un estudio tiene un cuadro único de estancias (dependencias) con superficie útil
y construida, y una lista de sectores de incendio. Cada estancia se asigna a un
sector y aporta carga de fuego (salvo que sea local de riesgo especial). Cada
sector es industrial (RSCIEI) o CTE; ambos calculan la carga de fuego (Qs) y los
sectores CTE se evalúan además con el CTE DB-SI. Todo el cálculo se delega en el
motor RSCIEI, que ya soporta LRE y sectores CTE.

Compatibilidad: si los datos traen `ambitos` (modelo antiguo por ámbitos), se
mantiene el enrutado anterior por ámbito.
"""
from normative_modules.cte_dbsi import engine as dbsi_engine
from normative_modules.rsciei import engine as rsciei_engine


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _to_dbsi_input(a: dict) -> dict:
    deps = a.get("dependencias") or []
    if deps and ("sup_construida" in deps[0] or "sup_util" in deps[0]):
        mapped = [{"id": d.get("id"), "nombre": d.get("nombre"),
                   "superficie": _num(d.get("sup_util")) or _num(d.get("sup_construida")),
                   "densidad": d.get("densidad"), "sin_ocupacion": d.get("sin_ocupacion"),
                   "uso_ocupacion": d.get("uso_ocupacion")} for d in deps]
        sup = _num(a.get("superficie_construida")) or sum(_num(d.get("sup_construida")) for d in deps)
        return {**a, "superficie_construida": sup, "dependencias": mapped}
    return a


def _compute_legacy_ambitos(data: dict) -> dict:
    """Modelo antiguo por ámbitos (se conserva por compatibilidad)."""
    ambitos = data.get("ambitos") or []
    sectores = data.get("sectores") or []
    deps = data.get("dependencias") or []
    if data.get("sectores") or data.get("dependencias"):
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
        ambito_dicts = [by[a.get("id")] for a in ambitos]
    else:
        ambito_dicts = ambitos

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
    estado_global = "no_cumple" if "no_cumple" in estados else ("observaciones" if "observaciones" in estados else "cumple")
    return {"ambitos": resultados, "estado_global": estado_global}


def compute(data: dict) -> dict:
    if data.get("ambitos"):
        return _compute_legacy_ambitos(data)
    return rsciei_engine.compute(data)
