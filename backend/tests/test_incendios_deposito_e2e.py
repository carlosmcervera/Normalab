"""E2E tests via public REACT_APP_BACKEND_URL for INCENDIOS P0 changes:
   (1) Qs uses superficie útil; superficie máxima sectorización usa construida.
   (2) 'Depósito de combustible' aporta Q = PCI × densidad × volumen × Ci al Qs.
   (3) Validaciones y exportaciones DOCX/XLSX incluyen el depósito.
"""
import os
import re
import io
import zipfile
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PWD = "Admin1234!"


@pytest.fixture(scope="module")
def sess():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PWD})
    assert r.status_code == 200, f"login: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    return s


@pytest.fixture(scope="module")
def project(sess):
    r = sess.post(f"{BASE_URL}/projects", json={"code": "TEST-DEP-1", "name": "TEST Depósito E2E"})
    if r.status_code >= 400:
        # buscar existente
        rl = sess.get(f"{BASE_URL}/projects")
        for p in rl.json():
            if p.get("code") == "TEST-DEP-1":
                return p
        pytest.fail(f"proj create: {r.status_code} {r.text}")
    return r.json()


def _study_payload():
    return {
        "establecimiento": {"config": "C"},
        "sectores": [
            {"id": "s1", "nombre": "Nave", "tipo": "sector", "ambito": "industrial",
             "config": "C", "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0}
        ],
        "dependencias": [
            {"id": "d1", "sector_id": "s1", "nombre": "Producción",
             "sup_util": 800, "sup_construida": 900,
             "modo": "produccion", "qsi": 400, "ci": 1.44, "ra": 1.0,
             "densidad": 10, "uso_ocupacion": "Fabricación", "sin_ocupacion": True},
            {"id": "d2", "sector_id": "s1", "nombre": "Depósito gasoil",
             "sup_util": 20, "sup_construida": 25,
             "modo": "deposito", "combustible": "Gasoil / gasóleo",
             "pci": 42.7, "dens_comb": 845, "volumen": 10, "ci": 1.3,
             "sin_ocupacion": True},
        ],
    }


@pytest.fixture(scope="module")
def study(sess, project):
    payload = {"project_id": project["id"], "module_code": "INCENDIOS", "name": "TEST Qs util + deposito"}
    r = sess.post(f"{BASE_URL}/studies", json=payload)
    assert r.status_code in (200, 201), f"studies POST: {r.status_code} {r.text}"
    st = r.json()
    # save data
    r2 = sess.put(f"{BASE_URL}/studies/{st['id']}", json={"data": _study_payload()})
    assert r2.status_code == 200, r2.text
    return r2.json()


# --------------------------------------------------------------------------- #
def test_compute_qs_uses_superficie_util_and_deposito(sess, study):
    r = sess.post(f"{BASE_URL}/studies/{study['id']}/compute")
    assert r.status_code == 200, r.text
    body = r.json()
    results = body["results"]
    sec = results["sectores"][0]
    calc = sec["calculo"]
    # A util = 800 (produccion) + 20 (deposito) = 820; A construida = 900 + 25 = 925
    assert calc["A"] == pytest.approx(820.0, abs=0.1), f"A util debía ser 820, got {calc['A']}"
    assert calc["A_construida"] == pytest.approx(925.0, abs=0.1), f"A construida debía ser 925, got {calc['A_construida']}"
    # sectorización usa construida
    assert sec["sectorizacion"]["superficie_sector"] == pytest.approx(925.0, abs=0.1)
    # Depositos: aporte = 42.7*845*10*1.3 = 469,169.5
    esperado_aporte = 42.7 * 845 * 10 * 1.3
    deps = results.get("depositos") or []
    assert len(deps) == 1
    assert deps[0]["aporte"] == pytest.approx(esperado_aporte, rel=1e-3)
    assert "justificacion" in deps[0]
    # numerador incluye: (400*1.44*800) + aporte
    num_prod = 400 * 1.44 * 800
    assert calc["numerador"] == pytest.approx(num_prod + esperado_aporte, rel=1e-3)
    # qs_mj = numerador / A_util * ra
    assert calc["qs_mj"] == pytest.approx((num_prod + esperado_aporte) / 820.0, rel=1e-3)
    # detalle_zonas contiene modo deposito
    modos = [z.get("modo") for z in calc.get("zonas", [])]
    assert "deposito" in modos, f"zonas: {calc.get('zonas')}"


def test_validation_deposito_missing_fields(sess, project):
    payload = {"project_id": project["id"], "module_code": "INCENDIOS", "name": "TEST bad deposito"}
    r = sess.post(f"{BASE_URL}/studies", json=payload)
    sid = r.json()["id"]
    bad = _study_payload()
    # borrar pci del depósito
    bad["dependencias"][1]["pci"] = 0
    sess.put(f"{BASE_URL}/studies/{sid}", json={"data": bad})
    r2 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r2.status_code == 422, f"expected 422, got {r2.status_code} {r2.text}"
    assert "pci" in r2.text.lower() or "depósito" in r2.text.lower() or "deposito" in r2.text.lower()

    # volumen <=0
    bad2 = _study_payload()
    bad2["dependencias"][1]["volumen"] = 0
    sess.put(f"{BASE_URL}/studies/{sid}", json={"data": bad2})
    r3 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r3.status_code == 422
    assert "volumen" in r3.text.lower() or "depósito" in r3.text.lower()

    # dens_comb faltante
    bad3 = _study_payload()
    bad3["dependencias"][1]["dens_comb"] = 0
    sess.put(f"{BASE_URL}/studies/{sid}", json={"data": bad3})
    r4 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r4.status_code == 422

    sess.delete(f"{BASE_URL}/studies/{sid}")


def test_export_docx_contains_deposito(sess, study):
    # asegurar compute
    sess.post(f"{BASE_URL}/studies/{study['id']}/compute")
    r = sess.get(f"{BASE_URL}/studies/{study['id']}/export/docx")
    assert r.status_code == 200
    assert "wordprocessingml" in r.headers["content-type"]
    # DOCX es un ZIP; leer document.xml y buscar "gasoil" o "depósito"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml = z.read("word/document.xml").decode("utf-8", errors="ignore").lower()
    assert "depósito" in xml or "deposito" in xml or "gasoil" in xml, "DOCX no menciona depósito"


def test_export_xlsx_valid_with_deposito(sess, study):
    sess.post(f"{BASE_URL}/studies/{study['id']}/compute")
    r = sess.get(f"{BASE_URL}/studies/{study['id']}/export/xlsx")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    # XLSX es un ZIP; asegurar apertura
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert any(n.startswith("xl/worksheets/") for n in names)
    # Buscar mención Gasoil/depósito en cualquier XML del libro (sharedStrings o inline strings)
    blob = ""
    for n in names:
        if n.endswith(".xml"):
            blob += z.read(n).decode("utf-8", errors="ignore").lower()
    assert "gasoil" in blob or "depósito" in blob or "deposito" in blob, "XLSX no menciona depósito"


def test_report_contains_depositos_resumen(sess, study):
    r = sess.post(f"{BASE_URL}/studies/{study['id']}/compute")
    report = r.json()["report"]
    sections = report.get("sections") or []
    # Buscar sección resumen_ejecutivo con depositos
    resumen = next((s for s in sections if s.get("type") == "resumen_ejecutivo" or s.get("id") == "resumen_ejecutivo"), None)
    assert resumen is not None, f"No hay resumen_ejecutivo. Types: {[s.get('type') for s in sections]}"
    # el bloque debe incluir depositos con justificacion
    txt = str(resumen).lower()
    assert "depósito" in txt or "deposito" in txt or "gasoil" in txt, "Resumen no incluye depósitos"


def test_cleanup(sess, study, project):
    sess.delete(f"{BASE_URL}/studies/{study['id']}")
    sess.delete(f"{BASE_URL}/projects/{project['id']}")
