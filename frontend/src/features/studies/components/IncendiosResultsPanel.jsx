import { Factory, Building2 } from "lucide-react";
import { ResultsPanel } from "@/features/studies/components/ResultsPanel";
import { DbsiResultsPanel } from "@/features/studies/components/DbsiResultsPanel";

export function IncendiosResultsPanel({ results }) {
  if (!results?.ambitos) return null;
  return (
    <div className="space-y-10" data-testid="incendios-results-panel">
      {results.ambitos.map((a) => (
        <div key={a.id} data-testid={`incendios-ambito-${a.id}`}>
          <div className="mb-4 flex items-center gap-2 border-l-4 border-orange-500 bg-secondary/40 px-4 py-3">
            {a.tipo === "industrial" ? <Factory className="h-5 w-5 text-orange-600" /> : <Building2 className="h-5 w-5 text-orange-600" />}
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{a.tipo === "industrial" ? "RSCIEI · RD 164/2025" : "CTE DB-SI"}</p>
              <h3 className="font-heading text-lg">{a.nombre}</h3>
            </div>
          </div>
          {a.tipo === "industrial" ? <ResultsPanel results={a.results} /> : <DbsiResultsPanel results={a.results} />}
        </div>
      ))}
    </div>
  );
}
