import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { ModuleIcon } from "@/components/ModuleIcon";
import { Badge } from "@/components/ui/badge";

export default function ModulesPage() {
  const { data: modules = [] } = useQuery({ queryKey: ["modules"], queryFn: () => api.get("/modules").then((r) => r.data) });

  return (
    <div>
      <PageHeader
        label="Registro de módulos"
        title="Módulos normativos"
        description="Cada normativa es un módulo desacoplado con su propio esquema, asistente, reglas y plantilla de informe. Añadir una nueva normativa no requiere rehacer la arquitectura base."
      />
      <div className="border border-border bg-background">
        {modules.map((m, i) => (
          <div
            key={m.code}
            data-testid={`module-row-${m.code}`}
            className={`flex flex-col gap-4 p-6 sm:flex-row sm:items-center ${i > 0 ? "border-t border-border" : ""}`}
          >
            <ModuleIcon icon={m.icon} accent={m.accent} />
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h3 className="font-heading text-lg">{m.name}</h3>
                <span className="font-mono text-xs text-muted-foreground">{m.code}</span>
              </div>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{m.description}</p>
              <p className="mt-2 font-mono text-xs text-muted-foreground">{m.legal_reference} · v{m.version} · {m.category}</p>
            </div>
            {m.status === "operativo" ? (
              <Badge className="rounded-sm bg-emerald-100 text-emerald-800 hover:bg-emerald-100">Operativo</Badge>
            ) : (
              <Badge variant="secondary" className="rounded-sm">Próximamente</Badge>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
