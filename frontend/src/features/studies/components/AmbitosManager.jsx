import { Plus, Trash2, Factory, Building2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DynamicField } from "@/features/studies/components/DynamicField";
import { ConfigSelector } from "@/features/studies/components/ConfigSelector";
import { ActivityCombobox } from "@/features/studies/components/ActivityCombobox";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

const newAmbito = (tipo, n) => tipo === "industrial"
  ? { id: genId(), tipo: "industrial", nombre: `Establecimiento industrial ${n}`, establecimiento: { config: "C" } }
  : { id: genId(), tipo: "edificacion", nombre: `Edificación ${n}`, num_plantas: 1, altura_evacuacion: 0, num_salidas: 2, bajo_rasante: false };

function AmbitoConfig({ ambito, fields, schema, onChange }) {
  const getVal = (f) => (f.target ? (ambito[f.target] || {})[f.name] : ambito[f.name]);
  const setVal = (f, v) => onChange(f.target ? { [f.target]: { ...(ambito[f.target] || {}), [f.name]: v } } : { [f.name]: v });
  return (
    <div className="grid grid-cols-1 gap-4 border-t border-border bg-secondary/20 p-4 sm:grid-cols-2">
      {fields.map((f) => {
        const custom = f.type === "config_selector" || f.type === "activity_combobox";
        const wide = f.type === "boolean" || custom || f.full;
        return (
          <div key={f.name} className={wide ? "sm:col-span-2" : ""}>
            {custom && <span className="mb-1.5 block text-sm">{f.label} {f.required && <span className="text-destructive">*</span>}</span>}
            {f.type === "activity_combobox" ? (
              <ActivityCombobox value={getVal(f)} onChange={(v) => setVal(f, v)} options={schema.activity_types || []} testid={`ambito-field-${f.name}`} />
            ) : f.type === "config_selector" ? (
              <ConfigSelector value={getVal(f)} onChange={(v) => setVal(f, v)} options={schema.config_types || []} testid={`ambito-field-${f.name}`} />
            ) : (
              <DynamicField field={f} value={getVal(f)} onChange={(v) => setVal(f, v)} testidPrefix="ambito-field" />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function AmbitosManager({ data, setData, schema = {} }) {
  const ambitos = data.ambitos || [];
  const countBy = (t) => ambitos.filter((a) => a.tipo === t).length + 1;

  const add = (tipo) => setData((d) => ({ ...d, ambitos: [...(d.ambitos || []), newAmbito(tipo, countBy(tipo))] }));
  const update = (id, patch) => setData((d) => ({ ...d, ambitos: d.ambitos.map((a) => (a.id === id ? { ...a, ...patch } : a)) }));
  const remove = (id) => setData((d) => ({
    ...d,
    ambitos: d.ambitos.filter((a) => a.id !== id),
    sectores: (d.sectores || []).filter((s) => s.ambito_id !== id),
  }));

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
        <div className="space-y-3">
          {ambitos.map((a, i) => (
            <div key={a.id} className="border border-border" data-testid={`ambito-row-${i}`}>
              <div className="flex items-center gap-3 p-3">
                <Badge variant="outline" className="rounded-sm shrink-0">
                  {a.tipo === "industrial" ? <Factory className="mr-1 h-3 w-3" /> : <Building2 className="mr-1 h-3 w-3" />}
                  {a.tipo === "industrial" ? "RSCIEI" : "DB-SI"}
                </Badge>
                <Input value={a.nombre || ""} onChange={(e) => update(a.id, { nombre: e.target.value })} className="rounded-sm" data-testid={`ambito-${i}-nombre`} />
                <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive" onClick={() => remove(a.id)} data-testid={`ambito-${i}-remove`}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              <AmbitoConfig
                ambito={a}
                schema={schema}
                fields={a.tipo === "industrial" ? (schema.industrial_config_fields || []) : (schema.edificacion_config_fields || [])}
                onChange={(patch) => update(a.id, patch)}
              />
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-muted-foreground">Configura cada ámbito y luego, en «Cuadro de superficies», asigna cada dependencia a un sector de su ámbito.</p>
    </div>
  );
}
