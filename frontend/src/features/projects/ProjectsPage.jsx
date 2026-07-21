import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Plus, FolderKanban, Loader2, Search, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function ProjectsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({ code: "", name: "", client: "", location: "", description: "" });

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
  });

  const createMut = useMutation({
    mutationFn: (payload) => api.post("/projects", payload).then((r) => r.data),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
      setForm({ code: "", name: "", client: "", location: "", description: "" });
      toast.success("Expediente creado");
      navigate(`/expedientes/${p.id}`);
    },
    onError: (e) => toast.error(apiError(e)),
  });

  const deleteMut = useMutation({
    mutationFn: (id) => api.delete(`/projects/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Expediente eliminado");
    },
    onError: (e) => toast.error(apiError(e)),
  });

  const submit = (e) => {
    e.preventDefault();
    if (!form.code || !form.name) return toast.error("Código y nombre son obligatorios");
    createMut.mutate(form);
  };

  const q = query.trim().toLowerCase();
  const filtered = q
    ? projects.filter((p) => [p.code, p.name, p.client, p.location].some((v) => (v || "").toLowerCase().includes(q)))
    : projects;

  return (
    <div>
      <PageHeader
        label="Proyectos"
        title="Expedientes"
        description="Cada expediente agrupa los estudios normativos de un proyecto o cliente."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-sm" data-testid="new-project-button">
                <Plus className="mr-2 h-4 w-4" /> Nuevo expediente
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-sm">
              <DialogHeader>
                <DialogTitle className="font-heading">Nuevo expediente</DialogTitle>
                <DialogDescription>Crea un expediente para agrupar sus estudios normativos.</DialogDescription>
              </DialogHeader>
              <form onSubmit={submit} className="space-y-4" data-testid="project-form">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>Código *</Label>
                    <Input data-testid="project-code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="EXP-2026-001" />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Cliente</Label>
                    <Input data-testid="project-client" value={form.client} onChange={(e) => setForm({ ...form, client: e.target.value })} placeholder="Cliente" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Nombre *</Label>
                  <Input data-testid="project-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Nave industrial en Pol. Ind. ..." />
                </div>
                <div className="space-y-1.5">
                  <Label>Emplazamiento</Label>
                  <Input data-testid="project-location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Municipio, provincia" />
                </div>
                <div className="space-y-1.5">
                  <Label>Descripción</Label>
                  <Textarea data-testid="project-description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
                </div>
                <DialogFooter>
                  <Button type="submit" className="rounded-sm" disabled={createMut.isPending} data-testid="submit-project">
                    {createMut.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Crear expediente
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      {!isLoading && projects.length > 0 && (
        <div className="relative mb-6 max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            data-testid="project-search"
            className="rounded-sm pl-9"
            placeholder="Buscar por código, nombre, cliente o emplazamiento…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center border border-dashed border-border py-20 text-center" data-testid="projects-empty">
          <FolderKanban className="h-10 w-10 text-muted-foreground" />
          <p className="mt-4 font-heading text-lg">Aún no hay expedientes</p>
          <p className="mt-1 text-sm text-muted-foreground">Crea el primer expediente para empezar a generar estudios.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center border border-dashed border-border py-16 text-center" data-testid="projects-no-results">
          <Search className="h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">Ningún expediente coincide con «{query}».</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <div
              key={p.id}
              data-testid={`project-card-${p.id}`}
              onClick={() => navigate(`/expedientes/${p.id}`)}
              className="group relative flex cursor-pointer flex-col items-start border border-border bg-background p-6 text-left transition-transform hover:-translate-y-1 hover:border-foreground"
            >
              <div className="flex w-full items-center justify-between">
                <span className="font-mono text-xs text-muted-foreground">{p.code}</span>
                <Badge variant="secondary" className="rounded-sm">{p.studies_count} estudios</Badge>
              </div>
              <h3 className="mt-3 pr-8 font-heading text-lg">{p.name}</h3>
              {p.client && <p className="mt-1 text-sm text-muted-foreground">{p.client}</p>}
              <p className="mt-4 text-xs text-muted-foreground">Actualizado {formatDate(p.updated_at)}</p>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute bottom-4 right-3 h-8 w-8 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                    onClick={(e) => e.stopPropagation()}
                    data-testid={`delete-project-${p.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="rounded-sm" onClick={(e) => e.stopPropagation()}>
                  <AlertDialogHeader>
                    <AlertDialogTitle className="font-heading">¿Eliminar expediente?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Se eliminará «{p.name}» ({p.code}) y sus {p.studies_count} estudio(s) asociados. Esta acción no se puede deshacer.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="rounded-sm" data-testid="cancel-delete-project">Cancelar</AlertDialogCancel>
                    <AlertDialogAction
                      className="rounded-sm bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      onClick={() => deleteMut.mutate(p.id)}
                      data-testid="confirm-delete-project"
                    >
                      Eliminar
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
