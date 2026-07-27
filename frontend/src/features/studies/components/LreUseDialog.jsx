import { useMemo, useState } from "react";
import { Search, ShieldAlert, Check } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { LRE_USES } from "@/lib/lreCatalog";

// Modal buscador de usos de Local de Riesgo Especial (Tabla 2.1 CTE DB-SI).
export function LreUseDialog({ open, onOpenChange, current, onSelect }) {
  const [q, setQ] = useState("");

  const groups = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return LRE_USES
      .map((g) => ({
        group: g.group,
        uses: g.uses.filter((u) =>
          !needle || u.name.toLowerCase().includes(needle) || g.group.toLowerCase().includes(needle)),
      }))
      .filter((g) => g.uses.length > 0);
  }, [q]);

  const total = groups.reduce((a, g) => a + g.uses.length, 0);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl gap-0 overflow-hidden p-0" data-testid="lre-use-dialog">
        <DialogHeader className="border-b border-border px-4 py-3">
          <DialogTitle className="font-heading text-base">Tabla 2.1 · Locales y zonas de riesgo especial (CTE DB-SI)</DialogTitle>
          <DialogDescription className="text-xs">
            Selecciona el uso del local. El riesgo (bajo/medio/alto) se determinará por el volumen (superficie × altura), la superficie o la potencia según el criterio.
          </DialogDescription>
        </DialogHeader>
        <div className="border-b border-border p-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input autoFocus value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar uso (p. ej. calderas, almacén, transformador…)"
              className="h-9 rounded-sm pl-9 text-sm" data-testid="lre-search-input" />
          </div>
          <p className="mt-1.5 text-[11px] text-muted-foreground">{total} uso(s)</p>
        </div>
        <div className="max-h-[55vh] overflow-y-auto">
          {groups.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">Sin coincidencias.</p>
          ) : groups.map((g) => (
            <div key={g.group}>
              <div className="sticky top-0 z-10 bg-secondary/80 px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground backdrop-blur">{g.group}</div>
              {g.uses.map((u, i) => {
                const active = current && current === u.name;
                return (
                  <button key={i} onClick={() => { onSelect(g.group, u); onOpenChange(false); }}
                    className={`flex w-full items-start gap-3 border-b border-border px-4 py-2 text-left transition-colors hover:bg-secondary/50 ${active ? "bg-primary/5" : ""}`}
                    data-testid={`lre-option-${i}`}>
                    <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm">{u.name}</span>
                      <span className="block font-mono text-[11px] text-muted-foreground">{u.crit}</span>
                    </span>
                    {active && <Check className="h-4 w-4 shrink-0 text-primary" />}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
