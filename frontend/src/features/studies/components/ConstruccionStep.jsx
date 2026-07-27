import { Flame, Building2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { sectorCarga, nriBadgeCls } from "@/lib/fireload";

const MEDIANERA_EI = { BAJO: "EI 120", MEDIO: "EI 180", ALTO: "EI 240" };
const REACCION = [
  ["Zonas ocupables, en general", "C-s2,d0", "CFL-s1"],
  ["Pasillos y escaleras protegidos", "B-s1,d0", "CFL-s1"],
  ["Aparcamientos y sectores de riesgo intrínseco alto", "B-s1,d0", "BFL-s1"],
  ["Espacios ocultos no estancos (patinillos, falsos techos, suelos elevados)", "B-s3,d0", "BFL-s2"],
];

const fieldLabel = "text-[11px] font-medium text-muted-foreground";

export function ConstruccionStep({ data, setData }) {
  const sectores = data.sectores || [];
  const deps = data.dependencias || [];

  const update = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));

  return (
    <div className="space-y-5" data-testid="construccion-step">
      <p className="text-sm text-muted-foreground">
        Reacción al fuego de revestimientos (Tabla 2.1.4), medianerías/separaciones con otros
        establecimientos (Tabla 2.2.1) y propagación exterior por fachada (Tabla 2.2.2). Los valores
        exigidos se determinan a partir del nivel de riesgo intrínseco de cada sector.
      </p>

      {sectores.length === 0 && (
        <div className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
          Aún no hay sectores. Créalos en el paso «Sectores de incendio».
        </div>
      )}

      {sectores.map((s) => {
        const sDeps = deps.filter((d) => d.sector_id === s.id);
        const carga = sectorCarga(sDeps);
        const cat = carga.categoria || "BAJO";
        const esCte = s.ambito === "cte";
        const medReq = MEDIANERA_EI[cat] || "EI 120";
        return (
          <div key={s.id} className="rounded-lg border border-border p-4" data-testid={`construccion-sector-${s.id}`}>
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                {esCte ? <Building2 className="h-4 w-4 text-cyan-600" /> : <Flame className="h-4 w-4 text-orange-600" />}
                <span className="font-heading text-sm font-semibold">{s.nombre}</span>
                <span className="text-xs text-muted-foreground">{esCte ? "CTE DB-SI" : "RSCIEI"}</span>
              </div>
              <span className={`rounded-sm px-2 py-0.5 text-xs font-semibold ${nriBadgeCls(cat)}`}>
                NRI {carga.nivel} · {cat}
              </span>
            </div>

            {/* Reacción al fuego */}
            <p className={fieldLabel}>Reacción al fuego de revestimientos (Tabla 2.1.4)</p>
            <div className="mt-1 overflow-x-auto border border-border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-secondary/60 text-left uppercase tracking-wide text-muted-foreground">
                    <th className="px-2 py-1.5">Situación</th><th className="px-2 py-1.5">Techos y paredes</th><th className="px-2 py-1.5">Suelos</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {REACCION.map((r, i) => (
                    <tr key={i} className={`border-b border-border last:border-0 ${cat === "ALTO" && i === 2 ? "bg-orange-100" : ""}`}>
                      <td className="px-2 py-1 font-sans">{r[0]}</td><td className="px-2 py-1">{r[1]}</td><td className="px-2 py-1">{r[2]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <Switch checked={!!s.reaccion_cumple} onCheckedChange={(v) => update(s.id, { reaccion_cumple: v })} data-testid={`construccion-${s.id}-reaccion-cumple`} />
              <Label className="text-sm">El proyecto cumple las clases de reacción al fuego exigidas</Label>
            </div>
            <Input className="mt-2 h-8 rounded-sm text-xs" placeholder="Observaciones de reacción al fuego (opcional)" value={s.reaccion_obs || ""} onChange={(e) => update(s.id, { reaccion_obs: e.target.value })} data-testid={`construccion-${s.id}-reaccion-obs`} />

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {/* Medianeras */}
              <div className="rounded-md border border-border p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">Medianería / separación (Tabla 2.2.1)</p>
                  <Switch checked={!!s.medianera_otro} onCheckedChange={(v) => update(s.id, { medianera_otro: v })} data-testid={`construccion-${s.id}-medianera-sw`} />
                </div>
                {s.medianera_otro ? (
                  <div className="mt-2 space-y-2">
                    <p className="text-xs text-muted-foreground">Linda con otro establecimiento. Exigido por NRI: <b className="font-mono text-foreground">{medReq}</b></p>
                    <div>
                      <Label className={fieldLabel}>EI proyectado</Label>
                      <Input className="mt-1 h-8 rounded-sm font-mono text-xs" placeholder="p. ej. EI 180" value={s.medianera_ei || ""} onChange={(e) => update(s.id, { medianera_ei: e.target.value })} data-testid={`construccion-${s.id}-medianera-ei`} />
                    </div>
                  </div>
                ) : <p className="mt-1 text-xs text-muted-foreground">Activar si el sector linda con otro establecimiento.</p>}
              </div>

              {/* Fachadas */}
              <div className="rounded-md border border-border p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">Propagación por fachada (Tabla 2.2.2)</p>
                  <Switch checked={!!s.fachada_encuentro} onCheckedChange={(v) => update(s.id, { fachada_encuentro: v })} data-testid={`construccion-${s.id}-fachada-sw`} />
                </div>
                {s.fachada_encuentro ? (
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <div>
                      <Label className={fieldLabel}>Ángulo α</Label>
                      <Select value={String(s.fachada_angulo || "180")} onValueChange={(v) => update(s.id, { fachada_angulo: v })}>
                        <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`construccion-${s.id}-fachada-angulo`}><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="90">90° (perpendiculares) · d 2,0 m</SelectItem>
                          <SelectItem value="135">135° · d 1,5 m</SelectItem>
                          <SelectItem value="180">180° (plana) · d 1,0 m</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className={fieldLabel}>EI franja proyectado</Label>
                      <Input className="mt-1 h-8 rounded-sm font-mono text-xs" placeholder="EI …" value={s.fachada_ei || ""} onChange={(e) => update(s.id, { fachada_ei: e.target.value })} data-testid={`construccion-${s.id}-fachada-ei`} />
                    </div>
                  </div>
                ) : <p className="mt-1 text-xs text-muted-foreground">Activar si un elemento compartimentador acomete en fachada.</p>}
              </div>
            </div>

            {/* Cubierta */}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Switch checked={!!s.cubierta_ligera} onCheckedChange={(v) => update(s.id, { cubierta_ligera: v })} data-testid={`construccion-${s.id}-cubierta-sw`} />
              <Label className="text-sm">Cubierta ligera</Label>
              <Input className="ml-2 h-8 flex-1 rounded-sm text-xs" placeholder="Observaciones de cubierta (opcional)" value={s.cubierta_obs || ""} onChange={(e) => update(s.id, { cubierta_obs: e.target.value })} data-testid={`construccion-${s.id}-cubierta-obs`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
