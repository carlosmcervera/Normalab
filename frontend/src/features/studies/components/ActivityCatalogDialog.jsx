import { useMemo, useState } from "react";
import { Search, Flame, Package, Check } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { num } from "@/lib/format";

// Modal buscador de la Tabla 1.3.5 (RSCIEI). Permite filtrar por texto y seleccionar
// una actividad/subactividad, devolviendo (categoría, subactividad) al padre.
export function ActivityCatalogDialog({ open, onOpenChange, catalog = [], current, onSelect }) {
  const [q, setQ] = useState("");

  const groups = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return catalog
      .map((c) => {
        const subs = c.subactivities.filter((s) =>
          !needle ||
          s.name.toLowerCase().includes(needle) ||
          c.category.toLowerCase().includes(needle));
        return { category: c.category, subs };
      })
      .filter((g) => g.subs.length > 0);
  }, [catalog, q]);

  const totalShown = groups.reduce((a, g) => a + g.subs.length, 0);

  const pick = (category, s) => {
    onSelect(category, s);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl gap-0 overflow-hidden p-0" data-testid="activity-catalog-dialog">
        <DialogHeader className="border-b border-border px-4 py-3">
          <DialogTitle className="font-heading text-base">Tabla 1.3.5 · Cargas de fuego (RSCIEI)</DialogTitle>
          <DialogDescription className="text-xs">
            Busca y selecciona la actividad. Producción en MJ/m² (qs); almacenamiento en MJ/m³ (qv bruto · neto).
          </DialogDescription>
        </DialogHeader>
        <div className="border-b border-border p-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar actividad (p. ej. oficinas, papel, almacén…)"
              className="h-9 rounded-sm pl-9 text-sm"
              data-testid="activity-search-input"
            />
          </div>
          <p className="mt-1.5 text-[11px] text-muted-foreground">{totalShown} resultado(s)</p>
        </div>
        <div className="max-h-[55vh] overflow-y-auto">
          {groups.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">Sin coincidencias.</p>
          ) : (
            groups.map((g) => (
              <div key={g.category}>
                <div className="sticky top-0 z-10 bg-secondary/80 px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground backdrop-blur">
                  {g.category}
                </div>
                {g.subs.map((s, i) => {
                  const alm = s.modo === "almacenamiento";
                  const active = current && current.category === g.category && current.name === s.name;
                  return (
                    <button
                      key={i}
                      onClick={() => pick(g.category, s)}
                      className={`flex w-full items-center gap-3 border-b border-border px-4 py-2 text-left transition-colors hover:bg-secondary/50 ${active ? "bg-primary/5" : ""}`}
                      data-testid={`activity-option-${g.category}-${s.name}`.replace(/[^a-zA-Z0-9-]/g, "_")}
                    >
                      <Badge variant="outline" className={`shrink-0 rounded-sm border-0 px-1.5 text-[10px] ${alm ? "bg-amber-100 text-amber-800" : "bg-orange-100 text-orange-800"}`}>
                        {alm ? <Package className="mr-1 h-3 w-3" /> : <Flame className="mr-1 h-3 w-3" />}
                        {alm ? "Almac." : "Prod."}
                      </Badge>
                      <span className="min-w-0 flex-1 truncate text-sm" title={s.name}>{s.name}</span>
                      <span className="shrink-0 font-mono text-xs text-muted-foreground">
                        {alm
                          ? <>qv {num(s.qvi)}{s.qvi_neto ? ` · ${num(s.qvi_neto)}` : ""} <span className="opacity-60">MJ/m³</span></>
                          : <>qs {num(s.qsi)} <span className="opacity-60">MJ/m²</span></>}
                        {"  "}· Ci {num(s.ci, 2)}{s.rmin ? ` · Rmin ${num(s.rmin, 1)}` : ""}
                      </span>
                      {active && <Check className="h-4 w-4 shrink-0 text-primary" />}
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
