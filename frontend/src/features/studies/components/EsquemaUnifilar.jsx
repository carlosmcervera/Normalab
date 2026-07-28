import { CircuitBoard, Zap } from "lucide-react";

const EST = { cumple: "text-emerald-700", no_cumple: "text-red-700 font-semibold", observaciones: "text-amber-700" };
const dot = (e) => (e === "no_cumple" ? "bg-red-500" : e === "observaciones" ? "bg-amber-500" : "bg-emerald-500");

// Aplana el árbol de cuadros en una lista de filas (sin recursión en JSX).
function flatten(board, nivel, out, raiz) {
  const a = board.alimentacion || {};
  out.push({ kind: "board", nivel, raiz, id: board.id, nombre: board.nombre, iga: board.iga,
    dif: board.diferencial_general_ma, p: board.potencia_demandada, ib: board.Ib,
    alim: `${a.tipo}: ${a.seccion_txt} mm² · caída ${a.caida_pct}% (acum. ${a.caida_acum_pct}%)` });
  const difs = board.diferenciales || [];
  const asignadas = new Set();
  difs.forEach((d) => {
    out.push({ kind: "dif", nivel, id: d.id, nombre: d.nombre, sens: d.sensibilidad, in: d.in });
    (board.cargas || []).filter((c) => c.diferencial_id === d.id).forEach((c) => {
      asignadas.add(c.id);
      out.push({ kind: "circ", nivel, dif: true, ...c });
    });
  });
  (board.cargas || []).filter((c) => !asignadas.has(c.id)).forEach((c) => out.push({ kind: "circ", nivel, dif: false, ...c }));
  (board.subcuadros || []).forEach((sc) => flatten(sc, nivel + 1, out, false));
}

export function EsquemaUnifilar({ arbol }) {
  if (!arbol) return null;
  const rows = [];
  flatten(arbol, 0, rows, true);
  return (
    <div className="space-y-1" data-testid="esquema-unifilar">
      {rows.map((r, i) => {
        const pad = { marginLeft: r.nivel * 18 };
        if (r.kind === "board") {
          return (
            <div key={i} style={pad} className={`rounded-sm border-2 ${r.raiz ? "border-orange-400" : "border-blue-400"} bg-secondary/30 p-2.5`} data-testid={`esquema-board-${r.id}`}>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                <CircuitBoard className={`h-4 w-4 ${r.raiz ? "text-orange-500" : "text-blue-500"}`} />
                <span className="font-semibold">{r.nombre}</span>
                <span className="rounded-sm bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-white">IGA {r.iga} A</span>
                <span className="rounded-sm border border-slate-300 px-1.5 py-0.5 font-mono text-[11px]">ID {r.dif} mA</span>
                <span className="font-mono text-[11px] text-muted-foreground">P cálc. {r.p} W · Ib {r.ib} A</span>
              </div>
              <div className="mt-1 font-mono text-[11px] text-muted-foreground">{r.alim}</div>
            </div>
          );
        }
        if (r.kind === "dif") {
          return (
            <div key={i} style={{ marginLeft: r.nivel * 18 + 16 }} className="pt-1" data-testid={`esquema-dif-${r.id}`}>
              <span className="rounded-sm border border-slate-300 bg-background px-1.5 py-0.5 font-mono text-xs">◊ {r.nombre} · {r.sens} mA · In {r.in} A</span>
            </div>
          );
        }
        return (
          <div key={i} style={{ marginLeft: r.nivel * 18 + (r.dif ? 32 : 16) }} className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs" data-testid={`esquema-circuito-${r.id}`}>
            <span className={`h-2 w-2 shrink-0 rounded-full ${dot(r.estado)}`} />
            <Zap className="h-3 w-3 text-amber-500" />
            <span className="min-w-[110px] font-medium">{r.nombre}</span>
            <span className="rounded-sm bg-slate-800 px-1 font-mono text-[10px] text-white">{r.magneto} A</span>
            <span className={`font-mono text-[11px] ${EST[r.estado] || ""}`}>{r.seccion_txt} mm² · {r.potencia} W · caída {r.caida_acum_pct}% (máx {r.limite_total}%) · tierra {r.tierra} mm²</span>
          </div>
        );
      })}
    </div>
  );
}
