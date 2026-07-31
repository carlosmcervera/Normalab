"""Iteration 29 — Phase 5 tests for RSCIEI Incendios:
  (1) Anexo justificativo de propagación (interior + exterior)
  (2) Reducción de R (estabilidad) un grado por rociadores automáticos (RSCIEI, Anexo II, Sección 5)
  (3) Aviso de ventilación de humos (RSCIEI Anexo III, 8.4)
  (4) Export DOCX contiene el Anexo de propagación
"""
import io
import os
import copy
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PASSWORD = "Admin1234!"
STUDY_MIXED = "6a6846ef73ca337c4f097a3f"
STUDY_ALT = "6a67710c3fd29edfa3820217"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token") or r.json().get("token")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    return s


@pytest.fixture
def restore_study(client):
    """Save & restore study data around a test to avoid xdist interference."""
    saved = {}

    def _save(sid):
        r = client.get(f"{API}/studies/{sid}")
        assert r.status_code == 200
        saved[sid] = copy.deepcopy(r.json().get("data") or {})

    yield _save
    for sid, data in saved.items():
        try:
            client.put(f"{API}/studies/{sid}", json={"data": data})
            client.post(f"{API}/studies/{sid}/compute")
        except Exception:
            pass


def _get_study(client, sid):
    r = client.get(f"{API}/studies/{sid}")
    assert r.status_code == 200, r.text
    return r.json()


def _recompute(client, sid, payload=None):
    if payload is not None:
        r = client.put(f"{API}/studies/{sid}", json={"data": payload})
        assert r.status_code == 200, r.text
    r = client.post(f"{API}/studies/{sid}/compute")
    assert r.status_code == 200, r.text
    return r.json()


def _get_report(client, sid):
    doc = _get_study(client, sid)
    return {"report": doc.get("report") or {}, "results": doc.get("results") or {}}


# ---------------------------------------------------------------- ANEXO ----
def test_report_includes_anexo_propagacion(client):
    _recompute(client, STUDY_MIXED)
    rep = _get_report(client, STUDY_MIXED)
    sections = rep.get("report", rep).get("sections") or rep.get("sections")
    anexo = next((s for s in sections if s.get("type") == "anexo_propagacion"), None)
    assert anexo is not None, "Missing anexo_propagacion section"
    assert "Anexo justificativo de propagación" in anexo["title"]
    items = anexo["items"]
    assert len(items) >= 1
    ambitos = {b.get("ambito") for b in items}
    # Study is mixed RSCIEI + CTE
    assert "RSCIEI" in ambitos or "CTE DB-SI" in ambitos
    for b in items:
        assert b.get("ambito") in ("RSCIEI", "CTE DB-SI")
        assert len(b.get("interior") or []) >= 2
        assert len(b.get("exterior") or []) >= 1
        for cita in b["interior"] + b["exterior"]:
            assert cita.get("tema") and cita.get("cita") and cita.get("referencia")
            assert "valor" in cita


# ------------------------------------------------------- REDUCCION R -------
def test_reduccion_r_por_rociadores_solo_en_rsciei(client, restore_study):
    restore_study(STUDY_ALT)
    study = _get_study(client, STUDY_ALT)
    data = copy.deepcopy(study["data"])
    sec_rsciei = next((s for s in data["sectores"] if (s.get("ambito") or "industrial") != "cte"), None)
    sec_cte = next((s for s in data["sectores"] if s.get("ambito") == "cte"), None)
    assert sec_rsciei is not None, "Need a RSCIEI sector"

    # ---- WITHOUT rociadores ----
    for s in data["sectores"]:
        s["rociadores"] = False
    res = _recompute(client, STUDY_ALT, data)
    results = res.get("results", res)
    s_out = next(s for s in results["sectores"] if s["id"] == sec_rsciei["id"])
    est_base = s_out["requisitos"]["estabilidad"]
    assert est_base.get("reduccion_rociadores") in (None, False)
    val_base = est_base["valor"]

    # ---- WITH rociadores on RSCIEI sector ----
    for s in data["sectores"]:
        if s["id"] == sec_rsciei["id"]:
            s["rociadores"] = True
    res2 = _recompute(client, STUDY_ALT, data)
    results2 = res2.get("results", res2)
    s_out2 = next(s for s in results2["sectores"] if s["id"] == sec_rsciei["id"])
    est_red = s_out2["requisitos"]["estabilidad"]

    escala = ["R 30", "R 60", "R 90", "R 120", "R 180", "R 240"]
    if val_base in escala and escala.index(val_base) > 0:
        assert est_red.get("reduccion_rociadores") is True
        assert est_red.get("valor_base") == val_base
        assert escala.index(est_red["valor"]) == escala.index(val_base) - 1
        assert "Anexo II, Sección 5" in est_red["detalle"]
    else:
        # If R 30 or "No exigible" (config D), no reduction possible
        assert est_red.get("reduccion_rociadores") in (None, False)

    # ---- CTE sector should NOT be reduced even if rociadores=true ----
    if sec_cte:
        for s in data["sectores"]:
            s["rociadores"] = True
        res3 = _recompute(client, STUDY_ALT, data)
        s_cte_out = next(s for s in res3.get("results", res3)["sectores"] if s["id"] == sec_cte["id"])
        assert s_cte_out["requisitos"]["estabilidad"].get("reduccion_rociadores") in (None, False)


# ------------------------------------------------------ HUMOS 8.4 ----------
def test_ventilacion_humos_aviso_84(client, restore_study):
    restore_study(STUDY_ALT)
    study = _get_study(client, STUDY_ALT)
    data = copy.deepcopy(study["data"])

    # Pick RSCIEI sector where control de humos is expected (categoria MEDIO/ALTO).
    # Compute once to know which sectors have superficie_aerodinamica > 0.
    res0 = _recompute(client, STUDY_ALT, data)
    results0 = res0.get("results", res0)
    target = None
    for s in results0["sectores"]:
        if (s.get("ambito") or "industrial") == "cte":
            continue
        inst = next((i for i in s["requisitos"]["instalaciones"]
                     if i.get("superficie_aerodinamica")), None)
        if inst and (inst["superficie_aerodinamica"].get("superficie_aerodinamica") or 0) > 0:
            target = s
            break
    assert target is not None, "No RSCIEI sector with aerodynamic surface computed"

    aero_req = target["requisitos"]["instalaciones"]
    _humo = next(i for i in aero_req if i.get("superficie_aerodinamica"))
    exigida = _humo["superficie_aerodinamica"]["superficie_aerodinamica"]
    sid = target["id"]

    # --- Case A: INSUFICIENTE (proyectada < exigida) ---
    for s in data["sectores"]:
        if s["id"] == sid:
            s["humos_ventilacion_proyectada"] = max(0.01, exigida / 2.0)
    resA = _recompute(client, STUDY_ALT, data)
    outA = next(s for s in resA.get("results", resA)["sectores"] if s["id"] == sid)
    humoA = next(i for i in outA["requisitos"]["instalaciones"] if i.get("superficie_aerodinamica"))
    aeroA = humoA["superficie_aerodinamica"]
    assert aeroA.get("proyectada") is not None
    assert aeroA.get("cumple") is False
    assert "AVISO" in humoA["detalle"]
    warnings = [o for o in outA["observaciones"] if o.get("tipo") == "warning" and "ventilación" in o.get("texto", "").lower()]
    assert warnings, "Expected a warning observation about ventilación insuficiente"
    assert outA["estado"] in ("observaciones", "no_cumple")

    # --- Case B: SUFICIENTE (proyectada >= exigida) ---
    for s in data["sectores"]:
        if s["id"] == sid:
            s["humos_ventilacion_proyectada"] = exigida + 5.0
    resB = _recompute(client, STUDY_ALT, data)
    outB = next(s for s in resB.get("results", resB)["sectores"] if s["id"] == sid)
    humoB = next(i for i in outB["requisitos"]["instalaciones"] if i.get("superficie_aerodinamica"))
    aeroB = humoB["superficie_aerodinamica"]
    assert aeroB.get("cumple") is True
    assert "AVISO" not in humoB["detalle"]
    warnings_B = [o for o in outB["observaciones"] if "ventilación proyectada" in o.get("texto", "").lower()]
    assert not warnings_B


# ------------------------------------------------------ DOCX EXPORT --------
def test_docx_export_contains_anexo(client):
    r = client.get(f"{API}/studies/{STUDY_MIXED}/export/docx")
    assert r.status_code == 200, r.text[:400]
    assert r.headers.get("content-type", "").startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    # Extract text from docx
    from zipfile import ZipFile
    import re
    with ZipFile(io.BytesIO(r.content)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    assert "Anexo justificativo de propagación" in text
    assert "Propagación interior" in text
    assert "Propagación exterior" in text
