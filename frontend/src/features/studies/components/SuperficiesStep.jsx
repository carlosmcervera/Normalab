import { Plus, Trash2, Layers } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { num } from "@/lib/format";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

export function SuperficiesStep({ data, setData, configTypes = [] }) {
  const sectores = data.sectores || [];
  const deps = data.dependencias || [];
  const estConfig = data.establecimiento?.config || "C";

  const addSector = () =>
    setData((d) => ({
      ...d,
      sectores: [...(d.sectores || []), {
        id: genId(), nombre: `Sector ${(d.sectores || []).length + 1}`, tipo: "sector",
        planta: "", config: estConfig, situacion: "sobre_rasante", num_salidas: 2,
        fachada_accesible: false, rociadores: false, altura_evacuacion: 0, cubierta_ligera: false, ra: "",
      }],
    }));
  const updateSector = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));
  const removeSector = (id) =>
    setData((d) => ({
      ...d,
      sectores: d.sectores.filter((s) => s.id !== id),
      dependencias: d.dependencias.map((x) => (x.sector_id === id ? { ...x, sector_id: "" } : x)),
    }));

  const addDep = () =>
    setData((d) => ({
      ...d,
      dependencias: [...(d.dependencias || []), {
        id: genId(), nombre: "", planta: "", sup_util: "", sup_construida: "",
        sector_id: (d.sectores?.[0]?.id) || "", modo: "produccion", ci: 1.44,
      }],
    }));
  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));
  const removeDep = (id) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.filter((x) => x.id !== id) }));

  const sectorTotal = (sid) =>
    deps.filter((x) => x.sector_id === sid).reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);

  return (
    <div className="space-y-8" data-testid="superficies-step">
      {/* Sectores */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-heading text-base">Sectores de incendio</h3>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={addSector} data-testid="add-sector">
            <Plus className="mr-1.5 h-4 w-4" /> Añadir sector
          </Button>
        </div>
        {sectores.length === 0 && (
          <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">
            Sin sectores. Crea al menos un sector de incendio.
          </p>
        )}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {sectores.map((s, i) => (
            <div key={s.id} className="border border-border p-4" data-testid={`sector-card-${i}`}>
              <div className="mb-3 flex items-center justify-between">
                <Badge variant="outline" className="rounded-sm"><Layers className="mr-1 h-3 w-3" /> {s.tipo === "area_exterior" ? "Área exterior" : "Sector"}</Badge>
                <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeSector(s.id)} data-testid={`remove-sector-${i}`}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2 space-y-1.5">
                  <Label>Nombre</Label>
                  <Input value={s.nombre || ""} onChange={(e) => updateSector(s.id, { nombre: e.target.value })} data-testid={`sector-${i}-nombre`} />
                </div>
                <div className="space-y-1.5">
                  <Label>Tipo</Label>
                  <Select value={s.tipo || "sector"} onValueChange={(v) => updateSector(s.id, { tipo: v })}>
                    <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-tipo`}><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sector">Sector de incendio</SelectItem>
                      <SelectItem value="area_exterior">Área exterior (tipo D)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Planta</Label>
                  <Input value={s.planta || ""} onChange={(e) => updateSector(s.id, { planta: e.target.value })} placeholder="Pl. Baja" data-testid={`sector-${i}-planta`} />
                </div>
                {s.tipo !== "area_exterior" && (
                  <div className="col-span-2 space-y-1.5">
                    <Label>Configuración (Anexo I)</Label>
                    <Select value={s.config || estConfig} onValueChange={(v) => updateSector(s.id, { config: v })}>
                      <SelectTrigger className="rounded-sm" data-testid={`sector-${i}-config`}><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {configTypes.filter((c) => c.value !== "D").map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
              <p className="mt-3 border-t border-border pt-2 font-mono text-xs text-muted-foreground">
                Superficie construida: <span className="font-semibold text-foreground">{num(sectorTotal(s.id), 2)} m²</span>
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Dependencias */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-heading text-base">Cuadro de superficies (dependencias)</h3>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={addDep} disabled={sectores.length === 0} data-testid="add-dependencia">
            <Plus className="mr-1.5 h-4 w-4" /> Añadir dependencia
          </Button>
        </div>
        {deps.length === 0 ? (
          <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">
            Sin dependencias. Añade las estancias/zonas con sus superficies útil y construida.
          </p>
        ) : (
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="px-3 py-2 font-semibold">Dependencia</th>
                  <th className="px-3 py-2 font-semibold">Planta</th>
                  <th className="px-3 py-2 text-right font-semibold">S. útil (m²)</th>
                  <th className="px-3 py-2 text-right font-semibold">S. construida (m²)</th>
                  <th className="px-3 py-2 font-semibold">Sector</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {deps.map((x, i) => (
                  <tr key={x.id} className="border-b border-border last:border-0" data-testid={`dep-row-${i}`}>
                    <td className="px-3 py-1.5">
                      <Input className="h-8 rounded-sm" value={x.nombre || ""} onChange={(e) => updateDep(x.id, { nombre: e.target.value })} placeholder="Nombre" data-testid={`dep-${i}-nombre`} />
                    </td>
                    <td className="px-3 py-1.5">
                      <Input className="h-8 w-20 rounded-sm" value={x.planta || ""} onChange={(e) => updateDep(x.id, { planta: e.target.value })} data-testid={`dep-${i}-planta`} />
                    </td>
                    <td className="px-3 py-1.5">
                      <Input type="number" min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.sup_util ?? ""} onChange={(e) => updateDep(x.id, { sup_util: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`dep-${i}-util`} />
                    </td>
                    <td className="px-3 py-1.5">
                      <Input type="number" min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.sup_construida ?? ""} onChange={(e) => updateDep(x.id, { sup_construida: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`dep-${i}-construida`} />
                    </td>
                    <td className="px-3 py-1.5">
                      <Select value={x.sector_id || ""} onValueChange={(v) => updateDep(x.id, { sector_id: v })}>
                        <SelectTrigger className="h-8 w-40 rounded-sm" data-testid={`dep-${i}-sector`}><SelectValue placeholder="Asignar" /></SelectTrigger>
                        <SelectContent>
                          {sectores.map((s) => <SelectItem key={s.id} value={s.id}>{s.nombre}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-3 py-1.5">
                      <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeDep(x.id)} data-testid={`remove-dep-${i}`}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
