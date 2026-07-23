import { Fragment } from "react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { NumberInput } from "@/components/NumberInput";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { num } from "@/lib/format";

const CUSTOM = "__custom__";

function ocupacionDe(dep) {
  if (dep.sin_ocupacion) return 0;
  if (dep.ocupacion_custom) {
    const m = Number(dep.ocupacion_manual);
    return dep.ocupacion_manual === "" || dep.ocupacion_manual == null || Number.isNaN(m) ? null : Math.ceil(m);
  }
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
      updateDep(dep.id, { sin_ocupacion: false, ocupacion_custom: true, densidad: "",
        uso_ocupacion: dep.uso_ocupacion || "Personalizado" });
      return;
    }
    const p = densities[Number(value)];
    if (!p) return;
    const base = { ocupacion_custom: false, ocupacion_manual: "", ocupacion_nota: "" };
    if (p.densidad == null) updateDep(dep.id, { ...base, sin_ocupacion: true, densidad: "", uso_ocupacion: p.uso });
    else updateDep(dep.id, { ...base, sin_ocupacion: false, densidad: p.densidad, uso_ocupacion: p.uso });
  };

  const presetIndex = (dep) => {
    if (dep.ocupacion_custom) return CUSTOM;
    if (dep.sin_ocupacion) return String(densities.findIndex((p) => p.densidad == null));
    const idx = densities.findIndex((p) => p.densidad != null && Math.abs(p.densidad - Number(dep.densidad)) < 1e-6 && p.uso === dep.uso_ocupacion);
    return idx >= 0 ? String(idx) : CUSTOM;
  };

  const total = deps.reduce((a, x) => a + (ocupacionDe(x) || 0), 0);

  if (deps.length === 0)
    return <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground" data-testid="ocupacion-empty">Primero añade dependencias en el paso «Cuadro de superficies».</p>;

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
              const custom = !!x.ocupacion_custom;
              const noteMissing = custom && !(x.ocupacion_nota || "").trim();
              return (
                <Fragment key={x.id}>
                  <tr className="border-b border-border" data-testid={`ocupacion-row-${i}`}>
                    <td className="px-3 py-1.5 font-medium">{x.nombre || "—"}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{secName[x.sector_id] || "—"}</td>
                    <td className="px-3 py-1.5 text-right font-mono">{num(Number(x.sup_util) || Number(x.sup_construida) || 0, 2)}</td>
                    <td className="px-3 py-1.5">
                      <Select value={presetIndex(x)} onValueChange={(v) => selectPreset(x, v)}>
                        <SelectTrigger className="h-8 w-56 rounded-sm" data-testid={`ocupacion-${i}-preset`}><SelectValue placeholder="Selecciona uso" /></SelectTrigger>
                        <SelectContent>
                          {densities.map((p, idx) => <SelectItem key={idx} value={String(idx)}>{p.uso}{p.densidad != null ? ` · ${p.densidad} m²/p` : ""}</SelectItem>)}
                          <SelectItem value={CUSTOM}>+ Ocupación personalizada (a mano)</SelectItem>
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-3 py-1.5">
                      {custom ? (
                        <span className="block text-right font-mono text-muted-foreground">—</span>
                      ) : (
                        <NumberInput min={0} className="h-8 w-20 rounded-sm text-right font-mono" disabled={x.sin_ocupacion}
                          value={x.sin_ocupacion ? "" : (x.densidad ?? "")} data-testid={`ocupacion-${i}-densidad`}
                          onChange={(v) => updateDep(x.id, { densidad: v, sin_ocupacion: false })} />
                      )}
                    </td>
                    <td className="px-3 py-1.5">
                      {custom ? (
                        <NumberInput integer min={0} className="h-8 w-24 rounded-sm text-right font-mono font-semibold"
                          value={x.ocupacion_manual ?? ""} data-testid={`ocupacion-${i}-manual`}
                          onChange={(v) => updateDep(x.id, { ocupacion_manual: v })} />
                      ) : (
                        <span className="block text-right font-mono font-semibold" data-testid={`ocupacion-${i}-result`}>
                          {x.sin_ocupacion ? "—" : (oc == null ? "?" : oc)}
                        </span>
                      )}
                    </td>
                  </tr>
                  {custom && (
                    <tr className="border-b border-border bg-amber-50/50" data-testid={`ocupacion-${i}-note-row`}>
                      <td colSpan={6} className="px-3 py-2">
                        <Label className="text-xs text-amber-800">Motivo de la ocupación personalizada (obligatorio) *</Label>
                        <Textarea
                          className="mt-1 min-h-[52px] rounded-sm text-sm"
                          value={x.ocupacion_nota || ""}
                          onChange={(e) => updateDep(x.id, { ocupacion_nota: e.target.value })}
                          placeholder="Ej.: ocupación fijada por proyecto de actividad / aforo autorizado / uso específico no tabulado en la Tabla 2.1."
                          data-testid={`ocupacion-${i}-nota`}
                          data-invalid={noteMissing ? "true" : undefined}
                          aria-invalid={noteMissing ? true : undefined}
                        />
                        {noteMissing && <p className="mt-1 text-xs text-destructive">Indica el motivo de la ocupación personalizada para continuar.</p>}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            <tr className="bg-secondary/40">
              <td className="px-3 py-2 font-medium" colSpan={5}>Ocupación total del establecimiento</td>
              <td className="px-3 py-2 text-right font-mono font-bold" data-testid="ocupacion-total">{total} pers.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">La ocupación se calcula como <span className="font-mono">techo(superficie útil / densidad)</span> según la Tabla 2.1 del CTE DB-SI. En «ocupación personalizada» se introduce el nº de personas a mano y se justifica con una nota.</p>
    </div>
  );
}
