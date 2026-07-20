import { Plus, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

const COEFS = [
  { value: "ninguno", label: "Sin incremento" },
  { value: "nota4a", label: "Nota 4a · extinción automática de agua (+25%)" },
  { value: "nota4b", label: "Nota 4b · control de humos y calor (+25%)" },
  { value: "nota4c", label: "Nota 4c · planta salida, ≥2 salidas directas, h≥8 m + extinción (+100%)" },
  { value: "nota5", label: "Nota 5 · riesgo bajo nivel 1 incombustible (A1/A2 95%)" },
];

export function EvacuacionStep({ data, setData }) {
  const sectores = (data.sectores || []).filter((s) => s.tipo !== "area_exterior");

  const updateSector = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));

  const addRecorrido = (sec) =>
    updateSector(sec.id, { recorridos: [...(sec.recorridos || []), { id: genId(), origen: "", tipo: "hasta_salida", distancia_real: "" }] });
  const updateRecorrido = (sec, rid, patch) =>
    updateSector(sec.id, { recorridos: (sec.recorridos || []).map((r) => (r.id === rid ? { ...r, ...patch } : r)) });
  const removeRecorrido = (sec, rid) =>
    updateSector(sec.id, { recorridos: (sec.recorridos || []).filter((r) => r.id !== rid) });

  if (sectores.length === 0)
    return <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground" data-testid="evac-empty">Primero crea sectores de incendio.</p>;

  return (
    <div className="space-y-6" data-testid="evacuacion-step">
      {sectores.map((s, si) => (
        <div key={s.id} className="border border-border" data-testid={`evac-sector-${si}`}>
          <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2.5">
            <span className="font-heading text-sm">{s.nombre}</span>
            <Badge variant="outline" className="rounded-sm text-xs">{s.num_salidas >= 2 ? "2 o más salidas" : "Una salida"}</Badge>
          </div>
          <div className="space-y-4 p-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Coeficiente de incremento (notas 4/5)</Label>
                <Select value={s.evac_coeficiente || "ninguno"} onValueChange={(v) => updateSector(s.id, { evac_coeficiente: v })}>
                  <SelectTrigger className="rounded-sm" data-testid={`evac-${si}-coef`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {COEFS.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Los coeficientes no son acumulativos (solo se aplica uno). La nota 5 solo aplica a riesgo bajo nivel 1.</p>
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <Label>Recorridos de evacuación (por origen)</Label>
                <Button variant="outline" size="sm" className="rounded-sm" onClick={() => addRecorrido(s)} data-testid={`evac-${si}-add`}>
                  <Plus className="mr-1.5 h-4 w-4" /> Añadir recorrido
                </Button>
              </div>
              {(s.recorridos || []).length === 0 ? (
                <p className="border border-dashed border-border py-4 text-center text-xs text-muted-foreground">Sin recorridos. Añade los orígenes de evacuación y su distancia real medida.</p>
              ) : (
                <div className="overflow-x-auto border border-border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                        <th className="px-3 py-2 font-semibold">Origen</th>
                        <th className="px-3 py-2 font-semibold">Tipo de recorrido</th>
                        <th className="px-3 py-2 text-right font-semibold">Distancia real (m)</th>
                        <th className="px-3 py-2" />
                      </tr>
                    </thead>
                    <tbody>
                      {(s.recorridos || []).map((r, ri) => (
                        <tr key={r.id} className="border-b border-border last:border-0" data-testid={`evac-${si}-rec-${ri}`}>
                          <td className="px-3 py-1.5">
                            <Input className="h-8 rounded-sm" value={r.origen || ""} onChange={(e) => updateRecorrido(s, r.id, { origen: e.target.value })} placeholder="p. ej. Fondo de nave" data-testid={`evac-${si}-rec-${ri}-origen`} />
                          </td>
                          <td className="px-3 py-1.5">
                            <Select value={r.tipo || "hasta_salida"} onValueChange={(v) => updateRecorrido(s, r.id, { tipo: v })}>
                              <SelectTrigger className="h-8 w-52 rounded-sm" data-testid={`evac-${si}-rec-${ri}-tipo`}><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="hasta_salida">Hasta la salida más próxima</SelectItem>
                                <SelectItem value="sin_alternativa">Recorrido sin alternativa</SelectItem>
                              </SelectContent>
                            </Select>
                          </td>
                          <td className="px-3 py-1.5">
                            <Input type="number" min={0} step={0.5} className="h-8 w-24 rounded-sm text-right font-mono" value={r.distancia_real ?? ""} onChange={(e) => updateRecorrido(s, r.id, { distancia_real: e.target.value === "" ? "" : Number(e.target.value) })} data-testid={`evac-${si}-rec-${ri}-dist`} />
                          </td>
                          <td className="px-3 py-1.5">
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeRecorrido(s, r.id)} data-testid={`evac-${si}-rec-${ri}-remove`}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
