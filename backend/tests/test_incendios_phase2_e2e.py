"""FASE 2 · Incendios · E2E tests · Construcción y propagación

Comprueba que:
  2a) results.sectores[].construccion tiene reaccion (tabla 2.1.4 con 4 filas + nri_alto+cumple+obs),
      medianeras (según Tabla 2.2.1) cuando medianera_otro=true, fachadas (según Tabla 2.2.2)
      cuando fachada_encuentro=true, y cubierta.
      · NRI MEDIO + medianera_ei='EI 120' → requerido 'EI 180' y estado 'no_cumple'.
      · fachada_encuentro=true, angulo='135', fachada_ei='EI 60', delimitador EI 180 →
        requerido 'EI 90' (50%), distancia_d 1.5, estado 'no_cumple'.
  2b) Observaciones: cuando medianera/fachada NO cumplen aparecen entradas 'error'; cuando
      reaccion.cumple=false, una observación de advertencia con la Tabla 2.1.4.
  2c) Schema (GET /api/modules/incendios/schema) → los 5 pasos en orden:
      superficies_proyecto, ocupacion, sectores_incendio, construccion, evacuacion.
  2d) Export DOCX 200 e incluye contenidos de reacción/propagación (tabla 2.1.4 + medianeras/fachadas).
"""
import os
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
def project_id(sess):
    r = sess.post(f"{BASE_URL}/projects", json={
        "code": "TEST-INC-PH2", "name": "TEST INC Phase 2", "description": "phase 2 e2e"
    })
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    pid = r.json().get("id")
    yield pid
    try:
        sess.delete(f"{BASE_URL}/projects/{pid}")
    except Exception:
        pass


def _put_and_compute(sess, sid, data):
    r = sess.put(f"{BASE_URL}/studies/{sid}", json={"data": data})
    assert r.status_code == 200, f"put: {r.status_code} {r.text[:400]}"
    r2 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r2.status_code == 200, f"compute: {r2.status_code} {r2.text[:400]}"
    body = r2.json()
    return body.get("results", body)


def _mk_study(sess, project_id, name, data):
    r = sess.post(f"{BASE_URL}/studies", json={
        "project_id": project_id, "module_code": "INCENDIOS", "name": name})
    assert r.status_code in (200, 201), f"create: {r.status_code} {r.text[:400]}"
    sid = r.json()["id"]
    return sid, _put_and_compute(sess, sid, data)


# ==================================================================== #
# 2c) Schema: pasos en orden
# ==================================================================== #
def test_2c_schema_steps_order(sess):
    # Intento con y sin prefijo de módulos
    r = sess.get(f"{BASE_URL}/modules/INCENDIOS/schema")
    assert r.status_code == 200, f"schema: {r.status_code} {r.text[:200]}"
    body = r.json()
    schema = body.get("schema") or body
    steps = schema.get("steps") or []
    types = [s.get("type") for s in steps]
    expected = ["superficies_proyecto", "ocupacion", "sectores_incendio", "construccion", "evacuacion"]
    assert types == expected, f"steps types order incorrecto: {types}"


# ==================================================================== #
# 2a + 2b) Cálculo de construccion + observaciones
# ==================================================================== #
def test_2a_construccion_medianera_fachada_no_cumple(sess, project_id):
    # NRI MEDIO: buscamos Qs > 850 MJ/m². Con qsi=1500·ci=1·A=100/100 → Qs=1500 → MEDIO (nivel 4)
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{
            "id": "s1", "nombre": "SEC-Medio", "tipo": "sector",
            "ambito": "industrial", "config": "C",
            "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
            # Reacción al fuego: NO cumple
            "reaccion_cumple": False,
            "reaccion_obs": "revisar techos",
            # Medianera con otro establecimiento: proyectado EI 120 (< EI 180 req.)
            "medianera_otro": True,
            "medianera_ei": "EI 120",
            # Fachada: 135° → d 1.5 m; EI 60 (< req 50% EI 180 = EI 90)
            "fachada_encuentro": True,
            "fachada_angulo": "135",
            "fachada_ei": "EI 60",
            "cubierta_ligera": True,
            "cubierta_obs": "chapa sandwich",
        }],
        "dependencias": [
            {"id": "d1", "nombre": "Nave", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 1500, "ci": 1.0},
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-2a", data)
    try:
        sec = res["sectores"][0]
        # NRI MEDIO
        assert sec["nivel_riesgo"]["categoria"] == "MEDIO", sec["nivel_riesgo"]

        c = sec.get("construccion")
        assert c, "construccion debe existir en sector"

        # Reacción al fuego
        reac = c["reaccion"]
        assert isinstance(reac["tabla"], list) and len(reac["tabla"]) == 4
        assert reac["nri_alto"] is False  # MEDIO, no ALTO
        assert reac["cumple"] is False
        assert reac["observaciones"] == "revisar techos"

        # Medianera: MEDIO → requerido EI 180, proyectado EI 120 → no_cumple
        med = c["medianeras"]
        assert med and med["aplica"] is True
        assert med["requerido"] == "EI 180", med
        assert med["proyectado"] == "EI 120"
        assert med["estado"] == "no_cumple", med

        # Fachada: 135° → d 1.5; delimitador EI 180 (por config C nivel MEDIO) → req_min = 180//2 = 90 → 'EI 90'
        # proyectado EI 60 → no_cumple
        fach = c["fachadas"]
        assert fach and fach["aplica"] is True
        assert fach["angulo"] == "135"
        assert abs(float(fach["distancia_d"]) - 1.5) < 1e-6
        assert fach["requerido"] == "EI 90", f"esperado EI 90 got {fach['requerido']}"
        assert fach["proyectado"] == "EI 60"
        assert fach["estado"] == "no_cumple"

        # Cubierta
        assert c["cubierta"]["ligera"] is True
        assert c["cubierta"]["observaciones"] == "chapa sandwich"

        # 2b) Observaciones
        obs = sec.get("observaciones") or []
        errors = [o for o in obs if o.get("tipo") == "error"]
        err_text = " | ".join(o.get("texto", "") for o in errors)
        assert "medianer" in err_text.lower() or "2.2.1" in err_text, err_text
        assert "fachada" in err_text.lower() or "2.2.2" in err_text or "compartimentador" in err_text.lower(), err_text
        # advertencia de reacción
        adv = [o for o in obs if o.get("tipo") in ("advertencia", "warning")]
        assert any("2.1.4" in (o.get("texto") or "").lower() or "reacci" in (o.get("texto") or "").lower() for o in adv), adv
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


def test_2a_construccion_alto_cumple(sess, project_id):
    """Contrapartida: sector ALTO con medianera EI 240 (cumple), fachada 180° (d=1.0) con EI adecuada."""
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{
            "id": "s1", "nombre": "SEC-Alto", "tipo": "sector",
            "ambito": "industrial", "config": "C",
            "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
            "reaccion_cumple": True,
            "medianera_otro": True, "medianera_ei": "EI 240",
            "fachada_encuentro": True, "fachada_angulo": "180", "fachada_ei": "EI 240",
        }],
        "dependencias": [
            {"id": "d1", "nombre": "Nave", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 5000, "ci": 1.5},  # Qs=7500 → ALTO
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-2a-alto", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["categoria"] == "ALTO"
        c = sec["construccion"]
        assert c["reaccion"]["nri_alto"] is True
        assert c["medianeras"]["requerido"] == "EI 240"
        assert c["medianeras"]["estado"] == "cumple"
        assert abs(float(c["fachadas"]["distancia_d"]) - 1.0) < 1e-6
        assert c["fachadas"]["estado"] == "cumple"
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


def test_2a_construccion_angulo_90(sess, project_id):
    """Verifica ángulo 90° → d = 2.0 m."""
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{
            "id": "s1", "nombre": "SEC-Bajo", "tipo": "sector",
            "ambito": "industrial", "config": "C",
            "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
            "fachada_encuentro": True, "fachada_angulo": "90", "fachada_ei": "EI 60",
        }],
        "dependencias": [
            {"id": "d1", "nombre": "Nave", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 300, "ci": 1.0},  # BAJO
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-2a-90", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["categoria"] == "BAJO"
        f = sec["construccion"]["fachadas"]
        assert f["angulo"] == "90"
        assert abs(float(f["distancia_d"]) - 2.0) < 1e-6
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ==================================================================== #
# 2d) Export DOCX incluye construccion
# ==================================================================== #
def test_2d_export_docx_incluye_construccion(sess, project_id):
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{
            "id": "s1", "nombre": "SEC-DOCX", "tipo": "sector",
            "ambito": "industrial", "config": "C",
            "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
            "reaccion_cumple": True,
            "medianera_otro": True, "medianera_ei": "EI 180",
            "fachada_encuentro": True, "fachada_angulo": "135", "fachada_ei": "EI 90",
            "cubierta_ligera": True,
        }],
        "dependencias": [
            {"id": "d1", "nombre": "Nave", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 1500, "ci": 1.0},
        ],
    }
    sid, _ = _mk_study(sess, project_id, "TEST-2d", data)
    try:
        r = sess.get(f"{BASE_URL}/studies/{sid}/export/docx")
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        z = zipfile.ZipFile(io.BytesIO(r.content))
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        # Textos representativos de la sección construccion
        low = xml.lower()
        assert "reacci" in low or "2.1.4" in xml, "sección de reacción al fuego ausente"
        assert "medianer" in low or "2.2.1" in xml, "sección de medianerías ausente"
        assert "fachada" in low or "2.2.2" in xml, "sección de fachada ausente"
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ==================================================================== #
# Regresión FASE 1: LRE fuera de Qs, sector CTE config '—'
# ==================================================================== #
def test_regresion_fase1_lre_y_cte(sess, project_id):
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [
            {"id": "s1", "nombre": "S-Ind", "tipo": "sector", "ambito": "industrial",
             "config": "C", "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0},
            {"id": "s2", "nombre": "S-CTE", "tipo": "sector", "ambito": "cte",
             "uso_cte": "Administrativo", "situacion": "sobre_rasante",
             "num_salidas": 2, "ra": 1.0, "altura_evacuacion": 3, "num_plantas": 1},
        ],
        "dependencias": [
            {"id": "d1", "nombre": "Nave", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 500, "ci": 1.0},
            {"id": "d2", "nombre": "LRE", "clase": "lre", "sector_id": "s1",
             "sup_util": 30, "sup_construida": 30, "modo": "produccion",
             "qsi": 200, "ci": 1.0, "lre_uso": "Salas de calderas",
             "lre_metric": "P", "lre_potencia": 150, "lre_riesgo": "bajo", "lre_r": "R 90"},
            {"id": "d3", "nombre": "Ofi", "clase": "estancia", "sector_id": "s2",
             "sup_util": 80, "sup_construida": 80, "modo": "produccion",
             "qsi": 300, "ci": 1.0, "uso_ocupacion": "administrativo", "densidad": 10},
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-reg-p1", data)
    try:
        # LRE excluido de zonas
        sec_ind = next(s for s in res["sectores"] if s["nombre"] == "S-Ind")
        nombres = [z.get("descripcion") for z in sec_ind["calculo"]["zonas"]]
        assert "LRE" not in nombres
        assert float(sec_ind["calculo"]["A"]) == 100.0

        # Sector CTE con config '—' en resumen
        by_name = {f["nombre"]: f for f in res["resumen_sectores"]}
        assert by_name["S-CTE"]["config"] == "—"

        # Export DOCX regresión
        r = sess.get(f"{BASE_URL}/studies/{sid}/export/docx")
        assert r.status_code == 200
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")
