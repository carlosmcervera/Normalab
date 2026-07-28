"""Motor de cálculo REBT (RD 842/2002): cuadro eléctrico con esquema unifilar.

Modelo de árbol por cuadro:
  cabecera = línea de alimentación (LGA opcional + DI en la raíz; línea puente larga
  en subcuadros) + IGA (magnetotérmico general) + diferencial general + protector de
  sobretensiones (SPD). De la cabecera cuelgan nodos:
    - "linea"     : circuito final directo (magnetotérmico + diferencial propio o el general).
    - "puente"    : línea puente física (diferencial + magnetotérmico + longitud) que alimenta
                    una o varias sublíneas; las sublíneas comparten el diferencial de la puente
                    y cada una lleva su magnetotérmico.
    - "subcuadro" : cuadro anidado (línea puente más larga) con su propio esquema (recursivo).

Dimensiona todas las líneas con las comprobaciones del REBT (Ib, sección por caída de
tensión y calentamiento ITC-BT-19, magnetotérmico Ib≤In≤Iz, diferencial, tierra ITC-BT-18).
"""
import math

from normative_modules.rebt.catalog import (
    TENSION, CONDUCTIVIDAD, SECCIONES, MAGNETOS, ampacidad, seccion_tierra,
)

SQRT3 = math.sqrt(3)
_TIPO_OTROS = ("tomas", "fuerza", "motor", "clima", "otros")


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
        return _num(general.get("caida_max_total_alumbrado"), 3) or 3
    return _num(general.get("caida_max_total_otros"), 5) or 5


def _fmt_s(s):
    return f"{s:g}".replace(".", ",")


# ---------------------------------------------------------------------------
# Migración del modelo antiguo (cargas/diferenciales/subcuadros) al nuevo (nodos).
# ---------------------------------------------------------------------------
def _migrate_board(board):
    if not isinstance(board, dict):
        return {"nombre": "Cuadro general", "nodos": []}
    if "nodos" in board:
        # Asegura sub-boards de subcuadros migrados también.
        for n in board.get("nodos", []):
            if n.get("kind") == "subcuadro":
                n["board"] = _migrate_board(n.get("board") or {})
        return board
    nodos = []
    for c in board.get("cargas", []):
        nodos.append({
            "id": c.get("id"), "kind": "linea", "nombre": c.get("nombre"),
            "tipo": c.get("tipo") or "otros", "potencia": c.get("potencia"),
            "cosphi": c.get("cosphi", 0.9), "factor_uso": c.get("factor_uso", 1),
            "longitud": c.get("longitud"), "estancia": c.get("estancia") or "",
            "dif_propio": False, "sensibilidad": 30,
        })
    for sc in board.get("subcuadros", []):
        nodos.append({"id": sc.get("id"), "kind": "subcuadro", "board": _migrate_board(sc)})
    return {
        "id": board.get("id"), "nombre": board.get("nombre"),
        "alim": {"longitud": board.get("longitud"), "cosphi": board.get("cosphi", 0.9)},
        "simultaneidad": board.get("simultaneidad", 1),
        "diferencial_general": {"sensibilidad": board.get("sensibilidad_general", 300)},
        "spd": {"presente": False, "tipo": "T2"},
        "lga": {"presente": False},
        "nodos": nodos,
    }


# ---------------------------------------------------------------------------
# Potencias
# ---------------------------------------------------------------------------
def _p_inst(board):
    p = 0.0
    for n in board.get("nodos", []):
        k = n.get("kind")
        if k == "linea":
            p += _num(n.get("potencia"))
        elif k == "puente":
            p += sum(_num(s.get("potencia")) for s in n.get("sublineas", []))
        elif k == "subcuadro":
            p += _p_inst(n.get("board") or {})
    return p


def _p_dem(board):
    p = 0.0
    for n in board.get("nodos", []):
        k = n.get("kind")
        if k == "linea":
            p += _num(n.get("potencia")) * (_num(n.get("factor_uso"), 1) or 1)
        elif k == "puente":
            sp = sum(_num(s.get("potencia")) * (_num(s.get("factor_uso"), 1) or 1) for s in n.get("sublineas", []))
            p += sp * (_num(n.get("simultaneidad"), 1) or 1)
        elif k == "subcuadro":
            p += _p_dem(n.get("board") or {})
    return p * (_num(board.get("simultaneidad"), 1) or 1)


# ---------------------------------------------------------------------------
# Cálculo de un circuito final (línea directa o sublínea de puente)
# ---------------------------------------------------------------------------
def _final_line(carga, general, caida_base, cuadro_nombre, dif_sens, obs, lineas, cuadro_pot):
    V = general["V"]; suministro = general["suministro"]
    material = general["material"]; gamma = CONDUCTIVIDAD.get(material, 56.0)
    P = _num(carga.get("potencia"))
    cosphi = _num(carga.get("cosphi"), 0.9) or 0.9
    L = _num(carga.get("longitud"))
    tipo = carga.get("tipo") or "otros"
    caida_max_c = _num(carga.get("caida_max"), general.get("caida_max_circuito", 3)) or 3
    Ib = _ib(suministro, P, V, cosphi)
    s_el, iz, caida_c = _seccion_caida(suministro, L, P, gamma, V, caida_max_c, Ib, material)
    caida_total = caida_base + caida_c
    breaker, br_ok = _breaker(Ib, iz)
    tierra = seccion_tierra(s_el)
    limite = _limite_total(general, tipo)
    cdt_ok = caida_total <= limite + 1e-6
    estado = "cumple"
    if P <= 0 or not cdt_ok:
        estado = "no_cumple"
    elif not br_ok:
        estado = "observaciones"
    nombre = carga.get("nombre") or "Circuito"
    out = {
        "id": carga.get("id"), "nombre": nombre, "estancia": carga.get("estancia") or "",
        "tipo": tipo, "potencia": round(P, 1), "cosphi": cosphi, "longitud": L,
        "Ib": round(Ib, 2), "seccion": s_el, "seccion_txt": _fmt_s(s_el), "iz": round(iz, 1),
        "caida_pct": round(caida_c, 2), "caida_acum_pct": round(caida_total, 2), "limite_total": limite,
        "magneto": breaker, "sensibilidad": int(dif_sens), "tierra": _fmt_s(tierra),
        "estado": estado, "factor_uso": _num(carga.get("factor_uso"), 1) or 1,
    }
    lineas.append({
        "cuadro": cuadro_nombre, "circuito": nombre, "tipo": "circuito",
        "potencia": round(P, 1), "Ib": round(Ib, 2), "seccion": s_el, "seccion_txt": _fmt_s(s_el),
        "iz": round(iz, 1), "caida_pct": round(caida_c, 2), "caida_acum_pct": round(caida_total, 2),
        "proteccion": f"{breaker} A", "diferencial": f"{int(dif_sens)} mA", "tierra": _fmt_s(tierra),
        "estado": estado, "longitud": L,
    })
    cuadro_pot.append({
        "cuadro": cuadro_nombre, "circuito": nombre, "tipo": tipo,
        "potencia": round(P, 1), "factor_uso": _num(carga.get("factor_uso"), 1) or 1,
        "potencia_calculo": round(P * (_num(carga.get("factor_uso"), 1) or 1), 1),
    })
    if not cdt_ok and P > 0:
        obs.append({"tipo": "error", "texto": f"«{cuadro_nombre} · {nombre}»: caída de tensión acumulada "
                    f"{caida_total:.2f} % supera el límite del {limite:g} % "
                    f"({'alumbrado' if tipo == 'alumbrado' else 'otros usos'}). Aumente la sección."})
    return out


# ---------------------------------------------------------------------------
# Cálculo de un cuadro (recursivo)
# ---------------------------------------------------------------------------
def _compute_board(board, general, caida_base_pct, es_raiz, obs, lineas, cuadro_pot):
    V = general["V"]; suministro = general["suministro"]
    material = general["material"]; gamma = CONDUCTIVIDAD.get(material, 56.0)

    nombre = board.get("nombre") or ("Cuadro general" if es_raiz else "Subcuadro")
    p_inst = _p_inst(board)
    p_dem = _p_dem(board)
    simult = _num(board.get("simultaneidad"), 1) or 1

    caida_busbar = caida_base_pct
    lga_out = None
    lga = board.get("lga") or {}
    if es_raiz and lga.get("presente"):
        L = _num(lga.get("longitud"))
        cmax = _num(lga.get("caida_max"), general.get("caida_max_lga", 0.5)) or 0.5
        Ib_l = _ib(suministro, p_dem, V, 0.9)
        s_l, iz_l, caida_l = _seccion_caida(suministro, L, p_dem, gamma, V, cmax, Ib_l, material)
        caida_busbar += caida_l
        lga_out = {"seccion_txt": _fmt_s(s_l), "longitud": L, "caida_pct": round(caida_l, 2),
                   "caida_acum_pct": round(caida_busbar, 2)}
        lineas.append({
            "cuadro": nombre, "circuito": "Línea general de alimentación (LGA)", "tipo": "alimentacion",
            "potencia": round(p_dem, 1), "Ib": round(Ib_l, 2), "seccion": s_l, "seccion_txt": _fmt_s(s_l),
            "iz": round(iz_l, 1), "caida_pct": round(caida_l, 2), "caida_acum_pct": round(caida_busbar, 2),
            "proteccion": "—", "diferencial": "—", "tierra": _fmt_s(seccion_tierra(s_l)),
            "estado": "cumple", "longitud": L,
        })

    alim = board.get("alim") or {}
    L_feed = _num(alim.get("longitud"))
    cosphi_gen = _num(alim.get("cosphi"), 0.9) or 0.9
    caida_feed_max = _num(alim.get("caida_max"), general.get("caida_max_di", 1.5) if es_raiz else 1.5) or 1.5
    Ib_board = _ib(suministro, p_dem, V, cosphi_gen)
    s_feed, iz_feed, caida_feed = _seccion_caida(suministro, L_feed, p_dem, gamma, V, caida_feed_max, Ib_board, material)
    iga_manual = board.get("iga_manual")
    if iga_manual:
        iga = int(_num(iga_manual))
        iga_ok = (Ib_board <= iga + 1e-9) and (iga <= iz_feed + 1e-9)
    else:
        iga, iga_ok = _breaker(Ib_board, iz_feed)
    tierra_feed = seccion_tierra(s_feed)
    caida_busbar += caida_feed
    sens_gen = int(_num((board.get("diferencial_general") or {}).get("sensibilidad"), 300) or 300)
    spd = board.get("spd") or {}
    spd_out = {"presente": bool(spd.get("presente")), "tipo": spd.get("tipo") or "T2"}

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
        obs.append({"tipo": "warning", "texto": f"«{nombre}»: no hay calibre de IGA que cumpla Ib≤In≤Iz "
                    f"(Ib {Ib_board:.1f} A, Iz {iz_feed:.0f} A). Revise la sección de la línea de alimentación."})
    if es_raiz and not spd_out["presente"]:
        obs.append({"tipo": "info", "texto": "No se ha previsto protector contra sobretensiones (SPD). Valore su "
                    "instalación conforme a la ITC-BT-23 según la categoría de sobretensión y el riesgo."})

    nodos_out = []
    for node in board.get("nodos", []):
        k = node.get("kind")
        if k == "linea":
            dif_sens = int(_num(node.get("sensibilidad"), 30)) if node.get("dif_propio") else sens_gen
            out = _final_line(node, general, caida_busbar, nombre, dif_sens, obs, lineas, cuadro_pot)
            out["kind"] = "linea"
            out["dif_propio"] = bool(node.get("dif_propio"))
            nodos_out.append(out)
        elif k == "puente":
            pnombre = node.get("nombre") or "Línea puente"
            simult_p = _num(node.get("simultaneidad"), 1) or 1
            cosphi_p = _num(node.get("cosphi"), 0.9) or 0.9
            L_p = _num(node.get("longitud"))
            p_dem_p = sum(_num(s.get("potencia")) * (_num(s.get("factor_uso"), 1) or 1)
                          for s in node.get("sublineas", [])) * simult_p
            caida_max_p = _num(node.get("caida_max"), general.get("caida_max_circuito", 3)) or 3
            Ib_p = _ib(suministro, p_dem_p, V, cosphi_p)
            s_p, iz_p, caida_p = _seccion_caida(suministro, L_p, p_dem_p, gamma, V, caida_max_p, Ib_p, material)
            caida_busbar_p = caida_busbar + caida_p
            magneto_p, ok_p = _breaker(Ib_p, iz_p)
            sens_p = int(_num(node.get("sensibilidad"), 30) or 30)
            tierra_p = seccion_tierra(s_p)
            lineas.append({
                "cuadro": nombre, "circuito": f"{pnombre} (puente)", "tipo": "puente",
                "potencia": round(p_dem_p, 1), "Ib": round(Ib_p, 2), "seccion": s_p, "seccion_txt": _fmt_s(s_p),
                "iz": round(iz_p, 1), "caida_pct": round(caida_p, 2), "caida_acum_pct": round(caida_busbar_p, 2),
                "proteccion": f"{magneto_p} A", "diferencial": f"{sens_p} mA", "tierra": _fmt_s(tierra_p),
                "estado": "cumple" if ok_p else "observaciones", "longitud": L_p,
            })
            if not ok_p:
                obs.append({"tipo": "warning", "texto": f"«{nombre} · {pnombre}»: el magnetotérmico de la línea "
                            f"puente no cumple Ib≤In≤Iz (Ib {Ib_p:.1f} A, Iz {iz_p:.0f} A)."})
            sub_out = []
            for sub in node.get("sublineas", []):
                o = _final_line(sub, general, caida_busbar_p, nombre, sens_p, obs, lineas, cuadro_pot)
                sub_out.append(o)
            nodos_out.append({
                "kind": "puente", "id": node.get("id"), "nombre": pnombre, "longitud": L_p,
                "potencia": round(p_dem_p, 1), "Ib": round(Ib_p, 2), "seccion_txt": _fmt_s(s_p),
                "iz": round(iz_p, 1), "caida_pct": round(caida_p, 2), "caida_acum_pct": round(caida_busbar_p, 2),
                "magneto": magneto_p, "sensibilidad": sens_p, "tierra": _fmt_s(tierra_p),
                "estado": "cumple" if ok_p else "observaciones", "sublineas": sub_out,
            })
        elif k == "subcuadro":
            sub_arbol = _compute_board(node.get("board") or {}, general, caida_busbar, False, obs, lineas, cuadro_pot)
            nodos_out.append({"kind": "subcuadro", "id": node.get("id"), "board": sub_arbol})

    return {
        "id": board.get("id"), "nombre": nombre, "es_raiz": es_raiz,
        "potencia_instalada": round(p_inst, 1), "potencia_demandada": round(p_dem, 1),
        "simultaneidad": simult, "Ib": round(Ib_board, 2),
        "alimentacion": {"tipo": tipo_linea, "longitud": L_feed, "seccion": s_feed, "seccion_txt": _fmt_s(s_feed),
                         "iz": round(iz_feed, 1), "caida_pct": round(caida_feed, 2),
                         "caida_acum_pct": round(caida_busbar, 2), "tierra": _fmt_s(tierra_feed)},
        "lga": lga_out,
        "iga": iga, "iga_ok": iga_ok, "diferencial_general_ma": sens_gen, "spd": spd_out,
        "nodos": nodos_out,
    }


def compute(data: dict) -> dict:
    suministro = data.get("suministro") or "monofasica"
    V = TENSION.get(suministro, 230)
    general = {
        "suministro": suministro, "V": V,
        "material": data.get("material") or "Cu",
        "tipo_instalacion": data.get("tipo_instalacion") or "otro",
        "caida_max_lga": _num(data.get("caida_max_lga"), 0.5),
        "caida_max_di": _num(data.get("caida_max_di"), 1.5),
        "caida_max_circuito": _num(data.get("caida_max_circuito"), 3),
        "caida_max_total_alumbrado": _num(data.get("caida_max_total_alumbrado"), 3),
        "caida_max_total_otros": _num(data.get("caida_max_total_otros"), 5),
    }
    root = _migrate_board(data.get("cuadro") or {})
    has_load = any(
        (n.get("kind") == "linea") or
        (n.get("kind") == "puente" and n.get("sublineas")) or
        (n.get("kind") == "subcuadro")
        for n in root.get("nodos", [])
    )
    if not has_load:
        raise ValueError("Añade al menos una carga o línea al cuadro para calcular el esquema.")

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
            "spd": arbol["spd"],
        },
    }
