import { useState } from "react";
import { Plus, Trash2, Flame, Building2, ShieldAlert, StretchHorizontal, Info, Wand2, ChevronRight, ChevronDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { NumberInput } from "@/components/NumberInput";
import { num } from "@/lib/format";
import { sectorCarga, depAporte, depOcupacion, nriBadgeCls, escaleraCalc } from "@/lib/fireload";
import { ActivityCatalogDialog } from "@/features/studies/components/ActivityCatalogDialog";
import { LreUseDialog } from "@/features/studies/components/LreUseDialog";
import { findLreUse, classifyLre } from "@/lib/lreCatalog";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const CUSTOM = "__custom__";
const RIESGO_R = { bajo: "R 90", medio: "R 120", alto: "R 180" };

// Combustibles habituales: PCI (MJ/kg) y densidad (kg/m³) típicos y editables.
const COMBUSTIBLES = [
  { value: "Gasoil / gasóleo", pci: 42.7, dens: 845 },
  { value: "Gasolina", pci: 44.0, dens: 750 },
  { value: "Fuelóleo", pci: 40.6, dens: 960 },
  { value: "Otro (personalizado)", pci: null, dens: null },
];

const ESC_TIPOS = [
  { value: "abierta", label: "Abierta (solo descendente)" },
  { value: "protegida", label: "Protegida" },
  { value: "especialmente_protegida", label: "Especialmente protegida" },
  { value: "compartimentada", label: "Compartimentada" },
];
const ESC_TIPO_LABEL = {
  abierta: "abierta", protegida: "protegida",
  especialmente_protegida: "especialmente protegida", compartimentada: "compartimentada",
};

// Usos previstos para la protección de escaleras (CTE DB-SI SI 3, Tabla 5.1).
const ESC_USOS = [
  "Residencial Vivienda",
  "Administrativo/Docente",
  "Comercial/Pública concurrencia",
  "Hospitalario (hospitalización)",
  "Hospitalario (otras zonas)",
  "Aparcamiento / Industrial",
];

const LRE_TIPOS = [
  { value: "almacen", label: "Almacén / archivo de combustibles", crit: "por volumen (100<V≤200 m³ bajo · 200<V≤400 medio · V>400 alto)" },
  { value: "caldera", label: "Sala de calderas", crit: "por potencia útil (70<P≤200 kW bajo · 200<P≤600 medio · P>600 alto)" },
  { value: "maquinaria", label: "Sala de maquinaria de instalaciones", crit: "según la Tabla 2.1 del DB-SI" },
  { value: "transformador", label: "Centro de transformación", crit: "según la Tabla 2.1 del DB-SI" },
  { value: "cocina", label: "Cocina", crit: "por potencia instalada (20<P≤30 kW bajo · 30<P≤50 medio · P>50 alto)" },
  { value: "aparcamiento", label: "Aparcamiento", crit: "según la Tabla 2.1 del DB-SI" },
  { value: "generico", label: "Otro / genérico", crit: "según la Tabla 2.1 del DB-SI" },
];

const CLASE_META = {
  normal: { label: "Normal", cls: "border-slate-300 bg-slate-100 text-slate-600" },
  lre: { label: "LRE", cls: "border-amber-300 bg-amber-100 text-amber-800" },
  escalera: { label: "Escalera", cls: "border-blue-300 bg-blue-100 text-blue-800" },
};

const LRE_QS_METODOS = [
  { value: "actividad", label: "Por actividad (Tabla 1.3.5)" },
  { value: "combustible", label: "Por combustible (PCI × densidad × volumen)" },
  { value: "manual", label: "Qs manual (MJ/m²)" },
];

// Carga de fuego Qs (MJ/m²) de un LRE clasificado por carga de fuego (Tabla 2.1 · fila QS).
function computeLreQs(d) {
  const metodo = d.lre_qs_metodo || "actividad";
  const ci = Number(d.lre_ci) || 1;
  if (metodo === "manual") return Number(d.lre_qs_manual) || 0;
  if (metodo === "combustible") {
    const sup = Number(d.sup_construida) || Number(d.sup_util) || 0;
    if (sup <= 0) return 0;
    return computeLreCargaTotal(d) / sup;
  }
  if (d.lre_act_modo === "almacenamiento") return (Number(d.lre_act_qvi) || 0) * (Number(d.lre_altura) || 0) * ci;
  return (Number(d.lre_act_qsi) || 0) * ci;
}

// Carga de fuego TOTAL Q (MJ) de un LRE por combustible: PCI × densidad × volumen × Ci.
function computeLreCargaTotal(d) {
  const ci = Number(d.lre_ci) || 1;
  return (Number(d.lre_pci) || 0) * (Number(d.lre_dens_comb) || 0) * (Number(d.lre_volumen) || 0) * ci;
}

const draftLRE = (x) => {
  const use = findLreUse(x.lre_uso);
  const r = x.lre_riesgo || "bajo";
  const sup = Number(x.sup_construida) || 0;
  const partes = [`El local «${x.nombre || "—"}»`];
  if (use) partes.push(`destinado a ${use.name.charAt(0).toLowerCase()}${use.name.slice(1)}`);
  if (use && use.metric === "V" && x.lre_altura) {
    partes.push(`con un volumen construido de ${num(sup * Number(x.lre_altura), 1)} m³ (superficie ${num(sup)} m² × altura ${x.lre_altura} m)`);
  } else if (use && use.metric === "P" && x.lre_potencia) {
    partes.push(`con una potencia de ${x.lre_potencia} ${use.unit}`);
  } else if (use && use.metric === "QS") {
    if (x.lre_qs_metodo === "combustible") {
      partes.push(`con una carga de fuego total Q de ${num(computeLreCargaTotal(x), 0)} MJ (PCI × densidad × volumen × Ci del combustible almacenado) y una densidad de carga de fuego ponderada y corregida Qs de ${num(computeLreQs(x), 0)} MJ/m²`);
    } else {
      partes.push(`con una carga de fuego ponderada Qs de ${num(computeLreQs(x), 0)} MJ/m² (calculada ${x.lre_qs_metodo === "manual" ? "de forma manual" : "por el tipo de actividad, Tabla 1.3.5"})`);
    }
  } else if (use && use.metric === "S") {
    partes.push(`con una superficie construida de ${num(sup)} m²`);
  }
  const crit = use ? ` (criterio Tabla 2.1: ${use.crit})` : "";
  return `${partes.join(", ")} se clasifica como local de riesgo especial de riesgo ${r} conforme a la Tabla 2.1 del CTE DB-SI${crit}. En consecuencia se dota de estructura ${x.lre_r || RIESGO_R[r]}, sectorización EI y las condiciones de acceso/vestíbulo de independencia exigidas para riesgo ${r}. No computa en la carga de fuego del sector (se evalúa por el CTE, Tabla 2.1).`;
};

const draftEscalera = (x) => {
  const tipo = ESC_TIPO_LABEL[x.esc_tipo] || "protegida";
  const sit = x.esc_situacion === "exterior" ? "exterior" : "interior";
  const sentido = x.esc_tipo === "abierta" ? "descendente" : (x.esc_sentido === "ascendente" ? "ascendente" : "descendente");
  const partes = [`La escalera «${x.nombre || "—"}» es una escalera ${tipo} ${sit}, de evacuación ${sentido}`];
  if (x.esc_anchura) partes.push(`de ${x.esc_anchura} m de anchura`);
  if (x.esc_capacidad) partes.push(`con capacidad de evacuación de ${x.esc_capacidad} personas`);
  if (x.esc_uso_restringido) partes.push("de uso restringido");
  const prot = {
    abierta: "sin recinto protegido (solo admisible para evacuación descendente y con las limitaciones de altura del CTE DB-SI, SI 3, Tabla 5.1)",
    protegida: "recinto con resistencia al fuego EI 120, puertas EI2 60-C5 y protección de la estructura y cerramientos (CTE DB-SI, SI 3)",
    especialmente_protegida: "recinto protegido dotado de vestíbulos de independencia y ventilación (natural o por sobrepresión) conforme al CTE DB-SI, SI 3",
    compartimentada: "recinto compartimentado del resto del edificio con la resistencia al fuego exigida y sin comunicación directa con sectores de riesgo",
  }[x.esc_tipo] || "recinto protegido con la resistencia al fuego exigida";
  const c = escaleraCalc(x);
  let calc = "";
  if (c.ocupantes || c.altura) {
    calc = ` Para ${num(c.ocupantes)} ocupantes a evacuar y una altura de evacuación de ${num(c.altura, 2)} m, el CTE DB-SI (SI 3, Tabla 5.1) exige una escalera ${c.proteccionLabel} con recinto ${c.resistencia}, y una anchura mínima de ${c.anchuraMinTexto} (Tabla 4.1).`;
  }
  return `${partes.join(", ")}. Se justifica conforme al CTE DB-SI (SI 3) y DB-SUA: ${prot}, con continuidad hasta la salida de edificio y anchura suficiente para la ocupación evacuada.${calc} Al ser zona de paso, no computa carga de fuego.`;
};

const fieldLabel = "text-[11px] font-medium uppercase tracking-wide text-muted-foreground";

// Carga de fuego con catálogo (Tabla 1.3.5) + edición manual.
function CargaFuegoInline({ x, i, catalog, update, top = true }) {
  const isCustom = x.actividad_cat === CUSTOM;
  const almacen = x.modo === "almacenamiento";
  const deposito = x.modo === "deposito";
  const [dlgOpen, setDlgOpen] = useState(false);
  const applyCatalog = (category, s) => update({
    actividad_cat: category, subactividad: s.name, modo: s.modo,
    qsi: s.modo === "produccion" ? s.qsi : undefined,
    qvi: s.modo === "almacenamiento" ? s.qvi : undefined,
    ci: s.ci, ra: s.ra, rmin: s.rmin ?? null,
  });
  return (
    <div className={`grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7 ${top ? "mt-3 border-t border-border pt-3" : ""}`}>
      <div className="col-span-2 lg:col-span-4">
        <div className="flex items-center justify-between">
          <Label className={fieldLabel}>Actividad (Tabla 1.3.5)</Label>
          {isCustom
            ? <button type="button" className="text-[11px] text-primary hover:underline" onClick={() => { update({ actividad_cat: "" }); setDlgOpen(true); }} data-testid={`estancia-${i}-from-table`}>Elegir de la tabla</button>
            : <button type="button" className="text-[11px] text-primary hover:underline" onClick={() => update({ actividad_cat: CUSTOM, subactividad: "" })} data-testid={`estancia-${i}-custom`}>Personalizada</button>}
        </div>
        {isCustom ? (
          <Input className="mt-1 h-8 rounded-sm text-xs" value={x.subactividad || ""} onChange={(e) => update({ subactividad: e.target.value })} placeholder="Descripción de la actividad (personalizada)" data-testid={`estancia-${i}-sub`} />
        ) : (
          <Button type="button" variant="outline" className="mt-1 h-8 w-full justify-between rounded-sm px-2 text-xs font-normal" onClick={() => setDlgOpen(true)} data-testid={`estancia-${i}-cat`}>
            <span className="truncate">{x.actividad_cat && x.subactividad ? `${x.actividad_cat} · ${x.subactividad}` : "Seleccionar de la tabla 1.3.5…"}</span>
            <Search className="ml-2 h-3.5 w-3.5 shrink-0 opacity-60" />
          </Button>
        )}
        <ActivityCatalogDialog open={dlgOpen} onOpenChange={setDlgOpen} catalog={catalog}
          current={{ category: x.actividad_cat, name: x.subactividad }} onSelect={applyCatalog} />
      </div>
      <div>
        <Label className={fieldLabel}>Modo</Label>
        <Select value={x.modo || "produccion"} onValueChange={(v) => update(v === "deposito" ? { modo: v, ci: 1, ra: 1 } : { modo: v })}>
          <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-modo`}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="produccion">Producción</SelectItem>
            <SelectItem value="almacenamiento">Almacenam.</SelectItem>
            <SelectItem value="deposito">Depósito comb.</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {deposito ? (
        <>
          <div className="col-span-2">
            <Label className={fieldLabel}>Combustible</Label>
            <Select value={x.combustible || ""} onValueChange={(v) => {
              const c = COMBUSTIBLES.find((k) => k.value === v);
              update(c && c.pci ? { combustible: v, pci: c.pci, dens_comb: c.dens } : { combustible: v });
            }}>
              <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-combustible`}><SelectValue placeholder="Combustible" /></SelectTrigger>
              <SelectContent>{COMBUSTIBLES.map((c) => <SelectItem key={c.value} value={c.value}>{c.value}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div><Label className={fieldLabel}>PCI (MJ/kg)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.pci ?? ""} onChange={(v) => update({ pci: v })} data-testid={`estancia-${i}-pci`} /></div>
          <div><Label className={fieldLabel}>Densidad (kg/m³)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.dens_comb ?? ""} onChange={(v) => update({ dens_comb: v })} data-testid={`estancia-${i}-dens`} /></div>
          <div><Label className={fieldLabel}>Volumen (m³)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.volumen ?? ""} onChange={(v) => update({ volumen: v })} data-testid={`estancia-${i}-volumen`} /></div>
        </>
      ) : almacen ? (
        <>
          <div><Label className={fieldLabel}>qv (MJ/m³)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.qvi ?? ""} onChange={(v) => update({ qvi: v })} data-testid={`estancia-${i}-qvi`} /></div>
          <div><Label className={fieldLabel}>hi (m)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.hi ?? ""} onChange={(v) => update({ hi: v })} data-testid={`estancia-${i}-hi`} /></div>
        </>
      ) : (
        <div><Label className={fieldLabel}>qs (MJ/m²)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.qsi ?? ""} onChange={(v) => update({ qsi: v })} data-testid={`estancia-${i}-qsi`} /></div>
      )}
      <div><Label className={fieldLabel}>Ci</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.ci ?? (deposito ? 1 : 1.44)} onChange={(v) => update({ ci: v })} data-testid={`estancia-${i}-ci`} /></div>
      <div><Label className={fieldLabel}>Ra</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.ra ?? 1} onChange={(v) => update({ ra: v })} data-testid={`estancia-${i}-ra`} /></div>
    </div>
  );
}

function SectorTile({ s, i, cte, carga, ocup, configTypes, usos, updateSector, removeSector }) {
  return (
    <div className="border border-border bg-secondary/30 p-3" data-testid={`sector-card-${i}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <Badge variant="outline" className={`rounded-sm border-0 px-1.5 text-[11px] ${cte ? "bg-blue-100 text-blue-800" : "bg-orange-100 text-orange-800"}`}>
          {cte ? <Building2 className="mr-1 h-3 w-3" /> : <Flame className="mr-1 h-3 w-3" />}
          {cte ? "CTE DB-SI" : "RSCIEI"}
        </Badge>
        <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removeSector(s.id)} data-testid={`remove-sector-${i}`}><Trash2 className="h-3.5 w-3.5" /></Button>
      </div>
      <div className="mb-2 flex items-center justify-between gap-2 border-b border-border pb-2 font-mono text-[11px]">
        <span className="text-muted-foreground">A <b className="text-foreground">{num(carga.A)}</b> m² <span className="opacity-60">s/LRE</span></span>
        <span className="text-muted-foreground" data-testid={`sector-${i}-qs`}>Qs <b className="text-foreground">{carga.hasData ? num(carga.qs) : "—"}</b> MJ/m²</span>
        <span className="text-muted-foreground" data-testid={`sector-${i}-ocup`}>Ocup <b className="text-foreground">{ocup}</b> p.</span>
        {carga.hasData
          ? <span className={`rounded-sm px-1.5 py-0.5 text-[10px] font-semibold ${nriBadgeCls(carga.categoria)}`} data-testid={`sector-${i}-nri`}>NRI {carga.nivel} · {carga.categoria}</span>
          : <span className="text-muted-foreground">NRI —</span>}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="col-span-2">
          <Label className={fieldLabel}>Nombre</Label>
          <Input className="mt-1 h-8 rounded-sm text-sm" value={s.nombre || ""} onChange={(e) => updateSector(s.id, { nombre: e.target.value })} data-testid={`sector-${i}-nombre`} />
        </div>
        <div className="col-span-2">
          <Label className={fieldLabel}>Actividad</Label>
          <Input className="mt-1 h-8 rounded-sm text-sm" value={s.actividad || ""} onChange={(e) => updateSector(s.id, { actividad: e.target.value })} placeholder="Taller / Almacén / Oficinas" data-testid={`sector-${i}-actividad`} />
        </div>
        <div>
          <Label className={fieldLabel}>Ámbito</Label>
          <Select value={s.ambito || "industrial"} onValueChange={(v) => updateSector(s.id, { ambito: v })}>
            <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`sector-${i}-ambito`}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="industrial">Industrial (RSCIEI)</SelectItem>
              <SelectItem value="cte">CTE (edificación)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {cte ? (
          <div>
            <Label className={fieldLabel}>Uso CTE</Label>
            <Select value={s.uso_cte || "Administrativo"} onValueChange={(v) => updateSector(s.id, { uso_cte: v })}>
              <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`sector-${i}-uso`}><SelectValue /></SelectTrigger>
              <SelectContent>{usos.map((u) => <SelectItem key={u.value || u} value={u.value || u}>{u.label || u}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        ) : (
          <div>
            <Label className={fieldLabel}>Configuración</Label>
            <Select value={s.config || "C"} onValueChange={(v) => updateSector(s.id, { config: v })}>
              <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`sector-${i}-config`}><SelectValue /></SelectTrigger>
              <SelectContent>{configTypes.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        )}
        <div>
          <Label className={fieldLabel}>Situación</Label>
          <Select value={s.situacion || "sobre_rasante"} onValueChange={(v) => updateSector(s.id, { situacion: v })}>
            <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`sector-${i}-situacion`}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="sobre_rasante">Sobre rasante</SelectItem>
              <SelectItem value="bajo_rasante">Bajo rasante</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className={fieldLabel}>Nº salidas</Label>
          <NumberInput integer min={1} className="mt-1 h-8 rounded-sm font-mono text-xs" value={s.num_salidas ?? 2} onChange={(v) => updateSector(s.id, { num_salidas: v })} data-testid={`sector-${i}-salidas`} />
        </div>
        <div>
          <Label className={fieldLabel}>Altura evac. (m)</Label>
          <NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={s.altura_evacuacion ?? 0} onChange={(v) => updateSector(s.id, { altura_evacuacion: v })} data-testid={`sector-${i}-altura`} />
        </div>
        <label className="col-span-2 mt-0.5 flex items-center gap-2 text-xs">
          <Switch checked={!!s.rociadores} onCheckedChange={(v) => updateSector(s.id, { rociadores: v })} data-testid={`sector-${i}-rociadores`} />
          Rociadores automáticos en todo el sector
        </label>
      </div>
    </div>
  );
}

export function SectoresStep({ data, setData, schema = {} }) {
  const sectores = data.sectores || [];
  const deps = data.dependencias || [];
  const configTypes = (schema.config_types || []).filter((c) => c.value !== "D");
  const usos = schema.dbsi_uses || [];
  const catalog = schema.activity_catalog || [];
  const [expanded, setExpanded] = useState(() => new Set());

  const toggle = (id) => setExpanded((prev) => {
    const n = new Set(prev);
    n.has(id) ? n.delete(id) : n.add(id);
    return n;
  });

  const addSector = () =>
    setData((d) => ({
      ...d,
      sectores: [...(d.sectores || []), {
        id: genId(), nombre: `Sector ${(d.sectores || []).length + 1}`, actividad: "",
        ambito: "industrial", config: "C", uso_cte: "Administrativo",
        situacion: "sobre_rasante", num_salidas: 2, altura_evacuacion: 0, rociadores: false,
      }],
    }));
  const updateSector = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));
  const removeSector = (id) =>
    setData((d) => ({ ...d, sectores: d.sectores.filter((s) => s.id !== id),
      dependencias: (d.dependencias || []).map((x) => (x.sector_id === id ? { ...x, sector_id: "" } : x)) }));
  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));

  const setClase = (id, clase) => updateDep(id, { clase, es_lre: clase === "lre",
    ...(clase === "lre" ? { lre_riesgo: "bajo", lre_r: RIESGO_R.bajo } : {}) });

  return (
    <TooltipProvider>
      <div className="space-y-6" data-testid="sectores-step">
        {/* ── Bloque A · Sectores de incendio ─────────────────────────── */}
        <section>
          <div className="mb-2 flex items-center justify-between border-b border-border pb-2">
            <div className="flex items-baseline gap-2">
              <span className="flex h-5 w-5 items-center justify-center bg-primary text-[11px] font-bold text-primary-foreground">1</span>
              <h3 className="font-heading text-base">Sectores de incendio</h3>
              <span className="font-mono text-xs text-muted-foreground">{sectores.length}</span>
            </div>
            <Button variant="outline" size="sm" className="h-8 rounded-sm" onClick={addSector} data-testid="add-sector">
              <Plus className="mr-1.5 h-4 w-4" /> Añadir sector
            </Button>
          </div>
          {sectores.length === 0 ? (
            <p className="border border-dashed border-border py-5 text-center text-sm text-muted-foreground">Sin sectores. Crea el primer sector de incendio.</p>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {sectores.map((s, i) => (
                <SectorTile key={s.id} s={s} i={i} cte={s.ambito === "cte"} carga={sectorCarga(deps.filter((d) => d.sector_id === s.id))}
                  ocup={deps.filter((d) => d.sector_id === s.id).reduce((a, d) => a + (depOcupacion(d) || 0), 0)}
                  configTypes={configTypes} usos={usos} updateSector={updateSector} removeSector={removeSector} />
              ))}
            </div>
          )}
        </section>

        {/* ── Bloque B · Asignación de estancias ──────────────────────── */}
        <section>
          <div className="mb-2 flex items-center justify-between border-b border-border pb-2">
            <div className="flex items-baseline gap-2">
              <span className="flex h-5 w-5 items-center justify-center bg-primary text-[11px] font-bold text-primary-foreground">2</span>
              <h3 className="font-heading text-base">Asignación de estancias y carga de fuego</h3>
              <span className="font-mono text-xs text-muted-foreground">{deps.length}</span>
            </div>
          </div>
          {deps.length === 0 ? (
            <p className="border border-dashed border-border py-5 text-center text-sm text-muted-foreground">No hay estancias. Vuelve al paso «Cuadro de superficies».</p>
          ) : sectores.length === 0 ? (
            <p className="border border-dashed border-border py-5 text-center text-sm text-muted-foreground">Crea al menos un sector para asignar las estancias.</p>
          ) : (
            <div className="overflow-x-auto border border-border">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border bg-secondary/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                    <th className="w-8 px-2 py-2" />
                    <th className="px-2 py-2 font-semibold">Estancia</th>
                    <th className="px-2 py-2 text-right font-semibold">m² útil</th>
                    <th className="px-2 py-2 text-right font-semibold">Carga (MJ)</th>
                    <th className="px-2 py-2 text-right font-semibold">Ocup.</th>
                    <th className="px-2 py-2 font-semibold">Sector</th>
                    <th className="px-2 py-2 font-semibold">Clasificación</th>
                  </tr>
                </thead>
                <tbody>
                  {deps.map((x, i) => {
                    const clase = x.clase || "normal";
                    const isEscalera = clase === "escalera" || clase === "escalera_protegida";
                    const meta = CLASE_META[isEscalera ? "escalera" : clase] || CLASE_META.normal;
                    const isOpen = expanded.has(x.id);
                    const sinSector = !x.sector_id;
                    return (
                      <AssignmentRows key={x.id} {...{ x, i, clase, isEscalera, meta, isOpen, sinSector, sectores, catalog, toggle, updateDep, setClase }} />
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </TooltipProvider>
  );
}

function AssignmentRows({ x, i, clase, isEscalera, meta, isOpen, sinSector, sectores, catalog, toggle, updateDep, setClase }) {
  const [lreDlg, setLreDlg] = useState(false);
  const [qsActDlg, setQsActDlg] = useState(false);
  const lreUse = findLreUse(x.lre_uso);
  const escCalc = isEscalera ? escaleraCalc(x) : null;
  const { riesgo: lreRiesgo } = classifyLre(lreUse, {
    superficie: x.sup_construida, altura: x.lre_altura, potencia: x.lre_potencia, qs: computeLreQs(x),
  });
  // Aplica un cambio a un LRE y recalcula el riesgo (bajo/medio/alto) según la Tabla 2.1.
  const applyLre = (patch) => {
    const merged = { ...x, ...patch };
    const use = findLreUse(merged.lre_uso);
    const qs = computeLreQs(merged);
    const { riesgo, valor } = classifyLre(use, {
      superficie: merged.sup_construida, altura: merged.lre_altura, potencia: merged.lre_potencia, qs,
    });
    const eff = riesgo && riesgo !== "ninguno" ? riesgo : (merged.lre_riesgo || "bajo");
    updateDep(x.id, {
      ...patch,
      lre_metric: use?.metric || null,
      lre_criterio: use?.crit || null,
      lre_valor: valor,
      lre_qs: use?.metric === "QS" ? Math.round(qs * 100) / 100 : x.lre_qs,
      lre_riesgo: eff,
      lre_r: RIESGO_R[eff] || merged.lre_r || RIESGO_R.bajo,
    });
  };
  return (
    <>
      <tr className={`border-b border-border transition-colors hover:bg-secondary/30 ${isOpen ? "bg-secondary/20" : ""}`} data-testid={`estancia-row-${i}`}>
        <td className="px-2 py-1.5 align-middle">
          <button onClick={() => toggle(x.id)} className="flex h-6 w-6 items-center justify-center text-muted-foreground hover:text-foreground" data-testid={`estancia-${i}-expand`} aria-label="Detalles">
            {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </td>
        <td className="px-2 py-1.5">
          <div className="flex items-center gap-2">
            <span className="truncate font-medium" title={x.nombre}>{x.nombre || `Estancia ${i + 1}`}</span>
            <span className={`shrink-0 rounded-sm border px-1.5 py-0.5 text-[10px] font-semibold ${meta.cls}`} data-testid={`estancia-${i}-clase-badge`}>{meta.label}</span>
          </div>
        </td>
        <td className="px-2 py-1.5 text-right font-mono text-xs text-muted-foreground">{num(x.sup_util || x.sup_construida || 0)}</td>
        <td className="px-2 py-1.5 text-right font-mono text-xs" data-testid={`estancia-${i}-carga`}>
          {(isEscalera || clase === "lre")
            ? <span className="text-muted-foreground/70">no computa</span>
            : (() => { const ap = depAporte(x); return ap == null ? <span className="text-muted-foreground/60">—</span> : <span className="font-semibold text-foreground">{num(ap)}</span>; })()}
        </td>
        <td className="px-2 py-1.5 text-right font-mono text-xs" data-testid={`estancia-${i}-ocup`}>
          {(() => { const o = depOcupacion(x); return o == null ? <span className="text-muted-foreground/60">—</span> : <span className="text-foreground">{o}</span>; })()}
        </td>
        <td className="px-2 py-1.5">
          <Select value={x.sector_id || ""} onValueChange={(v) => updateDep(x.id, { sector_id: v })}>
            <SelectTrigger className={`h-8 w-44 rounded-sm text-xs ${sinSector ? "border-amber-400 text-amber-700" : ""}`} data-testid={`estancia-${i}-sector`}><SelectValue placeholder="Asignar…" /></SelectTrigger>
            <SelectContent>{sectores.map((s) => <SelectItem key={s.id} value={s.id}>{s.nombre}</SelectItem>)}</SelectContent>
          </Select>
        </td>
        <td className="px-2 py-1.5">
          <div className="flex items-center gap-1">
            <Select value={clase} onValueChange={(v) => setClase(x.id, v)}>
              <SelectTrigger className="h-8 w-52 rounded-sm text-xs" data-testid={`estancia-${i}-clase`}><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">Estancia normal</SelectItem>
                <SelectItem value="lre"><span className="inline-flex items-center gap-1"><ShieldAlert className="h-3 w-3" /> Local de riesgo especial</span></SelectItem>
                <SelectItem value="escalera"><span className="inline-flex items-center gap-1"><StretchHorizontal className="h-3 w-3" /> Escalera</span></SelectItem>
              </SelectContent>
            </Select>
            {clase === "lre" && (
              <Tooltip>
                <TooltipTrigger asChild><Info className="h-3.5 w-3.5 cursor-help text-amber-600" data-testid={`estancia-${i}-lre-info`} /></TooltipTrigger>
                <TooltipContent className="max-w-xs">Este local NO computa en la carga de fuego del sector. Se clasifica y evalúa como Local de Riesgo Especial según el CTE DB-SI (Tabla 2.1), por el uso y el volumen/potencia. Define su uso y altura más abajo.</TooltipContent>
              </Tooltip>
            )}
          </div>
        </td>
      </tr>
      {isOpen && (
        <tr data-testid={`estancia-${i}-detail`}>
          <td className="border-b border-border bg-slate-50 p-0" colSpan={7}>
            <div className={`border-l-2 p-3 ${clase === "lre" ? "border-l-amber-400" : isEscalera ? "border-l-blue-400" : "border-l-primary"}`}>
              {clase === "lre" ? (
                <>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <div className="col-span-2 sm:col-span-2">
                    <Label className={fieldLabel}>Uso del local (Tabla 2.1 DB-SI)</Label>
                    <Button type="button" variant="outline" className="mt-1 h-8 w-full justify-between rounded-sm px-2 text-xs font-normal" onClick={() => setLreDlg(true)} data-testid={`estancia-${i}-lre-uso`}>
                      <span className="truncate">{x.lre_uso || "Seleccionar uso…"}</span>
                      <Search className="ml-2 h-3.5 w-3.5 shrink-0 opacity-60" />
                    </Button>
                    <LreUseDialog open={lreDlg} onOpenChange={setLreDlg} current={x.lre_uso}
                      onSelect={(group, u) => applyLre({ lre_uso: u.name, lre_uso_grupo: group })} />
                  </div>
                  {lreUse && lreUse.metric === "V" && (
                    <div><Label className={fieldLabel}>Altura (m)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_altura ?? ""} onChange={(v) => applyLre({ lre_altura: v })} data-testid={`estancia-${i}-lre-altura`} /></div>
                  )}
                  {lreUse && lreUse.metric === "P" && (
                    <div><Label className={fieldLabel}>Potencia ({lreUse.unit})</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_potencia ?? ""} onChange={(v) => applyLre({ lre_potencia: v })} data-testid={`estancia-${i}-lre-potencia`} /></div>
                  )}
                  {lreUse && lreUse.metric === "QS" && (
                    <div className="col-span-2 space-y-2 rounded-sm border border-orange-200 bg-orange-50/70 p-2 sm:col-span-4" data-testid={`estancia-${i}-lre-qs-block`}>
                      <div className="flex flex-wrap items-end gap-2">
                        <div className="min-w-[240px] flex-1">
                          <Label className={fieldLabel}>Cálculo de la carga de fuego Qs</Label>
                          <Select value={x.lre_qs_metodo || "actividad"} onValueChange={(v) => applyLre({ lre_qs_metodo: v })}>
                            <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-lre-qs-metodo`}><SelectValue /></SelectTrigger>
                            <SelectContent>{LRE_QS_METODOS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
                          </Select>
                        </div>
                        <div className="w-20"><Label className={fieldLabel}>Ci</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_ci ?? ""} onChange={(v) => applyLre({ lre_ci: v })} data-testid={`estancia-${i}-lre-ci`} /></div>
                      </div>
                      {(x.lre_qs_metodo || "actividad") === "actividad" && (
                        <div className="space-y-2">
                          <Button type="button" variant="outline" className="h-8 w-full justify-between rounded-sm px-2 text-xs font-normal" onClick={() => setQsActDlg(true)} data-testid={`estancia-${i}-lre-act`}>
                            <span className="truncate">{x.lre_act_name || "Seleccionar actividad (Tabla 1.3.5)…"}</span>
                            <Search className="ml-2 h-3.5 w-3.5 shrink-0 opacity-60" />
                          </Button>
                          <ActivityCatalogDialog open={qsActDlg} onOpenChange={setQsActDlg} catalog={catalog}
                            current={x.lre_act_name ? { category: x.lre_act_cat, name: x.lre_act_name } : null}
                            onSelect={(cat, s) => applyLre({ lre_act_cat: cat, lre_act_name: s.name, lre_act_qsi: s.qsi, lre_act_qvi: s.qvi, lre_act_modo: s.modo, lre_ci: x.lre_ci ?? s.ci })} />
                          {x.lre_act_modo === "almacenamiento" && (
                            <div className="w-40"><Label className={fieldLabel}>Altura almac. (m)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_altura ?? ""} onChange={(v) => applyLre({ lre_altura: v })} data-testid={`estancia-${i}-lre-qs-altura`} /></div>
                          )}
                        </div>
                      )}
                      {x.lre_qs_metodo === "combustible" && (
                        <div className="grid grid-cols-3 gap-2">
                          <div><Label className={fieldLabel}>PCI (MJ/kg)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_pci ?? ""} onChange={(v) => applyLre({ lre_pci: v })} data-testid={`estancia-${i}-lre-pci`} /></div>
                          <div><Label className={fieldLabel}>Densidad (kg/m³)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_dens_comb ?? ""} onChange={(v) => applyLre({ lre_dens_comb: v })} data-testid={`estancia-${i}-lre-dens`} /></div>
                          <div><Label className={fieldLabel}>Volumen (m³)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_volumen ?? ""} onChange={(v) => applyLre({ lre_volumen: v })} data-testid={`estancia-${i}-lre-vol`} /></div>
                        </div>
                      )}
                      {x.lre_qs_metodo === "manual" && (
                        <div className="w-40"><Label className={fieldLabel}>Qs (MJ/m²)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_qs_manual ?? ""} onChange={(v) => applyLre({ lre_qs_manual: v })} data-testid={`estancia-${i}-lre-qs-manual`} /></div>
                      )}
                      {x.lre_qs_metodo === "combustible" ? (() => {
                        const qTotal = computeLreCargaTotal(x);
                        const sup = Number(x.sup_construida) || Number(x.sup_util) || 0;
                        return (
                          <div className="space-y-0.5" data-testid={`estancia-${i}-lre-qs-valor`}>
                            <p className="font-mono text-[11px] font-semibold text-orange-800">Carga de fuego total Q = {num(qTotal, 0)} MJ <span className="font-normal text-muted-foreground">(PCI × densidad × volumen × Ci)</span></p>
                            <p className="font-mono text-[11px] font-semibold text-orange-800">Qs = Q / superficie = {num(computeLreQs(x), 0)} MJ/m² <span className="font-normal text-muted-foreground">(densidad — clasifica la Tabla 2.1{sup > 0 ? `, sup. ${num(sup)} m²` : ""})</span></p>
                            {sup <= 0 && <p className="text-[11px] font-semibold text-red-700">Aviso — define la superficie del recinto para obtener la densidad Qs.</p>}
                            {qTotal >= 3000000 && <p className="text-[11px] font-semibold text-red-700">Aviso — Q ≥ 3×10⁶ MJ: el recinto puede considerarse uso «Almacén» sujeto al RSCIEI.</p>}
                            {qTotal >= 10000 && qTotal < 3000000 && <p className="text-[11px] font-semibold text-amber-700">Aviso — Q ≥ 10.000 MJ: revisar la obligatoriedad de clasificarlo como local de riesgo especial.</p>}
                          </div>
                        );
                      })() : (
                        <p className="font-mono text-[11px] font-semibold text-orange-800" data-testid={`estancia-${i}-lre-qs-valor`}>Qs = {num(computeLreQs(x), 0)} MJ/m²</p>
                      )}
                    </div>
                  )}
                  <div className="col-span-2 sm:col-span-4 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-sm border border-amber-200 bg-amber-50 px-2 py-1.5 text-[11px]">
                    <span className="text-muted-foreground">Superficie constr. <b className="text-foreground font-mono">{num(x.sup_construida || 0)}</b> m²</span>
                    {lreUse?.metric === "V" && <span className="text-muted-foreground">Volumen <b className="text-foreground font-mono">{num((Number(x.sup_construida) || 0) * (Number(x.lre_altura) || 0), 1)}</b> m³</span>}
                    <span className="text-muted-foreground">Criterio: {lreUse?.crit || "—"}</span>
                    <span className="ml-auto text-muted-foreground" data-testid={`estancia-${i}-lre-riesgo-auto`}>
                      Riesgo:{" "}
                      {lreRiesgo === "ninguno"
                        ? <b className="text-amber-700">No alcanza umbral (revisar)</b>
                        : <span className={`rounded-sm px-1.5 py-0.5 font-semibold ${nriBadgeCls(String(lreRiesgo || "").toUpperCase() === "ALTO" ? "ALTO" : String(lreRiesgo || "").toUpperCase() === "MEDIO" ? "MEDIO" : "BAJO")}`}>{(lreRiesgo || x.lre_riesgo || "bajo").toUpperCase()}</span>}
                      {" · "}{x.lre_r || RIESGO_R[x.lre_riesgo || "bajo"]}
                    </span>
                  </div>
                  <div>
                    <Label className={fieldLabel}>Riesgo (editable)</Label>
                    <Select value={x.lre_riesgo || "bajo"} onValueChange={(v) => updateDep(x.id, { lre_riesgo: v, lre_r: RIESGO_R[v] })}>
                      <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-lre-riesgo`}><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bajo">Bajo</SelectItem>
                        <SelectItem value="medio">Medio</SelectItem>
                        <SelectItem value="alto">Alto</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className={fieldLabel}>Resistencia (R)</Label>
                    <Input className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.lre_r || RIESGO_R[x.lre_riesgo || "bajo"]} onChange={(e) => updateDep(x.id, { lre_r: e.target.value })} data-testid={`estancia-${i}-lre-r`} />
                  </div>
                  <div className="col-span-2 sm:col-span-4">
                    <div className="flex items-center justify-between">
                      <Label className={fieldLabel}>Justificación (Tabla 2.1: uso, volumen/superficie/potencia)</Label>
                      <Button variant="ghost" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => updateDep(x.id, { lre_justificacion: draftLRE(x) })} data-testid={`estancia-${i}-lre-gen`}><Wand2 className="mr-1 h-3 w-3" /> Generar</Button>
                    </div>
                    <Textarea className="mt-1 min-h-[56px] rounded-sm text-sm" value={x.lre_justificacion || ""} onChange={(e) => updateDep(x.id, { lre_justificacion: e.target.value })} placeholder="Pulsa «Generar» para redactarla, o escribe tu justificación." data-testid={`estancia-${i}-lre-just`} />
                  </div>
                </div>
                <p className="mt-2 text-[11px] text-muted-foreground">Los locales de riesgo especial NO computan carga de fuego: se clasifican por el CTE DB-SI (Tabla 2.1) según el uso y el volumen/potencia. Su superficie sí cuenta en el cuadro de superficies.</p>
                </>
              ) : isEscalera ? (
                <>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <div>
                      <Label className={fieldLabel}>Tipo</Label>
                      <Select value={x.esc_tipo || "protegida"} onValueChange={(v) => updateDep(x.id, { esc_tipo: v, ...(v === "abierta" ? { esc_sentido: "descendente" } : {}) })}>
                        <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-esc-tipo`}><SelectValue /></SelectTrigger>
                        <SelectContent>{ESC_TIPOS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className={fieldLabel}>Sentido evacuación</Label>
                      <Select value={x.esc_tipo === "abierta" ? "descendente" : (x.esc_sentido || "descendente")} onValueChange={(v) => updateDep(x.id, { esc_sentido: v })} disabled={x.esc_tipo === "abierta"}>
                        <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-esc-sentido`}><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="descendente">Descendente</SelectItem>
                          <SelectItem value="ascendente">Ascendente</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className={fieldLabel}>Uso previsto (Tabla 5.1)</Label>
                      <Select value={x.esc_uso || "Aparcamiento / Industrial"} onValueChange={(v) => updateDep(x.id, { esc_uso: v })}>
                        <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-esc-uso`}><SelectValue /></SelectTrigger>
                        <SelectContent>{ESC_USOS.map((u) => <SelectItem key={u} value={u}>{u}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className={fieldLabel}>Situación</Label>
                      <Select value={x.esc_situacion || "interior"} onValueChange={(v) => updateDep(x.id, { esc_situacion: v })}>
                        <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`estancia-${i}-esc-situacion`}><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="interior">Interior</SelectItem>
                          <SelectItem value="exterior">Exterior</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div><Label className={fieldLabel}>Ocupantes a evacuar (P)</Label><NumberInput integer min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.esc_ocupantes ?? ""} onChange={(v) => updateDep(x.id, { esc_ocupantes: v })} data-testid={`estancia-${i}-esc-ocupantes`} /></div>
                    <div><Label className={fieldLabel}>Altura evacuación (m)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.esc_altura_evac ?? ""} onChange={(v) => updateDep(x.id, { esc_altura_evac: v })} data-testid={`estancia-${i}-esc-altura`} /></div>
                    <div><Label className={fieldLabel}>Anchura proyectada (m)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.esc_anchura ?? ""} onChange={(v) => updateDep(x.id, { esc_anchura: v })} data-testid={`estancia-${i}-esc-anchura`} /></div>
                    {(x.esc_tipo === "protegida" || x.esc_tipo === "especialmente_protegida") && (
                      <div><Label className={fieldLabel}>Sup. recinto (m²)</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={x.esc_superficie ?? ""} onChange={(v) => updateDep(x.id, { esc_superficie: v })} data-testid={`estancia-${i}-esc-superficie`} /></div>
                    )}
                    <label className="col-span-2 flex items-center gap-2 pb-1 text-xs sm:col-span-1">
                      <Switch checked={!!x.esc_uso_restringido} onCheckedChange={(v) => updateDep(x.id, { esc_uso_restringido: v })} data-testid={`estancia-${i}-esc-restringido`} />
                      Uso restringido
                    </label>
                    {/* Resultado en vivo (CTE DB-SI · Tablas 4.1 y 5.1) */}
                    <div className="col-span-2 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-sm border border-blue-200 bg-blue-50 px-2 py-1.5 text-[11px] sm:col-span-4" data-testid={`estancia-${i}-esc-calc`}>
                      <span className="text-muted-foreground">Protección exigida:{" "}
                        <b className={`${escCalc?.proteccionEstado === "no_cumple" ? "text-red-700" : "text-blue-800"}`} data-testid={`estancia-${i}-esc-proteccion`}>{escCalc?.proteccionLabel || "—"}</b></span>
                      <span className="text-muted-foreground">RF recinto: <b className="font-mono text-foreground" data-testid={`estancia-${i}-esc-rf`}>{escCalc?.resistencia || "—"}</b></span>
                      <span className="text-muted-foreground">Anchura mín. (Tabla 4.1): <b className="font-mono text-foreground" data-testid={`estancia-${i}-esc-anchura-min`}>{escCalc?.anchuraMinTexto || "—"}</b></span>
                      <span className={`ml-auto rounded-sm px-1.5 py-0.5 font-semibold ${escCalc?.estado === "no_cumple" ? "bg-red-100 text-red-700" : escCalc?.estado === "cumple" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`} data-testid={`estancia-${i}-esc-estado`}>
                        {escCalc?.estado === "no_cumple" ? "No cumple" : escCalc?.estado === "cumple" ? "Cumple" : "Pendiente"}
                      </span>
                    </div>
                    <div className="col-span-2 sm:col-span-4">
                      <div className="flex items-center justify-between">
                        <Label className={fieldLabel}>Justificación CTE (SI 3 / SUA)</Label>
                        <Button variant="ghost" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => updateDep(x.id, { esc_justificacion: draftEscalera(x) })} data-testid={`estancia-${i}-esc-gen`}><Wand2 className="mr-1 h-3 w-3" /> Generar</Button>
                      </div>
                      <Textarea className="mt-1 min-h-[56px] rounded-sm text-sm" value={x.esc_justificacion || ""} onChange={(e) => updateDep(x.id, { esc_justificacion: e.target.value })} placeholder="Pulsa «Generar» o escribe tu justificación CTE." data-testid={`estancia-${i}-esc-just`} />
                    </div>
                  </div>
                  <p className="mt-2 text-[11px] text-muted-foreground">Introduce nº de ocupantes y altura de evacuación: el sistema calcula automáticamente la protección exigida (RF), la sectorización y la anchura mínima según el CTE DB-SI (Tablas 4.1 y 5.1). La escalera NO computa carga de fuego (zona de paso).</p>
                </>
              ) : (
                <CargaFuegoInline x={x} i={i} catalog={catalog} update={(p) => updateDep(x.id, p)} top={false} />
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
