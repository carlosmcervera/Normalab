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

// Aporte de una estancia en MJ (producción: qs·Ci·S ; almacenamiento: qv·Ci·hi·S).
export function depAporte(d) {
  const ci = Number(d.ci) || 0;
  const s = Number(d.sup_construida) || 0;
  if (!ci || !s) return null;
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

// Carga de fuego del sector a partir de sus estancias asignadas (LRE excluidos).
export function sectorCarga(deps) {
  const calc = deps.filter((d) => d.clase !== "lre" && !d.es_lre);
  const A = calc.reduce((a, d) => a + (Number(d.sup_construida) || 0), 0);
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

export const nriBadgeCls = (categoria) =>
  categoria === "ALTO" ? "bg-red-100 text-red-700"
    : categoria === "MEDIO" ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";
