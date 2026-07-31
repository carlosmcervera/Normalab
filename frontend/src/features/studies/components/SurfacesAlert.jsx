import { AlertTriangle, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

// Un estudio queda "desactualizado" si fue calculado antes del último cambio
// del cuadro de superficies/ocupación compartido del expediente.
export function isSurfacesOutdated(study, project) {
  if (!study || !project || study.status !== "calculado") return false;
  const upd = project.estancias_updated_at;
  if (!upd) return false;
  const ver = study.estancias_version;
  return !ver || ver < upd;
}

export function SurfacesOutdatedBanner({ onRecompute, pending, compact }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-3 border border-amber-300 bg-amber-50 text-amber-800 ${compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm"}`}
      data-testid="surfaces-outdated-banner"
    >
      <AlertTriangle className="h-4 w-4 shrink-0" />
      <p className="flex-1">
        El <b>cuadro de superficies y ocupación</b> del expediente ha cambiado después de calcular este informe.
        Recalcúlalo para reflejar los datos actuales.
      </p>
      {onRecompute && (
        <Button size="sm" variant="outline" className="rounded-sm border-amber-400 text-amber-900 hover:bg-amber-100"
          onClick={onRecompute} disabled={pending} data-testid="recompute-outdated-button">
          {pending ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="mr-1.5 h-3.5 w-3.5" />}
          Recalcular
        </Button>
      )}
    </div>
  );
}
