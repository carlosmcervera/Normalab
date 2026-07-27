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

ESC_TIPO_LABEL = {
    "abierta": "abierta", "protegida": "protegida",
    "especialmente_protegida": "especialmente protegida", "compartimentada": "compartimentada",
}

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
            if d.get("clase") in ("escalera", "escalera_protegida", "lre") or d.get("es_lre"):
                continue
            nombre = d.get("nombre") or "Dependencia"
            if not d.get("ci") or float(d.get("ci") or 0) <= 0:
                errors.append(f"«{nombre}»: defina el coeficiente Ci (carga de fuego).")
            if d.get("modo") == "deposito":
                if not d.get("pci") or float(d.get("pci") or 0) <= 0:
                    errors.append(f"«{nombre}»: el PCI (MJ/kg) del combustible debe ser mayor que 0.")
                if not d.get("dens_comb") or float(d.get("dens_comb") or 0) <= 0:
                    errors.append(f"«{nombre}»: la densidad del combustible (kg/m³) debe ser mayor que 0.")
                if not d.get("volumen") or float(d.get("volumen") or 0) <= 0:
                    errors.append(f"«{nombre}»: el volumen del depósito (m³) debe ser mayor que 0.")
            elif d.get("modo") == "almacenamiento":
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
    man = d.get("ocupacion_manual")
    if d.get("ocupacion_custom") and man not in (None, ""):
        try:
            return int(math.ceil(float(man)))
        except (TypeError, ValueError):
            pass
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


# --- Construcción y propagación exterior (RSCIEI Anexo II · CTE DB-SI SI-2) --- #
# Tabla 2.1.4 · Clases de reacción al fuego de los elementos constructivos.
REACCION_2_1_4 = [
    {"situacion": "Zonas ocupables, en general", "techos_paredes": "C-s2,d0", "suelos": "CFL-s1"},
    {"situacion": "Pasillos y escaleras protegidos", "techos_paredes": "B-s1,d0", "suelos": "CFL-s1"},
    {"situacion": "Aparcamientos y sectores de riesgo intrínseco alto", "techos_paredes": "B-s1,d0", "suelos": "BFL-s1"},
    {"situacion": "Espacios ocultos no estancos (patinillos, falsos techos, suelos elevados)",
     "techos_paredes": "B-s3,d0", "suelos": "BFL-s2"},
]
# Tabla 2.2.1 · Resistencia al fuego de elementos separadores con otros establecimientos.
MEDIANERA_EI = {"BAJO": "EI 120", "MEDIO": "EI 180", "ALTO": "EI 240"}
# Tabla 2.2.2 · distancia «d» (m) de la franja de fachada según el ángulo α.
FACHADA_D = {"90": 2.0, "135": 1.5, "180": 1.0}


def _parse_ei(valor):
    """Extrae los minutos de un texto tipo «EI 240» / «REI 180»."""
    if not valor:
        return None
    import re
    m = re.search(r"(\d+)", str(valor))
    return int(m.group(1)) if m else None


def _ei_ok(proyectado, requerido):
    p, r = _parse_ei(proyectado), _parse_ei(requerido)
    if p is None:
        return "pendiente"
    if r is None:
        return "cumple"
    return "cumple" if p >= r else "no_cumple"


def _construccion(sec, categoria, delim_valor, ambito="industrial"):
    """Reacción al fuego (Tabla 2.1.4), medianeras (Tabla 2.2.1) y fachadas (Tabla 2.2.2)."""
    out = {
        "ambito": ambito,
        "reaccion": {
            "tabla": REACCION_2_1_4,
            "nri_alto": categoria == "ALTO",
            "cumple": bool(sec.get("reaccion_cumple")),
            "observaciones": sec.get("reaccion_obs") or "",
        },
        "medianeras": None,
        "fachadas": None,
        "cubierta": {"ligera": bool(sec.get("cubierta_ligera")), "observaciones": sec.get("cubierta_obs") or ""},
    }
    if sec.get("medianera_otro"):
        req = MEDIANERA_EI.get(categoria, "EI 120")
        proy = sec.get("medianera_ei") or ""
        out["medianeras"] = {"aplica": True, "requerido": req, "proyectado": proy,
                             "estado": _ei_ok(proy, req),
                             "nota": ("Reducible a EI 120 en config. tipo B con muros a ≤ 3 m (nota 4, "
                                      "Tabla 2.2.1); sin exigencia si la separación es > 3 m libre de carga.")}
    if sec.get("fachada_encuentro"):
        ang = str(sec.get("fachada_angulo") or "180")
        d = FACHADA_D.get(ang, 1.0)
        delim = _parse_ei(delim_valor)
        req_min = max(15, delim // 2) if delim else None
        req_txt = f"EI {req_min}" if req_min else "—"
        proy = sec.get("fachada_ei") or ""
        out["fachadas"] = {"aplica": True, "angulo": ang, "distancia_d": d,
                           "requerido": req_txt, "proyectado": proy, "estado": _ei_ok(proy, req_txt),
                           "nota": ("La fachada donde acomete un elemento compartimentador debe ser ≥ 50% "
                                    "de su EI en una franja; puntos por debajo, separados ≥ d en proyección "
                                    "horizontal (d = 3 − α/90).")}
    return out



def _compute_sector(sec, deps, establecimiento):
    config = _sector_config(sec, establecimiento)
    situacion = sec.get("situacion", "sobre_rasante")
    # Las ESCALERAS y los LOCALES DE RIESGO ESPECIAL (LRE) no computan carga de fuego:
    # se excluyen del Qs y se evalúan aparte por el CTE DB-SI (escaleras: SI-3/SUA;
    # LRE: Tabla 2.1). El resto de dependencias sí computan.
    esc_deps = [d for d in deps if d.get("clase") in ("escalera", "escalera_protegida")]
    lre_deps = [d for d in deps if d.get("es_lre") or d.get("clase") == "lre"]
    calc_deps = [d for d in deps if d.get("clase") not in ("escalera", "escalera_protegida")
                 and not (d.get("es_lre") or d.get("clase") == "lre")]
    # Superficie construida (Tabla 2.1.1 · superficie máx. admisible del sector) y
    # superficie útil (denominador de la carga de fuego Qs, según criterio del despacho).
    A_const = sum(float(d.get("sup_construida") or 0) for d in calc_deps)
    A_util = sum(float(d.get("sup_util") or d.get("sup_construida") or 0) for d in calc_deps)

    detalle_zonas = []
    depositos = []
    numerador = 0.0
    rmins, used_ci, ras = [], [], []
    for d in calc_deps:
        ci = float(d.get("ci") or 0)
        s = float(d.get("sup_util") or d.get("sup_construida") or 0)
        modo = d.get("modo")
        if modo == "deposito":
            pci = float(d.get("pci") or 0)
            dens = float(d.get("dens_comb") or 0)
            vol = float(d.get("volumen") or 0)
            aporte = pci * dens * vol * ci
            comb = d.get("combustible") or "combustible"
            detalle_zonas.append({"descripcion": d.get("nombre", "Depósito"), "modo": "deposito",
                                  "combustible": comb, "pci": pci, "dens_comb": dens, "volumen": vol,
                                  "ci": ci, "superficie": round(s, 2), "aporte": round(aporte, 2)})
            depositos.append({
                "sector": sec.get("nombre", "Sector"),
                "nombre": d.get("nombre", "Depósito"), "combustible": comb,
                "pci": pci, "dens_comb": dens, "volumen": vol, "ci": ci, "aporte": round(aporte, 2),
                "justificacion": (
                    f"El depósito «{d.get('nombre', 'Depósito')}» ({comb}) se clasifica como "
                    f"almacenamiento de combustible. Su carga de fuego se determina por el volumen "
                    f"almacenado: Q = PCI × densidad × volumen × Ci = {pci:g} MJ/kg × {dens:g} kg/m³ × "
                    f"{vol:g} m³ × {ci:g} = {aporte:,.0f} MJ, que se incorpora al sumatorio de carga de "
                    f"fuego del sector «{sec.get('nombre', 'Sector')}»."),
            })
        elif modo == "almacenamiento":
            qvi = float(d.get("qvi") or 0)
            hi = float(d.get("hi") or 0)
            aporte = qvi * ci * hi * s
            detalle_zonas.append({"descripcion": d.get("nombre", "Zona"), "modo": "almacenamiento",
                                  "qvi": qvi, "hi": hi, "ci": ci, "superficie": round(s, 2), "aporte": round(aporte, 2)})
        else:
            qsi = float(d.get("qsi") or 0)
            aporte = qsi * ci * s
            detalle_zonas.append({"descripcion": d.get("nombre", "Zona"), "modo": "produccion",
                                  "qsi": qsi, "ci": ci, "superficie": round(s, 2), "aporte": round(aporte, 2)})
        numerador += aporte
        used_ci.append(ci)
        ras.append(float(d.get("ra") or 1.0))
        if d.get("rmin"):
            rmins.append(float(d["rmin"]))

    ra_auto = max(ras) if ras else 1.0
    ra = float(sec.get("ra") or ra_auto)
    rmin_req = max(rmins) if rmins else None

    qs_mj = (numerador / A_util) * ra if A_util > 0 else 0.0
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

    sector = _sectorizacion(config, nivel, A_const, factor, factores, situacion)

    sup_alm = sum(float(d.get("sup_construida") or 0) for d in calc_deps if d.get("modo") in ("almacenamiento", "deposito"))
    sup_prod = A_const - sup_alm
    modo_pred = "almacenamiento" if sup_alm > sup_prod else "produccion"

    ocupacion_sector = 0
    for d in deps:
        o = _dep_ocupacion(d)
        if o:
            ocupacion_sector += o

    total_est = sum(float(d.get("sup_construida") or 0) for d in establecimiento.get("_all_deps", []))
    req_sec = dict(sec)
    req_sec["config"] = config
    requisitos = build_requirements(req_sec, nivel, categoria, modo_pred, A_const, total_est)

    evacuacion = _evacuacion(sec, categoria, nivel, ocupacion_sector)

    delim_valor = (requisitos.get("delimitadores") or {}).get("valor")
    construccion = _construccion(sec, categoria, delim_valor, ambito=sec.get("ambito") or "industrial")

    # Locales de riesgo especial (LRE): NO computan carga de fuego (excluidos del Qs);
    # se clasifican y evalúan conforme al CTE DB-SI (Tabla 2.1) con su resistencia (R).
    locales_re = []
    for d in lre_deps:
        sup_lre = float(d.get("sup_construida") or d.get("sup_util") or 0)
        metric = d.get("lre_metric")
        volumen = round(sup_lre * float(d.get("lre_altura") or 0), 2) if metric == "V" and d.get("lre_altura") else None
        locales_re.append({
            "nombre": d.get("nombre", "Local de riesgo especial"),
            "superficie": round(sup_lre, 2),
            "riesgo": (d.get("lre_riesgo") or "bajo").upper(),
            "resistencia": d.get("lre_r") or "R 90",
            "actividad": d.get("lre_uso") or d.get("actividad_cat") or d.get("uso_ocupacion") or "-",
            "uso": d.get("lre_uso") or "",
            "uso_grupo": d.get("lre_uso_grupo") or "",
            "altura": d.get("lre_altura"),
            "volumen": volumen,
            "potencia": d.get("lre_potencia") if metric == "P" else None,
            "metric": metric or "",
            "criterio": d.get("lre_criterio") or "",
            "justificacion": d.get("lre_justificacion") or "",
        })

    # Escaleras: NO computan carga de fuego (zona de paso); requieren justificación
    # por el CTE DB-SI/SUA (protección, anchura, capacidad, situación…).
    escaleras = []
    for d in esc_deps:
        tipo = d.get("esc_tipo") or "protegida"
        sentido = "descendente" if tipo == "abierta" else (d.get("esc_sentido") or "descendente")
        escaleras.append({
            "nombre": d.get("nombre", "Escalera"),
            "tipo": tipo,
            "sentido": sentido,
            "situacion": d.get("esc_situacion") or "interior",
            "anchura": d.get("esc_anchura"),
            "capacidad": d.get("esc_capacidad"),
            "uso_restringido": bool(d.get("esc_uso_restringido")),
            "justificacion": d.get("esc_justificacion") or "",
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
                "superficie_construida": A_const or 1,
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
                                  "ocupacion_custom": d.get("ocupacion_custom"),
                                  "ocupacion_manual": d.get("ocupacion_manual"),
                                  "uso_ocupacion": d.get("uso_ocupacion")} for d in (calc_deps or deps)],
            })
        except ValueError:
            dbsi_res = None

    observaciones = []
    observaciones.append({"tipo": "info", "texto": f"Sector «{sec.get('nombre','?')}»: nivel de riesgo intrínseco {nivel} ({categoria}), Tabla 1.3.1."})
    if ambito == "cte":
        sector = {**sector, "estado": "no_aplica", "max_admisible": None,
                  "mensaje": ("Sector de ámbito CTE: no aplica la Tabla 2.1.1 del RSCIEI; la "
                              "compartimentación y las superficies se evalúan según el CTE DB-SI.")}
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
            f"Sector «{sec.get('nombre','?')}»: {len(locales_re)} local(es) de riesgo especial que NO computan en la carga de fuego del sector; se clasifican y evalúan conforme al CTE DB-SI (Tabla 2.1), con su resistencia (R).")})
        for l in locales_re:
            if l.get("justificacion"):
                observaciones.append({"tipo": "info", "texto": f"LRE «{l['nombre']}» (riesgo {l['riesgo'].lower()}, {l['resistencia']}): {l['justificacion']}"})
    for e in escaleras:
        tipo_txt = ESC_TIPO_LABEL.get(e["tipo"], "protegida")
        detalle = f"Escalera {tipo_txt} «{e['nombre']}» ({e['situacion']}, evacuación {e.get('sentido', 'descendente')}"
        if e.get("anchura"):
            detalle += f", anchura {e['anchura']} m"
        if e.get("capacidad"):
            detalle += f", capacidad {e['capacidad']} pers."
        if e["uso_restringido"]:
            detalle += ", uso restringido"
        detalle += f"): NO computa carga de fuego (zona de paso). Justificación CTE DB-SI/SUA: {e['justificacion'] or 'pendiente de justificar'}."
        observaciones.append({"tipo": "info" if e["justificacion"] else "warning", "texto": detalle})

    for dep in depositos:
        observaciones.append({"tipo": "info", "texto": (
            f"Sector «{sec.get('nombre','?')}»: {dep['justificacion']}")})

    med = construccion.get("medianeras")
    if med and med.get("estado") == "no_cumple":
        observaciones.append({"tipo": "error", "texto": (
            f"Sector «{sec.get('nombre','?')}»: la medianería/separación proyectada ({med['proyectado'] or '—'}) es inferior a la exigida ({med['requerido']}) por la Tabla 2.2.1 del RSCIEI.")})
    fach = construccion.get("fachadas")
    if fach and fach.get("estado") == "no_cumple":
        observaciones.append({"tipo": "error", "texto": (
            f"Sector «{sec.get('nombre','?')}»: la fachada en el encuentro del elemento compartimentador ({fach['proyectado'] or '—'}) no alcanza el mínimo exigido ({fach['requerido']}, franja con d = {fach['distancia_d']} m).")})
    if not construccion["reaccion"].get("cumple"):
        observaciones.append({"tipo": "advertencia", "texto": (
            f"Sector «{sec.get('nombre','?')}»: verificar/justificar las clases de reacción al fuego de los revestimientos (Tabla 2.1.4).")})

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
        "calculo": {"numerador": round(numerador, 2), "A": round(A_util, 2), "A_construida": round(A_const, 2),
                    "ra": ra, "qs_mj": round(qs_mj, 2), "qs_mcal": round(qs_mcal, 2), "zonas": detalle_zonas},
        "nivel_riesgo": {"nivel": nivel, "categoria": categoria,
                         "qs_mj": round(qs_mj, 2), "qs_mcal": round(qs_mcal, 2)},
        "sectorizacion": sector,
        "requisitos": requisitos,
        "evacuacion": evacuacion,
        "construccion": construccion,
        "ambito": ambito,
        "uso_cte": sec.get("uso_cte"),
        "locales_riesgo_especial": locales_re,
        "escaleras_protegidas": escaleras,
        "dbsi": dbsi_res,
        "depositos": depositos,
        "observaciones": observaciones,
        "estado": estado,
    }


def _build_superficies(sectores, dependencias):
    sec_name = {s.get("id"): s.get("nombre", "Sector") for s in sectores}
    filas = []
    grupos = {}
    orden = []
    tot_util = tot_const = 0.0
    for d in dependencias:
        u = float(d.get("sup_util") or 0)
        c = float(d.get("sup_construida") or 0)
        tot_util += u
        tot_const += c
        planta = (d.get("planta") or "").strip() or "Sin planta"
        fila = {"nombre": d.get("nombre", "-"), "planta": planta,
                "sector": sec_name.get(d.get("sector_id"), "-"),
                "sup_util": round(u, 2), "sup_construida": round(c, 2)}
        filas.append(fila)
        if planta not in grupos:
            grupos[planta] = {"planta": planta, "filas": [], "sub_util": 0.0, "sub_construida": 0.0}
            orden.append(planta)
        g = grupos[planta]
        g["filas"].append(fila)
        g["sub_util"] += u
        g["sub_construida"] += c
    for g in grupos.values():
        g["sub_util"] = round(g["sub_util"], 2)
        g["sub_construida"] = round(g["sub_construida"], 2)
    return {"filas": filas, "grupos": [grupos[p] for p in orden],
            "total_util": round(tot_util, 2), "total_construida": round(tot_const, 2)}


def _build_ocupacion(sectores, dependencias):
    sec_name = {s.get("id"): s.get("nombre", "Sector") for s in sectores}
    filas = []
    total = 0
    por_planta = {}
    orden_p = []
    for d in dependencias:
        o = _dep_ocupacion(d)
        sup = float(d.get("sup_util") or d.get("sup_construida") or 0)
        dens = d.get("densidad")
        if o:
            total += o
        planta = (d.get("planta") or "").strip() or "Sin planta"
        if planta not in por_planta:
            por_planta[planta] = 0
            orden_p.append(planta)
        if o:
            por_planta[planta] += o
        manual = bool(d.get("ocupacion_custom")) and d.get("ocupacion_manual") not in (None, "")
        densidad_label = ("Sin ocupación" if d.get("sin_ocupacion")
                          else ("Manual" if manual else (f"{dens} m²/p" if dens else "-")))
        filas.append({"nombre": d.get("nombre", "-"),
                      "planta": planta,
                      "sector": sec_name.get(d.get("sector_id"), "-"),
                      "uso": d.get("uso_ocupacion", "-"),
                      "superficie": round(sup, 2),
                      "densidad": densidad_label,
                      "nota": (d.get("ocupacion_nota") or "").strip() if manual else "",
                      "ocupacion": o if o is not None else "-"})
    return {"filas": filas, "total": total,
            "por_planta": [{"planta": p, "ocupacion": por_planta[p]} for p in orden_p]}


def _build_resumen(sector_results):
    filas = []
    for s in sector_results:
        sec = s["sectorizacion"]
        filas.append({
            "nombre": s["nombre"],
            "tipo": "Área exterior" if s["tipo"] == "area_exterior" else "Sector",
            "config": "—" if s.get("ambito") == "cte" else s["config_label"],
            "superficie": s["sectorizacion"].get("superficie_sector", s["calculo"]["A"]),
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

    depositos = []
    for s in sector_results:
        depositos.extend(s.get("depositos", []))

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
        "depositos": depositos,
        "tablas": tablas,
        "observaciones": observaciones,
        "estado_global": estado_global,
    }
