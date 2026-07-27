"""Exportadores del estudio: informe en DOCX y tablas de cálculo en XLSX.

- build_docx(report, study, project): reproduce el informe completo (mismas
  secciones que el PDF en pantalla) en un documento Word editable.
- build_xlsx(study, project): libro con hojas Superficies, Ocupación y una hoja
  por sector con la carga de fuego (Qs) escrita como FÓRMULAS vivas, de modo que
  el técnico pueda editar los datos y recalcular en Excel.
"""
from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# --------------------------------------------------------------------------- #
# Helpers de formato
# --------------------------------------------------------------------------- #
def _fmt(v, dec=0):
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        s = f"{v:,.{dec}f}"
        return s.replace(",", "§").replace(".", ",").replace("§", ".")
    return str(v)


# --------------------------------------------------------------------------- #
# DOCX
# --------------------------------------------------------------------------- #
ORANGE = RGBColor(0xEA, 0x58, 0x0C)
GREY = RGBColor(0x64, 0x74, 0x8B)

ESC_TIPO_LABEL = {
    "abierta": "abierta", "protegida": "protegida",
    "especialmente_protegida": "especialmente protegida", "compartimentada": "compartimentada",
}


def _shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def _set_cell(cell, text, bold=False, align=None, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(8.5)
    if color:
        run.font.color.rgb = color


def _ref_table(doc, t):
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run(t.get("titulo", ""))
    r.bold = True
    r.font.size = Pt(9.5)
    headers = t.get("headers", [])
    rows = t.get("rows", [])
    hl_rows = set(t.get("highlight_rows") or [])
    hl_cells = {tuple(c) for c in (t.get("highlight_cells") or [])}
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        _set_cell(table.rows[0].cells[i], h, bold=True)
        _shade(table.rows[0].cells[i], "E2E8F0")
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        for ci, val in enumerate(row):
            hl = ri in hl_rows or (ri, ci) in hl_cells
            _set_cell(cells[ci], val, bold=hl)
            if hl:
                _shade(cells[ci], "FDBA74")
    if t.get("nota"):
        n = doc.add_paragraph()
        rn = n.add_run(t["nota"])
        rn.italic = True
        rn.font.size = Pt(8)
    ref = doc.add_paragraph()
    rr = ref.add_run(f"Fuente: {t.get('referencia', '')}")
    rr.italic = True
    rr.font.size = Pt(8)
    rr.font.color.rgb = GREY


def _kv_table(doc, rows):
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    for row in rows:
        cells = table.add_row().cells
        _set_cell(cells[0], row.get("k", ""), color=GREY)
        _set_cell(cells[1], row.get("v", ""), bold=True)


def _generic_table(doc, headers, rows, shade_header=True, totals=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        _set_cell(table.rows[0].cells[i], h, bold=True)
        if shade_header:
            _shade(table.rows[0].cells[i], "E2E8F0")
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            _set_cell(cells[i], val)
    if totals:
        cells = table.add_row().cells
        for i, val in enumerate(totals):
            _set_cell(cells[i], val, bold=True)
            _shade(cells[i], "F1F5F9")


def _sector_docx(doc, s):
    nr = s.get("nivel_riesgo", {})
    h = doc.add_paragraph()
    rh = h.add_run(f"{s.get('nombre', 'Sector')}  ·  NRI {nr.get('nivel')} ({nr.get('categoria')})")
    rh.bold = True
    rh.font.size = Pt(11)
    rh.font.color.rgb = ORANGE

    calc = s.get("calculo", {})
    rows = []
    for z in calc.get("zonas", []):
        modo = {"almacenamiento": "Almac.", "deposito": "Depósito"}.get(z.get("modo"), "Prod.")
        rows.append([z.get("descripcion", ""), modo, f"Ci {_fmt(z.get('ci'), 2)}",
                     f"{_fmt(z.get('superficie'))} m²", f"{_fmt(z.get('aporte'))} MJ"])
    totals = [f"A = {_fmt(calc.get('A'))} m² (útil)  ·  Ra = {_fmt(calc.get('ra'), 1)}", "", "", "",
              f"Qs = {_fmt(calc.get('qs_mj'), 1)} MJ/m²"]
    _generic_table(doc, ["Zona", "Modo", "Ci", "Superficie", "Aporte"], rows, totals=totals)

    sec = s.get("sectorizacion", {})
    if sec.get("mensaje"):
        doc.add_paragraph(sec["mensaje"])

    req = s.get("requisitos", {})
    _kv_table(doc, [
        {"k": "Estabilidad estructura", "v": (req.get("estabilidad") or {}).get("valor", "-")},
        {"k": "Delimitadores", "v": (req.get("delimitadores") or {}).get("valor", "-")},
        {"k": "Evacuación (máx.)", "v": f"{(s.get('evacuacion') or {}).get('distancia_maxima', '-')} m · "
                                        f"{(s.get('evacuacion') or {}).get('num_salidas', '-')} salidas"},
    ])

    for it in req.get("instalaciones", []):
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(f"{it.get('nombre')} — {'Obligatorio' if it.get('obligatorio') else 'No exigible'}")
        r.font.size = Pt(9)

    for l in s.get("locales_riesgo_especial", []):
        p = doc.add_paragraph(style="List Bullet")
        magnitud = ""
        if l.get("volumen") is not None:
            magnitud = f"{_fmt(l.get('volumen'), 1)} m³ · "
        elif l.get("potencia") is not None:
            magnitud = f"{_fmt(l.get('potencia'), 1)} · "
        uso = f" · uso: {l['uso']}" if l.get("uso") else ""
        crit = f" ({l['criterio']})" if l.get("criterio") else ""
        r = p.add_run(f"LRE «{l.get('nombre')}» · riesgo {str(l.get('riesgo', '')).lower()} · "
                      f"{magnitud}{_fmt(l.get('superficie'))} m² · {l.get('resistencia')}{uso}{crit}"
                      f"{'. ' + l['justificacion'] if l.get('justificacion') else ''}")
        r.font.size = Pt(9)

    for e in s.get("escaleras_protegidas", []):
        p = doc.add_paragraph(style="List Bullet")
        tipo = ESC_TIPO_LABEL.get(e.get("tipo"), "protegida")
        sentido = f" · {e.get('sentido')}" if e.get("sentido") else ""
        r = p.add_run(f"Escalera «{e.get('nombre')}» · {tipo}{sentido} · {e.get('situacion')}"
                      f"{'. ' + e['justificacion'] if e.get('justificacion') else ''}")
        r.font.size = Pt(9)

    dbsi = s.get("dbsi")
    if dbsi:
        p = doc.add_paragraph()
        pr = p.add_run("CTE DB-SI · verificación por secciones")
        pr.bold = True
        pr.font.size = Pt(9.5)
        for sc in dbsi.get("secciones", []):
            est = sc.get("estado")
            label = "No cumple" if est == "no_cumple" else "Cumple" if est == "cumple" else "Info"
            b = doc.add_paragraph(style="List Bullet")
            rb = b.add_run(f"{sc.get('titulo', sc.get('id'))} — {label}")
            rb.font.size = Pt(9)
        for t in dbsi.get("tablas", []):
            _ref_table(doc, t)


def build_docx(report: dict, study: dict, project: dict) -> BytesIO:
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)

    title = doc.add_paragraph()
    tr = title.add_run(report.get("title", "Informe"))
    tr.bold = True
    tr.font.size = Pt(18)
    tr.font.color.rgb = ORANGE
    sub = doc.add_paragraph()
    sr = sub.add_run(f"{study.get('name', '')}  ·  {project.get('code', '')} — {project.get('name', '')}")
    sr.font.color.rgb = GREY
    doc.add_paragraph(f"Generado: {report.get('generated_at', '')[:19].replace('T', ' ')}")

    for s in report.get("sections", []):
        stype = s.get("type")
        if stype == "ambito_header":
            p = doc.add_paragraph()
            pr = p.add_run(f"{s.get('tipo', '')}")
            pr.font.size = Pt(8)
            pr.font.color.rgb = GREY
            doc.add_heading(s.get("title", ""), level=1)
            continue

        doc.add_heading(s.get("title", ""), level=2)

        if stype == "text":
            doc.add_paragraph(s.get("body", ""))
        elif stype == "keyvalue":
            _kv_table(doc, s.get("rows", []))
        elif stype == "resumen_ejecutivo":
            rows = [[f.get("nombre"), f.get("ambito"), _fmt(f.get("qs_mj"), 1),
                     f"{f.get('nivel')} · {f.get('categoria')}",
                     {"cumple": "Cumple", "no_cumple": "No cumple"}.get(f.get("estado"), "Observaciones")]
                    for f in s.get("filas", [])]
            _generic_table(doc, ["Sector", "Ámbito", "Qs", "NRI", "Estado"], rows)
            for dep in s.get("depositos", []):
                p = doc.add_paragraph(style="List Bullet")
                r = p.add_run(dep.get("justificacion", ""))
                r.font.size = Pt(9)
        elif stype == "superficies":
            d = s.get("data", {})
            rows = [[f.get("nombre"), f.get("planta"), f.get("sector"),
                     _fmt(f.get("sup_util"), 2), _fmt(f.get("sup_construida"), 2)] for f in d.get("filas", [])]
            _generic_table(doc, ["Dependencia", "Planta", "Sector", "S. útil", "S. construida"], rows,
                           totals=["Total", "", "", _fmt(d.get("total_util"), 2), _fmt(d.get("total_construida"), 2)])
            grupos = d.get("grupos") or []
            if grupos:
                gp = doc.add_paragraph()
                gpr = gp.add_run("Superficies por planta")
                gpr.bold = True
                gpr.font.size = Pt(9.5)
                grows = [[g.get("planta"), _fmt(g.get("sub_util"), 2), _fmt(g.get("sub_construida"), 2)] for g in grupos]
                _generic_table(doc, ["Planta", "S. útil", "S. construida"], grows,
                               totals=["Total", _fmt(d.get("total_util"), 2), _fmt(d.get("total_construida"), 2)])
        elif stype == "ocupacion":
            d = s.get("data", {})
            rows = [[f.get("nombre"), f.get("sector"), f.get("uso"), _fmt(f.get("superficie"), 2),
                     str(f.get("densidad")), str(f.get("ocupacion"))] for f in d.get("filas", [])]
            _generic_table(doc, ["Dependencia", "Sector", "Uso", "Sup.", "Densidad", "Ocupación"], rows,
                           totals=["Ocupación total", "", "", "", "", str(d.get("total"))])
            for f in d.get("filas", []):
                if f.get("nota"):
                    p = doc.add_paragraph(style="List Bullet")
                    pr = p.add_run(f"Ocupación personalizada · {f.get('nombre')}: {f.get('nota')}")
                    pr.italic = True
                    pr.font.size = Pt(8)
            pp = d.get("por_planta") or []
            if pp:
                op = doc.add_paragraph()
                opr = op.add_run("Ocupación por planta")
                opr.bold = True
                opr.font.size = Pt(9.5)
                _generic_table(doc, ["Planta", "Ocupación"], [[x.get("planta"), str(x.get("ocupacion"))] for x in pp])
        elif stype == "resumen":
            rows = [[f.get("nombre"), f.get("config"), _fmt(f.get("superficie")), _fmt(f.get("qs_mj"), 1),
                     f"{f.get('nivel')} · {f.get('categoria')}", f.get("estabilidad"), str(f.get("ocupacion"))]
                    for f in s.get("filas", [])]
            _generic_table(doc, ["Sector", "Config.", "Sup.", "Qs", "NRI", "Estab.", "Ocup."], rows)
        elif stype == "sectores":
            for sec in s.get("items", []):
                _sector_docx(doc, sec)
        elif stype == "tablas":
            for t in s.get("items", []):
                _ref_table(doc, t)
        elif stype == "instalaciones":
            for it in s.get("items", []):
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(f"{it.get('nombre')} — {'Obligatorio' if it.get('obligatorio') else 'No exigible'}: {it.get('detalle', '')}")
        elif stype == "observaciones":
            for o in s.get("items", []):
                doc.add_paragraph(o.get("texto", ""), style="List Bullet")

    doc.add_paragraph()
    disc = doc.add_paragraph()
    dr = disc.add_run(report.get("disclaimer", ""))
    dr.italic = True
    dr.font.size = Pt(8)
    dr.font.color.rgb = GREY

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# --------------------------------------------------------------------------- #
# XLSX (con fórmulas vivas)
# --------------------------------------------------------------------------- #
HEAD_FILL = PatternFill("solid", fgColor="1E293B")
HEAD_FONT = Font(color="FFFFFF", bold=True, size=10)
TOTAL_FILL = PatternFill("solid", fgColor="F1F5F9")
CALC_FILL = PatternFill("solid", fgColor="FEF3C7")
THIN = Side(style="thin", color="CBD5E1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _sheet_title(name):
    # Excel: máx 31 chars, sin caracteres inválidos
    for ch in "[]:*?/\\":
        name = name.replace(ch, " ")
    return name[:31]


def _header_row(ws, row, headers):
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.fill = HEAD_FILL
        c.font = HEAD_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER


def _autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def build_xlsx(study: dict, project: dict) -> BytesIO:
    results = study.get("results") or {}
    wb = Workbook()

    # --- Hoja Superficies --------------------------------------------------- #
    ws = wb.active
    ws.title = "Superficies"
    ws.cell(row=1, column=1, value=f"Cuadro de superficies · {project.get('code','')} {project.get('name','')}").font = Font(bold=True, size=12)
    _header_row(ws, 3, ["Dependencia", "Planta", "Sector", "S. útil (m²)", "S. construida (m²)"])
    sup = results.get("superficies", {})
    r = 4
    first = r
    for f in sup.get("filas", []):
        ws.cell(row=r, column=1, value=f.get("nombre"))
        ws.cell(row=r, column=2, value=f.get("planta"))
        ws.cell(row=r, column=3, value=f.get("sector"))
        ws.cell(row=r, column=4, value=f.get("sup_util"))
        ws.cell(row=r, column=5, value=f.get("sup_construida"))
        for c in range(1, 6):
            ws.cell(row=r, column=c).border = BORDER
        r += 1
    last = r - 1
    tot = ws.cell(row=r, column=1, value="TOTAL")
    tot.font = Font(bold=True)
    if last >= first:
        ws.cell(row=r, column=4, value=f"=SUM(D{first}:D{last})").font = Font(bold=True)
        ws.cell(row=r, column=5, value=f"=SUM(E{first}:E{last})").font = Font(bold=True)
    for c in range(1, 6):
        ws.cell(row=r, column=c).fill = TOTAL_FILL
        ws.cell(row=r, column=c).border = BORDER
    grupos = sup.get("grupos") or []
    if grupos:
        r += 2
        ws.cell(row=r, column=1, value="Superficies por planta").font = Font(bold=True)
        r += 1
        _header_row(ws, r, ["Planta", "", "", "S. útil (m²)", "S. construida (m²)"])
        r += 1
        for g in grupos:
            ws.cell(row=r, column=1, value=g.get("planta"))
            ws.cell(row=r, column=4, value=g.get("sub_util"))
            ws.cell(row=r, column=5, value=g.get("sub_construida"))
            for c in range(1, 6):
                ws.cell(row=r, column=c).border = BORDER
            r += 1
    _autosize(ws, [30, 14, 22, 16, 18])

    # --- Hoja Ocupación ----------------------------------------------------- #
    wo = wb.create_sheet("Ocupación")
    wo.cell(row=1, column=1, value="Cálculo de ocupación (CTE DB-SI, Tabla 2.1)").font = Font(bold=True, size=12)
    _header_row(wo, 3, ["Dependencia", "Sector", "Uso", "Superficie (m²)", "Densidad", "Ocupación", "Nota"])
    occ = results.get("ocupacion", {})
    r = 4
    for f in occ.get("filas", []):
        wo.cell(row=r, column=1, value=f.get("nombre"))
        wo.cell(row=r, column=2, value=f.get("sector"))
        wo.cell(row=r, column=3, value=f.get("uso"))
        wo.cell(row=r, column=4, value=f.get("superficie"))
        wo.cell(row=r, column=5, value=str(f.get("densidad")))
        wo.cell(row=r, column=6, value=f.get("ocupacion"))
        wo.cell(row=r, column=7, value=f.get("nota") or "")
        for c in range(1, 8):
            wo.cell(row=r, column=c).border = BORDER
        r += 1
    wo.cell(row=r, column=1, value="OCUPACIÓN TOTAL").font = Font(bold=True)
    wo.cell(row=r, column=6, value=occ.get("total")).font = Font(bold=True)
    for c in range(1, 8):
        wo.cell(row=r, column=c).fill = TOTAL_FILL
        wo.cell(row=r, column=c).border = BORDER
    porp = occ.get("por_planta") or []
    if porp:
        r += 2
        wo.cell(row=r, column=1, value="Ocupación por planta").font = Font(bold=True)
        r += 1
        for x in porp:
            wo.cell(row=r, column=1, value=x.get("planta"))
            wo.cell(row=r, column=6, value=x.get("ocupacion"))
            for c in range(1, 8):
                wo.cell(row=r, column=c).border = BORDER
            r += 1
    _autosize(wo, [30, 22, 22, 16, 16, 14, 40])

    # --- Hoja por sector: carga de fuego Qs con fórmulas -------------------- #
    for s in results.get("sectores", []):
        calc = s.get("calculo", {})
        zonas = calc.get("zonas", [])
        ws = wb.create_sheet(_sheet_title(f"Qs · {s.get('nombre', 'Sector')}"))
        nr = s.get("nivel_riesgo", {})
        ws.cell(row=1, column=1, value=f"Carga de fuego · {s.get('nombre','Sector')}").font = Font(bold=True, size=12)
        ws.cell(row=2, column=1, value="Los aportes y la Qs son fórmulas vivas: edite qsi/qvi/Ci/hi/superficie y Excel recalcula.").font = Font(italic=True, size=9, color="64748B")
        headers = ["Zona", "Modo", "qsi (MJ/m²)", "qvi (MJ/m³)", "Ci", "hi (m)", "Superficie (m²)", "Aporte (MJ)"]
        _header_row(ws, 4, headers)
        first = 5
        r = first
        for z in zonas:
            modo = z.get("modo")
            almac = modo == "almacenamiento"
            deposito = modo == "deposito"
            ws.cell(row=r, column=1, value=z.get("descripcion"))
            ws.cell(row=r, column=2, value={"almacenamiento": "Almacenamiento", "deposito": "Depósito"}.get(modo, "Producción"))
            ws.cell(row=r, column=3, value=(None if (almac or deposito) else z.get("qsi")))
            ws.cell(row=r, column=4, value=(z.get("qvi") if almac else None))
            ws.cell(row=r, column=5, value=z.get("ci"))
            ws.cell(row=r, column=6, value=(z.get("hi") if almac else None))
            ws.cell(row=r, column=7, value=z.get("superficie"))
            # Aporte: producción = qsi*Ci*S ; almacenamiento = qvi*Ci*hi*S ; depósito = PCI*densidad*volumen*Ci (valor calculado)
            if deposito:
                ws.cell(row=r, column=8, value=z.get("aporte"))
            elif almac:
                ws.cell(row=r, column=8, value=f"=D{r}*E{r}*F{r}*G{r}")
            else:
                ws.cell(row=r, column=8, value=f"=C{r}*E{r}*G{r}")
            for c in range(1, 9):
                ws.cell(row=r, column=c).border = BORDER
            r += 1
        last = r - 1
        r += 1
        a_row, ra_row, num_row, qs_row = r, r + 1, r + 2, r + 3
        ws.cell(row=a_row, column=1, value="Superficie útil del sector A (m²)").font = Font(bold=True)
        ws.cell(row=a_row, column=8, value=(f"=SUM(G{first}:G{last})" if last >= first else calc.get("A")))
        ws.cell(row=ra_row, column=1, value="Coeficiente de activación Ra").font = Font(bold=True)
        ws.cell(row=ra_row, column=8, value=calc.get("ra"))
        ws.cell(row=num_row, column=1, value="Suma de aportes (MJ)").font = Font(bold=True)
        ws.cell(row=num_row, column=8, value=(f"=SUM(H{first}:H{last})" if last >= first else calc.get("numerador")))
        ws.cell(row=qs_row, column=1, value="Qs = (Σ aportes / A) · Ra  (MJ/m²)").font = Font(bold=True, size=11)
        qs = ws.cell(row=qs_row, column=8, value=f"=IF(H{a_row}=0,0,H{num_row}/H{a_row}*H{ra_row})")
        qs.font = Font(bold=True, size=11)
        for rr in (a_row, ra_row, num_row, qs_row):
            for c in (1, 8):
                ws.cell(row=rr, column=c).fill = CALC_FILL if rr == qs_row else TOTAL_FILL
                ws.cell(row=rr, column=c).border = BORDER
        ws.cell(row=qs_row + 2, column=1,
                value=f"NRI resultante: nivel {nr.get('nivel')} ({nr.get('categoria')}). "
                      "Las escaleras están excluidas del cálculo; los locales de riesgo especial SÍ computan.").font = Font(italic=True, size=9, color="64748B")
        _autosize(ws, [28, 16, 14, 14, 10, 10, 16, 16])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
