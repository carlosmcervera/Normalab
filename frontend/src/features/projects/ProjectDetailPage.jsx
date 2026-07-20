import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { Plus, Loader2, FileText, ArrowLeft, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { formatDate, STATE_META } from "@/lib/format";
import { PageHeader } from "@/components/PageHeader";
import { ModuleIcon } from "@/components/ModuleIcon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [studyName, setStudyName] = useState("");
  const [moduleCode, setModuleCode] = useState("");

  const { data: project } = useQuery({ queryKey: ["project", projectId], queryFn: () => api.get(`/projects/${projectId}`).then((r) => r.data) });
  const { data: modules = [] } = useQuery({ queryKey: ["modules"], queryFn: () => api.get("/modules").then((r) => r.data) });
  const { data: studies = [], isLoading } = useQuery({ queryKey: ["studies", projectId], queryFn: () => api.get(`/studies?project_id=${projectId}`).then((r) => r.data) });

  const operativos = modules.filter((m) => m.status === "operativo");

  const createStudy = useMutation({
    mutationFn: (payload) => api.post("/studies", payload).then((r) => r.data),
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ["studies", projectId] });
      setOpen(false);
      setStudyName(""); setModuleCode("");
      toast.success("Estudio creado");
      navigate(`/estudios/${s.id}`);
    },
    onError: (e) => toast.error(apiError(e)),
  });

  const deleteStudy = useMutation({
    mutationFn: (id) => api.delete(`/studies/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["studies", projectId] }); toast.success("Estudio eliminado"); },
    onError: (e) => toast.error(apiError(e)),
  });

  const submit = (e) => {
    e.preventDefault();
    if (!moduleCode || !studyName) return toast.error("Selecciona módulo y nombre");
    createStudy.mutate({ project_id: projectId, module_code: moduleCode, name: studyName });
  };

  return (
    <div>
      <button onClick={() => navigate("/expedientes")} className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground" data-testid="back-to-projects">
        <ArrowLeft className="h-4 w-4" /> Expedientes
      </button>
      <PageHeader
        label={project?.code}
        title={project?.name || "Expediente"}
        description={[project?.client, project?.location].filter(Boolean).join(" · ")}
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-sm" data-testid="new-study-button">
                <Plus className="mr-2 h-4 w-4" /> Nuevo estudio
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-sm">
              <DialogHeader>
                <DialogTitle className="font-heading">Nuevo estudio normativo</DialogTitle>
                <DialogDescription>Selecciona la normativa y asigna un nombre al estudio.</DialogDescription>
              </DialogHeader>
              <form onSubmit={submit} className="space-y-4" data-testid="study-form">
                <div className="space-y-1.5">
                  <Label>Normativa *</Label>
                  <Select value={moduleCode} onValueChange={setModuleCode}>
                    <SelectTrigger data-testid="study-module-select" className="rounded-sm"><SelectValue placeholder="Selecciona un módulo operativo" /></SelectTrigger>
                    <SelectContent>
                      {operativos.map((m) => (
                        <SelectItem key={m.code} value={m.code} data-testid={`module-option-${m.code}`}>{m.short_name} — {m.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Nombre del estudio *</Label>
                  <Input data-testid="study-name" value={studyName} onChange={(e) => setStudyName(e.target.value)} placeholder="Ej. Sector de incendio nave A" />
                </div>
                <DialogFooter>
                  <Button type="submit" className="rounded-sm" disabled={createStudy.isPending} data-testid="submit-study">
                    {createStudy.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Crear y abrir asistente
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <h2 className="mb-4 font-heading text-xl">Estudios</h2>
      {isLoading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : studies.length === 0 ? (
        <div className="flex flex-col items-center border border-dashed border-border py-16 text-center" data-testid="studies-empty">
          <FileText className="h-10 w-10 text-muted-foreground" />
          <p className="mt-4 font-heading text-lg">Sin estudios todavía</p>
          <p className="mt-1 text-sm text-muted-foreground">Crea un estudio seleccionando un módulo normativo operativo.</p>
        </div>
      ) : (
        <div className="border border-border bg-background">
          {studies.map((s, i) => {
            const state = STATE_META[s.results?.estado_global];
            const mod = modules.find((m) => m.code === s.module_code);
            return (
              <div key={s.id} data-testid={`study-row-${s.id}`} className={`flex flex-col gap-4 p-5 sm:flex-row sm:items-center ${i > 0 ? "border-t border-border" : ""}`}>
                <ModuleIcon icon={mod?.icon} accent={mod?.accent} />
                <div className="flex-1 cursor-pointer" onClick={() => navigate(`/estudios/${s.id}`)}>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">{s.name}</p>
                    <Badge variant="outline" className="rounded-sm font-mono text-xs">{s.module_name}</Badge>
                    {s.current_version > 0 && <Badge variant="secondary" className="rounded-sm text-xs">v{s.current_version}</Badge>}
                    {state && <span className={`rounded-sm border px-2 py-0.5 text-xs font-medium ${state.cls}`}>{state.label}</span>}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">Actualizado {formatDate(s.updated_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" className="rounded-sm" onClick={() => navigate(`/estudios/${s.id}`)} data-testid={`open-study-${s.id}`}>Abrir</Button>
                  {s.status === "calculado" && (
                    <Button variant="outline" size="sm" className="rounded-sm" onClick={() => navigate(`/estudios/${s.id}/informe`)} data-testid={`report-study-${s.id}`}>Informe</Button>
                  )}
                  <Button variant="ghost" size="icon" className="rounded-sm text-muted-foreground hover:text-destructive" onClick={() => deleteStudy.mutate(s.id)} data-testid={`delete-study-${s.id}`}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
