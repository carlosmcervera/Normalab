import { Flame, Building2, ArrowLeftRight, DoorOpen } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { sectorCarga, nriBadgeCls } from "@/lib/fireload";

const MEDIANERA_EI = { BAJO: "EI 120", MEDIO: "EI 180", ALTO: "EI 240" };

const REACCION_RSCIEI = [
  ["Zonas ocupables, en general", "C-s2,d0", "CFL-s1"],
  ["Pasillos y escaleras protegidos", "B-s1,d0", "CFL-s1"],
  ["Aparcamientos y sectores de riesgo intrínseco alto", "B-s1,d0", "BFL-s1"],
  ["Espacios ocultos no estancos (patinillos, falsos techos, suelos elevados)", "B-s3,d0", "BFL-s2"],
];
const REACCION_CTE = [
  ["Zonas ocupables y recorridos de evacuación", "C-s2,d0", "EFL"],
  ["Pasillos y escaleras protegidos", "B-s1,d0", "CFL-s1"],
  ["Aparcamientos y recintos de riesgo especial", "B-s1,d0", "BFL-s1"],
  ["Espacios ocultos: patinillos, falsos techos, suelos elevados", "B-s3,d0", "BFL-s2"],
];

// CTE DB-SI SI 2 · Fig. 1.1 · separación mínima entre huecos según el ángulo (m).
const HUECOS_ANG = [
  ["0", "3,00 m"], ["45", "2,75 m"], ["60", "2,50 m"],
  ["90", "2,00 m"], ["135", "1,25 m"], ["180", "0,50 m"],
];
// RSCIEI Anexo II · Tabla 2.2.2 · franja d según ángulo α.
const FACHADA_ANG = [["90", "2,0"], ["135", "1,5"], ["180", "1,0"]];

const fieldLabel = "text-[11px] font-medium text-muted-foreground";

function ReaccionTable({ rows, highlightAlto }) {
  return (
    <div className="mt-1 overflow-x-auto border border-border">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border bg-secondary/60 text-left uppercase tracking-wide text-muted-foreground">
            <th className="px-2 py-1.5">Situación</th><th className="px-2 py-1.5">Techos y paredes</th><th className="px-2 py-1.5">Suelos</th>
          </tr>
        </thead>
        <tbody className="font-mono">
          {rows.map((r, i) => (
            <tr key={i} className={`border-b border-border last:border-0 ${highlightAlto && i === 2 ? "bg-orange-100" : ""}`}>
              <td className="px-2 py-1 font-sans">{r[0]}</td><td className="px-2 py-1">{r[1]}</td><td className="px-2 py-1">{r[2]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ConstruccionStep({ data, setData }) {
  const sectores = data.sectores || [];
  const deps = data.dependencias || [];

  const update = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));

  return (
    <div className="space-y-5" data-testid="construccion-step">
      <p className="text-sm text-muted-foreground">
        Propagación <b>interior</b> y <b>exterior</b> por sector. Las opciones y los valores exigidos se
        adaptan al ámbito de cada sector: <b>RSCIEI (Anexo II)</b> para sectores industriales y
        <b> CTE DB-SI (SI 1 / SI 2)</b> para sectores de edificación.
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
        const medReq = esCte ? "EI 120" : (MEDIANERA_EI[cat] || "EI 120");
        const reaccionRows = esCte ? REACCION_CTE : REACCION_RSCIEI;
        return (
          <div key={s.id} className="rounded-lg border border-border p-4" data-testid={`construccion-sector-${s.id}`}>
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                {esCte ? <Building2 className="h-4 w-4 text-cyan-600" /> : <Flame className="h-4 w-4 text-orange-600" />}
                <span className="font-heading text-sm font-semibold">{s.nombre}</span>
                <span className={`rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase ${esCte ? "bg-cyan-50 text-cyan-700" : "bg-orange-50 text-orange-700"}`}>
                  {esCte ? "CTE DB-SI · SI 1 / SI 2" : "RSCIEI · Anexo II"}
                </span>
              </div>
              <span className={`rounded-sm px-2 py-0.5 text-xs font-semibold ${nriBadgeCls(cat)}`}>
                NRI {carga.nivel} · {cat}
              </span>
            </div>

            {/* ================= PROPAGACIÓN INTERIOR ================= */}
            <div className="rounded-md border border-border bg-secondary/20 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <ArrowLeftRight className="h-3.5 w-3.5" /> Propagación interior · {esCte ? "SI 1 (Tablas 1.2 y 4.1)" : "Anexo II (Tablas 2.1.4 y 2.2)"}
              </div>

              <div className="mb-3 rounded-sm border border-border bg-background px-3 py-2 text-xs">
                <span className="text-muted-foreground">Elementos delimitadores del sector: </span>
                <b className="font-mono">{esCte ? "según altura de evacuación (SI 1, Tabla 1.2)" : (MEDIANERA_EI[cat] || "EI 120")}</b>
                <span className="text-muted-foreground"> · determinados automáticamente por el nivel de riesgo/altura.</span>
              </div>

              <p className={fieldLabel}>Reacción al fuego de revestimientos ({esCte ? "SI 1, Tabla 4.1" : "Tabla 2.1.4"})</p>
              <ReaccionTable rows={reaccionRows} highlightAlto={!esCte && cat === "ALTO"} />
              <div className="mt-2 flex items-center gap-2">
                <Switch checked={!!s.reaccion_cumple} onCheckedChange={(v) => update(s.id, { reaccion_cumple: v })} data-testid={`construccion-${s.id}-reaccion-cumple`} />
                <Label className="text-sm">El proyecto cumple las clases de reacción al fuego exigidas</Label>
              </div>
              <Input className="mt-2 h-8 rounded-sm text-xs" placeholder="Observaciones de reacción al fuego (opcional)" value={s.reaccion_obs || ""} onChange={(e) => update(s.id, { reaccion_obs: e.target.value })} data-testid={`construccion-${s.id}-reaccion-obs`} />
            </div>

            {/* ================= PROPAGACIÓN EXTERIOR ================= */}
            <div className="mt-3 rounded-md border border-border bg-secondary/20 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <DoorOpen className="h-3.5 w-3.5" /> Propagación exterior · {esCte ? "SI 2 (Tabla 1.1)" : "Anexo II (Tablas 2.2.1 y 2.2.2)"}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {/* Medianeras */}
                <div className="rounded-md border border-border bg-background p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{esCte ? "Medianería (SI 2)" : "Medianería / separación (Tabla 2.2.1)"}</p>
                    <Switch checked={!!s.medianera_otro} onCheckedChange={(v) => update(s.id, { medianera_otro: v })} data-testid={`construccion-${s.id}-medianera-sw`} />
                  </div>
                  {s.medianera_otro ? (
                    <div className="mt-2 space-y-2">
                      <p className="text-xs text-muted-foreground">Linda con otro {esCte ? "edificio" : "establecimiento"}. Exigido: <b className="font-mono text-foreground">{medReq}</b></p>
                      <div>
                        <Label className={fieldLabel}>EI proyectado</Label>
                        <Input className="mt-1 h-8 rounded-sm font-mono text-xs" placeholder="p. ej. EI 120" value={s.medianera_ei || ""} onChange={(e) => update(s.id, { medianera_ei: e.target.value })} data-testid={`construccion-${s.id}-medianera-ei`} />
                      </div>
                    </div>
                  ) : <p className="mt-1 text-xs text-muted-foreground">Activar si el sector linda con otro {esCte ? "edificio" : "establecimiento"}.</p>}
                </div>

                {/* Fachadas */}
                <div className="rounded-md border border-border bg-background p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{esCte ? "Fachada (SI 2)" : "Propagación por fachada (Tabla 2.2.2)"}</p>
                    <Switch checked={!!s.fachada_encuentro} onCheckedChange={(v) => update(s.id, { fachada_encuentro: v })} data-testid={`construccion-${s.id}-fachada-sw`} />
                  </div>
                  {s.fachada_encuentro ? (
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      {!esCte && (
                        <div>
                          <Label className={fieldLabel}>Ángulo α (franja d)</Label>
                          <Select value={String(s.fachada_angulo || "180")} onValueChange={(v) => update(s.id, { fachada_angulo: v })}>
                            <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`construccion-${s.id}-fachada-angulo`}><SelectValue /></SelectTrigger>
                            <SelectContent>
                              {FACHADA_ANG.map(([a, d]) => <SelectItem key={a} value={a}>{a}° · d {d} m</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                      <div className={esCte ? "col-span-2" : ""}>
                        <Label className={fieldLabel}>{esCte ? "EI franja proyectado (mín. EI 60)" : "EI franja proyectado"}</Label>
                        <Input className="mt-1 h-8 rounded-sm font-mono text-xs" placeholder="EI …" value={s.fachada_ei || ""} onChange={(e) => update(s.id, { fachada_ei: e.target.value })} data-testid={`construccion-${s.id}-fachada-ei`} />
                      </div>
                    </div>
                  ) : <p className="mt-1 text-xs text-muted-foreground">Activar si un elemento compartimentador acomete en fachada.</p>}
                </div>
              </div>

              {/* Separación entre huecos (SI 2 · Fig. 1.1) */}
              {s.fachada_encuentro && (
                <div className="mt-3 rounded-md border border-border bg-background p-3" data-testid={`construccion-${s.id}-huecos`}>
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Separación entre huecos de sectores/edificios distintos (SI 2, Fig. 1.1)</p>
                    <Switch checked={!!s.fachada_huecos} onCheckedChange={(v) => update(s.id, { fachada_huecos: v })} data-testid={`construccion-${s.id}-huecos-sw`} />
                  </div>
                  {s.fachada_huecos ? (
                    <div className="mt-2 grid gap-2 sm:grid-cols-4">
                      <div>
                        <Label className={fieldLabel}>Ángulo entre planos</Label>
                        <Select value={String(s.fachada_angulo || "180")} onValueChange={(v) => update(s.id, { fachada_angulo: v })}>
                          <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`construccion-${s.id}-huecos-angulo`}><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {HUECOS_ANG.map(([a, d]) => <SelectItem key={a} value={a}>{a}° · {d}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className={fieldLabel}>Distancia proyectada (m)</Label>
                        <Input className="mt-1 h-8 rounded-sm font-mono text-xs" placeholder="m" value={s.fachada_huecos_dist ?? ""} onChange={(e) => update(s.id, { fachada_huecos_dist: e.target.value })} data-testid={`construccion-${s.id}-huecos-dist`} disabled={!!s.fachada_huecos_ei60} />
                      </div>
                      <div className="flex items-end gap-2 pb-1">
                        <Switch checked={!!s.fachada_huecos_ei60} onCheckedChange={(v) => update(s.id, { fachada_huecos_ei60: v })} data-testid={`construccion-${s.id}-huecos-ei60`} />
                        <Label className="text-xs">Huecos EI 60</Label>
                      </div>
                      <div className="flex items-end gap-2 pb-1">
                        <Switch checked={!!s.edificio_colindante} onCheckedChange={(v) => update(s.id, { edificio_colindante: v })} data-testid={`construccion-${s.id}-colindante`} />
                        <Label className="text-xs">Edificio colindante (50 %)</Label>
                      </div>
                    </div>
                  ) : <p className="mt-1 text-xs text-muted-foreground">Activar para comprobar la separación mínima entre huecos según el ángulo entre planos de fachada.</p>}
                </div>
              )}

              {/* Cubierta */}
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Switch checked={!!s.cubierta_ligera} onCheckedChange={(v) => update(s.id, { cubierta_ligera: v })} data-testid={`construccion-${s.id}-cubierta-sw`} />
                <Label className="text-sm">Cubierta ligera</Label>
                {esCte && <span className="text-xs text-muted-foreground">· exigencia SI 2: REI 60 en franja de 0,50 m</span>}
                <Input className="ml-2 h-8 flex-1 rounded-sm text-xs" placeholder="Observaciones de cubierta (opcional)" value={s.cubierta_obs || ""} onChange={(e) => update(s.id, { cubierta_obs: e.target.value })} data-testid={`construccion-${s.id}-cubierta-obs`} />
              </div>
            </div>

            {/* ================= EVACUACIÓN DE HUMOS (8.4) ================= */}
            {!esCte && (
              <div className="mt-3 rounded-md border border-sky-200 bg-sky-50/40 p-3" data-testid={`construccion-${s.id}-humos`}>
                <p className="text-xs font-semibold uppercase tracking-wide text-sky-800">Evacuación de humos y calor · superficie de ventilación (RSCIEI Anexo III, 8.4)</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  La superficie aerodinámica exigida (0,5 m² por cada 200/150 m² en producción y 150/100 m² en almacenamiento, según rasante) se calcula automáticamente.
                  Introduzca la superficie de ventilación proyectada para que el informe avise si es insuficiente.
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <Label className={fieldLabel}>Superficie de ventilación proyectada (m²)</Label>
                  <Input className="h-8 w-32 rounded-sm font-mono text-xs" placeholder="m²" value={s.humos_ventilacion_proyectada ?? ""} onChange={(e) => update(s.id, { humos_ventilacion_proyectada: e.target.value })} data-testid={`construccion-${s.id}-humos-vent`} />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
