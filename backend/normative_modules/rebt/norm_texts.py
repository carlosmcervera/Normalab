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
]
