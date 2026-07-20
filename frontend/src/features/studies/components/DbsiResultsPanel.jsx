import { AlertTriangle, CheckCircle2, Info, XCircle, Users } from "lucide-react";
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
const SEC_LABEL = { cumple: "Cumple", no_cumple: "No cumple", observaciones: "Con observaciones", info: "Informativo" };

export function DbsiResultsPanel({ results }) {
  if (!results || !results.secciones) return null;
  const { ocupacion, secciones, observaciones, estado_global } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;

  return (
    <div className="space-y-6" data-testid="dbsi-results-panel">
      <div className="grid grid-cols-1 gap-px border border-border bg-border sm:grid-cols-3">
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Users className="mr-1 inline h-3 w-3" />Ocupación</p><p className="mt-2 font-heading text-3xl font-light">{ocupacion.total}</p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Secciones evaluadas</p><p className="mt-2 font-heading text-3xl font-light">{secciones.length}<span className="text-sm text-muted-foreground"> (SI 1–6)</span></p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Resultado</p>
          <span className={`mt-3 inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="dbsi-global-state">
            {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : estado_global === "no_cumple" ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {state.label}
          </span>
        </div>
      </div>

      {secciones.map((s) => (
        <div key={s.id} className="border border-border bg-background" data-testid={`dbsi-seccion-${s.id}`}>
          <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
            <div><h3 className="font-heading text-base">{s.titulo}</h3><p className="text-xs text-muted-foreground">{s.referencia}</p></div>
            <span className={`shrink-0 rounded-sm border px-2 py-1 text-xs font-medium ${SEC_BADGE[s.estado] || SEC_BADGE.info}`}>{SEC_LABEL[s.estado] || "—"}</span>
          </div>
          {s.filas?.length > 0 && (
            <table className="w-full text-sm">
              <tbody>
                {s.filas.map((f, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="px-5 py-2 text-muted-foreground">{f.k}</td>
                    <td className="px-5 py-2 text-right font-medium">{f.v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {s.instalaciones?.map((it, i) => (
            <div key={i} className="flex items-start justify-between gap-4 border-b border-border px-5 py-2.5 last:border-0" data-testid={`dbsi-inst-${i}`}>
              <div className="flex-1"><p className="text-sm font-medium">{it.nombre}</p><p className="mt-0.5 text-xs text-muted-foreground">{it.detalle}</p></div>
              <span className={`shrink-0 rounded-sm border px-2 py-1 text-xs font-medium ${it.obligatorio ? "border-red-300 bg-red-50 text-red-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>{it.obligatorio ? "Obligatorio" : "No exigible"}</span>
            </div>
          ))}
        </div>
      ))}

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
