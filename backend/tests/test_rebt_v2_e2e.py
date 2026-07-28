"""E2E tests for REBT v2 module (multi-circuit unifilar with sub-panels).

Flow: login -> create project -> create REBT study -> save data (root board
with a motor + a nested sub-panel with a load) -> POST /compute -> verify
tree, cascading caida_acum, cuadro_potencias, lineas -> export DOCX/XLSX.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://normlab.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PASSWORD = "Admin1234!"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    body = r.json()
    tok = body.get("access_token") or body.get("token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def project(client):
    code = f"TEST-REBTV2-{uuid.uuid4().hex[:6].upper()}"
    r = client.post(f"{API}/projects", json={"code": code, "name": "TEST REBT v2 e2e", "client": "TEST"}, timeout=20)
    assert r.status_code in (200, 201), r.text
    p = r.json()
    pid = p.get("id") or p.get("_id")
    assert pid
    # Optional: give it estancias
    client.put(f"{API}/projects/{pid}/estancias", json={"estancias": [
        {"id": "e1", "nombre": "Sala máquinas", "superficie_util": 20, "superficie_construida": 22, "densidad": 5},
    ]}, timeout=15)
    yield {"id": pid, "code": code}
    client.delete(f"{API}/projects/{pid}", timeout=15)


@pytest.fixture(scope="module")
def study(client, project):
    r = client.post(f"{API}/studies", json={
        "project_id": project["id"], "module_code": "REBT", "name": "REBT v2 e2e"
    }, timeout=20)
    assert r.status_code in (200, 201), r.text
    doc = r.json()
    sid = doc.get("id") or doc.get("_id")
    assert sid
    yield sid
    client.delete(f"{API}/studies/{sid}", timeout=15)


REBT_DATA = {
    "suministro": "trifasica",
    "material": "Cu",
    "tipo_instalacion": "industrial",
    "caida_max_di": 1.5,
    "caida_max_circuito": 3,
    "caida_max_total_alumbrado": 4.5,
    "caida_max_total_otros": 6.5,
    "cuadro": {
        "id": "root",
        "nombre": "Cuadro general",
        "longitud": 15,
        "simultaneidad": 1,
        "cosphi": 0.9,
        "sensibilidad_general": 300,
        "diferenciales": [{"id": "d1", "nombre": "Dif 1", "sensibilidad": 30}],
        "cargas": [
            {"id": "c1", "nombre": "Motor principal", "tipo": "motor", "potencia": 5000,
             "cosphi": 0.85, "factor_uso": 1, "longitud": 20, "estancia": "Sala máquinas",
             "diferencial_id": "d1"},
        ],
        "subcuadros": [
            {
                "id": "sub1", "nombre": "Subcuadro planta 1", "longitud": 25,
                "simultaneidad": 1, "cosphi": 0.9, "sensibilidad_general": 300,
                "diferenciales": [{"id": "sd1", "nombre": "Dif sub", "sensibilidad": 30}],
                "cargas": [
                    {"id": "sc1", "nombre": "Bomba", "tipo": "motor", "potencia": 3000,
                     "cosphi": 0.85, "factor_uso": 1, "longitud": 15, "estancia": "",
                     "diferencial_id": "sd1"},
                ],
                "subcuadros": [],
            }
        ],
    },
}


class TestRebtV2E2E:
    def test_01_save_and_compute(self, client, study):
        r = client.put(f"{API}/studies/{study}", json={"data": REBT_DATA}, timeout=20)
        assert r.status_code == 200, r.text
        r = client.post(f"{API}/studies/{study}/compute", timeout=30)
        assert r.status_code == 200, r.text
        payload = r.json()
        results = payload["results"]
        assert results["estado_global"] in ("cumple", "observaciones", "no_cumple")
        assert results.get("arbol") is not None
        arbol = results["arbol"]
        assert arbol["es_raiz"] is True
        assert len(arbol["cargas"]) == 1
        assert len(arbol["subcuadros"]) == 1
        sub = arbol["subcuadros"][0]
        assert len(sub["cargas"]) == 1

        # Cascading caida acum: sub feeder > root feeder; sub circuit > sub feeder
        root_feed = arbol["alimentacion"]["caida_acum_pct"]
        sub_feed = sub["alimentacion"]["caida_acum_pct"]
        assert sub_feed > root_feed, (root_feed, sub_feed)
        root_circ_acc = arbol["cargas"][0]["caida_acum_pct"]
        sub_circ_acc = sub["cargas"][0]["caida_acum_pct"]
        assert root_circ_acc >= root_feed
        assert sub_circ_acc > sub_feed, (sub_feed, sub_circ_acc)

        # cuadro_potencias present + line count = 2 alimentacion + 2 circuitos
        assert len(results["cuadro_potencias"]) == 2
        lineas = results["lineas"]
        assert len(lineas) == 4
        tipos = [l["tipo"] for l in lineas]
        assert tipos.count("alimentacion") == 2 and tipos.count("circuito") == 2

        # Resumen has 4 metrics
        assert len(results["resumen"]) == 4
        labels = [m["label"] for m in results["resumen"]]
        assert any("Potencia instalada" in l for l in labels)
        assert any("IGA" in l for l in labels)

        # Persistence: GET returns results
        rr = client.get(f"{API}/studies/{study}", timeout=15)
        assert rr.status_code == 200
        assert rr.json().get("results") is not None

    def test_02_compute_rejects_empty_board(self, client, project):
        # A separate study with no loads should return 422
        r = client.post(f"{API}/studies", json={
            "project_id": project["id"], "module_code": "REBT", "name": "REBT empty"
        }, timeout=15)
        sid = r.json().get("id") or r.json().get("_id")
        client.put(f"{API}/studies/{sid}", json={"data": {"suministro": "trifasica", "cuadro": {"id": "r", "cargas": [], "subcuadros": []}}}, timeout=15)
        r = client.post(f"{API}/studies/{sid}/compute", timeout=15)
        assert r.status_code == 422
        client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_03_export_docx(self, client, study):
        r = client.get(f"{API}/studies/{study}/export/docx", timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert len(r.content) > 2000
        assert r.content[:2] == b"PK"

    def test_04_export_xlsx(self, client, study):
        r = client.get(f"{API}/studies/{study}/export/xlsx", timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert len(r.content) > 1500
        assert r.content[:2] == b"PK"
