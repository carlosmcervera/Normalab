import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Loader2, Calculator, Save, FileText, Check } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DynamicField } from "@/features/studies/components/DynamicField";
import { ResultsPanel } from "@/features/studies/components/ResultsPanel";
import { ActivityCombobox } from "@/features/studies/components/ActivityCombobox";
import { ConfigSelector } from "@/features/studies/components/ConfigSelector";
import { SuperficiesStep } from "@/features/studies/components/SuperficiesStep";
import { OcupacionStep } from "@/features/studies/components/OcupacionStep";
import { CargaFuegoStep } from "@/features/studies/components/CargaFuegoStep";
import { EvacuacionStep } from "@/features/studies/components/EvacuacionStep";
import { DbsiOcupacionStep } from "@/features/studies/components/DbsiOcupacionStep";
import { DbsiResultsPanel } from "@/features/studies/components/DbsiResultsPanel";

const EMPTY = { establecimiento: { config: "C" }, sectores: [], dependencias: [] };

export default function StudyWizardPage() {
  const { studyId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState(0);
  const [data, setData] = useState(null);
  const [results, setResults] = useState(null);

  const { data: study } = useQuery({ queryKey: ["study", studyId], queryFn: () => api.get(`/studies/${studyId}`).then((r) => r.data) });
  const schemaQ = useQuery({
    queryKey: ["schema", study?.module_code],
    enabled: !!study?.module_code,
    queryFn: () => api.get(`/modules/${study.module_code}/schema`).then((r) => r.data),
  });

  useEffect(() => {
    if (study && data === null) {
      const d = study.data || {};
      setData({ ...EMPTY, ...d, establecimiento: { ...EMPTY.establecimiento, ...(d.establecimiento || {}) } });
      if (study.results) setResults(study.results);
    }
  }, [study, data]);

  const schema = schemaQ.data?.schema;
  const steps = useMemo(() => (schema ? [...schema.steps, { id: "resultados", title: "Resultados", synthetic: true }] : []), [schema]);
  const totalSteps = steps.length;

  const saveMut = useMutation({ mutationFn: (d) => api.put(`/studies/${studyId}`, { data: d }) });
  const computeMut = useMutation({
    mutationFn: () => api.post(`/studies/${studyId}/compute`).then((r) => r.data),
    onSuccess: (res) => { setResults(res.results); qc.invalidateQueries({ queryKey: ["study", studyId] }); toast.success("Cálculo realizado"); },
    onError: (e) => { setResults(null); toast.error(apiError(e)); },
  });
  const versionMut = useMutation({
    mutationFn: () => api.post(`/studies/${studyId}/version`, { note: null }).then((r) => r.data),
    onSuccess: (res) => { setResults(res.results); qc.invalidateQueries({ queryKey: ["study", studyId] }); toast.success(`Versión v${res.version} guardada`); },
    onError: (e) => toast.error(apiError(e)),
  });

  if (!study || !schema || data === null) {
    return <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }

  const getVal = (f) => (f.target ? (data[f.target] || {})[f.name] : data[f.name]);
  const setVal = (f, v) => setData((d) => (f.target ? { ...d, [f.target]: { ...(d[f.target] || {}), [f.name]: v } } : { ...d, [f.name]: v }));

  const goTo = async (target) => {
    await saveMut.mutateAsync(data);
    setStep(target);
    if (target === totalSteps - 1) computeMut.mutate();
    window.scrollTo(0, 0);
  };

  const current = steps[step];

  const renderField = (f) => {
    if (f.type === "activity_combobox")
      return <ActivityCombobox value={getVal(f)} onChange={(v) => setVal(f, v)} options={schema.activity_types || []} testid={`field-${f.name}`} />;
    if (f.type === "config_selector")
      return <ConfigSelector value={getVal(f)} onChange={(v) => setVal(f, v)} options={schema.config_types || []} testid={`field-${f.name}`} />;
    return <DynamicField field={f} value={getVal(f)} onChange={(v) => setVal(f, v)} testidPrefix="field" />;
  };

  const isCte = study.module_code === "CTE";

  return (
    <div className="mx-auto max-w-5xl">
      <button onClick={() => navigate(`/expedientes/${study.project_id}`)} className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground" data-testid="back-to-project">
        <ArrowLeft className="h-4 w-4" /> Volver al expediente
      </button>

      <div className="mb-2 flex items-center gap-2">
        <h1 className="font-heading text-2xl tracking-tight">{study.name}</h1>
        <Badge variant="outline" className="rounded-sm font-mono text-xs">{study.module_code}</Badge>
      </div>

      <div className="mb-8 flex items-center gap-2 overflow-x-auto" data-testid="wizard-stepper">
        {steps.map((s, i) => (
          <div key={s.id} className="flex flex-1 items-center gap-2">
            <button onClick={() => goTo(i)} data-testid={`step-${i}`}
              className={`flex items-center gap-2 whitespace-nowrap border px-3 py-2 text-sm transition-colors ${
                i === step ? "border-foreground bg-foreground text-background" : i < step ? "border-border text-foreground" : "border-border text-muted-foreground"}`}>
              <span className="flex h-5 w-5 items-center justify-center border border-current text-xs">
                {i < step ? <Check className="h-3 w-3" /> : i + 1}
              </span>
              <span className="hidden sm:inline">{s.title}</span>
            </button>
            {i < steps.length - 1 && <div className="h-px flex-1 bg-border" />}
          </div>
        ))}
      </div>

      <div className="border border-border bg-background p-6">
        <h2 className="font-heading text-xl">{current.title}</h2>
        {current.description && <p className="mt-1 text-sm text-muted-foreground">{current.description}</p>}

        <div className="mt-6">
          {current.fields && !current.type && !current.synthetic && (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              {current.fields.map((f) => {
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
          )}

          {current.type === "superficies" && <SuperficiesStep data={data} setData={setData} configTypes={schema.config_types || []} />}
          {current.type === "ocupacion" && <OcupacionStep data={data} setData={setData} densities={schema.occupancy_densities || []} />}
          {current.type === "carga_fuego" && <CargaFuegoStep data={data} setData={setData} catalog={schema.activity_catalog || []} ciTable={schema.ci_table || []} />}
          {current.type === "evacuacion" && <EvacuacionStep data={data} setData={setData} />}
          {current.type === "dbsi_ocupacion" && <DbsiOcupacionStep data={data} setData={setData} densities={schema.occupancy_densities || []} />}

          {current.synthetic && (
            <div>
              {computeMut.isPending ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
              ) : results ? (
                isCte ? <DbsiResultsPanel results={results} /> : <ResultsPanel results={results} />
              ) : (
                <div className="border border-dashed border-border py-12 text-center">
                  <p className="text-sm text-muted-foreground">Pulsa «Calcular» para ejecutar el motor de reglas.</p>
                  <Button className="mt-4 rounded-sm" onClick={() => computeMut.mutate()} data-testid="compute-button">
                    <Calculator className="mr-2 h-4 w-4" /> Calcular
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <Button variant="outline" className="rounded-sm" disabled={step === 0} onClick={() => goTo(step - 1)} data-testid="wizard-prev">
          <ArrowLeft className="mr-2 h-4 w-4" /> Anterior
        </Button>
        <div className="flex items-center gap-2">
          {current.synthetic && results && (
            <>
              <Button variant="outline" className="rounded-sm" onClick={() => computeMut.mutate()} disabled={computeMut.isPending} data-testid="recompute-button">
                <Calculator className="mr-2 h-4 w-4" /> Recalcular
              </Button>
              <Button variant="outline" className="rounded-sm" onClick={() => versionMut.mutate()} disabled={versionMut.isPending} data-testid="save-version-button">
                {versionMut.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />} Guardar versión
              </Button>
              <Button className="rounded-sm" onClick={() => navigate(`/estudios/${studyId}/informe`)} data-testid="view-report-button">
                <FileText className="mr-2 h-4 w-4" /> Ver informe
              </Button>
            </>
          )}
          {step < totalSteps - 1 && (
            <Button className="rounded-sm" onClick={() => goTo(step + 1)} disabled={saveMut.isPending} data-testid="wizard-next">
              {saveMut.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {step === totalSteps - 2 ? "Calcular resultados" : "Siguiente"} <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
