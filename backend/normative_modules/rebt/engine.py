"""Motor de cálculo REBT (RD 842/2002): dimensionado de línea de baja tensión.

Calcula la corriente de diseño, la sección del conductor por caída de tensión y por
calentamiento (ITC-BT-19), el calibre del magnetotérmico, el diferencial, la sección
de tierra (ITC-BT-18) y el grado de electrificación en viviendas (ITC-BT-25).
"""
import math

from normative_modules.rebt.catalog import (
    TENSION, CONDUCTIVIDAD, SECCIONES, MAGNETOS, GRADOS_VIVIENDA,
    ampacidad, seccion_tierra,
)


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _caida_volts(suministro, L, P, gamma, S, V):
    if S <= 0:
        return float("inf")
    if suministro == "trifasica":
        return (L * P) / (gamma * S * V)
    return (2 * L * P) / (gamma * S * V)


def compute(data: dict) -> dict:
    suministro = data.get("suministro") or "monofasica"
    V = TENSION.get(suministro, 230)
    P = _num(data.get("potencia"))
    cosphi = _num(data.get("cosphi"), 0.9) or 0.9
    L = _num(data.get("longitud"))
    material = data.get("material") or "Cu"
    gamma = CONDUCTIVIDAD.get(material, 56.0)
    caida_pct = _num(data.get("caida_max_pct"), 3.0) or 3.0
    tipo = data.get("tipo_instalacion") or "otro"

    errors = []
    if P <= 0:
        errors.append("La potencia prevista (W) debe ser mayor que 0.")
    if L <= 0:
        errors.append("La longitud de la línea (m) debe ser mayor que 0.")
    if errors:
        raise ValueError(" ".join(errors))

    # Corriente de diseño Ib
    if suministro == "trifasica":
        Ib = P / (math.sqrt(3) * V * cosphi)
    else:
        Ib = P / (V * cosphi)

    # Sección por caída de tensión admisible
    e_max = caida_pct / 100.0 * V
    if suministro == "trifasica":
        s_cdt = (L * P) / (gamma * e_max * V)
    else:
        s_cdt = (2 * L * P) / (gamma * e_max * V)

    # Sección por calentamiento (menor normalizada con Iz ≥ Ib)
    s_termica = None
    for s in SECCIONES:
        if ampacidad(s, material) >= Ib:
            s_termica = s
            break

    # Sección elegida: menor normalizada que cumpla caída de tensión Y calentamiento
    s_elegida = None
    for s in SECCIONES:
        if s >= s_cdt - 1e-9 and ampacidad(s, material) >= Ib:
            s_elegida = s
            break
    if s_elegida is None:
        s_elegida = SECCIONES[-1]

    iz = ampacidad(s_elegida, material)
    e_real = _caida_volts(suministro, L, P, gamma, s_elegida, V)
    caida_real_pct = e_real / V * 100.0

    # Magnetotérmico (IGA): Ib ≤ In ≤ Iz
    iga = None
    for br in MAGNETOS:
        if br >= Ib and br <= iz:
            iga = br
            break
    if iga is None:  # no hay calibre por debajo de Iz: escoger mayor ≤ Iz o el menor ≥ Ib
        candidatos = [b for b in MAGNETOS if b <= iz]
        iga = candidatos[-1] if candidatos else next((b for b in MAGNETOS if b >= Ib), MAGNETOS[-1])

    s_tierra = seccion_tierra(s_elegida)
    diff_ma = 30 if tipo in ("vivienda_basica", "vivienda_elevada", "garaje", "publica_concurrencia") else 300

    def _sec(s):
        return f"{s:g}".replace(".", ",")

    secciones = []
    observaciones = []

    # 1) Corriente de diseño
    secciones.append({
        "id": "corriente", "titulo": "Corriente de diseño (Ib)", "estado": "info",
        "descripcion": f"Suministro {'trifásico 400 V' if suministro == 'trifasica' else 'monofásico 230 V'}, cos φ = {_sec(cosphi)}.",
        "items": [
            {"nombre": "Potencia prevista", "detalle": f"{P:,.0f} W", "valor": ""},
            {"nombre": "Corriente de diseño Ib", "detalle": f"Ib = P/({'√3·' if suministro == 'trifasica' else ''}V·cos φ) = {Ib:.2f} A", "valor": ""},
        ],
    })

    # 2) Sección del conductor
    cdt_ok = caida_real_pct <= caida_pct + 1e-6
    est_sec = "cumple" if cdt_ok else "no_cumple"
    secciones.append({
        "id": "seccion", "titulo": "Sección del conductor", "estado": est_sec,
        "descripcion": f"Material {material}; γ = {gamma:g} m/(Ω·mm²). Se elige la mayor entre la exigida por caída de tensión y por calentamiento (ITC-BT-19).",
        "items": [
            {"nombre": "Sección por caída de tensión", "detalle": f"S ≥ {s_cdt:.2f} mm²", "valor": ""},
            {"nombre": "Sección por calentamiento", "detalle": f"S = {_sec(s_termica) if s_termica else '—'} mm² (Iz ≥ Ib)", "valor": ""},
            {"nombre": "Sección adoptada", "detalle": f"{_sec(s_elegida)} mm² (Iz = {iz:.0f} A)", "valor": "", "estado": "cumple"},
        ],
    })

    # 3) Caída de tensión
    secciones.append({
        "id": "caida", "titulo": "Caída de tensión", "estado": "cumple" if cdt_ok else "no_cumple",
        "descripcion": f"Máxima admisible {caida_pct:g} % ({e_max:.1f} V).",
        "items": [
            {"nombre": "Caída de tensión real", "detalle": f"{caida_real_pct:.2f} % ({e_real:.1f} V) con {_sec(s_elegida)} mm²",
             "valor": "", "estado": "cumple" if cdt_ok else "no_cumple"},
        ],
    })
    if not cdt_ok:
        observaciones.append({"tipo": "error", "texto": f"La caída de tensión real ({caida_real_pct:.2f} %) supera la máxima admisible ({caida_pct:g} %). Aumente la sección del conductor."})

    # 4) Protecciones
    iga_ok = Ib <= iga <= iz
    secciones.append({
        "id": "protecciones", "titulo": "Protecciones", "estado": "cumple" if iga_ok else "observaciones",
        "descripcion": "Interruptor automático magnetotérmico y diferencial (ITC-BT-22/24).",
        "items": [
            {"nombre": "Magnetotérmico (IGA)", "detalle": f"In = {iga} A  (condición Ib ≤ In ≤ Iz: {Ib:.1f} ≤ {iga} ≤ {iz:.0f})",
             "valor": "", "estado": "cumple" if iga_ok else "observaciones"},
            {"nombre": "Interruptor diferencial", "detalle": f"Sensibilidad {diff_ma} mA ({'protección de personas' if diff_ma == 30 else 'protección general'})", "valor": ""},
        ],
    })
    if not iga_ok:
        observaciones.append({"tipo": "warning", "texto": f"No existe un calibre normalizado que cumpla Ib ≤ In ≤ Iz para la sección adoptada; revise sección/calibre (In propuesto {iga} A, Iz {iz:.0f} A)."})

    # 5) Puesta a tierra
    secciones.append({
        "id": "tierra", "titulo": "Puesta a tierra", "estado": "info",
        "descripcion": "Sección del conductor de protección según la ITC-BT-18 (Tabla 2).",
        "items": [
            {"nombre": "Conductor de protección", "detalle": f"S = {_sec(s_tierra)} mm² (fase {_sec(s_elegida)} mm²)", "valor": ""},
        ],
    })

    # 6) Grado de electrificación (viviendas)
    estado_global_extra = "cumple"
    if tipo in GRADOS_VIVIENDA:
        g = GRADOS_VIVIENDA[tipo]
        ok = P >= g["potencia_min"]
        est = "cumple" if ok else "no_cumple"
        secciones.append({
            "id": "electrificacion", "titulo": "Grado de electrificación (ITC-BT-25)", "estado": est,
            "descripcion": f"{'Electrificación básica' if tipo == 'vivienda_basica' else 'Electrificación elevada'}: potencia mínima {g['potencia_min']:,.0f} W, mínimo {g['circuitos']} circuitos.",
            "items": [
                {"nombre": "Potencia prevista vs mínima", "detalle": f"{P:,.0f} W {'≥' if ok else '<'} {g['potencia_min']:,.0f} W",
                 "valor": "", "estado": est},
                {"nombre": "Circuitos mínimos", "detalle": g["descripcion"], "valor": ""},
            ],
        })
        if not ok:
            observaciones.append({"tipo": "error", "texto": f"La potencia prevista ({P:,.0f} W) es inferior a la mínima del grado de electrificación seleccionado ({g['potencia_min']:,.0f} W)."})
            estado_global_extra = "no_cumple"

    # Estancias del expediente (para ubicar circuitos)
    estancias = data.get("estancias") or []

    estados = [s["estado"] for s in secciones]
    if "no_cumple" in estados or estado_global_extra == "no_cumple":
        estado_global = "no_cumple"
    elif "observaciones" in estados:
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    resumen = [
        {"label": "Corriente Ib", "valor": f"{Ib:.1f}", "unidad": "A"},
        {"label": "Sección adoptada", "valor": _sec(s_elegida), "unidad": "mm²"},
        {"label": "Caída de tensión", "valor": f"{caida_real_pct:.2f}", "unidad": "%"},
        {"label": "Magnetotérmico", "valor": f"{iga}", "unidad": "A"},
    ]

    return {
        "estado_global": estado_global,
        "resumen": resumen,
        "secciones": secciones,
        "observaciones": observaciones,
        "estancias": estancias,
        "datos": {
            "suministro": suministro, "tension": V, "potencia": P, "cosphi": cosphi,
            "longitud": L, "material": material, "caida_max_pct": caida_pct,
            "Ib": round(Ib, 2), "seccion": s_elegida, "iz": round(iz, 1),
            "caida_real_pct": round(caida_real_pct, 2), "iga": iga,
            "diferencial_ma": diff_ma, "seccion_tierra": s_tierra, "tipo": tipo,
        },
    }
