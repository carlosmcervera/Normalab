import { AlertTriangle, CheckCircle2, Info, XCircle, Cable, Wand2 } from "lucide-react";
import { STATE_META } from "@/lib/format";
import { Button } from "@/components/ui/button";

const OBS_CLS = {
  info: "border-slate-200 bg-slate-50 text-slate-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800",
};
const OBS_ICON = { info: Info, warning: AlertTriangle, error: XCircle };

// Diagrama del agrupamiento: n_circuitos manojos dentro de una canalización; el circuito
// estudiado se resalta y muestra sus conductores en paralelo por fase.
function GroupingDiagram({ nCirc, factor, nCond, fases }) {
  const N = Math.max(1, Math.min(12, nCirc || 1));
  const nc = Math.max(1, nCond || 1);
  const r = 6, condGap = 3, phaseGap = 7, bundleGap = 12, padX = 16, padY = 12;
  const condW = 2 * r;
  const phaseW = nc * condW + (nc - 1) * condGap;
  const bundleW = fases * phaseW + (fases - 1) * phaseGap;
  const W = padX * 2 + N * bundleW + (N - 1) * bundleGap;
  const H = padY * 2 + 2 * r;
  return (
    <div className="flex flex-col items-center gap-2" data-testid="linea-grouping-diagram">
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" className="max-w-lg">
        <rect x="1" y="1" width={W - 2} height={H - 2} rx="10" className="fill-slate-50 stroke-slate-300" strokeWidth="1.5" />
        {Array.from({ length: N }).map((_, ci) => {
          const active = ci === 0;
          const bx = padX + ci * (bundleW + bundleGap);
          return (
            <g key={ci}>
              {Array.from({ length: fases }).map((__, fi) => {
                const px = bx + fi * (phaseW + phaseGap);
                return Array.from({ length: nc }).map((___, ki) => (
                  <circle key={`${fi}-${ki}`} cx={px + r + ki * (condW + condGap)} cy={padY + r} r={r}
                    className={active ? "fill-amber-400 stroke-amber-600" : "fill-slate-200 stroke-slate-400"} strokeWidth="1.1" />
                ));
              })}
            </g>
          );
        })}
      </svg>
      <p className="text-center text-xs text-muted-foreground">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-400 align-middle" /> Circuito estudiado
        {" · "}{N} circuito{N > 1 ? "s" : ""} en la misma canalización
        {nc > 1 ? ` · ${nc} conductores por fase` : ""}
        {" → factor de agrupamiento "}<strong>{factor}</strong>
      </p>
    </div>
  );
}

// Panel de resultados del módulo «REBT · Comprobación de una línea» (presentacional).
export function RebtLineaResultPanel({ results, onApplyReco }) {
  if (!results) return null;
  const {
    resumen = [], comprobaciones = [], observaciones = [], estado_global,
    agrupamiento = {}, entradas = {}, paralelo = {}, recomendada,
  } = results;
  const state = STATE_META[estado_global] || STATE_META.observaciones;
  const n = paralelo.n || 1;
  const fases = entradas.suministro === "trifasica" ? 3 : 2;

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

      {/* Solución recomendada (cuando no cumple) */}
      {recomendada && (
        <div className="flex flex-col gap-3 border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900 sm:flex-row sm:items-center sm:justify-between" data-testid="linea-recomendada">
          <div className="flex items-start gap-3">
            <Wand2 className="mt-0.5 h-4 w-4 shrink-0" />
            <p>
              Solución que cumple: <strong>{recomendada.n > 1 ? `${recomendada.n}×` : ""}{`${recomendada.s}`.replace(".", ",")} mm²/fase</strong>
              {" "}con protección <strong>{recomendada.In} A</strong> (caída {recomendada.caida}%).
            </p>
          </div>
          {onApplyReco && (
            <Button size="sm" className="shrink-0 rounded-sm" onClick={() => onApplyReco(recomendada)} data-testid="linea-apply-reco">
              Aplicar ({recomendada.n} conductor{recomendada.n > 1 ? "es" : ""}/fase)
            </Button>
          )}
        </div>
      )}

      {/* Conductores en paralelo (solo si N > 1) */}
      {n > 1 && (
        <div className="flex items-start gap-3 border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900" data-testid="linea-paralelo">
          <Cable className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Línea con <strong>{n} conductores en paralelo por fase</strong> de{" "}
            <strong>{paralelo.seccion_por_conductor_txt} mm²</strong> (sección total{" "}
            <strong>{paralelo.seccion_efectiva_txt} mm²/fase</strong>). Deben tener la misma longitud,
            sección y disposición para repartir la corriente (ITC-BT-19).
          </p>
        </div>
      )}

      {/* Agrupamiento + diagrama */}
      <div className="border border-border bg-background" data-testid="linea-agrupamiento">
        <div className="border-b border-border bg-secondary/40 px-4 py-2.5">
          <span className="font-heading text-sm">Factor de agrupamiento (UNE-HD 60364-5-52, Tabla B.52.17)</span>
        </div>
        <div className="border-b border-border p-4">
          <GroupingDiagram nCirc={agrupamiento.n_circuitos} factor={agrupamiento.factor} nCond={n} fases={fases} />
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
