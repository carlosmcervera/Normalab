"""Utilidades para el cuadro de superficies + ocupación compartido del expediente.

Las estancias son la fuente única a nivel de expediente (project.estancias) y las
consumen los módulos RITE y REBT (y opcionalmente INCENDIOS por importación).
"""
import math


def dep_ocupacion(d: dict):
    """Ocupación de una estancia: manual (nº personas) o techo(sup útil / densidad)."""
    if d.get("sin_ocupacion"):
        return 0
    if d.get("ocupacion_custom") and d.get("ocupacion_manual") not in (None, ""):
        try:
            return int(math.ceil(float(d["ocupacion_manual"])))
        except (TypeError, ValueError):
            pass
    dens = d.get("densidad")
    if dens is None or float(dens or 0) <= 0:
        return None
    sup = float(d.get("sup_util") or d.get("sup_construida") or 0)
    if sup <= 0:
        return 0
    return math.ceil(sup / float(dens))


def resumen_estancias(estancias: list) -> dict:
    """Totales agregados del cuadro compartido: superficies, volumen y ocupación."""
    total_util = total_const = total_vol = 0.0
    total_ocup = 0
    filas = []
    for e in estancias or []:
        u = float(e.get("sup_util") or 0)
        c = float(e.get("sup_construida") or 0)
        h = float(e.get("altura") or 0)
        vol = (u or c) * h
        o = dep_ocupacion(e)
        total_util += u
        total_const += c
        total_vol += vol
        if o:
            total_ocup += o
        filas.append({
            "nombre": e.get("nombre", "-"), "planta": e.get("planta", "-"),
            "sup_util": round(u, 2), "sup_construida": round(c, 2),
            "altura": h or None, "volumen": round(vol, 2) if vol else None,
            "uso": e.get("uso_ocupacion", "-"),
            "ocupacion": o if o is not None else "-",
        })
    return {
        "filas": filas,
        "total_util": round(total_util, 2),
        "total_construida": round(total_const, 2),
        "total_volumen": round(total_vol, 2),
        "total_ocupacion": total_ocup,
        "num_estancias": len(estancias or []),
    }
