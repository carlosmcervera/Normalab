from normative_modules.base import NormativeModule


class CteModule(NormativeModule):
    code = "CTE"
    name = "Código Técnico de la Edificación"
    short_name = "CTE"
    description = ("Estructura preparada para la Parte I y los Documentos Básicos "
                   "(DB-SI, DB-SUA, DB-HE, DB-HR, DB-HS, DB-SE). Módulo en preparación.")
    category = "Edificación"
    status = "placeholder"
    legal_reference = "RD 314/2006 y modificaciones posteriores"
    icon = "building-2"
    accent = "blue"


class RebtModule(NormativeModule):
    code = "REBT"
    name = "Reglamento Electrotécnico para Baja Tensión"
    short_name = "REBT"
    description = ("Instrucciones Técnicas Complementarias (ITC-BT). "
                   "Módulo en preparación.")
    category = "Instalaciones"
    status = "placeholder"
    legal_reference = "RD 842/2002"
    icon = "zap"
    accent = "amber"


class RiteModule(NormativeModule):
    code = "RITE"
    name = "Reglamento de Instalaciones Térmicas en los Edificios"
    short_name = "RITE"
    description = ("Instalaciones térmicas de calefacción, climatización y ACS. "
                   "Módulo en preparación.")
    category = "Instalaciones"
    status = "placeholder"
    legal_reference = "RD 1027/2007"
    icon = "thermometer"
    accent = "rose"


class AccesibilidadModule(NormativeModule):
    code = "ACCESS2023"
    name = "RD Accesibilidad 2023"
    short_name = "Accesibilidad"
    description = ("Condiciones básicas de accesibilidad y no discriminación. "
                   "Módulo en preparación.")
    category = "Edificación"
    status = "placeholder"
    legal_reference = "RD 193/2023"
    icon = "accessibility"
    accent = "emerald"
