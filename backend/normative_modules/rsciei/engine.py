"""RSCIEI rules & calculation engine (RD 164/2025).

Modelo multi-sector: un estudio se compone de dependencias (con superficie útil
y construida) agrupadas en sectores de incendio. Cada dependencia aporta carga
de fuego y ocupación. Para cada sector se calcula la densidad de carga de fuego
ponderada y corregida (Qs), el nivel de riesgo intrínseco (NRI), la superficie
máxima admisible (Tabla 2.1.1), los requisitos (Anexos II y III) y las
condiciones de evacuación (Tabla 2.3.1).
"""

import math

from normative_modules.rsciei.requirements import build_requirements

MCAL_PER_MJ = 1 / 4.184

# Tabla 1.3.1 · niveles de riesgo intrínseco (Qs en MJ/m²)
NRI_TABLE = [
    (1, 0, 425, "BAJO"),
    (2, 425, 850, "BAJO"),
    (3, 850, 1275, "MEDIO"),
    (4, 1275, 1700, "MEDIO"),
    (5, 1700, 3400, "MEDIO"),
    (6, 3400, 6800, "ALTO"),
    (7, 6800, 13600, "ALTO"),
    (8, 13600, float("inf"), "ALTO"),
]

# Tabla 2.1.1 (RD 164/2025) · superficie máxima construida admisible por sector (m²)
# None = NO ADMITIDO ; "SIN_LIMITE" = sin límite establecido
MAX_SURFACE = {
    "AV": {1: 2000, 2: 1000, 3: 500, 4: 400, 5: 300, 6: None, 7: None, 8: None},
    "AH": {1: 6000, 2: 4000, 3: 3500, 4: 3000, 5: 2500, 6: 2000, 7: 1500, 8: None},
    "B": {1: 12000, 2: 8000, 3: 7000, 4: 6000, 5: 5000, 6: 4000, 7: 3000, 8: None},
    "C": {1: "SIN_LIMITE", 2: 12000, 3: 10000, 4: 8000, 5: 7000, 6: 6000, 7: 5000, 8: 4000},
}

CONFIG_LABELS = {
    "AV": "Tipo A - separación vertical",
    "AH": "Tipo A - separación horizontal",
    "B": "Tipo B - edificio adosado",
    "C": "Tipo C - edificio aislado",
    "D": "Tipo D - espacio abierto",
}

# Tabla 2.3.1 · longitud máxima del recorrido de evacuación (m)
EVAC_TABLE = {
    "BAJO": {"una": 50, "varias": 50, "sin_alt": 50},
    "MEDIO": {"una": 35, "varias": 50, "sin_alt": 35},
    "ALTO": {"una": 20, "varias": 35, "sin_alt": 20},
}


def _validate(sectores, dependencias):
    errors = []
    if not sectores:
        errors.append("Debe definir al menos un sector de incendio.")
    if not dependencias:
        errors.append("Debe introducir al menos una dependencia en el cuadro de superficies.")
    sector_ids = {s.get("id") for s in sectores}
    for d in dependencias:
        nombre = d.get("nombre") or "Dependencia sin nombre"
        if not d.get("sector_id") or d.get("sector_id") not in sector_ids:
            errors.append(f"«{nombre}»: debe asignarse a un sector de incendio.")
        if not d.get("sup_construida") or float(d.get("sup_construida") or 0) <= 0:
            errors.append(f"«{nombre}»: la superficie construida debe ser mayor que 0.")
    for s in sectores:
        deps = [d for d in dependencias if d.get("sector_id") == s.get("id")]
        if not deps:
            errors.append(f"El sector «{s.get('nombre', '?')}» no tiene dependencias asignadas.")
        for d in deps:
            if d.get("es_lre"):
                continue
            nombre = d.get("nombre") or "Dependencia"
            if not d.get("ci") or float(d.get("ci") or 0) <= 0:
                errors.append(f"«{nombre}»: defina el coeficiente Ci (carga de fuego).")
            if d.get("modo") == "almacenamiento":
                if not d.get("qvi") or float(d.get("qvi") or 0) <= 0:
                    errors.append(f"«{nombre}»: qvi (MJ/m³) debe ser mayor que 0.")
                if not d.get("hi") or float(d.get("hi") or 0) <= 0:
                    errors.append(f"«{nombre}»: la altura de almacenamiento hi debe ser mayor que 0.")
            else:
                if not d.get("qsi") or float(d.get("qsi") or 0) <= 0:
                    errors.append(f"«{nombre}»: qsi (MJ/m²) debe ser mayor que 0.")
    return errors


def _nri_for(qs_mj: float):
    for nivel, low, high, cat in NRI_TABLE:
        if low < qs_mj <= high or (nivel == 1 and qs_mj <= high):
            return nivel, cat
    return 8, "ALTO"


def _dep_ocupacion(d):
    if d.get("sin_ocupacion"):
        return 0
    dens = d.get("densidad")
    if dens is None or float(dens) <= 0:
        return None
    sup = float(d.get("sup_util") or d.get("sup_construida") or 0)
    if sup <= 0:
        return 0
    return math.ceil(sup / float(dens))


def _sector_config(sec, establecimiento):
    if sec.get("tipo") == "area_exterior":
        return "D"
    return sec.get("config") or establecimiento.get("config") or "C"


def _sectorizacion(config, nivel, A, factor, factores_aplicados, situacion):
    base = {
        "config": config,
        "config_label": CONFIG_LABELS.get(config, config),
        "superficie_sector": round(A, 2),
        "factor_incremento": round(factor, 3),
        "factores_aplicados": factores_aplicados,
    }
    if config == "D":
        base.update({"estado": "no_aplica", "max_admisible": None, "max_admisible_base": None,
                     "mensaje": "Configuración en espacio abierto (tipo D): no aplica límite de superficie de sector (Tabla 2.1.1)."})
        return base
    tabla = MAX_SURFACE.get(config, {})
    valor = tabla.get(nivel)
    if valor is None:
        base.update({"estado": "no_admitido", "max_admisible": None, "max_admisible_base": None,
                     "mensaje": f"NO ADMITIDO: la configuración {config} no admite el nivel de riesgo {nivel} (Tabla 2.1.1)."})
        return base
    if valor == "SIN_LIMITE":
        base.update({"estado": "cumple", "max_admisible": None, "max_admisible_base": "SIN LÍMITE",
                     "mensaje": "Sin límite de superficie establecido para esta configuración y nivel."})
        return base
    bajo_rasante = situacion == "bajo_rasante"
    base_val = valor / 2 if bajo_rasante else valor
    if bajo_rasante:
        factores_aplicados.append("Planta bajo rasante: superficie base ÷ 2 (nota 1, Tabla 2.1.1)")
    max_adm = base_val * factor
    cumple = A <= max_adm
    base.update({
        "max_admisible_base": base_val,
        "max_admisible": round(max_adm, 2),
        "estado": "cumple" if cumple else "no_cumple",
        "mensaje": (f"Superficie {A:.0f} m² ≤ máx. admisible {max_adm:.0f} m²."
                    if cumple else
                    f"Superficie {A:.0f} m² SUPERA el máximo admisible {max_adm:.0f} m². "
                    "Es necesario compartimentar en varios sectores de incendio."),
    })
    return base


EVAC_COEF_FACTOR = {"nota4a": 1.25, "nota4b": 1.25, "nota4c": 2.0}
EVAC_COEF_LABEL = {
    "ninguno": "Sin incremento",
    "nota4a": "Nota 4a · extinción automática de agua (+25%)",
    "nota4b": "Nota 4b · control de humos y calor (+25%)",
    "nota4c": "Nota 4c · planta de salida, ≥2 salidas directas, h≥8 m y extinción automática (+100%)",
    "nota5": "Nota 5 · riesgo bajo nivel 1 con materiales incombustibles (A1/A2, 95% masa)",
}


def _evac_base(cat, varias, tipo):
    e = EVAC_TABLE.get(cat, EVAC_TABLE["MEDIO"])
    if tipo == "sin_alternativa":
        return e["sin_alt"] if varias else e["una"]
    return e["varias"] if varias else e["una"]


def _evac_max(cat, nivel, varias, tipo, coef):
    if coef == "nota5" and cat == "BAJO" and nivel == 1:
        if not varias:
            return 100.0
        return 100.0 if tipo == "sin_alternativa" else 150.0
    base = _evac_base(cat, varias, tipo)
    return round(base * EVAC_COEF_FACTOR.get(coef, 1.0), 2)


def _evacuacion(sec, categoria, nivel, ocupacion):
    num_salidas = int(sec.get("num_salidas") or 1)
    varias = num_salidas >= 2
    coef = sec.get("evac_coeficiente") or "ninguno"
    if coef == "nota5" and not (categoria == "BAJO" and nivel == 1):
        coef = "ninguno"  # Nota 5 solo aplica a riesgo bajo nivel 1

    recorridos, all_ok = [], True
    for r in (sec.get("recorridos") or []):
        tipo = r.get("tipo") or "hasta_salida"
        dmax = _evac_max(categoria, nivel, varias, tipo, coef)
        dreal = float(r.get("distancia_real") or 0)
        cumple = dreal <= dmax if dreal > 0 else True
        if not cumple:
            all_ok = False
        recorridos.append({"origen": r.get("origen") or "Origen de evacuación", "tipo": tipo,
                           "distancia_real": dreal, "distancia_max": dmax, "cumple": cumple})

    dist_hasta = _evac_max(categoria, nivel, varias, "hasta_salida", coef)
    dist_sin = _evac_max(categoria, nivel, varias, "sin_alternativa", coef)
    salidas_ok, nota = True, None
    if (ocupacion or 0) > 100 and not varias:
        salidas_ok = False
        nota = "Ocupación > 100 personas: se requieren al menos 2 salidas alternativas."
    return {
        "num_salidas": num_salidas,
        "ocupacion": ocupacion or 0,
        "categoria": categoria,
        "coeficiente": coef,
        "coeficiente_label": EVAC_COEF_LABEL.get(coef, "Sin incremento"),
        "distancia_maxima": dist_hasta,
        "recorrido_sin_alternativa": dist_sin,
        "recorridos": recorridos,
        "recorridos_cumplen": all_ok,
        "salidas_suficientes": salidas_ok,
        "nota": nota,
        "detalle": (f"Riesgo {categoria.lower()}, {'2 o más salidas' if varias else 'una salida'}: "
                    f"recorrido de evacuación máximo {dist_hasta} m; sin alternativa {dist_sin} m (Tabla 2.3.1"
                    f"{'' if coef == 'ninguno' else '; ' + EVAC_COEF_LABEL.get(coef, '')})."),
    }


def _compute_sector(sec, deps, establecimiento):
    config = _sector_config(sec, establecimiento)
    situacion = sec.get("situacion", "sobre_rasante")
    lre_deps = [d for d in deps if d.get("es_lre")]
    calc_deps = [d for d in deps if not d.get("es_lre")]
    A = sum(float(d.get("sup_construida") or 0) for d in calc_deps)

    detalle_zonas = []
    numerador = 0.0
    rmins, used_ci, ras = [], [], []
    for d in calc_deps:
        ci = float(d.get("ci") or 0)
        s = float(d.get("sup_construida") or 0)
        if d.get("modo") == "almacenamiento":
            qvi = float(d.get("qvi") or 0)
            hi = float(d.get("hi") or 0)
            aporte = qvi * ci * hi * s
            detalle_zonas.append({"descripcion": d.get("nombre", "Zona"), "modo": "almacenamiento",
                                  "qvi": qvi, "hi": hi, "ci": ci, "superficie": s, "aporte": round(aporte, 2)})
        else:
            qsi = float(d.get("qsi") or 0)
            aporte = qsi * ci * s
            detalle_zonas.append({"descripcion": d.get("nombre", "Zona"), "modo": "produccion",
                                  "qsi": qsi, "ci": ci, "superficie": s, "aporte": round(aporte, 2)})
        numerador += aporte
        used_ci.append(ci)
        ras.append(float(d.get("ra") or 1.0))
        if d.get("rmin"):
            rmins.append(float(d["rmin"]))

    ra_auto = max(ras) if ras else 1.0
    ra = float(sec.get("ra") or ra_auto)
    rmin_req = max(rmins) if rmins else None

    qs_mj = (numerador / A) * ra if A > 0 else 0.0
    qs_mcal = qs_mj * MCAL_PER_MJ
    nivel, categoria = _nri_for(qs_mj)

    factor = 1.0
    factores = []
    if bool(sec.get("fachada_accesible")):
        factor *= 1.25
        factores.append("Fachada accesible ≥ 50% del perímetro (×1,25)")
    if bool(sec.get("rociadores")):
        factor *= 2.0
        factores.append("Rociadores automáticos en todo el sector (×2)")

    sector = _sectorizacion(config, nivel, A, factor, factores, situacion)

    sup_alm = sum(float(d.get("sup_construida") or 0) for d in calc_deps if d.get("modo") == "almacenamiento")
    sup_prod = A - sup_alm
    modo_pred = "almacenamiento" if sup_alm > sup_prod else "produccion"

    ocupacion_sector = 0
    for d in deps:
        o = _dep_ocupacion(d)
        if o:
            ocupacion_sector += o

    total_est = sum(float(d.get("sup_construida") or 0) for d in establecimiento.get("_all_deps", []))
    req_sec = dict(sec)
    req_sec["config"] = config
    requisitos = build_requirements(req_sec, nivel, categoria, modo_pred, A, total_est)

    evacuacion = _evacuacion(sec, categoria, nivel, ocupacion_sector)

    # Locales de riesgo especial (LRE): fuera del cálculo de la carga de fuego del sector.
    locales_re = []
    for d in lre_deps:
        locales_re.append({
            "nombre": d.get("nombre", "Local de riesgo especial"),
            "superficie": round(float(d.get("sup_construida") or d.get("sup_util") or 0), 2),
            "riesgo": (d.get("lre_riesgo") or "bajo").upper(),
            "resistencia": d.get("lre_r") or "R 90",
            "actividad": d.get("actividad_cat") or d.get("uso_ocupacion") or "-",
        })

    # Ámbito del sector: industrial (RSCIEI) o CTE. Los sectores CTE calculan igualmente
    # la carga de fuego (Qs) y, además, se evalúan con las secciones del CTE DB-SI.
    ambito = sec.get("ambito") or "industrial"
    dbsi_res = None
    if ambito == "cte":
        try:
            from normative_modules.cte_dbsi import engine as _dbsi
            dbsi_res = _dbsi.compute({
                "uso": sec.get("uso_cte") or "Administrativo",
                "superficie_construida": A or 1,
                "altura_evacuacion": float(sec.get("altura_evacuacion") or 0),
                "num_salidas": int(sec.get("num_salidas") or 1),
                "num_plantas": int(sec.get("num_plantas") or 1),
                "recorrido_max_real": sec.get("recorrido_max_real"),
                "sentido_evacuacion": sec.get("sentido_evacuacion"),
                "ancho_salidas_proyectado": sec.get("ancho_salidas_proyectado"),
                "distancia_colindantes": sec.get("distancia_colindantes"),
                "bajo_rasante": situacion == "bajo_rasante",
                "dependencias": [{"nombre": d.get("nombre"),
                                  "superficie": float(d.get("sup_util") or d.get("sup_construida") or 0),
                                  "densidad": d.get("densidad"), "sin_ocupacion": d.get("sin_ocupacion"),
                                  "uso_ocupacion": d.get("uso_ocupacion")} for d in (calc_deps or deps)],
            })
        except ValueError:
            dbsi_res = None

    observaciones = []
    observaciones.append({"tipo": "info", "texto": f"Sector «{sec.get('nombre','?')}»: nivel de riesgo intrínseco {nivel} ({categoria}), Tabla 1.3.1."})
    if rmin_req and ra < rmin_req - 1e-6:
        observaciones.append({"tipo": "warning", "texto": (
            f"El coeficiente de activación Ra={ra:.1f} del sector es inferior al mínimo normativo "
            f"Rmin={rmin_req:.1f} exigido por alguna actividad (Tabla 1.3.4/1.3.5). Debe usarse Ra ≥ {rmin_req:.1f}.")})
    if sector.get("estado") in ("no_cumple", "no_admitido"):
        observaciones.append({"tipo": "error", "texto": sector["mensaje"]})
    if not evacuacion["salidas_suficientes"]:
        observaciones.append({"tipo": "error", "texto": f"Sector «{sec.get('nombre','?')}»: {evacuacion['nota']}"})
    if not evacuacion["recorridos_cumplen"]:
        observaciones.append({"tipo": "error", "texto": f"Sector «{sec.get('nombre','?')}»: algún recorrido de evacuación supera la distancia máxima admisible (Tabla 2.3.1)."})
    if categoria == "ALTO":
        observaciones.append({"tipo": "warning", "texto": f"Sector «{sec.get('nombre','?')}»: riesgo ALTO, revise requisitos reforzados de estabilidad e instalaciones."})
    if ambito == "cte":
        observaciones.append({"tipo": "info", "texto": (
            f"Sector «{sec.get('nombre','?')}» dentro del ámbito de aplicación del CTE "
            f"({sec.get('uso_cte') or 'edificación'}); se calcula igualmente la carga de fuego (Qs) y se evalúa con el CTE DB-SI.")})
    if locales_re:
        observaciones.append({"tipo": "info", "texto": (
            f"Sector «{sec.get('nombre','?')}»: {len(locales_re)} local(es) de riesgo especial excluidos del cálculo de la carga de fuego (se evalúan por separado).")})

    estado = "cumple"
    if sector.get("estado") in ("no_cumple", "no_admitido") or not evacuacion["salidas_suficientes"] or not evacuacion["recorridos_cumplen"] or (dbsi_res and dbsi_res.get("estado_global") == "no_cumple"):
        estado = "no_cumple"
    elif any(o["tipo"] == "warning" for o in observaciones):
        estado = "observaciones"

    return {
        "id": sec.get("id"),
        "nombre": sec.get("nombre", "Sector"),
        "tipo": sec.get("tipo", "sector"),
        "planta": sec.get("planta", "-"),
        "config": config,
        "config_label": CONFIG_LABELS.get(config, config),
        "situacion": situacion,
        "modo_predominante": modo_pred,
        "ocupacion": ocupacion_sector,
        "rmin_requerido": rmin_req,
        "calculo": {"numerador": round(numerador, 2), "A": round(A, 2), "ra": ra,
                    "qs_mj": round(qs_mj, 2), "qs_mcal": round(qs_mcal, 2), "zonas": detalle_zonas},
        "nivel_riesgo": {"nivel": nivel, "categoria": categoria,
                         "qs_mj": round(qs_mj, 2), "qs_mcal": round(qs_mcal, 2)},
        "sectorizacion": sector,
        "requisitos": requisitos,
        "evacuacion": evacuacion,
        "ambito": ambito,
        "uso_cte": sec.get("uso_cte"),
        "locales_riesgo_especial": locales_re,
        "dbsi": dbsi_res,
        "observaciones": observaciones,
        "estado": estado,
    }


def _build_superficies(sectores, dependencias):
    sec_name = {s.get("id"): s.get("nombre", "Sector") for s in sectores}
    filas = []
    tot_util = tot_const = 0.0
    for d in dependencias:
        u = float(d.get("sup_util") or 0)
        c = float(d.get("sup_construida") or 0)
        tot_util += u
        tot_const += c
        filas.append({"nombre": d.get("nombre", "-"), "planta": d.get("planta", "-"),
                      "sector": sec_name.get(d.get("sector_id"), "-"),
                      "sup_util": round(u, 2), "sup_construida": round(c, 2)})
    return {"filas": filas, "total_util": round(tot_util, 2), "total_construida": round(tot_const, 2)}


def _build_ocupacion(sectores, dependencias):
    sec_name = {s.get("id"): s.get("nombre", "Sector") for s in sectores}
    filas = []
    total = 0
    for d in dependencias:
        o = _dep_ocupacion(d)
        sup = float(d.get("sup_util") or d.get("sup_construida") or 0)
        dens = d.get("densidad")
        if o:
            total += o
        filas.append({"nombre": d.get("nombre", "-"),
                      "sector": sec_name.get(d.get("sector_id"), "-"),
                      "uso": d.get("uso_ocupacion", "-"),
                      "superficie": round(sup, 2),
                      "densidad": ("Sin ocupación" if d.get("sin_ocupacion") else (f"{dens} m²/p" if dens else "-")),
                      "ocupacion": o if o is not None else "-"})
    return {"filas": filas, "total": total}


def _build_resumen(sector_results):
    filas = []
    for s in sector_results:
        sec = s["sectorizacion"]
        filas.append({
            "nombre": s["nombre"],
            "tipo": "Área exterior" if s["tipo"] == "area_exterior" else "Sector",
            "config": s["config_label"],
            "superficie": s["calculo"]["A"],
            "qs_mj": s["nivel_riesgo"]["qs_mj"],
            "nivel": s["nivel_riesgo"]["nivel"],
            "categoria": s["nivel_riesgo"]["categoria"],
            "max_admisible": sec.get("max_admisible"),
            "max_admisible_base": sec.get("max_admisible_base"),
            "estabilidad": (s["requisitos"].get("estabilidad") or {}).get("valor", "-"),
            "ocupacion": s["ocupacion"],
            "estado": s["estado"],
        })
    return filas


def compute(data: dict) -> dict:
    establecimiento = dict(data.get("establecimiento") or {})
    sectores = data.get("sectores") or []
    dependencias = data.get("dependencias") or []

    errors = _validate(sectores, dependencias)
    if errors:
        raise ValueError(" ".join(errors))

    establecimiento["_all_deps"] = dependencias
    sector_results = []
    for sec in sectores:
        deps = [d for d in dependencias if d.get("sector_id") == sec.get("id")]
        sector_results.append(_compute_sector(sec, deps, establecimiento))

    superficies = _build_superficies(sectores, dependencias)
    ocupacion = _build_ocupacion(sectores, dependencias)
    resumen = _build_resumen(sector_results)

    from normative_modules.rsciei.tablas import build_tablas
    tablas = build_tablas(data, sector_results)

    observaciones = []
    for s in sector_results:
        observaciones.extend(s["observaciones"])

    if any(s["estado"] == "no_cumple" for s in sector_results):
        estado_global = "no_cumple"
    elif any(s["estado"] == "observaciones" for s in sector_results):
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    return {
        "establecimiento": {"actividad": establecimiento.get("actividad", "-"),
                            "config": establecimiento.get("config", "-")},
        "superficies": superficies,
        "ocupacion": ocupacion,
        "sectores": sector_results,
        "resumen_sectores": resumen,
        "tablas": tablas,
        "observaciones": observaciones,
        "estado_global": estado_global,
    }
