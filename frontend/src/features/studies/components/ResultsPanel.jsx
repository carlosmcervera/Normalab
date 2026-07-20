import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { num, RISK_STYLES, STATE_META } from "@/lib/format";

const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };
const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};

export function ResultsPanel({ results }) {
  if (!results) return null;
  const { calculo, nivel_riesgo, sectorizacion, observaciones, estado_global } = results;
  const risk = RISK_STYLES[nivel_riesgo.categoria] || RISK_STYLES.MEDIO;
  const state = STATE_META[estado_global] || STATE_META.observaciones;

  return (
    <div className="space-y-6" data-testid="results-panel">
      {/* Summary tiles */}
      <div className="grid grid-cols-1 gap-px border border-border bg-border sm:grid-cols-3">
        <div className="bg-background p-6">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Densidad de carga (Qs)</p>
          <p className="mt-3 font-heading text-3xl font-light">{num(calculo.qs_mj, 1)} <span className="text-base text-muted-foreground">MJ/m²</span></p>
          <p className="mt-1 font-mono text-xs text-muted-foreground">{num(calculo.qs_mcal, 1)} Mcal/m²</p>
        </div>
        <div className="bg-background p-6">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Nivel de riesgo intrínseco</p>
          <div className="mt-3 flex items-center gap-3">
            <span className={`flex h-10 w-10 items-center justify-center font-heading text-lg font-bold text-white ${risk.bg}`}>{nivel_riesgo.nivel}</span>
            <span className={`font-heading text-xl ${risk.text}`}>{nivel_riesgo.categoria}</span>
          </div>
        </div>
        <div className="bg-background p-6">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Resultado global</p>
          <div className="mt-3">
            <span className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="global-state">
              {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : estado_global === "no_cumple" ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
              {state.label}
            </span>
          </div>
        </div>
      </div>

      {/* Zonas table */}
      <div className="border border-border bg-background">
        <div className="border-b border-border px-5 py-3">
          <h3 className="font-heading text-base">Cálculo por zonas</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-2 font-semibold">Zona</th>
                <th className="px-5 py-2 font-semibold">Tipo</th>
                <th className="px-5 py-2 text-right font-semibold">Carga</th>
                <th className="px-5 py-2 text-right font-semibold">Ci</th>
                <th className="px-5 py-2 text-right font-semibold">Sup. (m²)</th>
                <th className="px-5 py-2 text-right font-semibold">Aporte (MJ)</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {calculo.zonas.map((z, i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  <td className="px-5 py-2 font-sans">{z.descripcion}</td>
                  <td className="px-5 py-2 font-sans text-muted-foreground">{z.modo === "almacenamiento" ? "Almacenamiento" : "Producción"}</td>
                  <td className="px-5 py-2 text-right">{z.modo === "almacenamiento" ? `${num(z.qvi)} MJ/m³ · ${num(z.hi, 1)} m` : `${num(z.qsi)} MJ/m²`}</td>
                  <td className="px-5 py-2 text-right">{num(z.ci, 2)}</td>
                  <td className="px-5 py-2 text-right">{num(z.superficie)}</td>
                  <td className="px-5 py-2 text-right font-medium">{num(z.aporte)}</td>
                </tr>
              ))}
              <tr className="bg-secondary/40">
                <td className="px-5 py-2 font-sans font-medium" colSpan={5}>Σ ponderada · A = {num(calculo.A)} m² · Ra = {num(calculo.ra, 2)}</td>
                <td className="px-5 py-2 text-right font-mono font-bold">{num(calculo.numerador)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Sectorización */}
      <div className="border border-border bg-background p-5">
        <h3 className="font-heading text-base">Sectorización (Tabla 2.1)</h3>
        <div className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Configuración</p><p className="mt-1 font-medium">{sectorizacion.config_label}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Superficie sector</p><p className="mt-1 font-mono font-medium">{num(sectorizacion.superficie_sector)} m²</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Máx. admisible</p><p className="mt-1 font-mono font-medium">{sectorizacion.max_admisible != null ? `${num(sectorizacion.max_admisible)} m²` : (sectorizacion.max_admisible_base || "—")}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-muted-foreground">Factor incremento</p><p className="mt-1 font-mono font-medium">×{num(sectorizacion.factor_incremento, 2)}</p></div>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">{sectorizacion.mensaje}</p>
      </div>

      {/* Observaciones */}
      <div className="space-y-2">
        <h3 className="font-heading text-base">Observaciones</h3>
        {observaciones.map((o, i) => {
          const Icon = OBS_ICON[o.tipo] || Info;
          return (
            <div key={i} className={`flex items-start gap-3 border p-3 text-sm ${OBS_CLS[o.tipo] || OBS_CLS.info}`} data-testid={`observation-${i}`}>
              <Icon className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{o.texto}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
