import { Plus, Trash2, Flame, Building2, ShieldAlert } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { num } from "@/lib/format";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

const RIESGO_R = { bajo: "R 90", medio: "R 120", alto: "R 180" };

// Paso 2 · Sectores de incendio: crear sectores, asignar estancias, marcar LRE y carga de fuego.
export function SectoresStep({ data, setData, schema = {} }) {
  const sectores = data.sectores || [];
  const deps = data.dependencias || [];
  const configTypes = (schema.config_types || []).filter((c) => c.value !== "D");
  const usos = schema.dbsi_uses || [];
  const secById = Object.fromEntries(sectores.map((s) => [s.id, s]));

  const addSector = () =>
    setData((d) => ({
      ...d,
      sectores: [...(d.sectores || []), {
        id: genId(), nombre: `Sector ${(d.sectores || []).length + 1}`, actividad: "",
        ambito: "industrial", config: "C", uso_cte: "Administrativo",
        situacion: "sobre_rasante", num_salidas: 2, altura_evacuacion: 0,
        rociadores: false, fachada_accesible: false,
      }],
    }));
  const updateSector = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));
  const removeSector = (id) =>
    setData((d) => ({
      ...d,
      sectores: d.sectores.filter((s) => s.id !== id),
      dependencias: (d.dependencias || []).map((x) => (x.sector_id === id ? { ...x, sector_id: "" } : x)),
    }));

  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));

  const totalC = (sid) => deps.filter((x) => x.sector_id === sid && !x.es_lre).reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);

  return (
    <div className="space-y-8" data-testid="sectores-step">
      {/* Sectores */}
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
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {sectores.map((s, i) => {
            const cte = s.ambito === "cte";
            return (
              <div key={s.id} className="border border-border p-4" data-testid={`sector-card-${i}`}>
                <div className="mb-3 flex items-center justify-between">
                  <Badge variant="outline" className="rounded-sm">
                    {cte ? <Building2 className="mr-1 h-3 w-3" /> : <Flame className="mr-1 h-3 w-3" />}
                    {cte ? "CTE DB-SI" : "RSCIEI"}
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">{num(totalC(s.id))} m² construidos</span>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeSector(s.id)} data-testid={`remove-sector-${i}`}><Trash2 className="h-4 w-4" /></Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2 space-y-1.5">
                    <Label>Nombre del sector</Label>
                    <Input value={s.nombre || ""} onChange={(e) => updateSector(s.id, { nombre: e.target.value })} data-testid={`sector-${i}-nombre`} />
                  </div>
                  <div className="col-span-2 space-y-1.5">
                    <Label>Actividad</Label>
                    <Input value={s.actividad || ""} onChange={(e) => updateSector(s.id, { actividad: e.target.value })} placeholder="p. ej. Taller / Almacén / Oficinas" data-testid={`sector-${i}-actividad`} />
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
                        <SelectContent>
                          {usos.map((u) => <SelectItem key={u.value || u} value={u.value || u}>{u.label || u}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      <Label>Configuración</Label>
                      <Select value={s.config || "C"} onValueChange={(v) => updateSector(s.id, { config: v })}>
                        <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-config`}><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {configTypes.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  <div className="space-y-1.5">
                    <Label>Nº de salidas</Label>
                    <Input type="number" min={1} value={s.num_salidas ?? 2} onChange={(e) => updateSector(s.id, { num_salidas: Number(e.target.value) })} data-testid={`sector-${i}-salidas`} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Altura evac. (m)</Label>
                    <Input type="number" min={0} step={0.5} value={s.altura_evacuacion ?? 0} onChange={(e) => updateSector(s.id, { altura_evacuacion: Number(e.target.value) })} data-testid={`sector-${i}-altura`} />
                  </div>
                  <label className="col-span-2 flex items-center gap-2 text-sm">
                    <Switch checked={!!s.rociadores} onCheckedChange={(v) => updateSector(s.id, { rociadores: v })} data-testid={`sector-${i}-rociadores`} />
                    Rociadores automáticos en todo el sector (×2 sup. máx.)
                  </label>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Asignación de estancias + carga de fuego */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-heading text-base">Asignación de estancias y carga de fuego</h3>
          <span className="text-xs text-muted-foreground">Los locales de riesgo especial (LRE) no entran en el cálculo de la carga de fuego.</span>
        </div>
        {deps.length === 0 ? (
          <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">No hay estancias. Vuelve al paso «Cuadro de superficies».</p>
        ) : sectores.length === 0 ? (
          <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">Crea al menos un sector para asignar las estancias.</p>
        ) : (
          <div className="space-y-2">
            {deps.map((x, i) => {
              const sec = secById[x.sector_id];
              const cte = sec?.ambito === "cte";
              return (
                <div key={x.id} className="border border-border p-3" data-testid={`estancia-row-${i}`}>
                  <div className="flex flex-wrap items-end gap-3">
                    <div className="min-w-[160px] flex-1">
                      <Label className="text-xs">Estancia</Label>
                      <p className="mt-1 truncate text-sm font-medium" title={x.nombre}>{x.nombre || `Estancia ${i + 1}`}</p>
                      <p className="font-mono text-xs text-muted-foreground">{num(x.sup_construida || 0)} m² constr.</p>
                    </div>
                    <div className="w-52">
                      <Label className="text-xs">Sector</Label>
                      <Select value={x.sector_id || ""} onValueChange={(v) => updateDep(x.id, { sector_id: v })}>
                        <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-sector`}><SelectValue placeholder="Asignar" /></SelectTrigger>
                        <SelectContent>
                          {sectores.map((s) => <SelectItem key={s.id} value={s.id}>{s.nombre}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <label className="flex items-center gap-2 pb-1.5 text-sm">
                      <Switch checked={!!x.es_lre} onCheckedChange={(v) => updateDep(x.id, { es_lre: v })} data-testid={`estancia-${i}-lre`} />
                      <ShieldAlert className="h-3.5 w-3.5 text-amber-600" /> LRE
                    </label>
                  </div>

                  {x.es_lre ? (
                    <div className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-4">
                      <div>
                        <Label className="text-xs">Riesgo LRE</Label>
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
                    </div>
                  ) : (
                    <div className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-5">
                      <div>
                        <Label className="text-xs">Modo</Label>
                        <Select value={x.modo || "produccion"} onValueChange={(v) => updateDep(x.id, { modo: v })}>
                          <SelectTrigger className="mt-1 h-8 rounded-sm" data-testid={`estancia-${i}-modo`}><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="produccion">Producción</SelectItem>
                            <SelectItem value="almacenamiento">Almacenamiento</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {x.modo === "almacenamiento" ? (
                        <>
                          <div><Label className="text-xs">qvi (MJ/m³)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.qvi ?? ""} onChange={(e) => updateDep(x.id, { qvi: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-qvi`} /></div>
                          <div><Label className="text-xs">hi (m)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.hi ?? ""} onChange={(e) => updateDep(x.id, { hi: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-hi`} /></div>
                        </>
                      ) : (
                        <div><Label className="text-xs">qsi (MJ/m²)</Label><Input type="number" className="mt-1 h-8 rounded-sm font-mono" value={x.qsi ?? ""} onChange={(e) => updateDep(x.id, { qsi: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-qsi`} /></div>
                      )}
                      <div><Label className="text-xs">Ci</Label><Input type="number" step={0.01} className="mt-1 h-8 rounded-sm font-mono" value={x.ci ?? 1.44} onChange={(e) => updateDep(x.id, { ci: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-ci`} /></div>
                      <div><Label className="text-xs">Ra</Label><Input type="number" step={0.1} className="mt-1 h-8 rounded-sm font-mono" value={x.ra ?? 1} onChange={(e) => updateDep(x.id, { ra: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`estancia-${i}-ra`} /></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
