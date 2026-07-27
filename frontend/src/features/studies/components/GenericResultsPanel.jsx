import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { STATE_META } from "@/lib/format";

const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };

const SEC_BADGE = {
  cumple: "border-emerald-300 bg-emerald-50 text-emerald-800",
  no_cumple: "border-red-300 bg-red-50 text-red-800",
  observaciones: "border-amber-300 bg-amber-50 text-amber-800",
  info: "border-slate-300 bg-slate-50 text-slate-600",
};
const SEC_LABEL = { cumple: "Cumple", no_cumple: "No cumple", observaciones: "Revisar", info: "Info" };

// Panel de resultados genérico para módulos no sectoriales (REBT, RITE).
export function GenericResultsPanel({ results }) {
  if (!results) return null;
  const { resumen = [], secciones = [], observaciones = [], estado_global } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;

  return (
    <div className="space-y-6" data-testid="generic-results-panel">
      {/* Métricas + estado global */}
      <div className="grid grid-cols-1 gap-px border border-border bg-border sm:grid-cols-4">
        {resumen.map((m, i) => (
          <div key={i} className="bg-background p-5" data-testid={`metric-${i}`}>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{m.label}</p>
            <p className="mt-2 font-heading text-3xl font-light">{m.valor}<span className="text-sm text-muted-foreground"> {m.unidad}</span></p>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between border border-border bg-background p-4">
        <h3 className="font-heading text-base">Resultado global</h3>
        <span className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="global-state">
          {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : estado_global === "no_cumple" ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          {state.label}
        </span>
      </div>

      {/* Secciones */}
      <div className="space-y-4">
        {secciones.map((s) => (
          <div key={s.id} className="border border-border bg-background" data-testid={`result-seccion-${s.id}`}>
            <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2.5">
              <span className="font-heading text-sm">{s.titulo}</span>
              <span className={`rounded-sm border px-2 py-0.5 text-xs font-medium ${SEC_BADGE[s.estado] || SEC_BADGE.info}`} data-testid={`result-seccion-${s.id}-estado`}>{SEC_LABEL[s.estado] || "Info"}</span>
            </div>
            {s.descripcion && <p className="px-4 pt-2 text-xs text-muted-foreground">{s.descripcion}</p>}
            <div className="p-2">
              {(s.items || []).map((it, i) => (
                <div key={i} className="flex items-start justify-between gap-3 px-2 py-1.5 text-sm">
                  <span className="font-medium">{it.nombre}</span>
                  <span className={`text-right font-mono text-xs ${it.estado === "no_cumple" ? "text-red-700 font-semibold" : it.estado === "cumple" ? "text-emerald-700 font-semibold" : "text-muted-foreground"}`}>{it.detalle}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Observaciones */}
      {observaciones.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-heading text-base">Observaciones</h3>
          {observaciones.map((o, i) => {
            const Icon = OBS_ICON[o.tipo] || Info;
            return (
              <div key={i} className={`flex items-start gap-3 border p-3 text-sm ${OBS_CLS[o.tipo] || OBS_CLS.info}`} data-testid={`observation-${i}`}>
                <Icon className="mt-0.5 h-4 w-4 shrink-0" /><p>{o.texto}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
