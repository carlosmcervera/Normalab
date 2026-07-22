import { Plus, Trash2, Flame, Building2, ShieldAlert, StretchHorizontal, Info, Wand2 } from "lucide-react";
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
import { num } from "@/lib/format";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const CUSTOM = "__custom__";
const RIESGO_R = { bajo: "R 90", medio: "R 120", alto: "R 180" };

const LRE_TIPOS = [
  { value: "almacen", label: "Almacén / archivo de combustibles", crit: "por volumen (100<V≤200 m³ bajo · 200<V≤400 medio · V>400 alto)" },
  { value: "caldera", label: "Sala de calderas", crit: "por potencia útil (70<P≤200 kW bajo · 200<P≤600 medio · P>600 alto)" },
  { value: "maquinaria", label: "Sala de maquinaria de instalaciones", crit: "según la Tabla 2.1 del DB-SI" },
  { value: "transformador", label: "Centro de transformación", crit: "según la Tabla 2.1 del DB-SI" },
  { value: "cocina", label: "Cocina", crit: "por potencia instalada (20<P≤30 kW bajo · 30<P≤50 medio · P>50 alto)" },
  { value: "aparcamiento", label: "Aparcamiento", crit: "según la Tabla 2.1 del DB-SI" },
  { value: "generico", label: "Otro / genérico", crit: "según la Tabla 2.1 del DB-SI" },
];

const draftLRE = (x) => {
  const t = LRE_TIPOS.find((k) => k.value === (x.lre_tipo || "generico")) || LRE_TIPOS[6];
  const r = x.lre_riesgo || "bajo";
  return `El local «${x.nombre || "—"}» (${t.label.toLowerCase()}) se clasifica como local de riesgo especial de riesgo ${r} conforme a la Tabla 2.1 del CTE DB-SI, ${t.crit}. En consecuencia se dota de estructura ${x.lre_r || RIESGO_R[r]}, sectorización EI y las condiciones de acceso/vestíbulo de independencia exigidas para riesgo ${r}. Su superficie no se computa en la carga de fuego del sector.`;
};

const draftEscalera = (x) => {
  const tipo = x.esc_tipo === "especialmente_protegida" ? "especialmente protegida" : "protegida";
  const sit = x.esc_situacion === "exterior" ? "exterior" : "interior";
  const partes = [`La escalera «${x.nombre || "—"}» es una escalera ${tipo} ${sit}`];
  if (x.esc_anchura) partes.push(`de ${x.esc_anchura} m de anchura`);
  if (x.esc_capacidad) partes.push(`con capacidad de evacuación de ${x.esc_capacidad} personas`);
  if (x.esc_uso_restringido) partes.push("de uso restringido");
  const prot = tipo === "especialmente protegida"
    ? "vestíbulos de independencia y ventilación (natural o por sobrepresión)"
    : "puertas EI2 45-C5 y protección al fuego de la estructura y cerramientos";
  return `${partes.join(", ")}. Se justifica conforme al CTE DB-SI (SI 3) y DB-SUA: la caja constituye un recinto independiente con la resistencia al fuego exigida, ${prot}, anchura ≥ 1,00 m y continuidad hasta la salida de edificio. Al ser zona de paso peatonal de trabajadores, computa carga de fuego.`;
};

// Carga de fuego con catálogo (Tabla 1.3.5) + edición manual.
function CargaFuegoInline({ x, i, catalog, update }) {
  const cat = catalog.find((c) => c.category === x.actividad_cat);
  const isCustom = x.actividad_cat === CUSTOM;
  const almacen = x.modo === "almacenamiento";
  const selectCat = (v) => v === CUSTOM
    ? update({ actividad_cat: CUSTOM, subactividad: "" })
    : update({ actividad_cat: v, subactividad: "", qsi: undefined, qvi: undefined });
  const selectSub = (idx) => {
    const s = cat.subactivities[Number(idx)];
    update({ subactividad: s.name, modo: s.modo, qsi: s.modo === "produccion" ? s.qsi : undefined,
      qvi: s.modo === "almacenamiento" ? s.qvi : undefined, ci: s.ci, ra: s.ra, rmin: s.rmin ?? null });
  };
  return (
    <div className="mt-3 space-y-3 border-t border-border pt-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <Label className="text-xs">Actividad (Tabla 1.3.5)</Label>
          <Select value={x.actividad_cat || ""} onValueChange={selectCat}>
            <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-cat`}><SelectValue placeholder="Selecciona categoría" /></SelectTrigger>
            <SelectContent>
              {catalog.map((c) => <SelectItem key={c.category} value={c.category}>{c.category}</SelectItem>)}
              <SelectItem value={CUSTOM}>+ Actividad personalizada</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs">Subactividad (qs/qv, Ci, Rmin)</Label>
          {isCustom ? (
            <Input className="mt-1 h-8 rounded-sm" value={x.subactividad || ""} onChange={(e) => update({ subactividad: e.target.value })} placeholder="Descripción" data-testid={`estancia-${i}-sub`} />
          ) : (
            <Select value={cat ? String(cat.subactivities.findIndex((s) => s.name === x.subactividad)) : ""} onValueChange={selectSub} disabled={!cat}>
              <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-sub`}><SelectValue placeholder="Selecciona subactividad" /></SelectTrigger>
              <SelectContent>
                {(cat?.subactivities || []).map((s, k) => <SelectItem key={k} value={String(k)}>{s.name} · {s.modo === "almacenamiento" ? `qv ${s.qvi}` : `qs ${s.qsi}`} · Ci {s.ci}{s.rmin ? ` · Rmin ${s.rmin}` : ""}</SelectItem>)}
              </SelectContent>
            </Select>
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <div>
          <Label className="text-xs">Modo</Label>
          <Select value={x.modo || "produccion"} onValueChange={(v) => update({ modo: v })}>
            <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-modo`}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="produccion">Producción</SelectItem>
              <SelectItem value="almacenamiento">Almacenamiento</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {almacen ? (
          <>
            <div><Label className="text-xs">qv (MJ/m³)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.qvi ?? ""} onChange={(e) => update({ qvi: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-qvi`} /></div>
            <div><Label className="text-xs">hi (m)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.hi ?? ""} onChange={(e) => update({ hi: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-hi`} /></div>
          </>
        ) : (
          <div><Label className="text-xs">qs (MJ/m²)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.qsi ?? ""} onChange={(e) => update({ qsi: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-qsi`} /></div>
        )}
        <div><Label className="text-xs">Ci</Label><Input type="number" step={0.01} className="mt-1 h-8 rounded-sm font-mono" value={x.ci ?? 1.44} onChange={(e) => update({ ci: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-ci`} /></div>
        <div><Label className="text-xs">Ra</Label><Input type="number" step={0.1} className="mt-1 h-8 rounded-sm font-mono" value={x.ra ?? 1} onChange={(e) => update({ ra: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-ra`} /></div>
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
  const secById = Object.fromEntries(sectores.map((s) => [s.id, s]));

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
  const totalC = (sid) => deps.filter((x) => x.sector_id === sid && x.clase !== "lre").reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);

  return (
    <TooltipProvider>
      <div className="space-y-8" data-testid="sectores-step">
        {/* Sectores · full-width apilados */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-heading text-base">Sectores de incendio</h3>
            <Button variant="outline" size="sm" className="rounded-sm" onClick={addSector} data-testid="add-sector">
              <Plus className="mr-1.5 h-4 w-4" /> Añadir sector
            </Button>
          </div>
          {sectores.length === 0 && (
            <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">Sin sectores. Crea el primer sector de incendio.</p>
          )}
          <div className="space-y-3">
            {sectores.map((s, i) => {
              const cte = s.ambito === "cte";
              return (
                <div key={s.id} className="border border-border p-4" data-testid={`sector-card-${i}`}>
                  <div className="mb-3 flex items-center justify-between">
                    <Badge variant="outline" className="rounded-sm">
                      {cte ? <Building2 className="mr-1 h-3 w-3" /> : <Flame className="mr-1 h-3 w-3" />}
                      {cte ? "CTE DB-SI" : "RSCIEI"}
                    </Badge>
                    <span className="font-mono text-xs text-muted-foreground">{num(totalC(s.id))} m² construidos (sin LRE)</span>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeSector(s.id)} data-testid={`remove-sector-${i}`}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                    <div className="col-span-2 space-y-1.5 lg:col-span-1">
                      <Label>Nombre</Label>
                      <Input value={s.nombre || ""} onChange={(e) => updateSector(s.id, { nombre: e.target.value })} data-testid={`sector-${i}-nombre`} />
                    </div>
                    <div className="col-span-2 space-y-1.5 lg:col-span-1">
                      <Label>Actividad</Label>
                      <Input value={s.actividad || ""} onChange={(e) => updateSector(s.id, { actividad: e.target.value })} placeholder="Taller / Almacén / Oficinas" data-testid={`sector-${i}-actividad`} />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Ámbito</Label>
                      <Select value={s.ambito || "industrial"} onValueChange={(v) => updateSector(s.id, { ambito: v })}>
                        <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-ambito`}><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="industrial">Industrial (RSCIEI)</SelectItem>
                          <SelectItem value="cte">CTE (edificación)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    {cte ? (
                      <div className="space-y-1.5">
                        <Label>Uso CTE</Label>
                        <Select value={s.uso_cte || "Administrativo"} onValueChange={(v) => updateSector(s.id, { uso_cte: v })}>
                          <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-uso`}><SelectValue /></SelectTrigger>
                          <SelectContent>{usos.map((u) => <SelectItem key={u.value || u} value={u.value || u}>{u.label || u}</SelectItem>)}</SelectContent>
                        </Select>
                      </div>
                    ) : (
                      <div className="space-y-1.5">
                        <Label>Configuración</Label>
                        <Select value={s.config || "C"} onValueChange={(v) => updateSector(s.id, { config: v })}>
                          <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-config`}><SelectValue /></SelectTrigger>
                          <SelectContent>{configTypes.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
                        </Select>
                      </div>
                    )}
                    <div className="space-y-1.5">
                      <Label>Situación</Label>
                      <Select value={s.situacion || "sobre_rasante"} onValueChange={(v) => updateSector(s.id, { situacion: v })}>
                        <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-situacion`}><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="sobre_rasante">Sobre rasante</SelectItem>
                          <SelectItem value="bajo_rasante">Bajo rasante (sótano)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Nº de salidas</Label>
                      <Input type="number" min={1} value={s.num_salidas ?? 2} onChange={(e) => updateSector(s.id, { num_salidas: Number(e.target.value) })} data-testid={`sector-${i}-salidas`} />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Altura evac. (m)</Label>
                      <Input type="number" min={0} step={0.5} value={s.altura_evacuacion ?? 0} onChange={(e) => updateSector(s.id, { altura_evacuacion: Number(e.target.value) })} data-testid={`sector-${i}-altura`} />
                    </div>
                    <label className="col-span-2 flex items-center gap-2 text-sm sm:col-span-3 lg:col-span-4">
                      <Switch checked={!!s.rociadores} onCheckedChange={(v) => updateSector(s.id, { rociadores: v })} data-testid={`sector-${i}-rociadores`} />
                      Rociadores automáticos en todo el sector
                    </label>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Asignación de estancias + clasificación + carga de fuego */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-heading text-base">Asignación de estancias y carga de fuego</h3>
          </div>
          {deps.length === 0 ? (
            <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">No hay estancias. Vuelve al paso «Cuadro de superficies».</p>
          ) : sectores.length === 0 ? (
            <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">Crea al menos un sector para asignar las estancias.</p>
          ) : (
            <div className="space-y-2">
              {deps.map((x, i) => {
                const clase = x.clase || "normal";
                return (
                  <div key={x.id} className="border border-border p-3" data-testid={`estancia-row-${i}`}>
                    <div className="flex flex-wrap items-end gap-3">
                      <div className="min-w-[150px] flex-1">
                        <Label className="text-xs">Estancia</Label>
                        <p className="mt-1 truncate text-sm font-medium" title={x.nombre}>{x.nombre || `Estancia ${i + 1}`}</p>
                        <p className="font-mono text-xs text-muted-foreground">{num(x.sup_construida || 0)} m² constr.</p>
                      </div>
                      <div className="w-48">
                        <Label className="text-xs">Sector</Label>
                        <Select value={x.sector_id || ""} onValueChange={(v) => updateDep(x.id, { sector_id: v })}>
                          <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-sector`}><SelectValue placeholder="Asignar" /></SelectTrigger>
                          <SelectContent>{sectores.map((s) => <SelectItem key={s.id} value={s.id}>{s.nombre}</SelectItem>)}</SelectContent>
                        </Select>
                      </div>
                      <div className="w-56">
                        <div className="flex items-center gap-1">
                          <Label className="text-xs">Clasificación</Label>
                          {clase === "lre" && (
                            <Tooltip>
                              <TooltipTrigger asChild><Info className="h-3 w-3 cursor-help text-amber-600" data-testid={`estancia-${i}-lre-info`} /></TooltipTrigger>
                              <TooltipContent className="max-w-xs">Esta superficie NO se tiene en cuenta para el cálculo de la carga de fuego del sector, porque está contemplada como Local de Riesgo Especial (se evalúa por separado según la Tabla 2.1 del CTE DB-SI).</TooltipContent>
                            </Tooltip>
                          )}
                        </div>
                        <Select value={clase} onValueChange={(v) => setClase(x.id, v)}>
                          <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-clase`}><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="normal">Estancia normal</SelectItem>
                            <SelectItem value="lre"><span className="inline-flex items-center gap-1"><ShieldAlert className="h-3 w-3" /> Local de riesgo especial</span></SelectItem>
                            <SelectItem value="escalera_protegida"><span className="inline-flex items-center gap-1"><StretchHorizontal className="h-3 w-3" /> Escalera protegida</span></SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {clase === "lre" ? (
                      <div className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-4">
                        <div>
                          <Label className="text-xs">Riesgo (Tabla 2.1 DB-SI)</Label>
                          <Select value={x.lre_riesgo || "bajo"} onValueChange={(v) => updateDep(x.id, { lre_riesgo: v, lre_r: RIESGO_R[v] })}>
                            <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-lre-riesgo`}><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="bajo">Bajo</SelectItem>
                              <SelectItem value="medio">Medio</SelectItem>
                              <SelectItem value="alto">Alto</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label className="text-xs">Resistencia (R)</Label>
                          <Input className="mt-1 h-8 rounded-sm" value={x.lre_r || RIESGO_R[x.lre_riesgo || "bajo"]} onChange={(e) => updateDep(x.id, { lre_r: e.target.value })} data-testid={`estancia-${i}-lre-r`} />
                        </div>
                        <div className="col-span-2">
                          <Label className="text-xs">Tipo de local (Tabla 2.1)</Label>
                          <Select value={x.lre_tipo || "generico"} onValueChange={(v) => updateDep(x.id, { lre_tipo: v })}>
                            <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-lre-tipo`}><SelectValue /></SelectTrigger>
                            <SelectContent>{LRE_TIPOS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2 sm:col-span-4">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs">Justificación (Tabla 2.1: superficie, volumen, potencia…)</Label>
                            <Button variant="ghost" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => updateDep(x.id, { lre_justificacion: draftLRE(x) })} data-testid={`estancia-${i}-lre-gen`}><Wand2 className="mr-1 h-3 w-3" /> Generar</Button>
                          </div>
                          <Textarea className="mt-1 min-h-[64px] rounded-sm text-sm" value={x.lre_justificacion || ""} onChange={(e) => updateDep(x.id, { lre_justificacion: e.target.value })} placeholder="Pulsa «Generar» para redactarla a partir del tipo y el riesgo, o escribe tu justificación." data-testid={`estancia-${i}-lre-just`} />
                        </div>
                      </div>
                    ) : clase === "escalera_protegida" ? (
                      <>
                        <div className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-4">
                          <div>
                            <Label className="text-xs">Tipo</Label>
                            <Select value={x.esc_tipo || "protegida"} onValueChange={(v) => updateDep(x.id, { esc_tipo: v })}>
                              <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-esc-tipo`}><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="protegida">Protegida</SelectItem>
                                <SelectItem value="especialmente_protegida">Especialmente protegida</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label className="text-xs">Situación</Label>
                            <Select value={x.esc_situacion || "interior"} onValueChange={(v) => updateDep(x.id, { esc_situacion: v })}>
                              <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-esc-situacion`}><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="interior">Interior</SelectItem>
                                <SelectItem value="exterior">Exterior</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div><Label className="text-xs">Anchura (m)</Label><Input type="number" step={0.1} className="mt-1 h-8 rounded-sm font-mono" value={x.esc_anchura ?? ""} onChange={(e) => updateDep(x.id, { esc_anchura: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-esc-anchura`} /></div>
                          <div><Label className="text-xs">Capacidad evac. (pers.)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.esc_capacidad ?? ""} onChange={(e) => updateDep(x.id, { esc_capacidad: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-esc-capacidad`} /></div>
                          <label className="col-span-2 flex items-center gap-2 text-sm sm:col-span-4">
                            <Switch checked={!!x.esc_uso_restringido} onCheckedChange={(v) => updateDep(x.id, { esc_uso_restringido: v })} data-testid={`estancia-${i}-esc-restringido`} />
                            Uso restringido
                          </label>
                          <div className="col-span-2 sm:col-span-4">
                            <div className="flex items-center justify-between">
                              <Label className="text-xs">Justificación CTE (protección, ventilación/vestíbulo, resistencia, evacuación)</Label>
                              <Button variant="ghost" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => updateDep(x.id, { esc_justificacion: draftEscalera(x) })} data-testid={`estancia-${i}-esc-gen`}><Wand2 className="mr-1 h-3 w-3" /> Generar</Button>
                            </div>
                            <Textarea className="mt-1 min-h-[64px] rounded-sm text-sm" value={x.esc_justificacion || ""} onChange={(e) => updateDep(x.id, { esc_justificacion: e.target.value })} placeholder="Pulsa «Generar» para redactarla a partir de los parámetros, o escribe tu justificación CTE." data-testid={`estancia-${i}-esc-just`} />
                          </div>
                        </div>
                        <p className="mt-2 text-xs text-muted-foreground">La escalera protegida SÍ computa carga de fuego (zona de paso peatonal); su protección se justifica por el CTE y consta en el informe.</p>
                        <CargaFuegoInline x={x} i={i} catalog={catalog} update={(p) => updateDep(x.id, p)} />
                      </>
                    ) : (
                      <CargaFuegoInline x={x} i={i} catalog={catalog} update={(p) => updateDep(x.id, p)} />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
