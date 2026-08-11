"""Generador del documento tipo «Proyecto de Baja Tensión» (Word/DOCX) para el módulo REBT.

Combina campos de plantilla editables (marcados con «[COMPLETAR: …]») con las tablas y
resultados calculados por el motor. Estudio orientativo, no vinculante.
"""
from datetime import datetime
from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

PH = lambda t: f"«[COMPLETAR: {t}]»"

_LEGISLACION = [
    "Reglamento Electrotécnico para Baja Tensión (RD 842/2002) e Instrucciones Técnicas Complementarias (ITC-BT).",
    "ITC-BT-19: Instalaciones interiores o receptoras. Prescripciones generales (intensidades admisibles, caídas de tensión).",
    "ITC-BT-22: Protección contra sobreintensidades.",
    "ITC-BT-23: Protección contra sobretensiones.",
    "ITC-BT-24: Protección contra los contactos directos e indirectos.",
    "ITC-BT-18: Instalaciones de puesta a tierra.",
    "UNE-HD 60364-5-52: Selección e instalación de canalizaciones.",
    "Normas particulares de la compañía distribuidora y ordenanzas municipales aplicables.",
]


def _h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    return p


def _placeholder_par(doc, label):
    p = doc.add_paragraph()
    r = p.add_run(PH(label))
    r.italic = True
    r.font.color.rgb = RGBColor(0x99, 0x66, 0x00)
    return p


def _kv_table(doc, rows):
    tbl = doc.add_table(rows=0, cols=2)
    tbl.style = "Light List Accent 1"
    for k, v in rows:
        c = tbl.add_row().cells
        rk = c[0].paragraphs[0].add_run(k); rk.bold = True; rk.font.size = Pt(9)
        c[1].paragraphs[0].add_run(str(v)).font.size = Pt(9)
    doc.add_paragraph()


def _lineas_table(doc, lineas, cols, keys):
    tbl = doc.add_table(rows=1, cols=len(cols))
    tbl.style = "Light Grid Accent 1"
    for i, c in enumerate(cols):
        r = tbl.rows[0].cells[i].paragraphs[0].add_run(c); r.bold = True; r.font.size = Pt(7.5)
    for l in lineas:
        cells = tbl.add_row().cells
        for i, k in enumerate(keys):
            val = k(l) if callable(k) else l.get(k, "")
            rr = cells[i].paragraphs[0].add_run("" if val is None else str(val)); rr.font.size = Pt(7.5)
    doc.add_paragraph()


def build_proyecto_docx(study: dict, project: dict, results: dict) -> BytesIO:
    doc = Document()
    datos = results.get("datos", {}) or {}
    arbol = results.get("arbol", {}) or {}
    lga = arbol.get("lga")
    lineas = results.get("lineas", []) or []
    resumen = results.get("resumen", []) or []

    # ---- Portada ----
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = t.add_run("PROYECTO DE INSTALACIÓN ELÉCTRICA DE BAJA TENSIÓN")
    rt.bold = True; rt.font.size = Pt(20)
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(project.get("name", "") or PH("denominación del proyecto")).font.size = Pt(13)
    doc.add_paragraph()
    _kv_table(doc, [
        ("Expediente", project.get("code", "") or PH("código")),
        ("Emplazamiento", PH("dirección completa, población y provincia")),
        ("Titular / Promotor", PH("nombre y NIF del titular")),
        ("Técnico redactor", PH("nombre, titulación y nº de colegiado")),
        ("Fecha", datetime.now().strftime("%d/%m/%Y")),
    ])
    doc.add_paragraph("Documento orientativo, no vinculante. Los valores de cálculo deben verificarse con las "
                      "condiciones reales del punto de suministro.").italic = True
    doc.add_page_break()

    # ---- 1. Objeto ----
    _h(doc, "1. Objeto del proyecto")
    doc.add_paragraph("El presente proyecto tiene por objeto describir y justificar las características técnicas de "
                      "la instalación eléctrica de baja tensión, así como el cumplimiento del Reglamento "
                      "Electrotécnico para Baja Tensión (REBT) y sus Instrucciones Técnicas Complementarias, "
                      "para su tramitación ante los organismos competentes y su ejecución.")

    # ---- 2. Titular ----
    _h(doc, "2. Titular de la instalación")
    _placeholder_par(doc, "Datos del titular: nombre/razón social, NIF/CIF, domicilio y datos de contacto")

    # ---- 3. Emplazamiento ----
    _h(doc, "3. Emplazamiento")
    _placeholder_par(doc, "Dirección, referencia catastral, población, provincia y coordenadas")

    # ---- 4. Legislación aplicable ----
    _h(doc, "4. Legislación y normativa aplicable")
    for n in _LEGISLACION:
        doc.add_paragraph(n, style="List Bullet")

    # ---- 5. Descripción ----
    _h(doc, "5. Descripción de la instalación")
    _placeholder_par(doc, "Descripción del local/actividad, uso, superficie y distribución de estancias")
    doc.add_paragraph(f"Tipo de suministro: {datos.get('suministro', PH('mono/trifásico'))} · "
                      f"Tensión: {datos.get('tension', PH('V'))} V. "
                      f"La instalación se estructura en un cuadro general y "
                      f"{max(0, int(datos.get('num_lineas', 0)))} circuitos, según el esquema unifilar adjunto.")

    # ---- 6. Potencia prevista ----
    _h(doc, "6. Potencia total prevista")
    _kv_table(doc, [(m.get("label", ""), f"{m.get('valor', '')} {m.get('unidad', '')}") for m in resumen] or
              [("Potencia", PH("kW")), ("Intensidad de diseño (Ib)", PH("A"))])
    _placeholder_par(doc, "Potencia contratada y tarifa de acceso")

    # ---- 7. Características de la instalación ----
    _h(doc, "7. Características de la instalación")
    _h(doc, "7.1. Acometida y Caja General de Protección (CGP)", level=2)
    _placeholder_par(doc, "Tipo de acometida (aérea/subterránea), esquema CGP y calibre de fusibles gL/gG de la CGP")
    _h(doc, "7.2. Línea General de Alimentación (LGA)", level=2)
    if lga:
        _kv_table(doc, [
            ("Longitud", f"{lga.get('longitud', '')} m"),
            ("Sección", f"{lga.get('seccion_txt', '')} mm²"),
            ("Caída de tensión", f"{lga.get('caida_pct', '')} %"),
            ("Protección en cabecera", lga.get("dispositivo", PH("fusible/IGA y calibre"))),
        ])
    else:
        doc.add_paragraph("No se define LGA independiente (suministro con derivación individual directa al cuadro).")
    _h(doc, "7.3. Derivación individual y cuadro general", level=2)
    doc.add_paragraph(f"Interruptor General Automático (IGA): {datos.get('iga', PH('A'))} A. "
                      f"Poder de corte de los interruptores: {datos.get('poder_corte_ka', PH('kA'))} kA. "
                      f"Dispositivo de protección contra sobretensiones (SPD): "
                      f"{'sí' if datos.get('spd') else PH('sí/no y tipo')}.")
    _h(doc, "7.4. Instalación interior", level=2)
    doc.add_paragraph("Circuitos, secciones y protecciones según el cuadro de resultados del apartado 12. "
                      "Canalizaciones y métodos de instalación indicados por circuito (ITC-BT-19/20/21).")

    # ---- 8. Puesta a tierra ----
    _h(doc, "8. Puesta a tierra")
    doc.add_paragraph("Red de tierra según ITC-BT-18, con conductor de protección dimensionado en función de la "
                      "sección de fase (tabla 2 de la ITC-BT-19). Resistencia de tierra objetivo de forma que la "
                      "tensión de contacto no supere los valores admisibles con el diferencial instalado.")
    _placeholder_par(doc, "Descripción del electrodo (picas/anillo), resistividad del terreno y resistencia de tierra prevista")

    # ---- 9. Bases de cálculo ----
    _h(doc, "9. Bases de cálculo")
    doc.add_paragraph("Intensidad de diseño (Ib): monofásica Ib=P/(V·cosφ); trifásica Ib=P/(√3·V·cosφ).")
    doc.add_paragraph("Intensidad máxima admisible (Iz): según ITC-BT-19 (Tabla 1), en función de la sección, "
                      "el aislamiento y el método de instalación de referencia (B1/B2/C/E/F/D).")
    doc.add_paragraph("Coordinación de protecciones frente a sobrecargas (ITC-BT-22): Ib ≤ In ≤ Iz e I2 ≤ 1,45·Iz.")
    doc.add_paragraph("Caída de tensión: acumulada desde el origen, dentro de los límites reglamentarios "
                      "(≤3 % alumbrado, ≤5 % otros usos; ≤4,5 %/6,5 % en instalaciones con LGA).")
    doc.add_paragraph("Cortocircuito (ITC-BT-22, método simplificado): Icc en cada punto a partir de la Icc presunta "
                      "en origen y la impedancia de los conductores; comprobación k²·S² ≥ I²·t (solicitación térmica) "
                      "y disparo magnético Icc_mín ≥ Im.")
    doc.add_paragraph("Sobretensiones (ITC-BT-23): protección mediante SPD según el nivel de riesgo.")

    # ---- 10. Cálculos: secciones y protecciones ----
    _h(doc, "10. Cálculo de secciones y protecciones")
    _lineas_table(
        doc, lineas,
        ["Cuadro", "Circuito", "P (W)", "Ib (A)", "Sección", "Iz (A)", "Método", "Protección", "Dif.", "c.d.t. acum.", "Estado"],
        ["cuadro", "circuito", "potencia", "Ib",
         lambda l: f"{l.get('seccion_txt','')} mm²", "iz",
         lambda l: l.get("metodo_label", ""),
         lambda l: l.get("proteccion") or (f"{l.get('magneto')} A" if l.get("magneto") else ""),
         lambda l: (f"{l.get('sensibilidad')} mA" if l.get("sensibilidad") else "—"),
         lambda l: f"{l.get('caida_acum_pct','')} %",
         lambda l: {"cumple": "Cumple", "no_cumple": "No cumple"}.get(l.get("estado"), "Revisar")],
    )

    # ---- 11. Cortocircuito (resumen) ----
    _h(doc, "11. Comprobación de cortocircuito (ITC-BT-22)")
    cc_lines = [l for l in lineas if l.get("cortocircuito")]
    _lineas_table(
        doc, cc_lines,
        ["Circuito", "Icc máx (A)", "Icc mín (A)", "Poder corte", "k²S²≥I²t", "Disparo", "Protege CC"],
        [lambda l: f"{l.get('cuadro','')} · {l.get('circuito','')}",
         lambda l: l["cortocircuito"].get("icc_max_a"), lambda l: l["cortocircuito"].get("icc_min_a"),
         lambda l: "Sí" if l["cortocircuito"].get("pdc_ok") else "No",
         lambda l: "Sí" if l["cortocircuito"].get("termico_ok") else "No",
         lambda l: "Sí" if l["cortocircuito"].get("magnetico_ok") else "No",
         lambda l: "Sí" if l["cortocircuito"].get("protege_cc") else "No"],
    )

    # ---- 12. Cuadro de resultados ----
    _h(doc, "12. Cuadro de resultados")
    doc.add_paragraph(f"Estado global del cuadro: "
                      f"{ {'cumple':'CUMPLE','no_cumple':'NO CUMPLE'}.get(results.get('estado_global'),'CON OBSERVACIONES') }.")
    obs = results.get("observaciones", []) or []
    if obs:
        _h(doc, "Observaciones", level=2)
        for o in obs:
            doc.add_paragraph(f"[{o.get('tipo','info').upper()}] {o.get('texto','')}", style="List Bullet")

    # ---- 13. Pliego de condiciones ----
    _h(doc, "13. Pliego de condiciones")
    doc.add_paragraph("Los materiales serán de marca reconocida y dispondrán de marcado CE y de las certificaciones "
                      "reglamentarias. La ejecución se realizará por instalador autorizado conforme al REBT, sus ITC "
                      "y las normas particulares de la compañía distribuidora.")
    _placeholder_par(doc, "Condiciones particulares de materiales, ejecución, pruebas y mantenimiento")

    # ---- 14. Mediciones y presupuesto ----
    _h(doc, "14. Mediciones y presupuesto")
    _placeholder_par(doc, "Mediciones por partidas (cableado, protecciones, cuadros, tierra) y presupuesto")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
