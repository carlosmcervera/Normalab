"""Motor de comprobación de una única línea de baja tensión (REBT).

Verifica el cumplimiento de una línea: intensidad de diseño (Ib), intensidad máxima
admisible (Iz) según ITC-BT-19/UNE-HD 60364-5-52 con **factor de agrupamiento** por
circuitos que comparten canalización (Tabla B.52.17), caída de tensión y cortocircuito
(ITC-BT-22). Estudio orientativo, no vinculante.
"""
from normative_modules.rebt import engine as reng
from normative_modules.rebt.catalog import (
    TENSION, CONDUCTIVIDAD, SECCIONES, ampacidad, seccion_tierra, METODOS_INSTALACION,
)

# Tabla B.52.17 (UNE-HD 60364-5-52): factores de reducción por agrupamiento de circuitos.
_AGRUP = {
    "haz":        {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 6: 0.60, 9: 0.57, 12: 0.54, 16: 0.52, 20: 0.50},
    "capa_pared": {1: 1.00, 2: 0.85, 3: 0.79, 4: 0.75, 6: 0.73, 9: 0.72, 12: 0.72, 16: 0.71, 20: 0.70},
    "capa_perf":  {1: 1.00, 2: 0.88, 3: 0.82, 4: 0.77, 6: 0.75, 9: 0.73, 12: 0.73, 16: 0.72, 20: 0.72},
    "capa_esc":   {1: 1.00, 2: 0.87, 3: 0.82, 4: 0.80, 6: 0.80, 9: 0.79, 12: 0.79, 16: 0.78, 20: 0.78},
}
_AGRUP_LABEL = {
    "haz": "Agrupados en el aire/superficie, empotrados o bajo tubo/canaleta (B.52.17-1)",
    "capa_pared": "Capa única sobre pared, suelo o bandeja sin perforar (B.52.17-2)",
    "capa_perf": "Capa única sobre bandeja perforada (B.52.17-4)",
    "capa_esc": "Capa única sobre bandeja de escalera/soportes (B.52.17-5)",
}
_METODO_LABEL = {m["value"]: m["label"] for m in METODOS_INSTALACION}


def _factor_agrupamiento(disposicion, n):
    tabla = _AGRUP.get(disposicion or "haz", _AGRUP["haz"])
    n = max(1, int(n or 1))
    if n in tabla:
        return tabla[n]
    keys = sorted(tabla)
    for k in keys:
        if k >= n:
            return tabla[k]
    return tabla[keys[-1]]


def _build_general(data):
    suministro = data.get("suministro") or "monofasica"
    V = TENSION.get(suministro, 230)
    material = data.get("material") or "Cu"
    aislamiento = (data.get("aislamiento") or "PVC").upper()
    curva = (data.get("curva") or "C").upper()
    icc_origen = reng._num(data.get("icc_origen_a"), 6000)
    return {
        "suministro": suministro, "V": V, "material": material,
        "gamma": CONDUCTIVIDAD.get(material, 56.0),
        "m": reng.SQRT3 if suministro == "trifasica" else 2.0, "U_icc": V,
        "icc_origen": icc_origen, "aislamiento": aislamiento,
        "k_term": reng._K_TERMICO.get((material, aislamiento), 115),
        "curva": curva, "im_factor": reng._IM_CURVA.get(curva, 10),
        "t_disparo": reng._num(data.get("t_disparo_s"), 0.01) or 0.01,
        "poder_corte_ka": int(reng._num(data.get("poder_corte_ka"), 6)),
        "auto_cumplimiento": False,
    }


def _sec_txt(n, s):
    return (f"{n}×" if n > 1 else "") + reng._fmt_s(s)


def compute(data: dict) -> dict:
    g = _build_general(data)
    sum_, V, material, gamma = g["suministro"], g["V"], g["material"], g["gamma"]
    P = reng._num(data.get("potencia"))
    L = reng._num(data.get("longitud"))
    cosphi = reng._num(data.get("cosphi"), 0.9) or 0.9
    metodo = data.get("metodo_instalacion") or "b1"
    disp = data.get("disposicion") or "haz"
    n_circ = int(reng._num(data.get("n_circuitos"), 1) or 1)
    uso = data.get("tipo_uso") or "otros"
    cmax = reng._num(data.get("caida_max"), 3 if uso == "alumbrado" else 5) or (3 if uso == "alumbrado" else 5)
    s_min = 1.5 if uso == "alumbrado" else 2.5
    sec_manual = reng._num(data.get("seccion_manual")) or None
    n_forzado = int(reng._num(data.get("n_conductores"), 1) or 1)
    n_forzado = max(1, n_forzado)

    f = _factor_agrupamiento(disp, n_circ)
    Ib = reng._ib(sum_, P, V, cosphi)

    def _iz(s, n):
        # Iz de n conductores en paralelo por fase, corregida por agrupamiento de circuitos.
        return round(ampacidad(s, material, metodo) * f * n, 1)

    manual = bool(sec_manual and sec_manual in SECCIONES)
    if manual:
        n = n_forzado
        s = sec_manual
        iz = _iz(s, n)
        In = reng._breaker_fit(Ib, iz) or reng._breaker(Ib, iz)[0]
        caida = reng._caida_real(sum_, L, P, gamma, V, s * n)
    else:
        # Dimensionado automático de la sección; si el técnico fija los conductores por fase
        # (n_conductores > 1) se respeta ese número exacto y solo se dimensiona la sección.
        # Con n_conductores = 1 (auto) se aumentan los conductores en paralelo si hace falta
        # (potencias elevadas, p. ej. 2×240).
        n_list = [n_forzado] if n_forzado > 1 else [1, 2, 3, 4]
        preferida = None   # cumple sobrecarga + caída + cortocircuito
        fallback = None    # cumple al menos sobrecarga + caída
        for nn in n_list:
            for s in [x for x in SECCIONES if x >= s_min - 1e-9]:
                iz = _iz(s, nn)
                In = reng._breaker_fit(Ib, iz)
                caida = reng._caida_real(sum_, L, P, gamma, V, s * nn)
                if In is None or caida > cmax + 1e-9:
                    continue
                if fallback is None:
                    fallback = (nn, s, iz, In, caida)
                cc_try = reng._cortocircuito(g, 0.0, L, s * nn, In)
                if cc_try["protege_cc"]:
                    preferida = (nn, s, iz, In, caida)
                    break
            if preferida:
                break
        elegida = preferida or fallback
        if elegida is None:
            nn = n_list[-1]
            s = SECCIONES[-1]
            iz = _iz(s, nn)
            In = reng._breaker_fit(Ib, iz) or reng._breaker(Ib, iz)[0]
            elegida = (nn, s, iz, In, reng._caida_real(sum_, L, P, gamma, V, s * nn))
        n, s, iz, In, caida = elegida

    s_eff = s * n
    coord = reng._proteccion_dict(Ib, In, iz)
    cc = reng._cortocircuito(g, 0.0, L, s_eff, In)
    caida_ok = caida <= cmax + 1e-9
    iz_base_unit = ampacidad(s, material, metodo)

    det_calent = f"Ib = {Ib:.1f} A ≤ Iz = {iz:.1f} A "
    if n > 1:
        det_calent += f"({n}×{reng._fmt_s(s)} mm²: {iz_base_unit:.1f} A/conductor × factor agrup. {f:.2f} × {n} cond.)"
    else:
        det_calent += f"(Iz base {iz_base_unit:.1f} A × factor agrup. {f:.2f})"

    comprobaciones = [
        {"nombre": "Calentamiento (Ib ≤ Iz)", "ok": Ib <= iz + 1e-9, "detalle": det_calent},
        {"nombre": "Coordinación sobrecarga (Ib ≤ In ≤ Iz, I2 ≤ 1,45·Iz)", "ok": coord["protege"],
         "detalle": f"In = {In} A · I2 = 1,45·In = {round(1.45 * In)} A ≤ 1,45·Iz = {round(1.45 * iz)} A"},
        {"nombre": f"Caída de tensión (≤ {cmax:g} %)", "ok": caida_ok,
         "detalle": f"c.d.t. = {caida:.2f} %"},
        {"nombre": "Poder de corte ≥ Icc máx.", "ok": cc["pdc_ok"],
         "detalle": f"Icc máx = {cc['icc_max_a']:.0f} A · pdc = {g['poder_corte_ka']} kA"},
        {"nombre": "Solicitación térmica cortocircuito (k²·S² ≥ I²·t)", "ok": cc["termico_ok"],
         "detalle": f"k²·S² = {cc['i2t_cable']:.0f} ≥ I²·t = {cc['i2t_paso']:.0f}" + (f" (S efectiva {n}×{reng._fmt_s(s)} = {reng._fmt_s(s_eff)} mm²)" if n > 1 else "")},
        {"nombre": "Disparo magnético (Icc mín ≥ Im)", "ok": cc["magnetico_ok"],
         "detalle": f"Icc mín = {cc['icc_min_a']:.0f} A · Im = {cc['im_a']:.0f} A (curva {cc['curva']})"},
    ]
    cumple = all(c["ok"] for c in comprobaciones)

    sec_txt = _sec_txt(n, s)
    tierra_s = seccion_tierra(s)
    tierra_txt = _sec_txt(n, tierra_s)

    observaciones = ([{"tipo": "warning", "texto": cc["recomendacion"]}] if cc.get("recomendacion") else []) + \
        ([] if caida_ok else [{"tipo": "warning", "texto":
            f"La caída de tensión ({caida:.2f} %) supera el máximo ({cmax:g} %): aumente la sección o reduzca la longitud."}])
    if n > 1:
        observaciones.insert(0, {"tipo": "info", "texto":
            f"Se resuelve con {n} conductores en paralelo por fase de {reng._fmt_s(s)} mm² "
            f"(sección total {reng._fmt_s(s_eff)} mm²/fase). Verifique el reparto equilibrado de corriente "
            f"y la longitud igual de los conductores en paralelo (ITC-BT-19)."})

    return {
        "linea_unica": True,
        "estado_global": "cumple" if cumple else "no_cumple",
        "entradas": {
            "potencia": P, "longitud": L, "suministro": sum_, "tension": V, "cosphi": cosphi,
            "material": material, "aislamiento": g["aislamiento"], "uso": uso,
            "metodo_label": _METODO_LABEL.get(metodo, metodo),
            "disposicion_label": _AGRUP_LABEL.get(disp, disp), "n_circuitos": n_circ,
            "conductores_por_fase": n,
        },
        "agrupamiento": {"factor": f, "n_circuitos": n_circ, "disposicion_label": _AGRUP_LABEL.get(disp, disp),
                         "iz_base": round(iz_base_unit, 1), "iz_corregida": iz},
        "paralelo": {"n": n, "seccion_por_conductor_txt": reng._fmt_s(s), "seccion_efectiva_txt": reng._fmt_s(s_eff)},
        "resumen": [
            {"label": "Ib (diseño)", "valor": f"{Ib:.1f}", "unidad": "A"},
            {"label": "Sección/fase", "valor": sec_txt, "unidad": "mm²"},
            {"label": "Iz corregida", "valor": f"{iz:.0f}", "unidad": "A"},
            {"label": "Caída acum.", "valor": f"{caida:.2f}", "unidad": "%"},
            {"label": "Protección", "valor": f"{In}", "unidad": "A"},
            {"label": "Tierra", "valor": tierra_txt, "unidad": "mm²"},
        ],
        "linea": {
            "seccion_txt": sec_txt, "iz": iz, "Ib": round(Ib, 2),
            "caida_pct": round(caida, 2), "magneto": In, "curva": cc["curva"],
            "conductores_por_fase": n, "seccion_efectiva_txt": reng._fmt_s(s_eff),
            "tierra": tierra_txt, "coordinacion": coord, "cortocircuito": cc,
        },
        "comprobaciones": comprobaciones,
        "observaciones": observaciones,
    }
