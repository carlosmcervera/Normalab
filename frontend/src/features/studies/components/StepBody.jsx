import { DynamicField } from "@/features/studies/components/DynamicField";
import { ActivityCombobox } from "@/features/studies/components/ActivityCombobox";
import { ConfigSelector } from "@/features/studies/components/ConfigSelector";
import { SuperficiesStep } from "@/features/studies/components/SuperficiesStep";
import { OcupacionStep } from "@/features/studies/components/OcupacionStep";
import { CargaFuegoStep } from "@/features/studies/components/CargaFuegoStep";
import { EvacuacionStep } from "@/features/studies/components/EvacuacionStep";
import { DbsiOcupacionStep } from "@/features/studies/components/DbsiOcupacionStep";
import { AmbitosManager } from "@/features/studies/components/AmbitosManager";
import { ProyectoSuperficiesStep } from "@/features/studies/components/ProyectoSuperficiesStep";
import { SectoresStep } from "@/features/studies/components/SectoresStep";

// Renders a single wizard sub-step given its (sub-)schema, scoped data and setData.
export function StepBody({ step, schema, data, setData }) {
  const getVal = (f) => (f.target ? (data[f.target] || {})[f.name] : data[f.name]);
  const setVal = (f, v) => setData((d) => (f.target ? { ...d, [f.target]: { ...(d[f.target] || {}), [f.name]: v } } : { ...d, [f.name]: v }));

  const renderField = (f) => {
    if (f.type === "activity_combobox")
      return <ActivityCombobox value={getVal(f)} onChange={(v) => setVal(f, v)} options={schema.activity_types || []} testid={`field-${f.name}`} />;
    if (f.type === "config_selector")
      return <ConfigSelector value={getVal(f)} onChange={(v) => setVal(f, v)} options={schema.config_types || []} testid={`field-${f.name}`} />;
    return <DynamicField field={f} value={getVal(f)} onChange={(v) => setVal(f, v)} testidPrefix="field" />;
  };

  if (step.fields && !step.type) {
    return (
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {step.fields.map((f) => {
          const custom = f.type === "config_selector" || f.type === "activity_combobox";
          const wide = f.type === "boolean" || custom || f.full;
          return (
            <div key={f.name} className={wide ? "sm:col-span-2" : ""}>
              {custom && <span className="mb-1.5 block text-sm">{f.label} {f.required && <span className="text-destructive">*</span>}</span>}
              {renderField(f)}
            </div>
          );
        })}
      </div>
    );
  }

  if (step.type === "superficies") return <SuperficiesStep data={data} setData={setData} configTypes={schema.config_types || []} />;
  if (step.type === "superficies_proyecto") return <ProyectoSuperficiesStep data={data} setData={setData} schema={schema} />;
  if (step.type === "sectores_incendio") return <SectoresStep data={data} setData={setData} schema={schema} />;
  if (step.type === "ambitos") return <AmbitosManager data={data} setData={setData} schema={schema} />;
  if (step.type === "ocupacion") return <OcupacionStep data={data} setData={setData} densities={schema.occupancy_densities || []} />;
  if (step.type === "carga_fuego") return <CargaFuegoStep data={data} setData={setData} catalog={schema.activity_catalog || []} ciTable={schema.ci_table || []} />;
  if (step.type === "evacuacion") return <EvacuacionStep data={data} setData={setData} />;
  if (step.type === "dbsi_ocupacion") return <DbsiOcupacionStep data={data} setData={setData} densities={schema.occupancy_densities || []} />;
  return null;
}
