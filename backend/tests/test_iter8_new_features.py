"""Iteration 8 tests:
- RSCIEI evacuation extension (recorridos, coeficientes nota4a/4b/4c/nota5)
- CTE DB-SI new operative module (schema + compute + report + validations)
"""
import os
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://normlab.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PASSWORD = "Admin1234!"


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def project_id(admin_session):
    r = admin_session.post(f"{API}/projects", json={
        "code": f"TEST-IT8-{int(time.time())}", "name": "TEST it8"})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _create_study(admin_session, project_id, name, module="RSCIEI"):
    r = admin_session.post(f"{API}/studies", json={
        "project_id": project_id, "module_code": module, "name": name})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _put_compute(sess, sid, data, expect=200):
    r = sess.put(f"{API}/studies/{sid}", json={"data": data})
    assert r.status_code == 200, r.text
    cr = sess.post(f"{API}/studies/{sid}/compute")
    assert cr.status_code == expect, cr.text
    return cr


# ---- RSCIEI evacuation ----
def _rsciei_base(evac_coef=None, recorridos=None, extra_dep=None):
    data = {
        "establecimiento": {"actividad": "Nave", "config": "B"},
        "sectores": [
            {"id": "S1", "nombre": "Sector 1", "tipo": "sector",
             "config": "B", "situacion": "sobre_rasante", "num_salidas": 2,
             "altura_evacuacion": 6},
        ],
        "dependencias": [
            {"id": "D1", "nombre": "Zona", "planta": "0",
             "sup_util": 400, "sup_construida": 500, "sector_id": "S1",
             "densidad": 20, "modo": "produccion",
             "qsi": 300, "ci": 1.0, "ra": 1.0},
        ],
    }
    if evac_coef is not None:
        data["sectores"][0]["evac_coeficiente"] = evac_coef
    if recorridos is not None:
        data["sectores"][0]["recorridos"] = recorridos
    if extra_dep:
        data["dependencias"].append(extra_dep)
    return data


class TestRscieiEvacuation:
    def test_evacuacion_default_shape(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_evac_default")
        try:
            cr = _put_compute(admin_session, sid,
                              _rsciei_base(recorridos=[{"origen": "Origen A", "tipo": "hasta_salida", "distancia_real": 30}]))
            sec = cr.json()["results"]["sectores"][0]
            ev = sec["evacuacion"]
            for k in ("num_salidas", "coeficiente", "coeficiente_label",
                      "distancia_maxima", "recorrido_sin_alternativa", "recorridos"):
                assert k in ev, f"missing {k}"
            assert ev["coeficiente"] == "ninguno"
            assert ev["distancia_maxima"] == 50  # BAJO, varias salidas
            r0 = ev["recorridos"][0]
            for k in ("origen", "tipo", "distancia_real", "distancia_max", "cumple"):
                assert k in r0
            assert r0["cumple"] is True
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_nota4a_multiplies_1_25(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_nota4a")
        try:
            cr = _put_compute(admin_session, sid,
                              _rsciei_base(evac_coef="nota4a",
                                           recorridos=[{"origen": "A", "tipo": "hasta_salida", "distancia_real": 60}]))
            ev = cr.json()["results"]["sectores"][0]["evacuacion"]
            assert ev["coeficiente"] == "nota4a"
            assert ev["distancia_maxima"] == 62.5  # 50*1.25
            assert ev["recorridos"][0]["distancia_max"] == 62.5
            assert ev["recorridos"][0]["cumple"] is True  # 60 <= 62.5
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_recorrido_excede_no_cumple(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_recorrido_ko")
        try:
            cr = _put_compute(admin_session, sid,
                              _rsciei_base(recorridos=[{"origen": "A", "tipo": "hasta_salida", "distancia_real": 80}]))
            res = cr.json()["results"]
            sec = res["sectores"][0]
            ev = sec["evacuacion"]
            assert ev["recorridos"][0]["cumple"] is False
            assert sec["estado"] == "no_cumple"
            # observacion tipo error
            has_err = any(o.get("tipo") == "error" for o in sec["observaciones"])
            assert has_err
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_nota5_solo_bajo_nivel1(self, admin_session, project_id):
        # nivel bajo 1: qsi=100 (Qs=100) => nivel 1 BAJO. Nota 5 aplica.
        sid = _create_study(admin_session, project_id, "TEST_nota5_ok")
        try:
            data = _rsciei_base(evac_coef="nota5", recorridos=[{"origen": "A", "tipo": "hasta_salida", "distancia_real": 80}])
            data["dependencias"][0]["qsi"] = 100
            cr = _put_compute(admin_session, sid, data)
            sec = cr.json()["results"]["sectores"][0]
            assert sec["nivel_riesgo"]["nivel"] == 1
            ev = sec["evacuacion"]
            assert ev["coeficiente"] == "nota5"
            # varias salidas hasta_salida => 150
            assert ev["distancia_maxima"] == 150.0
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_nota5_ignorada_si_nivel_mayor(self, admin_session, project_id):
        # qsi=500 (Qs=500) => nivel 2. Nota 5 ignorada -> coef="ninguno"
        sid = _create_study(admin_session, project_id, "TEST_nota5_ignore")
        try:
            data = _rsciei_base(evac_coef="nota5", recorridos=[{"origen": "A", "tipo": "hasta_salida", "distancia_real": 30}])
            data["dependencias"][0]["qsi"] = 500
            cr = _put_compute(admin_session, sid, data)
            sec = cr.json()["results"]["sectores"][0]
            assert sec["nivel_riesgo"]["nivel"] == 2
            ev = sec["evacuacion"]
            assert ev["coeficiente"] == "ninguno"
            assert ev["distancia_maxima"] == 50
        finally:
            admin_session.delete(f"{API}/studies/{sid}")


# ---- CTE DB-SI module ----
class TestCteDbsiModule:
    def test_modules_list_contains_cte_operativo(self, admin_session):
        r = admin_session.get(f"{API}/modules/")
        assert r.status_code == 200, r.text
        data = r.json()
        mods = data if isinstance(data, list) else data.get("modules") or data.get("items") or []
        codes = {m.get("code"): m for m in mods}
        assert "CTE" in codes, codes
        assert codes["CTE"].get("status") == "operativo"

    def test_cte_schema(self, admin_session):
        r = admin_session.get(f"{API}/modules/CTE/schema")
        assert r.status_code == 200, r.text
        s = r.json().get("schema", r.json())
        # occupancy_densities and uses
        assert "occupancy_densities" in s
        assert "uses" in s and len(s["uses"]) > 0
        steps = s["steps"]
        ids = [st["id"] for st in steps]
        assert ids == ["edificio", "ocupacion"], ids
        edificio = steps[0]
        assert "fields" in edificio
        field_names = {f["name"] for f in edificio["fields"]}
        for req in ("uso", "superficie_construida", "altura_evacuacion",
                    "num_salidas", "recorrido_max_real", "bajo_rasante"):
            assert req in field_names, req
        assert steps[1].get("type") == "dbsi_ocupacion"

    def test_cte_compute_full_shape(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_cte_full", module="CTE")
        try:
            data = {
                "uso": "Administrativo",
                "superficie_construida": 800,
                "altura_evacuacion": 12,
                "num_salidas": 2,
                "recorrido_max_real": 30,
                "bajo_rasante": False,
                "dependencias": [
                    {"id": "Z1", "nombre": "Oficinas", "superficie": 500, "densidad": 10, "uso_ocupacion": "Administrativo"},
                    {"id": "Z2", "nombre": "Archivo", "superficie": 200, "densidad": 40, "uso_ocupacion": "Almacén"},
                ],
            }
            cr = _put_compute(admin_session, sid, data)
            body = cr.json()
            res = body["results"]
            for k in ("uso", "superficie", "ocupacion", "si1", "si3", "si4", "si6",
                      "tablas", "observaciones", "estado_global"):
                assert k in res, f"missing {k}"
            # ocupacion
            assert res["ocupacion"]["total"] == 50 + 5  # 500/10 + 200/40 = 50+5
            assert len(res["ocupacion"]["filas"]) == 2
            # si1
            for k in ("max_sector", "cumple", "mensaje"):
                assert k in res["si1"]
            # si3
            for k in ("salidas_requeridas", "salidas_proyectadas", "salidas_ok",
                      "recorrido_max_permitido", "recorrido_real", "recorrido_ok",
                      "ancho_calculado", "ancho_minimo"):
                assert k in res["si3"], k
            # si4
            assert isinstance(res["si4"]["instalaciones"], list)
            assert len(res["si4"]["instalaciones"]) >= 5
            for inst in res["si4"]["instalaciones"]:
                assert "nombre" in inst and "obligatorio" in inst
            # si6
            for k in ("estabilidad", "detalle"):
                assert k in res["si6"]
            # report
            report = body.get("report")
            assert report and "sections" in report
            types = {s.get("type") for s in report["sections"]}
            # Expected section types
            for t in ("text", "keyvalue", "ocupacion", "instalaciones", "tablas", "observaciones"):
                assert t in types, f"missing report section type {t}: got {types}"
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_cte_validation_missing_uso(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_cte_no_uso", module="CTE")
        try:
            data = {"superficie_construida": 500, "dependencias": [{"id": "Z1", "nombre": "Z", "superficie": 100, "densidad": 10}]}
            _put_compute(admin_session, sid, data, expect=422)
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_cte_validation_missing_superficie(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_cte_no_sup", module="CTE")
        try:
            data = {"uso": "Administrativo", "superficie_construida": 0,
                    "dependencias": [{"id": "Z1", "nombre": "Z", "superficie": 100, "densidad": 10}]}
            cr = _put_compute(admin_session, sid, data, expect=422)
            msg = str(cr.json()).lower()
            assert "superficie" in msg
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_cte_validation_no_dependencias(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_cte_no_deps", module="CTE")
        try:
            data = {"uso": "Administrativo", "superficie_construida": 500, "dependencias": []}
            cr = _put_compute(admin_session, sid, data, expect=422)
            msg = str(cr.json()).lower()
            assert "zona" in msg or "ocupaci" in msg or "dependencia" in msg
        finally:
            admin_session.delete(f"{API}/studies/{sid}")
