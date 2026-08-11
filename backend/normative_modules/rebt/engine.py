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
    METODOS_INSTALACION,
)

SQRT3 = math.sqrt(3)
_TIPO_OTROS = ("tomas", "fuerza", "motor", "clima", "otros")
_METODO_LABEL = {m["value"]: m["label"] for m in METODOS_INSTALACION}

# Sección mínima del conductor de fase por tipo de circuito final (ITC-BT-25, viviendas;
# criterio general de buena práctica para el resto): alumbrado 1,5 mm², tomas/fuerza 2,5 mm².
_SECCION_MIN = {"alumbrado": 1.5}
_SECCION_MIN_OTROS = 2.5

# Poder de corte mínimo recomendado del magnetotérmico (kA) según emplazamiento (ITC-BT-22,
# orientativo: contrastar con la Icc real en el punto de instalación).
_PODER_CORTE = {
    "vivienda_basica": 6, "vivienda_elevada": 6, "local_comercial": 6,
    "garaje": 6, "industrial": 10, "publica_concurrencia": 10, "otro": 6,
}

# Corriente de cortocircuito presunta en el origen (cabecera) por defecto (A), método
# simplificado de la Guía Técnica BT-22 (a falta de datos de red). Configurable por estudio.
_ICC_ORIGEN = {
    "vivienda_basica": 4500, "vivienda_elevada": 6000, "local_comercial": 6000,
    "garaje": 6000, "industrial": 10000, "publica_concurrencia": 10000, "otro": 6000,
}

# Constante térmica k del conductor (A·s^0,5/mm²), UNE 20460-4-43 / ITC-BT-22.
_K_TERMICO = {("Cu", "PVC"): 115, ("Cu", "XLPE"): 143, ("Al", "PVC"): 76, ("Al", "XLPE"): 94}

# Factor de disparo magnético Im = f·In según la curva del interruptor automático.
_IM_CURVA = {"B": 5, "C": 10, "D": 20}

# Sobre-resistencia del cable a temperatura de servicio (para la Icc mínima, conductor caliente).
_TEMP_FACTOR = 1.24


def _z_cable(L, gamma, s):
    """Resistencia por conductor del tramo (Ω). Se desprecia la reactancia (estudio orientativo)."""
    return (L / (gamma * s)) if (L > 0 and s > 0 and gamma > 0) else 0.0


def _icc(icc_origen, z_acum, m, U):
    """Icc en un punto: 1/Icc = 1/Icc_origen + m·Z_acum/U (impedancias en serie)."""
    if icc_origen <= 0:
        return 0.0
    inv = 1.0 / icc_origen + (m * z_acum / U if U > 0 else 0.0)
    return 1.0 / inv if inv > 0 else 0.0


# Poderes de corte normalizados (kA) para recomendación.
_PDC_NORM = [3, 4.5, 6, 10, 15, 25, 36, 50]


def _cortocircuito(general, z_up, L, s, In):
    """Comprobación frente a cortocircuitos (ITC-BT-22): poder de corte, resistencia térmica
    (k²·S² ≥ I²t) y actuación del disparo magnético (Icc_min ≥ Im). Incluye recomendación."""
    m = general["m"]; U = general["U_icc"]; gamma = general["gamma"]
    icc0 = general["icc_origen"]; k = general["k_term"]; t = general["t_disparo"]
    pdc = general["poder_corte_ka"] * 1000.0
    z_line = _z_cable(L, gamma, s)
    icc_max = _icc(icc0, z_up, m, U)                       # falta al inicio del cable (conductor frío)
    icc_min = _icc(icc0, (z_up + z_line) * _TEMP_FACTOR, m, U)  # falta al final (conductor caliente)
    i2t_cable = (k * s) ** 2                                # capacidad térmica del cable
    i2t_paso = (icc_max ** 2) * t                           # energía pasante estimada
    t_adm = (k * s / icc_max) ** 2 if icc_max > 0 else float("inf")
    im = In * general["im_factor"] if In else 0.0
    curva_used = general["curva"]
    curva_ajustada = False
    pdc_ok = pdc >= icc_max - 1e-6
    term_ok = i2t_cable >= i2t_paso - 1e-6
    mag_ok = (icc_min >= im - 1e-6) if In else True
    # Curva óptima (auto-dimensionado): si falla el disparo magnético, probar curvas más
    # sensibles (menor Im: D→C→B) sin superar la configurada, antes de aumentar la sección.
    if general.get("auto_cumplimiento") and In and not mag_ok:
        conf = general["im_factor"]
        for cv, f in sorted(_IM_CURVA.items(), key=lambda kv: -kv[1]):
            if f > conf:
                continue
            if icc_min >= In * f - 1e-6:
                im = In * f
                curva_used = cv
                curva_ajustada = (cv != general["curva"])
                mag_ok = True
                break
    # Recomendaciones cuando no cumple.
    s_term = (icc_max * (t ** 0.5) / k) if k > 0 else 0.0          # sección térmica mínima
    s_reco = next((x for x in SECCIONES if x >= s_term - 1e-9), SECCIONES[-1])
    pdc_reco = next((x for x in _PDC_NORM if x >= icc_max / 1000.0 - 1e-9), _PDC_NORM[-1])
    recos = []
    if not pdc_ok:
        recos.append(f"usar interruptores con poder de corte ≥ {pdc_reco:g} kA (Icc máx ≈ {icc_max/1000:.1f} kA)")
    if not term_ok:
        recos.append(f"aumentar la sección a ≥ {_fmt_s(s_reco)} mm² (o usar protección limitadora) para que k²·S² ≥ I²t")
    if not mag_ok and In:
        recos.append(f"reducir la longitud o aumentar la sección para elevar la Icc mín, o emplear curva B "
                     f"(Im menor); con la selección actual Im ≈ {im:.0f} A > Icc mín {icc_min:.0f} A")
    recomendacion = ("Recomendación: " + "; ".join(recos) + ".") if recos else None
    return {
        "icc_max_a": round(icc_max, 0), "icc_min_a": round(icc_min, 0),
        "im_a": round(im, 0), "curva": curva_used, "curva_original": general["curva"],
        "curva_ajustada": curva_ajustada,
        "i2t_cable": round(i2t_cable, 0), "i2t_paso": round(i2t_paso, 0),
        "t_adm_s": round(t_adm, 3) if t_adm != float("inf") else None, "t_disparo_s": t,
        "poder_corte_ka": general["poder_corte_ka"], "pdc_ok": pdc_ok,
        "termico_ok": term_ok, "magnetico_ok": mag_ok, "z_line": z_line,
        "protege_cc": bool(pdc_ok and term_ok and mag_ok),
        "seccion_min_termica": _fmt_s(s_reco), "pdc_recomendado_ka": pdc_reco,
        "recomendacion": recomendacion,
    }


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


def _seccion_min_tipo(tipo):
    return _SECCION_MIN.get(tipo, _SECCION_MIN_OTROS)


def _caida_real(suministro, L, P, gamma, V, s):
    if L <= 0 or P <= 0 or s <= 0 or V <= 0:
        return 0.0
    if suministro == "trifasica":
        e = (L * P) / (gamma * s * V)
    else:
        e = (2 * L * P) / (gamma * s * V)
    return e / V * 100.0


def _seccion_cdt_teorica(suministro, L, P, gamma, V, caida_max_pct):
    e_max = caida_max_pct / 100.0 * V if caida_max_pct > 0 else 0
    if L <= 0 or P <= 0 or e_max <= 0:
        return 0.0
    if suministro == "trifasica":
        return (L * P) / (gamma * e_max * V)
    return (2 * L * P) / (gamma * e_max * V)


def _idx_seccion_base(suministro, L, P, gamma, V, caida_max_pct, Ib, material, s_min, metodo="b1"):
    """Índice de la menor sección que cumple caída de tensión, calentamiento (Iz≥Ib) y sección mínima."""
    s_cdt = _seccion_cdt_teorica(suministro, L, P, gamma, V, caida_max_pct)
    for i, s in enumerate(SECCIONES):
        if s >= s_min - 1e-9 and s >= s_cdt - 1e-9 and ampacidad(s, material, metodo) >= Ib - 1e-9:
            return i
    return len(SECCIONES) - 1


def _breaker_fit(Ib, iz):
    """Menor calibre normalizado In tal que Ib ≤ In ≤ Iz (o None si no existe)."""
    for b in MAGNETOS:
        if b >= Ib - 1e-9 and b <= iz + 1e-9:
            return b
    return None


def _proteccion_dict(Ib, In, iz):
    """Coordinación magnetotérmico↔cable frente a sobrecargas (REBT ITC-BT-22 / IEC 60364-4-43).

    C1: Ib ≤ In ≤ Iz    C2: I2 ≤ 1,45·Iz, con I2 = 1,45·In (corriente convencional de disparo).
    """
    if In is None:
        return {"Ib": round(Ib, 2), "In": None, "Iz": round(iz, 1), "I2": None,
                "I2_max": round(1.45 * iz, 1), "cond_ib_in_iz": False, "cond_i2": False,
                "protege": False}
    i2 = 1.45 * In
    c1 = (Ib - 1e-9) <= In <= (iz + 1e-9)
    c2 = i2 <= 1.45 * iz + 1e-9
    return {"Ib": round(Ib, 2), "In": In, "Iz": round(iz, 1), "I2": round(i2, 1),
            "I2_max": round(1.45 * iz, 1), "cond_ib_in_iz": c1, "cond_i2": c2,
            "protege": bool(c1 and c2)}


def _coordinar(suministro, L, P, gamma, V, caida_max_pct, Ib, material, s_min, con_proteccion=True, metodo="b1"):
    """Dimensiona el cable y (si procede) su magnetotérmico garantizando que la protección
    protege al cable. Si con la sección mínima por caída/Ib no existe un calibre que cumpla
    Ib≤In≤Iz, aumenta automáticamente la sección hasta lograrlo.

    Devuelve: (seccion, Iz, caida_pct, In, proteccion, ajustada).
    """
    i0 = _idx_seccion_base(suministro, L, P, gamma, V, caida_max_pct, Ib, material, s_min, metodo)
    if not con_proteccion:
        s = SECCIONES[i0]
        return s, ampacidad(s, material, metodo), _caida_real(suministro, L, P, gamma, V, s), None, None, False
    for i in range(i0, len(SECCIONES)):
        s = SECCIONES[i]
        iz = ampacidad(s, material, metodo)
        In = _breaker_fit(Ib, iz)
        if In is not None:
            prot = _proteccion_dict(Ib, In, iz)
            return s, iz, _caida_real(suministro, L, P, gamma, V, s), In, prot, i > i0
    # Ningún calibre encaja ni ampliando: usar la mayor sección y el calibre más próximo.
    s = SECCIONES[-1]
    iz = ampacidad(s, material, metodo)
    In, _ = _breaker(Ib, iz)
    return s, iz, _caida_real(suministro, L, P, gamma, V, s), In, _proteccion_dict(Ib, In, iz), True


def _apply_seccion_manual(seccion_manual, suministro, L, P, gamma, V, Ib, material, auto, metodo="b1"):
    """Aplica una sección elegida manualmente por el técnico sobre el resultado automático.

    `auto` = tupla devuelta por `_coordinar` (s, iz, caida, In, prot, ajustada).
    Si `seccion_manual` es una sección normalizada válida, recalcula Iz, caída y la
    coordinación (Ib≤In≤Iz) frente a ESA sección; si no, devuelve el resultado automático.
    Devuelve: (s, iz, caida, In, prot, ajustada, s_auto, manual_ok).
    """
    s_a, iz_a, caida_a, In_a, prot_a, ajustada = auto
    sm = _num(seccion_manual) or None
    if not sm or float(sm) not in SECCIONES:
        return s_a, iz_a, caida_a, In_a, prot_a, ajustada, s_a, False
    s = float(sm)
    iz = ampacidad(s, material, metodo)
    caida = _caida_real(suministro, L, P, gamma, V, s)
    In = _breaker_fit(Ib, iz)
    prot = _proteccion_dict(Ib, In, iz)
    return s, iz, caida, In, prot, False, s_a, True


def _dimensionar_cumplimiento(general, z_up, L, P, Ib, material, s_min, suministro, V, caida_max_pct, gamma, metodo="b1"):
    """Dimensionado automático con cumplimiento REBT 100%: elige la menor sección normalizada
    que satisface a la vez la caída de tensión, la coordinación frente a sobrecargas
    (Ib≤In≤Iz e I2≤1,45·Iz) y las comprobaciones de cortocircuito (k²·S²≥I²t e Icc_mín≥Im)
    en el punto de instalación (z_up). Devuelve (s, iz, caida, In, prot, ajustada)."""
    i0 = _idx_seccion_base(suministro, L, P, gamma, V, caida_max_pct, Ib, material, s_min, metodo)
    for i in range(i0, len(SECCIONES)):
        s = SECCIONES[i]
        iz = ampacidad(s, material, metodo)
        In = _breaker_fit(Ib, iz)
        if In is None:
            continue
        prot = _proteccion_dict(Ib, In, iz)
        cc = _cortocircuito(general, z_up, L, s, In)
        if prot["protege"] and cc["termico_ok"] and cc["magnetico_ok"]:
            return s, iz, _caida_real(suministro, L, P, gamma, V, s), In, prot, i > i0
    # Ninguna sección lo cumple todo (p. ej. Icc muy elevada): usar la mayor disponible.
    s = SECCIONES[-1]
    iz = ampacidad(s, material, metodo)
    In = _breaker_fit(Ib, iz) or _breaker(Ib, iz)[0]
    return s, iz, _caida_real(suministro, L, P, gamma, V, s), In, _proteccion_dict(Ib, In, iz), True


def _seccion_caida(suministro, L, P, gamma, V, caida_max_pct, Ib, material, metodo="b1"):
    """Compat.: (seccion, Iz, caida_pct) sin coordinación de protección (usado por LGA)."""
    i0 = _idx_seccion_base(suministro, L, P, gamma, V, caida_max_pct, Ib, material, 0, metodo)
    s = SECCIONES[i0]
    return s, ampacidad(s, material, metodo), _caida_real(suministro, L, P, gamma, V, s)


def _breaker(Ib, Iz):
    b = _breaker_fit(Ib, Iz)
    if b is not None:
        return b, True
    cands = [x for x in MAGNETOS if x <= Iz + 1e-9]
    if cands:
        return cands[-1], False
    return next((x for x in MAGNETOS if x >= Ib), MAGNETOS[-1]), False


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
def _final_line(carga, general, caida_base, z_busbar, cuadro_nombre, dif_sens, obs, lineas, cuadro_pot):
    V = general["V"]; suministro = general["suministro"]
    material = general["material"]; gamma = CONDUCTIVIDAD.get(material, 56.0)
    P = _num(carga.get("potencia"))
    cosphi = _num(carga.get("cosphi"), 0.9) or 0.9
    L = _num(carga.get("longitud"))
    tipo = carga.get("tipo") or "otros"
    caida_max_c = _num(carga.get("caida_max"), general.get("caida_max_circuito", 3)) or 3
    Ib = _ib(suministro, P, V, cosphi)
    s_min = _seccion_min_tipo(tipo)
    metodo = carga.get("metodo_instalacion") or general.get("metodo_instalacion") or "b1"
    overload_tuple = _coordinar(suministro, L, P, gamma, V, caida_max_c, Ib, material, s_min, metodo=metodo)
    s_sobrecarga = overload_tuple[0]
    if general.get("auto_cumplimiento"):
        auto_tuple = _dimensionar_cumplimiento(general, z_busbar, L, P, Ib, material, s_min, suministro, V, caida_max_c, gamma, metodo)
    else:
        auto_tuple = overload_tuple
    s_el, iz, caida_c, In_auto, prot_auto, ajustada = auto_tuple
    s_el, iz, caida_c, In_auto, prot_auto, ajustada, s_auto, sec_manual_ok = _apply_seccion_manual(
        carga.get("seccion_manual"), suministro, L, P, gamma, V, Ib, material,
        (s_el, iz, caida_c, In_auto, prot_auto, ajustada), metodo)
    if In_auto is None:
        In_auto = _breaker(Ib, iz)[0]
    manual_in = int(_num(carga.get("magneto_manual"))) or None
    if manual_in:
        breaker = manual_in
        prot = _proteccion_dict(Ib, breaker, iz)
    else:
        breaker = In_auto
        prot = prot_auto
    caida_total = caida_base + caida_c
    br_ok = bool(prot and prot["protege"])
    cc = _cortocircuito(general, z_busbar, L, s_el, breaker)
    # Validación del diferencial: 30 mA recomendado en circuitos finales (protección de personas).
    dif_ok = int(dif_sens) <= 30
    dif_nota = ("Sensibilidad ≤ 30 mA: adecuada para protección de personas (contactos directos)."
                if dif_ok else "Sensibilidad 300 mA: solo protección de bienes/contactos indirectos; "
                "para circuitos finales se recomienda 30 mA (ITC-BT-24/25).")
    tierra = seccion_tierra(s_el)
    limite = _limite_total(general, tipo)
    cdt_ok = caida_total <= limite + 1e-6
    estado = "cumple"
    if P <= 0 or not cdt_ok:
        estado = "no_cumple"
    elif not br_ok:
        estado = "observaciones"
    elif not cc["protege_cc"]:
        estado = "observaciones"
    nombre = carga.get("nombre") or "Circuito"
    out = {
        "id": carga.get("id"), "nombre": nombre, "estancia": carga.get("estancia") or "",
        "tipo": tipo, "potencia": round(P, 1), "cosphi": cosphi, "longitud": L,
        "Ib": round(Ib, 2), "seccion": s_el, "seccion_txt": _fmt_s(s_el), "iz": round(iz, 1),
        "caida_pct": round(caida_c, 2), "caida_acum_pct": round(caida_total, 2), "limite_total": limite,
        "magneto": breaker, "sensibilidad": int(dif_sens), "tierra": _fmt_s(tierra),
        "estado": estado, "factor_uso": _num(carga.get("factor_uso"), 1) or 1,
        "proteccion": prot, "seccion_ajustada": ajustada, "seccion_min": s_min, "cortocircuito": cc,
    }
    lineas.append({
        "id": carga.get("id"), "cuadro": cuadro_nombre, "circuito": nombre, "tipo": "circuito",
        "potencia": round(P, 1), "Ib": round(Ib, 2), "seccion": s_el, "seccion_txt": _fmt_s(s_el),
        "iz": round(iz, 1), "caida_pct": round(caida_c, 2), "caida_acum_pct": round(caida_total, 2),
        "proteccion": f"{breaker} A", "diferencial": f"{int(dif_sens)} mA", "tierra": _fmt_s(tierra),
        "estado": estado, "longitud": L, "protege_cable": br_ok, "coordinacion": prot, "cortocircuito": cc,
        "magneto": breaker, "magneto_auto": In_auto, "magneto_manual": manual_in,
        "seleccion_manual": bool(manual_in), "sensibilidad": int(dif_sens),
        "diferencial_ok": dif_ok, "diferencial_nota": dif_nota, "editable": True,
        "seccion_auto": s_auto, "seccion_auto_txt": _fmt_s(s_auto),
        "seccion_manual": (s_el if sec_manual_ok else None), "seleccion_seccion_manual": sec_manual_ok,
        "seccion_min_sobrecarga": s_sobrecarga, "seccion_min_sobrecarga_txt": _fmt_s(s_sobrecarga),
        "metodo_instalacion": metodo, "metodo_label": _METODO_LABEL.get(metodo, metodo),
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
    elif P > 0 and not br_ok:
        if manual_in:
            obs.append({"tipo": "warning", "texto": f"«{cuadro_nombre} · {nombre}»: la selección manual del "
                        f"magnetotérmico ({manual_in} A) NO protege el cable (se requiere Ib≤In≤Iz e I2≤1,45·Iz; "
                        f"Ib {Ib:.1f} A, Iz {iz:.0f} A). Recomendado: {In_auto} A."})
        else:
            obs.append({"tipo": "warning", "texto": f"«{cuadro_nombre} · {nombre}»: no existe un calibre normalizado que "
                        f"proteja el cable (Ib {Ib:.1f} A, Iz {iz:.0f} A). Revise sección/protección."})
    elif ajustada and P > 0:
        obs.append({"tipo": "info", "texto": f"«{cuadro_nombre} · {nombre}»: se ha aumentado la sección a "
                    f"{_fmt_s(s_el)} mm² para que el magnetotérmico de {breaker} A proteja el cable "
                    f"(Ib≤In≤Iz e I2≤1,45·Iz, ITC-BT-22)."})
    if P > 0 and br_ok and not cc["protege_cc"]:
        if not cc["pdc_ok"]:
            obs.append({"tipo": "warning", "texto": f"«{cuadro_nombre} · {nombre}»: poder de corte insuficiente frente "
                        f"a cortocircuito: se prevé Icc máx ≈ {cc['icc_max_a']:.0f} A > {cc['poder_corte_ka']} kA "
                        f"del interruptor (ITC-BT-22). Aumente el poder de corte."})
        if not cc["termico_ok"]:
            obs.append({"tipo": "warning", "texto": f"«{cuadro_nombre} · {nombre}»: comprobación térmica de cortocircuito "
                        f"no cumple (k²·S² {cc['i2t_cable']:.0f} < I²t {cc['i2t_paso']:.0f}, ITC-BT-22). "
                        f"Aumente la sección o use protección más rápida."})
        if not cc["magnetico_ok"]:
            obs.append({"tipo": "warning", "texto": f"«{cuadro_nombre} · {nombre}»: la Icc mínima ({cc['icc_min_a']:.0f} A) "
                        f"no garantiza el disparo magnético (Im curva {cc['curva']} ≈ {cc['im_a']:.0f} A). "
                        f"Reduzca longitud/aumente sección o use una curva inferior."})
    return out


# ---------------------------------------------------------------------------
# Cálculo de un cuadro (recursivo)
# ---------------------------------------------------------------------------
def _compute_board(board, general, caida_base_pct, z_base, es_raiz, obs, lineas, cuadro_pot, board_id="__root__"):
    V = general["V"]; suministro = general["suministro"]
    material = general["material"]; gamma = CONDUCTIVIDAD.get(material, 56.0)

    nombre = board.get("nombre") or ("Cuadro general" if es_raiz else "Subcuadro")
    p_inst = _p_inst(board)
    p_dem = _p_dem(board)
    simult = _num(board.get("simultaneidad"), 1) or 1

    caida_busbar = caida_base_pct
    z_busbar = z_base
    lga_out = None
    lga = board.get("lga") or {}
    if es_raiz and lga.get("presente"):
        L = _num(lga.get("longitud"))
        cmax = _num(lga.get("caida_max"), general.get("caida_max_lga", 0.5)) or 0.5
        Ib_l = _ib(suministro, p_dem, V, 0.9)
        s_l, iz_l, caida_l = _seccion_caida(suministro, L, p_dem, gamma, V, cmax, Ib_l, material)
        caida_busbar += caida_l
        z_busbar += _z_cable(L, gamma, s_l)
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
    metodo_feed = board.get("metodo_instalacion") or general.get("metodo_instalacion") or "b1"
    feed_overload = _coordinar(suministro, L_feed, p_dem, gamma, V, caida_feed_max, Ib_board, material, 0, metodo=metodo_feed)
    s_feed_sobrecarga = feed_overload[0]
    if general.get("auto_cumplimiento"):
        feed_auto = _dimensionar_cumplimiento(general, z_busbar, L_feed, p_dem, Ib_board, material, 0, suministro, V, caida_feed_max, gamma, metodo_feed)
    else:
        feed_auto = feed_overload
    s_feed, iz_feed, caida_feed, In_feed, prot_feed, ajustada_feed = feed_auto
    s_feed, iz_feed, caida_feed, In_feed, prot_feed, ajustada_feed, s_feed_auto, sec_feed_manual = _apply_seccion_manual(
        board.get("seccion_manual"), suministro, L_feed, p_dem, gamma, V, Ib_board, material,
        (s_feed, iz_feed, caida_feed, In_feed, prot_feed, ajustada_feed), metodo_feed)
    iga_manual = board.get("iga_manual")
    if iga_manual:
        iga = int(_num(iga_manual))
        prot_feed = _proteccion_dict(Ib_board, iga, iz_feed)
        iga_ok = prot_feed["protege"]
    else:
        iga = In_feed if In_feed is not None else _breaker(Ib_board, iz_feed)[0]
        iga_ok = bool(prot_feed and prot_feed["protege"])
    iga_auto = In_feed if In_feed is not None else _breaker(Ib_board, iz_feed)[0]
    tierra_feed = seccion_tierra(s_feed)
    cc_feed = _cortocircuito(general, z_busbar, L_feed, s_feed, iga)
    caida_busbar += caida_feed
    z_busbar += _z_cable(L_feed, gamma, s_feed)
    sens_gen = int(_num((board.get("diferencial_general") or {}).get("sensibilidad"), 300) or 300)
    spd = board.get("spd") or {}
    spd_out = {"presente": bool(spd.get("presente")), "tipo": spd.get("tipo") or "T2"}

    feed_estado = "cumple" if (iga_ok and cc_feed["protege_cc"]) else "observaciones"
    tipo_linea = "Acometida / DI" if es_raiz else "Línea puente (alimentación subcuadro)"
    lineas.append({
        "board_id": board_id, "cuadro": nombre, "circuito": tipo_linea, "tipo": "alimentacion",
        "potencia": round(p_dem, 1), "Ib": round(Ib_board, 2), "seccion": s_feed, "seccion_txt": _fmt_s(s_feed),
        "iz": round(iz_feed, 1), "caida_pct": round(caida_feed, 2), "caida_acum_pct": round(caida_busbar, 2),
        "proteccion": f"IGA {iga} A", "diferencial": f"{sens_gen} mA (general)",
        "tierra": _fmt_s(tierra_feed), "estado": feed_estado,
        "longitud": L_feed, "protege_cable": iga_ok, "coordinacion": prot_feed, "cortocircuito": cc_feed,
        "magneto": iga, "magneto_auto": iga_auto, "magneto_manual": (int(_num(iga_manual)) or None),
        "seleccion_manual": bool(iga_manual), "sensibilidad": sens_gen,
        "editable_board": True, "es_alimentacion": True,
        "seccion_auto": s_feed_auto, "seccion_auto_txt": _fmt_s(s_feed_auto),
        "seccion_manual": (s_feed if sec_feed_manual else None), "seleccion_seccion_manual": sec_feed_manual,
        "seccion_min_sobrecarga": s_feed_sobrecarga, "seccion_min_sobrecarga_txt": _fmt_s(s_feed_sobrecarga),
        "metodo_instalacion": metodo_feed, "metodo_label": _METODO_LABEL.get(metodo_feed, metodo_feed),
    })
    if not iga_ok:
        obs.append({"tipo": "warning", "texto": f"«{nombre}»: el IGA ({iga} A) no protege el cable de alimentación "
                    f"(no se cumple Ib≤In≤Iz / I2≤1,45·Iz; Ib {Ib_board:.1f} A, Iz {iz_feed:.0f} A). "
                    f"Recomendado: {iga_auto} A."})
    elif ajustada_feed and not iga_manual:
        obs.append({"tipo": "info", "texto": f"«{nombre}»: sección de la línea de alimentación aumentada a "
                    f"{_fmt_s(s_feed)} mm² para que el IGA de {iga} A proteja el cable (ITC-BT-22)."})
    if iga_ok and not cc_feed["protege_cc"] and cc_feed.get("recomendacion"):
        obs.append({"tipo": "warning", "texto": f"«{nombre} · {tipo_linea}»: no cumple la comprobación de "
                    f"cortocircuito. {cc_feed['recomendacion']}"})
    if es_raiz and not spd_out["presente"]:
        obs.append({"tipo": "info", "texto": "No se ha previsto protector contra sobretensiones (SPD). Valore su "
                    "instalación conforme a la ITC-BT-23 según la categoría de sobretensión y el riesgo."})

    nodos_out = []
    for node in board.get("nodos", []):
        k = node.get("kind")
        if k == "linea":
            dif_sens = int(_num(node.get("sensibilidad"), 30)) if node.get("dif_propio") else sens_gen
            out = _final_line(node, general, caida_busbar, z_busbar, nombre, dif_sens, obs, lineas, cuadro_pot)
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
            metodo_p = node.get("metodo_instalacion") or general.get("metodo_instalacion") or "b1"
            p_overload = _coordinar(suministro, L_p, p_dem_p, gamma, V, caida_max_p, Ib_p, material, _SECCION_MIN_OTROS, metodo=metodo_p)
            s_p_sobrecarga = p_overload[0]
            if general.get("auto_cumplimiento"):
                p_auto = _dimensionar_cumplimiento(general, z_busbar, L_p, p_dem_p, Ib_p, material, _SECCION_MIN_OTROS, suministro, V, caida_max_p, gamma, metodo_p)
            else:
                p_auto = p_overload
            s_p, iz_p, caida_p, In_p, prot_p, ajustada_p = p_auto
            s_p, iz_p, caida_p, In_p, prot_p, ajustada_p, s_p_auto, sec_p_manual = _apply_seccion_manual(
                node.get("seccion_manual"), suministro, L_p, p_dem_p, gamma, V, Ib_p, material,
                (s_p, iz_p, caida_p, In_p, prot_p, ajustada_p), metodo_p)
            In_p_auto = In_p if In_p is not None else _breaker(Ib_p, iz_p)[0]
            manual_p = int(_num(node.get("magneto_manual"))) or None
            if manual_p:
                magneto_p = manual_p
                prot_p = _proteccion_dict(Ib_p, magneto_p, iz_p)
            else:
                magneto_p = In_p_auto
            ok_p = bool(prot_p and prot_p["protege"])
            cc_p = _cortocircuito(general, z_busbar, L_p, s_p, magneto_p)
            caida_busbar_p = caida_busbar + caida_p
            z_busbar_p = z_busbar + _z_cable(L_p, gamma, s_p)
            sens_p = int(_num(node.get("sensibilidad"), 30) or 30)
            tierra_p = seccion_tierra(s_p)
            estado_p = "cumple" if (ok_p and cc_p["protege_cc"]) else "observaciones"
            lineas.append({
                "id": node.get("id"), "cuadro": nombre, "circuito": f"{pnombre} (puente)", "tipo": "puente",
                "potencia": round(p_dem_p, 1), "Ib": round(Ib_p, 2), "seccion": s_p, "seccion_txt": _fmt_s(s_p),
                "iz": round(iz_p, 1), "caida_pct": round(caida_p, 2), "caida_acum_pct": round(caida_busbar_p, 2),
                "proteccion": f"{magneto_p} A", "diferencial": f"{sens_p} mA", "tierra": _fmt_s(tierra_p),
                "estado": estado_p, "longitud": L_p,
                "protege_cable": ok_p, "coordinacion": prot_p, "cortocircuito": cc_p,
                "magneto": magneto_p, "magneto_auto": In_p_auto, "magneto_manual": manual_p,
                "seleccion_manual": bool(manual_p), "sensibilidad": sens_p, "editable": True, "es_puente": True,
                "seccion_auto": s_p_auto, "seccion_auto_txt": _fmt_s(s_p_auto),
                "seccion_manual": (s_p if sec_p_manual else None), "seleccion_seccion_manual": sec_p_manual,
                "seccion_min_sobrecarga": s_p_sobrecarga, "seccion_min_sobrecarga_txt": _fmt_s(s_p_sobrecarga),
                "metodo_instalacion": metodo_p, "metodo_label": _METODO_LABEL.get(metodo_p, metodo_p),
            })
            if not ok_p:
                sug = f" Recomendado: {In_p_auto} A." if manual_p else ""
                obs.append({"tipo": "warning", "texto": f"«{nombre} · {pnombre}»: el magnetotérmico de la línea "
                            f"puente ({magneto_p} A) no protege el cable (Ib≤In≤Iz / I2≤1,45·Iz; Ib {Ib_p:.1f} A, "
                            f"Iz {iz_p:.0f} A).{sug}"})
            elif ajustada_p:
                obs.append({"tipo": "info", "texto": f"«{nombre} · {pnombre}»: sección de la línea puente aumentada a "
                            f"{_fmt_s(s_p)} mm² para que el magnetotérmico de {magneto_p} A proteja el cable (ITC-BT-22)."})
            sub_out = []
            for sub in node.get("sublineas", []):
                o = _final_line(sub, general, caida_busbar_p, z_busbar_p, nombre, sens_p, obs, lineas, cuadro_pot)
                sub_out.append(o)
            nodos_out.append({
                "kind": "puente", "id": node.get("id"), "nombre": pnombre, "longitud": L_p,
                "potencia": round(p_dem_p, 1), "Ib": round(Ib_p, 2), "seccion_txt": _fmt_s(s_p),
                "iz": round(iz_p, 1), "caida_pct": round(caida_p, 2), "caida_acum_pct": round(caida_busbar_p, 2),
                "magneto": magneto_p, "sensibilidad": sens_p, "tierra": _fmt_s(tierra_p),
                "estado": estado_p, "sublineas": sub_out,
                "proteccion": prot_p, "protege_cable": ok_p, "cortocircuito": cc_p,
            })
        elif k == "subcuadro":
            sub_arbol = _compute_board(node.get("board") or {}, general, caida_busbar, z_busbar, False, obs, lineas, cuadro_pot, board_id=node.get("id") or "sub")
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
    material = data.get("material") or "Cu"
    tipo_inst = data.get("tipo_instalacion") or "otro"
    aislamiento = (data.get("aislamiento") or "PVC").upper()
    curva = (data.get("curva") or "C").upper()
    poder_corte = int(_num(data.get("poder_corte_ka"), _PODER_CORTE.get(tipo_inst, 6)))
    auto_cumplimiento = bool(data.get("auto_cumplimiento"))
    icc_origen = _num(data.get("icc_origen_a"), _ICC_ORIGEN.get(tipo_inst, 6000))
    pdc_ajustado = False
    if auto_cumplimiento:
        pdc_needed = next((x for x in _PDC_NORM if x >= icc_origen / 1000.0 - 1e-9), _PDC_NORM[-1])
        if pdc_needed > poder_corte:
            poder_corte = pdc_needed
            pdc_ajustado = True
    general = {
        "suministro": suministro, "V": V,
        "material": material,
        "tipo_instalacion": tipo_inst,
        "auto_cumplimiento": auto_cumplimiento,
        "gamma": CONDUCTIVIDAD.get(material, 56.0),
        "caida_max_lga": _num(data.get("caida_max_lga"), 0.5),
        "caida_max_di": _num(data.get("caida_max_di"), 1.5),
        "caida_max_circuito": _num(data.get("caida_max_circuito"), 3),
        "caida_max_total_alumbrado": _num(data.get("caida_max_total_alumbrado"), 3),
        "caida_max_total_otros": _num(data.get("caida_max_total_otros"), 5),
        # Cortocircuito (ITC-BT-22)
        "m": SQRT3 if suministro == "trifasica" else 2.0,
        "U_icc": V,
        "icc_origen": icc_origen,
        "aislamiento": aislamiento,
        "k_term": _K_TERMICO.get((material, aislamiento), 115),
        "curva": curva,
        "im_factor": _IM_CURVA.get(curva, 10),
        "t_disparo": _num(data.get("t_disparo_s"), 0.01) or 0.01,
        "poder_corte_ka": poder_corte,
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
    arbol = _compute_board(root, general, 0.0, 0.0, True, obs, lineas, cuadro_pot)

    icc_max_global = max((l.get("cortocircuito", {}).get("icc_max_a", 0) or 0 for l in lineas), default=0)
    obs.append({"tipo": "info", "texto": f"Cortocircuito (ITC-BT-22, método simplificado): Icc presunta en origen "
                f"{general['icc_origen']/1000:.1f} kA; Icc máx. calculada {icc_max_global/1000:.1f} kA. Poder de corte "
                f"recomendado de los interruptores ≥ {poder_corte} kA (conductor {material}/{aislamiento}, k={general['k_term']}; "
                f"curva {curva}). Contrastar con la Icc real del punto de instalación."})
    if auto_cumplimiento:
        no_cc = [l for l in lineas if l.get("cortocircuito") and not l["cortocircuito"].get("protege_cc")
                 and not l.get("seleccion_manual") and not l.get("seleccion_seccion_manual")]
        base = ("Dimensionado automático (cumplimiento REBT 100%) activado: se han ajustado las secciones "
                "para cumplir sobrecarga (Ib≤In≤Iz, I2≤1,45·Iz) y cortocircuito (k²·S²≥I²t, Icc_mín≥Im) en cada línea")
        if pdc_ajustado:
            base += f"; el poder de corte de los interruptores se ha elevado a {poder_corte} kA para superar la Icc presunta en origen"
        base += ". Revise y valide el dimensionado propuesto (estudio orientativo, no vinculante)."
        obs.append({"tipo": "info", "texto": base})
        curva_adj = [l for l in lineas if (l.get("cortocircuito") or {}).get("curva_ajustada")]
        if curva_adj:
            det = "; ".join(f"«{l.get('circuito', '')}» → curva {l['cortocircuito']['curva']}" for l in curva_adj)
            obs.append({"tipo": "info", "texto": "Para garantizar el disparo magnético (Icc_mín≥Im) sin aumentar "
                        f"la sección, se ha ajustado la curva del interruptor en: {det} (curva original "
                        f"{curva}). Verifique que la curva elegida no provoque disparos intempestivos por corrientes de arranque."})
        if no_cc:
            obs.append({"tipo": "warning", "texto": "Con dimensionado automático, las siguientes líneas no pueden "
                        "cumplir cortocircuito solo aumentando la sección (Icc demasiado elevada o límites de "
                        f"catálogo): {', '.join(l.get('circuito', '') for l in no_cc)}. Considere protección "
                        "limitadora de corriente, reducir la longitud o revisar la Icc presunta en origen."})

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
            "spd": arbol["spd"], "poder_corte_ka": poder_corte,
            "auto_cumplimiento": auto_cumplimiento, "pdc_ajustado": pdc_ajustado,
        },
    }
