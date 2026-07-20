"""Test integral del módulo unificado de Incendios (RSCIEI + CTE DB-SI).

Cubre: fórmulas reglamentarias con valores conocidos, límites de tablas
(RD 164/2025 y DB-SI), coherencia interna (monotonía de umbrales y de la
resistencia estructural), enrutado del módulo unificado, proyectos mixtos,
estructura del informe y validaciones. Un solo archivo, ejecutable con pytest.
"""
import math
import re

import pytest

from normative_modules.registry import bootstrap_modules
from normative_modules.rsciei import engine as rs
from normative_modules.rsciei import requirements as rq
from normative_modules.rsciei import catalog as cat
from normative_modules.cte_dbsi import engine as db
from normative_modules.incendios import engine as inc
from normative_modules.incendios import report as inc_report
from normative_modules.incendios import schema as inc_schema


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _r_to_int(v):
    """R 90 -> 90 ; NO ADMITIDO -> inf (más restrictivo)."""
    if "ADMIT" in v.upper():
        return math.inf
    m = re.search(r"(\d+)", v)
    return int(m.group(1)) if m else 0


def rsciei_sector(qsi=400, ci=1.44, sup=1000, ra=1.0, config="C", **sec):
    base = {"id": "s1", "nombre": "S", "tipo": "sector", "config": config,
            "situacion": "sobre_rasante", "num_salidas": 2}
    base.update(sec)
    return {
        "establecimiento": {"config": config},
        "sectores": [base],
        "dependencias": [{"id": "d1", "nombre": "Z", "sup_construida": sup,
                          "sector_id": "s1", "modo": "produccion",
                          "qsi": qsi, "ci": ci, "ra": ra, "sin_ocupacion": True}],
    }


# --------------------------------------------------------------------------- #
# 1 · RSCIEI · fórmula de Qs y nivel de riesgo intrínseco
# --------------------------------------------------------------------------- #
def test_qs_single_activity():
    r = rs.compute(rsciei_sector(qsi=400, ci=1.44, sup=846.78, ra=1.0))
    # Qs = (400*1.44*S)/S * 1 = 576
    assert r["sectores"][0]["calculo"]["qs_mj"] == pytest.approx(576.0, abs=0.1)


def test_qs_weighted_multi_activity():
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{"id": "s1", "nombre": "S", "tipo": "sector", "config": "C",
                      "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0}],
        "dependencias": [
            {"id": "d1", "sup_construida": 100, "sector_id": "s1", "modo": "produccion", "qsi": 800, "ci": 1.0, "ra": 1.0, "sin_ocupacion": True},
            {"id": "d2", "sup_construida": 100, "sector_id": "s1", "modo": "produccion", "qsi": 400, "ci": 1.0, "ra": 1.0, "sin_ocupacion": True},
        ],
    }
    # numerador = (800+400)*100 = 120000 ; A = 200 ; Qs = 600
    r = rs.compute(data)
    assert r["sectores"][0]["calculo"]["qs_mj"] == pytest.approx(600.0, abs=0.1)


def test_qs_storage_uses_height():
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{"id": "s1", "nombre": "S", "tipo": "sector", "config": "C", "num_salidas": 2, "ra": 1.0}],
        "dependencias": [{"id": "d1", "sup_construida": 100, "sector_id": "s1",
                          "modo": "almacenamiento", "qvi": 200, "ci": 1.0, "hi": 3.0, "ra": 1.0, "sin_ocupacion": True}],
    }
    # Qs = (200*1*3*100)/100 = 600
    r = rs.compute(data)
    assert r["sectores"][0]["calculo"]["qs_mj"] == pytest.approx(600.0, abs=0.1)


@pytest.mark.parametrize("qs,nivel,cat", [
    (400, 1, "BAJO"), (425, 1, "BAJO"), (426, 2, "BAJO"), (850, 2, "BAJO"),
    (851, 3, "MEDIO"), (1275, 3, "MEDIO"), (1276, 4, "MEDIO"), (1700, 4, "MEDIO"),
    (1701, 5, "MEDIO"), (3400, 5, "MEDIO"), (3401, 6, "ALTO"), (6800, 6, "ALTO"),
    (6801, 7, "ALTO"), (13600, 7, "ALTO"), (20000, 8, "ALTO"),
])
def test_nri_boundaries(qs, nivel, cat):
    # La Tabla 1.3.1 usa intervalos con límite superior inclusivo:
    # el valor frontera pertenece al nivel inferior.
    n, c = rs._nri_for(qs)
    assert (n, c) == (nivel, cat)


# --------------------------------------------------------------------------- #
# 2 · RSCIEI · Tabla 2.1.1 superficie máxima (RD 164/2025)
# --------------------------------------------------------------------------- #
def test_max_surface_values_rd164():
    m = rs.MAX_SURFACE
    assert m["C"][1] == "SIN_LIMITE" and m["C"][2] == 12000 and m["C"][8] == 4000
    assert m["AV"][6] is None and m["AV"][7] is None and m["AV"][8] is None
    assert m["AH"][7] == 1500 and m["AH"][8] is None
    assert m["B"][7] == 3000 and m["B"][8] is None


def test_max_surface_monotonic_decreasing():
    for cfg in ("AV", "AH", "B"):
        vals = [rs.MAX_SURFACE[cfg][n] for n in range(1, 9)]
        nums = [v for v in vals if isinstance(v, (int, float))]
        assert nums == sorted(nums, reverse=True), f"{cfg} no es decreciente"


def test_sectorizacion_factors():
    # B, nivel bajo: base 12000. fachada x1.25, rociadores x2, bajo rasante /2
    base = rsciei_sector(qsi=100, ci=1.0, sup=100, ra=1.0, config="B")
    r = rs.compute(base)["sectores"][0]["sectorizacion"]
    assert r["max_admisible"] == pytest.approx(12000)

    r2 = rs.compute(rsciei_sector(qsi=100, ci=1.0, sup=100, config="B", fachada_accesible=True, rociadores=True))["sectores"][0]["sectorizacion"]
    assert r2["max_admisible"] == pytest.approx(12000 * 1.25 * 2)

    r3 = rs.compute(rsciei_sector(qsi=100, ci=1.0, sup=100, config="B", situacion="bajo_rasante"))["sectores"][0]["sectorizacion"]
    assert r3["max_admisible_base"] == pytest.approx(6000)


def test_sector_exceeds_surface_no_cumple():
    # C nivel 2 max 12000; poner A=13000 con Qs en rango nivel2
    data = rsciei_sector(qsi=600, ci=1.0, sup=13000, ra=1.0, config="C")  # Qs=600 -> nivel2
    r = rs.compute(data)["sectores"][0]
    assert r["nivel_riesgo"]["nivel"] == 2
    assert r["sectorizacion"]["estado"] == "no_cumple"
    assert r["estado"] == "no_cumple"


# --------------------------------------------------------------------------- #
# 3 · RSCIEI · Rmin y coeficiente Ra
# --------------------------------------------------------------------------- #
def test_rmin_warning_when_ra_below():
    data = rsciei_sector(qsi=100, ci=1.92, sup=200, config="C", ra=1.0)
    data["dependencias"][0]["rmin"] = 1.4
    r = rs.compute(data)["sectores"][0]
    assert any(o["tipo"] == "warning" and "Rmin" in o["texto"] for o in r["observaciones"])


def test_catalog_rmin_present_and_coherent():
    total = 0
    for c in cat.ACTIVITY_CATALOG:
        for s in c["subactivities"]:
            total += 1
            assert "rmin" in s
            assert s["modo"] in ("produccion", "almacenamiento")
            if s["modo"] == "produccion":
                assert "qsi" in s and s["qsi"] > 0
            else:
                assert "qvi" in s and s["qvi"] > 0
            if s["rmin"]:
                assert s["ra"] >= s["rmin"] - 1e-9
    assert total >= 120  # catálogo Tabla 1.3.5 completo


# --------------------------------------------------------------------------- #
# 4 · RSCIEI · evacuación (Tabla 2.3.1 + notas 4/5)
# --------------------------------------------------------------------------- #
def test_evac_nota4a_increment():
    data = rsciei_sector(qsi=400, ci=1.0, sup=800, config="C")  # nivel bajo
    data["sectores"][0]["evac_coeficiente"] = "nota4a"
    data["sectores"][0]["recorridos"] = [{"id": "r1", "origen": "A", "tipo": "hasta_salida", "distancia_real": 55}]
    ev = rs.compute(data)["sectores"][0]["evacuacion"]
    # BAJO, varias salidas: base 50 -> x1.25 = 62.5
    assert ev["distancia_maxima"] == pytest.approx(62.5)
    assert ev["recorridos"][0]["cumple"] is True


def test_evac_recorrido_no_cumple_sets_error():
    data = rsciei_sector(qsi=400, ci=1.0, sup=800, config="C")
    data["sectores"][0]["recorridos"] = [{"id": "r1", "origen": "A", "tipo": "sin_alternativa", "distancia_real": 999}]
    r = rs.compute(data)["sectores"][0]
    assert r["evacuacion"]["recorridos"][0]["cumple"] is False
    assert r["estado"] == "no_cumple"


def test_evac_nota5_only_bajo_nivel1():
    # riesgo MEDIO -> nota5 debe ignorarse (coeficiente 'ninguno')
    data = rsciei_sector(qsi=1000, ci=1.0, sup=800, config="C")  # Qs 1000 -> nivel3 MEDIO
    data["sectores"][0]["evac_coeficiente"] = "nota5"
    ev = rs.compute(data)["sectores"][0]["evacuacion"]
    assert ev["coeficiente"] == "ninguno"


# --------------------------------------------------------------------------- #
# 5 · RSCIEI · coherencia de requisitos (Anexo II y III)
# --------------------------------------------------------------------------- #
def test_estabilidad_monotonic_with_risk_and_situation():
    for cfg in ("AV", "AH", "B", "C"):
        for sit in ("sobre", "bajo"):
            vals = [_r_to_int(rq.ESTABILIDAD[cfg][sit][c]) for c in ("BAJO", "MEDIO", "ALTO")]
            assert vals == sorted(vals), f"{cfg}/{sit} R no crece con el riesgo"
        for c in ("BAJO", "MEDIO", "ALTO"):
            assert _r_to_int(rq.ESTABILIDAD[cfg]["bajo"][c]) >= _r_to_int(rq.ESTABILIDAD[cfg]["sobre"][c]), \
                f"{cfg}/{c}: sótano debe ser >= sobre rasante"


def test_anexo3_thresholds_monotonic():
    def mono(table):
        for cfg, cells in table.items():
            if "any" in cells:
                continue
            present = [cells[k] for k in ("BAJO", "MEDIO", "ALTO") if k in cells]
            assert present == sorted(present, reverse=True), f"{cfg}: umbral no decrece con el riesgo"
    mono(rq.DETECCION["produccion"]); mono(rq.DETECCION["almacenamiento"])
    mono(rq.ROCIADORES["produccion"]); mono(rq.ROCIADORES["almacenamiento"])
    mono(rq.BIE); mono(rq.HIDRANTES)


def test_requirements_extintores_always_and_bajo_nivel1_exempt_deteccion():
    req = rq.build_requirements({"config": "C", "situacion": "sobre_rasante"}, 1, "BAJO", "produccion", 300, 300)
    inst = {i["nombre"]: i for i in req["instalaciones"]}
    assert inst["Extintores portátiles"]["obligatorio"] is True
    assert inst["Detección automática de incendio"]["obligatorio"] is False


def test_hidrante_camion_tabla331():
    # C: umbral 5000 m² totales
    req_lo = rq.build_requirements({"config": "C"}, 2, "BAJO", "produccion", 1000, 4000)
    req_hi = rq.build_requirements({"config": "C"}, 2, "BAJO", "produccion", 1000, 6000)
    g = lambda req: [i for i in req["instalaciones"] if "camiones" in i["nombre"]][0]["obligatorio"]
    assert g(req_lo) is False and g(req_hi) is True


# --------------------------------------------------------------------------- #
# 6 · RSCIEI · validaciones
# --------------------------------------------------------------------------- #
def test_rsciei_validation_errors():
    with pytest.raises(ValueError):
        rs.compute({"sectores": [], "dependencias": []})
    with pytest.raises(ValueError):
        # dependencia sin sector
        rs.compute({"establecimiento": {"config": "C"},
                    "sectores": [{"id": "s1", "nombre": "S", "tipo": "sector", "config": "C"}],
                    "dependencias": [{"id": "d1", "sup_construida": 100, "modo": "produccion", "qsi": 100, "ci": 1.0}]})


# --------------------------------------------------------------------------- #
# 7 · CTE DB-SI
# --------------------------------------------------------------------------- #
def dbsi_data(uso="Administrativo", sup=1200, alt=9, salidas=2, rec=30, bajo=False, deps=None):
    return {"uso": uso, "superficie_construida": sup, "altura_evacuacion": alt,
            "num_salidas": salidas, "recorrido_max_real": rec, "bajo_rasante": bajo,
            "dependencias": deps or [{"id": "z1", "nombre": "P1", "superficie": 1000, "densidad": 10, "uso_ocupacion": "Administrativo"}]}


def test_dbsi_occupancy_ceil():
    r = db.compute(dbsi_data(deps=[{"id": "z1", "superficie": 1005, "densidad": 10}]))
    assert r["ocupacion"]["total"] == math.ceil(1005 / 10)  # 101


def test_dbsi_si3_salidas_and_recorrido():
    # ocupación 101 > 100 => 2 salidas requeridas
    r = db.compute(dbsi_data(salidas=1, deps=[{"id": "z1", "superficie": 1010, "densidad": 10}]))
    assert r["si3"]["salidas_requeridas"] == 2
    assert r["si3"]["salidas_ok"] is False
    # ancho = max(0.8, P/200)
    assert r["si3"]["ancho_calculado"] == pytest.approx(max(0.8, r["ocupacion"]["total"] / 200), abs=0.01)


def test_dbsi_si6_by_use_height():
    assert db._si6("Administrativo", 10, False)["estabilidad"] == "R 60"
    assert db._si6("Administrativo", 20, False)["estabilidad"] == "R 90"
    assert db._si6("Comercial", 10, False)["estabilidad"] == "R 90"
    assert db._si6("Administrativo", 5, True)["estabilidad"] == "R 120"
    assert db._si6("Aparcamiento", 30, False)["estabilidad"] == "R 90"


def test_dbsi_si1_max_sector():
    assert db._si1("Administrativo", 3000)["cumple"] is False   # >2500
    assert db._si1("Aparcamiento", 99999)["cumple"] is True     # sin límite


def test_dbsi_validation():
    with pytest.raises(ValueError):
        db.compute({"uso": "", "superficie_construida": 0, "dependencias": []})


# --------------------------------------------------------------------------- #
# 8 · MÓDULO UNIFICADO
# --------------------------------------------------------------------------- #
def test_registry_only_incendios_operativo():
    reg = bootstrap_modules()
    ops = [m.code for m in reg.all() if m.status == "operativo"]
    assert ops == ["INCENDIOS"]
    assert reg.get("RSCIEI") is None and reg.get("CTE") is None


def test_schema_exposes_both():
    sc = inc_schema.get_schema()
    assert set(sc.keys()) == {"rsciei", "dbsi"}
    assert len(sc["rsciei"]["steps"]) == 5 and len(sc["dbsi"]["steps"]) == 2


def _mixed_data():
    ind = rsciei_sector(qsi=400, ci=1.44, sup=800, config="C")
    ind = {"id": "a1", "tipo": "industrial", "nombre": "Nave", **ind}
    edi = {"id": "a2", "tipo": "edificacion", "nombre": "Oficinas", **dbsi_data()}
    return {"ambitos": [ind, edi]}


def test_unified_mixed_compute():
    r = inc.compute(_mixed_data())
    assert [a["tipo"] for a in r["ambitos"]] == ["industrial", "edificacion"]
    assert r["estado_global"] in ("cumple", "observaciones", "no_cumple")
    assert "sectores" in r["ambitos"][0]["results"]
    assert "si3" in r["ambitos"][1]["results"]


def test_unified_estado_global_is_worst():
    data = _mixed_data()
    # forzar no_cumple en el ámbito industrial (recorrido imposible)
    data["ambitos"][0]["sectores"][0]["recorridos"] = [{"id": "r", "origen": "x", "tipo": "sin_alternativa", "distancia_real": 999}]
    assert inc.compute(data)["estado_global"] == "no_cumple"


def test_unified_report_structure():
    data = _mixed_data()
    res = inc.compute(data)
    rep = inc_report.build_report({"code": "P", "name": "N"}, {"name": "E"}, data, res)
    headers = [s for s in rep["sections"] if s["type"] == "ambito_header"]
    assert len(headers) == 2
    ids = [s["id"] for s in rep["sections"]]
    assert len(ids) == len(set(ids)), "ids de sección duplicados"


def test_unified_validation():
    with pytest.raises(ValueError):
        inc.compute({"ambitos": []})
    with pytest.raises(ValueError) as e:
        inc.compute({"ambitos": [{"id": "a1", "tipo": "industrial", "nombre": "X",
                                  "establecimiento": {"config": "C"}, "sectores": [], "dependencias": []}]})
    assert "Ámbito" in str(e.value)
