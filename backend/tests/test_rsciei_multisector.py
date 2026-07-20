"""Iteration 7 tests: RSCIEI multi-sector flow (RD 164/2025).

Covers:
- POST /api/studies/{id}/compute returns multi-sector results (superficies,
  ocupacion, sectores[], resumen_sectores, tablas, observaciones, estado_global).
- Per-sector output shape (calculo.qs_mj, nivel_riesgo, sectorizacion, requisitos
  incl. Hidrante llenado camiones bomberos Tabla 3.3.1, evacuacion).
- 422 validation errors: dep without sector, sector without deps, missing qsi/ci.
- Rmin < Ra warning (dependencia rmin=1.4 en sector con ra=1.0 explícito).
- Tabla 2.1.1 RD 164/2025 values via engine outputs: C n2=12000, AH n7=1500,
  AV n7 = NO ADMITIDO.
- Schema iteration 7: steps establecimiento, superficies, ocupacion, carga_fuego.
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
        "code": f"TEST-MS-{int(time.time())}", "name": "TEST Multi-sector"})
    assert r.status_code in (200, 201), r.text
    pid = r.json()["id"]
    yield pid
    # Cleanup handled per test


def _create_study(admin_session, project_id, name):
    r = admin_session.post(f"{API}/studies", json={
        "project_id": project_id, "module_code": "RSCIEI", "name": name})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _put_and_compute(admin_session, sid, data, expect_status=200):
    r = admin_session.put(f"{API}/studies/{sid}", json={"data": data})
    assert r.status_code == 200, r.text
    cr = admin_session.post(f"{API}/studies/{sid}/compute")
    assert cr.status_code == expect_status, cr.text
    return cr


def _basic_multi_sector_data(*, ra_override=None, rmin=None):
    """2 sectores, 3 dependencias. Sector S1 config B; Sector S2 config C."""
    data = {
        "establecimiento": {"actividad": "Nave industrial mixta", "config": "B"},
        "sectores": [
            {"id": "S1", "nombre": "Sector Producción", "tipo": "sector",
             "config": "B", "situacion": "sobre_rasante", "num_salidas": 2,
             "fachada_accesible": True, "rociadores": False,
             "altura_evacuacion": 6},
            {"id": "S2", "nombre": "Sector Almacén", "tipo": "sector",
             "config": "C", "situacion": "sobre_rasante", "num_salidas": 2,
             "fachada_accesible": False, "rociadores": True,
             "altura_evacuacion": 5},
        ],
        "dependencias": [
            {"id": "D1", "nombre": "Taller producción", "planta": "Planta 0",
             "sup_util": 900, "sup_construida": 1000, "sector_id": "S1",
             "densidad": 20, "uso_ocupacion": "Industrial",
             "modo": "produccion", "qsi": 800, "ci": 1.2, "ra": 1.0},
            {"id": "D2", "nombre": "Oficinas", "planta": "Planta 1",
             "sup_util": 180, "sup_construida": 200, "sector_id": "S1",
             "densidad": 10, "uso_ocupacion": "Administrativo",
             "modo": "produccion", "qsi": 800, "ci": 1.0, "ra": 1.0},
            {"id": "D3", "nombre": "Almacén cartón", "planta": "Planta 0",
             "sup_util": 1400, "sup_construida": 1500, "sector_id": "S2",
             "densidad": 40, "uso_ocupacion": "Almacén",
             "modo": "almacenamiento", "qvi": 3000, "ci": 1.2, "hi": 4,
             "ra": 1.4},
        ],
    }
    if ra_override is not None:
        data["sectores"][0]["ra"] = ra_override
    if rmin is not None:
        data["dependencias"][0]["rmin"] = rmin
    return data


class TestMultiSectorCompute:
    def test_schema_new_steps(self, admin_session):
        r = admin_session.get(f"{API}/modules/RSCIEI/schema")
        assert r.status_code == 200
        s = r.json().get("schema", r.json())
        ids = [st["id"] for st in s["steps"]]
        assert ids == ["establecimiento", "superficies", "ocupacion", "carga_fuego", "evacuacion"], ids
        # types
        smap = {st["id"]: st for st in s["steps"]}
        assert smap["superficies"].get("type") == "superficies"
        assert smap["ocupacion"].get("type") == "ocupacion"
        assert smap["carga_fuego"].get("type") == "carga_fuego"

    def test_compute_multi_sector_result_shape(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_ms basic")
        try:
            cr = _put_and_compute(admin_session, sid, _basic_multi_sector_data())
            res = cr.json()["results"]
            # Top-level keys
            for k in ("establecimiento", "superficies", "ocupacion", "sectores",
                      "resumen_sectores", "tablas", "observaciones", "estado_global"):
                assert k in res, f"missing key: {k}"
            # 2 sectores
            assert isinstance(res["sectores"], list) and len(res["sectores"]) == 2
            # superficies total_construida = 1000+200+1500 = 2700
            assert res["superficies"]["total_construida"] == 2700
            # Sector shape
            sec1 = res["sectores"][0]
            for k in ("calculo", "nivel_riesgo", "sectorizacion", "requisitos", "evacuacion"):
                assert k in sec1, f"sector missing {k}"
            assert "qs_mj" in sec1["calculo"]
            # Hidrante camiones instalación presente (Tabla 3.3.1)
            names = {i["nombre"] for i in sec1["requisitos"]["instalaciones"]}
            assert "Hidrante para llenado de camiones de bomberos" in names, names
            # resumen_sectores same length
            assert len(res["resumen_sectores"]) == 2
            # report also present
            report = cr.json().get("report")
            assert report and any(s["id"] == "superficies" for s in report["sections"])
            assert any(s["id"] == "ocupacion" for s in report["sections"])
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_ocupacion_computed_per_dependency(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_ms ocupacion")
        try:
            cr = _put_and_compute(admin_session, sid, _basic_multi_sector_data())
            res = cr.json()["results"]
            # D1 sup_util=900 / 20 = 45; D2 = 180/10 = 18; D3 = 1400/40=35 -> total 98
            assert res["ocupacion"]["total"] == 45 + 18 + 35, res["ocupacion"]
            assert len(res["ocupacion"]["filas"]) == 3
        finally:
            admin_session.delete(f"{API}/studies/{sid}")


class TestValidations422:
    def test_missing_sector_assignment(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_val no-sector")
        try:
            data = _basic_multi_sector_data()
            data["dependencias"][0]["sector_id"] = None
            r = admin_session.put(f"{API}/studies/{sid}", json={"data": data})
            assert r.status_code == 200
            cr = admin_session.post(f"{API}/studies/{sid}/compute")
            assert cr.status_code == 422, cr.text
            body = cr.json()
            msg = (body.get("detail") or "") if isinstance(body.get("detail"), str) else str(body)
            assert "sector" in msg.lower()
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_sector_without_dependencies(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_val sector-empty")
        try:
            data = _basic_multi_sector_data()
            # Add an extra sector with no deps assigned
            data["sectores"].append({
                "id": "SX", "nombre": "Sector vacío", "tipo": "sector",
                "config": "B", "situacion": "sobre_rasante", "num_salidas": 1,
                "altura_evacuacion": 4})
            r = admin_session.put(f"{API}/studies/{sid}", json={"data": data})
            assert r.status_code == 200
            cr = admin_session.post(f"{API}/studies/{sid}/compute")
            assert cr.status_code == 422, cr.text
            msg = str(cr.json())
            assert "vacío" in msg or "no tiene dependencias" in msg.lower() or "sector" in msg.lower()
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_missing_ci_and_qsi(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_val no-ci-qsi")
        try:
            data = _basic_multi_sector_data()
            data["dependencias"][0]["ci"] = 0
            data["dependencias"][0]["qsi"] = 0
            r = admin_session.put(f"{API}/studies/{sid}", json={"data": data})
            assert r.status_code == 200
            cr = admin_session.post(f"{API}/studies/{sid}/compute")
            assert cr.status_code == 422, cr.text
            msg = str(cr.json()).lower()
            assert "ci" in msg or "qsi" in msg
        finally:
            admin_session.delete(f"{API}/studies/{sid}")


class TestRminWarning:
    def test_rmin_greater_than_sector_ra_yields_warning(self, admin_session, project_id):
        sid = _create_study(admin_session, project_id, "TEST_rmin warn")
        try:
            # Dependencia con rmin=1.4 en sector S1 con ra=1.0 EXPLÍCITO
            data = _basic_multi_sector_data(ra_override=1.0, rmin=1.4)
            cr = _put_and_compute(admin_session, sid, data)
            res = cr.json()["results"]
            # Observaciones debe contener warning sobre Ra < Rmin
            warn_texts = [o["texto"] for o in res["observaciones"] if o.get("tipo") == "warning"]
            assert any("Rmin" in t and "Ra" in t for t in warn_texts), \
                f"expected Rmin warning; got: {warn_texts}"
            # Y estado del sector S1 al menos con observaciones (no cumple si otras fallan)
            s1 = next(s for s in res["sectores"] if s["nombre"] == "Sector Producción")
            assert s1.get("rmin_requerido") == 1.4
            assert s1["calculo"]["ra"] == 1.0
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_rmin_no_warning_when_ra_auto_used(self, admin_session, project_id):
        """Cuando sec.ra vacío el motor usa max(ra dependencias) y no debe avisar."""
        sid = _create_study(admin_session, project_id, "TEST_rmin auto")
        try:
            data = _basic_multi_sector_data(rmin=1.4)
            # Set dependency D1 ra=1.4 so auto Ra >= rmin
            data["dependencias"][0]["ra"] = 1.4
            # No override sec.ra
            cr = _put_and_compute(admin_session, sid, data)
            res = cr.json()["results"]
            warn_texts = [o["texto"] for o in res["observaciones"] if o.get("tipo") == "warning"
                          and "Rmin" in o.get("texto", "")]
            assert warn_texts == [], f"unexpected Rmin warnings: {warn_texts}"
        finally:
            admin_session.delete(f"{API}/studies/{sid}")


class TestTabla211RD164:
    def _run(self, admin_session, project_id, cfg, qsi_target, ci=1.0, name="t211"):
        sid = _create_study(admin_session, project_id, f"TEST_{name}")
        try:
            data = {
                "establecimiento": {"actividad": f"Test {cfg}", "config": cfg},
                "sectores": [
                    {"id": "S1", "nombre": "S", "tipo": "sector",
                     "config": cfg, "situacion": "sobre_rasante",
                     "num_salidas": 2, "altura_evacuacion": 6},
                ],
                "dependencias": [
                    {"id": "D1", "nombre": "Zona", "planta": "0",
                     "sup_util": 400, "sup_construida": 500,
                     "sector_id": "S1", "densidad": 20,
                     "modo": "produccion", "qsi": qsi_target, "ci": ci, "ra": 1.0},
                ],
            }
            cr = _put_and_compute(admin_session, sid, data)
            return cr.json()["results"]
        finally:
            admin_session.delete(f"{API}/studies/{sid}")

    def test_config_C_nivel2_max_12000(self, admin_session, project_id):
        # Qs entre 425 y 850 => nivel 2. qsi*ci=500, sup=500 -> Qs = 500 (nivel 2)
        res = self._run(admin_session, project_id, "C", qsi_target=500, name="C_n2")
        s = res["sectores"][0]
        assert s["nivel_riesgo"]["nivel"] == 2, s["nivel_riesgo"]
        assert s["sectorizacion"]["max_admisible_base"] == 12000

    def test_config_AH_nivel7_1500(self, admin_session, project_id):
        # nivel 7: Qs entre 6800 y 13600. qsi*ci=7000
        res = self._run(admin_session, project_id, "AH", qsi_target=7000, ci=1.0, name="AH_n7")
        s = res["sectores"][0]
        assert s["nivel_riesgo"]["nivel"] == 7, s["nivel_riesgo"]
        assert s["sectorizacion"]["max_admisible_base"] == 1500

    def test_config_AV_nivel7_no_admitido(self, admin_session, project_id):
        res = self._run(admin_session, project_id, "AV", qsi_target=7000, ci=1.0, name="AV_n7")
        s = res["sectores"][0]
        assert s["nivel_riesgo"]["nivel"] == 7
        assert s["sectorizacion"]["estado"] == "no_admitido"
        assert s["sectorizacion"]["max_admisible_base"] is None
        # tabla superficie debe mostrar la fila 6 (nivel 7) resaltada
        tabla_sup = next(t for t in res["tablas"] if t["id"] == "superficie")
        assert isinstance(tabla_sup["highlight_cells"], list)
