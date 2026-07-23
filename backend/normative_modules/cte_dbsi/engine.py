"""Motor CTE DB-SI completo (método tabulado): SI 1 a SI 6.

Devuelve una lista de `secciones` (una por SI) con sus verificaciones, filas
resumen e instalaciones. Se apoya en la tabla maestra `tablas_oficiales`.
Carácter orientativo.
"""
import math

from normative_modules.cte_dbsi import tablas_oficiales as T


def _validate(data):
    errors = []
    if not data.get("uso"):
        errors.append("Debe seleccionar el uso previsto del edificio.")
    if not data.get("superficie_construida") or float(data.get("superficie_construida") or 0) <= 0:
        errors.append("La superficie construida debe ser mayor que 0.")
    if not (data.get("dependencias") or []):
        errors.append("Debe introducir al menos una zona en el cálculo de ocupación.")
    return errors


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _dep_ocupacion(d):
    if d.get("sin_ocupacion"):
        return 0
    man = d.get("ocupacion_manual")
    if d.get("ocupacion_custom") and man not in (None, ""):
        try:
            return int(math.ceil(float(man)))
        except (TypeError, ValueError):
            pass
    dens = d.get("densidad")
    if dens is None or _num(dens) <= 0:
        return None
    sup = _num(d.get("superficie"))
    return 0 if sup <= 0 else math.ceil(sup / _num(dens))


def _build_ocupacion(deps):
    filas, total = [], 0
    for d in deps:
        o = _dep_ocupacion(d)
        if o:
            total += o
        filas.append({"nombre": d.get("nombre", "-"), "sector": "—",
                      "uso": d.get("uso_ocupacion", "-"),
                      "superficie": round(_num(d.get("superficie")), 2),
                      "densidad": ("Sin ocupación" if d.get("sin_ocupacion") else (f"{d.get('densidad')} m²/p" if d.get("densidad") else "-")),
                      "ocupacion": o if o is not None else "-"})
    return {"filas": filas, "total": total}


def _sec(id, titulo, ref, estado, filas, instalaciones=None, obs=None):
    return {"id": id, "titulo": titulo, "referencia": ref, "estado": estado,
            "filas": filas, "instalaciones": instalaciones, "observaciones": obs or []}


def _kv(k, v):
    return {"k": k, "v": v}


def _si1(uso, sup, altura, bajo_rasante, local_re):
    maxs = T.SI1_SECTOR_MAX.get(uso, 2500)
    if maxs is None:
        cumple, msg = True, "Un sector por planta / sin límite general de superficie (condiciones específicas del uso)."
        max_txt = "Un sector por planta"
    else:
        cumple = sup <= maxs
        max_txt = f"{maxs:.0f} m²"
        msg = (f"Superficie {sup:.0f} m² ≤ máximo {maxs:.0f} m²." if cumple
               else f"Superficie {sup:.0f} m² SUPERA el máximo de {maxs:.0f} m²: es necesario compartimentar.")
    ei = T.si1_delimitador_ei(altura, bajo_rasante)
    filas = [
        _kv("Superficie construida", f"{sup:.0f} m²"),
        _kv("Superficie máx. por sector (Tabla 1.1)", max_txt),
        _kv("Resistencia de elementos delimitadores (Tabla 1.2)", ei),
        _kv("Reacción al fuego de revestimientos (Tabla 4.1)", T.SI1_REACCION),
    ]
    obs = [] if cumple else [msg]
    if local_re and local_re != "ninguno":
        c = T.SI1_RIESGO_ESPECIAL[local_re]
        filas += [
            _kv(f"Local de riesgo especial ({local_re})", f"Estructura {c['R']} · paredes/techos {c['EI']}"),
            _kv("Vestíbulo de independencia", "Sí" if c["vestibulo"] else "No exigible"),
            _kv("Puertas del local", c["puerta"]),
            _kv("Recorrido máx. hasta salida del local", f"{c['recorrido']} m"),
        ]
    return _sec("SI1", "SI 1 · Compartimentación en sectores de incendio",
                "CTE DB-SI · SI 1 (Tablas 1.1, 1.2, 2.2 y 4.1)",
                "cumple" if cumple else "no_cumple", filas, None, obs)


def _si2(dist_colindantes, angulo=None, dist_huecos=None, huecos_ei60=False, colindante=False):
    filas = [
        _kv("Medianerías y muros colindantes", T.SI2_MEDIANERIA),
        _kv("Fachadas (limitación de propagación)", T.SI2_FACHADA),
        _kv("Cubiertas", T.SI2_CUBIERTA),
    ]
    estado, obs = "info", []
    d = _num(dist_colindantes, -1)
    if d >= 0:
        filas.append(_kv("Separación a edificios/linderos colindantes", f"{d:.1f} m"))
        if d < T.SI2_DIST_MIN:
            estado = "no_cumple"
            obs.append(f"Separación {d:.1f} m < {T.SI2_DIST_MIN:.0f} m: los huecos de fachada requieren protección EI o retranqueo (SI 2).")
        else:
            estado = "cumple"

    # Separación entre huecos según el ángulo entre planos de fachada (SI 2, Tabla 1.1)
    ang = _num(angulo, -1)
    if ang >= 0:
        d_req = T.si2_distancia_huecos(ang)
        d_ef = round(d_req / 2, 2) if colindante else d_req
        filas.append(_kv("Ángulo entre planos de fachada", f"{ang:.0f}°"))
        filas.append(_kv("Distancia mínima entre huecos (Tabla 1.1)",
                         f"{d_ef:.2f} m" + (" (50 % · edificio colindante)" if colindante else "")))
        if huecos_ei60:
            filas.append(_kv("Resistencia al fuego de los huecos", "EI 60 (no requiere separación mínima)"))
        else:
            dh = _num(dist_huecos, -1)
            if dh >= 0:
                filas.append(_kv("Distancia entre huecos proyectada", f"{dh:.2f} m"))
                if dh < d_ef:
                    estado = "no_cumple"
                    obs.append(f"Los huecos distan {dh:.2f} m < {d_ef:.2f} m exigidos para un ángulo de {ang:.0f}°: "
                               f"dote a los huecos de EI 60 o aumente la separación (SI 2, Tabla 1.1).")
                elif estado != "no_cumple":
                    estado = "cumple"
    return _sec("SI2", "SI 2 · Propagación exterior", "CTE DB-SI · SI 2 (Tabla 1.1)", estado, filas, None, obs)


def _si3(uso, ocupacion, num_salidas, recorrido_real, ancho_proyectado, altura, sentido):
    num_salidas = int(num_salidas or 1)
    varias = num_salidas >= 2
    salidas_req = 1 if ocupacion <= 100 else 2
    salidas_ok = num_salidas >= salidas_req

    tabla = T.SI3_RECORRIDO_ESPECIAL.get(uso, T.SI3_RECORRIDO)
    rec_max = tabla["varias"] if varias else tabla["una"]
    recorrido_real = _num(recorrido_real)
    recorrido_ok = recorrido_real <= rec_max if recorrido_real > 0 else True

    ancho_req = max(T.SI3_ANCHO_MIN["puerta"], round(ocupacion / T.SI3_MODULO, 2))
    ancho_proyectado = _num(ancho_proyectado)
    ancho_ok = ancho_proyectado >= ancho_req if ancho_proyectado > 0 else True

    escalera = T.si3_proteccion_escalera(altura, sentido)
    humos = uso == "Aparcamiento" or (uso in ("Comercial", "Pública concurrencia") and ocupacion > 1000)
    pmr = altura > 14 and uso != "Aparcamiento"

    filas = [
        _kv("Ocupación total (Tabla 2.1)", f"{ocupacion} personas"),
        _kv("Nº de salidas (requeridas / proyectadas)", f"{salidas_req} / {num_salidas}"),
        _kv("Recorrido máx. admisible (Tabla 3.1)", f"{rec_max} m"),
        _kv("Recorrido real", f"{recorrido_real:.1f} m" if recorrido_real else "—"),
        _kv("Ancho de salida A ≥ P/200 (Tabla 4.1)", f"req. {ancho_req:.2f} m · proy. {ancho_proyectado:.2f} m" if ancho_proyectado else f"requerido {ancho_req:.2f} m (mín. 0,80 m)"),
        _kv("Protección de escaleras (Tabla 5.1)", f"{escalera} (evac. {sentido})"),
        _kv("Control de humos (SI 3.8)", "Obligatorio" if humos else "No exigible"),
        _kv("Evacuación de PMR / zona de refugio (SI 3.9)", "Zona de refugio exigible (altura > 14 m)" if pmr else "No exigible"),
    ]
    obs = []
    if not salidas_ok:
        obs.append(f"Se proyectan {num_salidas} salida(s) pero se requieren {salidas_req} (ocupación {ocupacion}).")
    if not recorrido_ok:
        obs.append(f"El recorrido real ({recorrido_real:.1f} m) supera el máximo ({rec_max} m).")
    if not ancho_ok:
        obs.append(f"El ancho proyectado ({ancho_proyectado:.2f} m) es inferior al requerido ({ancho_req:.2f} m).")
    estado = "no_cumple" if obs else "cumple"
    return _sec("SI3", "SI 3 · Evacuación de ocupantes",
                "CTE DB-SI · SI 3 (Tablas 3.1, 4.1 y 5.1)", estado, filas, None, obs)


def _inst(nombre, obligatorio, detalle):
    return {"nombre": nombre, "obligatorio": obligatorio, "detalle": detalle}


def _si4(uso, sup, altura, ocup, num_plantas=1, deps=None):
    num_plantas = max(1, int(num_plantas or 1))
    deps = deps or []
    bie = {"Comercial": sup >= 500, "Pública concurrencia": sup >= 500, "Aparcamiento": sup > 500,
           "Hospitalario": True, "Administrativo": sup >= 2000, "Docente": sup >= 2000,
           "Residencial Público": sup >= 2000, "Residencial Vivienda": False}.get(uso, sup >= 2000)
    det = {"Residencial Vivienda": altura > 50, "Administrativo": sup > 2000, "Docente": sup > 2000,
           "Comercial": sup > 1000, "Pública concurrencia": sup > 1000, "Hospitalario": True,
           "Residencial Público": sup > 500, "Aparcamiento": sup > 500}.get(uso, sup > 2000)
    alarma = {"Administrativo": sup > 5000, "Comercial": sup > 1000, "Pública concurrencia": ocup > 500,
              "Hospitalario": True, "Residencial Público": True, "Docente": sup > 5000,
              "Residencial Vivienda": altura > 50, "Aparcamiento": False}.get(uso, ocup > 500)
    hid = {"Comercial": sup > 1000, "Pública concurrencia": sup > 5000, "Hospitalario": True,
           "Administrativo": sup > 5000, "Docente": sup > 5000, "Aparcamiento": sup > 1000,
           "Residencial Público": sup > 5000, "Residencial Vivienda": sup > 5000}.get(uso, sup > 5000)
    roc = (uso == "Comercial" and sup > 1500) or (uso == "Aparcamiento" and sup > 10000)
    por_planta = f" Dotación en cada una de las {num_plantas} planta(s)." if num_plantas > 1 else ""
    inst = [
        _inst("Extintores portátiles", True, f"Eficacia 21A-113B a ≤ 15 m de recorrido en cada planta y en zonas de riesgo especial.{por_planta}"),
        _inst("Bocas de incendio equipadas (BIE)", bie, f"Uso {uso}, superficie {sup:.0f} m² (DB-SI SI 4, Tabla 1.1)."),
        _inst("Columna seca", altura > 24, f"Obligatoria si la altura de evacuación > 24 m (altura: {altura:.1f} m)."),
        _inst("Sistema de detección automática", det, f"Uso {uso}, superficie {sup:.0f} m² (Tabla 1.1)."),
        _inst("Sistema de alarma", bool(alarma) or ocup > 500, f"Uso {uso}, ocupación {ocup} (Tabla 1.1)."),
        _inst("Hidrantes exteriores", hid, f"Uso {uso}, superficie {sup:.0f} m² (Tabla 1.1)."),
        _inst("Rociadores automáticos", roc, f"Uso {uso}, superficie {sup:.0f} m² (Tabla 1.1)."),
        _inst("Ascensor de emergencia", altura > 28, f"Obligatorio si la altura de evacuación > 28 m (altura: {altura:.1f} m)."),
        _inst("Alumbrado de emergencia", True, f"Recorridos de evacuación y locales de riesgo (DB-SUA 4).{por_planta}"),
        _inst("Señalización de evacuación y de medios de protección", True, f"DB-SI SI 3.7 y SI 4.2.{por_planta}"),
    ]
    filas = [_kv("Nº de plantas", str(num_plantas))]
    for d in deps:
        s = _num(d.get("superficie"))
        if s > 0:
            n_ext = max(1, math.ceil(s / 300))
            filas.append(_kv(f"Extintores orientativos · {d.get('nombre') or 'zona'} ({s:.0f} m²)",
                             f"{n_ext} (≥ 1 cada 300 m², recorrido ≤ 15 m)"))
    return _sec("SI4", "SI 4 · Instalaciones de protección contra incendios",
                "CTE DB-SI · SI 4 (Tabla 1.1)", "info", filas, inst, [])


def _si5(altura, vial_ok):
    v = T.SI5_VIAL
    espacio = altura > T.SI5_ALTURA_ESPACIO_MANIOBRA
    filas = [
        _kv("Vial de aproximación", f"anchura ≥ {v['anchura']} m · gálibo ≥ {v['altura_libre']} m · capacidad ≥ {v['capacidad_portante']:.0f} kN/m²"),
        _kv("Espacio de maniobra en fachada", "Obligatorio (altura de evacuación > 9 m)" if espacio else "No exigible por altura"),
        _kv("Accesibilidad por fachada", "Huecos practicables ≤ cada 25 m, ≥ 0,80 × 1,20 m, alféizar ≤ 1,20 m"),
    ]
    obs = []
    estado = "info"
    if vial_ok is False:
        estado = "no_cumple"
        obs.append("El vial de aproximación no cumple las condiciones mínimas de SI 5.")
    return _sec("SI5", "SI 5 · Intervención de los bomberos", "CTE DB-SI · SI 5", estado, filas, None, obs)


def _si6(uso, altura, bajo_rasante, local_re):
    r = T.si6_estructura(uso, altura, bajo_rasante)
    filas = [
        _kv("Resistencia de la estructura portante (Tabla 3.1)", r),
        _kv("Situación", "Planta bajo rasante" if bajo_rasante else f"Sobre rasante · h {altura:.1f} m"),
    ]
    if local_re and local_re != "ninguno":
        filas.append(_kv(f"Estructura en local de riesgo especial ({local_re}) (Tabla 3.2)", T.SI6_RIESGO_ESPECIAL_R[local_re]))
    return _sec("SI6", "SI 6 · Resistencia al fuego de la estructura",
                "CTE DB-SI · SI 6 (Tablas 3.1 y 3.2)", "info", filas, None, [])


def compute(data: dict) -> dict:
    errors = _validate(data)
    if errors:
        raise ValueError(" ".join(errors))

    uso = data["uso"]
    sup = _num(data["superficie_construida"])
    altura = _num(data.get("altura_evacuacion"))
    bajo_rasante = bool(data.get("bajo_rasante"))
    local_re = data.get("local_riesgo_especial") or "ninguno"
    sentido = data.get("sentido_evacuacion") or "descendente"
    deps = data.get("dependencias") or []

    ocupacion = _build_ocupacion(deps)
    secciones = [
        _si1(uso, sup, altura, bajo_rasante, local_re),
        _si2(data.get("distancia_colindantes"), data.get("angulo_fachadas"),
             data.get("distancia_huecos"), bool(data.get("huecos_ei60")), bool(data.get("edificio_colindante"))),
        _si3(uso, ocupacion["total"], data.get("num_salidas", 1), data.get("recorrido_max_real"),
             data.get("ancho_salidas_proyectado"), altura, sentido),
        _si4(uso, sup, altura, ocupacion["total"], data.get("num_plantas"), deps),
        _si5(altura, data.get("vial_aproximacion_ok")),
        _si6(uso, altura, bajo_rasante, local_re),
    ]

    from normative_modules.cte_dbsi.tablas import build_tablas
    tablas = build_tablas(uso, altura, bajo_rasante)

    observaciones = [{"tipo": "info", "texto": f"Uso previsto: {uso}. Ocupación total: {ocupacion['total']} personas (DB-SI, Tabla 2.1)."}]
    for s in secciones:
        for o in s["observaciones"]:
            observaciones.append({"tipo": "error", "texto": f"{s['id']}: {o}"})

    estados = [s["estado"] for s in secciones]
    if "no_cumple" in estados:
        estado_global = "no_cumple"
    elif "observaciones" in estados:
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    return {
        "uso": uso, "superficie": round(sup, 2), "altura": altura,
        "ocupacion": ocupacion, "secciones": secciones,
        "tablas": tablas, "observaciones": observaciones, "estado_global": estado_global,
    }
