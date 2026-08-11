import { AlertTriangle, CheckCircle2, Info, XCircle, Cable } from "lucide-react";
import { STATE_META } from "@/lib/format";

const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };

// Panel de resultados del módulo «REBT · Comprobación de una línea» (línea única, con
// factor de agrupamiento UNE-HD 60364-5-52 y conductores en paralelo por fase).
export function RebtLineaResultPanel({ results }) {
  if (!results) return null;
  const {
    resumen = [], comprobaciones = [], observaciones = [], estado_global,
    agrupamiento = {}, entradas = {}, paralelo = {},
  } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;
  const n = paralelo.n || 1;

  return (
    <div className="space-y-6" data-testid="rebt-linea-results-panel">
      {/* Métricas resumen */}
      <div className="grid grid-cols-2 gap-px border border-border bg-border sm:grid-cols-3 lg:grid-cols-6">
        {resumen.map((m, i) => (
          <div key={i} className="bg-background p-5" data-testid={`linea-metric-${i}`}>
            <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-muted-foreground">{m.label}</p>
            <p className="mt-2 font-heading text-2xl font-light">{m.valor}<span className="text-sm text-muted-foreground"> {m.unidad}</span></p>
          </div>
        ))}
      </div>

      {/* Estado global */}
      <div className="flex items-center justify-between border border-border bg-background p-4">
        <h3 className="font-heading text-base">Resultado de la comprobación</h3>
        <span className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="linea-global-state">
          {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          {state.label}
        </span>
      </div>

      {/* Conductores en paralelo (solo si N > 1) */}
      {n > 1 && (
        <div className="flex items-start gap-3 border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900" data-testid="linea-paralelo">
          <Cable className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Línea resuelta con <strong>{n} conductores en paralelo por fase</strong> de{" "}
            <strong>{paralelo.seccion_por_conductor_txt} mm²</strong> (sección total{" "}
            <strong>{paralelo.seccion_efectiva_txt} mm²/fase</strong>). Los conductores en paralelo deben
            tener la misma longitud, sección y disposición para repartir la corriente (ITC-BT-19).
          </p>
        </div>
      )}

      {/* Agrupamiento */}
      <div className="border border-border bg-background" data-testid="linea-agrupamiento">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5">
          <span className="font-heading text-sm">Factor de agrupamiento (UNE-HD 60364-5-52, Tabla B.52.17)</span>
        </div>
        <div className="grid grid-cols-1 gap-px bg-border sm:grid-cols-2">
          {[
            ["Disposición", agrupamiento.disposicion_label],
            ["Nº de circuitos en la canalización", agrupamiento.n_circuitos],
            ["Factor de reducción aplicado", agrupamiento.factor],
            ["Iz base (por conductor, sin agrupar)", `${agrupamiento.iz_base} A`],
            ["Iz corregida (aplicada)", `${agrupamiento.iz_corregida} A`],
            ["Método de instalación (ITC-BT-19)", entradas.metodo_label],
          ].map(([k, v], i) => (
            <div key={i} className="flex items-center justify-between gap-3 bg-background px-4 py-2.5 text-sm">
              <span className="text-muted-foreground">{k}</span>
              <span className="text-right font-medium">{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Comprobaciones normativas */}
      <div className="border border-border bg-background" data-testid="linea-comprobaciones">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5">
          <span className="font-heading text-sm">Comprobaciones normativas (ITC-BT-19 / ITC-BT-22)</span>
        </div>
        <div className="divide-y divide-border">
          {comprobaciones.map((c, i) => (
            <div key={i} className="flex items-start justify-between gap-4 px-4 py-3" data-testid={`linea-check-${i}`}>
              <div className="flex items-start gap-3">
                {c.ok ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> : <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />}
                <div>
                  <p className="text-sm font-medium">{c.nombre}</p>
                  <p className="mt-0.5 font-mono text-xs text-muted-foreground">{c.detalle}</p>
                </div>
              </div>
              <span className={`shrink-0 rounded-sm px-2 py-0.5 text-xs font-semibold ${c.ok ? "text-emerald-700" : "text-red-700"}`}>
                {c.ok ? "Cumple" : "No cumple"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Observaciones */}
      {observaciones.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-heading text-base">Observaciones</h3>
          {observaciones.map((o, i) => {
            const Icon = OBS_ICON[o.tipo] || Info;
            return (
              <div key={i} className={`flex items-start gap-3 border p-3 text-sm ${OBS_CLS[o.tipo] || OBS_CLS.info}`} data-testid={`linea-observation-${i}`}>
                <Icon className="mt-0.5 h-4 w-4 shrink-0" /><p>{o.texto}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
