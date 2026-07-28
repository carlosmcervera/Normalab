import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

// Aviso: el cuadro de superficies es compartido por el expediente. Si lo usan
// varios estudios, editarlo afecta a todos los informes.
export function SharedTableAlert({ projectId, currentStudyId }) {
  const { data: studies = [] } = useQuery({
    queryKey: ["project-studies", projectId],
    queryFn: () => api.get(`/studies?project_id=${projectId}`).then((r) => r.data || []),
    enabled: !!projectId,
  });
  if (studies.length <= 1) return null;
  const otros = studies.filter((s) => s.id !== currentStudyId);
  const nombres = [...new Set(otros.map((s) => s.module_name).filter(Boolean))];
  return (
    <div className="flex items-start gap-3 border border-amber-300 bg-amber-50 px-3 py-2.5 text-sm text-amber-800" data-testid="shared-table-alert">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <p>
        Este cuadro de superficies es <b>compartido</b> por {studies.length} estudios de este expediente
        {nombres.length ? <> (también en: {nombres.join(", ")})</> : null}. Cualquier cambio afectará a todos los
        informes que lo utilizan; revísalos después de editarlo para evitar incoherencias.
      </p>
    </div>
  );
}
