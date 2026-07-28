import { CircuitBoard, Zap, GitBranch, ShieldPlus } from "lucide-react";

const EST = { cumple: "text-emerald-700", no_cumple: "text-red-700 font-semibold", observaciones: "text-amber-700" };
const dot = (e) => (e === "no_cumple" ? "bg-red-500" : e === "observaciones" ? "bg-amber-500" : "bg-emerald-500");
const chip = "rounded-sm bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-white";
const tag = "rounded-sm border border-slate-300 px-1.5 py-0.5 font-mono text-[11px]";

// Aplana el árbol en filas (sin recursión en JSX) para dibujar el esquema unifilar.
function flatten(board, nivel, out, raiz) {
  const a = board.alimentacion || {};
  if (board.lga) out.push({ kind: "lga", nivel, ...board.lga, id: `lga-${board.id}` });
  out.push({
    kind: "board", nivel, raiz, id: board.id, nombre: board.nombre, iga: board.iga,
    dif: board.diferencial_general_ma, spd: board.spd || {}, p: board.potencia_demandada, ib: board.Ib,
    alim: `${a.tipo}: ${a.seccion_txt} mm² · caída ${a.caida_pct}% (acum. ${a.caida_acum_pct}%)`,
  });
  (board.nodos || []).forEach((n) => {
    if (n.kind === "linea") out.push({ kind: "circ", nivel, ...n });
    else if (n.kind === "puente") {
      out.push({ kind: "puente", nivel, ...n });
      (n.sublineas || []).forEach((s) => out.push({ kind: "circ", nivel, sub: true, ...s }));
    } else if (n.kind === "subcuadro") {
      flatten(n.board, nivel + 1, out, false);
    }
  });
}

export function EsquemaUnifilar({ arbol }) {
  if (!arbol) return null;
  const rows = [];
  flatten(arbol, 0, rows, true);
  return (
    <div className="space-y-1" data-testid="esquema-unifilar">
      {rows.map((r, i) => {
        if (r.kind === "lga") {
          return (
            <div key={i} style={{ marginLeft: r.nivel * 18 }} className="flex flex-wrap items-center gap-x-2 text-xs" data-testid={`esquema-lga-${r.id}`}>
              <span className={tag}>LGA · {r.seccion_txt} mm² · caída {r.caida_pct}%</span>
            </div>
          );
        }
        if (r.kind === "board") {
          return (
            <div key={i} style={{ marginLeft: r.nivel * 18 }} className={`rounded-sm border-2 ${r.raiz ? "border-orange-400" : "border-blue-400"} bg-secondary/30 p-2.5`} data-testid={`esquema-board-${r.id}`}>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                <CircuitBoard className={`h-4 w-4 ${r.raiz ? "text-orange-500" : "text-blue-500"}`} />
                <span className="font-semibold">{r.nombre}</span>
                <span className={chip}>IGA {r.iga} A</span>
                <span className={tag}>ID {r.dif} mA</span>
                {r.spd?.presente && <span className="inline-flex items-center gap-1 rounded-sm border border-emerald-300 bg-emerald-50 px-1.5 py-0.5 font-mono text-[11px] text-emerald-700"><ShieldPlus className="h-3 w-3" />SPD {r.spd.tipo}</span>}
                <span className="font-mono text-[11px] text-muted-foreground">P cálc. {r.p} W · Ib {r.ib} A</span>
              </div>
              <div className="mt-1 font-mono text-[11px] text-muted-foreground">{r.alim}</div>
            </div>
          );
        }
        if (r.kind === "puente") {
          return (
            <div key={i} style={{ marginLeft: r.nivel * 18 + 16 }} className="flex flex-wrap items-center gap-x-2 pt-1 text-xs" data-testid={`esquema-puente-${r.id}`}>
              <GitBranch className="h-3.5 w-3.5 text-purple-600" />
              <span className="font-medium">{r.nombre}</span>
              <span className={chip}>{r.magneto} A</span>
              <span className={tag}>ID {r.sensibilidad} mA</span>
              <span className={`font-mono text-[11px] ${EST[r.estado] || ""}`}>{r.seccion_txt} mm² · caída {r.caida_acum_pct}% · tierra {r.tierra} mm²</span>
            </div>
          );
        }
        return (
          <div key={i} style={{ marginLeft: r.nivel * 18 + (r.sub ? 34 : 16) }} className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs" data-testid={`esquema-circuito-${r.id}`}>
            <span className={`h-2 w-2 shrink-0 rounded-full ${dot(r.estado)}`} />
            <Zap className="h-3 w-3 text-amber-500" />
            <span className="min-w-[110px] font-medium">{r.nombre}</span>
            <span className={chip}>{r.magneto} A</span>
            {!r.sub && <span className={tag}>ID {r.sensibilidad} mA</span>}
            <span className={`font-mono text-[11px] ${EST[r.estado] || ""}`}>{r.seccion_txt} mm² · {r.potencia} W · caída {r.caida_acum_pct}% (máx {r.limite_total}%) · tierra {r.tierra} mm²</span>
          </div>
        );
      })}
    </div>
  );
}
