"""Genera las tablas de referencia de la Guía RSCIEI 2025 (RD 164/2025) para el
informe, resaltando las opciones/valores aplicables al estudio multi-sector.
Cada tabla incluye su referencia normativa."""

from normative_modules.rsciei.catalog import CI_TABLE, RA_TABLE
from normative_modules.rsciei.engine import MAX_SURFACE, NRI_TABLE
from normative_modules.rsciei.requirements import (
    BIE, DETECCION, ESTABILIDAD, HIDRANTES, ROCIADORES,
)

GUIA = "Guía de aplicación del RSCIEI 2025 · RD 164/2025"
CONFIG_COL = {"AV": 1, "AH": 2, "B": 3, "C": 4}
RISK_COL = {"BAJO": 1, "MEDIO": 2, "ALTO": 3}


def _fmt(v):
    if v is None:
        return "NO ADMITIDO"
    if v == "SIN_LIMITE":
        return "SIN LÍMITE"
    return f"{int(v):,}".replace(",", ".")


def _cat_row(categoria):
    return {"BAJO": 0, "MEDIO": 1, "ALTO": 2}[categoria]


def _t_nri(niveles):
    rows = []
    for n, low, high, cat in NRI_TABLE:
        if n == 1:
            q = "Qs ≤ 425"
        elif high == float("inf"):
            q = "Qs > 13.600"
        else:
            q = f"{_fmt(low)} < Qs ≤ {_fmt(high)}"
        rows.append([str(n), cat.capitalize(), q])
    return {"id": "nri", "titulo": "Tabla 1.3.1 · Nivel de riesgo intrínseco (NRI)",
            "referencia": f"{GUIA}, Anexo I, Tabla 1.3.1",
            "headers": ["Nivel", "Categoría", "Qs (MJ/m²)"],
            "rows": rows, "highlight_rows": [n - 1 for n in niveles], "highlight_cells": []}


def _t_ci(used):
    rows, hl = [], []
    for i, r in enumerate(CI_TABLE):
        rows.append([r["grado"], f"{r['ci']:.2f}".replace(".", ","), r["descripcion"]])
        if any(abs(float(u) - r["ci"]) < 1e-6 for u in used):
            hl.append(i)
    return {"id": "ci", "titulo": "Tabla 1.3.2 · Coeficiente de peligrosidad por combustibilidad (Ci)",
            "referencia": f"{GUIA}, Anexo I, Tabla 1.3.2",
            "headers": ["Grado", "Ci", "Descripción"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": []}


def _t_ra(ras):
    rows, hl = [], []
    for i, r in enumerate(RA_TABLE):
        rows.append([f"{r['ra']:.1f}".replace(".", ","), r["grado"], r["criterio"]])
        if any(abs(float(ra) - r["ra"]) < 1e-6 for ra in ras):
            hl.append(i)
    return {"id": "ra", "titulo": "Tabla 1.3.4 · Coeficiente de peligrosidad por activación (Ra)",
            "referencia": f"{GUIA}, Anexo I, Tabla 1.3.4",
            "headers": ["Ra", "Grado", "Criterio"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": []}


def _t_superficie(config_nivel):
    rows = []
    for n in range(1, 9):
        rows.append([str(n), _fmt(MAX_SURFACE["AV"][n]), _fmt(MAX_SURFACE["AH"][n]),
                     _fmt(MAX_SURFACE["B"][n]), _fmt(MAX_SURFACE["C"][n])])
    hl = []
    for cfg, nivel in config_nivel:
        col = CONFIG_COL.get(cfg)
        if col:
            hl.append([nivel - 1, 0])
            hl.append([nivel - 1, col])
    return {"id": "superficie", "titulo": "Tabla 2.1.1 · Máxima superficie construida admisible por sector (m²)",
            "referencia": f"{GUIA}, Anexo II, Tabla 2.1.1",
            "headers": ["Nivel", "Tipo AV", "Tipo AH", "Tipo B", "Tipo C"],
            "rows": rows, "highlight_rows": [], "highlight_cells": hl,
            "nota": ("Nota 1: planta bajo rasante → superficie ÷ 2. Nota 2: fachada accesible ≥ 50% "
                     "del perímetro → ×1,25. Nota 3: rociadores automáticos en todo el sector → ×2. "
                     "Nota 4: tipo C sin límite con extinción automática y separación > 10 m.")}


EST_COL = {("AV", "bajo"): 1, ("AV", "sobre"): 2, ("AH", "bajo"): 3, ("AH", "sobre"): 4,
           ("B", "bajo"): 5, ("B", "sobre"): 6, ("C", "bajo"): 7, ("C", "sobre"): 8}


def _t_estabilidad(config_sit_cat):
    rows = []
    for cat in ("BAJO", "MEDIO", "ALTO"):
        row = [f"Riesgo {cat.lower()}"]
        for cfg in ("AV", "AH", "B", "C"):
            row.append(ESTABILIDAD[cfg]["bajo"][cat])
            row.append(ESTABILIDAD[cfg]["sobre"][cat])
        rows.append(row)
    hl = []
    for cfg, sitk, cat in config_sit_cat:
        col = EST_COL.get((cfg, sitk))
        if col:
            r = _cat_row(cat)
            hl.append([r, 0])
            hl.append([r, col])
    return {"id": "estabilidad", "titulo": "Tabla 2.5.1 · Estabilidad al fuego (R) de la estructura portante",
            "referencia": f"{GUIA}, Anexo II, Tabla 2.5.1",
            "headers": ["Riesgo", "AV sótano", "AV s/rasante", "AH sótano", "AH s/rasante",
                        "B sótano", "B s/rasante", "C sótano", "C s/rasante"],
            "rows": rows, "highlight_rows": [], "highlight_cells": hl}


def _t_evacuacion(cats):
    data = {"BAJO": ["50 m", "50 m", "50 m"], "MEDIO": ["35 m", "50 m", "35 m"],
            "ALTO": ["20 m", "35 m", "20 m"]}
    rows, hl = [], []
    for i, cat in enumerate(("BAJO", "MEDIO", "ALTO")):
        rows.append([f"Riesgo {cat.lower()}", *data[cat]])
        if cat in cats:
            hl.append(i)
    return {"id": "evacuacion", "titulo": "Tabla 2.3.1 · Longitud máxima del recorrido de evacuación",
            "referencia": f"{GUIA}, Anexo II, Tabla 2.3.1",
            "headers": ["Nivel de riesgo", "Una salida", "Dos o más salidas", "Recorrido sin alternativa"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": [],
            "nota": "Los recorridos pueden incrementarse un 25%-100% según notas 4 y 5 de la tabla (extinción/control de humos)."}


def _anexo3_table(tid, titulo, ref, table, config_cat, modo_note=""):
    rows = []
    order = ["AV", "AH", "B", "C", "D"]
    present = [c for c in order if c in table]
    row_index = {}
    for i, cfg in enumerate(present):
        cell = table[cfg]
        vals = []
        for risk in ("BAJO", "MEDIO", "ALTO"):
            if "any" in cell:
                vals.append(f"≥ {_fmt(cell['any'])}")
            elif risk in cell:
                vals.append(f"≥ {_fmt(cell[risk])}")
            else:
                vals.append("—")
        rows.append([f"Tipo {cfg}", *vals])
        row_index[cfg] = i
    hl = []
    for cfg, cat in config_cat:
        if cfg in row_index:
            r = row_index[cfg]
            hl.append([r, 0])
            hl.append([r, RISK_COL[cat]])
    return {"id": tid, "titulo": titulo, "referencia": ref,
            "headers": ["Configuración", "Riesgo bajo", "Riesgo medio", "Riesgo alto"],
            "rows": rows, "highlight_rows": [], "highlight_cells": hl, "nota": modo_note}


def build_tablas(data, sectores):
    real = [s for s in sectores if s.get("tipo") != "area_exterior"] or sectores
    if not real:
        return []
    niveles = sorted({s["nivel_riesgo"]["nivel"] for s in real})
    cats = {s["nivel_riesgo"]["categoria"] for s in real}
    ras = {s["calculo"]["ra"] for s in real}
    ci_used, config_nivel, config_sit_cat, config_cat = [], set(), set(), set()
    for s in real:
        cfg = s["config"]
        cat = s["nivel_riesgo"]["categoria"]
        config_nivel.add((cfg, s["nivel_riesgo"]["nivel"]))
        sitk = "bajo" if s.get("situacion") == "bajo_rasante" else "sobre"
        config_sit_cat.add((cfg, sitk, cat))
        config_cat.add((cfg, cat))
        for z in s["calculo"]["zonas"]:
            if z.get("ci"):
                ci_used.append(z["ci"])

    gov = max(real, key=lambda s: s["nivel_riesgo"]["nivel"])
    modo_pred = gov.get("modo_predominante", "produccion")
    modo_label = "almacenamiento" if modo_pred == "almacenamiento" else "producción/fabricación"
    modo_note = f"Umbrales para actividad de {modo_label} (modo predominante del sector con mayor riesgo)."

    return [
        _t_nri(niveles),
        _t_ci(ci_used),
        _t_ra(ras),
        _t_superficie(config_nivel),
        _t_estabilidad(config_sit_cat),
        _t_evacuacion(cats),
        _anexo3_table("deteccion", "Anexo III · Detección automática de incendio",
                      f"{GUIA}, Anexo III", DETECCION[modo_pred], config_cat, modo_note),
        _anexo3_table("rociadores", "Anexo III · Rociadores automáticos de agua",
                      f"{GUIA}, Anexo III", ROCIADORES[modo_pred], config_cat, modo_note),
        _anexo3_table("bie", "Anexo III · Bocas de incendio equipadas (BIE)",
                      f"{GUIA}, Anexo III", BIE, config_cat),
        _anexo3_table("hidrantes", "Anexo III · Hidrantes exteriores (Tabla 3.3.1)",
                      f"{GUIA}, Anexo III", HIDRANTES, config_cat),
    ]
