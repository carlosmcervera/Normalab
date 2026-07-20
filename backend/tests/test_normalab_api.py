"""Backend tests for NormaLab MVP.

Covers: auth (login/register/me), modules registry+schema, projects CRUD,
studies create + placeholder-block, RSCIEI compute, validations,
versioning (create + list), persistence via PUT.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://normlab.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PASSWORD = "Admin1234!"


@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    # Cookies should be httpOnly
    assert "access_token" in s.cookies, "access_token cookie missing"
    assert "refresh_token" in s.cookies, "refresh_token cookie missing"
    return s


# ---------- Auth ----------
class TestAuth:
    def test_health(self):
        r = requests.get(f"{API}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_login_admin_and_me(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"

    def test_login_invalid_credentials(self):
        r = requests.post(f"{API}/auth/login", json={"email": "no@no.com", "password": "wrong"})
        assert r.status_code in (401, 429)
        assert "detail" in r.json()

    def test_register_new_tecnico(self):
        unique = f"TEST_tec_{int(time.time()*1000)}@example.com"
        s = requests.Session()
        r = s.post(f"{API}/auth/register",
                   json={"email": unique, "password": "Passw0rd!", "name": "Test Tec"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == unique.lower()
        assert data["role"] == "tecnico"
        # cookies set
        assert "access_token" in s.cookies
        # /me works
        r2 = s.get(f"{API}/auth/me")
        assert r2.status_code == 200
        assert r2.json()["email"] == unique.lower()


# ---------- Modules ----------
class TestModules:
    def test_list_modules(self, admin_session):
        r = admin_session.get(f"{API}/modules")
        assert r.status_code == 200
        mods = r.json()
        codes = {m["code"]: m for m in mods}
        assert {"RSCIEI", "CTE", "REBT", "RITE"}.issubset(codes.keys())
        # 5 modules total
        assert len(mods) == 5
        assert codes["RSCIEI"]["status"] == "operativo"
        # Other 4 should be placeholders
        for c in codes:
            if c != "RSCIEI":
                assert codes[c]["status"] != "operativo", f"{c} unexpectedly operativo"

    def test_rsciei_schema(self, admin_session):
        r = admin_session.get(f"{API}/modules/RSCIEI/schema")
        assert r.status_code == 200
        payload = r.json()
        s = payload.get("schema", payload)
        assert "steps" in s
        assert len(s["steps"]) >= 2
        step_ids = [st["id"] for st in s["steps"]]
        assert "establecimiento" in step_ids and "zonas" in step_ids
        # New schema pieces (iteration 2)
        assert "config_types" in s and len(s["config_types"]) == 6
        for ct in s["config_types"]:
            assert "value" in ct and "label" in ct and "image" in ct
            assert ct["image"].startswith("http")
        assert {c["value"] for c in s["config_types"]} == {"AV", "AH", "B", "C", "D", "E"}
        assert "ci_table" in s and len(s["ci_table"]) == 7
        for row in s["ci_table"]:
            assert "grado" in row and "ci" in row and isinstance(row["ci"], (int, float))
        assert "activity_catalog" in s and len(s["activity_catalog"]) == 13
        for cat in s["activity_catalog"]:
            assert "category" in cat and "subactivities" in cat and len(cat["subactivities"]) >= 1
            for sub in cat["subactivities"]:
                assert "name" in sub and "modo" in sub and "ci" in sub and "ra" in sub
                assert sub["modo"] in ("produccion", "almacenamiento")
                if sub["modo"] == "produccion":
                    assert "qsi" in sub
                else:
                    assert "qvi" in sub
        assert "activity_types" in s and len(s["activity_types"]) == 13
        # Step 2 must be 'activities' type
        step2 = next(st for st in s["steps"] if st["id"] == "zonas")
        assert step2.get("type") == "activities"
        # Step 1 field types
        step1 = next(st for st in s["steps"] if st["id"] == "establecimiento")
        fmap = {f["name"]: f for f in step1["fields"]}
        assert fmap["actividad"]["type"] == "activity_combobox"
        assert fmap["tipo_configuracion"]["type"] == "config_selector"


# ---------- Projects + Studies + Compute ----------
@pytest.fixture(scope="session")
def project_id(admin_session):
    payload = {"code": f"TEST-{int(time.time())}", "name": "TEST Expediente"}
    r = admin_session.post(f"{API}/projects", json=payload)
    assert r.status_code in (200, 201), r.text
    pid = r.json()["id"]
    # GET back
    r2 = admin_session.get(f"{API}/projects/{pid}")
    assert r2.status_code == 200
    assert r2.json()["code"] == payload["code"]
    return pid


@pytest.fixture(scope="session")
def study_id(admin_session, project_id):
    r = admin_session.post(f"{API}/studies", json={
        "project_id": project_id, "module_code": "RSCIEI", "name": "TEST Estudio RSCIEI"
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


class TestStudiesFlow:
    def test_placeholder_module_blocked(self, admin_session, project_id):
        r = admin_session.post(f"{API}/studies", json={
            "project_id": project_id, "module_code": "CTE", "name": "TEST cte"
        })
        assert r.status_code == 400
        assert "operativo" in r.json()["detail"].lower() or "cte" in r.json()["detail"].lower()

    def test_update_persists_data(self, admin_session, study_id):
        data = {
            "actividad": "Nave test",
            "tipo_configuracion": "B",
            "superficie_sector": 2000,
            "ra": 1.5,
            "fachada_accesible": True,
            "rociadores": True,
            "zonas": [
                {"descripcion": "Prod", "modo": "produccion", "qsi": 1200, "ci": 1.2, "superficie": 1200},
                {"descripcion": "Alm", "modo": "almacenamiento", "qvi": 800, "hi": 3, "ci": 1.0, "superficie": 800},
            ],
        }
        r = admin_session.put(f"{API}/studies/{study_id}", json={"data": data})
        assert r.status_code == 200
        r2 = admin_session.get(f"{API}/studies/{study_id}")
        assert r2.status_code == 200
        got = r2.json()["data"]
        assert got["superficie_sector"] == 2000
        assert len(got["zonas"]) == 2

    def test_compute_multiple_activities_sum(self, admin_session, project_id):
        """Iteración 2: al añadir varias actividades al sector, la carga se suma."""
        r = admin_session.post(f"{API}/studies", json={
            "project_id": project_id, "module_code": "RSCIEI", "name": "TEST multiactividad"
        })
        sid = r.json()["id"]
        # 3 actividades: 2 producción + 1 almacenamiento
        data = {
            "actividad": "Nave multi",
            "tipo_configuracion": "C",
            "superficie_sector": 4000,
            "ra": 1.4,
            "fachada_accesible": False,
            "rociadores": True,
            "zonas": [
                {"descripcion": "Carpintería · producción con depósito intermedio",
                 "modo": "produccion", "qsi": 1700, "ci": 1.2, "superficie": 1500},
                {"descripcion": "Muebles tapizados · fabricación",
                 "modo": "produccion", "qsi": 550, "ci": 1.44, "superficie": 500},
                {"descripcion": "Carpintería · almacenamiento",
                 "modo": "almacenamiento", "qvi": 3200, "ci": 1.2, "hi": 4, "superficie": 800},
            ],
        }
        pr = admin_session.put(f"{API}/studies/{sid}", json={"data": data})
        assert pr.status_code == 200
        cr = admin_session.post(f"{API}/studies/{sid}/compute")
        assert cr.status_code == 200, cr.text
        res = cr.json()["results"]
        # Numerador esperado
        # 1700*1500*1.2 = 3,060,000
        # 550*500*1.44 = 396,000
        # 3200*1.2*4*800 = 12,288,000
        # Total = 15,744,000
        # qs = 15744000/4000 * 1.4 = 5510.4
        expected_num = 1700 * 1500 * 1.2 + 550 * 500 * 1.44 + 3200 * 1.2 * 4 * 800
        expected_qs = (expected_num / 4000) * 1.4
        assert abs(res["calculo"]["numerador"] - expected_num) < 1.0
        assert abs(res["nivel_riesgo"]["qs_mj"] - expected_qs) < 1.0
        # 3 zones in results
        assert len(res["calculo"]["zonas"]) == 3
        # Level for qs≈5510 => nivel 6 ALTO
        assert res["nivel_riesgo"]["nivel"] == 6
        assert res["nivel_riesgo"]["categoria"] == "ALTO"
        # Sectorization factor: rociadores only -> 2.0; base C nivel 6 = 6000 -> max 12000
        assert res["sectorizacion"]["factor_incremento"] == 2.0
        assert res["sectorizacion"]["max_admisible"] == 12000.0
        admin_session.delete(f"{API}/studies/{sid}")

    def test_compute_storage_uses_hi(self, admin_session, project_id):
        """Iteración 2: modo almacenamiento usa altura hi en el aporte (qvi·Ci·hi·Si)."""
        r = admin_session.post(f"{API}/studies", json={
            "project_id": project_id, "module_code": "RSCIEI", "name": "TEST alm hi"
        })
        sid = r.json()["id"]
        data = {
            "actividad": "Almacén test",
            "tipo_configuracion": "B",
            "superficie_sector": 1000,
            "ra": 1.0,
            "zonas": [
                {"descripcion": "Cartón bobinas",
                 "modo": "almacenamiento", "qvi": 14700, "ci": 1.2, "hi": 5, "superficie": 1000},
            ],
        }
        admin_session.put(f"{API}/studies/{sid}", json={"data": data})
        cr = admin_session.post(f"{API}/studies/{sid}/compute")
        assert cr.status_code == 200
        res = cr.json()["results"]
        # numerador = 14700*1.2*5*1000 = 88,200,000; qs = 88200000/1000 = 88200
        assert abs(res["calculo"]["numerador"] - 88200000.0) < 1.0
        assert abs(res["nivel_riesgo"]["qs_mj"] - 88200.0) < 1.0
        assert res["nivel_riesgo"]["nivel"] == 8
        # Verify the aporte formula
        z = res["calculo"]["zonas"][0]
        assert z["modo"] == "almacenamiento"
        assert z.get("hi") == 5
        admin_session.delete(f"{API}/studies/{sid}")

    def test_compute_rsciei(self, admin_session, study_id):
        r = admin_session.post(f"{API}/studies/{study_id}/compute")
        assert r.status_code == 200, r.text
        res = r.json()["results"]
        assert "calculo" in res and "nivel_riesgo" in res and "sectorizacion" in res
        qs_mj = res["nivel_riesgo"]["qs_mj"]
        # Compute expected: numerador = 1200*1200*1.2 + 800*1.0*3*800 = 1728000 + 1920000 = 3648000
        # qs = 3648000/2000 * 1.5 = 2736.0
        assert abs(qs_mj - 2736.0) < 1.0, f"qs_mj wrong: {qs_mj}"
        # Sectorization: base for B nivel 5 = 5000; factor 1.25*2=2.5 => 12500
        sec = res["sectorizacion"]
        assert sec["factor_incremento"] == 2.5
        assert sec["max_admisible"] == 12500.0
        # Level 5 corresponds to MEDIO per NRI table (1700 < qs<=3400)
        assert res["nivel_riesgo"]["nivel"] == 5
        assert res["nivel_riesgo"]["categoria"] == "MEDIO"

    def test_compute_invalid_no_zonas(self, admin_session, project_id):
        # create another study
        r = admin_session.post(f"{API}/studies", json={
            "project_id": project_id, "module_code": "RSCIEI", "name": "TEST invalid"
        })
        sid = r.json()["id"]
        admin_session.put(f"{API}/studies/{sid}", json={"data": {
            "tipo_configuracion": "B", "superficie_sector": 0, "ra": 1.0, "zonas": []
        }})
        r2 = admin_session.post(f"{API}/studies/{sid}/compute")
        assert r2.status_code == 422
        # Cleanup
        admin_session.delete(f"{API}/studies/{sid}")

    def test_versioning(self, admin_session, study_id):
        r = admin_session.post(f"{API}/studies/{study_id}/version", json={"note": "TEST v1"})
        assert r.status_code == 200, r.text
        v1 = r.json()["version"]
        assert v1 >= 1
        # second version
        r2 = admin_session.post(f"{API}/studies/{study_id}/version", json={"note": "TEST v2"})
        assert r2.status_code == 200
        assert r2.json()["version"] == v1 + 1
        # list
        r3 = admin_session.get(f"{API}/studies/{study_id}/versions")
        assert r3.status_code == 200
        versions = r3.json()
        assert len(versions) >= 2
        # historical fetch
        r4 = admin_session.get(f"{API}/studies/{study_id}/versions/{v1}")
        assert r4.status_code == 200
        assert r4.json()["version"] == v1
