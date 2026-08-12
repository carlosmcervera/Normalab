import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Loader2, Calculator, Save, FileText, FileDown, Check } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StepBody } from "@/features/studies/components/StepBody";
import { isSurfacesOutdated, SurfacesOutdatedBanner } from "@/features/studies/components/SurfacesAlert";
import { IncendiosResultsPanel } from "@/features/studies/components/IncendiosResultsPanel";
import { ResultsPanel } from "@/features/studies/components/ResultsPanel";
import { GenericResultsPanel } from "@/features/studies/components/GenericResultsPanel";
import { RebtResultsPanel } from "@/features/studies/components/RebtResultsPanel";
import { RebtLineaResultPanel } from "@/features/studies/components/RebtLineaResultPanel";

const defaultData = (code) => (code === "INCENDIOS" ? { establecimiento: { config: "C" }, sectores: [], dependencias: [] } : { establecimiento: { config: "C" }, sectores: [], dependencias: [] });

const migrateIncendios = (d) => {
  if (!d.ambitos || !d.ambitos.length) return d;
  if ((d.sectores && d.sectores.length) || (d.dependencias && d.dependencias.length)) {
    const { ambitos, ...rest } = d;
    return rest;
  }
  const sectores = [];
  const dependencias = [];
  d.ambitos.forEach((a) => {
    if (a.tipo === "industrial") {
      (a.sectores || []).forEach((s) => sectores.push({ ...s, ambito: "industrial" }));
      (a.dependencias || []).forEach((dep) => dependencias.push(dep));
    } else {
      const sid = `${a.id}_sec`;
      sectores.push({ id: sid, nombre: a.nombre || "Sector", tipo: "sector", ambito: "cte", uso_cte: a.uso });
      (a.dependencias || []).forEach((dep) => dependencias.push({
        id: dep.id, sector_id: sid, nombre: dep.nombre || "Zona",
        sup_util: dep.superficie, sup_construida: dep.superficie,
        densidad: dep.densidad, uso_ocupacion: dep.uso_ocupacion, sin_ocupacion: dep.sin_ocupacion,
      }));
    }
  });
  const { ambitos, ...rest } = d;
  return { ...rest, sectores, dependencias };
};

const patchTree = (board, id, patch) => {
  if (!board) return board;
  const nodos = (board.nodos || []).map((n) => {
    if (n.id === id) return { ...n, ...patch };
    if (n.kind === "puente") return { ...n, sublineas: (n.sublineas || []).map((s) => (s.id === id ? { ...s, ...patch } : s)) };
    if (n.kind === "subcuadro") return { ...n, board: patchTree(n.board, id, patch) };
    return n;
  });
  return { ...board, nodos };
};

const patchBoard = (board, boardId, patch) => {
  if (!board) return board;
  if (boardId === "__lga__") return { ...board, lga: { ...(board.lga || {}), ...patch } };
  if (boardId === "__root__") return { ...board, ...patch };
  const nodos = (board.nodos || []).map((n) => {
    if (n.kind === "subcuadro") {
      if (n.id === boardId) return { ...n, board: { ...(n.board || {}), ...patch } };
      return { ...n, board: patchBoard(n.board, boardId, patch) };
    }
    return n;
  });
  return { ...board, nodos };
};

export default function StudyWizardPage() {
  const { studyId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState(0);
  const [data, setData] = useState(null);
  const [results, setResults] = useState(null);
  const [genProy, setGenProy] = useState(false);
  const generarProyecto = async () => {
    setGenProy(true);
    try {
      const res = await api.get(`/studies/${studyId}/export/proyecto-docx`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url; a.download = "proyecto_baja_tension.docx";
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(apiError(e) || "No se ha podido generar el proyecto.");
    } finally {
      setGenProy(false);
    }
  };

  const { data: study } = useQuery({ queryKey: ["study", studyId], queryFn: () => api.get(`/studies/${studyId}`).then((r) => r.data) });
  const { data: project } = useQuery({ queryKey: ["project", study?.project_id], enabled: !!study?.project_id, queryFn: () => api.get(`/projects/${study.project_id}`).then((r) => r.data) });
  const schemaQ = useQuery({
    queryKey: ["schema", study?.module_code],
    enabled: !!study?.module_code,
    queryFn: () => api.get(`/modules/${study.module_code}/schema`).then((r) => r.data),
  });

  useEffect(() => {
    if (study && data === null) {
      const merged = { ...defaultData(study.module_code), ...(study.data || {}) };
      setData(study.module_code === "INCENDIOS" ? migrateIncendios(merged) : merged);
      if (study.results) setResults(study.results);
    }
  }, [study, data]);

  const schema = schemaQ.data?.schema;
  const isIncendios = study?.module_code === "INCENDIOS";

  useEffect(() => {
    if (!schema || data === null || isIncendios) return;
    const defs = {};
    (schema.steps || []).forEach((st) => (st.fields || []).forEach((f) => {
      if (f.default !== undefined && data[f.name] === undefined) defs[f.name] = f.default;
    }));
    if (Object.keys(defs).length) setData((d) => ({ ...d, ...defs }));
  }, [schema]); // eslint-disable-line react-hooks/exhaustive-deps

  const steps = useMemo(() => {
    if (!schema) return [];
    return [...(schema.steps || []), { id: "resultados", synthetic: true, title: "Resultados" }];
  }, [schema]);
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
    if (target > step) {
      const invalid = document.querySelectorAll('[data-invalid="true"]');
      if (invalid.length) {
        toast.error("Corrige los valores marcados en rojo antes de continuar.");
        return;
      }
    }
    try {
      await saveMut.mutateAsync(data);
    } catch (e) {
      toast.error(apiError(e) || "No se ha podido guardar. Revisa tu conexión e inténtalo de nuevo.");
      return;
    }
    setStep(Math.max(0, Math.min(target, totalSteps - 1)));
    if (target === totalSteps - 1) computeMut.mutate();
    window.scrollTo(0, 0);
  };

  const current = steps[step] || steps[0];

  const updateRebtNode = (id, patch) => setData((d) => ({ ...d, cuadro: patchTree(d.cuadro, id, patch) }));
  const updateRebtBoard = (boardId, patch) => setData((d) => ({ ...d, cuadro: patchBoard(d.cuadro, boardId, patch) }));
  const recomputeRebt = async () => {
    try {
      await saveMut.mutateAsync(data);
      computeMut.mutate();
    } catch (e) {
      toast.error(apiError(e) || "No se ha podido guardar antes de recalcular.");
    }
  };
  const clearRebtOverrides = (board) => {
    if (!board) return board;
    const { seccion_manual, iga_manual, ...b } = board;
    b.nodos = (b.nodos || []).map((n) => {
      if (n.kind === "subcuadro") return { ...n, board: clearRebtOverrides(n.board) };
      const { seccion_manual: sm, magneto_manual: mm, ...node } = n;
      if (n.kind === "puente") node.sublineas = (n.sublineas || []).map((s) => { const { seccion_manual: s2, magneto_manual: m2, ...ss } = s; return ss; });
      return node;
    });
    return b;
  };
  const autoDimensionarRebt = async (enable) => {
    const next = enable
      ? { ...data, auto_cumplimiento: true, cuadro: clearRebtOverrides(data.cuadro) }
      : { ...data, auto_cumplimiento: false };
    setData(next);
    try {
      await saveMut.mutateAsync(next);
      computeMut.mutate();
      if (enable) toast.success("Dimensionado automático (REBT 100%) aplicado.");
    } catch (e) {
      toast.error(apiError(e) || "No se ha podido aplicar el dimensionado automático.");
    }
  };

  return (
    <div className="mx-auto max-w-7xl">
      <button onClick={() => navigate(`/expedientes/${study.project_id}`)} className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground" data-testid="back-to-project">
        <ArrowLeft className="h-4 w-4" /> Volver al expediente
      </button>

      <div className="mb-2 flex items-center gap-2">
        <h1 className="font-heading text-2xl tracking-tight">{study.name}</h1>
        <Badge variant="outline" className="rounded-sm font-mono text-xs">{study.module_code}</Badge>
      </div>

      {isSurfacesOutdated(study, project) && (
        <div className="mb-4"><SurfacesOutdatedBanner pending={computeMut.isPending} onRecompute={() => computeMut.mutate()} /></div>
      )}

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
          {!current.synthetic && <StepBody step={current} schema={schema} data={data} setData={setData} study={study} />}

          {current.synthetic && (
            <div>
              {computeMut.isPending ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
              ) : results ? (
                results?.arbol ? <RebtResultsPanel results={results} editable data={data} onUpdateNode={updateRebtNode} onUpdateBoard={updateRebtBoard} onRecompute={recomputeRebt} onAutoDimensionar={autoDimensionarRebt} autoOn={!!data.auto_cumplimiento} recomputing={computeMut.isPending || saveMut.isPending} />
                  : results?.linea_unica ? <RebtLineaResultPanel results={results} data={data} setData={setData} onRecompute={recomputeRebt} recomputing={computeMut.isPending || saveMut.isPending} />
                  : results?.sectores ? <ResultsPanel results={results} />
                    : results?.ambitos ? <IncendiosResultsPanel results={results} />
                      : <GenericResultsPanel results={results} />
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
              {results?.arbol && (
                <Button className="rounded-sm" onClick={generarProyecto} disabled={genProy} data-testid="generate-project-button">
                  {genProy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileDown className="mr-2 h-4 w-4" />} Generar proyecto
                </Button>
              )}
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
