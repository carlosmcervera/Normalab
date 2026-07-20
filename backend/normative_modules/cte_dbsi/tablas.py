"""Tablas de referencia del módulo CTE DB-SI para el informe, con resaltado."""
from normative_modules.cte_dbsi.catalog import (
    SI1_MAX_SECTOR, SI3_RECORRIDO, SI3_RECORRIDO_ESPECIAL, SI6_GRUPO2, USOS,
)

REF = "CTE · Documento Básico DB-SI (RD 314/2006)"


def _fmt(v):
    return "Sin límite" if v is None else f"{int(v):,}".replace(",", ".")


def _t_si1(uso):
    rows, hl = [], []
    for i, u in enumerate(USOS):
        rows.append([u, _fmt(SI1_MAX_SECTOR.get(u, 2500))])
        if u == uso:
            hl.append(i)
    return {"id": "si1", "titulo": "SI 1 · Superficie máxima construida por sector de incendio",
            "referencia": f"{REF}, SI 1, Tabla 1.1", "headers": ["Uso previsto", "Sup. máx. sector (m²)"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": []}


def _t_si3(uso):
    rows, hl = [], []
    for i, u in enumerate(USOS):
        t = SI3_RECORRIDO_ESPECIAL.get(u, SI3_RECORRIDO)
        rows.append([u, f"{t['una']} m", f"{t['varias']} m"])
        if u == uso:
            hl.append(i)
    return {"id": "si3", "titulo": "SI 3 · Longitud máxima del recorrido de evacuación",
            "referencia": f"{REF}, SI 3, Tabla 3.1", "headers": ["Uso previsto", "Una salida", "Dos o más salidas"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": [],
            "nota": "Origen de evacuación hasta la salida de planta o de edificio. Valores orientativos del DB-SI."}


def _t_si6(uso, altura, bajo_rasante):
    grupo2 = uso in SI6_GRUPO2
    headers = ["Situación / altura de evacuación", "Grupo 1 (resid./admin./docente)", "Grupo 2 (comercial/púb.conc./hosp.)"]
    rows = [
        ["Bajo rasante (sótano)", "R 120", "R 180"],
        ["Sobre rasante · h ≤ 15 m", "R 60", "R 90"],
        ["Sobre rasante · 15 < h ≤ 28 m", "R 90", "R 120"],
        ["Sobre rasante · h > 28 m", "R 120", "R 180"],
    ]
    if bajo_rasante:
        r = 0
    elif altura <= 15:
        r = 1
    elif altura <= 28:
        r = 2
    else:
        r = 3
    col = 2 if grupo2 else 1
    return {"id": "si6", "titulo": "SI 6 · Resistencia al fuego de la estructura",
            "referencia": f"{REF}, SI 6, Tabla 3.1", "headers": headers, "rows": rows,
            "highlight_rows": [], "highlight_cells": [[r, 0], [r, col]]}


def build_tablas(uso, altura, bajo_rasante, si3):
    return [_t_si1(uso), _t_si3(uso), _t_si6(uso, altura, bajo_rasante)]
