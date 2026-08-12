import { AlertTriangle, CheckCircle2, Info, XCircle, Cable, RotateCcw, Loader2 } from "lucide-react";
import { STATE_META } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui/select";

const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };
const SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240];
const fmtS = (s) => `${s}`.replace(".", ",");

// Diagrama del agrupamiento: n bundles dentro de una canalización, el estudiado resaltado.
function GroupingDiagram({ n, factor, nCond, fases }) {
  const N = Math.max(1, Math.min(12, n || 1));
  const r = 9, gap = 8, padX = 16, padY = 12;
  const bundleW = fases * (2 * r) + (fases - 1) * 4;
  const W = padX * 2 + N * bundleW + (N - 1) * gap;
  const H = padY * 2 + 2 * r;
  return (
    <div className="flex flex-col items-center gap-2" data-testid="linea-grouping-diagram">
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" className="max-w-md">
        <rect x="1" y="1" width={W - 2} height={H - 2} rx="10" className="fill-slate-50 stroke-slate-300" strokeWidth="1.5" />
        {Array.from({ length: N }).map((_, ci) => {
          const bx = padX + ci * (bundleW + gap);
          const active = ci === 0;
          return (
            <g key={ci}>
              {Array.from({ length: fases }).map((__, fi) => (
                <circle key={fi} cx={bx + r + fi * (2 * r + 4)} cy={padY + r} r={r}
                  className={active ? "fill-amber-400 stroke-amber-600" : "fill-slate-200 stroke-slate-400"} strokeWidth="1.2" />
              ))}
            </g>
          );
        })}
      </svg>
      <p className="text-center text-xs text-muted-foreground">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-400 align-middle" /> Circuito estudiado
        {" · "}{N} circuito{N > 1 ? "s" : ""} en la misma canalización
        {nCond > 1 ? ` · ${nCond} conductor(es) por fase` : ""}
        {" → factor de agrupamiento "}<strong>{factor}</strong>
      </p>
    </div>
  );
}

// Panel de resultados del módulo «REBT · Comprobación de una línea» con edición y recálculo.
export function RebtLineaResultPanel({ results, data, setData, onRecompute, recomputing }) {
  if (!results) return null;
  const {
    resumen = [], comprobaciones = [], observaciones = [], estado_global,
    agrupamiento = {}, entradas = {}, paralelo = {},
  } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;
  const n = paralelo.n || 1;
  const fases = entradas.suministro === "trifasica" ? 3 : 2;
  const editable = !!setData;

  const setField = (name, value) => setData((d) => ({ ...d, [name]: value }));

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

      {/* Ajuste de la solución (editable en resultados) */}
      {editable && (
        <div className="border border-border bg-background" data-testid="linea-ajustes">
          <div className="border-b border-border bg-secondary/40 px-4 py-2.5">
            <span className="font-heading text-sm">Ajustar solución para que cumpla</span>
          </div>
          <div className="grid grid-cols-2 gap-4 p-4 sm:grid-cols-3 lg:grid-cols-5">
            <div>
              <Label className="text-xs">Conductores por fase</Label>
              <Input type="number" min={1} className="mt-1 rounded-sm" data-testid="linea-edit-nconductores"
                value={data?.n_conductores ?? 1}
                onChange={(e) => setField("n_conductores", Math.max(1, parseInt(e.target.value || "1", 10)))} />
            </div>
            <div>
              <Label className="text-xs">Sección/conductor</Label>
              <Select value={data?.seccion_manual ? String(data.seccion_manual) : "auto"}
                onValueChange={(v) => setField("seccion_manual", v === "auto" ? undefined : parseFloat(v))}>
                <SelectTrigger className="mt-1 rounded-sm" data-testid="linea-edit-seccion"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Automática</SelectItem>
                  {SECCIONES.map((s) => <SelectItem key={s} value={String(s)}>{fmtS(s)} mm²</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs">Curva magnetotérmico</Label>
              <Select value={data?.curva || "C"} onValueChange={(v) => setField("curva", v)}>
                <SelectTrigger className="mt-1 rounded-sm" data-testid="linea-edit-curva"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["B", "C", "D"].map((c) => <SelectItem key={c} value={c}>Curva {c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs">Poder de corte (kA)</Label>
              <Input type="number" min={1} className="mt-1 rounded-sm" data-testid="linea-edit-pdc"
                value={data?.poder_corte_ka ?? 6}
                onChange={(e) => setField("poder_corte_ka", Math.max(1, parseInt(e.target.value || "6", 10)))} />
            </div>
            <div>
              <Label className="text-xs">Icc en origen (A)</Label>
              <Input type="number" min={0} className="mt-1 rounded-sm" data-testid="linea-edit-icc"
                value={data?.icc_origen_a ?? 6000}
                onChange={(e) => setField("icc_origen_a", Math.max(0, parseInt(e.target.value || "6000", 10)))} />
            </div>
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">
              Con «Sección automática» el motor dimensiona la sección para el nº de conductores indicado. Si sigue sin
              cumplir, aumenta los conductores por fase, sube la sección o revisa la Icc/curva.
            </p>
            <Button className="rounded-sm" onClick={onRecompute} disabled={recomputing} data-testid="linea-recompute">
              {recomputing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RotateCcw className="mr-2 h-4 w-4" />}
              Recalcular
            </Button>
          </div>
        </div>
      )}

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

      {/* Agrupamiento + diagrama */}
      <div className="border border-border bg-background" data-testid="linea-agrupamiento">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5">
          <span className="font-heading text-sm">Factor de agrupamiento (UNE-HD 60364-5-52, Tabla B.52.17)</span>
        </div>
        <div className="border-b border-border p-4">
          <GroupingDiagram n={agrupamiento.n_circuitos} factor={agrupamiento.factor} nCond={n} fases={fases} />
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
