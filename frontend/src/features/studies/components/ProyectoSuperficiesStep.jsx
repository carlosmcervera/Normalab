import { Plus, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { NumberInput } from "@/components/NumberInput";
import { num } from "@/lib/format";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

// Paso 1 · Cuadro de superficies: inventario de estancias/dependencias (útil + construida).
export function ProyectoSuperficiesStep({ data, setData }) {
  const deps = data.dependencias || [];

  const addDep = () =>
    setData((d) => ({
      ...d,
      dependencias: [...(d.dependencias || []), {
        id: genId(), nombre: "", etiqueta: "", planta: "", grupo: "",
        sup_util: "", sup_construida: "", modo: "produccion", ci: 1.44,
      }],
    }));
  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));
  const removeDep = (id) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.filter((x) => x.id !== id) }));

  const totalU = deps.reduce((a, x) => a + (Number(x.sup_util) || 0), 0);
  const totalC = deps.reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);

  return (
    <div className="space-y-4" data-testid="superficies-proyecto-step">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Lista todas las estancias del proyecto con su superficie útil y construida. Los sectores se definen en el paso siguiente.</p>
        <Button variant="outline" size="sm" className="rounded-sm shrink-0" onClick={addDep} data-testid="add-dependencia">
          <Plus className="mr-1.5 h-4 w-4" /> Añadir estancia
        </Button>
      </div>

      {deps.length === 0 ? (
        <p className="border border-dashed border-border py-10 text-center text-sm text-muted-foreground">Sin estancias. Añade la primera para empezar el cuadro de superficies.</p>
      ) : (
        <div className="overflow-x-auto border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-3 py-2 font-semibold">Estancia</th>
                <th className="px-3 py-2 font-semibold">Etiqueta</th>
                <th className="px-3 py-2 font-semibold">Planta</th>
                <th className="px-3 py-2 text-right font-semibold">S. útil (m²)</th>
                <th className="px-3 py-2 text-right font-semibold">S. construida (m²)</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {deps.map((x, i) => (
                <tr key={x.id} className="border-b border-border last:border-0" data-testid={`dep-row-${i}`}>
                  <td className="px-3 py-1.5"><Input className="h-8 rounded-sm" value={x.nombre || ""} onChange={(e) => updateDep(x.id, { nombre: e.target.value })} placeholder="Nombre" data-testid={`dep-${i}-nombre`} /></td>
                  <td className="px-3 py-1.5"><Input className="h-8 w-32 rounded-sm" value={x.etiqueta || ""} onChange={(e) => updateDep(x.id, { etiqueta: e.target.value })} placeholder="Ref./EN" data-testid={`dep-${i}-etiqueta`} /></td>
                  <td className="px-3 py-1.5"><Input className="h-8 w-20 rounded-sm" value={x.planta || ""} onChange={(e) => updateDep(x.id, { planta: e.target.value })} data-testid={`dep-${i}-planta`} /></td>
                  <td className="px-3 py-1.5"><NumberInput min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.sup_util ?? ""} onChange={(v) => updateDep(x.id, { sup_util: v })} data-testid={`dep-${i}-util`} /></td>
                  <td className="px-3 py-1.5"><NumberInput min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.sup_construida ?? ""} onChange={(v) => updateDep(x.id, { sup_construida: v })} data-testid={`dep-${i}-construida`} /></td>
                  <td className="px-3 py-1.5"><Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeDep(x.id)} data-testid={`remove-dep-${i}`}><Trash2 className="h-4 w-4" /></Button></td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-border bg-secondary/30 font-mono text-sm font-semibold">
                <td className="px-3 py-2 font-sans" colSpan={3}>TOTAL ({deps.length} estancias)</td>
                <td className="px-3 py-2 text-right" data-testid="total-util">{num(totalU, 2)}</td>
                <td className="px-3 py-2 text-right" data-testid="total-construida">{num(totalC, 2)}</td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
