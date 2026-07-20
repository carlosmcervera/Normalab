import { AlertTriangle, CheckCircle2, Info, XCircle, Building2, Users, Ruler } from "lucide-react";
import { num, RISK_STYLES, STATE_META } from "@/lib/format";

const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };

function fmtMax(f) {
  if (f.max_admisible != null) return `${num(f.max_admisible)} m²`;
  return f.max_admisible_base || "—";
}

function SectorCard({ s }) {
  const risk = RISK_STYLES[s.nivel_riesgo.categoria] || RISK_STYLES.MEDIO;
  const sec = s.sectorizacion;
  return (
    <div className="border border-border" data-testid={`result-sector-${s.id}`}>
      <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2.5">
        <span className="font-heading text-sm">{s.nombre}</span>
        <div className="flex items-center gap-2">
          <span className={`flex h-7 w-7 items-center justify-center font-heading text-sm font-bold text-white ${risk.bg}`}>{s.nivel_riesgo.nivel}</span>
          <span className={`text-sm font-medium ${risk.text}`}>{s.nivel_riesgo.categoria}</span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 p-4 text-sm sm:grid-cols-4">
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Qs</p><p className="mt-1 font-mono font-semibold">{num(s.calculo.qs_mj, 1)} MJ/m²</p></div>
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Superficie</p><p className="mt-1 font-mono">{num(s.calculo.A)} m²</p></div>
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Máx. admisible</p><p className="mt-1 font-mono">{fmtMax(sec)}</p></div>
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Ra</p><p className="mt-1 font-mono">{num(s.calculo.ra, 1)}</p></div>
      </div>
      <p className="border-t border-border px-4 py-2 text-sm text-muted-foreground">{sec.mensaje}</p>
      <div className="grid grid-cols-1 gap-4 border-t border-border p-4 sm:grid-cols-3">
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Estabilidad estructura</p><p className="mt-1 font-mono font-semibold">{s.requisitos.estabilidad?.valor}</p></div>
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Delimitadores</p><p className="mt-1 font-mono font-semibold">{s.requisitos.delimitadores?.valor}</p></div>
        <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Evacuación (máx.)</p><p className="mt-1 font-mono font-semibold">{s.evacuacion?.distancia_maxima} m · {s.evacuacion?.num_salidas} sal.</p></div>
      </div>
      {s.evacuacion?.recorridos?.length > 0 && (
        <div className="border-t border-border px-4 py-3">
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Recorridos de evacuación{s.evacuacion.coeficiente !== "ninguno" ? ` · ${s.evacuacion.coeficiente_label}` : ""}</p>
          <div className="space-y-1">
            {s.evacuacion.recorridos.map((r, i) => (
              <div key={i} className="flex items-center justify-between text-sm" data-testid={`sector-${s.id}-rec-${i}`}>
                <span>{r.origen} <span className="text-muted-foreground">({r.tipo === "sin_alternativa" ? "sin alternativa" : "hasta salida"})</span></span>
                <span className="font-mono">{num(r.distancia_real, 1)} / {num(r.distancia_max, 1)} m <span className={r.cumple ? "text-emerald-700" : "text-red-700"}>{r.cumple ? "✓" : "✗"}</span></span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="border-t border-border">
        {s.requisitos.instalaciones.map((it, i) => (
          <div key={i} className="flex items-start justify-between gap-3 border-b border-border px-4 py-2.5 last:border-0" data-testid={`sector-${s.id}-inst-${i}`}>
            <div className="flex-1">
              <p className="text-sm font-medium">{it.nombre}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{it.detalle}</p>
            </div>
            <span className={`shrink-0 rounded-sm border px-2 py-1 text-xs font-medium ${it.obligatorio ? "border-red-300 bg-red-50 text-red-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
              {it.obligatorio ? "Obligatorio" : "No exigible"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ResultsPanel({ results }) {
  if (!results || !results.sectores) return null;
  const { superficies, ocupacion, sectores, resumen_sectores, observaciones, estado_global } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;

  return (
    <div className="space-y-6" data-testid="results-panel">
      {/* Summary tiles */}
      <div className="grid grid-cols-1 gap-px border border-border bg-border sm:grid-cols-4">
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Building2 className="mr-1 inline h-3 w-3" />Sectores</p><p className="mt-2 font-heading text-3xl font-light">{sectores.length}</p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Ruler className="mr-1 inline h-3 w-3" />Sup. construida</p><p className="mt-2 font-heading text-3xl font-light">{num(superficies.total_construida)}<span className="text-sm text-muted-foreground"> m²</span></p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Users className="mr-1 inline h-3 w-3" />Ocupación</p><p className="mt-2 font-heading text-3xl font-light">{ocupacion.total}</p></div>
        <div className="bg-background p-5"><p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Resultado global</p>
          <span className={`mt-3 inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="global-state">
            {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : estado_global === "no_cumple" ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {state.label}
          </span>
        </div>
      </div>

      {/* Resumen sectores */}
      <div className="border border-border bg-background">
        <div className="border-b border-border px-5 py-3"><h3 className="font-heading text-base">Resumen de sectores</h3></div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 font-semibold">Sector</th><th className="px-4 py-2 font-semibold">Config.</th>
                <th className="px-4 py-2 text-right font-semibold">Sup. (m²)</th><th className="px-4 py-2 text-right font-semibold">Qs</th>
                <th className="px-4 py-2 font-semibold">NRI</th><th className="px-4 py-2 font-semibold">Máx. adm.</th>
                <th className="px-4 py-2 font-semibold">Estab.</th><th className="px-4 py-2 text-right font-semibold">Ocup.</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {resumen_sectores.map((f, i) => {
                const risk = RISK_STYLES[f.categoria] || RISK_STYLES.MEDIO;
                return (
                  <tr key={i} className="border-b border-border last:border-0" data-testid={`resumen-row-${i}`}>
                    <td className="px-4 py-2 font-sans font-medium">{f.nombre}</td>
                    <td className="px-4 py-2 font-sans text-xs">{f.config}</td>
                    <td className="px-4 py-2 text-right">{num(f.superficie)}</td>
                    <td className="px-4 py-2 text-right">{num(f.qs_mj, 1)}</td>
                    <td className="px-4 py-2"><span className={`font-sans font-semibold ${risk.text}`}>{f.nivel} · {f.categoria}</span></td>
                    <td className="px-4 py-2">{f.max_admisible != null ? `${num(f.max_admisible)} m²` : (f.max_admisible_base || "—")}</td>
                    <td className="px-4 py-2">{f.estabilidad}</td>
                    <td className="px-4 py-2 text-right font-sans">{f.ocupacion}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Per-sector detail */}
      <div className="space-y-4">
        <h3 className="font-heading text-base">Detalle por sector</h3>
        {sectores.map((s) => <SectorCard key={s.id} s={s} />)}
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
