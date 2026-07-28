"""Motor de cálculo REBT v2 (RD 842/2002): cuadro eléctrico con subcuadros.

Modela un cuadro general con protecciones de cabecera (IGA + diferencial general),
circuitos a cada carga (magnetotérmico + diferencial) y subcuadros anidados con su
propia línea de alimentación (línea puente). Calcula el cuadro de potencias
(potencia instalada y de cálculo con simultaneidad) y dimensiona todas las líneas
con las comprobaciones del REBT (Ib, sección por caída de tensión y calentamiento
ITC-BT-19, magnetotérmico Ib≤In≤Iz, diferencial, puesta a tierra ITC-BT-18).
"""
import math

from normative_modules.rebt.catalog import (
    TENSION, CONDUCTIVIDAD, SECCIONES, MAGNETOS, ampacidad, seccion_tierra,
)

SQRT3 = math.sqrt(3)


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _ib(suministro, P, V, cosphi):
    if P <= 0:
        return 0.0
    if suministro == "trifasica":
        return P / (SQRT3 * V * cosphi)
    return P / (V * cosphi)


def _seccion_caida(suministro, L, P, gamma, V, caida_max_pct, Ib, material):
    """Devuelve (seccion, Iz, caida_pct_real) para un tramo."""
    e_max = caida_max_pct / 100.0 * V if caida_max_pct > 0 else 0
    if L <= 0 or P <= 0 or e_max <= 0:
        s_cdt = 0.0
    elif suministro == "trifasica":
        s_cdt = (L * P) / (gamma * e_max * V)
    else:
        s_cdt = (2 * L * P) / (gamma * e_max * V)
    s_el = None
    for s in SECCIONES:
        if s >= s_cdt - 1e-9 and ampacidad(s, material) >= Ib:
            s_el = s
            break
    if s_el is None:
        s_el = SECCIONES[-1]
    iz = ampacidad(s_el, material)
    if L <= 0 or P <= 0:
        e_real = 0.0
    elif suministro == "trifasica":
        e_real = (L * P) / (gamma * s_el * V)
    else:
        e_real = (2 * L * P) / (gamma * s_el * V)
    return s_el, iz, (e_real / V * 100.0 if V else 0.0)


def _breaker(Ib, Iz):
    for b in MAGNETOS:
        if b >= Ib - 1e-9 and b <= Iz + 1e-9:
            return b, True
    cands = [b for b in MAGNETOS if b <= Iz + 1e-9]
    if cands:
        return cands[-1], False
    return next((b for b in MAGNETOS if b >= Ib), MAGNETOS[-1]), False


def _limite_total(general, tipo):
    if tipo == "alumbrado":
        return _num(general.get("caida_max_total_alumbrado"), 4.5) or 4.5
    return _num(general.get("caida_max_total_otros"), 6.5) or 6.5


def _potencia_instalada(board):
    p = sum(_num(c.get("potencia")) for c in board.get("cargas", []))
    p += sum(_potencia_instalada(sc) for sc in board.get("subcuadros", []))
    return p


def _potencia_demandada(board):
    p = sum(_num(c.get("potencia")) * (_num(c.get("factor_uso"), 1) or 1) for c in board.get("cargas", []))
    p += sum(_potencia_demandada(sc) for sc in board.get("subcuadros", []))
    return p * (_num(board.get("simultaneidad"), 1) or 1)


def _fmt_s(s):
    return f"{s:g}".replace(".", ",")


def _compute_board(board, general, caida_base_pct, es_raiz, obs, lineas, cuadro_pot, ruta=""):
    suministro = general["suministro"]
    V = general["V"]
    material = general["material"]
    gamma = CONDUCTIVIDAD.get(material, 56.0)

    nombre = board.get("nombre") or ("Cuadro general" if es_raiz else "Subcuadro")
    p_inst = _potencia_instalada(board)
    p_dem = _potencia_demandada(board)
    simult = _num(board.get("simultaneidad"), 1) or 1

    # Línea de alimentación del cuadro (acometida/DI en raíz; línea puente en subcuadros)
    L_feed = _num(board.get("longitud"))
    caida_feed_max = _num(board.get("caida_max"), 1.5 if es_raiz else 1.0) or (1.5 if es_raiz else 1.0)
    cosphi_gen = _num(board.get("cosphi"), 0.9) or 0.9
    Ib_board = _ib(suministro, p_dem, V, cosphi_gen)
    s_feed, iz_feed, caida_feed = _seccion_caida(suministro, L_feed, p_dem, gamma, V, caida_feed_max, Ib_board, material)
    iga, iga_ok = _breaker(Ib_board, iz_feed)
    tierra_feed = seccion_tierra(s_feed)
    caida_busbar = caida_base_pct + caida_feed
    sens_gen = int(_num(board.get("sensibilidad_general"), 300) or 300)

    tipo_linea = "Acometida / DI" if es_raiz else "Línea puente (alimentación subcuadro)"
    lineas.append({
        "cuadro": nombre, "circuito": tipo_linea, "tipo": "alimentacion",
        "potencia": round(p_dem, 1), "Ib": round(Ib_board, 2), "seccion": s_feed, "seccion_txt": _fmt_s(s_feed),
        "iz": round(iz_feed, 1), "caida_pct": round(caida_feed, 2), "caida_acum_pct": round(caida_busbar, 2),
        "proteccion": f"IGA {iga} A", "diferencial": f"{sens_gen} mA (general)",
        "tierra": _fmt_s(tierra_feed), "estado": "cumple" if iga_ok else "observaciones",
        "longitud": L_feed,
    })
    if not iga_ok:
        obs.append({"tipo": "warning", "texto": f"«{nombre}»: no hay calibre de IGA que cumpla Ib≤In≤Iz (Ib {Ib_board:.1f} A, Iz {iz_feed:.0f} A). Revise la sección de la línea de alimentación."})

    # Diferenciales del cuadro (pueden agrupar varios circuitos)
    difs = board.get("diferenciales") or []
    dif_by_id = {d.get("id"): d for d in difs}

    # Circuitos (cargas)
    cargas_out = []
    for c in board.get("cargas", []):
        P = _num(c.get("potencia"))
        cosphi = _num(c.get("cosphi"), 0.9) or 0.9
        L = _num(c.get("longitud"))
        tipo = c.get("tipo") or "otros"
        caida_max_c = _num(c.get("caida_max"), general.get("caida_max_circuito", 3)) or 3
        Ib = _ib(suministro, P, V, cosphi)
        s_el, iz, caida_c = _seccion_caida(suministro, L, P, gamma, V, caida_max_c, Ib, material)
        caida_total = caida_busbar + caida_c
        breaker, br_ok = _breaker(Ib, iz)
        tierra = seccion_tierra(s_el)
        dif = dif_by_id.get(c.get("diferencial_id"))
        sens = int(_num((dif or {}).get("sensibilidad"), 30 if tipo in ("alumbrado", "tomas") else 30) or 30)
        limite = _limite_total(general, tipo)
        cdt_ok = caida_total <= limite + 1e-6
        estado = "cumple"
        if not cdt_ok or not br_ok or P <= 0:
            estado = "no_cumple" if (not cdt_ok or P <= 0) else "observaciones"
        cargas_out.append({
            "id": c.get("id"), "nombre": c.get("nombre") or "Circuito", "estancia": c.get("estancia") or "",
            "tipo": tipo, "potencia": round(P, 1), "cosphi": cosphi, "longitud": L,
            "Ib": round(Ib, 2), "seccion": s_el, "seccion_txt": _fmt_s(s_el), "iz": round(iz, 1),
            "caida_pct": round(caida_c, 2), "caida_acum_pct": round(caida_total, 2), "limite_total": limite,
            "magneto": breaker, "diferencial_id": c.get("diferencial_id"), "sensibilidad": sens,
            "tierra": _fmt_s(tierra), "estado": estado, "factor_uso": _num(c.get("factor_uso"), 1) or 1,
        })
        lineas.append({
            "cuadro": nombre, "circuito": c.get("nombre") or "Circuito", "tipo": "circuito",
            "potencia": round(P, 1), "Ib": round(Ib, 2), "seccion": s_el, "seccion_txt": _fmt_s(s_el),
            "iz": round(iz, 1), "caida_pct": round(caida_c, 2), "caida_acum_pct": round(caida_total, 2),
            "proteccion": f"{breaker} A", "diferencial": f"{sens} mA", "tierra": _fmt_s(tierra),
            "estado": estado, "longitud": L,
        })
        cuadro_pot.append({
            "cuadro": nombre, "circuito": c.get("nombre") or "Circuito", "tipo": tipo,
            "potencia": round(P, 1), "factor_uso": _num(c.get("factor_uso"), 1) or 1,
            "potencia_calculo": round(P * (_num(c.get("factor_uso"), 1) or 1), 1),
        })
        if not cdt_ok:
            obs.append({"tipo": "error", "texto": f"«{nombre} · {c.get('nombre')}»: caída de tensión acumulada {caida_total:.2f} % supera el límite del {limite:g} % ({'alumbrado' if tipo == 'alumbrado' else 'otros usos'}). Aumente la sección."})

    # Diferenciales: In ≥ suma de Ib de sus circuitos
    dif_out = []
    for d in difs:
        ids = [c["id"] for c in cargas_out if c.get("diferencial_id") == d.get("id")]
        ib_sum = sum(c["Ib"] for c in cargas_out if c.get("diferencial_id") == d.get("id"))
        in_dif, _ = _breaker(ib_sum, 10 ** 6)
        dif_out.append({
            "id": d.get("id"), "nombre": d.get("nombre") or "Diferencial",
            "sensibilidad": int(_num(d.get("sensibilidad"), 30) or 30),
            "in": in_dif, "num_circuitos": len(ids), "ib_total": round(ib_sum, 2),
        })

    # Subcuadros (recursivo)
    subs_out = []
    for sc in board.get("subcuadros", []):
        subs_out.append(_compute_board(sc, general, caida_busbar, False, obs, lineas, cuadro_pot))

    return {
        "id": board.get("id"), "nombre": nombre, "es_raiz": es_raiz,
        "potencia_instalada": round(p_inst, 1), "potencia_demandada": round(p_dem, 1),
        "simultaneidad": simult, "Ib": round(Ib_board, 2),
        "alimentacion": {"tipo": tipo_linea, "longitud": L_feed, "seccion": s_feed, "seccion_txt": _fmt_s(s_feed),
                          "iz": round(iz_feed, 1), "caida_pct": round(caida_feed, 2),
                          "caida_acum_pct": round(caida_busbar, 2), "tierra": _fmt_s(tierra_feed)},
        "iga": iga, "iga_ok": iga_ok, "diferencial_general_ma": sens_gen,
        "cargas": cargas_out, "diferenciales": dif_out, "subcuadros": subs_out,
    }


def compute(data: dict) -> dict:
    suministro = data.get("suministro") or "monofasica"
    V = TENSION.get(suministro, 230)
    general = {
        "suministro": suministro, "V": V,
        "material": data.get("material") or "Cu",
        "tipo_instalacion": data.get("tipo_instalacion") or "otro",
        "caida_max_di": _num(data.get("caida_max_di"), 1.5),
        "caida_max_circuito": _num(data.get("caida_max_circuito"), 3),
        "caida_max_total_alumbrado": _num(data.get("caida_max_total_alumbrado"), 4.5),
        "caida_max_total_otros": _num(data.get("caida_max_total_otros"), 6.5),
    }
    root = data.get("cuadro") or {}
    if not root.get("cargas") and not root.get("subcuadros"):
        raise ValueError("Añade al menos una carga al cuadro para calcular el esquema.")

    obs, lineas, cuadro_pot = [], [], []
    arbol = _compute_board(root, general, 0.0, True, obs, lineas, cuadro_pot)

    estados = [l["estado"] for l in lineas]
    if "no_cumple" in estados:
        estado_global = "no_cumple"
    elif "observaciones" in estados:
        estado_global = "observaciones"
    else:
        estado_global = "cumple"

    total_inst = arbol["potencia_instalada"]
    total_dem = arbol["potencia_demandada"]
    resumen = [
        {"label": "Potencia instalada", "valor": f"{total_inst:g}", "unidad": "W"},
        {"label": "Potencia de cálculo", "valor": f"{total_dem:g}", "unidad": "W"},
        {"label": "Ib general", "valor": f"{arbol['Ib']:.1f}", "unidad": "A"},
        {"label": "IGA cabecera", "valor": f"{arbol['iga']}", "unidad": "A"},
    ]

    return {
        "estado_global": estado_global,
        "resumen": resumen,
        "arbol": arbol,
        "lineas": lineas,
        "cuadro_potencias": cuadro_pot,
        "observaciones": obs,
        "estancias": data.get("estancias") or [],
        "datos": {
            "suministro": suministro, "tension": V, "material": general["material"],
            "potencia_instalada": total_inst, "potencia_demandada": total_dem,
            "iga": arbol["iga"], "Ib": arbol["Ib"], "num_lineas": len(lineas),
        },
    }
