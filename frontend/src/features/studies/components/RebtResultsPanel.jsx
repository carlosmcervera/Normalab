import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { STATE_META, num } from "@/lib/format";
import { EsquemaUnifilar } from "@/features/studies/components/EsquemaUnifilar";

const OBS = { info: "border-slate-200 bg-slate-50 text-slate-700", warning: "border-amber-200 bg-amber-50 text-amber-800", error: "border-red-200 bg-red-50 text-red-800" };
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };
const estCls = (e) => (e === "no_cumple" ? "text-red-700 font-semibold" : e === "observaciones" ? "text-amber-700" : "text-emerald-700");
const estLbl = (e) => (e === "no_cumple" ? "No cumple" : e === "observaciones" ? "Revisar" : "Cumple");

export function RebtResultsPanel({ results }) {
  if (!results) return null;
  const { resumen = [], cuadro_potencias = [], lineas = [], observaciones = [], arbol, estado_global } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;

  return (
    <div className="space-y-6" data-testid="rebt-results-panel">
      <div className="grid grid-cols-2 gap-px border border-border bg-border sm:grid-cols-4">
        {resumen.map((m, i) => (
          <div key={i} className="bg-background p-5" data-testid={`metric-${i}`}>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{m.label}</p>
            <p className="mt-2 font-mono text-2xl font-light">{m.valor}<span className="text-sm text-muted-foreground"> {m.unidad}</span></p>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between border border-border bg-background p-4">
        <h3 className="font-heading text-base">Resultado global del cuadro</h3>
        <span className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium ${state.cls}`} data-testid="global-state">
          {estado_global === "cumple" ? <CheckCircle2 className="h-4 w-4" /> : estado_global === "no_cumple" ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          {state.label}
        </span>
      </div>

      {/* Cuadro de potencias */}
      <div className="border border-border bg-background">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5 font-heading text-sm">Cuadro de potencias</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-border text-left uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Cuadro</th><th className="px-3">Circuito</th><th className="px-3">Tipo</th><th className="px-3 text-right">P instalada (W)</th><th className="px-3 text-right">F. uso</th><th className="px-3 text-right">P cálculo (W)</th>
            </tr></thead>
            <tbody className="font-mono">
              {cuadro_potencias.map((r, i) => (
                <tr key={i} className="border-b border-border last:border-0" data-testid={`potencia-row-${i}`}>
                  <td className="px-3 py-1.5 font-sans">{r.cuadro}</td><td className="px-3 font-sans">{r.circuito}</td><td className="px-3 font-sans">{r.tipo}</td>
                  <td className="px-3 text-right">{num(r.potencia, 0)}</td><td className="px-3 text-right">{r.factor_uso}</td><td className="px-3 text-right">{num(r.potencia_calculo, 0)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr className="border-t-2 border-border bg-secondary/40 font-mono font-bold">
              <td className="px-3 py-2 font-sans" colSpan={3}>TOTAL</td>
              <td className="px-3 text-right" data-testid="total-instalada">{num(results.datos?.potencia_instalada, 0)}</td><td /><td className="px-3 text-right" data-testid="total-calculo">{num(results.datos?.potencia_demandada, 0)}</td>
            </tr></tfoot>
          </table>
        </div>
      </div>

      {/* Esquema unifilar */}
      <div className="border border-border bg-background p-4">
        <h3 className="mb-3 font-heading text-base">Esquema unifilar</h3>
        <EsquemaUnifilar arbol={arbol} />
      </div>

      {/* Líneas */}
      <div className="border border-border bg-background">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5 font-heading text-sm">Dimensionado y comprobación de líneas</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-border text-left uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Cuadro</th><th className="px-3">Línea</th><th className="px-3 text-right">Ib (A)</th><th className="px-3 text-right">Sección</th><th className="px-3 text-right">Iz (A)</th><th className="px-3">Protección</th><th className="px-3">Protege cable</th><th className="px-3 text-right">Caída acum.</th><th className="px-3">Difer.</th><th className="px-3 text-right">Tierra</th><th className="px-3">Estado</th>
            </tr></thead>
            <tbody className="font-mono">
              {lineas.map((l, i) => {
                const co = l.coordinacion;
                const protege = l.protege_cable;
                return (
                <tr key={i} className="border-b border-border last:border-0" data-testid={`linea-row-${i}`}>
                  <td className="px-3 py-1.5 font-sans">{l.cuadro}</td><td className="px-3 font-sans">{l.circuito}</td>
                  <td className="px-3 text-right">{l.Ib}</td><td className="px-3 text-right">{l.seccion_txt} mm²</td><td className="px-3 text-right">{l.iz}</td>
                  <td className="px-3 font-sans">{l.proteccion}</td>
                  <td className="px-3 font-sans">
                    {co ? (
                      <span
                        className={`inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5 text-[10px] font-medium ${protege ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-800"}`}
                        title={`Ib ${co.Ib} A ≤ In ${co.In ?? "—"} A ≤ Iz ${co.Iz} A · I2 ${co.I2 ?? "—"} A ≤ 1,45·Iz ${co.I2_max} A`}
                        data-testid={`linea-${i}-protege`}
                      >
                        {protege ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                        {protege ? "Sí" : "Revisar"}
                      </span>
                    ) : <span className="text-muted-foreground">—</span>}
                  </td>
                  <td className="px-3 text-right">{l.caida_acum_pct}%</td><td className="px-3 font-sans">{l.diferencial}</td><td className="px-3 text-right">{l.tierra}</td>
                  <td className={`px-3 font-sans ${estCls(l.estado)}`}>{estLbl(l.estado)}</td>
                </tr>
              );})}
            </tbody>
          </table>
        </div>
        <div className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          <b>Coordinación protección↔cable (ITC-BT-22):</b> Ib ≤ In ≤ Iz e I2 ≤ 1,45·Iz (I2 = 1,45·In). Poder de corte mínimo recomendado: <b className="text-foreground">{results.datos?.poder_corte_ka ?? 6} kA</b>.
        </div>
      </div>

      {observaciones.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-heading text-base">Observaciones</h3>
          {observaciones.map((o, i) => {
            const Icon = OBS_ICON[o.tipo] || Info;
            return <div key={i} className={`flex items-start gap-3 border p-3 text-sm ${OBS[o.tipo] || OBS.info}`} data-testid={`observation-${i}`}><Icon className="mt-0.5 h-4 w-4 shrink-0" /><p>{o.texto}</p></div>;
          })}
        </div>
      )}
    </div>
  );
}
