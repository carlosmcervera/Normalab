"""Motor de cálculo RITE (RD 1027/2007) — comprobaciones de una instalación térmica.

Usa el cuadro de superficies + ocupación compartido del expediente para estimar la
demanda térmica, el caudal de ventilación (renovaciones) y la demanda de ACS, y
verifica las exigencias de eficiencia energética (IT 1.2) y bienestar (IT 1.1).
"""
from normative_modules.rite.catalog import (
    DEMANDA_WM2, TIPOS_GENERADOR, IDA_CAUDAL, ACS_CONSUMO, AISLAMIENTO_TUBERIAS,
    FRACCIONAMIENTO_KW, RECUPERACION_M3S,
)
from normative_modules.shared_estancias import resumen_estancias


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def compute(data: dict) -> dict:
    tipo = data.get("tipo_instalacion") or "climatizacion"
    uso = data.get("uso_edificio") or "oficinas"
    zona = data.get("zona_climatica") or "C"
    potencia_kw = _num(data.get("potencia_termica_kw"))
    rendimiento = _num(data.get("rendimiento_pct"))
    generador = data.get("tipo_generador") or "otro"
    ida = data.get("categoria_ida") or "IDA2"
    caudal_expulsado = _num(data.get("caudal_expulsado_m3s"))
    consumo_acs = data.get("consumo_acs_persona")

    est = resumen_estancias(data.get("estancias") or [])
    sup_util = est["total_util"]
    ocupantes = int(_num(data.get("ocupantes_override")) or est["total_ocupacion"])

    if sup_util <= 0 and potencia_kw <= 0:
        raise ValueError("Introduce el cuadro de superficies del expediente y/o la potencia térmica instalada.")

    secciones = []
    observaciones = []

    incluye_calor = tipo in ("calefaccion", "climatizacion", "mixta")

    # 1) Bienestar térmico (IT 1.1) — informativo
    secciones.append({
        "id": "bienestar", "titulo": "Bienestar térmico (IT 1.1)", "estado": "info",
        "descripcion": "Condiciones interiores de diseño para las personas (RITE IT 1.1.4.1).",
        "items": [
            {"nombre": "Temperatura operativa (invierno)", "detalle": "21–23 °C · humedad relativa 40–50 %", "valor": ""},
            {"nombre": "Temperatura operativa (verano)", "detalle": "23–25 °C · humedad relativa 45–60 %", "valor": ""},
        ],
    })

    # 2) Demanda térmica estimada vs potencia instalada (IT 1.2 · eficiencia)
    demanda_kw = round(sup_util * DEMANDA_WM2.get(zona, 75) / 1000.0, 2)
    if incluye_calor and sup_util > 0 and potencia_kw > 0:
        if potencia_kw < demanda_kw * 0.9:
            est_dem = "no_cumple"
            det = f"La potencia instalada ({potencia_kw:g} kW) es INSUFICIENTE frente a la demanda estimada ({demanda_kw:g} kW)."
            observaciones.append({"tipo": "error", "texto": det})
        elif potencia_kw > demanda_kw * 1.5:
            est_dem = "observaciones"
            det = f"Posible SOBREDIMENSIONADO: potencia instalada {potencia_kw:g} kW frente a demanda estimada {demanda_kw:g} kW (> 150 %). Justifíquelo (IT 1.2.4.1.2.1)."
            observaciones.append({"tipo": "warning", "texto": det})
        else:
            est_dem = "cumple"
            det = f"Potencia instalada {potencia_kw:g} kW adecuada a la demanda estimada {demanda_kw:g} kW."
        secciones.append({
            "id": "demanda", "titulo": "Demanda térmica y potencia instalada (IT 1.2)", "estado": est_dem,
            "descripcion": f"Zona climática {zona}: demanda orientativa {DEMANDA_WM2.get(zona, 75)} W/m² × {sup_util:g} m².",
            "items": [
                {"nombre": "Demanda térmica estimada", "detalle": f"{demanda_kw:g} kW", "valor": ""},
                {"nombre": "Potencia instalada", "detalle": f"{potencia_kw:g} kW", "valor": "", "estado": est_dem},
            ],
        })

    # 3) Rendimiento del generador (IT 1.2.4.1.2)
    gen = next((g for g in TIPOS_GENERADOR if g["value"] == generador), None)
    if gen and rendimiento > 0:
        ok = rendimiento >= gen["rend_min"]
        est_r = "cumple" if ok else "no_cumple"
        secciones.append({
            "id": "rendimiento", "titulo": "Rendimiento de la generación (IT 1.2.4.1.2)", "estado": est_r,
            "descripcion": f"Generador: {gen['label']} · rendimiento mínimo exigido ≈ {gen['rend_min']} %.",
            "items": [{"nombre": "Rendimiento del generador", "detalle": f"{rendimiento:g} % {'≥' if ok else '<'} {gen['rend_min']} %", "valor": "", "estado": est_r}],
        })
        if not ok:
            observaciones.append({"tipo": "error", "texto": f"El rendimiento del generador ({rendimiento:g} %) es inferior al mínimo orientativo ({gen['rend_min']} %)."})

    # 4) Fraccionamiento de potencia (IT 1.2.4.1.2.2)
    if potencia_kw > 0:
        frac = potencia_kw > FRACCIONAMIENTO_KW
        secciones.append({
            "id": "fraccionamiento", "titulo": "Fraccionamiento de potencia (IT 1.2.4.1.2.2)",
            "estado": "observaciones" if frac else "cumple",
            "descripcion": f"Si la potencia térmica nominal supera {FRACCIONAMIENTO_KW} kW deben instalarse ≥ 2 generadores.",
            "items": [{"nombre": "Nº de generadores", "detalle": (f"Potencia {potencia_kw:g} kW > {FRACCIONAMIENTO_KW} kW: se exigen ≥ 2 generadores." if frac else f"Potencia {potencia_kw:g} kW ≤ {FRACCIONAMIENTO_KW} kW: admisible 1 generador."), "valor": ""}],
        })
        if frac:
            observaciones.append({"tipo": "warning", "texto": f"Potencia térmica {potencia_kw:g} kW > {FRACCIONAMIENTO_KW} kW: fraccione la potencia en ≥ 2 generadores (IT 1.2.4.1.2.2)."})

    # 5) Ventilación / renovaciones de aire (IT 1.1.4.2) — usa la ocupación compartida
    caudal_ls = round(ocupantes * IDA_CAUDAL.get(ida, 12.5), 1)
    caudal_m3h = round(caudal_ls * 3.6, 1)
    secciones.append({
        "id": "ventilacion", "titulo": "Ventilación y renovación de aire (IT 1.1.4.2)", "estado": "info",
        "descripcion": f"Categoría {ida}: {IDA_CAUDAL.get(ida, 12.5):g} dm³/s por persona · ocupación del expediente {ocupantes} personas.",
        "items": [
            {"nombre": "Caudal de aire exterior mínimo", "detalle": f"{caudal_ls:g} l/s ({caudal_m3h:g} m³/h)", "valor": ""},
            {"nombre": "Ocupación considerada", "detalle": f"{ocupantes} personas (cuadro de ocupación del expediente)", "valor": ""},
        ],
    })

    # 6) Recuperación de calor (IT 1.2.4.5.2)
    if caudal_expulsado > 0:
        rec = caudal_expulsado > RECUPERACION_M3S
        secciones.append({
            "id": "recuperacion", "titulo": "Recuperación de calor del aire de extracción (IT 1.2.4.5.2)",
            "estado": "observaciones" if rec else "cumple",
            "descripcion": f"Obligatoria si el caudal de aire expulsado supera {RECUPERACION_M3S} m³/s.",
            "items": [{"nombre": "Recuperador de calor", "detalle": (f"Caudal expulsado {caudal_expulsado:g} m³/s > {RECUPERACION_M3S} m³/s: recuperador OBLIGATORIO." if rec else f"Caudal {caudal_expulsado:g} m³/s ≤ {RECUPERACION_M3S} m³/s: no obligatorio."), "valor": ""}],
        })
        if rec:
            observaciones.append({"tipo": "warning", "texto": f"Caudal de aire expulsado {caudal_expulsado:g} m³/s > {RECUPERACION_M3S} m³/s: es obligatorio un sistema de recuperación de calor (IT 1.2.4.5.2)."})

    # 7) Aislamiento de tuberías (IT 1.2.4.2) — informativo con tabla
    secciones.append({
        "id": "aislamiento", "titulo": "Aislamiento térmico de tuberías (IT 1.2.4.2)", "estado": "info",
        "descripcion": "Espesor mínimo de aislamiento (mm) para tuberías interiores con fluido caliente (40–60 °C).",
        "items": [{"nombre": f"Diámetro {r['diametro']} mm", "detalle": f"Espesor mínimo {r['espesor']} mm", "valor": ""} for r in AISLAMIENTO_TUBERIAS],
    })

    # 8) Demanda de ACS
    if tipo in ("acs", "mixta") or consumo_acs not in (None, ""):
        cons = _num(consumo_acs) if consumo_acs not in (None, "") else ACS_CONSUMO.get(uso, 28)
        litros = round(ocupantes * cons, 1)
        energia = round(litros * (60 - 10) * 1.16 / 1000.0, 2)  # kWh/día a 60 °C, agua de red 10 °C
        secciones.append({
            "id": "acs", "titulo": "Demanda de agua caliente sanitaria (ACS)", "estado": "info",
            "descripcion": f"Consumo unitario {cons:g} l/persona·día a 60 °C · {ocupantes} personas.",
            "items": [
                {"nombre": "Demanda diaria de ACS", "detalle": f"{litros:g} litros/día", "valor": ""},
                {"nombre": "Energía de preparación", "detalle": f"≈ {energia:g} kWh/día (ΔT 50 °C)", "valor": ""},
            ],
        })

    # 9) Mantenimiento (IT 3)
    if potencia_kw > 0:
        if potencia_kw <= 70:
            periodicidad = "Instalación ≤ 70 kW: mantenimiento anual (o según instrucciones del fabricante)."
        elif potencia_kw <= 1000:
            periodicidad = "70 < P ≤ 1.000 kW: operaciones trimestrales/semestrales según la tabla 3.1 de la IT 3."
        else:
            periodicidad = "P > 1.000 kW: operaciones mensuales/quincenales según la tabla 3.1 de la IT 3."
        secciones.append({
            "id": "mantenimiento", "titulo": "Mantenimiento (IT 3)", "estado": "info",
            "descripcion": "Programa de gestión energética y mantenimiento preventivo.",
            "items": [{"nombre": "Periodicidad", "detalle": periodicidad, "valor": ""}],
        })

    estados = [s["estado"] for s in secciones]
    if "no_cumple" in estados:
        estado_global = "no_cumple"
    elif "observaciones" in estados:
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    resumen = [
        {"label": "Superficie útil", "valor": f"{sup_util:g}", "unidad": "m²"},
        {"label": "Ocupación", "valor": f"{ocupantes}", "unidad": "pers."},
        {"label": "Potencia instalada", "valor": f"{potencia_kw:g}", "unidad": "kW"},
        {"label": "Caudal ventilación", "valor": f"{caudal_ls:g}", "unidad": "l/s"},
    ]

    return {
        "estado_global": estado_global,
        "resumen": resumen,
        "secciones": secciones,
        "observaciones": observaciones,
        "estancias": data.get("estancias") or [],
        "datos": {
            "tipo": tipo, "uso": uso, "zona": zona, "potencia_kw": potencia_kw,
            "rendimiento": rendimiento, "generador": generador, "ida": ida,
            "caudal_expulsado": caudal_expulsado, "sup_util": sup_util,
            "ocupantes": ocupantes, "demanda_kw": demanda_kw,
            "caudal_ventilacion_ls": caudal_ls,
        },
    }
