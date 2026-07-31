"""Extractos literales de la normativa para fundamentar los resultados del informe.

Cada extracto incluye el tema, la cita (texto literal/normativo) y la referencia
exacta al artículo/tabla del RSCIEI (RD 164/2025) o del CTE DB-SI (RD 314/2006).
Se separan de la lógica de cálculo para mantener el informe legible.
"""

# Extractos base, siempre incluidos en el estudio de incendios.
FUNDAMENTOS_BASE = [
    {
        "tema": "Densidad de carga de fuego, ponderada y corregida (Qs)",
        "cita": ("«La densidad de carga de fuego, ponderada y corregida, Qs, del sector o área de "
                 "incendio se determinará mediante la expresión: Qs = (Σ qsi · Si · Ci / A) · Ra "
                 "(MJ/m² o Mcal/m²), donde qsi es la densidad de carga de fuego de cada zona, Ci el "
                 "coeficiente adimensional que refleja la peligrosidad de los combustibles, Ra el "
                 "coeficiente de riesgo de activación y A la superficie construida del sector.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo I, apartado 3.2.",
    },
    {
        "tema": "Nivel de riesgo intrínseco (NRI)",
        "cita": ("«El nivel de riesgo intrínseco de cada sector o área de incendio se evalúa calculando "
                 "la densidad de carga de fuego ponderada y corregida (Qs) y comparándola con los "
                 "valores de la Tabla 1.3: riesgo bajo (niveles 1-2, Qs ≤ 850 MJ/m²), medio (niveles "
                 "3-5, 850 < Qs ≤ 3.400 MJ/m²) y alto (niveles 6-8, Qs > 3.400 MJ/m²).»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo I, Tabla 1.3.",
    },
    {
        "tema": "Superficie máxima admisible del sector de incendio",
        "cita": ("«La máxima superficie construida admisible de cada sector de incendio se establece en "
                 "función de su configuración (tipo A, B o C) y de su nivel de riesgo intrínseco, "
                 "conforme a la Tabla 2.1. Dicha superficie podrá duplicarse cuando el sector disponga "
                 "de una instalación fija automática de extinción y podrá incrementarse un 25 % cuando "
                 "el sector cuente con fachadas accesibles en al menos el 50 % de su perímetro.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 2.1 y Tabla 2.1.",
    },
    {
        "tema": "Estabilidad al fuego de la estructura portante",
        "cita": ("«Los elementos estructurales portantes de los sectores de incendio deben tener la "
                 "estabilidad al fuego (R) que se indica en la Tabla 2.5, en función del tipo de "
                 "configuración del establecimiento, de la planta (sobre o bajo rasante) y del nivel de "
                 "riesgo intrínseco del sector.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 4 y Tabla 2.5.",
    },
    {
        "tema": "Evacuación · longitud máxima de los recorridos",
        "cita": ("«La longitud del recorrido de evacuación no será superior a la indicada en la Tabla 2.3 "
                 "en función del nivel de riesgo intrínseco del sector y del número de salidas: como "
                 "regla general 50 m con dos o más salidas alternativas y 25 m cuando exista una única "
                 "salida o recorrido, admitiéndose incrementos cuando el sector disponga de instalación "
                 "de extinción automática o de control de humos.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 6 y Tabla 2.3.",
    },
    {
        "tema": "Reacción al fuego de los elementos constructivos",
        "cita": ("«Los productos de revestimiento de suelos, paredes y techos cumplirán las clases de "
                 "reacción al fuego establecidas en la Tabla 2.4; en pasillos y escaleras protegidos, "
                 "así como en los sectores de riesgo intrínseco alto, se exigirán clases más restrictivas.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 3 y Tabla 2.4.",
    },
    {
        "tema": "Locales y zonas de riesgo especial (CTE)",
        "cita": ("«Los locales de riesgo especial se clasifican en riesgo bajo, medio o alto conforme a "
                 "los criterios de la Tabla 2.1 (volumen, superficie o potencia según el uso) y deben "
                 "cumplir las condiciones de resistencia al fuego de su estructura y de sectorización, "
                 "vestíbulo de independencia y recorridos que fija la Tabla 2.2.»"),
        "referencia": "CTE DB-SI, Sección SI 1, apartado 2 y Tablas 2.1 y 2.2.",
    },
]

# Extractos específicos de escaleras (Fase 3), incluidos solo si el estudio tiene escaleras.
FUNDAMENTO_ESCALERAS_DIM = {
    "tema": "Dimensionado de escaleras de evacuación (anchura)",
    "cita": ("«El dimensionado de los elementos de evacuación se realiza conforme a la Tabla 4.1. Para "
             "escaleras no protegidas de evacuación descendente la anchura cumple A ≥ P/160, siendo P "
             "el número de personas asignadas a la escalera. Para escaleras protegidas la capacidad de "
             "evacuación se obtiene de E ≤ 3·S + 160·As, donde S es la superficie útil del recinto de "
             "la escalera protegida y As su anchura. La anchura libre no será menor de 1,00 m (0,80 m "
             "en zonas de uso restringido).»"),
    "referencia": "CTE DB-SI, Sección SI 3, apartado 4 y Tabla 4.1.",
}
FUNDAMENTO_ESCALERAS_PROT = {
    "tema": "Protección de las escaleras según la altura de evacuación",
    "cita": ("«La necesidad de proteger las escaleras previstas para evacuación (no protegida, protegida "
             "o especialmente protegida) se determina según la Tabla 5.1, en función del uso previsto, "
             "del sentido de evacuación (ascendente o descendente) y de la altura de evacuación del "
             "recinto. El recinto de una escalera protegida debe compartimentarse con paredes EI 120 y "
             "puertas EI2 60-C5; la especialmente protegida añade vestíbulos de independencia con "
             "ventilación.»"),
    "referencia": "CTE DB-SI, Sección SI 3, apartado 5 y Tabla 5.1.",
}


def build_fundamentos(results: dict) -> list:
    """Devuelve los extractos aplicables al estudio (base + escaleras si procede)."""
    fundamentos = list(FUNDAMENTOS_BASE)
    tiene_escaleras = any(s.get("escaleras_protegidas") for s in results.get("sectores", []))
    if tiene_escaleras:
        fundamentos.append(FUNDAMENTO_ESCALERAS_DIM)
        fundamentos.append(FUNDAMENTO_ESCALERAS_PROT)
    return fundamentos


# --- Anexo justificativo de propagación (interior + exterior) por sector ---------

def _estado_txt(estado):
    return {"cumple": "cumple", "no_cumple": "NO cumple", "pendiente": "pendiente de justificar"}.get(estado, "informativo")


def _cita_rsciei(construccion, delim_req):
    interior = [
        {"tema": "Reacción al fuego de los revestimientos (interior)",
         "cita": ("«Los productos de revestimiento de suelos, paredes y techos cumplirán las clases de "
                  "reacción al fuego de la Tabla 2.4. Con carácter general: en techos y paredes C-s2,d0 y "
                  "en suelos CFL-s1; en pasillos y escaleras protegidos B-s1,d0, y en sectores de riesgo "
                  "intrínseco alto y aparcamientos, clases más restrictivas.»"),
         "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 3 y Tabla 2.4.",
         "valor": ("Verificación de las clases del proyecto: "
                   + ("cumple." if (construccion.get("reaccion") or {}).get("cumple") else "pendiente de justificar."))},
        {"tema": "Elementos delimitadores del sector (compartimentación interior)",
         "cita": ("«Los elementos que delimitan un sector de incendio respecto de otros sectores del mismo "
                  "establecimiento tendrán una resistencia al fuego (EI) no inferior a la indicada en la "
                  "Tabla 2.2, en función del nivel de riesgo intrínseco del sector.»"),
         "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 2 y Tabla 2.2.",
         "valor": f"Resistencia exigida a los delimitadores del sector: {delim_req}."},
    ]
    exterior = []
    med = construccion.get("medianeras")
    exterior.append({
        "tema": "Medianerías y separación con otros establecimientos (exterior)",
        "cita": ("«Cuando el establecimiento linde con otro edificio o establecimiento, los elementos "
                 "constructivos que los separen serán, como mínimo, EI 120 (riesgo bajo), EI 180 (medio) o "
                 "EI 240 (alto), pudiendo reducirse a EI 120 en configuraciones tipo B con las condiciones "
                 "de la nota de la Tabla 2.2.1.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 2 y Tabla 2.2.1.",
        "valor": (f"Exigido {med['requerido']} · proyectado {med['proyectado'] or '—'} ({_estado_txt(med['estado'])})."
                  if med else "El sector no linda con otro establecimiento."),
    })
    fach = construccion.get("fachadas")
    fach_val = "Sin encuentro de elementos compartimentadores en fachada."
    if fach:
        fach_val = (f"Encuentro en fachada con ángulo α = {fach.get('angulo')}° (franja d ≥ {fach.get('distancia_d')} m); "
                    f"exigido {fach.get('requerido')} · proyectado {fach.get('proyectado') or '—'} ({_estado_txt(fach.get('estado'))}).")
    exterior.append({
        "tema": "Propagación exterior por fachada (exterior)",
        "cita": ("«Para limitar el riesgo de propagación exterior del incendio por la fachada, la clase de "
                 "reacción al fuego de los materiales que ocupen más del 10 % de la superficie del acabado "
                 "exterior será B-s3,d2. Donde acometa un elemento compartimentador, la fachada tendrá una "
                 "resistencia al fuego EI no inferior a la mitad de la del elemento en una franja, con "
                 "separación d = 3 − α/90 (m) en proyección horizontal según el ángulo α entre planos.»"),
        "referencia": "RSCIEI (RD 164/2025), Anexo II, apartado 2 y Tabla 2.2.2.",
        "valor": fach_val,
    })
    huecos = (fach or {}).get("huecos")
    if huecos:
        exterior.append({
            "tema": "Separación entre huecos de sectores/edificios distintos (exterior)",
            "cita": ("«Los huecos de fachada de sectores de incendio diferentes o de edificios colindantes "
                     "estarán separados una distancia mínima que depende del ángulo entre sus planos de "
                     "fachada (Fig. 1.1), salvo que estén dotados de una resistencia al fuego EI 60.»"),
            "referencia": "CTE DB-SI, Sección SI 2, apartado 1 y Fig. 1.1 (referida por el RSCIEI).",
            "valor": (f"Ángulo {huecos['angulo']:.0f}° · separación mínima {huecos['efectivo_m']:.2f} m"
                      + (f" · proyectada {huecos['proyectado_m']:.2f} m" if huecos.get('proyectado_m') is not None else "")
                      + f" ({_estado_txt(huecos.get('estado'))})."),
        })
    return interior, exterior


def _cita_cte(construccion, delim_req):
    interior = [
        {"tema": "Reacción al fuego de los revestimientos (SI 1)",
         "cita": ("«Los elementos constructivos cumplirán las condiciones de reacción al fuego de la "
                  "Tabla 4.1 de la Sección SI 1: en zonas ocupables y recorridos de evacuación C-s2,d0 en "
                  "techos y paredes y EFL en suelos; en pasillos y escaleras protegidos B-s1,d0 y CFL-s1; "
                  "en recintos de riesgo especial y aparcamientos, clases más exigentes.»"),
         "referencia": "CTE DB-SI, Sección SI 1, apartado 4 y Tabla 4.1.",
         "valor": ("Verificación de las clases del proyecto: "
                   + ("cumple." if (construccion.get("reaccion") or {}).get("cumple") else "pendiente de justificar."))},
        {"tema": "Compartimentación en sectores de incendio (SI 1)",
         "cita": ("«La resistencia al fuego de las paredes, techos y puertas que delimitan sectores de "
                  "incendio se ajustará a la Tabla 1.2, en función de la altura de evacuación del edificio "
                  "y de si el sector está sobre o bajo rasante.»"),
         "referencia": "CTE DB-SI, Sección SI 1, apartado 1 y Tabla 1.2.",
         "valor": f"Resistencia exigida a los delimitadores del sector: {delim_req}."},
    ]
    exterior = []
    med = construccion.get("medianeras")
    exterior.append({
        "tema": "Medianerías y muros colindantes (SI 2)",
        "cita": ("«Los elementos verticales separadores de otro edificio serán, al menos, EI 120 para "
                 "limitar la propagación exterior del incendio entre edificios colindantes.»"),
        "referencia": "CTE DB-SI, Sección SI 2, apartado 1.",
        "valor": (f"Exigido EI 120 · proyectado {med['proyectado'] or '—'} ({_estado_txt(med['estado'])})."
                  if med else "El sector no linda con otro edificio."),
    })
    fach = construccion.get("fachadas")
    huecos = (fach or {}).get("huecos")
    fach_val = "Sin encuentro de sectores/edificios en fachada."
    if fach:
        fach_val = f"Franja de fachada exigida {fach.get('requerido')} · proyectado {fach.get('proyectado') or '—'} ({_estado_txt(fach.get('estado'))})."
    exterior.append({
        "tema": "Propagación exterior por fachada y separación entre huecos (SI 2)",
        "cita": ("«Con el fin de limitar el riesgo de propagación exterior horizontal del incendio entre "
                 "dos sectores, entre una zona de riesgo especial alto y otras zonas, o hacia un edificio "
                 "colindante, los puntos de sus fachadas que no sean al menos EI 60 estarán separados la "
                 "distancia d (en proyección horizontal) que, en función del ángulo α formado por los "
                 "planos de fachada, se indica en la Fig. 1.1. La franja de fachada será EI 60 en una "
                 "altura de al menos 1 m.»"),
        "referencia": "CTE DB-SI, Sección SI 2, apartado 1 y Fig. 1.1.",
        "valor": (fach_val + (f" Separación entre huecos: ángulo {huecos['angulo']:.0f}° · mínima {huecos['efectivo_m']:.2f} m"
                              + (f" · proyectada {huecos['proyectado_m']:.2f} m" if huecos.get('proyectado_m') is not None else "")
                              + f" ({_estado_txt(huecos.get('estado'))})." if huecos else "")),
    })
    exterior.append({
        "tema": "Cubiertas (SI 2)",
        "cita": ("«Con el fin de limitar el riesgo de propagación exterior del incendio por la cubierta, "
                 "ésta tendrá una resistencia al fuego REI 60 en una franja de 0,50 m de anchura medida "
                 "desde el edificio colindante, así como en una franja de 1,00 m de anchura situada sobre "
                 "el encuentro con la cubierta de todo elemento compartimentador de un sector de incendio "
                 "o de un local de riesgo especial alto.»"),
        "referencia": "CTE DB-SI, Sección SI 2, apartado 2.",
        "valor": ("Cubierta ligera declarada." if (construccion.get("cubierta") or {}).get("ligera") else "Cubierta no ligera."),
    })
    return interior, exterior


def build_anexo_propagacion(results: dict) -> list:
    """Anexo justificativo de propagación (interior + exterior) por sector, con citas literales."""
    bloques = []
    for s in results.get("sectores", []):
        construccion = s.get("construccion") or {}
        es_cte = construccion.get("ambito") == "cte"
        delim_req = ((construccion.get("interior") or {}).get("delimitadores") or {}).get("requerido") \
            or (s.get("requisitos") or {}).get("delimitadores", {}).get("valor", "—")
        interior, exterior = (_cita_cte(construccion, delim_req) if es_cte
                              else _cita_rsciei(construccion, delim_req))
        bloques.append({
            "sector": s.get("nombre", "Sector"),
            "ambito": "CTE DB-SI" if es_cte else "RSCIEI",
            "normativa": construccion.get("normativa", "RSCIEI (Anexo II)"),
            "interior": interior,
            "exterior": exterior,
        })
    return bloques
