"""Extractos normativos del REBT (RD 842/2002) para fundamentar el informe."""

FUNDAMENTOS = [
    {
        "tema": "Intensidad máxima admisible de los conductores",
        "cita": ("«Las intensidades máximas admisibles se regirán en su totalidad por lo indicado en "
                 "la norma UNE 20.460-5-523 y su anexo nacional. Las tablas de esta instrucción son "
                 "aplicables a los cables cuya temperatura máxima admisible en servicio permanente sea "
                 "de 70 °C (aislamiento termoplástico) o 90 °C (aislamiento termoestable).»"),
        "referencia": "REBT, ITC-BT-19, apartado 2.2.3 (Tabla 1).",
    },
    {
        "tema": "Caída de tensión máxima admisible",
        "cita": ("«La sección de los conductores a utilizar se determinará de forma que la caída de "
                 "tensión entre el origen de la instalación interior y cualquier punto de utilización "
                 "sea menor del 3 % para alumbrado y del 5 % para los demás usos. Para derivaciones "
                 "individuales, la caída de tensión máxima admisible será del 1 % (contadores "
                 "concentrados) o del 1,5 % (contador único).»"),
        "referencia": "REBT, ITC-BT-19, apartado 2.2.2.",
    },
    {
        "tema": "Conductores de protección (puesta a tierra)",
        "cita": ("«La sección de los conductores de protección será la indicada en la tabla 2, o se "
                 "obtendrá por cálculo. Para S ≤ 16 mm², Sp = S; para 16 < S ≤ 35 mm², Sp = 16 mm²; "
                 "para S > 35 mm², Sp = S/2 (siendo S la sección de los conductores de fase).»"),
        "referencia": "REBT, ITC-BT-18, apartado 3.4 (Tabla 2).",
    },
    {
        "tema": "Protección contra sobreintensidades",
        "cita": ("«Todo circuito estará protegido contra los efectos de las sobreintensidades. El "
                 "dispositivo de protección debe cumplir la condición Ib ≤ In ≤ Iz, siendo Ib la "
                 "corriente de diseño del circuito, In la corriente asignada del dispositivo de "
                 "protección e Iz la intensidad máxima admisible del conductor.»"),
        "referencia": "REBT, ITC-BT-22, apartado 1.1.",
    },
    {
        "tema": "Grado de electrificación y circuitos en viviendas",
        "cita": ("«La electrificación básica prevé una potencia mínima de 5.750 W a 230 V y un mínimo "
                 "de 5 circuitos independientes (C1 a C5). La electrificación elevada prevé una "
                 "potencia mínima de 9.200 W y circuitos adicionales para calefacción, aire "
                 "acondicionado, secadora y sistemas de automatización.»"),
        "referencia": "REBT, ITC-BT-25, apartados 3 y 4.",
    },
    {
        "tema": "Previsión de cargas y coeficiente de simultaneidad",
        "cita": ("«La previsión de cargas de la instalación se obtiene a partir de la potencia prevista "
                 "para cada circuito o receptor, aplicando los coeficientes de simultaneidad y de "
                 "utilización correspondientes. La potencia de cálculo de la línea de alimentación de "
                 "un cuadro es la resultante de aplicar dichos coeficientes al conjunto de sus cargas.»"),
        "referencia": "REBT, ITC-BT-10 (Previsión de cargas) e ITC-BT-25.",
    },
    {
        "tema": "Selectividad y coordinación de protecciones",
        "cita": ("«Los dispositivos de protección se dispondrán de forma que quede garantizada la "
                 "protección contra sobrecargas y cortocircuitos de todas las canalizaciones, "
                 "asegurando la coordinación entre la protección general de cabecera y las protecciones "
                 "de los circuitos derivados y de los subcuadros.»"),
        "referencia": "REBT, ITC-BT-22 e ITC-BT-17.",
    },
]


def build_anexo_calculo(results: dict) -> list:
    """Anexo justificativo de cálculo por circuito: fórmulas de Ib, Iz, caída de tensión,
    sobrecarga y cortocircuito con los valores del proyecto, citando la ITC-BT-22."""
    datos = results.get("datos", {}) or {}
    trifasica = datos.get("suministro") == "trifasica"
    V = datos.get("tension", 230)
    mat = datos.get("material", "Cu")
    ib_formula = (f"Ib = P / (√3 · U · cosφ), con U = {V} V (trifásica)"
                  if trifasica else f"Ib = P / (U · cosφ), con U = {V} V (monofásica)")
    e_formula = ("e = √3 · L · I · (R·cosφ + X·senφ) ≈ L·P / (γ·S·U) (trifásica)"
                 if trifasica else "e = 2 · L · P / (γ·S·U) (monofásica), con γ del " + mat)
    bloques = []
    for l in results.get("lineas", []):
        co = l.get("coordinacion") or {}
        cc = l.get("cortocircuito") or {}
        pasos = [
            {"tema": "Corriente de proyecto o de diseño (Ib)",
             "formula": ib_formula,
             "valor": f"Ib = {l.get('Ib')} A (para P = {l.get('potencia')} W).",
             "referencia": "REBT, ITC-BT-19 · UNE-HD 60364-5-52."},
            {"tema": "Intensidad máxima admisible del conductor (Iz)",
             "formula": f"Iz según sección y método de instalación (conductor {mat}).",
             "valor": f"Sección adoptada {l.get('seccion_txt')} mm² → Iz = {l.get('iz')} A ≥ Ib.",
             "referencia": "REBT, ITC-BT-19, Tabla 1 (intensidades admisibles)."},
            {"tema": "Caída de tensión",
             "formula": e_formula + f", con L = {l.get('longitud')} m",
             "valor": f"c.d.t. del tramo = {l.get('caida_pct')} % · acumulada = {l.get('caida_acum_pct')} %.",
             "referencia": "REBT, ITC-BT-19 (3 % alumbrado / 5 % otros usos; 4,5 %/6,5 % con transformador propio)."},
            {"tema": "Protección frente a sobrecargas (coordinación con el cable)",
             "formula": "Ib ≤ In ≤ Iz  y  I2 ≤ 1,45 · Iz  (I2 = 1,45 · In)",
             "valor": (f"{co.get('Ib')} A ≤ {co.get('In')} A ≤ {co.get('Iz')} A  y  "
                       f"I2 {co.get('I2')} A ≤ 1,45·Iz {co.get('I2_max')} A → "
                       f"{'CUMPLE' if co.get('protege') else 'NO CUMPLE'}."),
             "referencia": "REBT, ITC-BT-22 · UNE-HD 60364-4-43."},
            {"tema": "Protección frente a cortocircuitos",
             "formula": "Poder de corte ≥ Icc_máx · k²·S² ≥ I²t · Icc_mín ≥ Im",
             "valor": (f"Icc_máx = {cc.get('icc_max_a')} A, Icc_mín = {cc.get('icc_min_a')} A, "
                       f"Im = {cc.get('im_a')} A (curva {cc.get('curva')}); "
                       f"k²·S² = {cc.get('i2t_cable')} ≥ I²t = {cc.get('i2t_paso')} → "
                       f"{'CUMPLE' if cc.get('protege_cc') else 'NO CUMPLE'}."),
             "referencia": "REBT, ITC-BT-22 · UNE-HD 60364-4-43 (Guía BT-22, método simplificado)."},
        ]
        bloques.append({
            "circuito": f"{l.get('cuadro')} · {l.get('circuito')}",
            "estado": l.get("estado"), "pasos": pasos,
        })
    return bloques
