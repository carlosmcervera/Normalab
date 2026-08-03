"""E2E tests for iteration 32:
- Board-level iga_manual on root (__root__) and subcuadro flows to alimentacion lines.
- Cortocircuito 'recomendacion' string present when protege_cc=False; None when OK.
- Observations include CC warning with recomendacion.
- DOCX export works for seed REBT study and contains CC section.
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
    code = f"TEST-REBTBRD-{uuid.uuid4().hex[:6].upper()}"
    r = client.post(f"{API}/projects", json={"code": code, "name": "TEST REBT BOARD", "client": "TEST"}, timeout=20)
    assert r.status_code in (200, 201), r.text
    pid = r.json().get("id") or r.json().get("_id")
    yield pid
    try:
        client.delete(f"{API}/projects/{pid}", timeout=15)
    except Exception:
        pass


def _make_study(client, pid):
    r = client.post(f"{API}/studies", json={"project_id": pid, "module_code": "REBT", "name": "REBT BOARD"}, timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json().get("id") or r.json().get("_id")


def _put_and_compute(client, sid, data):
    r = client.put(f"{API}/studies/{sid}", json={"data": data}, timeout=20)
    assert r.status_code == 200, r.text
    r = client.post(f"{API}/studies/{sid}/compute", timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _data(iga_root=None, iga_sub=None, poder_corte_ka=10, long_final=15):
    return {
        "suministro": "trifasica", "material": "Cu", "tipo_instalacion": "industrial",
        "aislamiento": "PVC", "curva": "C", "poder_corte_ka": poder_corte_ka, "icc_origen_a": 10000,
        "caida_max_lga": 0.5, "caida_max_di": 1.5, "caida_max_circuito": 3,
        "caida_max_total_alumbrado": 4.5, "caida_max_total_otros": 6.5,
        "cuadro": {
            "id": "root", "nombre": "Cuadro general",
            "alim": {"longitud": 10, "caida_max": 1.5, "cosphi": 0.9},
            "simultaneidad": 1,
            "diferencial_general": {"sensibilidad": 300},
            "spd": {"presente": True, "tipo": "T2"},
            "lga": {"presente": False},
            "iga_manual": iga_root,
            "nodos": [
                {
                    "id": "sub1", "kind": "subcuadro",
                    "board": {
                        "id": "sub1", "nombre": "Subcuadro planta",
                        "alim": {"longitud": 20, "caida_max": 1.0, "cosphi": 0.9},
                        "simultaneidad": 1,
                        "diferencial_general": {"sensibilidad": 300},
                        "iga_manual": iga_sub,
                        "nodos": [
                            {"id": "lsub", "kind": "linea", "nombre": "Cargas sub",
                             "tipo": "otros", "potencia": 6000, "cosphi": 0.9, "factor_uso": 1,
                             "longitud": long_final, "dif_propio": False},
                        ],
                    },
                },
                {"id": "lroot", "kind": "linea", "nombre": "Tomas",
                 "tipo": "otros", "potencia": 15000, "cosphi": 0.9, "factor_uso": 1,
                 "longitud": long_final, "dif_propio": True, "sensibilidad": 30},
            ],
        },
    }


def _lineas(res):
    return res.get("results", {}).get("lineas") or res.get("lineas") or []


def _obs(res):
    return res.get("results", {}).get("observaciones") or res.get("observaciones") or []


class TestBoardIga:
    def test_01_auto_iga_no_manual(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _data())
            alims = [l for l in _lineas(res) if l.get("tipo") == "alimentacion"]
            assert len(alims) >= 2, f"want >=2 alimentacion lines (root+sub), got {len(alims)}: {[a.get('cuadro') for a in alims]}"
            for a in alims:
                assert a.get("seleccion_manual") is False, a
                assert a.get("magneto") == a.get("magneto_auto"), a
                assert "board_id" in a, a
                assert a.get("editable_board") is True, a
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_02_manual_iga_root_low_triggers_warning(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _data(iga_root=10))
            root_alim = next(l for l in _lineas(res)
                             if l.get("tipo") == "alimentacion" and l.get("board_id") == "__root__")
            assert root_alim["seleccion_manual"] is True
            assert root_alim["magneto"] == 10
            assert root_alim["magneto_manual"] == 10
            assert isinstance(root_alim["magneto_auto"], int)
            assert root_alim["protege_cable"] is False
            warns = [o for o in _obs(res) if o.get("tipo") == "warning"]
            assert any(("IGA" in o.get("texto", "")) and ("Recomendado" in o.get("texto", "")) for o in warns), warns
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)

    def test_03_manual_iga_subcuadro_low_triggers_warning(self, client, project):
        sid = _make_study(client, project)
        try:
            res = _put_and_compute(client, sid, _data(iga_sub=6))
            sub_alim = next(l for l in _lineas(res)
                            if l.get("tipo") == "alimentacion" and l.get("board_id") == "sub1")
            assert sub_alim["seleccion_manual"] is True
            assert sub_alim["magneto"] == 6
            assert sub_alim["protege_cable"] is False
            warns = [o for o in _obs(res) if o.get("tipo") == "warning"]
            assert any("Subcuadro" in o.get("texto", "") and "Recomendado" in o.get("texto", "") for o in warns), warns
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)


class TestCortocircuitoRecomendacion:
    def test_10_reco_none_when_ok_string_when_fails(self, client, project):
        sid = _make_study(client, project)
        try:
            # Force CC failure: low PDC and long final circuit
            res = _put_and_compute(client, sid, _data(poder_corte_ka=3, long_final=250))
            lineas = _lineas(res)
            any_fail = False
            for l in lineas:
                cc = l.get("cortocircuito")
                if not cc:
                    continue
                assert "recomendacion" in cc, cc
                if cc["protege_cc"]:
                    assert cc["recomendacion"] in (None, ""), cc
                else:
                    any_fail = True
                    assert cc["recomendacion"], cc
                    assert "Recomendaci" in cc["recomendacion"]
            assert any_fail, "expected at least one CC failure"
            # Observations: at least one CC warning citing recomendacion
            warns = [o for o in _obs(res) if o.get("tipo") == "warning"]
            assert any("cortocircuito" in o.get("texto", "").lower() for o in warns), warns
        finally:
            client.delete(f"{API}/studies/{sid}", timeout=15)


class TestSeedStudy:
    def test_20_seed_compute_shape(self, client):
        r = client.post(f"{API}/studies/{SEED_STUDY}/compute", timeout=30)
        assert r.status_code == 200, r.text
        res = r.json()
        lineas = _lineas(res)
        alims = [l for l in lineas if l.get("tipo") == "alimentacion"]
        assert len(alims) >= 2, f"seed should have >=2 alimentacion, got {len(alims)}"
        for a in alims:
            assert "board_id" in a
            assert a.get("editable_board") is True
            for k in ("magneto", "magneto_auto", "seleccion_manual", "protege_cable"):
                assert k in a, f"alim missing {k}: {a}"
        for l in lineas:
            cc = l.get("cortocircuito")
            if cc is not None:
                assert "recomendacion" in cc

    def test_21_docx_export_seed(self, client):
        r = client.get(f"{API}/studies/{SEED_STUDY}/export/docx", timeout=90)
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        body = r.content
        assert len(body) > 3000, f"docx too small: {len(body)} bytes"
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            names = z.namelist()
            assert "word/document.xml" in names
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        # Must contain REBT CC content
        assert "Cortocircuito" in xml or "cortocircuito" in xml, "docx missing CC section"
