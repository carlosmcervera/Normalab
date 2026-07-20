"""Motor de requisitos RSCIEI (Anexo II construcción + Anexo III instalaciones).

A partir de la configuración, el nivel de riesgo intrínseco y las superficies,
determina la estabilidad al fuego exigida, la resistencia de los elementos
delimitadores del sector y las instalaciones de protección obligatorias.
Valores orientativos según RD 2267/2004 (texto consolidado).
"""

# --- Anexo II ---------------------------------------------------------------

# Tabla 2.2 · Estabilidad al fuego (R) de la estructura portante
ESTABILIDAD = {
    "A": {"sobre": {"BAJO": "R 120", "MEDIO": "R 120", "ALTO": "NO ADMITIDO"},
          "bajo": {"BAJO": "R 90", "MEDIO": "R 180", "ALTO": "NO ADMITIDO"}},
    "B": {"sobre": {"BAJO": "R 120", "MEDIO": "R 180", "ALTO": "R 180"},
          "bajo": {"BAJO": "R 90", "MEDIO": "R 120", "ALTO": "R 120"}},
    "C": {"sobre": {"BAJO": "R 90", "MEDIO": "R 120", "ALTO": "R 120"},
          "bajo": {"BAJO": "R 60", "MEDIO": "R 90", "ALTO": "R 120"}},
}

# Tabla 2.3 · Resistencia al fuego (EI) de elementos delimitadores del sector
DELIMITADORES = {"BAJO": "EI 120", "MEDIO": "EI 180", "ALTO": "EI 240"}

# --- Anexo III · umbrales de superficie (m²) por instalación ----------------
# threshold = superficie a partir de la cual es obligatoria; None = no exigible

DETECCION = {
    "produccion": {"AV": {"any": 300}, "AH": {"any": 300},
                   "B": {"MEDIO": 2000, "ALTO": 1000, "BAJO": 3000},
                   "C": {"MEDIO": 3000, "ALTO": 2000, "BAJO": 4000}},
    "almacenamiento": {"AV": {"any": 150}, "AH": {"any": 150},
                       "B": {"MEDIO": 1000, "ALTO": 500, "BAJO": 1500},
                       "C": {"MEDIO": 1500, "ALTO": 800, "BAJO": 3000}},
}

BIE = {"AV": {"BAJO": 300, "MEDIO": 300, "ALTO": 300},
       "AH": {"MEDIO": 500, "ALTO": 200}, "B": {"MEDIO": 500, "ALTO": 200},
       "C": {"MEDIO": 1000, "ALTO": 500}, "D": {"ALTO": 5000}}

ROCIADORES = {
    "produccion": {"AV": {"MEDIO": 500, "ALTO": 300}, "AH": {"MEDIO": 1500, "ALTO": 750},
                   "B": {"MEDIO": 2500, "ALTO": 1000}, "C": {"MEDIO": 3500, "ALTO": 2000}},
    "almacenamiento": {"AV": {"MEDIO": 300, "ALTO": 300}, "AH": {"MEDIO": 1000, "ALTO": 600},
                       "B": {"MEDIO": 1500, "ALTO": 800}, "C": {"MEDIO": 2000, "ALTO": 1000}},
}

HUMOS = {"produccion": {"MEDIO": 2000, "ALTO": 1000},
         "almacenamiento": {"MEDIO": 1000, "ALTO": 800}}

HIDRANTES = {"AV": {"MEDIO": 2500, "ALTO": 3500}, "B": {"MEDIO": 2500, "ALTO": 3500},
             "C": {"MEDIO": 2500, "ALTO": 3500}, "D": {"MEDIO": 10000, "ALTO": 10000}}


def _base_type(config: str) -> str:
    if config in ("AV", "AH"):
        return "A"
    if config in ("D", "E"):
        return "D"
    return config


def _threshold(table, config, categoria, nivel):
    cfg = table.get(config)
    if cfg is None:
        return None
    if "any" in cfg:
        # excepción: riesgo bajo nivel 1 queda excluido en detección
        if categoria == "BAJO" and nivel == 1:
            return None
        return cfg["any"]
    return cfg.get(categoria)


def _inst(nombre, obligatorio, detalle):
    return {"nombre": nombre, "obligatorio": obligatorio, "detalle": detalle}


def build_requirements(data: dict, nivel: int, categoria: str, modo_pred: str) -> dict:
    config = data.get("tipo_configuracion", "B")
    base = _base_type(config)
    situacion = data.get("situacion", "sobre_rasante")
    sit_key = "bajo" if situacion == "bajo_rasante" else "sobre"
    A = float(data.get("superficie_sector") or 0)
    S_est = float(data.get("superficie_establecimiento") or 0) or A
    h_evac = float(data.get("altura_evacuacion") or 0)
    cubierta_ligera = bool(data.get("cubierta_ligera"))
    rociadores_previstos = bool(data.get("rociadores"))

    # Estabilidad estructura portante
    if base == "D":
        estabilidad = {"valor": "No exigible", "detalle": "Configuración en espacio abierto (tipo D/E): estabilidad al fuego no exigible con carácter general."}
    else:
        val = ESTABILIDAD[base][sit_key][categoria]
        estabilidad = {"valor": val, "detalle": f"Estructura portante · {('planta bajo rasante' if sit_key=='bajo' else 'planta sobre rasante')} · Tabla 2.2."}
    cubierta = {"valor": "R 15", "aplica": cubierta_ligera,
                "detalle": "Cubierta ligera no prevista para evacuación y con carga permanente < 100 kg/m²."} if cubierta_ligera else None

    delimitadores = {"valor": DELIMITADORES.get(categoria, "EI 120"),
                     "detalle": "Paredes y techos delimitadores del sector. Puertas de paso: EI de la mitad del elemento atravesado (Tabla 2.3, orientativo)."}

    modo_label = "almacenamiento" if modo_pred == "almacenamiento" else "producción/fabricación"

    inst = []

    # Extintores portátiles — siempre
    inst.append(_inst("Extintores portátiles", True, "Obligatorios en todos los sectores de incendio (Anexo III)."))

    # Sistemas manuales de alarma (pulsadores) — siempre
    inst.append(_inst("Sistema manual de alarma (pulsadores)", True, "Se instala en todos los sectores de incendio."))

    # Detección automática
    thr = _threshold(DETECCION[modo_pred], config, categoria, nivel)
    if thr is not None:
        obl = A >= thr
        inst.append(_inst("Detección automática de incendio", obl,
                          f"Actividad de {modo_label}, tipo {config}, riesgo {categoria}: obligatoria si superficie ≥ {thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Detección automática de incendio", False,
                          "No exigible por superficie para esta configuración/nivel (verificar criterios de ocupación)."))

    # BIE
    bie_thr = _threshold(BIE, config, categoria, nivel) if config in BIE else None
    if bie_thr is not None:
        obl = A >= bie_thr
        inst.append(_inst("Bocas de incendio equipadas (BIE)", obl,
                          f"Tipo {config}, riesgo {categoria}: obligatorias si superficie ≥ {bie_thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Bocas de incendio equipadas (BIE)", False,
                          "No exigibles por superficie para esta configuración/nivel."))

    # Rociadores automáticos
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

    # Control de humos y calor
    humo_thr = HUMOS[modo_pred].get(categoria) if categoria in ("MEDIO", "ALTO") else None
    if humo_thr is not None:
        obl = A >= humo_thr
        inst.append(_inst("Control de humos y calor", obl,
                          f"Actividad de {modo_label}, riesgo {categoria}: obligatorio si superficie ≥ {humo_thr:.0f} m² (sector: {A:.0f} m²)."))
    else:
        inst.append(_inst("Control de humos y calor", False, "No exigible en riesgo bajo (valorar huecos de ventilación)."))

    # Hidrantes exteriores
    hid_thr = HIDRANTES.get(config, {}).get(categoria)
    if hid_thr is not None:
        obl = S_est >= hid_thr
        inst.append(_inst("Hidrantes exteriores", obl,
                          f"Tipo {config}, riesgo {categoria}: obligatorios si superficie del establecimiento ≥ {hid_thr:.0f} m² (establecimiento: {S_est:.0f} m²)."))
    else:
        inst.append(_inst("Hidrantes exteriores", False, "No exigibles por superficie en riesgo bajo."))

    # Columna seca
    cs_obl = h_evac >= 15
    inst.append(_inst("Columna seca", cs_obl,
                      f"Obligatoria si la altura de evacuación ≥ 15 m (altura declarada: {h_evac:.1f} m)."))

    # Alumbrado de emergencia y señalización — siempre
    inst.append(_inst("Alumbrado de emergencia", True, "Según sección 4 del DB-SUA del CTE."))
    inst.append(_inst("Señalización de medios manuales", True, "Señalización de extintores, pulsadores, BIE e hidrantes (RIPCI)."))

    return {
        "config": config,
        "situacion": situacion,
        "modo_predominante": modo_pred,
        "estabilidad": estabilidad,
        "cubierta_ligera": cubierta,
        "delimitadores": delimitadores,
        "instalaciones": inst,
    }
