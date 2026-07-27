"""E2E tests for the RSCIEI activity catalog (Tabla 1.3.5, RD 164/2025).

Verifica:
  - GET del schema del módulo INCENDIOS expone activity_catalog con 11 categorías
    A–K y >=150 subactividades. Estructura por categoría/subactividad.
  - Filas concretas del BOE (Oficinas, Archivos, Fábrica de papel: celulosa,
    Imprenta: Producción) tienen valores exactos.
  - Regresión: compute() sigue funcionando con actividad del catálogo
    (qsi=700, ci=1.44 → Qs > 0, NRI coherente).
"""
import os
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
ADMIN_EMAIL = "admin@normalab.com"
ADMIN_PWD = "Admin1234!"

EXPECTED_PREFIXES = [
    "A. OFICINAS",
    "B. CARTÓN",         # "B. CARTÓN, PAPEL"
    "C. INDUSTRIA ALIMENTARIA",
    "D. INDUSTRIA QUÍMICA",
    "E. LOGÍSTICA",
    "F. MATERIAS Y MERCANCÍAS DIVERSAS",
    "G. TEXTILES",
    "H. TRANSFORMACIÓN DE METALES",
    "I. TRANSFORMACIÓN DE PLÁSTICOS",
    "J. ARTÍCULOS DE MADERA",
    "K. OTROS",
]


@pytest.fixture(scope="module")
def sess():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PWD})
    assert r.status_code == 200, f"login: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    return s


# ------------------------------- Schema tests ------------------------------- #
@pytest.fixture(scope="module")
def schema(sess):
    # probar varias posibles rutas del schema del módulo
    r = sess.get(f"{BASE_URL}/modules/INCENDIOS/schema")
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    data = r.json()
    # response shape: {"meta": ..., "schema": {...}}
    if "schema" in data and "activity_catalog" in data["schema"]:
        return data["schema"]
    assert "activity_catalog" in data, f"No activity_catalog in response: {list(data.keys())}"
    return data


def test_activity_catalog_categories(schema):
    cat = schema["activity_catalog"]
    assert isinstance(cat, list)
    assert len(cat) == 11, f"expected 11 categories, got {len(cat)}"
    for i, expected in enumerate(EXPECTED_PREFIXES):
        assert cat[i]["category"].startswith(expected), \
            f"category[{i}] = {cat[i]['category']!r}, expected prefix {expected!r}"


def test_activity_catalog_total_subactivities(schema):
    cat = schema["activity_catalog"]
    total = sum(len(c["subactivities"]) for c in cat)
    assert total >= 150, f"expected >=150 subactivities, got {total}"


def test_activity_catalog_structure(schema):
    cat = schema["activity_catalog"]
    for c in cat:
        for s in c["subactivities"]:
            assert "name" in s and "modo" in s and "ci" in s
            if s["modo"] == "produccion":
                assert s.get("qsi", 0) > 0, f"prod {s['name']} qsi={s.get('qsi')}"
            else:
                assert s["modo"] == "almacenamiento"
                assert s.get("qvi", 0) > 0, f"alm {s['name']} qvi={s.get('qvi')}"


def _find_sub(cat, category_prefix, name_substr):
    for c in cat:
        if c["category"].startswith(category_prefix):
            for s in c["subactivities"]:
                if name_substr.lower() in s["name"].lower():
                    return s
    return None


def test_activity_row_oficinas(schema):
    s = _find_sub(schema["activity_catalog"], "A. OFICINAS", "Oficinas")
    assert s is not None
    assert s["modo"] == "produccion"
    assert s["qsi"] == 700
    assert s["ci"] == pytest.approx(1.44)
    assert s["rmin"] == pytest.approx(1.0)


def test_activity_row_archivos(schema):
    s = _find_sub(schema["activity_catalog"], "A. OFICINAS", "Archivos")
    assert s is not None
    assert s["modo"] == "almacenamiento"
    assert s["qvi"] == 1600
    assert s.get("qvi_neto") == 2100
    assert s["ci"] == pytest.approx(1.20)


def test_activity_row_papel_celulosa(schema):
    s = _find_sub(schema["activity_catalog"], "B. CARTÓN", "celulosa")
    assert s is not None, "No se encontró 'Fábrica de papel: Almacenamiento de materias primas (celulosa)'"
    assert s["modo"] == "almacenamiento"
    assert s["qvi"] == 20000
    assert s.get("qvi_neto") == 22000


def test_activity_row_imprenta_produccion(schema):
    # 'Imprenta: Producción' — nombre exacto para no matchear las variantes
    for c in schema["activity_catalog"]:
        if c["category"].startswith("B. CARTÓN"):
            for s in c["subactivities"]:
                if s["name"] == "Imprenta: Producción":
                    assert s["modo"] == "produccion"
                    assert s["qsi"] == 500
                    assert s["ci"] == pytest.approx(1.68)
                    assert s.get("ra") == pytest.approx(1.4)
                    return
    pytest.fail("Fila 'Imprenta: Producción' no encontrada")


# ------------------------------- Compute regression ------------------------- #
@pytest.fixture(scope="module")
def project(sess):
    r = sess.post(f"{BASE_URL}/projects", json={"code": "TEST-CAT-1", "name": "TEST Catálogo E2E"})
    if r.status_code >= 400:
        rl = sess.get(f"{BASE_URL}/projects")
        for p in rl.json():
            if p.get("code") == "TEST-CAT-1":
                return p
        pytest.fail(f"proj create: {r.status_code} {r.text}")
    return r.json()


@pytest.fixture(scope="module")
def study(sess, project):
    payload = {"project_id": project["id"], "module_code": "INCENDIOS", "name": "TEST Catálogo Oficinas"}
    r = sess.post(f"{BASE_URL}/studies", json=payload)
    assert r.status_code in (200, 201), f"studies POST: {r.status_code} {r.text}"
    st = r.json()
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [
            {"id": "s1", "nombre": "Nave", "tipo": "sector", "ambito": "industrial",
             "config": "C", "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0}
        ],
        "dependencias": [
            {"id": "d1", "sector_id": "s1", "nombre": "Oficinas",
             "sup_util": 100, "sup_construida": 110,
             "modo": "produccion",
             "actividad_cat": "A. OFICINAS", "subactividad": "Oficinas",
             "qsi": 700, "ci": 1.44, "ra": 1.0,
             "densidad": 10, "uso_ocupacion": "Oficinas / administrativo",
             "sin_ocupacion": False},
        ],
    }
    r2 = sess.put(f"{BASE_URL}/studies/{st['id']}", json={"data": data})
    assert r2.status_code == 200, r2.text
    return r2.json()


def test_compute_with_catalog_activity(sess, study):
    r = sess.post(f"{BASE_URL}/studies/{study['id']}/compute")
    assert r.status_code == 200, r.text
    body = r.json()
    results = body["results"]
    sec = results["sectores"][0]
    calc = sec["calculo"]
    assert calc["qs_mj"] > 0
    # Qs esperado ≈ 700 * 1.44 * 100 / 100 * 1.0 = 1008 MJ/m²
    assert calc["qs_mj"] == pytest.approx(1008.0, rel=1e-3)
    # NRI presente
    nri = sec.get("nri") or sec.get("nivel_riesgo") or calc.get("nri")
    assert nri, f"NRI missing in sector: {sec.keys()}"


def test_cleanup(sess, study, project):
    sess.delete(f"{BASE_URL}/studies/{study['id']}")
    sess.delete(f"{BASE_URL}/projects/{project['id']}")
