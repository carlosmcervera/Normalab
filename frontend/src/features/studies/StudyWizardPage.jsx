import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Loader2, Calculator, Save, FileText, Check } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StepBody } from "@/features/studies/components/StepBody";
import { AmbitosManager } from "@/features/studies/components/AmbitosManager";
import { IncendiosResultsPanel } from "@/features/studies/components/IncendiosResultsPanel";
import { ResultsPanel } from "@/features/studies/components/ResultsPanel";

const defaultData = (code) => (code === "INCENDIOS" ? { ambitos: [] } : { establecimiento: { config: "C" }, sectores: [], dependencias: [] });

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
      setData({ ...defaultData(study.module_code), ...(study.data || {}) });
      if (study.results) setResults(study.results);
    }
  }, [study, data]);

  const schema = schemaQ.data?.schema;
  const isIncendios = study?.module_code === "INCENDIOS";

  const steps = useMemo(() => {
    if (!schema) return [];
    if (isIncendios) {
      const ambitos = data?.ambitos || [];
      return [
        { id: "ambitos", type: "ambitos", title: "Ámbitos del proyecto", description: "Define los ámbitos: establecimientos industriales (RSCIEI) y/o edificación (CTE DB-SI)." },
        ...ambitos.map((a, i) => ({ id: a.id, title: a.nombre || `Ámbito ${i + 1}`, ambitoIndex: i })),
        { id: "resultados", synthetic: true, title: "Resultados" },
      ];
    }
    return [...schema.steps, { id: "resultados", synthetic: true, title: "Resultados" }];
  }, [schema, data?.ambitos, isIncendios]);
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

  const goTo = async (target) => {
    await saveMut.mutateAsync(data);
    setStep(Math.max(0, Math.min(target, totalSteps - 1)));
    if (target === totalSteps - 1) computeMut.mutate();
    window.scrollTo(0, 0);
  };

  const current = steps[step] || steps[0];

  const renderAmbito = () => {
    const a = data.ambitos[current.ambitoIndex];
    if (!a) return null;
    const subSchema = a.tipo === "industrial" ? schema.rsciei : schema.dbsi;
    const setAmbito = (fn) => setData((d) => {
      const arr = [...d.ambitos];
      arr[current.ambitoIndex] = typeof fn === "function" ? fn(arr[current.ambitoIndex]) : fn;
      return { ...d, ambitos: arr };
    });
    return (
      <div className="space-y-8" data-testid={`ambito-editor-${current.ambitoIndex}`}>
        <Badge variant="outline" className="rounded-sm">{a.tipo === "industrial" ? "Establecimiento industrial · RSCIEI" : "Edificación · CTE DB-SI"}</Badge>
        {subSchema.steps.map((sub) => (
          <div key={sub.id} className="border-t border-border pt-6 first:border-t-0 first:pt-0">
            <h3 className="font-heading text-base">{sub.title}</h3>
            {sub.description && <p className="mb-4 mt-0.5 text-sm text-muted-foreground">{sub.description}</p>}
            <StepBody step={sub} schema={subSchema} data={a} setData={setAmbito} />
          </div>
        ))}
      </div>
    );
  };

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
          {current.type === "ambitos" && <AmbitosManager data={data} setData={setData} />}
          {current.ambitoIndex !== undefined && renderAmbito()}
          {!isIncendios && !current.synthetic && <StepBody step={current} schema={schema} data={data} setData={setData} />}

          {current.synthetic && (
            <div>
              {computeMut.isPending ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
              ) : results ? (
                isIncendios ? <IncendiosResultsPanel results={results} /> : <ResultsPanel results={results} />
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
