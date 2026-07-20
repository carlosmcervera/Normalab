"""Tablas de referencia del CTE DB-SI para el informe (a partir de la tabla maestra)."""
from normative_modules.cte_dbsi import tablas_oficiales as T
from normative_modules.cte_dbsi.catalog import USOS

REF = "CTE · Documento Básico DB-SI"


def _fmt(v):
    return "Un sector/planta" if v is None else f"{int(v):,}".replace(",", ".")


def _t_si1(uso):
    rows, hl = [], []
    for i, u in enumerate(USOS):
        rows.append([u, _fmt(T.SI1_SECTOR_MAX.get(u, 2500))])
        if u == uso:
            hl.append(i)
    return {"id": "si1", "titulo": "SI 1 · Superficie máxima construida por sector",
            "referencia": f"{REF}, SI 1, Tabla 1.1", "headers": ["Uso previsto", "Sup. máx. sector (m²)"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": []}


def _t_si3(uso):
    rows, hl = [], []
    for i, u in enumerate(USOS):
        t = T.SI3_RECORRIDO_ESPECIAL.get(u, T.SI3_RECORRIDO)
        rows.append([u, f"{t['una']} m", f"{t['varias']} m"])
        if u == uso:
            hl.append(i)
    return {"id": "si3", "titulo": "SI 3 · Longitud máxima del recorrido de evacuación",
            "referencia": f"{REF}, SI 3, Tabla 3.1", "headers": ["Uso previsto", "Una salida", "Dos o más salidas"],
            "rows": rows, "highlight_rows": hl, "highlight_cells": []}


def _t_si6(uso, altura, bajo_rasante):
    g2 = uso in T.SI6_GRUPO2
    rows = [
        ["Bajo rasante (sótano)", "R 120", "R 180"],
        ["Sobre rasante · h ≤ 15 m", "R 60", "R 90"],
        ["Sobre rasante · 15 < h ≤ 28 m", "R 90", "R 120"],
        ["Sobre rasante · h > 28 m", "R 120", "R 180"],
    ]
    r = 0 if bajo_rasante else (1 if altura <= 15 else 2 if altura <= 28 else 3)
    col = 2 if g2 else 1
    return {"id": "si6", "titulo": "SI 6 · Resistencia al fuego de la estructura",
            "referencia": f"{REF}, SI 6, Tabla 3.1",
            "headers": ["Situación / altura de evacuación", "Grupo 1 (resid./admin./docente)", "Grupo 2 (comercial/púb.conc./hosp.)"],
            "rows": rows, "highlight_rows": [], "highlight_cells": [[r, 0], [r, col]]}


def build_tablas(uso, altura, bajo_rasante):
    return [_t_si1(uso), _t_si3(uso), _t_si6(uso, altura, bajo_rasante)]
