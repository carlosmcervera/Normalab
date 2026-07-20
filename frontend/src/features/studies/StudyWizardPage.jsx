import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Loader2, Plus, Trash2, Calculator, Save, FileText, Check } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { DynamicField } from "@/features/studies/components/DynamicField";
import { ResultsPanel } from "@/features/studies/components/ResultsPanel";

function visible(field, item) {
  if (!field.show_if) return true;
  return Object.entries(field.show_if).every(([k, v]) => item[k] === v);
}

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
      setData({ zonas: [], ...study.data });
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
    onError: (e) => toast.error(apiError(e)),
  });
  const versionMut = useMutation({
    mutationFn: () => api.post(`/studies/${studyId}/version`, { note: null }).then((r) => r.data),
    onSuccess: (res) => { setResults(res.results); qc.invalidateQueries({ queryKey: ["study", studyId] }); toast.success(`Versión v${res.version} guardada`); },
    onError: (e) => toast.error(apiError(e)),
  });

  if (!study || !schema || data === null) {
    return <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }

  const setField = (name, value) => setData((d) => ({ ...d, [name]: value }));

  const setZona = (idx, name, value) =>
    setData((d) => ({ ...d, zonas: d.zonas.map((z, i) => (i === idx ? { ...z, [name]: value } : z)) }));
  const addZona = () => setData((d) => ({ ...d, zonas: [...(d.zonas || []), { modo: "produccion", ci: 1.0 }] }));
  const removeZona = (idx) => setData((d) => ({ ...d, zonas: d.zonas.filter((_, i) => i !== idx) }));
  const applyPreset = (idx, preset) =>
    setData((d) => ({ ...d, zonas: d.zonas.map((z, i) => (i === idx ? {
      ...z, descripcion: preset.label, modo: preset.modo, ci: preset.ci,
      ...(preset.modo === "produccion" ? { qsi: preset.qsi } : { qvi: preset.qvi }),
    } : z)) }));

  const goTo = async (target) => {
    await saveMut.mutateAsync(data);
    setStep(target);
    if (target === totalSteps - 1 && !results) computeMut.mutate();
    window.scrollTo(0, 0);
  };

  const current = steps[step];
  const presets = schema.presets || [];

  return (
    <div className="mx-auto max-w-4xl">
      <button onClick={() => navigate(`/expedientes/${study.project_id}`)} className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground" data-testid="back-to-project">
        <ArrowLeft className="h-4 w-4" /> Volver al expediente
      </button>

      <div className="mb-2 flex items-center gap-2">
        <h1 className="font-heading text-2xl tracking-tight">{study.name}</h1>
        <Badge variant="outline" className="rounded-sm font-mono text-xs">{study.module_code}</Badge>
      </div>

      {/* Stepper */}
      <div className="mb-8 flex items-center gap-2" data-testid="wizard-stepper">
        {steps.map((s, i) => (
          <div key={s.id} className="flex flex-1 items-center gap-2">
            <button
              onClick={() => goTo(i)}
              data-testid={`step-${i}`}
              className={`flex items-center gap-2 border px-3 py-2 text-sm transition-colors ${
                i === step ? "border-foreground bg-foreground text-background" : i < step ? "border-border text-foreground" : "border-border text-muted-foreground"
              }`}
            >
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
          {/* Regular fields step */}
          {!current.synthetic && current.type !== "repeater" && (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              {current.fields.map((f) => (
                <div key={f.name} className={f.type === "boolean" ? "sm:col-span-2" : ""}>
                  <DynamicField field={f} value={data[f.name]} onChange={(v) => setField(f.name, v)} testidPrefix="field" />
                </div>
              ))}
            </div>
          )}

          {/* Repeater step */}
          {current.type === "repeater" && (
            <div className="space-y-4">
              {(data.zonas || []).length === 0 && (
                <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground">
                  No hay zonas. Añade la primera zona del sector.
                </p>
              )}
              {(data.zonas || []).map((z, idx) => (
                <div key={idx} className="border border-border p-4" data-testid={`zona-${idx}`}>
                  <div className="mb-3 flex items-center justify-between">
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{current.item_label} {idx + 1}</p>
                    <div className="flex items-center gap-2">
                      {presets.length > 0 && (
                        <Select onValueChange={(val) => applyPreset(idx, presets[Number(val)])}>
                          <SelectTrigger className="h-8 w-48 rounded-sm text-xs" data-testid={`preset-${idx}`}><SelectValue placeholder="Cargar preset…" /></SelectTrigger>
                          <SelectContent>
                            {presets.map((p, pi) => <SelectItem key={pi} value={String(pi)}>{p.label}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      )}
                      <Button variant="ghost" size="icon" className="h-8 w-8 rounded-sm text-muted-foreground hover:text-destructive" onClick={() => removeZona(idx)} data-testid={`remove-zona-${idx}`}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
                    {current.fields.filter((f) => visible(f, z)).map((f) => (
                      <DynamicField key={f.name} field={f} value={z[f.name]} onChange={(v) => setZona(idx, f.name, v)} testidPrefix={`zona-${idx}`} />
                    ))}
                  </div>
                </div>
              ))}
              <Button variant="outline" className="rounded-sm" onClick={addZona} data-testid="add-zona">
                <Plus className="mr-2 h-4 w-4" /> Añadir zona
              </Button>
            </div>
          )}

          {/* Results step */}
          {current.synthetic && (
            <div>
              {computeMut.isPending ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
              ) : results ? (
                <ResultsPanel results={results} />
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

      {/* Footer nav */}
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
