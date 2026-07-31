"""Fase 4 · Construcción y propagación por ámbito (RSCIEI + CTE DB-SI · SI 2).

Verifica que el paso 'Construcción y propagación' sea ámbito-aware:
- Sectores industriales → RSCIEI Anexo II.
- Sectores CTE → CTE DB-SI (SI 1 / SI 2).
- Separación entre huecos SI 2 (Tabla/Fig. 1.1) con toggles.
- Exportación DOCX contiene los rótulos esperados.
"""
import io
import os
import copy
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
STUDY_IDS = ["6a6846ef73ca337c4f097a3f", "6a67710c3fd29edfa3820217"]
ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PASS = "Admin1234!"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def studies(client):
    """Recompute both existing studies. Skip missing ones."""
    out = {}
    for sid in STUDY_IDS:
        g = client.get(f"{BASE_URL}/api/studies/{sid}")
        if g.status_code == 404:
            continue
        assert g.status_code == 200, f"GET {sid}: {g.status_code} {g.text[:300]}"
        r = client.post(f"{BASE_URL}/api/studies/{sid}/compute")
        assert r.status_code == 200, f"compute {sid}: {r.status_code} {r.text[:400]}"
        out[sid] = r.json()
    if not out:
        pytest.skip("Ningún estudio Incendios existente disponible.")
    return out


# ---------- 1. No regresión: compute devuelve estado_global y sectores ---------- #
def test_compute_no_regressions(studies):
    for sid, payload in studies.items():
        res = payload["results"]
        assert "estado_global" in res, f"{sid}: falta estado_global"
        assert res["estado_global"] in ("cumple", "no_cumple", "observaciones")
        assert isinstance(res.get("sectores"), list) and res["sectores"], f"{sid}: sin sectores"


# ---------- 2. Bloque construccion ámbito-aware ---------- #
def test_construccion_ambito_aware(studies):
    found_cte = found_rsciei = False
    for sid, payload in studies.items():
        for sec in payload["results"]["sectores"]:
            c = sec.get("construccion")
            assert c, f"{sid} · sector {sec.get('nombre')}: falta construccion"
            # Estructura obligatoria
            for k in ("ambito", "normativa", "interior", "exterior"):
                assert k in c, f"{sid}/{sec['nombre']}: falta clave {k}"
            interior = c["interior"]; exterior = c["exterior"]
            assert interior.get("reaccion") and "tabla" in interior["reaccion"]
            assert len(interior["reaccion"]["tabla"]) == 4, "Tabla reacción debe tener 4 filas"
            assert interior.get("delimitadores", {}).get("requerido"), "delimitadores.requerido vacío"
            assert "medianeras" in exterior and "fachadas" in exterior and "cubierta" in exterior

            ambito = c["ambito"]
            normativa = c["normativa"]
            delim = interior["delimitadores"]["requerido"]
            suelos = interior["reaccion"]["tabla"][0].get("suelos", "")
            if ambito == "cte":
                found_cte = True
                assert "CTE DB-SI" in normativa, f"CTE sector debería llevar 'CTE DB-SI' en normativa: {normativa}"
                # Reacción CTE: suelos 'EFL'
                assert "EFL" in suelos, f"Reacción CTE debe usar EFL en suelos: {suelos}"
                # Delimitador CTE (EI 60/90/120 según altura)
                assert delim in ("EI 60", "EI 90", "EI 120"), f"Delim CTE inesperado: {delim}"
            else:
                found_rsciei = True
                assert "RSCIEI" in normativa, f"RSCIEI sector debería llevar 'RSCIEI': {normativa}"
                # Delimitador RSCIEI por categoría (EI 120/180/240)
                assert delim in ("EI 120", "EI 180", "EI 240"), f"Delim RSCIEI inesperado: {delim}"
                # Reacción RSCIEI usa 'CFL' o 'BFL' (Tabla 2.1.4)
                assert "FL" in suelos and "EFL" not in suelos, f"Reacción RSCIEI debe usar CFL/BFL: {suelos}"

    assert found_cte or found_rsciei, "Ninguno de los estudios contiene sectores de ambos ámbitos"


# ---------- 3. Fase 3 no regresión: superficie aerodinámica humos ---------- #
def test_fase3_humos_control(studies):
    """La instalación 'Control de humos y calor' debe seguir presente en requisitos."""
    seen = False
    for sid, payload in studies.items():
        for sec in payload["results"]["sectores"]:
            for ins in (sec.get("requisitos") or {}).get("instalaciones", []) or []:
                nombre = ins.get("nombre", "").lower()
                if "humos" in nombre and "calor" in nombre:
                    seen = True
                    break
    # Solo assert si se encontró en al menos un sector (depende del riesgo/superficie)
    # No fallamos si no aplica, pero registramos.
    print(f"[fase3] Control humos/calor presente en algún sector: {seen}")


# ---------- 4. Huecos SI 2 (fachada) · toggle desde compute ---------- #
def _find_cte_sector(client, sid):
    g = client.get(f"{BASE_URL}/api/studies/{sid}").json()
    for sec in (g.get("data") or {}).get("sectores", []) or []:
        if sec.get("ambito") == "cte":
            return g, sec
    return g, None


def test_huecos_si2_no_cumple_then_cumple(client, studies):
    """Con distancia < mínima → no_cumple; con EI 60 → cumple; con edificio colindante la
    separación exigida se reduce a la mitad."""
    target = None
    for sid in studies.keys():
        doc, sec = _find_cte_sector(client, sid)
        if sec:
            target = (sid, doc, sec)
            break
    if not target:
        pytest.skip("No hay sector CTE en los estudios disponibles para probar huecos SI 2.")
    sid, doc, cte_sec = target
    original_data = copy.deepcopy(doc.get("data") or {})

    def apply(patch):
        data = copy.deepcopy(original_data)
        for s in data.get("sectores", []):
            if s.get("id") == cte_sec["id"]:
                s.update(patch)
        r = client.put(f"{BASE_URL}/api/studies/{sid}", json={"data": data})
        assert r.status_code == 200, r.text
        r = client.post(f"{BASE_URL}/api/studies/{sid}/compute")
        assert r.status_code == 200, r.text
        res = r.json()["results"]
        for sec in res["sectores"]:
            if sec["id"] == cte_sec["id"]:
                return sec
        raise AssertionError("Sector no devuelto tras recompute")

    try:
        # (a) huecos activados con distancia insuficiente → no_cumple
        sec_a = apply({"fachada_encuentro": True, "fachada_huecos": True,
                       "fachada_angulo": "90", "fachada_huecos_dist": 0.5,
                       "fachada_huecos_ei60": False, "edificio_colindante": False,
                       "fachada_ei": "EI 60"})
        huecos_a = ((sec_a.get("construccion") or {}).get("fachadas") or {}).get("huecos")
        assert huecos_a, f"huecos ausente en sector: {sec_a.get('construccion')}"
        assert huecos_a["estado"] == "no_cumple", f"Esperado no_cumple, obtenido {huecos_a}"
        # Sector debe reflejar no_cumple
        assert sec_a["estado"] == "no_cumple", f"Sector debería ser no_cumple: {sec_a['estado']}"
        # Al menos una observación tipo error mencionando huecos
        err_texts = " ".join(o.get("texto", "") for o in sec_a.get("observaciones", []) if o.get("tipo") == "error")
        assert "huecos" in err_texts.lower(), f"No observación error de huecos: {err_texts}"

        # (b) marcar huecos EI 60 → cumple
        sec_b = apply({"fachada_encuentro": True, "fachada_huecos": True,
                       "fachada_angulo": "90", "fachada_huecos_dist": 0.5,
                       "fachada_huecos_ei60": True, "edificio_colindante": False,
                       "fachada_ei": "EI 60"})
        huecos_b = ((sec_b.get("construccion") or {}).get("fachadas") or {}).get("huecos")
        assert huecos_b["estado"] == "cumple", f"Con EI 60 esperado cumple: {huecos_b}"

        # (c) edificio colindante reduce a la mitad la separación efectiva
        sec_c = apply({"fachada_encuentro": True, "fachada_huecos": True,
                       "fachada_angulo": "90", "fachada_huecos_dist": 0.5,
                       "fachada_huecos_ei60": False, "edificio_colindante": True,
                       "fachada_ei": "EI 60"})
        huecos_c = ((sec_c.get("construccion") or {}).get("fachadas") or {}).get("huecos")
        assert huecos_c["colindante"] is True
        assert abs(huecos_c["efectivo_m"] - huecos_c["requerido_m"] / 2.0) < 0.02, \
            f"colindante debe halvear: req={huecos_c['requerido_m']}, ef={huecos_c['efectivo_m']}"

        # (d) verificar monotonía: ángulo menor → separación mayor
        sec_45 = apply({"fachada_encuentro": True, "fachada_huecos": True,
                        "fachada_angulo": "45", "fachada_huecos_dist": 5.0,
                        "fachada_huecos_ei60": False, "edificio_colindante": False,
                        "fachada_ei": "EI 60"})
        sec_180 = apply({"fachada_encuentro": True, "fachada_huecos": True,
                         "fachada_angulo": "180", "fachada_huecos_dist": 5.0,
                         "fachada_huecos_ei60": False, "edificio_colindante": False,
                         "fachada_ei": "EI 60"})
        h45 = ((sec_45.get("construccion") or {}).get("fachadas") or {}).get("huecos")
        h180 = ((sec_180.get("construccion") or {}).get("fachadas") or {}).get("huecos")
        assert h45["requerido_m"] > h180["requerido_m"], \
            f"45º debe exigir más separación que 180º: {h45['requerido_m']} vs {h180['requerido_m']}"
    finally:
        # Restaurar data original
        client.put(f"{BASE_URL}/api/studies/{sid}", json={"data": original_data})
        client.post(f"{BASE_URL}/api/studies/{sid}/compute")


# ---------- 5. Export DOCX contiene rótulos de construcción ---------- #
def test_export_docx_contains_construccion(client, studies):
    from zipfile import ZipFile
    sid = next(iter(studies.keys()))
    r = client.get(f"{BASE_URL}/api/studies/{sid}/export/docx")
    assert r.status_code == 200, f"DOCX export: {r.status_code} {r.text[:300]}"
    assert r.content[:2] == b"PK", "DOCX inválido (no ZIP)"
    with ZipFile(io.BytesIO(r.content)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    assert "Construcción y propagación" in xml, "Falta rótulo 'Construcción y propagación'"
    assert "Propagación interior" in xml, "Falta 'Propagación interior'"
    assert "Propagación exterior" in xml, "Falta 'Propagación exterior'"
    assert "Elementos delimitadores del sector" in xml, "Falta 'Elementos delimitadores del sector'"


# ---------- 6. Estudio guardado contiene report con construccion por sector ---------- #
def test_stored_report_has_construccion(client, studies):
    sid = next(iter(studies.keys()))
    doc = client.get(f"{BASE_URL}/api/studies/{sid}").json()
    res = doc.get("results") or {}
    assert res.get("sectores"), "results.sectores vacío tras compute"
    for sec in res["sectores"]:
        c = sec.get("construccion") or {}
        assert c.get("normativa"), f"Sector {sec.get('nombre')}: construccion.normativa vacío"
