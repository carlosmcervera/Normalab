import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ArrowUpRight, FolderKanban, FileStack, Boxes } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/features/auth/AuthContext";
import { PageHeader } from "@/components/PageHeader";
import { ModuleIcon } from "@/components/ModuleIcon";
import { Badge } from "@/components/ui/badge";

function StatCard({ icon: Icon, label, value, testid }) {
  return (
    <div className="border border-border bg-background p-6" data-testid={testid}>
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{label}</p>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <p className="mt-4 font-heading text-4xl font-light tracking-tight">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: modules = [] } = useQuery({ queryKey: ["modules"], queryFn: () => api.get("/modules").then((r) => r.data) });
  const { data: projects = [] } = useQuery({ queryKey: ["projects"], queryFn: () => api.get("/projects").then((r) => r.data) });

  const operativos = modules.filter((m) => m.status === "operativo");

  return (
    <div>
      <PageHeader
        label="Panel de control"
        title={`Hola, ${user?.name?.split(" ")[0] || "técnico"}`}
        description="Accede a los módulos normativos, gestiona expedientes y genera estudios con informe no vinculante."
      />

      <div className="grid grid-cols-1 gap-px border border-border bg-border sm:grid-cols-3">
        <StatCard icon={Boxes} label="Módulos operativos" value={operativos.length} testid="stat-modules" />
        <StatCard icon={FolderKanban} label="Expedientes" value={projects.length} testid="stat-projects" />
        <StatCard icon={FileStack} label="Estudios totales" value={projects.reduce((a, p) => a + (p.studies_count || 0), 0)} testid="stat-studies" />
      </div>

      <div className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading text-xl">Módulos normativos</h2>
          <button
            className="text-sm text-muted-foreground hover:text-foreground"
            onClick={() => navigate("/modulos")}
            data-testid="view-all-modules"
          >
            Ver todos
          </button>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {modules.map((m) => {
            const operativo = m.status === "operativo";
            return (
              <button
                key={m.code}
                data-testid={`module-card-${m.code}`}
                onClick={() => operativo && navigate("/expedientes")}
                className={`group flex flex-col items-start border border-border bg-background p-6 text-left transition-transform ${
                  operativo ? "cursor-pointer hover:-translate-y-1 hover:border-foreground" : "opacity-70"
                }`}
              >
                <div className="flex w-full items-start justify-between">
                  <ModuleIcon icon={m.icon} accent={m.accent} />
                  {operativo ? (
                    <Badge className="rounded-sm bg-emerald-100 text-emerald-800 hover:bg-emerald-100">Operativo</Badge>
                  ) : (
                    <Badge variant="secondary" className="rounded-sm">Próximamente</Badge>
                  )}
                </div>
                <h3 className="mt-4 font-heading text-lg">{m.short_name}</h3>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{m.description}</p>
                <p className="mt-3 font-mono text-xs text-muted-foreground">{m.legal_reference}</p>
                {operativo && (
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-orange-600">
                    Crear estudio <ArrowUpRight className="h-3.5 w-3.5" />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
