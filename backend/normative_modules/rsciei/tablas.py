"""Genera las tablas de referencia de la Guía RSCIEI 2025 (RD 164/2025) para el
informe, resaltando las opciones/valores aplicables a CADA sector con un color
propio (multi-sector). Cada tabla incluye su referencia normativa y una leyenda
que asocia color ↔ sector.
"""

from normative_modules.rsciei.catalog import CI_TABLE, RA_TABLE
from normative_modules.rsciei.engine import MAX_SURFACE, NRI_TABLE
from normative_modules.rsciei.requirements import (
    BIE, DETECCION, ESTABILIDAD, HIDRANTES, ROCIADORES,
)

GUIA = "Guía de aplicación del RSCIEI 2025 · RD 164/2025"
CONFIG_COL = {"AV": 1, "AH": 2, "B": 3, "C": 4}
RISK_COL = {"BAJO": 1, "MEDIO": 2, "ALTO": 3}

# Paleta de colores por sector (texto blanco encima).
SECTOR_COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed",
                 "#0891b2", "#db2777", "#65a30d", "#4f46e5", "#ea580c"]


def _fmt(v):
    if v is None:
        return "NO ADMITIDO"
    if v == "SIN_LIMITE":
        return "SIN LÍMITE"
    return f"{int(v):,}".replace(",", ".")


def _cat_row(categoria):
    return {"BAJO": 0, "MEDIO": 1, "ALTO": 2}[categoria]


def _add(store, key, idx):
    store.setdefault(key, [])
    if idx not in store[key]:
        store[key].append(idx)


def _t_nri(sects):
    rows = []
    for n, low, high, cat in NRI_TABLE:
        if n == 1:
            q = "Qs ≤ 425"
        elif high == float("inf"):
            q = "Qs > 13.600"
        else:
            q = f"{_fmt(low)} < Qs ≤ {_fmt(high)}"
        rows.append([str(n), cat.capitalize(), q])
    row_sectors = {}
    for s in sects:
        _add(row_sectors, str(s["nivel_riesgo"]["nivel"] - 1), s["_idx"])
    return {"id": "nri", "titulo": "Tabla 1.3.1 · Nivel de riesgo intrínseco (NRI)",
            "referencia": f"{GUIA}, Anexo I, Tabla 1.3.1",
            "headers": ["Nivel", "Categoría", "Qs (MJ/m²)"],
            "rows": rows, "row_sectors": row_sectors, "cell_sectors": {}}


def _t_ci(sects):
    rows = []
    for r in CI_TABLE:
        rows.append([r["grado"], f"{r['ci']:.2f}".replace(".", ","), r["descripcion"]])
    row_sectors = {}
    for s in sects:
        for z in s["calculo"]["zonas"]:
            ci = z.get("ci")
            if not ci:
                continue
            for i, r in enumerate(CI_TABLE):
                if abs(float(ci) - r["ci"]) < 1e-6:
                    _add(row_sectors, str(i), s["_idx"])
    return {"id": "ci", "titulo": "Tabla 1.3.2 · Coeficiente de peligrosidad por combustibilidad (Ci)",
            "referencia": f"{GUIA}, Anexo I, Tabla 1.3.2",
            "headers": ["Grado", "Ci", "Descripción"],
            "rows": rows, "row_sectors": row_sectors, "cell_sectors": {}}


def _t_ra(sects):
    rows = []
    for r in RA_TABLE:
        rows.append([f"{r['ra']:.1f}".replace(".", ","), r["grado"], r["criterio"]])
    row_sectors = {}
    for s in sects:
        ra = s["calculo"]["ra"]
        for i, r in enumerate(RA_TABLE):
            if abs(float(ra) - r["ra"]) < 1e-6:
                _add(row_sectors, str(i), s["_idx"])
    return {"id": "ra", "titulo": "Tabla 1.3.4 · Coeficiente de peligrosidad por activación (Ra)",
            "referencia": f"{GUIA}, Anexo I, Tabla 1.3.4",
            "headers": ["Ra", "Grado", "Criterio"],
            "rows": rows, "row_sectors": row_sectors, "cell_sectors": {}}


def _t_superficie(sects):
    rows = []
    for n in range(1, 9):
        rows.append([str(n), _fmt(MAX_SURFACE["AV"][n]), _fmt(MAX_SURFACE["AH"][n]),
                     _fmt(MAX_SURFACE["B"][n]), _fmt(MAX_SURFACE["C"][n])])
    cell_sectors = {}
    for s in sects:
        col = CONFIG_COL.get(s["config"])
        nivel = s["nivel_riesgo"]["nivel"]
        if col:
            _add(cell_sectors, f"{nivel - 1}-0", s["_idx"])
            _add(cell_sectors, f"{nivel - 1}-{col}", s["_idx"])
    return {"id": "superficie", "titulo": "Tabla 2.1.1 · Máxima superficie construida admisible por sector (m²)",
            "referencia": f"{GUIA}, Anexo II, Tabla 2.1.1",
            "headers": ["Nivel", "Tipo AV", "Tipo AH", "Tipo B", "Tipo C"],
            "rows": rows, "row_sectors": {}, "cell_sectors": cell_sectors,
            "nota": ("Nota 1: planta bajo rasante → superficie ÷ 2. Nota 2: fachada accesible ≥ 50% "
                     "del perímetro → ×1,25. Nota 3: rociadores automáticos en todo el sector → ×2. "
                     "Nota 4: tipo C sin límite con extinción automática y separación > 10 m.")}


EST_COL = {("AV", "bajo"): 1, ("AV", "sobre"): 2, ("AH", "bajo"): 3, ("AH", "sobre"): 4,
           ("B", "bajo"): 5, ("B", "sobre"): 6, ("C", "bajo"): 7, ("C", "sobre"): 8}


def _t_estabilidad(sects):
    rows = []
    for cat in ("BAJO", "MEDIO", "ALTO"):
        row = [f"Riesgo {cat.lower()}"]
        for cfg in ("AV", "AH", "B", "C"):
            row.append(ESTABILIDAD[cfg]["bajo"][cat])
            row.append(ESTABILIDAD[cfg]["sobre"][cat])
        rows.append(row)
    cell_sectors = {}
    for s in sects:
        sitk = "bajo" if s.get("situacion") == "bajo_rasante" else "sobre"
        cat = s["nivel_riesgo"]["categoria"]
        col = EST_COL.get((s["config"], sitk))
        if col:
            r = _cat_row(cat)
            _add(cell_sectors, f"{r}-0", s["_idx"])
            _add(cell_sectors, f"{r}-{col}", s["_idx"])
    return {"id": "estabilidad", "titulo": "Tabla 2.5.1 · Estabilidad al fuego (R) de la estructura portante",
            "referencia": f"{GUIA}, Anexo II, Tabla 2.5.1",
            "headers": ["Riesgo", "AV sótano", "AV s/rasante", "AH sótano", "AH s/rasante",
                        "B sótano", "B s/rasante", "C sótano", "C s/rasante"],
            "rows": rows, "row_sectors": {}, "cell_sectors": cell_sectors}


def _t_evacuacion(sects):
    data = {"BAJO": ["50 m", "50 m", "50 m"], "MEDIO": ["35 m", "50 m", "35 m"],
            "ALTO": ["20 m", "35 m", "20 m"]}
    rows = []
    for cat in ("BAJO", "MEDIO", "ALTO"):
        rows.append([f"Riesgo {cat.lower()}", *data[cat]])
    row_sectors = {}
    for s in sects:
        r = _cat_row(s["nivel_riesgo"]["categoria"])
        _add(row_sectors, str(r), s["_idx"])
    return {"id": "evacuacion", "titulo": "Tabla 2.3.1 · Longitud máxima del recorrido de evacuación",
            "referencia": f"{GUIA}, Anexo II, Tabla 2.3.1",
            "headers": ["Nivel de riesgo", "Una salida", "Dos o más salidas", "Recorrido sin alternativa"],
            "rows": rows, "row_sectors": row_sectors, "cell_sectors": {},
            "nota": "Los recorridos pueden incrementarse un 25%-100% según notas 4 y 5 de la tabla (extinción/control de humos)."}


def _anexo3_table(tid, titulo, ref, table, sects, modo_note="", modo_filter=None):
    order = ["AV", "AH", "B", "C", "D"]
    present = [c for c in order if c in table]
    rows, row_index = [], {}
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
    cell_sectors = {}
    for s in sects:
        if modo_filter and s.get("modo_predominante", "produccion") != modo_filter:
            continue
        cfg = s["config"]
        cat = s["nivel_riesgo"]["categoria"]
        if cfg in row_index:
            r = row_index[cfg]
            _add(cell_sectors, f"{r}-0", s["_idx"])
            _add(cell_sectors, f"{r}-{RISK_COL[cat]}", s["_idx"])
    return {"id": tid, "titulo": titulo, "referencia": ref,
            "headers": ["Configuración", "Riesgo bajo", "Riesgo medio", "Riesgo alto"],
            "rows": rows, "row_sectors": {}, "cell_sectors": cell_sectors, "nota": modo_note}


def build_tablas(data, sectores):
    # Solo sectores RSCIEI (industriales): los sectores CTE se evalúan por el DB-SI.
    real = [s for s in sectores if s.get("tipo") != "area_exterior" and s.get("ambito") != "cte"]
    if not real:
        return []
    sects = []
    for i, s in enumerate(real):
        sects.append({**s, "_idx": i})
    legend = [{"idx": i, "nombre": s.get("nombre", f"Sector {i + 1}"),
               "color": SECTOR_COLORS[i % len(SECTOR_COLORS)]}
              for i, s in enumerate(sects)]

    gov = max(sects, key=lambda s: s["nivel_riesgo"]["nivel"])
    modo_pred = gov.get("modo_predominante", "produccion")
    modo_label = "almacenamiento" if modo_pred == "almacenamiento" else "producción/fabricación"
    modo_note = (f"Umbrales para actividad de {modo_label} (modo predominante del sector gobernante). "
                 "Solo se colorean los sectores de ese mismo modo.")

    tables = [
        _t_nri(sects),
        _t_ci(sects),
        _t_ra(sects),
        _t_superficie(sects),
        _t_estabilidad(sects),
        _t_evacuacion(sects),
        _anexo3_table("deteccion", "Anexo III · Detección automática de incendio",
                      f"{GUIA}, Anexo III", DETECCION[modo_pred], sects, modo_note, modo_filter=modo_pred),
        _anexo3_table("rociadores", "Anexo III · Rociadores automáticos de agua",
                      f"{GUIA}, Anexo III", ROCIADORES[modo_pred], sects, modo_note, modo_filter=modo_pred),
        _anexo3_table("bie", "Anexo III · Bocas de incendio equipadas (BIE)",
                      f"{GUIA}, Anexo III", BIE, sects),
        _anexo3_table("hidrantes", "Anexo III · Hidrantes exteriores (Tabla 3.3.1)",
                      f"{GUIA}, Anexo III", HIDRANTES, sects),
    ]
    for t in tables:
        t["legend"] = legend
    return tables
