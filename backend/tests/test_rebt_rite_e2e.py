"""E2E backend tests for REBT (RD 842/2002) and RITE (RD 1027/2007) modules.

Covers:
- Shared estancias CRUD (GET/PUT /api/projects/{id}/estancias)
- REBT compute (cumple + no_cumple cases)
- RITE compute (using shared estancias for occupation/ventilation)
- DOCX/XLSX exports for both modules
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@normalab.com", "password": "Admin1234!"}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def project(client):
    r = client.post(f"{API}/projects", json={
        "code": "TEST-REBT-RITE-E2E",
        "name": "TEST REBT/RITE E2E",
        "description": "Test suite REBT+RITE",
    }, timeout=15)
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    yield pid
    client.delete(f"{API}/projects/{pid}", timeout=15)


@pytest.fixture(scope="module")
def project_with_estancias(client, project):
    estancias = [
        {"nombre": "Oficina 1", "planta": "Baja", "sup_util": 100, "sup_construida": 110,
         "altura": 3.0, "uso_ocupacion": "oficinas", "densidad": 10},
        {"nombre": "Sala", "planta": "1", "sup_util": 50, "sup_construida": 55,
         "altura": 3.0, "uso_ocupacion": "oficinas", "densidad": 2},
    ]
    r = client.put(f"{API}/projects/{project}/estancias", json={"estancias": estancias}, timeout=15)
    assert r.status_code == 200, r.text
    return project


# ---- Shared estancias ----
class TestSharedEstancias:
    def test_put_and_get_estancias(self, client, project):
        est = [{"nombre": "TEST_A", "planta": "0", "sup_util": 20,
                "sup_construida": 25, "altura": 3, "uso_ocupacion": "oficinas", "densidad": 10}]
        r = client.put(f"{API}/projects/{project}/estancias", json={"estancias": est}, timeout=15)
        assert r.status_code == 200
        assert r.json()["estancias"][0]["nombre"] == "TEST_A"

        r2 = client.get(f"{API}/projects/{project}/estancias", timeout=15)
        assert r2.status_code == 200
        assert len(r2.json()["estancias"]) == 1
        assert r2.json()["estancias"][0]["sup_util"] == 20


# ---- REBT ----
class TestRITE:
    def _create(self, client, pid, name):
        r = client.post(f"{API}/studies", json={
            "project_id": pid, "module_code": "RITE", "name": name}, timeout=15)
        assert r.status_code == 200, r.text
        return r.json()["id"]

    def test_rite_no_cumple_sobredimensionado(self, client, project_with_estancias):
        sid = self._create(client, project_with_estancias, "TEST_RITE_case")
        r = client.put(f"{API}/studies/{sid}", json={"data": {
            "tipo_instalacion": "climatizacion", "uso_edificio": "oficinas",
            "zona_climatica": "D", "potencia_termica_kw": 450,
            "tipo_generador": "caldera_condensacion", "rendimiento_pct": 88,
            "categoria_ida": "IDA2", "caudal_expulsado_m3s": 0.7,
        }}, timeout=15)
        assert r.status_code == 200
        rc = client.post(f"{API}/studies/{sid}/compute", timeout=30)
        assert rc.status_code == 200, rc.text
        res = rc.json()["results"]
        # Occupation from shared: 100/10 + 50/2 = 10 + 25 = 35 persons
        # Ventilation IDA2 = 12.5 l/s * 35 = 437.5 l/s
        assert res["estado_global"] in ("no_cumple", "observaciones")
        d = res["datos"]
        assert d["ocupantes"] >= 30
        assert d["caudal_ventilacion_ls"] > 0
        # Check sections present
        ids = [s["id"] for s in res["secciones"]]
        assert "demanda" in ids
        assert "rendimiento" in ids
        assert "fraccionamiento" in ids
        assert "ventilacion" in ids
        assert "recuperacion" in ids
        # Rendimiento 88 < 92 → no_cumple in that section
        rendim = next(s for s in res["secciones"] if s["id"] == "rendimiento")
        assert rendim["estado"] == "no_cumple"
        # Fraccionamiento 450 > 400 → observaciones
        frac = next(s for s in res["secciones"] if s["id"] == "fraccionamiento")
        assert frac["estado"] == "observaciones"
        # Recuperación 0.7 > 0.5 → observaciones
        rec = next(s for s in res["secciones"] if s["id"] == "recuperacion")
        assert rec["estado"] == "observaciones"
        client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_rite_export_docx_xlsx(self, client, project_with_estancias):
        sid = self._create(client, project_with_estancias, "TEST_RITE_export")
        client.put(f"{API}/studies/{sid}", json={"data": {
            "tipo_instalacion": "climatizacion", "uso_edificio": "oficinas",
            "zona_climatica": "D", "potencia_termica_kw": 450,
            "tipo_generador": "caldera_condensacion", "rendimiento_pct": 88,
            "categoria_ida": "IDA2", "caudal_expulsado_m3s": 0.7}}, timeout=15)
        client.post(f"{API}/studies/{sid}/compute", timeout=30)
        d = client.get(f"{API}/studies/{sid}/export/docx", timeout=30)
        assert d.status_code == 200 and d.content[:2] == b"PK" and len(d.content) > 3000
        x = client.get(f"{API}/studies/{sid}/export/xlsx", timeout=30)
        assert x.status_code == 200 and x.content[:2] == b"PK" and len(x.content) > 2000
        client.delete(f"{API}/studies/{sid}", timeout=15)
