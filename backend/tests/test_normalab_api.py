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
        assert "config_types" in s and len(s["config_types"]) == 5, \
            f"Expected 5 config_types (AV, AH, B, C, D) — iteration 4 removed 'E'. Got: {[c['value'] for c in s['config_types']]}"
        for ct in s["config_types"]:
            assert "value" in ct and "label" in ct and "image" in ct
            assert ct["image"].startswith("http")
        assert {c["value"] for c in s["config_types"]} == {"AV", "AH", "B", "C", "D"}, \
            "Config type 'E' must be removed per RSCIEI 2025 guide"
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

    def test_requisitos_schema_new_fields(self, admin_session):
        """Iteración 3: schema RSCIEI paso 1 incluye nuevos campos para requisitos."""
        r = admin_session.get(f"{API}/modules/RSCIEI/schema")
        assert r.status_code == 200
        s = r.json().get("schema", r.json())
        step1 = next(st for st in s["steps"] if st["id"] == "establecimiento")
        fmap = {f["name"]: f for f in step1["fields"]}
        # situacion select
        assert "situacion" in fmap and fmap["situacion"]["type"] == "select"
        vals = {o["value"] for o in fmap["situacion"]["options"]}
        assert {"sobre_rasante", "bajo_rasante"}.issubset(vals)
        # altura_evacuacion number
        assert fmap["altura_evacuacion"]["type"] == "number"
        # superficie_establecimiento number
        assert fmap["superficie_establecimiento"]["type"] == "number"
        # cubierta_ligera boolean
        assert fmap["cubierta_ligera"]["type"] == "boolean"

    def _make_and_compute(self, admin_session, project_id, data, name="TEST req"):
        r = admin_session.post(f"{API}/studies", json={
            "project_id": project_id, "module_code": "RSCIEI", "name": name})
        sid = r.json()["id"]
        admin_session.put(f"{API}/studies/{sid}", json={"data": data})
        cr = admin_session.post(f"{API}/studies/{sid}/compute")
        assert cr.status_code == 200, cr.text
        results = cr.json()["results"]
        admin_session.delete(f"{API}/studies/{sid}")
        return results

    def test_requisitos_tipoB_alto_2000(self, admin_session, project_id):
        """Tipo B, sobre rasante, riesgo ALTO, 2000 m² producción -> R180, EI240,
        instalaciones obligatorias (detección, BIE, rociadores, humos)."""
        data = {
            "actividad": "Nave B alto",
            "tipo_configuracion": "B",
            "superficie_sector": 2000,
            "superficie_establecimiento": 2000,
            "situacion": "sobre_rasante",
            "altura_evacuacion": 8,
            "cubierta_ligera": True,
            "ra": 1.5,
            "zonas": [
                {"descripcion": "Prod alto", "modo": "produccion",
                 "qsi": 3000, "ci": 1.3, "superficie": 2000},
            ],
        }
        res = self._make_and_compute(admin_session, project_id, data, "TEST req B alto")
        req = res["requisitos"]
        assert res["nivel_riesgo"]["categoria"] == "ALTO"
        assert req["modo_predominante"] == "produccion"
        assert req["estabilidad"]["valor"] == "R 120"  # Iteration 4 correction: B sobre rasante ALTO -> R 120 (was R 180)
        assert req["delimitadores"]["valor"] == "EI 240"
        assert req["cubierta_ligera"] and req["cubierta_ligera"]["valor"] == "R 15"
        # instalaciones
        by_name = {i["nombre"]: i for i in req["instalaciones"]}
        for always in ["Extintores portátiles", "Sistema manual de alarma (pulsadores)",
                       "Alumbrado de emergencia", "Señalización de medios manuales"]:
            assert by_name[always]["obligatorio"] is True, f"{always} debe ser obligatoria"
        assert by_name["Detección automática de incendio"]["obligatorio"] is True
        assert by_name["Bocas de incendio equipadas (BIE)"]["obligatorio"] is True
        assert by_name["Rociadores automáticos de agua"]["obligatorio"] is True
        assert by_name["Control de humos y calor"]["obligatorio"] is True
        # columna seca: altura 8 < 15 => no obligatoria
        assert by_name["Columna seca"]["obligatorio"] is False

    def test_requisitos_tipoC_bajo(self, admin_session, project_id):
        """Tipo C, sobre rasante, riesgo BAJO -> R 90, EI 120."""
        data = {
            "actividad": "Nave C bajo",
            "tipo_configuracion": "C",
            "superficie_sector": 500,
            "situacion": "sobre_rasante",
            "altura_evacuacion": 4,
            "ra": 1.0,
            "zonas": [
                {"descripcion": "Prod bajo", "modo": "produccion",
                 "qsi": 200, "ci": 1.0, "superficie": 500},
            ],
        }
        res = self._make_and_compute(admin_session, project_id, data, "TEST req C bajo")
        req = res["requisitos"]
        assert res["nivel_riesgo"]["categoria"] == "BAJO"
        assert req["estabilidad"]["valor"] == "R 30"  # C sobre rasante BAJO -> R 30 per Tabla 2.5.1
        assert req["delimitadores"]["valor"] == "EI 120"
        by_name = {i["nombre"]: i for i in req["instalaciones"]}
        # Riesgo BAJO nivel 1 => detección no exigible por regla any-BAJO-1
        # Para tipo B/C con BAJO existen umbrales altos; comprobamos que rociadores no obligatorios
        assert by_name["Rociadores automáticos de agua"]["obligatorio"] is False
        # columna seca no obligatoria (altura 4)
        assert by_name["Columna seca"]["obligatorio"] is False

    def test_requisitos_tipoA_alto_no_admitido(self, admin_session, project_id):
        """Tipo AV riesgo ALTO -> estabilidad NO ADMITIDO."""
        data = {
            "actividad": "AV alto",
            "tipo_configuracion": "AV",
            "superficie_sector": 300,
            "situacion": "sobre_rasante",
            "altura_evacuacion": 20,
            "ra": 2.0,
            "zonas": [
                {"descripcion": "Prod muy alto", "modo": "produccion",
                 "qsi": 8000, "ci": 1.5, "superficie": 300},
            ],
        }
        res = self._make_and_compute(admin_session, project_id, data, "TEST req AV alto")
        req = res["requisitos"]
        assert res["nivel_riesgo"]["categoria"] == "ALTO"
        assert req["estabilidad"]["valor"] == "NO ADMITIDO"
        by_name = {i["nombre"]: i for i in req["instalaciones"]}
        # Columna seca obligatoria (altura 20 >= 15)
        assert by_name["Columna seca"]["obligatorio"] is True

    def test_requisitos_persist_in_version(self, admin_session, project_id):
        """El snapshot de versión debe incluir results.requisitos."""
        r = admin_session.post(f"{API}/studies", json={
            "project_id": project_id, "module_code": "RSCIEI", "name": "TEST req version"})
        sid = r.json()["id"]
        data = {
            "actividad": "Nave ver",
            "tipo_configuracion": "B",
            "superficie_sector": 1500,
            "situacion": "sobre_rasante",
            "ra": 1.2,
            "zonas": [{"descripcion": "P", "modo": "produccion",
                       "qsi": 1500, "ci": 1.1, "superficie": 1500}],
        }
        admin_session.put(f"{API}/studies/{sid}", json={"data": data})
        admin_session.post(f"{API}/studies/{sid}/compute")
        vr = admin_session.post(f"{API}/studies/{sid}/version", json={"note": "TEST req"})
        assert vr.status_code == 200
        v = vr.json()["version"]
        gr = admin_session.get(f"{API}/studies/{sid}/versions/{v}")
        assert gr.status_code == 200
        snap = gr.json()
        # snapshot may embed results at top-level or under results field
        results = snap.get("results") or snap.get("snapshot", {}).get("results")
        assert results is not None, f"No results in snapshot: keys={list(snap.keys())}"
        assert "requisitos" in results
        assert "instalaciones" in results["requisitos"]
        admin_session.delete(f"{API}/studies/{sid}")

    # ---------- Iteration 4 corrections ----------
    def test_iter4_estabilidad_B_sobre_alto_R120(self, admin_session, project_id):
        """B sobre rasante riesgo ALTO -> R 120 (corregido en iter4)."""
        data = {"actividad": "B alto", "tipo_configuracion": "B",
                "superficie_sector": 1000, "situacion": "sobre_rasante",
                "altura_evacuacion": 8, "ra": 1.5,
                "zonas": [{"descripcion": "P", "modo": "produccion",
                           "qsi": 5000, "ci": 1.5, "superficie": 1000}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 B alto")
        assert res["nivel_riesgo"]["categoria"] == "ALTO"
        assert res["requisitos"]["estabilidad"]["valor"] == "R 120"

    def test_iter4_estabilidad_AV_sobre_medio_R120(self, admin_session, project_id):
        data = {"actividad": "AV medio", "tipo_configuracion": "AV",
                "superficie_sector": 500, "situacion": "sobre_rasante",
                "altura_evacuacion": 6, "ra": 1.0,
                "zonas": [{"descripcion": "P", "modo": "produccion",
                           "qsi": 1500, "ci": 1.2, "superficie": 500}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 AV medio")
        assert res["nivel_riesgo"]["categoria"] == "MEDIO"
        assert res["requisitos"]["estabilidad"]["valor"] == "R 120"

    def test_iter4_estabilidad_C_bajo_rasante_bajo_R60(self, admin_session, project_id):
        data = {"actividad": "C bajo", "tipo_configuracion": "C",
                "superficie_sector": 500, "situacion": "bajo_rasante",
                "altura_evacuacion": 3, "ra": 1.0,
                "zonas": [{"descripcion": "P", "modo": "produccion",
                           "qsi": 200, "ci": 1.0, "superficie": 500}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 C bajo bajo")
        assert res["nivel_riesgo"]["categoria"] == "BAJO"
        assert res["requisitos"]["estabilidad"]["valor"] == "R 60"

    def test_iter4_sectorizacion_bajo_rasante_divide_por_2(self, admin_session, project_id):
        """C nivel 2 bajo rasante => max_admisible_base = 12000/2 = 6000."""
        # Force nivel 2 (Qs entre 425 y 850)
        data = {"actividad": "C bajo", "tipo_configuracion": "C",
                "superficie_sector": 800, "situacion": "bajo_rasante",
                "altura_evacuacion": 3, "ra": 1.0,
                "zonas": [{"descripcion": "P", "modo": "produccion",
                           "qsi": 700, "ci": 1.0, "superficie": 800}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 C bajo nivel2")
        assert res["nivel_riesgo"]["nivel"] == 2
        sec = res["sectorizacion"]
        assert sec["max_admisible_base"] == 6000, f"expected 6000 (12000/2), got {sec['max_admisible_base']}"

    def test_iter4_max_surface_AV_nivel7_admitido_1500(self, admin_session, project_id):
        """AV nivel 7 admite 1500 m² (antes NO ADMITIDO)."""
        data = {"actividad": "AV nivel7", "tipo_configuracion": "AV",
                "superficie_sector": 300, "situacion": "sobre_rasante",
                "altura_evacuacion": 8, "ra": 2.0,
                "zonas": [{"descripcion": "Alm", "modo": "almacenamiento",
                           "qvi": 1000, "ci": 1.5, "hi": 4, "superficie": 300}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 AV nivel7")
        assert res["nivel_riesgo"]["nivel"] == 7, f"nivel={res['nivel_riesgo']['nivel']}"
        sec = res["sectorizacion"]
        # NO ADMITIDO would set state 'no_admitido' with base=None. Ahora debe estar admitido con 1500
        assert sec["estado"] != "no_admitido", "AV nivel 7 debe estar admitido en iter4"
        assert sec["max_admisible_base"] == 1500, f"expected 1500, got {sec['max_admisible_base']}"

    def test_iter4_max_surface_AH_nivel7_no_admitido(self, admin_session, project_id):
        data = {"actividad": "AH nivel7", "tipo_configuracion": "AH",
                "superficie_sector": 300, "situacion": "sobre_rasante",
                "altura_evacuacion": 6, "ra": 2.0,
                "zonas": [{"descripcion": "Alm", "modo": "almacenamiento",
                           "qvi": 1000, "ci": 1.5, "hi": 4, "superficie": 300}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 AH nivel7")
        assert res["nivel_riesgo"]["nivel"] == 7
        assert res["sectorizacion"]["estado"] == "no_admitido"

    def test_iter4_hidrantes_thresholds(self, admin_session, project_id):
        """Hidrantes: tipo B/C/AH riesgo ALTO obligatorios si >=2500, MEDIO si >=3500."""
        # B, riesgo ALTO, superficie 2500 => obligatorio
        data = {"actividad": "B alto 2500", "tipo_configuracion": "B",
                "superficie_sector": 2500, "situacion": "sobre_rasante",
                "altura_evacuacion": 8, "superficie_establecimiento": 2500, "ra": 1.5,
                "zonas": [{"descripcion": "P", "modo": "produccion",
                           "qsi": 5000, "ci": 1.5, "superficie": 2500}]}
        res = self._make_and_compute(admin_session, project_id, data, "TEST iter4 hid B alto 2500")
        assert res["nivel_riesgo"]["categoria"] == "ALTO"
        hid = next(i for i in res["requisitos"]["instalaciones"] if i["nombre"] == "Hidrantes exteriores")
        assert hid["obligatorio"] is True, f"hidrantes B ALTO 2500 debería ser obligatorio: {hid['detalle']}"

        # B, riesgo ALTO, superficie 2000 => NO obligatorio
        data2 = dict(data); data2["superficie_sector"] = 2000; data2["superficie_establecimiento"] = 2000
        data2["zonas"] = [{"descripcion": "P", "modo": "produccion", "qsi": 5000, "ci": 1.5, "superficie": 2000}]
        res2 = self._make_and_compute(admin_session, project_id, data2, "TEST iter4 hid B alto 2000")
        assert res2["nivel_riesgo"]["categoria"] == "ALTO"
        hid2 = next(i for i in res2["requisitos"]["instalaciones"] if i["nombre"] == "Hidrantes exteriores")
        assert hid2["obligatorio"] is False, "hidrantes B ALTO 2000 NO debe ser obligatorio (<2500)"

    def test_iter4_deteccion_bajo_nivel1_no_exige_todas_config(self, admin_session, project_id):
        """riesgo BAJO nivel 1 => detección no obligatoria para todas las configuraciones."""
        for cfg in ["AV", "AH", "B", "C"]:
            data = {"actividad": f"{cfg} n1", "tipo_configuracion": cfg,
                    "superficie_sector": 200, "situacion": "sobre_rasante",
                    "altura_evacuacion": 4, "ra": 1.0,
                    "zonas": [{"descripcion": "P", "modo": "produccion",
                               "qsi": 200, "ci": 1.0, "superficie": 200}]}
            res = self._make_and_compute(admin_session, project_id, data, f"TEST iter4 det {cfg}")
            assert res["nivel_riesgo"]["nivel"] == 1
            det = next(i for i in res["requisitos"]["instalaciones"] if i["nombre"] == "Detección automática de incendio")
            assert det["obligatorio"] is False, f"Detección {cfg} BAJO nivel1 no debería ser obligatoria"

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
