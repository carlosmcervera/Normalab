"""RSCIEI rules & calculation engine.

Basado en el Reglamento de seguridad contra incendios en los establecimientos
industriales (RD 2267/2004, texto consolidado). Cálculo de la densidad de carga
de fuego ponderada y corregida (Qs), determinación del nivel de riesgo intrínseco
(NRI) y verificación de la superficie máxima admisible de sector de incendio.
"""

from normative_modules.rsciei.requirements import build_requirements

MCAL_PER_MJ = 1 / 4.184

# Tabla 1.3: niveles de riesgo intrínseco (Qs en MJ/m²)
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

# Tabla 2.1: superficie máxima admisible del sector de incendio (m²)
# None = NO ADMITIDO ; "SIN_LIMITE" = sin límite establecido
MAX_SURFACE = {
    "AV": {1: 2000, 2: 1000, 3: 500, 4: 400, 5: 300, 6: None, 7: 1500, 8: None},
    "AH": {1: 6000, 2: 4000, 3: 3500, 4: 3000, 5: 2500, 6: 2000, 7: None, 8: None},
    "B": {1: 12000, 2: 8000, 3: 7000, 4: 6000, 5: 5000, 6: 4000, 7: 3000, 8: None},
    "C": {1: "SIN_LIMITE", 2: 12000, 3: 10000, 4: 8000, 5: 7000, 6: 6000, 7: 5000, 8: 4000},
}

CONFIG_LABELS = {
    "AV": "Tipo A - separación vertical",
    "AH": "Tipo A - separación horizontal",
    "B": "Tipo B",
    "C": "Tipo C",
    "D": "Tipo D (espacio abierto)",
}


def _validate(data: dict):
    errors = []
    A = data.get("superficie_sector")
    if not A or float(A) <= 0:
        errors.append("La superficie construida del sector (A) debe ser mayor que 0.")
    if not data.get("tipo_configuracion"):
        errors.append("Debe seleccionar el tipo de configuración del establecimiento.")
    ra = data.get("ra")
    if ra is None or float(ra) <= 0:
        errors.append("El coeficiente de activación (Ra) debe ser mayor que 0.")
    zonas = data.get("zonas") or []
    if not zonas:
        errors.append("Debe añadir al menos una zona/actividad al sector.")
    for i, z in enumerate(zonas, start=1):
        if not z.get("superficie") or float(z["superficie"]) <= 0:
            errors.append(f"Zona {i}: la superficie debe ser mayor que 0.")
        if not z.get("ci") or float(z["ci"]) <= 0:
            errors.append(f"Zona {i}: el coeficiente Ci debe ser mayor que 0.")
        if z.get("modo") == "almacenamiento":
            if not z.get("qvi") or float(z["qvi"]) <= 0:
                errors.append(f"Zona {i}: qvi (MJ/m³) debe ser mayor que 0.")
            if not z.get("hi") or float(z["hi"]) <= 0:
                errors.append(f"Zona {i}: la altura de almacenamiento hi debe ser mayor que 0.")
        else:
            if not z.get("qsi") or float(z["qsi"]) <= 0:
                errors.append(f"Zona {i}: qsi (MJ/m²) debe ser mayor que 0.")
    return errors


def _nri_for(qs_mj: float):
    for nivel, low, high, cat in NRI_TABLE:
        if low < qs_mj <= high or (nivel == 1 and qs_mj <= high):
            return nivel, cat
    return 8, "ALTO"


def compute(data: dict) -> dict:
    errors = _validate(data)
    if errors:
        raise ValueError(" ".join(errors))

    A = float(data["superficie_sector"])
    ra = float(data["ra"])
    zonas = data["zonas"]

    detalle_zonas = []
    numerador = 0.0
    for z in zonas:
        ci = float(z["ci"])
        s = float(z["superficie"])
        if z.get("modo") == "almacenamiento":
            qvi = float(z["qvi"])
            hi = float(z["hi"])
            aporte = qvi * ci * hi * s
            detalle_zonas.append({
                "descripcion": z.get("descripcion", "Zona"),
                "modo": "almacenamiento",
                "qvi": qvi, "hi": hi, "ci": ci, "superficie": s,
                "aporte": round(aporte, 2),
            })
        else:
            qsi = float(z["qsi"])
            aporte = qsi * s * ci
            detalle_zonas.append({
                "descripcion": z.get("descripcion", "Zona"),
                "modo": "produccion",
                "qsi": qsi, "ci": ci, "superficie": s,
                "aporte": round(aporte, 2),
            })
        numerador += aporte

    qs_mj = (numerador / A) * ra
    qs_mcal = qs_mj * MCAL_PER_MJ
    nivel, categoria = _nri_for(qs_mj)

    config = data["tipo_configuracion"]
    fachada = bool(data.get("fachada_accesible"))
    rociadores = bool(data.get("rociadores"))

    factor = 1.0
    factores_aplicados = []
    if fachada:
        factor *= 1.25
        factores_aplicados.append("Fachada accesible ≥ 50% del perímetro (×1,25)")
    if rociadores:
        factor *= 2.0
        factores_aplicados.append("Rociadores automáticos en todo el sector (×2)")

    sector = _sectorizacion(config, nivel, A, factor, factores_aplicados,
                            data.get("situacion", "sobre_rasante"))

    observaciones = _observaciones(nivel, categoria, sector, rociadores, config)
    estado = _estado_global(sector, observaciones)

    # Modo predominante del sector (por superficie)
    sup_alm = sum(float(z["superficie"]) for z in zonas if z.get("modo") == "almacenamiento")
    sup_prod = sum(float(z["superficie"]) for z in zonas if z.get("modo") != "almacenamiento")
    modo_pred = "almacenamiento" if sup_alm > sup_prod else "produccion"

    requisitos = build_requirements(data, nivel, categoria, modo_pred)

    return {
        "calculo": {
            "numerador": round(numerador, 2),
            "A": A,
            "ra": ra,
            "qs_mj": round(qs_mj, 2),
            "qs_mcal": round(qs_mcal, 2),
            "zonas": detalle_zonas,
        },
        "nivel_riesgo": {
            "nivel": nivel,
            "categoria": categoria,
            "qs_mj": round(qs_mj, 2),
            "qs_mcal": round(qs_mcal, 2),
        },
        "sectorizacion": sector,
        "requisitos": requisitos,
        "observaciones": observaciones,
        "estado_global": estado,
    }


def _sectorizacion(config, nivel, A, factor, factores_aplicados, situacion="sobre_rasante"):
    bajo_rasante = situacion == "bajo_rasante"
    base = {
        "config": config,
        "config_label": CONFIG_LABELS.get(config, config),
        "superficie_sector": A,
        "factor_incremento": round(factor, 3),
        "factores_aplicados": factores_aplicados,
    }
    if config in ("D",):
        base.update({
            "estado": "no_aplica",
            "max_admisible": None,
            "max_admisible_base": None,
            "mensaje": "Configuración en espacio abierto: no aplica límite de superficie de sector de la Tabla 2.1.",
        })
        return base

    tabla = MAX_SURFACE.get(config, {})
    valor = tabla.get(nivel)
    if valor is None:
        base.update({
            "estado": "no_admitido",
            "max_admisible": None,
            "max_admisible_base": None,
            "mensaje": f"NO ADMITIDO: la configuración {config} no admite nivel de riesgo {nivel}.",
        })
        return base
    if valor == "SIN_LIMITE":
        base.update({
            "estado": "cumple",
            "max_admisible": None,
            "max_admisible_base": "SIN LÍMITE",
            "mensaje": "Sin límite de superficie establecido para esta configuración y nivel.",
        })
        return base

    base_val = valor / 2 if bajo_rasante else valor
    if bajo_rasante:
        factores_aplicados.append("Planta bajo rasante: superficie base ÷ 2 (nota 1, Tabla 2.1)")
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


def _observaciones(nivel, categoria, sector, rociadores, config):
    obs = []
    obs.append({
        "tipo": "info",
        "texto": f"Nivel de riesgo intrínseco {nivel} ({categoria}) según Tabla 1.3 del RSCIEI.",
    })
    if categoria == "ALTO":
        obs.append({
            "tipo": "warning",
            "texto": "Riesgo intrínseco ALTO: revise requisitos reforzados de estabilidad al fuego, "
                     "instalaciones de protección activa y condiciones de evacuación.",
        })
    if sector.get("estado") == "no_cumple":
        obs.append({"tipo": "error", "texto": sector["mensaje"]})
    elif sector.get("estado") == "no_admitido":
        obs.append({"tipo": "error", "texto": sector["mensaje"]})
    if not rociadores and nivel >= 5:
        obs.append({
            "tipo": "warning",
            "texto": "Para niveles de riesgo medio-alto, valore la instalación de rociadores "
                     "automáticos: duplican la superficie máxima admisible de sector (nota 3, Tabla 2.1).",
        })
    if config in ("D",):
        obs.append({
            "tipo": "info",
            "texto": "Establecimiento en espacio abierto: aplique los requisitos específicos "
                     "de la configuración tipo D del Anexo II.",
        })
    return obs


def _estado_global(sector, observaciones):
    if sector.get("estado") in ("no_cumple", "no_admitido"):
        return "no_cumple"
    if any(o["tipo"] == "warning" for o in observaciones):
        return "observaciones"
    return "cumple"
