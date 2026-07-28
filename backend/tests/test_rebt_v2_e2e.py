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
    "caida_max_lga": 0.5,
    "caida_max_di": 1.5,
    "caida_max_circuito": 3,
    "caida_max_total_alumbrado": 4.5,
    "caida_max_total_otros": 6.5,
    "cuadro": {
        "id": "root",
        "nombre": "Cuadro general",
        "alim": {"longitud": 15, "caida_max": 1.5, "cosphi": 0.9},
        "simultaneidad": 1,
        "diferencial_general": {"sensibilidad": 300},
        "spd": {"presente": True, "tipo": "T2"},
        "lga": {"presente": True, "longitud": 8, "caida_max": 0.5},
        "nodos": [
            {"id": "l1", "kind": "linea", "nombre": "Motor principal", "tipo": "motor", "potencia": 5000,
             "cosphi": 0.85, "factor_uso": 1, "longitud": 20, "estancia": "Sala máquinas",
             "dif_propio": True, "sensibilidad": 300},
            {"id": "p1", "kind": "puente", "nombre": "Puente tomas", "longitud": 12, "cosphi": 0.9,
             "simultaneidad": 0.8, "sensibilidad": 30, "sublineas": [
                 {"id": "s1", "nombre": "Tomas 1", "tipo": "tomas", "potencia": 2000, "cosphi": 0.9, "factor_uso": 1, "longitud": 10},
                 {"id": "s2", "nombre": "Tomas 2", "tipo": "tomas", "potencia": 2000, "cosphi": 0.9, "factor_uso": 1, "longitud": 12},
             ]},
            {"id": "sub1", "kind": "subcuadro", "board": {
                "id": "b2", "nombre": "Subcuadro planta 1",
                "alim": {"longitud": 25, "caida_max": 1, "cosphi": 0.9}, "simultaneidad": 1,
                "diferencial_general": {"sensibilidad": 300}, "spd": {"presente": False, "tipo": "T2"},
                "lga": {"presente": False},
                "nodos": [
                    {"id": "sc1", "kind": "linea", "nombre": "Bomba", "tipo": "motor", "potencia": 3000,
                     "cosphi": 0.85, "factor_uso": 1, "longitud": 15, "estancia": "",
                     "dif_propio": True, "sensibilidad": 300},
                ],
            }},
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
        arbol = results.get("arbol")
        assert arbol is not None and arbol["es_raiz"] is True
        # New model: 3 nodos (linea, puente, subcuadro), SPD + LGA present
        assert len(arbol["nodos"]) == 3
        kinds = [n["kind"] for n in arbol["nodos"]]
        assert kinds == ["linea", "puente", "subcuadro"]
        assert arbol["spd"]["presente"] is True
        assert arbol["lga"] is not None
        puente = arbol["nodos"][1]
        assert len(puente["sublineas"]) == 2
        sub = arbol["nodos"][2]["board"]
        assert len(sub["nodos"]) == 1

        # Cascading caida acum: LGA < DI; puente feeder > DI; sublines > puente; sub board feed > DI; sub circ > sub feed
        lga_acc = arbol["lga"]["caida_acum_pct"]
        root_feed = arbol["alimentacion"]["caida_acum_pct"]
        assert root_feed > lga_acc
        assert puente["caida_acum_pct"] > root_feed
        assert puente["sublineas"][0]["caida_acum_pct"] > puente["caida_acum_pct"]
        sub_feed = sub["alimentacion"]["caida_acum_pct"]
        assert sub_feed > root_feed
        assert sub["nodos"][0]["caida_acum_pct"] > sub_feed

        # cuadro_potencias: motor + 2 sublines + bomba = 4
        assert len(results["cuadro_potencias"]) == 4
        lineas = results["lineas"]
        tipos = [l["tipo"] for l in lineas]
        assert tipos.count("alimentacion") == 3  # LGA + DI + subcuadro feed
        assert tipos.count("puente") == 1
        assert tipos.count("circuito") == 4       # motor + 2 sublines + bomba
        assert len(lineas) == 8

        assert len(results["resumen"]) == 4
        labels = [m["label"] for m in results["resumen"]]
        assert any("Potencia instalada" in l for l in labels)
        assert any("IGA" in l for l in labels)

        rr = client.get(f"{API}/studies/{study}", timeout=15)
        assert rr.status_code == 200
        assert rr.json().get("results") is not None

    def test_02_compute_rejects_empty_board(self, client, project):
        r = client.post(f"{API}/studies", json={
            "project_id": project["id"], "module_code": "REBT", "name": "REBT empty"
        }, timeout=15)
        sid = r.json().get("id") or r.json().get("_id")
        client.put(f"{API}/studies/{sid}", json={"data": {"suministro": "trifasica", "cuadro": {"id": "r", "nodos": []}}}, timeout=15)
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
