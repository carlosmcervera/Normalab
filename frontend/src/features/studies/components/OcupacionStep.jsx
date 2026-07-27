import { Fragment, useState } from "react";
import { useParams } from "react-router-dom";
import { Sparkles, Loader2, Check } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { NumberInput } from "@/components/NumberInput";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
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
  const { studyId } = useParams();
  const deps = data.dependencias || [];
  const plantas = data.plantas || [];
  const [aiLoading, setAiLoading] = useState(false);
  const [proposals, setProposals] = useState(null);

  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));

  const runAi = async () => {
    setAiLoading(true);
    try {
      const estancias = deps.map((x) => ({ id: x.id, nombre: x.nombre, superficie: Number(x.sup_util) || Number(x.sup_construida) || 0 }));
      const usos = densities.map((p) => ({ uso: p.uso, densidad: p.densidad ?? null }));
      const res = await api.post(`/studies/${studyId}/ai-ocupacion`, { estancias, usos });
      const props = (res.data.propuestas || []).filter((p) => p.id);
      if (!props.length) return toast.error("La IA no ha devuelto propuestas.");
      setProposals(props);
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setAiLoading(false);
    }
  };

  const applyProposals = () => {
    setData((d) => ({
      ...d,
      dependencias: d.dependencias.map((x) => {
        const p = proposals.find((q) => q.id === x.id);
        if (!p) return x;
        return { ...x, uso_ocupacion: p.uso, densidad: p.densidad ?? "",
          sin_ocupacion: p.densidad == null, ocupacion_custom: false, ocupacion_manual: "", ocupacion_nota: "" };
      }),
    }));
    toast.success(`Propuesta aplicada a ${proposals.length} estancia(s).`);
    setProposals(null);
  };

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
  const nombresPlanta = plantas.map((p) => p.nombre);
  const groups = [
    ...plantas.map((p) => ({ key: p.nombre, label: p.nombre, filas: deps.filter((x) => x.planta === p.nombre) })),
    { key: "__sin__", label: "Sin planta asignada", filas: deps.filter((x) => !x.planta || !nombresPlanta.includes(x.planta)) },
  ].filter((g) => g.filas.length > 0);

  if (deps.length === 0)
    return <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground" data-testid="ocupacion-empty">Primero añade dependencias en el paso «Cuadro de superficies».</p>;

  return (
    <div className="space-y-4" data-testid="ocupacion-step">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">Asigna a cada estancia su uso y densidad (Tabla 2.1 CTE DB-SI). Las estancias se agrupan por planta con la ocupación total de cada una.</p>
        <Button variant="outline" size="sm" className="rounded-sm shrink-0" onClick={runAi} disabled={aiLoading || deps.length === 0} data-testid="ai-ocupacion-btn">
          {aiLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />} Proponer ocupación con IA
        </Button>
      </div>

      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <th className="px-3 py-2 font-semibold">Dependencia</th>
              <th className="px-3 py-2 text-right font-semibold">Sup. (m²)</th>
              <th className="px-3 py-2 font-semibold">Uso / densidad (CTE)</th>
              <th className="px-3 py-2 text-right font-semibold">m²/persona</th>
              <th className="px-3 py-2 text-right font-semibold">Ocupación</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => {
              const sub = g.filas.reduce((a, x) => a + (ocupacionDe(x) || 0), 0);
              return (
                <Fragment key={g.key}>
                  <tr className="bg-secondary/25">
                    <td colSpan={5} className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-foreground/80" data-testid={`ocupacion-group-${g.label}`}>{g.label} · {g.filas.length} estancia(s)</td>
                  </tr>
                  {g.filas.map((x) => {
                    const i = deps.indexOf(x);
                    const oc = ocupacionDe(x);
                    const custom = !!x.ocupacion_custom;
                    const noteMissing = custom && !(x.ocupacion_nota || "").trim();
                    return (
                      <Fragment key={x.id}>
                        <tr className="border-b border-border" data-testid={`ocupacion-row-${i}`}>
                          <td className="px-3 py-1.5 font-medium">{x.nombre || "—"}</td>
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
                            <td colSpan={5} className="px-3 py-2">
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
                  <tr className="border-b border-border bg-secondary/10">
                    <td colSpan={4} className="px-3 py-1.5 text-right text-xs italic text-muted-foreground">Subtotal ocupación · {g.label}</td>
                    <td className="px-3 py-1.5 text-right font-mono font-bold" data-testid={`ocupacion-planta-${g.label}`}>{sub} pers.</td>
                  </tr>
                </Fragment>
              );
            })}
            <tr className="bg-secondary/40">
              <td className="px-3 py-2 font-medium" colSpan={4}>Ocupación total del establecimiento</td>
              <td className="px-3 py-2 text-right font-mono font-bold" data-testid="ocupacion-total">{total} pers.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">La ocupación se calcula como <span className="font-mono">techo(superficie útil / densidad)</span> según la Tabla 2.1 del CTE DB-SI. En «ocupación personalizada» se introduce el nº de personas a mano (sin m²/persona) y se justifica con una nota.</p>

      <Dialog open={!!proposals} onOpenChange={(o) => !o && setProposals(null)}>
        <DialogContent className="max-w-2xl rounded-sm" data-testid="ai-proposal-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading">Propuesta de ocupación (IA)</DialogTitle>
            <DialogDescription>Revisa la propuesta generada con IA. Al aplicarla se actualizará el uso y la densidad de cada estancia (podrás editarlos después).</DialogDescription>
          </DialogHeader>
          <div className="max-h-[50vh] overflow-y-auto border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
                  <th className="px-3 py-2">Estancia</th><th className="px-3 py-2">Uso propuesto</th><th className="px-3 py-2 text-right">m²/p</th>
                </tr>
              </thead>
              <tbody>
                {(proposals || []).map((p) => {
                  const dep = deps.find((x) => x.id === p.id);
                  return (
                    <tr key={p.id} className="border-b border-border last:border-0">
                      <td className="px-3 py-1.5 font-medium">{dep?.nombre || "—"}</td>
                      <td className="px-3 py-1.5">{p.uso}{p.motivo ? <span className="block text-xs text-muted-foreground">{p.motivo}</span> : null}</td>
                      <td className="px-3 py-1.5 text-right font-mono">{p.densidad ?? "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <DialogFooter>
            <Button variant="outline" className="rounded-sm" onClick={() => setProposals(null)} data-testid="ai-proposal-cancel">Cancelar</Button>
            <Button className="rounded-sm" onClick={applyProposals} data-testid="ai-proposal-apply"><Check className="mr-2 h-4 w-4" /> Aplicar propuesta</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
