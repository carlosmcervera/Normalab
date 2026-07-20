"""Motor de cálculo del módulo CTE DB-SI (Seguridad en caso de incendio).

Cubre un subconjunto operativo del Documento Básico DB-SI: SI 1
(compartimentación), SI 3 (evacuación de ocupantes), SI 4 (instalaciones de
protección) y SI 6 (resistencia al fuego de la estructura). Carácter orientativo.
"""
import math

from normative_modules.cte_dbsi.catalog import (
    SI1_MAX_SECTOR, SI3_RECORRIDO, SI3_RECORRIDO_ESPECIAL, SI6_GRUPO2,
)


def _validate(data):
    errors = []
    if not data.get("uso"):
        errors.append("Debe seleccionar el uso previsto del edificio.")
    if not data.get("superficie_construida") or float(data.get("superficie_construida") or 0) <= 0:
        errors.append("La superficie construida debe ser mayor que 0.")
    if not (data.get("dependencias") or []):
        errors.append("Debe introducir al menos una zona en el cálculo de ocupación.")
    return errors


def _dep_ocupacion(d):
    if d.get("sin_ocupacion"):
        return 0
    dens = d.get("densidad")
    if dens is None or float(dens) <= 0:
        return None
    sup = float(d.get("superficie") or 0)
    return 0 if sup <= 0 else math.ceil(sup / float(dens))


def _build_ocupacion(deps):
    filas, total = [], 0
    for d in deps:
        o = _dep_ocupacion(d)
        if o:
            total += o
        filas.append({"nombre": d.get("nombre", "-"), "sector": "—",
                      "uso": d.get("uso_ocupacion", "-"),
                      "superficie": round(float(d.get("superficie") or 0), 2),
                      "densidad": ("Sin ocupación" if d.get("sin_ocupacion") else (f"{d.get('densidad')} m²/p" if d.get("densidad") else "-")),
                      "ocupacion": o if o is not None else "-"})
    return {"filas": filas, "total": total}


def _si1(uso, superficie):
    maxs = SI1_MAX_SECTOR.get(uso, 2500)
    if maxs is None:
        return {"superficie": round(superficie, 2), "max_sector": None, "cumple": True,
                "mensaje": f"Uso {uso}: sin límite general de superficie de sector (condiciones específicas del DB-SI)."}
    cumple = superficie <= maxs
    return {"superficie": round(superficie, 2), "max_sector": maxs, "cumple": cumple,
            "mensaje": (f"Superficie {superficie:.0f} m² ≤ máx. {maxs:.0f} m² por sector (uso {uso})."
                        if cumple else
                        f"Superficie {superficie:.0f} m² SUPERA el máximo de {maxs:.0f} m² por sector (uso {uso}): es necesario compartimentar.")}


def _si3(uso, ocupacion, num_salidas, recorrido_real):
    num_salidas = int(num_salidas or 1)
    salidas_requeridas = 1 if ocupacion <= 100 else 2
    salidas_ok = num_salidas >= salidas_requeridas
    varias = num_salidas >= 2
    tabla = SI3_RECORRIDO_ESPECIAL.get(uso, SI3_RECORRIDO)
    rec_max = tabla["varias"] if varias else tabla["una"]
    recorrido_real = float(recorrido_real or 0)
    recorrido_ok = recorrido_real <= rec_max if recorrido_real > 0 else True
    ancho_min = 0.80
    ancho_calc = max(ancho_min, round(ocupacion / 200.0, 2))
    return {
        "ocupacion": ocupacion,
        "salidas_requeridas": salidas_requeridas,
        "salidas_proyectadas": num_salidas,
        "salidas_ok": salidas_ok,
        "recorrido_max_permitido": rec_max,
        "recorrido_real": recorrido_real,
        "recorrido_ok": recorrido_ok,
        "ancho_minimo": ancho_min,
        "ancho_calculado": ancho_calc,
        "detalle": (f"Con {ocupacion} ocupantes se requieren {salidas_requeridas} salida(s); "
                    f"recorrido máximo {rec_max} m (DB-SI SI 3). Ancho de salida A ≥ P/200 = {ancho_calc:.2f} m."),
    }


def _si6(uso, altura, bajo_rasante):
    grupo2 = uso in SI6_GRUPO2
    if bajo_rasante:
        val = "R 120" if not grupo2 else "R 180"
        det = "Planta bajo rasante (sótano). DB-SI SI 6, Tabla 3.1."
    else:
        if altura <= 15:
            val = "R 90" if grupo2 else "R 60"
        elif altura <= 28:
            val = "R 120" if grupo2 else "R 90"
        else:
            val = "R 180" if grupo2 else "R 120"
        det = f"Planta sobre rasante, altura de evacuación {altura:.1f} m. DB-SI SI 6, Tabla 3.1."
    if uso == "Aparcamiento":
        val = "R 90"
        det = "Uso Aparcamiento: R 90 (DB-SI SI 6)."
    return {"estabilidad": val, "detalle": det}


def _inst(nombre, obligatorio, detalle):
    return {"nombre": nombre, "obligatorio": obligatorio, "detalle": detalle}


def _si4(uso, superficie, altura, ocupacion):
    inst = []
    inst.append(_inst("Extintores portátiles", True, "Uno de eficacia 21A-113B cada 15 m de recorrido en cada planta (DB-SI SI 4)."))
    bie = superficie >= 500 and uso in ("Comercial", "Pública concurrencia", "Aparcamiento", "Hospitalario") \
        or (uso == "Administrativo" and superficie >= 2000)
    inst.append(_inst("Bocas de incendio equipadas (BIE)", bie,
                      f"Exigibles según uso {uso} y superficie ({superficie:.0f} m²) — DB-SI SI 4, Tabla 1.1."))
    col_seca = altura >= 24
    inst.append(_inst("Columna seca", col_seca, f"Obligatoria si la altura de evacuación ≥ 24 m (altura: {altura:.1f} m)."))
    deteccion = (uso == "Administrativo" and superficie > 2000) or \
                (uso == "Comercial" and superficie > 1000) or \
                (uso in ("Hospitalario", "Residencial Público")) or \
                (uso == "Pública concurrencia" and superficie > 1000)
    inst.append(_inst("Sistema de detección y alarma", deteccion,
                      f"Exigible según uso {uso} y superficie ({superficie:.0f} m²) — DB-SI SI 4, Tabla 1.1."))
    alarma = ocupacion > 500
    inst.append(_inst("Sistema de alarma por voz", alarma, f"Exigible si la ocupación supera 500 personas (ocupación: {ocupacion})."))
    hidrantes = superficie > 5000 or uso == "Aparcamiento" and superficie > 10000
    inst.append(_inst("Hidrantes exteriores", hidrantes, f"Exigibles según uso y superficie ({superficie:.0f} m²) — DB-SI SI 4."))
    rociadores = (uso == "Comercial" and superficie > 1500) or (uso == "Aparcamiento" and superficie > 10000)
    inst.append(_inst("Rociadores automáticos", rociadores, f"Exigibles según uso {uso} y superficie ({superficie:.0f} m²)."))
    inst.append(_inst("Alumbrado de emergencia", True, "Recorridos de evacuación y locales de riesgo (DB-SUA 4)."))
    inst.append(_inst("Señalización de evacuación e instalaciones", True, "Señalización de salidas y medios de protección (DB-SI SI 3.7 / SI 4.2)."))
    return {"instalaciones": inst}


def compute(data: dict) -> dict:
    errors = _validate(data)
    if errors:
        raise ValueError(" ".join(errors))

    uso = data["uso"]
    superficie = float(data["superficie_construida"])
    altura = float(data.get("altura_evacuacion") or 0)
    bajo_rasante = bool(data.get("bajo_rasante"))
    deps = data.get("dependencias") or []

    ocupacion = _build_ocupacion(deps)
    si1 = _si1(uso, superficie)
    si3 = _si3(uso, ocupacion["total"], data.get("num_salidas", 1), data.get("recorrido_max_real"))
    si6 = _si6(uso, altura, bajo_rasante)
    si4 = _si4(uso, superficie, altura, ocupacion["total"])

    from normative_modules.cte_dbsi.tablas import build_tablas
    tablas = build_tablas(uso, altura, bajo_rasante, si3)

    observaciones = [{"tipo": "info", "texto": f"Uso previsto: {uso}. Ocupación total calculada: {ocupacion['total']} personas (DB-SI Tabla 2.1)."}]
    if not si1["cumple"]:
        observaciones.append({"tipo": "error", "texto": si1["mensaje"]})
    if not si3["salidas_ok"]:
        observaciones.append({"tipo": "error", "texto": f"Se proyectan {si3['salidas_proyectadas']} salida(s) pero se requieren {si3['salidas_requeridas']} (SI 3)."})
    if not si3["recorrido_ok"]:
        observaciones.append({"tipo": "error", "texto": f"El recorrido real ({si3['recorrido_real']:.1f} m) supera el máximo admisible ({si3['recorrido_max_permitido']} m) (SI 3)."})

    if any(o["tipo"] == "error" for o in observaciones):
        estado_global = "no_cumple"
    elif any(o["tipo"] == "warning" for o in observaciones):
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    return {
        "uso": uso, "superficie": round(superficie, 2), "altura": altura,
        "ocupacion": ocupacion, "si1": si1, "si3": si3, "si4": si4, "si6": si6,
        "tablas": tablas, "observaciones": observaciones, "estado_global": estado_global,
    }
