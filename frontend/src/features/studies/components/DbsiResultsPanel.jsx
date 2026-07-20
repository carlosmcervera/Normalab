import { AlertTriangle, CheckCircle2, Info, XCircle, Users, Ruler, DoorOpen, Building2 } from "lucide-react";
import { num, STATE_META } from "@/lib/format";

const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };
const OKCLS = (ok) => (ok ? "text-emerald-700" : "text-red-700");

export function DbsiResultsPanel({ results }) {
  if (!results || !results.si3) return null;
  const { ocupacion, si1, si3, si4, si6, observaciones, estado_global } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;

  return (
    <div className="space-y-6" data-testid="dbsi-results-panel">
      <div className="grid grid-cols-1 gap-px border border-border bg-border sm:grid-cols-4">
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Users className="mr-1 inline h-3 w-3" />Ocupación</p><p className="mt-2 font-heading text-3xl font-light">{ocupacion.total}</p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><DoorOpen className="mr-1 inline h-3 w-3" />Salidas</p><p className="mt-2 font-heading text-3xl font-light">{si3.salidas_proyectadas}<span className="text-sm text-muted-foreground">/{si3.salidas_requeridas}</span></p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Building2 className="mr-1 inline h-3 w-3" />Estabilidad</p><p className="mt-2 font-heading text-3xl font-light">{si6.estabilidad}</p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Resultado</p>
          <span className={`mt-3 inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="dbsi-global-state">
            {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : estado_global === "no_cumple" ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {state.label}
          </span>
        </div>
      </div>

      <div className="border border-border bg-background p-5">
        <h3 className="font-heading text-base">SI 1 · Compartimentación en sectores de incendio</h3>
        <div className="mt-3 grid grid-cols-1 gap-4 text-sm sm:grid-cols-3">
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground"><Ruler className="mr-1 inline h-3 w-3" />Superficie construida</p><p className="mt-1 font-mono">{num(si1.superficie)} m²</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Máx. por sector</p><p className="mt-1 font-mono">{si1.max_sector != null ? `${num(si1.max_sector)} m²` : "Sin límite"}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Estado</p><p className={`mt-1 font-semibold ${OKCLS(si1.cumple)}`}>{si1.cumple ? "Cumple" : "Requiere sectorizar"}</p></div>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{si1.mensaje}</p>
      </div>

      <div className="border border-border bg-background p-5">
        <h3 className="font-heading text-base">SI 3 · Evacuación de ocupantes</h3>
        <div className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Salidas requeridas</p><p className={`mt-1 font-mono font-semibold ${OKCLS(si3.salidas_ok)}`}>{si3.salidas_proyectadas} / {si3.salidas_requeridas}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Recorrido máx.</p><p className="mt-1 font-mono">{si3.recorrido_max_permitido} m</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Recorrido real</p><p className={`mt-1 font-mono font-semibold ${OKCLS(si3.recorrido_ok)}`}>{si3.recorrido_real ? `${num(si3.recorrido_real, 1)} m` : "—"}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Ancho de salida</p><p className="mt-1 font-mono">{num(si3.ancho_calculado, 2)} m (mín. {num(si3.ancho_minimo, 2)})</p></div>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{si3.detalle}</p>
      </div>

      <div className="border border-border bg-background p-5">
        <h3 className="font-heading text-base">SI 6 · Resistencia al fuego de la estructura</h3>
        <p className="mt-2 font-mono text-lg font-semibold">{si6.estabilidad}</p>
        <p className="mt-1 text-sm text-muted-foreground">{si6.detalle}</p>
      </div>

      <div className="border border-border bg-background">
        <div className="border-b border-border px-5 py-3"><h3 className="font-heading text-base">SI 4 · Instalaciones de protección contra incendios</h3></div>
        {si4.instalaciones.map((it, i) => (
          <div key={i} className="flex items-start justify-between gap-4 border-b border-border p-4 last:border-0" data-testid={`dbsi-inst-${i}`}>
            <div className="flex-1"><p className="text-sm font-medium">{it.nombre}</p><p className="mt-0.5 text-xs text-muted-foreground">{it.detalle}</p></div>
            <span className={`shrink-0 rounded-sm border px-2 py-1 text-xs font-medium ${it.obligatorio ? "border-red-300 bg-red-50 text-red-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>{it.obligatorio ? "Obligatorio" : "No exigible"}</span>
          </div>
        ))}
      </div>

      {observaciones.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-heading text-base">Observaciones</h3>
          {observaciones.map((o, i) => {
            const Icon = OBS_ICON[o.tipo] || Info;
            return <div key={i} className={`flex items-start gap-3 border p-3 text-sm ${OBS_CLS[o.tipo] || OBS_CLS.info}`} data-testid={`dbsi-observation-${i}`}><Icon className="mt-0.5 h-4 w-4 shrink-0" /><p>{o.texto}</p></div>;
          })}
        </div>
      )}
    </div>
  );
}
