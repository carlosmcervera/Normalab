"""FASE 3 (escaleras + fundamentos) · Incendios · E2E.

Se verifica que el motor RSCIEI conecta `_escalera_calc` con el bucle de sector,
y que el informe incluye la sección de Fundamentos normativos con extractos
base y (si hay escaleras) los 2 extractos específicos.

Escenarios:
  A) NO CUMPLE: escalera 'abierta', altura 20m, uso 'Comercial/Pública concurrencia',
     anchura 0.9m → proteccion_requerida='protegida', anchura_min>=1.00 y anchura
     proyectada 0.9 < min → estado 'no_cumple' en escalera y sector.
  B) CUMPLE: escalera 'protegida', 100 ocupantes, altura 12m,
     uso 'Administrativo/Docente', anchura 1.2m → proteccion 'protegida',
     anchura_min ~1.00, estado 'cumple'.
  C) build_report: sección 'fundamentos' con base (7 items) + 2 escaleras cuando hay.
  D) Export DOCX y XLSX responden 200 y son binarios válidos.
"""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://normlab.preview.emergentagent.com").rstrip("/") + "/api"
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
def project_id(sess):
    r = sess.post(f"{BASE_URL}/projects", json={
        "code": "TEST-INC-PH3-ESC", "name": "TEST INC Phase 3 Escaleras",
        "description": "phase 3 escaleras + fundamentos"})
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    pid = r.json().get("id")
    yield pid
    try:
        sess.delete(f"{BASE_URL}/projects/{pid}")
    except Exception:
        pass


def _study_data(esc_tipo, esc_ocupantes, esc_altura, esc_uso, esc_anchura, esc_sentido="descendente"):
    """Cada sector necesita 1 estancia normal con qsi/ci + 1 escalera."""
    return {
        "establecimiento": {"config": "C"},
        "sectores": [{
            "id": "s1", "nombre": "S1", "tipo": "sector", "ambito": "industrial",
            "config": "C", "situacion": "sobre_rasante",
            "num_salidas": 2, "ra": 1.0,
        }],
        "dependencias": [
            {
                "id": "d1", "sector_id": "s1", "nombre": "Nave", "clase": "normal",
                "sup_util": 500, "sup_construida": 500, "modo": "produccion",
                "qsi": 300, "ci": 1.0, "ra": 1.0,
            },
            {
                "id": "d2", "sector_id": "s1", "nombre": "Esc-1", "clase": "escalera",
                "sup_construida": 20, "sup_util": 20,
                "esc_tipo": esc_tipo,
                "esc_sentido": esc_sentido,
                "esc_uso": esc_uso,
                "esc_situacion": "interior",
                "esc_ocupantes": esc_ocupantes,
                "esc_altura_evac": esc_altura,
                "esc_anchura": esc_anchura,
                "esc_superficie": 20,
            },
        ],
    }


def _create_study(sess, project_id, name, data):
    r = sess.post(f"{BASE_URL}/studies", json={
        "project_id": project_id, "module_code": "INCENDIOS", "name": name})
    assert r.status_code in (200, 201), r.text
    sid = r.json()["id"]
    r = sess.put(f"{BASE_URL}/studies/{sid}", json={"data": data})
    assert r.status_code == 200, r.text[:400]
    r2 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r2.status_code == 200, r2.text[:400]
    body = r2.json()
    return sid, body.get("results", body), body.get("report", {})


# ---------------- Test A: NO CUMPLE ----------------
def test_escalera_no_cumple_abierta_comercial(sess, project_id):
    data = _study_data("abierta", esc_ocupantes=100, esc_altura=20.0,
                       esc_uso="Comercial/Pública concurrencia", esc_anchura=0.9)
    sid, results, _ = _create_study(sess, project_id, "TEST-esc-nc", data)
    sec = results["sectores"][0]
    assert sec.get("escaleras_protegidas"), "escaleras_protegidas debe existir"
    esc = sec["escaleras_protegidas"][0]
    calc = esc.get("calculo")
    assert calc is not None, "bloque 'calculo' ausente en la escalera"
    # Para 'Comercial/Pública concurrencia' descendente h=20 → protegida
    assert calc["proteccion_requerida"] == "protegida", calc
    # RF del recinto: EI 120
    assert calc["resistencia"] == "EI 120"
    # Anchura mín ≥ 1.00 (P/160=0.625, min_w=1.00)
    assert calc["anchura_min"] >= 1.00
    # Anchura proyectada 0.9 < min → no_cumple
    assert calc["anchura_estado"] == "no_cumple"
    assert calc["estado"] == "no_cumple"
    # Sector también en no_cumple
    assert sec["estado"] == "no_cumple", f"sector estado={sec['estado']}"
    # Estado global no_cumple
    assert results["estado_global"] == "no_cumple"


# ---------------- Test B: CUMPLE ----------------
def test_escalera_cumple_protegida_admin(sess, project_id):
    # Admin/Docente descendente: h<=14 → no_protegida; 14<h<=28 → protegida.
    # Usamos h=20 para exigir 'protegida' (proyectada 'protegida' → cumple).
    data = _study_data("protegida", esc_ocupantes=100, esc_altura=20.0,
                       esc_uso="Administrativo/Docente", esc_anchura=1.2)
    sid, results, _ = _create_study(sess, project_id, "TEST-esc-ok", data)
    sec = results["sectores"][0]
    esc = sec["escaleras_protegidas"][0]
    calc = esc["calculo"]
    assert calc["proteccion_requerida"] == "protegida"
    assert calc["resistencia"] == "EI 120"
    # Protegida con S=20 y P=100 → anchura_min = max((100-60)/160, 1.00) = max(0.25, 1.00) = 1.00
    assert abs(calc["anchura_min"] - 1.00) < 1e-6, calc["anchura_min"]
    assert calc["anchura_estado"] == "cumple"
    assert calc["proteccion_estado"] == "cumple"
    assert calc["estado"] == "cumple"


# Verifica que h=12 Admin/Docente sí devuelve 'no_protegida' según Tabla 5.1
def test_escalera_admin_h12_no_protegida(sess, project_id):
    data = _study_data("protegida", esc_ocupantes=50, esc_altura=12.0,
                       esc_uso="Administrativo/Docente", esc_anchura=1.2)
    sid, results, _ = _create_study(sess, project_id, "TEST-esc-h12", data)
    calc = results["sectores"][0]["escaleras_protegidas"][0]["calculo"]
    assert calc["proteccion_requerida"] == "no_protegida"
    # protegida proyectada > no_protegida requerida → cumple (over-compliance)
    assert calc["proteccion_estado"] == "cumple"
    assert calc["estado"] == "cumple"


# ---------------- Test C: Report fundamentos ----------------
def test_report_fundamentos_section(sess, project_id):
    data = _study_data("protegida", esc_ocupantes=50, esc_altura=10.0,
                       esc_uso="Administrativo/Docente", esc_anchura=1.2)
    sid, _, report = _create_study(sess, project_id, "TEST-esc-report", data)
    sections = report.get("sections", [])
    fund_sec = next((s for s in sections if s.get("type") == "fundamentos"), None)
    assert fund_sec is not None, "sección 'fundamentos' ausente"
    assert "Fundamentos normativos" in fund_sec["title"]
    items = fund_sec.get("items", [])
    assert len(items) == 9, f"esperados 9 items (base+escaleras), got {len(items)}"
    for it in items:
        assert "tema" in it and "cita" in it and "referencia" in it
    temas = [i["tema"] for i in items]
    assert any("Qs" in t or "carga de fuego" in t for t in temas)
    assert any("Dimensionado" in t for t in temas)
    assert any("Protección de las escaleras" in t for t in temas)


def test_report_fundamentos_base_only_no_escaleras(sess, project_id):
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{"id": "s1", "nombre": "S1", "tipo": "sector", "ambito": "industrial",
                      "config": "C", "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0}],
        "dependencias": [{
            "id": "d1", "sector_id": "s1", "nombre": "Nave", "clase": "normal",
            "sup_util": 500, "sup_construida": 500, "modo": "produccion",
            "qsi": 300, "ci": 1.0, "ra": 1.0,
        }],
    }
    sid, _, report = _create_study(sess, project_id, "TEST-no-esc", data)
    fund = next(s for s in report["sections"] if s.get("type") == "fundamentos")
    assert len(fund["items"]) == 7


# ---------------- Test D: Exports DOCX/XLSX ----------------
def test_export_docx_xlsx(sess, project_id):
    data = _study_data("protegida", esc_ocupantes=100, esc_altura=20.0,
                       esc_uso="Administrativo/Docente", esc_anchura=1.2)
    sid, _, _ = _create_study(sess, project_id, "TEST-esc-export", data)

    r = sess.get(f"{BASE_URL}/studies/{sid}/export/docx")
    assert r.status_code == 200, r.text[:200]
    assert r.content[:2] == b"PK", "DOCX debe empezar por 'PK' (zip)"
    assert len(r.content) > 5000

    r = sess.get(f"{BASE_URL}/studies/{sid}/export/xlsx")
    assert r.status_code == 200, r.text[:200]
    assert r.content[:2] == b"PK", "XLSX debe empezar por 'PK' (zip)"
    assert len(r.content) > 3000
