import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { num } from "@/lib/format";

const CUSTOM = "__custom__";

function ocupacionDe(dep) {
  if (dep.sin_ocupacion) return 0;
  const dens = Number(dep.densidad);
  if (!dens || dens <= 0) return null;
  const sup = Number(dep.sup_util) || Number(dep.sup_construida) || 0;
  if (sup <= 0) return 0;
  return Math.ceil(sup / dens);
}

export function OcupacionStep({ data, setData, densities = [] }) {
  const deps = data.dependencias || [];
  const sectores = data.sectores || [];
  const secName = Object.fromEntries(sectores.map((s) => [s.id, s.nombre]));

  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));

  const selectPreset = (dep, value) => {
    if (value === CUSTOM) {
      updateDep(dep.id, { sin_ocupacion: false, uso_ocupacion: dep.uso_ocupacion || "Personalizado" });
      return;
    }
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

  if (deps.length === 0)
    return <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground" data-testid="ocupacion-empty">Primero añade dependencias en el paso «Superficies y sectores».</p>;

  return (
    <div className="space-y-4" data-testid="ocupacion-step">
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <th className="px-3 py-2 font-semibold">Dependencia</th>
              <th className="px-3 py-2 font-semibold">Sector</th>
              <th className="px-3 py-2 text-right font-semibold">Sup. (m²)</th>
              <th className="px-3 py-2 font-semibold">Uso / densidad (CTE)</th>
              <th className="px-3 py-2 text-right font-semibold">m²/persona</th>
              <th className="px-3 py-2 text-right font-semibold">Ocupación</th>
            </tr>
          </thead>
          <tbody>
            {deps.map((x, i) => {
              const oc = ocupacionDe(x);
              return (
                <tr key={x.id} className="border-b border-border last:border-0" data-testid={`ocupacion-row-${i}`}>
                  <td className="px-3 py-1.5 font-medium">{x.nombre || "—"}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">{secName[x.sector_id] || "—"}</td>
                  <td className="px-3 py-1.5 text-right font-mono">{num(Number(x.sup_util) || Number(x.sup_construida) || 0, 2)}</td>
                  <td className="px-3 py-1.5">
                    <Select value={presetIndex(x)} onValueChange={(v) => selectPreset(x, v)}>
                      <SelectTrigger className="h-8 w-56 rounded-sm" data-testid={`ocupacion-${i}-preset`}><SelectValue placeholder="Selecciona uso" /></SelectTrigger>
                      <SelectContent>
                        {densities.map((p, idx) => <SelectItem key={idx} value={String(idx)}>{p.uso}{p.densidad != null ? ` · ${p.densidad} m²/p` : ""}</SelectItem>)}
                        <SelectItem value={CUSTOM}>+ Densidad personalizada</SelectItem>
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="px-3 py-1.5">
                    <Input type="number" min={0} step={0.5} className="h-8 w-20 rounded-sm text-right font-mono" disabled={x.sin_ocupacion}
                      value={x.sin_ocupacion ? "" : (x.densidad ?? "")} data-testid={`ocupacion-${i}-densidad`}
                      onChange={(e) => updateDep(x.id, { densidad: e.target.value === "" ? "" : Number(e.target.value), sin_ocupacion: false })} />
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono font-semibold" data-testid={`ocupacion-${i}-result`}>
                    {x.sin_ocupacion ? "—" : (oc == null ? "?" : oc)}
                  </td>
                </tr>
              );
            })}
            <tr className="bg-secondary/40">
              <td className="px-3 py-2 font-medium" colSpan={5}>Ocupación total del establecimiento</td>
              <td className="px-3 py-2 text-right font-mono font-bold" data-testid="ocupacion-total">{total} pers.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">La ocupación se calcula como <span className="font-mono">techo(superficie útil / densidad)</span> según la Tabla 2.1 del CTE DB-SI.</p>
    </div>
  );
}
