"""Genera las tablas de referencia de la Guía RSCIEI 2025 para el informe,
resaltando la opción/valor aplicable al estudio. Cada tabla incluye su
referencia normativa."""

from normative_modules.rsciei.catalog import CI_TABLE
from normative_modules.rsciei.engine import MAX_SURFACE, NRI_TABLE
from normative_modules.rsciei.requirements import (
    BIE, DETECCION, ESTABILIDAD, HIDRANTES, ROCIADORES,
)

GUIA = "Guía de aplicación del RSCIEI 2025 · RD 2267/2004"


def _fmt(v):
    if v is None:
        return "NO ADMITIDO"
    if v == "SIN_LIMITE":
        return "SIN LÍMITE"
    return f"{int(v):,}".replace(",", ".")


def _cat_row(categoria):
    return {"BAJO": 0, "MEDIO": 1, "ALTO": 2}[categoria]


def _t_nri(nivel):
    rows = []
    for n, low, high, cat in NRI_TABLE:
        if n == 1:
            q = "Qs ≤ 425"
        elif high == float("inf"):
            q = "Qs > 13.600"
        else:
            q = f"{_fmt(low)} < Qs ≤ {_fmt(high)}"
        rows.append([str(n), cat.capitalize(), q])
    return {
        "id": "nri", "titulo": "Tabla 1.3.1 · Nivel de riesgo intrínseco (NRI)",
        "referencia": f"{GUIA}, Anexo I, Tabla 1.3.1",
        "headers": ["Nivel", "Categoría", "Qs (MJ/m²)"],
        "rows": rows, "highlight_rows": [nivel - 1], "highlight_cells": [],
    }


def _t_ci(used):
    rows, hl = [], []
    for i, r in enumerate(CI_TABLE):
        rows.append([r["grado"], f"{r['ci']:.2f}".replace(".", ","), r["descripcion"]])
        if any(abs(float(u) - r["ci"]) < 1e-6 for u in used):
            hl.append(i)
    return {
        "id": "ci", "titulo": "Coeficiente de peligrosidad por combustibilidad (Ci)",
        "referencia": f"{GUIA}, Anexo I (grado de combustibilidad)",
        "headers": ["Grado", "Ci", "Descripción"],
        "rows": rows, "highlight_rows": hl, "highlight_cells": [],
    }


def _t_ra(ra):
    tabla = [("Baja", "1,0", 1.0), ("Media", "1,5", 1.5), ("Alta", "2,0", 2.0)]
    rows, hl = [], []
    for i, (lab, val, num) in enumerate(tabla):
        rows.append([f"Activación {lab.lower()}", val])
        if abs(float(ra) - num) < 1e-6:
            hl.append(i)
    return {
        "id": "ra", "titulo": "Coeficiente de peligrosidad por activación (Ra)",
        "referencia": f"{GUIA}, Anexo I (grado de activación de la actividad)",
        "headers": ["Grado de activación", "Ra"],
        "rows": rows, "highlight_rows": hl, "highlight_cells": [],
    }


CONFIG_COL = {"AV": 1, "AH": 2, "B": 3, "C": 4}


def _t_superficie(config, nivel):
    rows = []
    for n in range(1, 9):
        rows.append([str(n), _fmt(MAX_SURFACE["AV"][n]), _fmt(MAX_SURFACE["AH"][n]),
                     _fmt(MAX_SURFACE["B"][n]), _fmt(MAX_SURFACE["C"][n])])
    hl = []
    col = CONFIG_COL.get(config)
    if col:
        hl = [[nivel - 1, 0], [nivel - 1, col]]
    return {
        "id": "superficie", "titulo": "Tabla 2.1.1 · Máxima superficie construida admisible por sector (m²)",
        "referencia": f"{GUIA}, Anexo II, Tabla 2.1.1",
        "headers": ["Nivel", "Tipo AV", "Tipo AH", "Tipo B", "Tipo C"],
        "rows": rows, "highlight_rows": [], "highlight_cells": hl,
        "nota": ("Nota 1: planta bajo rasante → superficie ÷ 2. Nota 2: fachada accesible ≥ 50% "
                 "del perímetro → ×1,25. Nota 3: rociadores automáticos en todo el sector → ×2 "
                 "(ambas → ×2,5). Nota 4: tipo C sin límite con extinción automática y separación > 10 m."),
    }


EST_COL = {("AV", "bajo"): 1, ("AV", "sobre"): 2, ("AH", "bajo"): 3, ("AH", "sobre"): 4,
           ("B", "bajo"): 5, ("B", "sobre"): 6, ("C", "bajo"): 7, ("C", "sobre"): 8}


def _t_estabilidad(config, categoria, sit_key):
    rows = []
    for cat in ("BAJO", "MEDIO", "ALTO"):
        row = [f"Riesgo {cat.lower()}"]
        for cfg in ("AV", "AH", "B", "C"):
            row.append(ESTABILIDAD[cfg]["bajo"][cat])
            row.append(ESTABILIDAD[cfg]["sobre"][cat])
        rows.append(row)
    hl = []
    col = EST_COL.get((config, sit_key))
    if col:
        r = _cat_row(categoria)
        hl = [[r, 0], [r, col]]
    return {
        "id": "estabilidad", "titulo": "Tabla 2.5.1 · Estabilidad al fuego (R) de la estructura portante",
        "referencia": f"{GUIA}, Anexo II, Tabla 2.5.1",
        "headers": ["Riesgo", "AV sótano", "AV s/rasante", "AH sótano", "AH s/rasante",
                    "B sótano", "B s/rasante", "C sótano", "C s/rasante"],
        "rows": rows, "highlight_rows": [], "highlight_cells": hl,
    }


RISK_COL = {"BAJO": 1, "MEDIO": 2, "ALTO": 3}


def _anexo3_table(tid, titulo, ref, table, config, categoria, modo_note=""):
    """Construye tabla config × riesgo a partir de un dict de umbrales."""
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
    if config in row_index:
        r = row_index[config]
        hl = [[r, 0], [r, RISK_COL[categoria]]]
    return {
        "id": tid, "titulo": titulo, "referencia": ref,
        "headers": ["Configuración", "Riesgo bajo", "Riesgo medio", "Riesgo alto"],
        "rows": rows, "highlight_rows": [], "highlight_cells": hl,
        "nota": modo_note,
    }


def build_tablas(data, nivel, categoria, modo_pred, used_ci):
    config = data.get("tipo_configuracion", "B")
    sit_key = "bajo" if data.get("situacion") == "bajo_rasante" else "sobre"
    ra = data.get("ra", 1.0)
    modo_label = "almacenamiento" if modo_pred == "almacenamiento" else "producción/fabricación"
    modo_note = f"Umbrales para actividad de {modo_label} (modo predominante del sector)."

    tablas = [
        _t_nri(nivel),
        _t_ci(used_ci),
        _t_ra(ra),
        _t_superficie(config, nivel),
        _t_estabilidad(config, categoria, sit_key),
        _anexo3_table("deteccion", "Anexo III · Detección automática de incendio",
                      f"{GUIA}, Anexo III", DETECCION[modo_pred], config, categoria, modo_note),
        _anexo3_table("rociadores", "Anexo III · Rociadores automáticos de agua",
                      f"{GUIA}, Anexo III", ROCIADORES[modo_pred], config, categoria, modo_note),
        _anexo3_table("bie", "Anexo III · Bocas de incendio equipadas (BIE)",
                      f"{GUIA}, Anexo III", BIE, config, categoria),
        _anexo3_table("hidrantes", "Anexo III · Hidrantes de impulsión directa",
                      f"{GUIA}, Anexo III", HIDRANTES, config, categoria),
    ]
    return tablas
