"""FASE 3 (fix) · Incendios · E2E — coherencia informe ↔ tablas.

Bug reportado: la R exigida y la superficie máxima en el detalle del sector no
coincidían con las celdas resaltadas de las tablas de referencia del informe.

Se verifica:
  3a) results.sectores[].requisitos.estabilidad.valor = ESTABILIDAD[cfg][sit][cat] SIN
      modulación por altura_evacuacion (h=10/20/40 producen el mismo valor).
  3b) bajo_rasante usa la columna 'bajo'.
  3c) sectorizacion.max_admisible_base = MAX_SURFACE[cfg][nivel] (sin factores).
  3d) Con rociadores=True el mensaje cita '×2' y max_admisible == base*2, base intacto.
  3e) Coherencia tabla↔informe: cell_sectors resaltado en 'estabilidad' contiene el
      mismo string que requisitos.estabilidad.valor, y en 'superficie' el mismo número
      que sectorizacion.max_admisible_base.
  3f) medianera_otro=True + medianera_ei debajo del requerido → sector.estado='no_cumple'
      y observación 'error'.
  3g) Regresión: schema 5 pasos y export DOCX 200.
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
        "code": "TEST-INC-PH3", "name": "TEST INC Phase 3", "description": "phase 3 e2e"
    })
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    pid = r.json().get("id")
    yield pid
    try:
        sess.delete(f"{BASE_URL}/projects/{pid}")
    except Exception:
        pass


def _mk_study(sess, project_id, name, data):
    r = sess.post(f"{BASE_URL}/studies", json={
        "project_id": project_id, "module_code": "INCENDIOS", "name": name})
    assert r.status_code in (200, 201), r.text
    sid = r.json()["id"]
    r = sess.put(f"{BASE_URL}/studies/{sid}", json={"data": data})
    assert r.status_code == 200, r.text[:400]
    r2 = sess.post(f"{BASE_URL}/studies/{sid}/compute")
    assert r2.status_code == 200, r2.text[:400]
    return sid, r2.json().get("results", r2.json())


def _base_data(config="C", situacion="sobre_rasante", altura=0.0, qsi=300, ci=1.0,
               rociadores=False, fachada_accesible=False, medianera_otro=False,
               medianera_ei=""):
    return {
        "establecimiento": {"config": config},
        "sectores": [{
            "id": "s1", "nombre": "S", "tipo": "sector", "ambito": "industrial",
            "config": config, "situacion": situacion,
            "num_salidas": 2, "ra": 1.0,
            "altura_evacuacion": altura,
            "rociadores": rociadores,
            "fachada_accesible": fachada_accesible,
            "medianera_otro": medianera_otro,
            "medianera_ei": medianera_ei,
        }],
        "dependencias": [
            {"id": "d1", "nombre": "N", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": qsi, "ci": ci},
        ],
    }


# ============================================================== #
# 3a) R = valor base de la Tabla 2.5.1 sin bump por altura
# ============================================================== #
@pytest.mark.parametrize("altura", [5.0, 10.0, 20.0, 40.0])
def test_3a_estabilidad_no_bump_por_altura(sess, project_id, altura):
    # C · sobre_rasante · BAJO → R 30 (valor base)
    data = _base_data(config="C", situacion="sobre_rasante", altura=altura, qsi=300)
    sid, res = _mk_study(sess, project_id, f"TEST-3a-h{int(altura)}", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["categoria"] == "BAJO", sec["nivel_riesgo"]
        assert sec["requisitos"]["estabilidad"]["valor"] == "R 30", \
            f"altura {altura}: {sec['requisitos']['estabilidad']}"
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3b) bajo_rasante usa columna 'bajo'
# ============================================================== #
def test_3b_bajo_rasante_columna_bajo(sess, project_id):
    # C · bajo · BAJO → R 60
    data = _base_data(config="C", situacion="bajo_rasante", altura=0.0, qsi=300)
    sid, res = _mk_study(sess, project_id, "TEST-3b", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["categoria"] == "BAJO"
        assert sec["requisitos"]["estabilidad"]["valor"] == "R 60"
        assert sec["situacion"] == "bajo_rasante"
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3c) max_admisible_base = valor base de la Tabla 2.1.1 (sin factores)
# ============================================================== #
def test_3c_max_admisible_base_sin_factores(sess, project_id):
    # C nivel 1 (BAJO) → 'SIN LÍMITE'; usamos nivel 2 (Qs > 425): qsi=500, ci=1 → 500 → BAJO nivel 2
    # C nivel 2 base = 12000
    data = _base_data(config="C", situacion="sobre_rasante", qsi=500)
    sid, res = _mk_study(sess, project_id, "TEST-3c", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["nivel"] == 2, sec["nivel_riesgo"]
        sect = sec["sectorizacion"]
        assert sect["max_admisible_base"] == 12000, sect
        assert sect["max_admisible"] == 12000.0, sect  # sin factores
        # Mensaje cita valor base
        assert "12.000" in sect["mensaje"] or "12000" in sect["mensaje"], sect["mensaje"]
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3d) Rociadores × 2: base intacto y admisible = base*2
# ============================================================== #
def test_3d_rociadores_factor_x2(sess, project_id):
    data = _base_data(config="C", situacion="sobre_rasante", qsi=500, rociadores=True)
    sid, res = _mk_study(sess, project_id, "TEST-3d", data)
    try:
        sec = res["sectores"][0]
        sect = sec["sectorizacion"]
        assert sec["nivel_riesgo"]["nivel"] == 2
        assert sect["max_admisible_base"] == 12000
        assert sect["max_admisible"] == 24000.0, sect
        assert "×2" in sect["mensaje"] or "x2" in sect["mensaje"].lower() or "(×2)" in sect["mensaje"], sect["mensaje"]
        assert "rociadores" in sect["mensaje"].lower(), sect["mensaje"]
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3e) Coherencia tabla↔informe (estabilidad y superficie)
# ============================================================== #
def test_3e_coherencia_tabla_informe(sess, project_id):
    # 2 sectores RSCIEI con distintos NRI y config
    data = {
        "establecimiento": {"config": "C"},
        "sectores": [
            {"id": "s1", "nombre": "SA", "tipo": "sector", "ambito": "industrial",
             "config": "C", "situacion": "sobre_rasante", "num_salidas": 2, "ra": 1.0,
             "altura_evacuacion": 20},
            {"id": "s2", "nombre": "SB", "tipo": "sector", "ambito": "industrial",
             "config": "B", "situacion": "bajo_rasante", "num_salidas": 2, "ra": 1.0},
        ],
        "dependencias": [
            {"id": "d1", "nombre": "N1", "clase": "estancia", "sector_id": "s1",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 500, "ci": 1.0},  # BAJO nivel 2
            {"id": "d2", "nombre": "N2", "clase": "estancia", "sector_id": "s2",
             "sup_util": 100, "sup_construida": 100, "modo": "produccion",
             "qsi": 1500, "ci": 1.0},  # MEDIO nivel 4
        ],
    }
    sid, res = _mk_study(sess, project_id, "TEST-3e", data)
    try:
        tablas = {t["id"]: t for t in res["tablas"]}
        t_est = tablas["estabilidad"]
        t_sup = tablas["superficie"]

        # ---- ESTABILIDAD ----
        # Cabeceras: ["Riesgo", "AV sótano","AV s/rasante","AH sótano","AH s/rasante",
        #             "B sótano","B s/rasante","C sótano","C s/rasante"]
        # EST_COL: (C,sobre)=8, (B,bajo)=5
        # cat_row: BAJO=0, MEDIO=1
        for sec in res["sectores"]:
            cat = sec["nivel_riesgo"]["categoria"]
            row = {"BAJO": 0, "MEDIO": 1, "ALTO": 2}[cat]
            sitk = "bajo" if sec["situacion"] == "bajo_rasante" else "sobre"
            col_map = {("AV", "bajo"): 1, ("AV", "sobre"): 2, ("AH", "bajo"): 3, ("AH", "sobre"): 4,
                       ("B", "bajo"): 5, ("B", "sobre"): 6, ("C", "bajo"): 7, ("C", "sobre"): 8}
            col = col_map[(sec["config"], sitk)]
            cell_str = t_est["rows"][row][col]
            # Coincide con el requisito del informe
            assert sec["requisitos"]["estabilidad"]["valor"] == cell_str, \
                f"sector {sec['nombre']}: informe={sec['requisitos']['estabilidad']['valor']} celda={cell_str}"
            # cell_sectors resalta esa celda para el sector
            key = f"{row}-{col}"
            assert key in t_est["cell_sectors"], f"celda {key} no resaltada en estabilidad"

        # ---- SUPERFICIE ----
        # Headers: ["Nivel","Tipo AV","Tipo AH","Tipo B","Tipo C"] → C=col 4, B=col 3
        for sec in res["sectores"]:
            nivel = sec["nivel_riesgo"]["nivel"]
            col = {"AV": 1, "AH": 2, "B": 3, "C": 4}[sec["config"]]
            cell_str = t_sup["rows"][nivel - 1][col]  # string formateado "12.000"
            base = sec["sectorizacion"]["max_admisible_base"]
            # base puede ser un número; comparamos con formato de _fmt (miles con punto)
            if isinstance(base, (int, float)):
                expected_str = f"{int(base):,}".replace(",", ".")
                assert cell_str == expected_str, f"sector {sec['nombre']}: celda={cell_str} base={expected_str}"
            key = f"{nivel - 1}-{col}"
            assert key in t_sup["cell_sectors"], f"celda {key} no resaltada en superficie"
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3e-bis) bajo_rasante · nivel 5 · B → max_admisible_base = tabla, max_admisible = base/2
# ============================================================== #
def test_3e_bis_bajo_rasante_base_es_tabla_pura(sess, project_id):
    # B, bajo_rasante, qsi que caiga en nivel 5 (MEDIO): 1700 <= Qs < 3400
    # qsi=2000, ci=1 -> Qs=2000 (nivel 5, MEDIO). MAX_SURFACE['B'][5]=5000.
    data = _base_data(config="B", situacion="bajo_rasante", qsi=2000)
    sid, res = _mk_study(sess, project_id, "TEST-3e-bis", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["nivel"] == 5, sec["nivel_riesgo"]
        sect = sec["sectorizacion"]
        # base = valor puro tabla (5000), NO 2500
        assert sect["max_admisible_base"] == 5000, sect
        # max_admisible = base * 0.5 = 2500
        assert sect["max_admisible"] == 2500.0, sect
        # Mensaje cita 'bajo rasante' con ÷ 2 y admisible final 2500
        msg = sect["mensaje"]
        assert "bajo rasante" in msg.lower(), msg
        assert "÷ 2" in msg or "/2" in msg or "÷2" in msg, msg
        # Coincide con celda resaltada tabla 2.1.1 (fila nivel-1=4, col B=3)
        t_sup = {t["id"]: t for t in res["tablas"]}["superficie"]
        cell = t_sup["rows"][4][3]
        assert cell == "5.000", cell
        assert "4-3" in t_sup["cell_sectors"], t_sup["cell_sectors"]
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3e-ter) bajo_rasante + rociadores + fachada → base intacto, factores combinados
# ============================================================== #
def test_3e_ter_bajo_rasante_con_factores_combinados(sess, project_id):
    # C, bajo_rasante, qsi=500 -> nivel 2 (BAJO). MAX_SURFACE['C'][2]=12000
    # rociadores(x2) + fachada(x1.25) + bajo_rasante(/2) -> 12000 * 2 * 1.25 * 0.5 = 15000
    data = _base_data(config="C", situacion="bajo_rasante", qsi=500,
                      rociadores=True, fachada_accesible=True)
    sid, res = _mk_study(sess, project_id, "TEST-3e-ter", data)
    try:
        sec = res["sectores"][0]
        sect = sec["sectorizacion"]
        assert sect["max_admisible_base"] == 12000, sect
        assert sect["max_admisible"] == 15000.0, sect
        aplicados = " | ".join(sect.get("factores_aplicados") or [])
        assert "Rociadores" in aplicados and "Fachada" in aplicados and "bajo rasante" in aplicados.lower(), aplicados
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")



# ============================================================== #
# 3f) medianera no cumple → sector.estado='no_cumple'
# ============================================================== #
def test_3f_medianera_no_cumple_degrada_estado(sess, project_id):
    # MEDIO: qsi=1500 → NRI MEDIO nivel 4. Requerido EI 180, proyectado EI 120 → no_cumple
    data = _base_data(config="C", situacion="sobre_rasante", qsi=1500,
                      medianera_otro=True, medianera_ei="EI 120")
    sid, res = _mk_study(sess, project_id, "TEST-3f", data)
    try:
        sec = res["sectores"][0]
        assert sec["nivel_riesgo"]["categoria"] == "MEDIO"
        med = sec["construccion"]["medianeras"]
        assert med["estado"] == "no_cumple"
        assert sec["estado"] == "no_cumple", sec["estado"]
        errs = [o for o in sec["observaciones"] if o.get("tipo") == "error"]
        assert any("medianer" in (o.get("texto") or "").lower() for o in errs), errs
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")


# ============================================================== #
# 3g) Regresión: schema 5 pasos + export DOCX 200
# ============================================================== #
def test_3g_schema_and_docx(sess, project_id):
    r = sess.get(f"{BASE_URL}/modules/INCENDIOS/schema")
    assert r.status_code == 200
    schema = r.json().get("schema") or r.json()
    types = [s.get("type") for s in schema.get("steps") or []]
    assert types == ["superficies_proyecto", "ocupacion", "sectores_incendio",
                     "construccion", "evacuacion"], types

    data = _base_data(config="C", situacion="sobre_rasante", qsi=500)
    sid, _res = _mk_study(sess, project_id, "TEST-3g", data)
    try:
        r = sess.get(f"{BASE_URL}/studies/{sid}/export/docx")
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    finally:
        sess.delete(f"{BASE_URL}/studies/{sid}")
