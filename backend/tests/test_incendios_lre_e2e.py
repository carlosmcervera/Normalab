"""E2E tests for LRE (Locales de Riesgo Especial · Tabla 2.1 CTE DB-SI).

Verifica:
  - compute() surfacea sector.locales_riesgo_especial con uso, uso_grupo,
    altura, volumen (metric V), potencia (metric P), metric, criterio, riesgo,
    resistencia, superficie, justificacion.
  - LRE por VOLUMEN: superficie 60 m² × altura 5 m → V=300 m³ → MEDIO · R 120.
  - LRE por POTENCIA (salas de calderas): P=150 → BAJO · R90, P=400 → MEDIO · R120,
    P=800 → ALTO · R180.
  - LRE incluido en calculo.zonas (computa carga de fuego) y suma al Qs del sector.
  - Escaleras NO computan carga de fuego (no aparece en zonas).
  - GET /api/studies/{id}/export/docx devuelve 200 y contiene 'LRE' + uso/vol/crit.
"""
import os
import io
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
    r = sess.post(f"{BASE_URL}/projects", json={"code": "TEST-LRE-1", "name": "TEST-LRE-1", "description": "LRE e2e"})
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    pid = r.json().get("id")
    yield pid
    try:
        sess.delete(f"{BASE_URL}/projects/{pid}")
    except Exception:
        pass


def _mk_study(sess, project_id, dependencias):
    """Crear estudio incendios con 1 sector y las dependencias indicadas."""
    payload = {"project_id": project_id, "module_code": "INCENDIOS", "name": "TEST LRE"}
    r = sess.post(f"{BASE_URL}/studies", json=payload)
    assert r.status_code in (200, 201), f"create: {r.status_code} {r.text[:400]}"
    sid = r.json()["id"]
    # asignar sector_id a las dependencias
    deps = [{**d, "sector_id": "s1"} for d in dependencias]
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [{"id": "s1", "nombre": "S1", "tipo": "sector", "ambito": "industrial",
                       "config": "C", "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0}],
        "dependencias": deps,
    }
    r2 = sess.put(f"{BASE_URL}/studies/{sid}", json={"data": data})
    assert r2.status_code == 200, f"put: {r2.status_code} {r2.text[:400]}"
    r3 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r3.status_code == 200, f"compute: {r3.status_code} {r3.text[:400]}"
    body = r3.json()
    # el compute puede devolver {results: {...}} o directamente los results
    return sid, body.get("results", body)


# -------------------------- LRE por VOLUMEN --------------------------- #
def test_lre_by_volume_medio(sess, project_id):
    deps = [
        {
            "id": "d1", "nombre": "Archivo",
            "clase": "lre",
            "sup_util": 60, "sup_construida": 60,
            "qsi": 1600, "ci": 1.20,
            "modo": "almacen",
            "lre_uso": "Talleres de mantenimiento, almacenes de elementos combustibles (mobiliario, lencería, limpieza, etc.), archivos de documentos, depósitos de libros, etc.",
            "lre_uso_grupo": "En cualquier edificio o establecimiento",
            "lre_metric": "V",
            "lre_altura": 5,
            "lre_valor": 300,
            "lre_riesgo": "medio",
            "lre_r": "R 120",
            "lre_criterio": "100<V≤200 bajo · 200<V≤400 medio · V>400 alto",
        }
    ]
    sid, res = _mk_study(sess, project_id, deps)
    sec = res["sectores"][0]
    lres = sec.get("locales_riesgo_especial") or []
    assert len(lres) == 1
    l = lres[0]
    assert l["uso"].startswith("Talleres")
    assert l["uso_grupo"] == "En cualquier edificio o establecimiento"
    assert l["metric"] == "V"
    assert float(l["altura"]) == 5
    assert float(l["volumen"]) == 300.0
    assert l["riesgo"].upper() == "MEDIO"
    assert l["resistencia"] == "R 120"
    assert "V" in l["criterio"]
    assert float(l["superficie"]) == 60.0

    # LRE computa carga (aparece en zonas y suma Qs)
    calc = sec.get("calculo") or {}
    zonas = calc.get("zonas") or []
    assert any(z.get("descripcion") == "Archivo" for z in zonas), f"LRE debe estar en zonas: {[z.get('descripcion') for z in zonas]}"
    assert float(calc.get("qs_mj") or calc.get("qs") or 0) > 0

    sess.delete(f"{BASE_URL}/studies/{sid}")


# ------------------------ LRE por POTENCIA (calderas) ------------------------ #
@pytest.mark.parametrize("potencia,esperado,r_esperado", [
    (150, "BAJO", "R 90"),
    (400, "MEDIO", "R 120"),
    (800, "ALTO", "R 180"),
])
def test_lre_by_power_calderas(sess, project_id, potencia, esperado, r_esperado):
    riesgo_lc = esperado.lower()
    deps = [
        {
            "id": "d1", "nombre": "Sala calderas",
            "clase": "lre",
            "sup_util": 40, "sup_construida": 40,
            "qsi": 200, "ci": 1.0, "modo": "produccion",
            "lre_uso": "Salas de calderas con potencia útil nominal P",
            "lre_uso_grupo": "En cualquier edificio o establecimiento",
            "lre_metric": "P",
            "lre_potencia": potencia,
            "lre_valor": potencia,
            "lre_riesgo": riesgo_lc,
            "lre_r": r_esperado,
            "lre_criterio": "70<P≤200 bajo · 200<P≤600 medio · P>600 alto",
        }
    ]
    sid, res = _mk_study(sess, project_id, deps)
    sec = res["sectores"][0]
    l = sec["locales_riesgo_especial"][0]
    assert l["metric"] == "P"
    assert float(l["potencia"]) == potencia
    assert l["volumen"] is None
    assert l["riesgo"] == esperado
    assert l["resistencia"] == r_esperado
    sess.delete(f"{BASE_URL}/studies/{sid}")


# ----------------------- Escaleras NO computan carga ----------------------- #
def test_escaleras_no_computan(sess, project_id):
    deps = [
        {"id": "e1", "nombre": "Esc1", "clase": "escalera",
         "sup_util": 20, "sup_construida": 20,
         "esc_tipo": "protegida", "esc_sentido": "descendente",
         "esc_situacion": "interior"},
        {"id": "d1", "nombre": "Prod", "clase": "estancia",
         "sup_util": 100, "sup_construida": 100, "modo": "produccion",
         "qsi": 700, "ci": 1.44},
    ]
    sid, res = _mk_study(sess, project_id, deps)
    sec = res["sectores"][0]
    calc = sec.get("calculo") or {}
    nombres = [z.get("descripcion") for z in (calc.get("zonas") or [])]
    assert "Esc1" not in nombres, f"escalera no debe computar: {nombres}"
    assert "Prod" in nombres
    escs = sec.get("escaleras_protegidas") or []
    assert len(escs) == 1
    sess.delete(f"{BASE_URL}/studies/{sid}")


# --------------------------- DOCX export ---------------------------- #
def test_docx_export_contains_lre(sess, project_id):
    deps = [
        {"id": "d1", "nombre": "ArchivoDocx", "clase": "lre",
         "sup_util": 60, "sup_construida": 60,
         "qsi": 1600, "ci": 1.20, "modo": "almacen",
         "lre_uso": "Talleres de mantenimiento, almacenes de elementos combustibles (mobiliario, lencería, limpieza, etc.), archivos de documentos, depósitos de libros, etc.",
         "lre_uso_grupo": "En cualquier edificio o establecimiento",
         "lre_metric": "V", "lre_altura": 5, "lre_valor": 300,
         "lre_riesgo": "medio", "lre_r": "R 120",
         "lre_criterio": "100<V≤200 bajo · 200<V≤400 medio · V>400 alto",
         "lre_justificacion": "Justif LRE archivo."}
    ]
    sid, _res = _mk_study(sess, project_id, deps)
    r = sess.get(f"{BASE_URL}/studies/{sid}/export/docx")
    assert r.status_code == 200, f"export docx: {r.status_code} {r.text[:200]}"
    assert r.headers.get("content-type", "").startswith("application/vnd.openxmlformats-officedocument"), r.headers
    # Abrir el DOCX (zip) y leer document.xml en busca de textos clave
    import zipfile
    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    assert "LRE" in xml
    assert "ArchivoDocx" in xml
    assert "300" in xml  # volumen
    assert "R 120" in xml
    # el uso puede estar troceado en runs; comprobamos una palabra estable
    assert "archivos" in xml.lower() or "archivo" in xml.lower()
    sess.delete(f"{BASE_URL}/studies/{sid}")
