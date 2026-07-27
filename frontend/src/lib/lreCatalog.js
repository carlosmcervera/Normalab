// Catálogo de usos de Locales/Zonas de Riesgo Especial · Tabla 2.1 del CTE DB-SI.
// Cada uso se clasifica por una métrica: V (volumen construido = superficie × altura),
// S (superficie construida), P (potencia), QS (carga de fuego) o "fijo" (En todo caso).
export const RIESGO_R = { bajo: "R 90", medio: "R 120", alto: "R 180", ninguno: "—" };

export const LRE_USES = [
  { group: "En cualquier edificio o establecimiento", uses: [
    { name: "Talleres de mantenimiento, almacenes de elementos combustibles (mobiliario, lencería, limpieza, etc.), archivos de documentos, depósitos de libros, etc.", metric: "V", unit: "m³", th: { min: 100, bajo: 200, medio: 400 }, crit: "100<V≤200 bajo · 200<V≤400 medio · V>400 alto" },
    { name: "Almacén de residuos", metric: "S", unit: "m²", th: { min: 5, bajo: 15, medio: 30 }, crit: "5<S≤15 bajo · 15<S≤30 medio · S>30 alto" },
    { name: "Aparcamiento de vehículos (S≤100 m²) o integrado en vivienda unifamiliar", metric: "fijo", fixed: "bajo", crit: "En todo caso · riesgo bajo" },
    { name: "Cocinas según potencia instalada P", metric: "P", unit: "kW", th: { min: 20, bajo: 30, medio: 50 }, crit: "20<P≤30 bajo · 30<P≤50 medio · P>50 alto" },
    { name: "Lavanderías. Vestuarios de personal. Camerinos", metric: "S", unit: "m²", th: { min: 20, bajo: 100, medio: 200 }, crit: "20<S≤100 bajo · 100<S≤200 medio · S>200 alto" },
    { name: "Salas de calderas con potencia útil nominal P", metric: "P", unit: "kW", th: { min: 70, bajo: 200, medio: 600 }, crit: "70<P≤200 bajo · 200<P≤600 medio · P>600 alto" },
    { name: "Salas de máquinas de instalaciones de climatización (RITE)", metric: "fijo", fixed: "bajo", crit: "En todo caso · riesgo bajo" },
    { name: "Salas de maquinaria frigorífica: refrigerante amoniaco", metric: "fijo", fixed: "medio", crit: "En todo caso · riesgo medio" },
    { name: "Salas de maquinaria frigorífica: refrigerante halogenado", metric: "P", unit: "kW", th: { min: 0, bajo: null, medio: 400 }, crit: "P≤400 medio · P>400 alto" },
    { name: "Almacén de combustible sólido para calefacción", metric: "S", unit: "m²", th: { min: 0, bajo: 3, medio: 3 }, crit: "S≤3 bajo · S>3 alto" },
    { name: "Local de contadores de electricidad y de cuadros generales de distribución", metric: "fijo", fixed: "bajo", crit: "En todo caso · riesgo bajo" },
    { name: "Centro de transformación (aislamiento dieléctrico seco o líquido con punto de inflamación > 300 ºC)", metric: "fijo", fixed: "bajo", crit: "En todo caso · riesgo bajo" },
    { name: "Centro de transformación (punto de inflamación ≤ 300 ºC), potencia instalada total P", metric: "P", unit: "kVA", th: { min: 0, bajo: 2520, medio: 4000 }, crit: "P<2520 bajo · 2520<P<4000 medio · P>4000 alto (kVA total)" },
    { name: "Sala de maquinaria de ascensores", metric: "fijo", fixed: "bajo", crit: "En todo caso · riesgo bajo" },
    { name: "Sala de grupo electrógeno", metric: "fijo", fixed: "bajo", crit: "En todo caso · riesgo bajo" },
  ] },
  { group: "Residencial Vivienda", uses: [
    { name: "Trasteros", metric: "S", unit: "m²", th: { min: 50, bajo: 100, medio: 500 }, crit: "50<S≤100 bajo · 100<S≤500 medio · S>500 alto" },
  ] },
  { group: "Hospitalario", uses: [
    { name: "Almacenes de productos farmacéuticos y clínicos", metric: "V", unit: "m³", th: { min: 100, bajo: 200, medio: 400 }, crit: "100<V≤200 bajo · 200<V≤400 medio · V>400 alto" },
    { name: "Locales destinados a esterilización y almacenes anejos", metric: "fijo", fixed: "alto", crit: "En todo caso · riesgo alto" },
    { name: "Laboratorios clínicos", metric: "V", unit: "m³", th: { min: 0, bajo: 350, medio: 500 }, crit: "V≤350 bajo · 350<V≤500 medio · V>500 alto" },
  ] },
  { group: "Administrativo", uses: [
    { name: "Imprenta, reprografía y locales anejos (almacenes de papel o publicaciones, encuadernado, etc.)", metric: "V", unit: "m³", th: { min: 100, bajo: 200, medio: 500 }, crit: "100<V≤200 bajo · 200<V≤500 medio · V>500 alto" },
  ] },
  { group: "Residencial Público", uses: [
    { name: "Roperos y locales para la custodia de equipajes", metric: "S", unit: "m²", th: { min: 0, bajo: 20, medio: 100 }, crit: "S≤20 bajo · 20<S≤100 medio · S>100 alto" },
  ] },
  { group: "Comercial", uses: [
    { name: "Almacenes clasificados por la carga de fuego QS de los productos almacenados", metric: "QS", unit: "MJ/m²", th: { min: 425, bajo: 850, medio: 3400 }, crit: "425<QS≤850 bajo · 850<QS≤3.400 medio · QS>3.400 alto" },
  ] },
  { group: "Pública concurrencia", uses: [
    { name: "Taller o almacén de decorados, de vestuario, etc.", metric: "V", unit: "m³", th: { min: 100, bajo: null, medio: 200 }, crit: "100<V≤200 medio · V>200 alto" },
  ] },
];

export function findLreUse(name) {
  for (const g of LRE_USES) {
    const u = g.uses.find((x) => x.name === name);
    if (u) return { ...u, group: g.group };
  }
  return null;
}

export function lreMetricValue(use, ctx = {}) {
  if (!use) return null;
  if (use.metric === "V") return (Number(ctx.superficie) || 0) * (Number(ctx.altura) || 0);
  if (use.metric === "S") return Number(ctx.superficie) || 0;
  if (use.metric === "P") return Number(ctx.potencia) || 0;
  if (use.metric === "QS") return Number(ctx.qs) || 0;
  return null;
}

// Determina el grado de riesgo (bajo/medio/alto) según la métrica y los umbrales.
export function classifyLre(use, ctx = {}) {
  if (!use) return { riesgo: null, valor: null };
  if (use.metric === "fijo") return { riesgo: use.fixed || "bajo", valor: null };
  const v = lreMetricValue(use, ctx);
  if (v == null || (!v && v !== 0)) return { riesgo: null, valor: null };
  const { min = 0, bajo, medio } = use.th || {};
  let riesgo;
  if (v <= min) riesgo = "ninguno";
  else if (bajo != null && v <= bajo) riesgo = "bajo";
  else if (v <= medio) riesgo = "medio";
  else riesgo = "alto";
  return { riesgo, valor: Math.round(v * 100) / 100 };
}
