import { Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { CiTableDialog } from "@/features/studies/components/CiTableDialog";
import { num } from "@/lib/format";

const CUSTOM = "__custom__";

export function ZonaActivityEditor({ zona, index, catalog = [], ciTable = [], onChange, onRemove, onBumpRa }) {
  const cat = catalog.find((c) => c.category === zona.categoria);
  const isCustom = zona.categoria === CUSTOM;

  const patch = (p) => onChange({ ...zona, ...p });

  const selectCategoria = (value) => {
    if (value === CUSTOM) {
      patch({ categoria: CUSTOM, subactividad: "", descripcion: zona.descripcion || "", modo: zona.modo || "produccion" });
    } else {
      patch({ categoria: value, subactividad: "", descripcion: "", qsi: undefined, qvi: undefined });
    }
  };

  const selectSubactividad = (idx) => {
    const s = cat.subactivities[Number(idx)];
    patch({
      subactividad: s.name,
      descripcion: s.name,
      modo: s.modo,
      qsi: s.modo === "produccion" ? s.qsi : undefined,
      qvi: s.modo === "almacenamiento" ? s.qvi : undefined,
      ci: s.ci,
      ra: s.ra,
    });
    if (s.ra) onBumpRa?.(s.ra);
  };

  const almacen = zona.modo === "almacenamiento";
  const dens = almacen ? zona.qvi : zona.qsi;
  const aporte = almacen
    ? (Number(zona.qvi) || 0) * (Number(zona.ci) || 0) * (Number(zona.hi) || 0) * (Number(zona.superficie) || 0)
    : (Number(zona.qsi) || 0) * (Number(zona.superficie) || 0) * (Number(zona.ci) || 0);

  return (
    <div className="border border-border" data-testid={`zona-${index}`}>
      <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Actividad {index + 1}</p>
        <div className="flex items-center gap-2">
          {dens != null && dens !== "" && (
            <Badge variant="outline" className="rounded-sm font-mono text-xs">
              {almacen ? `${num(zona.qvi)} MJ/m³` : `${num(zona.qsi)} MJ/m²`}
            </Badge>
          )}
          <Button variant="ghost" size="icon" className="h-7 w-7 rounded-sm text-muted-foreground hover:text-destructive" onClick={onRemove} data-testid={`remove-zona-${index}`}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-4 p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Actividad principal</Label>
            <Select value={zona.categoria || ""} onValueChange={selectCategoria}>
              <SelectTrigger className="rounded-sm" data-testid={`zona-${index}-categoria`}><SelectValue placeholder="Selecciona categoría" /></SelectTrigger>
              <SelectContent>
                {catalog.map((c) => <SelectItem key={c.category} value={c.category}>{c.category}</SelectItem>)}
                <SelectItem value={CUSTOM}>+ Actividad personalizada</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Subactividad</Label>
            {isCustom ? (
              <Input value={zona.descripcion || ""} onChange={(e) => patch({ descripcion: e.target.value })} placeholder="Descripción de la actividad" data-testid={`zona-${index}-descripcion`} />
            ) : (
              <Select
                value={cat ? String(cat.subactivities.findIndex((s) => s.name === zona.subactividad)) : ""}
                onValueChange={selectSubactividad}
                disabled={!cat}
              >
                <SelectTrigger className="rounded-sm" data-testid={`zona-${index}-subactividad`}><SelectValue placeholder="Selecciona subactividad" /></SelectTrigger>
                <SelectContent>
                  {(cat?.subactivities || []).map((s, i) => <SelectItem key={i} value={String(i)}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="space-y-1.5">
            <Label>Tipo</Label>
            <Select value={zona.modo || "produccion"} onValueChange={(v) => patch({ modo: v })}>
              <SelectTrigger className="rounded-sm" data-testid={`zona-${index}-modo`}><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="produccion">Producción</SelectItem>
                <SelectItem value="almacenamiento">Almacenamiento</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>{almacen ? "qvi (MJ/m³)" : "qsi (MJ/m²)"}</Label>
            <Input type="number" min={0} value={dens ?? ""} data-testid={`zona-${index}-densidad`}
              onChange={(e) => patch(almacen ? { qvi: e.target.value === "" ? "" : Number(e.target.value) } : { qsi: e.target.value === "" ? "" : Number(e.target.value) })} />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Ci</Label>
              <CiTableDialog ciTable={ciTable} current={Number(zona.ci)} onSelect={(ci) => patch({ ci })} />
            </div>
            <Input type="number" min={0} step={0.01} value={zona.ci ?? ""} data-testid={`zona-${index}-ci`}
              onChange={(e) => patch({ ci: e.target.value === "" ? "" : Number(e.target.value) })} />
          </div>
          <div className="space-y-1.5">
            <Label>Superficie Si (m²)</Label>
            <Input type="number" min={0} value={zona.superficie ?? ""} data-testid={`zona-${index}-superficie`}
              onChange={(e) => patch({ superficie: e.target.value === "" ? "" : Number(e.target.value) })} />
          </div>
        </div>

        {almacen && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="space-y-1.5">
              <Label>Altura almac. hi (m)</Label>
              <Input type="number" min={0} step={0.1} value={zona.hi ?? ""} data-testid={`zona-${index}-altura`}
                onChange={(e) => patch({ hi: e.target.value === "" ? "" : Number(e.target.value) })} />
            </div>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-border pt-3 text-sm">
          <span className="text-muted-foreground">Ra actividad: <span className="font-mono">{zona.ra ? num(zona.ra, 2) : "—"}</span></span>
          <span className="font-mono">Aporte: <span className="font-semibold">{num(aporte)} MJ</span></span>
        </div>
      </div>
    </div>
  );
}
