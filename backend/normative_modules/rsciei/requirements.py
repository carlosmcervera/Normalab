"""Motor de requisitos RSCIEI (Anexo II construcción + Anexo III instalaciones).

Valores según la Guía de aplicación del RSCIEI 2025 (RD 164/2025). Determina la
estabilidad al fuego exigida, la resistencia de los elementos delimitadores del
sector y las instalaciones de protección obligatorias, incluido el hidrante para
llenado de camiones de bomberos (Tabla 3.3.1).
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

# --- Anexo III · umbrales de superficie (m²) por instalación ----------------

DETECCION = {
    "produccion": {"AV": {"any": 300}, "AH": {"any": 300},
                   "B": {"BAJO": 3000, "MEDIO": 2000, "ALTO": 1000},
                   "C": {"BAJO": 4000, "MEDIO": 3000, "ALTO": 2000}},
    "almacenamiento": {"AV": {"any": 150}, "AH": {"any": 150},
                       "B": {"BAJO": 1500, "MEDIO": 1000, "ALTO": 500},
                       "C": {"BAJO": 3000, "MEDIO": 1500, "ALTO": 800}},
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

# Hidrantes de impulsión directa: riesgo alto ≥2500, riesgo medio ≥3500
HIDRANTES = {"AH": {"MEDIO": 3500, "ALTO": 2500}, "B": {"MEDIO": 3500, "ALTO": 2500},
             "C": {"MEDIO": 3500, "ALTO": 2500}, "D": {"MEDIO": 10000, "ALTO": 10000}}

# Tabla 3.3.1 · Hidrante para llenado de camiones de bomberos.
# Superficie total construida del establecimiento (m²) a partir de la cual es
# obligatorio disponer de un hidrante exterior accesible (a < 100 m).
HIDRANTE_CAMION = {"AV": 1000, "AH": 2500, "B": 3500, "C": 5000, "D": 15000}


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
        estabilidad = {"valor": val, "detalle": f"Estructura portante · {('planta bajo rasante' if sit_key=='bajo' else 'planta sobre rasante')} · Tabla 2.5.1."}
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
    if humo_thr is not None:
        inst.append(_inst("Control de humos y calor", A >= humo_thr,
                          f"Actividad de {modo_label}, riesgo {categoria}: obligatorio si superficie ≥ {humo_thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Control de humos y calor", False, "No exigible en riesgo bajo (valorar huecos de ventilación)."))

    hid_thr = HIDRANTES.get(config, {}).get(categoria) if categoria in ("MEDIO", "ALTO") else None
    if hid_thr is not None:
        inst.append(_inst("Hidrantes exteriores (impulsión directa)", A >= hid_thr,
                          f"Tipo {config}, riesgo {categoria}: obligatorios si superficie del sector ≥ {hid_thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Hidrantes exteriores (impulsión directa)", False,
                          "No exigibles por superficie en riesgo bajo."))

    # Tabla 3.3.1 · hidrante para llenado de camiones de bomberos
    cam_thr = HIDRANTE_CAMION.get(config, 5000)
    cam_obl = S_est >= cam_thr
    inst.append(_inst("Hidrante para llenado de camiones de bomberos", cam_obl,
                      f"Tabla 3.3.1: obligatorio un hidrante exterior accesible (a < 100 m) si la superficie total "
                      f"del establecimiento (tipo {config}) ≥ {cam_thr:.0f} m² (total: {S_est:.0f} m²)."))

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
