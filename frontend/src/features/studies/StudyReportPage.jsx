import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Printer, History, Loader2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate, num, RISK_STYLES, STATE_META } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

function RefTable({ t }) {
  const hlRows = new Set(t.highlight_rows || []);
  const hlCells = new Set((t.highlight_cells || []).map(([r, c]) => `${r}-${c}`));
  return (
    <div data-testid={`ref-table-${t.id}`}>
      <p className="mb-2 text-sm font-semibold">{t.titulo}</p>
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border bg-secondary/60 text-left uppercase tracking-wide text-muted-foreground">
              {t.headers.map((h, i) => (
                <th key={i} className="px-2.5 py-2 font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="font-mono">
            {t.rows.map((row, r) => {
              const rowHl = hlRows.has(r);
              return (
                <tr key={r} className={`border-b border-border last:border-0 ${rowHl ? "bg-orange-100" : ""}`}>
                  {row.map((cell, c) => {
                    const cellHl = hlCells.has(`${r}-${c}`);
                    return (
                      <td key={c} className={`px-2.5 py-1.5 ${c === 0 ? "font-sans" : ""} ${cellHl ? "bg-orange-500 font-bold text-white" : ""}`}>
                        {cell}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {t.nota && <p className="mt-1.5 text-[11px] leading-relaxed text-muted-foreground">{t.nota}</p>}
      <p className="mt-1 text-[11px] italic text-muted-foreground">Fuente: {t.referencia}</p>
    </div>
  );
}


function Section({ s }) {
  return (
    <section className="border-t border-border py-6 first:border-t-0">
      <h3 className="font-heading text-lg">{s.title}</h3>
      <div className="mt-3 text-sm text-slate-700">
        {s.type === "text" && <p className="leading-relaxed">{s.body}</p>}

        {s.type === "keyvalue" && (
          <table className="w-full">
            <tbody>
              {s.rows.map((r, i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  <td className="py-2 pr-4 text-muted-foreground">{r.k}</td>
                  <td className="py-2 font-medium">{r.v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {s.type === "zonas" && (
          <div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                  <th className="py-2">Zona</th><th className="py-2">Tipo</th>
                  <th className="py-2 text-right">Ci</th><th className="py-2 text-right">Sup.</th>
                  <th className="py-2 text-right">Aporte (MJ)</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {s.zonas.map((z, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="py-2 font-sans">{z.descripcion}</td>
                    <td className="py-2 font-sans">{z.modo === "almacenamiento" ? "Almac." : "Prod."}</td>
                    <td className="py-2 text-right">{num(z.ci, 2)}</td>
                    <td className="py-2 text-right">{num(z.superficie)}</td>
                    <td className="py-2 text-right">{num(z.aporte)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3 grid grid-cols-2 gap-2 border border-border bg-secondary/40 p-3 font-mono text-sm sm:grid-cols-4">
              <span>A = {num(s.resumen.A)} m²</span>
              <span>Ra = {num(s.resumen.ra, 2)}</span>
              <span className="font-bold">Qs = {num(s.resumen.qs_mj, 1)} MJ/m²</span>
              <span>{num(s.resumen.qs_mcal, 1)} Mcal/m²</span>
            </div>
          </div>
        )}

        {s.type === "nri" && (
          <div className="flex items-center gap-4">
            <span className={`flex h-14 w-14 items-center justify-center font-heading text-2xl font-bold text-white ${(RISK_STYLES[s.categoria] || RISK_STYLES.MEDIO).bg}`}>{s.nivel}</span>
            <div>
              <p className="font-heading text-xl">Nivel {s.nivel} · {s.categoria}</p>
              <p className="font-mono text-sm text-muted-foreground">Qs = {num(s.qs_mj, 1)} MJ/m² ({num(s.qs_mcal, 1)} Mcal/m²)</p>
            </div>
          </div>
        )}

        {s.type === "tablas" && (
          <div className="space-y-6">
            {s.items.map((t) => (
              <RefTable key={t.id} t={t} />
            ))}
          </div>
        )}

        {s.type === "instalaciones" && (
          <div className="border border-border">
            {s.items.map((it, i) => (
              <div key={i} className="flex items-start justify-between gap-3 border-b border-border p-3 last:border-0">
                <div className="flex-1">
                  <p className="text-sm font-medium">{it.nombre}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{it.detalle}</p>
                </div>
                <span className={`shrink-0 rounded-sm border px-2 py-0.5 text-xs font-medium ${it.obligatorio ? "border-red-300 bg-red-50 text-red-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
                  {it.obligatorio ? "Obligatorio" : "No exigible"}
                </span>
              </div>
            ))}
          </div>
        )}

        {s.type === "observaciones" && (
          <ul className="space-y-2">
            {s.items.map((o, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${o.tipo === "error" ? "bg-red-500" : o.tipo === "warning" ? "bg-amber-500" : "bg-slate-400"}`} />
                <span>{o.texto}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

export default function StudyReportPage() {
  const { studyId } = useParams();
  const navigate = useNavigate();
  const [showVersions, setShowVersions] = useState(false);
  const [activeReport, setActiveReport] = useState(null);

  const { data: study, isLoading } = useQuery({ queryKey: ["study", studyId], queryFn: () => api.get(`/studies/${studyId}`).then((r) => r.data) });
  const { data: versions = [] } = useQuery({ queryKey: ["versions", studyId], queryFn: () => api.get(`/studies/${studyId}/versions`).then((r) => r.data) });

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  const report = activeReport || study?.report;
  if (!report) {
    return (
      <div className="mx-auto max-w-2xl text-center">
        <p className="font-heading text-lg">Aún no hay informe</p>
        <p className="mt-1 text-sm text-muted-foreground">Completa el asistente y ejecuta el cálculo para generar el informe.</p>
        <Button className="mt-4 rounded-sm" onClick={() => navigate(`/estudios/${studyId}`)}>Ir al asistente</Button>
      </div>
    );
  }

  const state = STATE_META[report.estado_global] || STATE_META.observaciones;

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex items-center justify-between no-print">
        <button onClick={() => navigate(`/estudios/${studyId}`)} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground" data-testid="back-to-wizard">
          <ArrowLeft className="h-4 w-4" /> Asistente
        </button>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="rounded-sm" onClick={() => setShowVersions((v) => !v)} data-testid="toggle-versions">
            <History className="mr-2 h-4 w-4" /> Versiones ({versions.length})
          </Button>
          <Button className="rounded-sm" onClick={() => window.print()} data-testid="print-report">
            <Printer className="mr-2 h-4 w-4" /> Descargar PDF
          </Button>
        </div>
      </div>

      {showVersions && (
        <div className="mb-4 border border-border bg-background no-print" data-testid="versions-panel">
          {versions.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">Sin versiones guardadas todavía.</p>
          ) : versions.map((v) => (
            <div key={v.id} className="flex items-center justify-between border-b border-border p-3 last:border-0">
              <div>
                <span className="font-mono text-sm font-medium">v{v.version}</span>
                <span className="ml-3 text-xs text-muted-foreground">{formatDate(v.created_at)}</span>
              </div>
              <Button variant="ghost" size="sm" className="rounded-sm" onClick={() => setActiveReport(v.report)} data-testid={`view-version-${v.version}`}>Ver</Button>
            </div>
          ))}
        </div>
      )}

      <div className="print-area border border-border bg-background p-8 sm:p-12">
        {/* Report header */}
        <div className="flex items-start justify-between border-b-2 border-foreground pb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center bg-orange-500 font-heading text-sm font-bold text-white">N</div>
              <span className="font-heading font-semibold">NormaLab</span>
            </div>
            <h1 className="mt-4 font-heading text-2xl font-light tracking-tight">{report.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{study.name}</p>
          </div>
          <div className="text-right">
            <span className={`inline-flex rounded-sm border px-2.5 py-1 text-xs font-medium ${state.cls}`}>{state.label}</span>
            <p className="mt-2 font-mono text-xs text-muted-foreground">{formatDate(report.generated_at)}</p>
            {activeReport && <Badge variant="secondary" className="mt-1 rounded-sm text-xs">versión histórica</Badge>}
          </div>
        </div>

        {report.sections.map((s) => <Section key={s.id} s={s} />)}

        <div className="mt-6 flex items-start gap-2 border border-amber-300 bg-amber-50 p-4 text-xs text-amber-900">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{report.disclaimer}</p>
        </div>
      </div>
    </div>
  );
}
