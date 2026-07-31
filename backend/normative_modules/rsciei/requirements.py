"""Motor de requisitos RSCIEI (Anexo II construcción + Anexo III instalaciones).

Valores según la Guía de aplicación del RSCIEI 2025 (RD 164/2025). Determina la
estabilidad al fuego exigida, la resistencia de los elementos delimitadores del
sector y las instalaciones de protección obligatorias, incluidos los hidrantes
exteriores (Tabla 3.3.1) y el sistema de comunicación de alarma.
"""

# --- Anexo II ---------------------------------------------------------------

# Estabilidad al fuego (R) de la estructura portante por configuración y situación
ESTABILIDAD = {
    "AV": {"sobre": {"BAJO": "R 90", "MEDIO": "R 120", "ALTO": "NO ADMITIDO"},
           "bajo": {"BAJO": "R 120", "MEDIO": "NO ADMITIDO", "ALTO": "NO ADMITIDO"}},
    "AH": {"sobre": {"BAJO": "R 90", "MEDIO": "R 120", "ALTO": "R 180"},
           "bajo": {"BAJO": "R 120", "MEDIO": "R 180", "ALTO": "NO ADMITIDO"}},
    "B": {"sobre": {"BAJO": "R 60", "MEDIO": "R 90", "ALTO": "R 120"},
          "bajo": {"BAJO": "R 90", "MEDIO": "R 120", "ALTO": "R 180"}},
    "C": {"sobre": {"BAJO": "R 30", "MEDIO": "R 60", "ALTO": "R 90"},
          "bajo": {"BAJO": "R 60", "MEDIO": "R 90", "ALTO": "R 120"}},
}

DELIMITADORES = {"BAJO": "EI 120", "MEDIO": "EI 180", "ALTO": "EI 240"}

# Escala de estabilidad al fuego (R) para modular por altura de evacuación (Anexo II, Tabla 2.2):
# en plantas sobre rasante la R exigida sube un escalón para 15 < h ≤ 28 m y dos para h > 28 m.
_ESCALA_R = ["R 30", "R 60", "R 90", "R 120", "R 180", "R 240"]


def _modular_r_por_altura(valor: str, h_evac: float):
    if valor not in _ESCALA_R:
        return valor, 0
    bump = 2 if h_evac > 28 else (1 if h_evac > 15 else 0)
    if bump == 0:
        return valor, 0
    idx = min(_ESCALA_R.index(valor) + bump, len(_ESCALA_R) - 1)
    return _ESCALA_R[idx], bump

# --- Anexo III · umbrales de superficie (m²) por instalación ----------------

DETECCION = {
    "produccion": {"AV": {"any": 300}, "AH": {"any": 300},
                   "B": {"BAJO": 3000, "MEDIO": 2000, "ALTO": 1000},
                   "C": {"BAJO": 4000, "MEDIO": 3000, "ALTO": 2000}},
    "almacenamiento": {"AV": {"any": 150}, "AH": {"any": 150},
                       "B": {"BAJO": 1500, "MEDIO": 1000, "ALTO": 500},
                       "C": {"BAJO": 3000, "MEDIO": 1500, "ALTO": 800},
                       "D": {"ALTO": 5000}},
}

BIE = {"AV": {"BAJO": 300, "MEDIO": 300, "ALTO": 300},
       "AH": {"MEDIO": 500, "ALTO": 200}, "B": {"MEDIO": 500, "ALTO": 200},
       "C": {"MEDIO": 1000, "ALTO": 500}, "D": {"ALTO": 5000}}

ROCIADORES = {
    "produccion": {"AV": {"MEDIO": 500}, "AH": {"MEDIO": 1500, "ALTO": 750},
                   "B": {"MEDIO": 2500, "ALTO": 1000}, "C": {"MEDIO": 3500, "ALTO": 2000}},
    "almacenamiento": {"AV": {"MEDIO": 300, "ALTO": 300}, "AH": {"MEDIO": 1000, "ALTO": 600},
                       "B": {"MEDIO": 1500, "ALTO": 800}, "C": {"MEDIO": 2000, "ALTO": 1000}},
}

HUMOS = {"produccion": {"MEDIO": 2000, "ALTO": 1000},
         "almacenamiento": {"MEDIO": 1000, "ALTO": 800}}

# Anexo III · 8.4 · Sistemas de evacuación (control) de humos: superficie aerodinámica
# de evacuación de humos = 0,5 m² por cada N m² de superficie construida del sector,
# según el modo de la actividad y la situación de la planta (sobre/bajo rasante).
# Fabricación/producción: 0,5 / 200 m² (sobre) · 0,5 / 150 m² (bajo).
# Almacenamiento:         0,5 / 150 m² (sobre) · 0,5 / 100 m² (bajo).
HUMOS_AERODINAMICO = {
    "produccion": {"sobre": 200.0, "bajo": 150.0},
    "almacenamiento": {"sobre": 150.0, "bajo": 100.0},
}


def _superficie_aerodinamica_humos(modo_pred: str, sit_key: str, A: float) -> dict:
    modo = "almacenamiento" if modo_pred == "almacenamiento" else "produccion"
    denom = HUMOS_AERODINAMICO[modo]["bajo" if sit_key == "bajo" else "sobre"]
    superficie = round(0.5 * (A / denom), 2) if A > 0 else 0.0
    sit_txt = "planta bajo rasante" if sit_key == "bajo" else "planta sobre rasante"
    modo_txt = "almacenamiento" if modo == "almacenamiento" else "fabricación/producción"
    return {
        "modo": modo,
        "situacion": "bajo_rasante" if sit_key == "bajo" else "sobre_rasante",
        "ratio_m2": denom,
        "superficie_construida": round(A, 2),
        "superficie_aerodinamica": superficie,
        "detalle": (f"Superficie aerodinámica de evacuación de humos ≥ {superficie:.2f} m² "
                    f"= 0,5 m² × ({A:.0f} m² / {denom:.0f} m²), para actividad de {modo_txt} en "
                    f"{sit_txt} (RSCIEI, Anexo III, punto 8.4)."),
    }

# Tabla 3.3.1 · Hidrantes exteriores (RSCIEI, Anexo III). Obligatorios si la superficie
# del sector/área de incendio ≥ umbral (m²), en función de la configuración y del nivel
# de riesgo intrínseco. La exigencia es más estricta (umbral menor) a mayor riesgo.
# Tipo A: no se exige en riesgo bajo nivel 1 (nota *). Tipo C: no exigible en riesgo bajo.
HIDRANTES = {
    "AV": {"BAJO": 1000, "MEDIO": 300},
    "AH": {"BAJO": 1000, "MEDIO": 300},
    "B": {"BAJO": 3500, "MEDIO": 2500, "ALTO": 1000},
    "C": {"MEDIO": 3500, "ALTO": 2000},
    "D": {"BAJO": 5000, "MEDIO": 5000, "ALTO": 5000},
}

# Sistema de comunicación de alarma (Anexo III, punto 5.1): obligatorio si la superficie
# construida total de los sectores del establecimiento ≥ 10.000 m² (megafonía preferente).
COMUNICACION_ALARMA_MIN = 10000


def _threshold(table, config, categoria, nivel):
    cfg = table.get(config)
    if cfg is None:
        return None
    if "any" in cfg:
        if categoria == "BAJO" and nivel == 1:
            return None
        return cfg["any"]
    if categoria == "BAJO" and nivel == 1:
        return None
    return cfg.get(categoria)


def _inst(nombre, obligatorio, detalle):
    return {"nombre": nombre, "obligatorio": obligatorio, "detalle": detalle}


def build_requirements(sec: dict, nivel: int, categoria: str, modo_pred: str,
                       A: float, total_est: float) -> dict:
    config = sec.get("config", "B")
    situacion = sec.get("situacion", "sobre_rasante")
    sit_key = "bajo" if situacion == "bajo_rasante" else "sobre"
    A = float(A or 0)
    S_est = float(total_est or 0) or A
    h_evac = float(sec.get("altura_evacuacion") or 0)
    cubierta_ligera = bool(sec.get("cubierta_ligera"))
    rociadores_previstos = bool(sec.get("rociadores"))

    if config == "D":
        estabilidad = {"valor": "No exigible", "detalle": "Configuración tipo D (espacio abierto): estabilidad al fuego no exigible con carácter general."}
    else:
        val = ESTABILIDAD[config][sit_key][categoria]
        sit_txt = "planta bajo rasante" if sit_key == "bajo" else "planta sobre rasante"
        estabilidad = {"valor": val,
                       "detalle": f"Estructura portante · {sit_txt} · riesgo {categoria.lower()} · Anexo II, Tabla 2.5.1."}
        # Reducción por instalación fija de extinción automática (rociadores) que cubre todo el
        # sector (RSCIEI RD 164/2025, Anexo II, Sección 5): la estabilidad exigida se reduce un grado.
        if rociadores_previstos and val in _ESCALA_R:
            idx = _ESCALA_R.index(val)
            if idx > 0:
                val_red = _ESCALA_R[idx - 1]
                estabilidad = {
                    "valor": val_red,
                    "valor_base": val,
                    "reduccion_rociadores": True,
                    "detalle": (f"Estructura portante · {sit_txt} · riesgo {categoria.lower()} · Anexo II, "
                                f"Tabla 2.5.1: valor base {val}. Reducido un grado a {val_red} por disponer de "
                                f"instalación fija automática de extinción (rociadores) que protege todo el "
                                f"sector (Anexo II, Sección 5, RD 164/2025)."),
                }
    cubierta = {"valor": "R 15", "aplica": cubierta_ligera,
                "detalle": "Cubierta ligera no prevista para evacuación y con carga permanente < 100 kg/m²."} if cubierta_ligera else None

    delimitadores = {"valor": DELIMITADORES.get(categoria, "EI 120"),
                     "detalle": "Paredes y techos delimitadores del sector. Puertas de paso: EI de la mitad del elemento atravesado (orientativo)."}

    modo_label = "almacenamiento" if modo_pred == "almacenamiento" else "producción/fabricación"
    inst = []

    inst.append(_inst("Extintores portátiles", True, "Obligatorios en todos los sectores de incendio (salvo almacenamientos automáticos sin acceso de personas)."))
    inst.append(_inst("Sistema manual de alarma (pulsadores)", A >= 400,
                      f"Obligatorio en sectores con superficie ≥ 400 m² (sector: {A:.0f} m²)."))

    thr = _threshold(DETECCION[modo_pred], config, categoria, nivel)
    if thr is not None:
        inst.append(_inst("Detección automática de incendio", A >= thr,
                          f"Actividad de {modo_label}, tipo {config}, riesgo {categoria}: obligatoria si superficie ≥ {thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Detección automática de incendio", False,
                          "No exigible por superficie para esta configuración/nivel (riesgo bajo nivel 1 exento)."))

    bie_thr = _threshold(BIE, config, categoria, nivel) if config in BIE else None
    if bie_thr is not None:
        inst.append(_inst("Bocas de incendio equipadas (BIE)", A >= bie_thr,
                          f"Tipo {config}, riesgo {categoria}: obligatorias si superficie ≥ {bie_thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Bocas de incendio equipadas (BIE)", False,
                          "No exigibles por superficie para esta configuración/nivel."))

    roc_thr = _threshold(ROCIADORES[modo_pred], config, categoria, nivel)
    if roc_thr is not None:
        obl = A >= roc_thr
        det = f"Actividad de {modo_label}, tipo {config}, riesgo {categoria}: obligatorios si superficie ≥ {roc_thr:.0f} m² (sector: {A:.0f} m²)."
        if obl and rociadores_previstos:
            det += " Ya previstos en el estudio."
        inst.append(_inst("Rociadores automáticos de agua", obl, det))
    else:
        inst.append(_inst("Rociadores automáticos de agua", False,
                          "No exigibles por superficie para esta configuración/nivel (riesgo bajo)."))

    humo_thr = HUMOS[modo_pred].get(categoria) if categoria in ("MEDIO", "ALTO") else None
    aero = _superficie_aerodinamica_humos(modo_pred, sit_key, A)
    # Superficie de ventilación proyectada por el técnico (m²) → aviso si no alcanza la aerodinámica exigida (8.4).
    try:
        proy_vent = float(sec.get("humos_ventilacion_proyectada")) if sec.get("humos_ventilacion_proyectada") not in (None, "") else None
    except (TypeError, ValueError):
        proy_vent = None
    if proy_vent is not None:
        aero["proyectada"] = round(proy_vent, 2)
        aero["cumple"] = proy_vent + 1e-6 >= aero["superficie_aerodinamica"]
    if humo_thr is not None:
        humo_inst = _inst("Control de humos y calor", A >= humo_thr,
                          f"Actividad de {modo_label}, riesgo {categoria}: obligatorio si superficie ≥ {humo_thr:.0f} m² "
                          f"(sector: {A:.0f} m²). {aero['detalle']}")
    else:
        humo_inst = _inst("Control de humos y calor", False,
                          f"No exigible con carácter general en riesgo bajo (valorar huecos de ventilación). {aero['detalle']}")
    if aero.get("proyectada") is not None:
        if aero.get("cumple"):
            humo_inst["detalle"] += (f" Ventilación proyectada {aero['proyectada']:.2f} m² ≥ exigida "
                                     f"{aero['superficie_aerodinamica']:.2f} m²: suficiente.")
        else:
            humo_inst["detalle"] += (f" AVISO: ventilación proyectada {aero['proyectada']:.2f} m² < exigida "
                                     f"{aero['superficie_aerodinamica']:.2f} m²: insuficiente para la evacuación de humos (8.4).")
    humo_inst["superficie_aerodinamica"] = aero
    inst.append(humo_inst)

    hid_thr = _threshold(HIDRANTES, config, categoria, nivel)
    if hid_thr is not None:
        inst.append(_inst("Hidrantes exteriores (Tabla 3.3.1)", A >= hid_thr,
                          f"Tabla 3.3.1: obligatorios si la superficie del sector (tipo {config}, riesgo {categoria.lower()}) "
                          f"≥ {hid_thr:.0f} m² (sector: {A:.0f} m²). Al menos un hidrante con salida de 100 mm; radio de "
                          f"cobertura 40 m y ≥ 5 m al límite del edificio."))
    else:
        inst.append(_inst("Hidrantes exteriores (Tabla 3.3.1)", False,
                          f"No exigibles por superficie para el tipo {config} en riesgo {categoria.lower()}."))

    # Sistema de comunicación de alarma (Anexo III, punto 5.1)
    inst.append(_inst("Sistema de comunicación de alarma", S_est >= COMUNICACION_ALARMA_MIN,
                      f"Obligatorio si la superficie construida total de los sectores ≥ {COMUNICACION_ALARMA_MIN:.0f} m² "
                      f"(megafonía preferente; diferencia emergencia parcial/general). Total: {S_est:.0f} m²."))

    cs_obl = h_evac >= 15
    inst.append(_inst("Columna seca", cs_obl,
                      f"Obligatoria si la altura de evacuación ≥ 15 m (altura declarada: {h_evac:.1f} m)."))
    inst.append(_inst("Alumbrado de emergencia", True, "Según sección 4 del DB-SUA del CTE."))
    inst.append(_inst("Señalización de medios manuales", True, "Señalización de extintores, pulsadores, BIE e hidrantes (RIPCI / DB-SI)."))

    return {
        "config": config,
        "situacion": situacion,
        "modo_predominante": modo_pred,
        "estabilidad": estabilidad,
        "cubierta_ligera": cubierta,
        "delimitadores": delimitadores,
        "instalaciones": inst,
    }
