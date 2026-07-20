import { Plus, Trash2, Factory, Building2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

const newAmbito = (tipo, n) => tipo === "industrial"
  ? { id: genId(), tipo: "industrial", nombre: `Establecimiento industrial ${n}`, establecimiento: { config: "C" }, sectores: [], dependencias: [] }
  : { id: genId(), tipo: "edificacion", nombre: `Edificación ${n}`, uso: "", superficie_construida: "", altura_evacuacion: 0, num_salidas: 2, recorrido_max_real: "", bajo_rasante: false, dependencias: [] };

export function AmbitosManager({ data, setData }) {
  const ambitos = data.ambitos || [];
  const countBy = (t) => ambitos.filter((a) => a.tipo === t).length + 1;

  const add = (tipo) => setData((d) => ({ ...d, ambitos: [...(d.ambitos || []), newAmbito(tipo, countBy(tipo))] }));
  const update = (id, patch) => setData((d) => ({ ...d, ambitos: d.ambitos.map((a) => (a.id === id ? { ...a, ...patch } : a)) }));
  const remove = (id) => setData((d) => ({ ...d, ambitos: d.ambitos.filter((a) => a.id !== id) }));

  return (
    <div className="space-y-4" data-testid="ambitos-manager">
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" className="rounded-sm" onClick={() => add("industrial")} data-testid="add-ambito-industrial">
          <Factory className="mr-2 h-4 w-4" /> Añadir establecimiento industrial (RSCIEI)
        </Button>
        <Button variant="outline" className="rounded-sm" onClick={() => add("edificacion")} data-testid="add-ambito-edificacion">
          <Building2 className="mr-2 h-4 w-4" /> Añadir edificación (CTE DB-SI)
        </Button>
      </div>

      {ambitos.length === 0 ? (
        <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground">
          Sin ámbitos. Un proyecto puede combinar establecimientos industriales (RSCIEI) y zonas de edificación (CTE DB-SI).
        </p>
      ) : (
        <div className="space-y-2">
          {ambitos.map((a, i) => (
            <div key={a.id} className="flex items-center gap-3 border border-border p-3" data-testid={`ambito-row-${i}`}>
              <Badge variant="outline" className="rounded-sm shrink-0">
                {a.tipo === "industrial" ? <Factory className="mr-1 h-3 w-3" /> : <Building2 className="mr-1 h-3 w-3" />}
                {a.tipo === "industrial" ? "RSCIEI" : "DB-SI"}
              </Badge>
              <Input value={a.nombre || ""} onChange={(e) => update(a.id, { nombre: e.target.value })} className="rounded-sm" data-testid={`ambito-${i}-nombre`} />
              <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive" onClick={() => remove(a.id)} data-testid={`ambito-${i}-remove`}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-muted-foreground">Cada ámbito tiene su propio asistente y cálculo. Avanza con «Siguiente» para configurar cada ámbito.</p>
    </div>
  );
}
