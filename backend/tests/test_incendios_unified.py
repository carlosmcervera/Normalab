"""Backend tests for unified INCENDIOS module (RSCIEI + CTE DB-SI)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://normlab.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@normalab.com", "password": "Admin1234!"}
SEEDED_STUDY_ID = "6a5e8d366baf3a93ee959a97"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/login", json=ADMIN)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


# --- Module registry ---
class TestRegistry:
    def test_modules_list_has_incendios(self, client):
        r = client.get(f"{API}/modules/")
        assert r.status_code == 200
        mods = r.json()
        codes = {m["code"]: m for m in mods}
        assert "INCENDIOS" in codes
        assert codes["INCENDIOS"]["status"] == "operativo"
        assert "Incendios" in codes["INCENDIOS"]["name"] or codes["INCENDIOS"].get("short_name") == "Incendios"
        # RSCIEI + CTE no longer standalone
        assert "RSCIEI" not in codes
        assert "CTE" not in codes
        # placeholders remain
        for p in ("REBT", "RITE", "ACCESS2023"):
            assert p in codes, f"placeholder {p} missing"

    def test_schema_shape(self, client):
        r = client.get(f"{API}/modules/INCENDIOS/schema")
        assert r.status_code == 200
        sch = r.json()
        # Response is wrapped as {meta, schema}
        inner = sch.get("schema", sch)
        assert "rsciei" in inner and "dbsi" in inner
        assert isinstance(inner["rsciei"].get("steps"), list) and len(inner["rsciei"]["steps"]) == 5
        assert isinstance(inner["dbsi"].get("steps"), list) and len(inner["dbsi"]["steps"]) == 2


# --- Compute ---
def _industrial_ambito():
    return {
        "id": "amb-ind-1",
        "nombre": "Nave A",
        "tipo": "industrial",
        "establecimiento": {"actividad": "Taller", "config": "C"},
        "sectores": [
            {"id": "s1", "nombre": "Sector 1", "tipo": "sector",
             "config": "C", "situacion": "sobre_rasante", "num_salidas": 2,
             "fachada_accesible": False, "rociadores": False,
             "altura_evacuacion": 3.0},
        ],
        "dependencias": [
            {"id": "d1", "nombre": "Taller", "planta": "-", "sector_id": "s1",
             "sup_construida": 500.0, "sup_util": 500.0, "densidad": 20,
             "uso_ocupacion": "Industrial",
             "modo": "produccion", "qsi": 400, "ci": 1.2, "ra": 1.0},
        ],
    }


def _edificacion_ambito():
    return {
        "id": "amb-edi-1",
        "nombre": "Oficinas",
        "tipo": "edificacion",
        "uso": "Administrativo",
        "superficie_construida": 300.0,
        "altura_evacuacion": 3.0,
        "num_salidas": 2,
        "recorrido_max_real": 15.0,
        "bajo_rasante": False,
        "dependencias": [
            {"id": "e1", "nombre": "Oficina", "superficie": 100.0, "densidad": 10, "uso_ocupacion": "Administrativo"}
        ],
    }


@pytest.fixture(scope="module")
def study_id(client):
    # Try seeded first
    r = client.get(f"{API}/studies/{SEEDED_STUDY_ID}")
    if r.status_code == 200 and r.json().get("module_code") == "INCENDIOS":
        return SEEDED_STUDY_ID
    # Create one under a project
    pr = client.get(f"{API}/projects/")
    assert pr.status_code == 200
    projects = pr.json()
    if not projects:
        cp = client.post(f"{API}/projects/", json={"nombre": "TEST_PROJ_INC", "cliente": "T"})
        assert cp.status_code in (200, 201), cp.text
        project_id = cp.json()["id"]
    else:
        project_id = projects[0]["id"]
    cs = client.post(
        f"{API}/studies/",
        json={
            "project_id": project_id,
            "module_code": "INCENDIOS",
            "nombre": "TEST_INC_" + uuid.uuid4().hex[:6],
            "data": {"ambitos": [_industrial_ambito(), _edificacion_ambito()]},
        },
    )
    assert cs.status_code in (200, 201), cs.text
    return cs.json()["id"]


class TestCompute:
    def test_compute_mixed(self, client, study_id):
        # Patch data to mixed
        upd = client.put(
            f"{API}/studies/{study_id}",
            json={"data": {"ambitos": [_industrial_ambito(), _edificacion_ambito()]}},
        )
        assert upd.status_code in (200, 204), upd.text
        r = client.post(f"{API}/studies/{study_id}/compute")
        assert r.status_code == 200, r.text
        res = r.json()
        # results wrapped somewhere; support common shapes
        results = res.get("results", res)
        assert "ambitos" in results, results
        assert "estado_global" in results
        assert len(results["ambitos"]) == 2
        types = [a["tipo"] for a in results["ambitos"]]
        assert "industrial" in types and "edificacion" in types
        for a in results["ambitos"]:
            assert "results" in a and isinstance(a["results"], dict)

    def test_report_merged(self, client, study_id):
        # Compute returns { results, report } merged
        client.put(
            f"{API}/studies/{study_id}",
            json={"data": {"ambitos": [_industrial_ambito(), _edificacion_ambito()]}},
        )
        r = client.post(f"{API}/studies/{study_id}/compute")
        assert r.status_code == 200, r.text
        payload = r.json()
        rep = payload.get("report") or payload
        assert rep.get("module_code") == "INCENDIOS"
        sections = rep.get("sections") or []
        types = [s.get("type") for s in sections]
        assert types[0] == "text", f"first section type={types[0]}"
        assert types.count("ambito_header") == 2, f"expected 2 ambito_header, got {types.count('ambito_header')}"

    def test_compute_empty_ambitos_422(self, client, study_id):
        client.put(f"{API}/studies/{study_id}", json={"data": {"ambitos": []}})
        r = client.post(f"{API}/studies/{study_id}/compute")
        assert r.status_code == 422, r.text
        detail = str(r.json())
        assert "ámbito" in detail.lower() or "ambito" in detail.lower()

    def test_compute_invalid_subdata_422(self, client, study_id):
        bad = _industrial_ambito()
        bad["dependencias"] = []  # RSCIEI should reject
        client.put(f"{API}/studies/{study_id}", json={"data": {"ambitos": [bad]}})
        r = client.post(f"{API}/studies/{study_id}/compute")
        assert r.status_code == 422, r.text
        detail = str(r.json())
        assert "Ámbito" in detail or "ámbito" in detail.lower()

    def test_restore_valid_state(self, client, study_id):
        # cleanup - restore valid data so subsequent runs are stable
        client.put(
            f"{API}/studies/{study_id}",
            json={"data": {"ambitos": [_industrial_ambito(), _edificacion_ambito()]}},
        )
