import { Plus, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { num } from "@/lib/format";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const CUSTOM = "__custom__";

function ocupacionDe(dep) {
  if (dep.sin_ocupacion) return 0;
  const dens = Number(dep.densidad);
  if (!dens || dens <= 0) return null;
  const sup = Number(dep.superficie) || 0;
  return sup <= 0 ? 0 : Math.ceil(sup / dens);
}

export function DbsiOcupacionStep({ data, setData, densities = [] }) {
  const deps = data.dependencias || [];

  const addDep = () =>
    setData((d) => ({ ...d, dependencias: [...(d.dependencias || []), { id: genId(), nombre: "", superficie: "", densidad: "", sin_ocupacion: false, uso_ocupacion: "" }] }));
  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));
  const removeDep = (id) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.filter((x) => x.id !== id) }));

  const selectPreset = (dep, value) => {
    if (value === CUSTOM) { updateDep(dep.id, { sin_ocupacion: false, uso_ocupacion: dep.uso_ocupacion || "Personalizado" }); return; }
    const p = densities[Number(value)];
    if (!p) return;
    if (p.densidad == null) updateDep(dep.id, { sin_ocupacion: true, densidad: "", uso_ocupacion: p.uso });
    else updateDep(dep.id, { sin_ocupacion: false, densidad: p.densidad, uso_ocupacion: p.uso });
  };
  const presetIndex = (dep) => {
    if (dep.sin_ocupacion) return String(densities.findIndex((p) => p.densidad == null));
    const idx = densities.findIndex((p) => p.densidad != null && Math.abs(p.densidad - Number(dep.densidad)) < 1e-6 && p.uso === dep.uso_ocupacion);
    return idx >= 0 ? String(idx) : CUSTOM;
  };

  const total = deps.reduce((a, x) => a + (ocupacionDe(x) || 0), 0);

  return (
    <div className="space-y-4" data-testid="dbsi-ocupacion-step">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Añada las dependencias/zonas del edificio y su densidad de ocupación (CTE DB-SI Tabla 2.1).</p>
        <Button variant="outline" size="sm" className="rounded-sm" onClick={addDep} data-testid="dbsi-add-dep">
          <Plus className="mr-1.5 h-4 w-4" /> Añadir zona
        </Button>
      </div>
      {deps.length === 0 ? (
        <p className="border border-dashed border-border py-6 text-center text-sm text-muted-foreground">Sin zonas. Añade la primera zona del edificio.</p>
      ) : (
        <div className="overflow-x-auto border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-3 py-2 font-semibold">Zona</th>
                <th className="px-3 py-2 text-right font-semibold">Superficie (m²)</th>
                <th className="px-3 py-2 font-semibold">Uso / densidad</th>
                <th className="px-3 py-2 text-right font-semibold">m²/p</th>
                <th className="px-3 py-2 text-right font-semibold">Ocupación</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {deps.map((x, i) => {
                const oc = ocupacionDe(x);
                return (
                  <tr key={x.id} className="border-b border-border last:border-0" data-testid={`dbsi-dep-${i}`}>
                    <td className="px-3 py-1.5"><Input className="h-8 rounded-sm" value={x.nombre || ""} onChange={(e) => updateDep(x.id, { nombre: e.target.value })} placeholder="Nombre" data-testid={`dbsi-dep-${i}-nombre`} /></td>
                    <td className="px-3 py-1.5"><Input type="number" min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.superficie ?? ""} onChange={(e) => updateDep(x.id, { superficie: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`dbsi-dep-${i}-sup`} /></td>
                    <td className="px-3 py-1.5">
                      <Select value={presetIndex(x)} onValueChange={(v) => selectPreset(x, v)}>
                        <SelectTrigger className="h-8 w-56 rounded-sm" data-testid={`dbsi-dep-${i}-preset`}><SelectValue placeholder="Selecciona uso" /></SelectTrigger>
                        <SelectContent>
                          {densities.map((p, idx) => <SelectItem key={idx} value={String(idx)}>{p.uso}{p.densidad != null ? ` · ${p.densidad} m²/p` : ""}</SelectItem>)}
                          <SelectItem value={CUSTOM}>+ Densidad personalizada</SelectItem>
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-3 py-1.5"><Input type="number" min={0} step={0.5} className="h-8 w-20 rounded-sm text-right font-mono" disabled={x.sin_ocupacion} value={x.sin_ocupacion ? "" : (x.densidad ?? "")} onChange={(e) => updateDep(x.id, { densidad: e.target.value === "" ? "" : Number(e.target.value), sin_ocupacion: false })} data-testid={`dbsi-dep-${i}-densidad`} /></td>
                    <td className="px-3 py-1.5 text-right font-mono font-semibold" data-testid={`dbsi-dep-${i}-result`}>{x.sin_ocupacion ? "—" : (oc == null ? "?" : oc)}</td>
                    <td className="px-3 py-1.5"><Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeDep(x.id)} data-testid={`dbsi-dep-${i}-remove`}><Trash2 className="h-4 w-4" /></Button></td>
                  </tr>
                );
              })}
              <tr className="bg-secondary/40">
                <td className="px-3 py-2 font-medium" colSpan={4}>Ocupación total</td>
                <td className="px-3 py-2 text-right font-mono font-bold" data-testid="dbsi-ocupacion-total">{total}</td>
                <td />
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
