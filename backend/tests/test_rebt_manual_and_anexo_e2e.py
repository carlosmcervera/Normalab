"""E2E tests for REBT iteration 31: manual magnetotérmico selection + anexo justificativo de cálculo.

Verifies:
 - Manual magnetothermic override on final circuit (magneto_manual too high → seleccion_manual=True,
   protege_cable=False, warning observation with recommendation).
 - Empty/absent magneto_manual → seleccion_manual=False and auto is used (magneto == magneto_auto).
 - Differential validation: diferencial_ok=True when sensibilidad<=30mA, False when 300mA, with note.
 - Report /api/studies/{id}/informe contains section type 'rebt_anexo_calculo' titled
   '8. Anexo justificativo de cálculo por circuito (ITC-BT-22)' with 5 pasos per bloque
   (Ib, Iz, caída, sobrecarga, cortocircuito).
 - DOCX export contains the anexo texts ('Corriente de proyecto', 'Protección frente a sobrecargas',
   'Protección frente a cortocircuitos').
 - Existing seeded study 6a685484405c68bf00035174 also exposes the anexo section.
"""
import io
import os
import uuid
import zipfile

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://normlab.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PASSWORD = "Admin1234!"
SEED_STUDY = "6a685484405c68bf00035174"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token") or r.json().get("token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def project(client):
    code = f"TEST-REBTMAN-{uuid.uuid4().hex[:6].upper()}"
    r = client.post(f"{API}/projects", json={"code": code, "name": "TEST REBT MAN", "client": "TEST"}, timeout=20)
    assert r.status_code in (200, 201), r.text
    pid = r.json().get("id") or r.json().get("_id")
    yield pid
    client.delete(f"{API}/projects/{pid}", timeout=15)


def _make_study(client, pid):
    r = client.post(f"{API}/studies", json={"project_id": pid, "module_code": "REBT", "name": "REBT MAN"}, timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json().get("id") or r.json().get("_id")


def _put_and_compute(client, sid, data):
    r = client.put(f"{API}/studies/{sid}", json={"data": data}, timeout=20)
    assert r.status_code == 200, r.text
    r = client.post(f"{API}/studies/{sid}/compute", timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _base_data(magneto_manual=None, sensibilidad=30):
    return {
        "suministro": "monofasica", "material": "Cu", "tipo_instalacion": "industrial",
        "aislamiento": "PVC", "curva": "C", "poder_corte_ka": 10, "icc_origen_a": 10000,
        "caida_max_lga": 0.5, "caida_max_di": 1.5, "caida_max_circuito": 3,
        "caida_max_total_alumbrado": 4.5, "caida_max_total_otros": 6.5,
        "cuadro": {
            "id": "root", "nombre": "Cuadro general",
            "alim": {"longitud": 10, "caida_max": 1.5, "cosphi": 0.9},
            "simultaneidad": 1,
            "diferencial_general": {"sensibilidad": 300},
            "spd": {"presente": True, "tipo": "T2"},
            "lga": {"presente": False},
            "nodos": [
                {"id": "l_alu", "kind": "linea", "nombre": "Alumbrado sala",
                 "tipo": "alumbrado", "potencia": 800, "cosphi": 1.0, "factor_uso": 1,
                 "longitud": 15, "dif_propio": True, "sensibilidad": sensibilidad,
                 "magneto_manual": magneto_manual},
            ],
        },
    }


class TestManualMagneto:
    def test_01_manual_high_breaks_protection(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _base_data(magneto_manual=63))
            lineas = res["results"]["lineas"]
            circuit = [l for l in lineas if l.get("tipo") == "circuito"]
            assert circuit, f"no circuit line: {lineas}"
            l = circuit[0]
            assert l["magneto"] == 63, l
            assert l.get("magneto_auto") is not None and l["magneto_auto"] < 63, l
            assert l.get("seleccion_manual") is True
            assert l.get("protege_cable") is False
            # A warning observation must recommend the auto calibre
            obs_texts = [o.get("texto", "") for o in res["results"].get("observaciones", []) if o.get("tipo") == "warning"]
            assert any("Recomendado" in t or "recomendado" in t.lower() or f"{l['magneto_auto']} A" in t for t in obs_texts), obs_texts
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_02_manual_absent_uses_auto(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _base_data(magneto_manual=None))
            circuit = [l for l in res["results"]["lineas"] if l.get("tipo") == "circuito"][0]
            assert circuit.get("seleccion_manual") is False
            assert circuit["magneto"] == circuit["magneto_auto"]
            assert circuit.get("magneto_manual") in (None, 0)
            assert circuit.get("protege_cable") is True
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_03_diferencial_ok_flags(self, client, project):
        sid = _make_study(client, project)
        try:
            # Sensibilidad 30 → diferencial_ok True
            res30 = _put_and_compute(client, sid, _base_data(sensibilidad=30))
            c30 = [l for l in res30["results"]["lineas"] if l.get("tipo") == "circuito"][0]
            assert c30.get("diferencial_ok") is True
            assert isinstance(c30.get("diferencial_nota"), str) and c30["diferencial_nota"]
            # Sensibilidad 300 → diferencial_ok False
            res300 = _put_and_compute(client, sid, _base_data(sensibilidad=300))
            c300 = [l for l in res300["results"]["lineas"] if l.get("tipo") == "circuito"][0]
            assert c300.get("diferencial_ok") is False
            assert "30 mA" in (c300.get("diferencial_nota") or "")
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_04_line_has_id_for_frontend_editing(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _base_data())
            circuit = [l for l in res["results"]["lineas"] if l.get("tipo") == "circuito"][0]
            assert circuit.get("id") == "l_alu"
            assert circuit.get("editable") is True
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)


class TestAnexoCalculo:
    def test_10_report_has_anexo_section(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _base_data())
            report = res.get("report") or {}
            secs = report.get("sections") or []
            anexo = [s for s in secs if s.get("type") == "rebt_anexo_calculo"]
            assert anexo, f"missing rebt_anexo_calculo, types={[s.get('type') for s in secs]}"
            s = anexo[0]
            assert "8." in s.get("title", ""), s.get("title")
            assert "Anexo" in s.get("title", "")
            items = s.get("items", [])
            assert items, "anexo empty"
            for b in items:
                assert "circuito" in b and "pasos" in b
                pasos = b["pasos"]
                assert len(pasos) == 5, f"expected 5 pasos, got {len(pasos)}"
                temas = " | ".join(p.get("tema", "") for p in pasos)
                assert "Ib" in temas
                assert "Iz" in temas
                assert "Caída" in temas or "caída" in temas.lower()
                assert "sobrecargas" in temas.lower()
                assert "cortocircuitos" in temas.lower()
                for p in pasos:
                    for k in ("tema", "formula", "valor", "referencia"):
                        assert p.get(k), f"paso missing {k}: {p}"
                    assert "ITC-BT" in p["referencia"]
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_11_seed_study_report_has_anexo(self, client):
        # Ensure seed study (used by frontend tests) has the anexo section too
        r = client.post(f"{API}/studies/{SEED_STUDY}/compute", timeout=30)
        assert r.status_code == 200, r.text
        secs = (r.json().get("report") or {}).get("sections") or []
        anexo = [s for s in secs if s.get("type") == "rebt_anexo_calculo"]
        assert anexo and anexo[0].get("items"), f"seed study missing anexo; types={[s.get('type') for s in secs]}"

    def test_12_docx_export_contains_anexo_texts(self, client, project):
        sid = _make_study(client, project)
        try:
            _put_and_compute(client, sid, _base_data())
            r = client.get(f"{API}/studies/{sid}/export/docx", timeout=60)
            assert r.status_code == 200, r.text
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            for token in ("Corriente de proyecto", "Protección frente a sobrecargas",
                          "Protección frente a cortocircuitos", "Anexo"):
                assert token in xml, f"missing '{token}' in DOCX"
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)
