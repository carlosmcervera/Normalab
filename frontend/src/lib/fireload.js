// Cálculo en vivo de la carga de fuego (réplica del motor RSCIEI en el frontend)
// para mostrar Qs/NRI por sector y el aporte por estancia antes de calcular.
const NRI_TABLE = [
  [1, 0, 425, "BAJO"], [2, 425, 850, "BAJO"], [3, 850, 1275, "MEDIO"],
  [4, 1275, 1700, "MEDIO"], [5, 1700, 3400, "MEDIO"], [6, 3400, 6800, "ALTO"],
  [7, 6800, 13600, "ALTO"], [8, 13600, Infinity, "ALTO"],
];

export function nriFor(qs) {
  for (const [nivel, low, high, cat] of NRI_TABLE) {
    if ((qs > low && qs <= high) || (nivel === 1 && qs <= high)) return { nivel, categoria: cat };
  }
  return { nivel: 8, categoria: "ALTO" };
}

// Aporte de una estancia en MJ (producción: qs·Ci·S ; almacenamiento: qv·Ci·hi·S ;
// depósito de combustible: PCI·densidad·volumen·Ci). Superficie = útil (fallback construida).
export function depAporte(d) {
  const ci = Number(d.ci) || 0;
  const s = Number(d.sup_util) || Number(d.sup_construida) || 0;
  if (!ci) return null;
  if (d.modo === "deposito") {
    const pci = Number(d.pci) || 0;
    const dens = Number(d.dens_comb) || 0;
    const vol = Number(d.volumen) || 0;
    if (!pci || !dens || !vol) return null;
    return pci * dens * vol * ci;
  }
  if (!s) return null;
  if (d.modo === "almacenamiento") {
    const qvi = Number(d.qvi) || 0;
    const hi = Number(d.hi) || 0;
    if (!qvi || !hi) return null;
    return qvi * ci * hi * s;
  }
  const qsi = Number(d.qsi) || 0;
  if (!qsi) return null;
  return qsi * ci * s;
}

// Carga de fuego del sector a partir de sus estancias asignadas (escaleras y locales
// de riesgo especial excluidos: no computan carga de fuego).
export function sectorCarga(deps) {
  const calc = deps.filter((d) => d.clase !== "escalera" && d.clase !== "escalera_protegida" && d.clase !== "lre" && !d.es_lre);
  const A = calc.reduce((a, d) => a + (Number(d.sup_util) || Number(d.sup_construida) || 0), 0);
  let numerador = 0;
  const ras = [];
  for (const d of calc) {
    const ap = depAporte(d);
    if (ap == null) continue;
    numerador += ap;
    ras.push(Number(d.ra) || 1);
  }
  const ra = ras.length ? Math.max(...ras) : 1;
  const qs = A > 0 ? (numerador / A) * ra : 0;
  const { nivel, categoria } = nriFor(qs);
  return { A, numerador, ra, qs, nivel, categoria, hasData: numerador > 0 && A > 0 };
}

// Ocupación de una estancia (techo(sup útil / densidad) o manual).
export function depOcupacion(d) {
  if (d.sin_ocupacion) return 0;
  if (d.ocupacion_custom) {
    const m = Number(d.ocupacion_manual);
    return d.ocupacion_manual === "" || d.ocupacion_manual == null || Number.isNaN(m) ? null : Math.ceil(m);
  }
  const dens = Number(d.densidad);
  if (!dens || dens <= 0) return null;
  const sup = Number(d.sup_util) || Number(d.sup_construida) || 0;
  if (sup <= 0) return 0;
  return Math.ceil(sup / dens);
}

export const nriBadgeCls = (categoria) =>
  categoria === "ALTO" ? "bg-red-100 text-red-700"
    : categoria === "MEDIO" ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";

// --- Escaleras (CTE DB-SI SI 3 · Tablas 4.1 y 5.1) · réplica cliente ------- //
const PROT_ESC_DESC = {
  "Residencial Vivienda": [14.0, 28.0],
  "Administrativo/Docente": [14.0, 28.0],
  "Comercial/Pública concurrencia": [10.0, 20.0],
  "Hospitalario (hospitalización)": [0.0, 14.0],
  "Hospitalario (otras zonas)": [10.0, 20.0],
  "Aparcamiento / Industrial": [14.0, 28.0],
};
const PROT_ESC_ASC = [2.80, 6.00];
const ESC_RANK = { abierta: 0, no_protegida: 0, protegida: 1, compartimentada: 1, especialmente: 2 };
const ESC_RES = {
  no_protegida: { r: "—", label: "no protegida" },
  protegida: { r: "EI 120", label: "protegida" },
  especialmente: { r: "EI 120 + vestíbulo", label: "especialmente protegida" },
};

function proteccionRequerida(uso, sentido, h) {
  const [lo, hi] = sentido === "ascendente" ? PROT_ESC_ASC : (PROT_ESC_DESC[uso] || [14.0, 28.0]);
  if (h <= lo) return "no_protegida";
  if (h <= hi) return "protegida";
  return "especialmente";
}

export function escaleraCalc(d) {
  const tipo = d.esc_tipo || "protegida";
  const sentido = tipo === "abierta" ? "descendente" : (d.esc_sentido || "descendente");
  const P = Number(d.esc_ocupantes) || 0;
  const h = Number(d.esc_altura_evac) || 0;
  const uso = d.esc_uso || "Aparcamiento / Industrial";
  const S = Number(d.esc_superficie) || 0;
  const minW = d.esc_uso_restringido ? 0.80 : 1.00;
  const protReq = proteccionRequerida(uso, sentido, h);
  const protegida = protReq === "protegida" || protReq === "especialmente";
  let aMin;
  let noAdmisible = false;
  if (protegida && S) {
    aMin = Math.max((P - 3 * S) / 160.0, 0.0);
  } else if (sentido === "ascendente") {
    const denom = 160.0 - 10.0 * h;
    if (denom > 0) aMin = P / denom;
    else { aMin = Infinity; noAdmisible = true; }
  } else {
    aMin = P / 160.0;
  }
  aMin = noAdmisible ? Infinity : Math.max(aMin, minW);
  const aProy = Number(d.esc_anchura) || 0;
  let anchuraEstado;
  if (aMin === Infinity) anchuraEstado = "no_admitido";
  else if (aProy <= 0) anchuraEstado = "pendiente";
  else anchuraEstado = aProy >= aMin - 1e-6 ? "cumple" : "no_cumple";
  const protEstado = (ESC_RANK[tipo] || 0) >= (ESC_RANK[protReq] || 0) ? "cumple" : "no_cumple";
  const res = ESC_RES[protReq] || ESC_RES.protegida;
  let estado = "cumple";
  if (anchuraEstado === "no_admitido" || anchuraEstado === "no_cumple" || protEstado === "no_cumple") estado = "no_cumple";
  else if (anchuraEstado === "pendiente") estado = "pendiente";
  return {
    ocupantes: P, altura: h, uso, sentido,
    anchuraMin: aMin === Infinity ? null : aMin,
    anchuraMinTexto: aMin === Infinity ? "No admisible sin protección" : `${aMin.toFixed(2)} m`,
    anchuraProy: aProy, anchuraEstado,
    proteccionRequerida: protReq, proteccionLabel: res.label, proteccionEstado: protEstado,
    resistencia: res.r, estado,
  };
}

