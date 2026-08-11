import { AlertTriangle, CheckCircle2, Info, XCircle, Calculator, Loader2, Wand2 } from "lucide-react";
import { STATE_META, num } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EsquemaUnifilar } from "@/features/studies/components/EsquemaUnifilar";

const MAGNETOS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250];
const SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240];
const secTxt = (s) => String(s).replace(".", ",");
const OBS = { info: "border-slate-200 bg-slate-50 text-slate-700", warning: "border-amber-200 bg-amber-50 text-amber-800", error: "border-red-200 bg-red-50 text-red-800" };
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };
const estCls = (e) => (e === "no_cumple" ? "text-red-700 font-semibold" : e === "observaciones" ? "text-amber-700" : "text-emerald-700");
const estLbl = (e) => (e === "no_cumple" ? "No cumple" : e === "observaciones" ? "Revisar" : "Cumple");

export function RebtResultsPanel({ results, editable = false, onUpdateNode, onUpdateBoard, onRecompute, onAutoDimensionar, autoOn = false, recomputing = false }) {
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
      {editable && onAutoDimensionar && (
        <div className={`flex flex-col gap-3 border p-4 sm:flex-row sm:items-center sm:justify-between ${autoOn ? "border-emerald-300 bg-emerald-50/60" : "border-border bg-background"}`} data-testid="rebt-auto-dim-panel">
          <div className="flex items-start gap-3">
            <Wand2 className={`mt-0.5 h-5 w-5 ${autoOn ? "text-emerald-600" : "text-muted-foreground"}`} />
            <div>
              <p className="text-sm font-semibold">Dimensionado automático · cumplimiento REBT 100%</p>
              <p className="text-xs text-muted-foreground">Ajusta la sección de cada línea (y el poder de corte) para cumplir sobrecarga (Ib≤In≤Iz) y cortocircuito (k²·S²≥I²t, Icc_mín≥Im, poder de corte≥Icc) según la ITC-BT-22. Reemplaza las selecciones manuales.</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {autoOn && <span className="inline-flex items-center gap-1 rounded-sm border border-emerald-300 bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800" data-testid="rebt-auto-badge"><CheckCircle2 className="h-3 w-3" />Activado</span>}
            {autoOn
              ? <Button variant="outline" size="sm" className="rounded-sm text-xs" onClick={() => onAutoDimensionar(false)} disabled={recomputing} data-testid="rebt-auto-off">Desactivar</Button>
              : <Button size="sm" className="rounded-sm text-xs" onClick={() => onAutoDimensionar(true)} disabled={recomputing} data-testid="rebt-auto-on">{recomputing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Wand2 className="mr-2 h-4 w-4" />}Dimensionar automáticamente</Button>}
          </div>
        </div>
      )}
      <div className="border border-border bg-background">
        <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2.5">
          <span className="font-heading text-sm">Dimensionado y comprobación de líneas</span>
          {editable && (
            <Button size="sm" className="h-8 rounded-sm" onClick={() => onRecompute?.()} disabled={recomputing} data-testid="rebt-recalcular">
              {recomputing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Calculator className="mr-2 h-4 w-4" />} Recalcular
            </Button>
          )}
        </div>
        {editable && (
          <div className="border-b border-border bg-sky-50/50 px-4 py-1.5 text-[11px] text-sky-800">
            Ajusta la <b>sección</b>, el <b>magnetotérmico</b> y el <b>diferencial</b> de cada circuito y pulsa «Recalcular» para validar la selección (columnas «Protege cable» y «Sel.»).
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-border text-left uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Cuadro</th><th className="px-3">Línea</th><th className="px-3 text-right">Ib (A)</th><th className="px-3 text-right">Sección</th><th className="px-3 text-right">Iz (A)</th><th className="px-3">Magnetotérmico</th><th className="px-3">Protege cable</th><th className="px-3">Sel.</th><th className="px-3 text-right">Caída acum.</th><th className="px-3">Diferencial</th><th className="px-3 text-right">Tierra</th><th className="px-3">Estado</th>
            </tr></thead>
            <tbody className="font-mono">
              {lineas.map((l, i) => {
                const co = l.coordinacion;
                const protege = l.protege_cable;
                const canEdit = editable && l.editable && l.id;
                const canEditBoard = editable && l.editable_board && l.board_id;
                return (
                <tr key={i} className="border-b border-border last:border-0" data-testid={`linea-row-${i}`}>
                  <td className="px-3 py-1.5 font-sans">{l.cuadro}</td><td className="px-3 font-sans">{l.circuito}</td>
                  <td className="px-3 text-right">{l.Ib}</td>
                  <td className="px-3 text-right font-sans">
                    {canEdit ? (
                      <Select value={l.seccion_manual ? String(l.seccion_manual) : "auto"} onValueChange={(v) => onUpdateNode(l.id, { seccion_manual: v === "auto" ? "" : Number(v) })}>
                        <SelectTrigger className="h-7 w-24 rounded-sm text-xs" data-testid={`linea-${i}-seccion-sel`}><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="auto">Auto ({secTxt(l.seccion_auto)} mm²)</SelectItem>{SECCIONES.map((s) => <SelectItem key={s} value={String(s)}>{secTxt(s)} mm²</SelectItem>)}</SelectContent>
                      </Select>
                    ) : canEditBoard ? (
                      <Select value={l.seccion_manual ? String(l.seccion_manual) : "auto"} onValueChange={(v) => onUpdateBoard(l.board_id, { seccion_manual: v === "auto" ? "" : Number(v) })}>
                        <SelectTrigger className="h-7 w-24 rounded-sm text-xs" data-testid={`board-${i}-seccion-sel`}><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="auto">Auto ({secTxt(l.seccion_auto)} mm²)</SelectItem>{SECCIONES.map((s) => <SelectItem key={s} value={String(s)}>{secTxt(s)} mm²</SelectItem>)}</SelectContent>
                      </Select>
                    ) : <>{l.seccion_txt} mm²</>}
                  </td>
                  <td className="px-3 text-right">{l.iz}</td>
                  <td className="px-3 font-sans">
                    {canEdit ? (
                      <Select value={l.magneto_manual ? String(l.magneto_manual) : "auto"} onValueChange={(v) => onUpdateNode(l.id, { magneto_manual: v === "auto" ? "" : Number(v) })}>
                        <SelectTrigger className="h-7 w-24 rounded-sm text-xs" data-testid={`linea-${i}-magneto-sel`}><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="auto">Auto ({l.magneto_auto} A)</SelectItem>{MAGNETOS.map((m) => <SelectItem key={m} value={String(m)}>{m} A</SelectItem>)}</SelectContent>
                      </Select>
                    ) : canEditBoard ? (
                      <Select value={l.magneto_manual ? String(l.magneto_manual) : "auto"} onValueChange={(v) => onUpdateBoard(l.board_id, { iga_manual: v === "auto" ? "" : Number(v) })}>
                        <SelectTrigger className="h-7 w-28 rounded-sm text-xs" data-testid={`board-${i}-iga-sel`}><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="auto">IGA Auto ({l.magneto_auto} A)</SelectItem>{MAGNETOS.map((m) => <SelectItem key={m} value={String(m)}>IGA {m} A</SelectItem>)}</SelectContent>
                      </Select>
                    ) : l.proteccion}
                  </td>
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
                  <td className="px-3 font-sans" data-testid={`linea-${i}-seleccion`}>
                    {l.seleccion_manual != null ? (
                      l.seleccion_manual ? (
                        <span className={protege ? "text-emerald-700" : "text-red-700 font-semibold"}>{protege ? "Correcta" : `Incorrecta (rec. ${l.magneto_auto} A)`}</span>
                      ) : <span className="text-muted-foreground">Auto</span>
                    ) : "—"}
                  </td>
                  <td className="px-3 text-right">{l.caida_acum_pct}%</td>
                  <td className="px-3 font-sans">
                    {canEdit ? (
                      <div className="flex items-center gap-1">
                        <Select value={String(l.sensibilidad ?? 30)} onValueChange={(v) => onUpdateNode(l.id, { dif_propio: true, sensibilidad: Number(v) })}>
                          <SelectTrigger className="h-7 w-20 rounded-sm text-xs" data-testid={`linea-${i}-dif-sel`}><SelectValue /></SelectTrigger>
                          <SelectContent><SelectItem value="30">30 mA</SelectItem><SelectItem value="300">300 mA</SelectItem></SelectContent>
                        </Select>
                        {l.diferencial_ok === false && <AlertTriangle className="h-3.5 w-3.5 text-amber-600" title={l.diferencial_nota} />}
                      </div>
                    ) : canEditBoard ? (
                      <Select value={String(l.sensibilidad ?? 300)} onValueChange={(v) => onUpdateBoard(l.board_id, { diferencial_general: { sensibilidad: Number(v) } })}>
                        <SelectTrigger className="h-7 w-28 rounded-sm text-xs" data-testid={`board-${i}-dif-sel`}><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="30">30 mA (gen.)</SelectItem><SelectItem value="300">300 mA (gen.)</SelectItem></SelectContent>
                      </Select>
                    ) : l.diferencial}
                  </td>
                  <td className="px-3 text-right">{l.tierra}</td>
                  <td className={`px-3 font-sans ${estCls(l.estado)}`}>{estLbl(l.estado)}</td>
                </tr>
              );})}
            </tbody>
          </table>
        </div>
        <div className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          <b>Coordinación protección↔cable (ITC-BT-22):</b> Sobrecarga — Ib ≤ In ≤ Iz e I2 ≤ 1,45·Iz (I2 = 1,45·In). Cortocircuito — poder de corte ≥ Icc máx, k²·S² ≥ I²t e Icc mín ≥ Im. Poder de corte mínimo recomendado: <b className="text-foreground">{results.datos?.poder_corte_ka ?? 6} kA</b>.
        </div>
      </div>

      {/* Cortocircuito (ITC-BT-22) */}
      <div className="border border-border bg-background">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5 font-heading text-sm">Cortocircuito (ITC-BT-22)</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-border text-left uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Cuadro</th><th className="px-3">Línea</th><th className="px-3 text-right">Icc máx (A)</th><th className="px-3 text-right">Icc mín (A)</th><th className="px-3 text-right">Im (A)</th><th className="px-3">Poder corte</th><th className="px-3">Térmico k²S²≥I²t</th><th className="px-3">Disparo Icc≥Im</th><th className="px-3">Protege CC</th><th className="px-3">Recomendación</th>
            </tr></thead>
            <tbody className="font-mono">
              {lineas.filter((l) => l.cortocircuito).map((l, i) => {
                const c = l.cortocircuito;
                const yn = (ok) => <span className={ok ? "text-emerald-700" : "text-amber-800 font-semibold"}>{ok ? "Sí ✓" : "No ✗"}</span>;
                return (
                  <tr key={i} className="border-b border-border last:border-0" data-testid={`cc-row-${i}`}>
                    <td className="px-3 py-1.5 font-sans">{l.cuadro}</td><td className="px-3 font-sans">{l.circuito}</td>
                    <td className="px-3 text-right">{num(c.icc_max_a, 0)}</td><td className="px-3 text-right">{num(c.icc_min_a, 0)}</td>
                    <td className="px-3 text-right">{num(c.im_a, 0)}</td>
                    <td className="px-3 font-sans">{yn(c.pdc_ok)}</td><td className="px-3 font-sans">{yn(c.termico_ok)}</td><td className="px-3 font-sans">{yn(c.magnetico_ok)}</td>
                    <td className="px-3 font-sans">{yn(c.protege_cc)}</td>
                    <td className="px-3 font-sans text-[11px] text-amber-800" data-testid={`cc-${i}-reco`}>{c.recomendacion ? c.recomendacion.replace(/^Recomendación:\s*/, "") : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          Icc por método simplificado (Guía BT-22) a partir de la Icc presunta en origen y la impedancia de los conductores. Valores orientativos: contrastar con la Icc real del punto de instalación.
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
