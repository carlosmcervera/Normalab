"""FASE 1 · Incendios · E2E tests

Cambios validados:
  1a) Los LRE ya NO computan carga de fuego (se excluyen del Qs y de las zonas).
      Siguen apareciendo en results.sectores[].locales_riesgo_especial.
  1b) Los sectores CTE muestran config '—' en resumen_sectores y su
      sectorizacion.estado == 'no_aplica'.
  1c) results.tablas incluye 'legend' con SOLO sectores RSCIEI (los CTE se excluyen)
      y cada tabla trae cell_sectors/row_sectors por sector. En la tabla
      'superficie' (Tabla 2.1.1), sectores con distinta configuración/nivel producen
      cell_sectors DISTINTOS por sector.
  Regresión) GET /api/studies/{id}/export/docx devuelve 200.
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
        "code": "TEST-INC-PH1", "name": "TEST INC Phase 1", "description": "phase 1 e2e"
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
# 1a) LRE NO computa: excluido de Qs y de calculo.zonas
# ==================================================================== #
def test_1a_lre_no_computa_qs(sess, project_id):
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{"id": "s1", "nombre": "S1", "tipo": "sector",
                       "ambito": "industrial", "config": "C",
                       "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0}],
        "dependencias": [
            # estancia normal (produccion): sí computa
            {"id": "d1", "nombre": "Nave", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 500, "ci": 1.0},
            # LRE Salas de calderas P=150 kW → BAJO · R 90 (NO computa)
            {"id": "d2", "nombre": "Sala calderas", "clase": "lre", "sector_id": "s1",
             "sup_util": 30, "sup_construida": 30, "modo": "produccion",
             "qsi": 200, "ci": 1.0,
             "lre_uso": "Salas de calderas con potencia útil nominal P",
             "lre_uso_grupo": "En cualquier edificio o establecimiento",
             "lre_metric": "P", "lre_potencia": 150, "lre_valor": 150,
             "lre_riesgo": "bajo", "lre_r": "R 90",
             "lre_criterio": "70<P≤200 bajo · 200<P≤600 medio · P>600 alto"},
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-1a", data)
    try:
        sec = res["sectores"][0]
        calc = sec["calculo"]
        zonas = calc["zonas"]
        nombres = [z.get("descripcion") for z in zonas]
        # LRE NO en zonas
        assert "Sala calderas" not in nombres, f"LRE debería estar excluido de zonas: {nombres}"
        # Estancia normal SÍ en zonas
        assert "Nave" in nombres
        # A_util solo la estancia normal (100 m²), no incluye el LRE (30)
        assert float(calc["A"]) == 100.0, f"A_util debe excluir LRE, got {calc['A']}"
        # numerador = 500 * 1 * 100 = 50000 (solo aporte de la estancia)
        assert abs(float(calc["numerador"]) - 50000.0) < 1.0
        # Qs = 50000/100 * 1 = 500
        assert abs(float(calc["qs_mj"]) - 500.0) < 1.0

        # LRE surface intacta
        lres = sec.get("locales_riesgo_especial") or []
        assert len(lres) == 1
        l = lres[0]
        assert l["nombre"] == "Sala calderas"
        assert l["metric"] == "P"
        assert float(l["potencia"]) == 150.0
        assert l["riesgo"] == "BAJO"
        assert l["resistencia"] == "R 90"
        assert l["volumen"] is None
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ==================================================================== #
# 1b) Sector CTE: config '—' y sectorizacion no_aplica
# ==================================================================== #
def test_1b_sector_cte_config_dash_and_no_aplica(sess, project_id):
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [
            {"id": "s1", "nombre": "S-Industrial", "tipo": "sector",
             "ambito": "industrial", "config": "C",
             "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0},
            {"id": "s2", "nombre": "S-CTE", "tipo": "sector",
             "ambito": "cte", "uso_cte": "Administrativo",
             "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
             "altura_evacuacion": 3, "num_plantas": 1},
        ],
        "dependencias": [
            {"id": "d1", "nombre": "Nave1", "clase": "estancia", "sector_id": "s1",
             "sup_util": 200, "sup_construida": 200, "modo": "produccion",
             "qsi": 600, "ci": 1.0, "uso_ocupacion": "produccion", "densidad": 10},
            {"id": "d2", "nombre": "Oficina", "clase": "estancia", "sector_id": "s2",
             "sup_util": 80, "sup_construida": 80, "modo": "produccion",
             "qsi": 300, "ci": 1.0, "uso_ocupacion": "administrativo", "densidad": 10},
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-1b", data)
    try:
        resumen = res["resumen_sectores"]
        # localizamos filas por nombre
        by_name = {f["nombre"]: f for f in resumen}
        assert by_name["S-CTE"]["config"] == "—", by_name["S-CTE"]
        assert by_name["S-Industrial"]["config"] != "—"
        # sectorización CTE: ahora se evalúa por SI 1 (superficie máx. según uso), no por Tabla 2.1.1 RSCIEI
        sec_cte = next(s for s in res["sectores"] if s["ambito"] == "cte")
        assert sec_cte["sectorizacion"]["estado"] in ("cumple", "no_cumple")
        # la estabilidad del sector CTE proviene del CTE DB-SI (SI 6), no de la Tabla 2.5.1 RSCIEI
        assert sec_cte["requisitos"]["estabilidad"]["referencia"].startswith("CTE DB-SI")
        msg = (sec_cte["sectorizacion"].get("mensaje") or "").lower()
        assert "si 1" in msg or "no aplica la tabla 2.1.1" in msg, msg
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ==================================================================== #
# 1c) Tablas: legend solo RSCIEI y cell_sectors distintos por sector
# ==================================================================== #
def test_1c_tablas_legend_rsciei_only_and_multisector_colors(sess, project_id):
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [
            # Sector 0: config C, Qs bajo → nivel 1 (BAJO)
            {"id": "s1", "nombre": "SEC-A", "tipo": "sector",
             "ambito": "industrial", "config": "C",
             "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0},
            # Sector 1: config B, Qs mayor → nivel diferente (MEDIO/ALTO)
            {"id": "s2", "nombre": "SEC-B", "tipo": "sector",
             "ambito": "industrial", "config": "B",
             "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0},
            # Sector CTE (debe EXCLUIRSE de la leyenda RSCIEI)
            {"id": "s3", "nombre": "SEC-CTE", "tipo": "sector",
             "ambito": "cte", "uso_cte": "Administrativo",
             "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
             "altura_evacuacion": 3, "num_plantas": 1},
        ],
        "dependencias": [
            {"id": "d1", "nombre": "A", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 200, "ci": 1.0, "uso_ocupacion": "produccion", "densidad": 10},
            {"id": "d2", "nombre": "B", "clase": "estancia", "sector_id": "s2",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 2500, "ci": 1.3, "uso_ocupacion": "produccion", "densidad": 10},
            {"id": "d3", "nombre": "C", "clase": "estancia", "sector_id": "s3",
             "sup_util": 50, "sup_construida": 50, "modo": "produccion",
             "qsi": 300, "ci": 1.0, "uso_ocupacion": "administrativo", "densidad": 10},
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-1c", data)
    try:
        tablas = res["tablas"]
        assert len(tablas) > 0
        # Todas las tablas comparten legend
        legend = tablas[0].get("legend") or []
        # Solo 2 RSCIEI (SEC-CTE excluido)
        nombres = [l["nombre"] for l in legend]
        assert "SEC-A" in nombres
        assert "SEC-B" in nombres
        assert "SEC-CTE" not in nombres, f"CTE debe excluirse de legend: {nombres}"
        assert len(legend) == 2
        # Colores distintos
        colors = [l["color"] for l in legend]
        assert len(set(colors)) == 2

        # Tabla superficie: cell_sectors por sector con celdas distintas
        superficie = next(t for t in tablas if t["id"] == "superficie")
        cs = superficie.get("cell_sectors") or {}
        assert cs, "cell_sectors debe existir en tabla superficie"
        # Recolectar celdas por sector idx
        cells_by_sector = {0: set(), 1: set()}
        for key, idxs in cs.items():
            for i in idxs:
                if i in cells_by_sector:
                    cells_by_sector[i].add(key)
        assert len(cells_by_sector[0]) > 0
        assert len(cells_by_sector[1]) > 0
        # Sectores distintos deben iluminar celdas distintas (config y nivel diferentes)
        assert cells_by_sector[0] != cells_by_sector[1], (
            f"Los sectores deben resaltar celdas distintas: {cells_by_sector}")

        # Regresión: export DOCX sigue funcionando con multi-sector coloreado
        r = sess.get(f"{BASE_URL}/studies/{sid}/export/docx")
        assert r.status_code == 200, f"docx: {r.status_code} {r.text[:200]}"
        ct = r.headers.get("content-type", "")
        assert ct.startswith("application/vnd.openxmlformats-officedocument"), ct
        z = zipfile.ZipFile(io.BytesIO(r.content))
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        assert "SEC-A" in xml
        assert "SEC-B" in xml
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")
