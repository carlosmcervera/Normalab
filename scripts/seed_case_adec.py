"""Crea el expediente PR26099 - Ejemplo ADEC (caso del PDF) para verificar el fix CTE."""
import os, requests, math

API = os.environ.get("API") or "http://localhost:8001"
s = requests.Session()
s.post(f"{API}/api/auth/login", json={"email": "admin@normalab.com", "password": "Admin1234!"})

# Sectores: (key, nombre, ambito, extras)
sectores = [
    {"id": "taller", "nombre": "SECTOR TALLER Y MANTENIMIENTO CAMIONES", "ambito": "industrial",
     "config": "AH", "situacion": "sobre_rasante", "num_salidas": 2, "altura_evacuacion": 0, "ra": 1.4},
    {"id": "ofi", "nombre": "SECTOR OFICINES > 250 m2", "ambito": "cte", "uso_cte": "Administrativo",
     "situacion": "sobre_rasante", "num_salidas": 2, "altura_evacuacion": 7},
    {"id": "lre", "nombre": "LOCAL DE RIESGO ESPECIAL", "ambito": "cte", "uso_cte": "Administrativo",
     "situacion": "sobre_rasante", "num_salidas": 1, "altura_evacuacion": 7},
]

# (nombre, planta, sector, sup_util, sup_construida, modo, qsi, ci, densidad|None, uso, sin_ocup, clase)
R = [
    ("ZONA DE MANTENIMIENTO DE CAMIONES", "Planta Baja", "taller", 842.41, 875.60, "produccion", 400, 1.44, None, "Taller / laboratorio", True, None),
    ("ALMACÉN RECAMBIOS", "Planta Baja", "taller", 6.88, 7.15, "produccion", 800, 1.44, 40, "Almacén / archivo", False, None),
    ("ALMACÉN TOPOGRÁFICO", "Planta Baja", "taller", 6.67, 6.93, "produccion", 800, 1.44, 40, "Almacén / archivo", False, None),
    ("ALMACÉN EPIS", "Planta Baja", "taller", 6.68, 6.94, "produccion", 800, 1.44, 40, "Almacén / archivo", False, None),
    ("ZONA TALLER MECÁNICO", "Planta Baja", "taller", 160.81, 167.15, "produccion", 400, 1.44, None, "Taller / laboratorio", True, None),
    ("ALMACÉN 1", "Planta Baja", "taller", 33.80, 35.13, "produccion", 800, 1.44, 40, "Almacén / archivo", False, None),
    # Oficinas planta baja
    ("PASILLO PB", "Planta Baja", "ofi", 13.80, 14.34, "produccion", 425, 1.0, None, "Sin ocupación", True, None),
    ("ASEOS", "Planta Baja", "ofi", 9.07, 9.43, "produccion", 425, 1.0, 3, "Aseos de planta", False, None),
    ("SANITARIO MOVILIDAD REDUCIDA", "Planta Baja", "ofi", 6.25, 6.50, "produccion", 425, 1.0, 3, "Aseos de planta", False, None),
    ("VESTUARIOS", "Planta Baja", "ofi", 25.85, 26.87, "produccion", 425, 1.0, None, "Sin ocupación", True, None),
    ("ESCALERA 1 PB", "Planta Baja", "ofi", 10.20, 10.60, "produccion", 0, 1.0, None, "Sin ocupación", True, "escalera"),
    ("ESCALERA 2 / ASCENSOR PB", "Planta Baja", "ofi", 15.55, 8.08, "produccion", 0, 1.0, None, "Sin ocupación", True, "escalera"),
    # Oficinas planta 1
    ("COMEDOR", "Planta 1", "ofi", 46.80, 50.44, "produccion", 425, 1.0, None, "Sin ocupación", True, None),
    ("ESCALERA 1 P1", "Planta 1", "ofi", 10.20, 10.99, "produccion", 0, 1.0, None, "Sin ocupación", True, "escalera"),
    ("ESCALERA 2 / ASCENSOR P1", "Planta 1", "ofi", 15.55, 16.76, "produccion", 0, 1.0, None, "Sin ocupación", True, "escalera"),
    # Oficinas planta 2
    ("VESTÍBULO 2", "Planta 2", "ofi", 12.05, 12.94, "produccion", 425, 1.0, None, "Sin ocupación", True, None),
    ("DESPACHO 1", "Planta 2", "ofi", 11.10, 11.92, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("SALA DE REUNIONES", "Planta 2", "ofi", 19.00, 20.40, "produccion", 425, 1.0, 2, "Zona de ventas (comercial)", False, None),
    ("PASILLO P2", "Planta 2", "ofi", 40.60, 43.59, "produccion", 425, 1.0, None, "Sin ocupación", True, None),
    ("DESPACHO ADMINISTRACIÓN", "Planta 2", "ofi", 35.97, 38.62, "produccion", 1000, 1.0, 10, "Despacho / administrativo", False, None),
    ("DESPACHO JEFE ADMINISTRACIÓN", "Planta 2", "ofi", 9.93, 10.66, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("DESPACHO TOPOGRAFÍA", "Planta 2", "ofi", 32.10, 34.46, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("VESTÍBULO ASEOS", "Planta 2", "ofi", 3.62, 3.89, "produccion", 425, 1.0, 3, "Aseos de planta", False, None),
    ("ASEO MUJERES", "Planta 2", "ofi", 5.67, 6.09, "produccion", 425, 1.0, 3, "Aseos de planta", False, None),
    ("ASEO HOMBRES", "Planta 2", "ofi", 7.00, 7.52, "produccion", 425, 1.0, 3, "Aseos de planta", False, None),
    ("DESPACHO DIRECCIÓN", "Planta 2", "ofi", 35.00, 37.00, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("DESPACHO 2", "Planta 2", "ofi", 20.45, 21.96, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("DESPACHO 3", "Planta 2", "ofi", 25.20, 27.06, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("DESPACHO 4", "Planta 2", "ofi", 12.10, 12.99, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("DESPACHO 5", "Planta 2", "ofi", 15.90, 17.07, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("DESPACHO 6", "Planta 2", "ofi", 21.20, 22.76, "produccion", 1000, 1.0, 10, "Despacho", False, None),
    ("VESTÍBULO 1", "Planta 2", "ofi", 6.86, 7.37, "produccion", 425, 1.0, None, "Sin ocupación", True, None),
    ("ESCALERA 1 P2", "Planta 2", "ofi", 10.20, 10.95, "produccion", 0, 1.0, None, "Sin ocupación", True, "escalera"),
    ("ESCALERA 2 / ASCENSOR P2", "Planta 2", "ofi", 15.50, 16.64, "produccion", 0, 1.0, None, "Sin ocupación", True, "escalera"),
    # LRE
    ("ZONA DEPÓSITO GASOIL Y CALDERA", "Planta Baja", "lre", 7.40, 7.69, "almacenamiento", 0, 1.0, 40, "Almacén / archivo", False, "lre"),
    ("ARCHIVO", "Planta 2", "lre", 38.65, 41.50, "almacenamiento", 0, 1.0, 40, "Almacén / archivo", False, "lre"),
    ("SERVIDORES", "Planta 2", "lre", 6.90, 7.41, "almacenamiento", 0, 1.0, 40, "Almacén / archivo", False, "lre"),
]

deps = []
for i, (n, pl, sk, su, sc, modo, qsi, ci, dens, uso, sinocup, clase) in enumerate(R):
    d = {"id": f"d{i}", "nombre": n, "planta": pl, "sector_id": sk,
         "sup_util": su, "sup_construida": sc, "modo": modo, "qsi": qsi, "ci": ci,
         "uso_ocupacion": uso, "sin_ocupacion": sinocup}
    if dens is not None:
        d["densidad"] = dens
    if clase:
        d["clase"] = clase
    if clase == "escalera":
        d["esc_tipo"] = "protegida"; d["esc_sentido"] = "descendente"
        d["esc_uso"] = "Administrativo/Docente"; d["esc_altura_evac"] = 7; d["esc_anchura"] = 1.2
    if clase == "lre":
        d["lre_uso"] = "combustibles"; d["lre_volumen"] = 150
    deps.append(d)

plantas = [{"id": "pb", "nombre": "Planta Baja"}, {"id": "p1", "nombre": "Planta 1"}, {"id": "p2", "nombre": "Planta 2"}]
data = {"establecimiento": {"actividad": "Taller y oficinas", "config": "C"},
        "plantas": plantas, "sectores": sectores, "dependencias": deps}

pr = s.post(f"{API}/api/projects", json={"code": "PR26099", "name": "Ejemplo ADEC", "client": "ADEC"}).json()
pid = pr["id"]
st = s.post(f"{API}/api/studies", json={"project_id": pid, "module_code": "INCENDIOS", "name": "Estudio de incendios"}).json()
sid = st["id"]
s.put(f"{API}/api/studies/{sid}", json={"data": data})
res = s.post(f"{API}/api/studies/{sid}/compute").json()
print("PROJECT:", pid, "STUDY:", sid)
for sec in res["results"]["sectores"]:
    print(f"  {sec['nombre'][:35]:35} ámbito={sec['ambito']:10} estab={sec['requisitos']['estabilidad']['valor']:6} "
          f"maxbase={sec['sectorizacion'].get('max_admisible_base')} estado={sec['estado']}")
