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
