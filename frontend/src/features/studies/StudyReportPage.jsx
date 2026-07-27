import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Printer, History, Loader2, AlertTriangle, FileText, FileSpreadsheet } from "lucide-react";
import { toast } from "sonner";
import { api, apiError, downloadFile } from "@/lib/api";
import { formatDate, num, RISK_STYLES, STATE_META } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const ESC_TIPO_LABEL = {
  abierta: "abierta", protegida: "protegida",
  especialmente_protegida: "especialmente protegida", compartimentada: "compartimentada",
};

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


function SectorReport({ s }) {
  const risk = RISK_STYLES[s.nivel_riesgo.categoria] || RISK_STYLES.MEDIO;
  const sec = s.sectorizacion;
  return (
    <div className="mt-5 border border-border first:mt-0" data-testid={`report-sector-${s.id}`}>
      <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2">
        <span className="font-heading text-base">{s.nombre}</span>
        <span className={`flex items-center gap-2 text-sm font-medium ${risk.text}`}>
          <span className={`flex h-6 w-6 items-center justify-center text-xs font-bold text-white ${risk.bg}`}>{s.nivel_riesgo.nivel}</span>
          {s.nivel_riesgo.categoria}
        </span>
      </div>
      <table className="w-full text-sm">
        <tbody className="font-mono">
          {s.calculo.zonas.map((z, i) => (
            <tr key={i} className="border-b border-border">
              <td className="px-4 py-1.5 font-sans">{z.descripcion}</td>
              <td className="px-4 py-1.5 font-sans text-muted-foreground">{z.modo === "deposito" ? "Depósito" : z.modo === "almacenamiento" ? "Almac." : "Prod."}</td>
              <td className="px-4 py-1.5 text-right">Ci {num(z.ci, 2)}</td>
              <td className="px-4 py-1.5 text-right">{num(z.superficie)} m²</td>
              <td className="px-4 py-1.5 text-right">{num(z.aporte)} MJ</td>
            </tr>
          ))}
          <tr className="bg-secondary/40">
            <td className="px-4 py-2 font-sans" colSpan={3}>A = {num(s.calculo.A)} m² (útil) · Ra = {num(s.calculo.ra, 1)}</td>
            <td className="px-4 py-2 text-right font-bold" colSpan={2}>Qs = {num(s.calculo.qs_mj, 1)} MJ/m²</td>
          </tr>
        </tbody>
      </table>
      <p className="border-t border-border px-4 py-2 text-sm text-slate-700">{sec.mensaje}</p>
      <div className="grid grid-cols-3 gap-3 border-t border-border p-4 text-sm">
        <div><span className="text-xs uppercase text-muted-foreground">Estabilidad</span><p className="font-mono font-semibold">{s.requisitos.estabilidad?.valor}</p></div>
        <div><span className="text-xs uppercase text-muted-foreground">Delimitadores</span><p className="font-mono font-semibold">{s.requisitos.delimitadores?.valor}</p></div>
        <div><span className="text-xs uppercase text-muted-foreground">Evacuación</span><p className="font-mono font-semibold">{s.evacuacion?.distancia_maxima} m · {s.evacuacion?.num_salidas} sal.</p></div>
      </div>
      {s.evacuacion?.recorridos?.length > 0 && (
        <div className="border-t border-border p-4">
          <p className="mb-2 text-xs uppercase text-muted-foreground">Recorridos de evacuación{s.evacuacion.coeficiente !== "ninguno" ? ` · ${s.evacuacion.coeficiente_label}` : ""}</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="py-1.5">Origen</th><th className="py-1.5">Tipo</th>
                <th className="py-1.5 text-right">Real</th><th className="py-1.5 text-right">Máx.</th><th className="py-1.5 text-right">Estado</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {s.evacuacion.recorridos.map((r, i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  <td className="py-1.5 font-sans">{r.origen}</td>
                  <td className="py-1.5 font-sans text-muted-foreground">{r.tipo === "sin_alternativa" ? "Sin alternativa" : "Hasta salida"}</td>
                  <td className="py-1.5 text-right">{num(r.distancia_real, 1)} m</td>
                  <td className="py-1.5 text-right">{num(r.distancia_max, 1)} m</td>
                  <td className={`py-1.5 text-right font-sans font-semibold ${r.cumple ? "text-emerald-700" : "text-red-700"}`}>{r.cumple ? "Cumple" : "No cumple"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="border-t border-border">
        {s.requisitos.instalaciones.map((it, i) => (
          <div key={i} className="flex items-start justify-between gap-3 border-b border-border px-4 py-2 last:border-0">
            <div className="flex-1"><p className="text-sm font-medium">{it.nombre}</p><p className="mt-0.5 text-xs text-muted-foreground">{it.detalle}</p></div>
            <span className={`shrink-0 rounded-sm border px-2 py-0.5 text-xs font-medium ${it.obligatorio ? "border-red-300 bg-red-50 text-red-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
              {it.obligatorio ? "Obligatorio" : "No exigible"}
            </span>
          </div>
        ))}
      </div>
      {s.locales_riesgo_especial?.length > 0 && (
        <div className="border-t border-border p-4" data-testid={`report-sector-${s.id}-lre`}>
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Locales de riesgo especial (excluidos de la carga de fuego · Tabla 2.1 DB-SI)</p>
          <div className="space-y-2">
            {s.locales_riesgo_especial.map((l, i) => (
              <div key={i} className="text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{l.nombre} · riesgo {l.riesgo?.toLowerCase?.()}</span>
                  <span className="font-mono text-muted-foreground">{num(l.superficie)} m² · {l.resistencia}</span>
                </div>
                {l.justificacion && <p className="mt-0.5 text-xs text-muted-foreground">{l.justificacion}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      {s.escaleras_protegidas?.length > 0 && (
        <div className="border-t border-border p-4" data-testid={`report-sector-${s.id}-escaleras`}>
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Escaleras protegidas (justificación CTE)</p>
          <div className="space-y-2">
            {s.escaleras_protegidas.map((e, i) => (
              <div key={i} className="text-sm">
                <span className="font-medium">{e.nombre} · {ESC_TIPO_LABEL[e.tipo] || "protegida"}{e.sentido ? ` · ${e.sentido}` : ""} · {e.situacion}{e.anchura ? ` · ${e.anchura} m` : ""}{e.capacidad ? ` · ${e.capacidad} pers.` : ""}</span>
                {e.justificacion && <p className="mt-0.5 text-xs text-muted-foreground">{e.justificacion}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      {s.dbsi && (
        <div className="border-t border-border p-4" data-testid={`report-sector-${s.id}-dbsi`}>
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">CTE DB-SI · secciones (sector en ámbito CTE)</p>
          <div className="space-y-1.5">
            {(s.dbsi.secciones || []).map((sec) => (
              <div key={sec.id} className="flex items-center justify-between text-sm">
                <span>{sec.titulo || sec.id}</span>
                <span className={`rounded-sm border px-2 py-0.5 text-xs font-medium ${sec.estado === "no_cumple" ? "border-red-300 bg-red-50 text-red-800" : sec.estado === "cumple" ? "border-emerald-300 bg-emerald-50 text-emerald-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
                  {sec.estado === "no_cumple" ? "No cumple" : sec.estado === "cumple" ? "Cumple" : "Info"}
                </span>
              </div>
            ))}
          </div>
          {(s.dbsi.tablas || []).length > 0 && (
            <div className="mt-4 space-y-5" data-testid={`report-sector-${s.id}-dbsi-tablas`}>
              <p className="text-xs uppercase tracking-wider text-muted-foreground">Tablas DB-SI aplicadas (resultado resaltado)</p>
              {s.dbsi.tablas.map((t) => <RefTable key={t.id} t={{ ...t, id: `${s.id}-${t.id}` }} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Section({ s }) {
  if (s.type === "ambito_header") {
    return (
      <div className="mt-10 border-l-4 border-orange-500 bg-secondary/40 px-4 py-3" data-testid={`report-ambito-${s.id}`}>
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{s.tipo}</p>
        <h2 className="font-heading text-xl">{s.title}</h2>
      </div>
    );
  }
  return (
    <section className="border-t border-border py-6 first:border-t-0">
      <h3 className="font-heading text-lg">{s.title}</h3>
      <div className="mt-3 text-sm text-slate-700">
        {s.type === "text" && <p className="leading-relaxed">{s.body}</p>}

        {s.type === "resumen_ejecutivo" && (
          <>
          <div className="overflow-x-auto border border-border" data-testid="report-resumen-ejecutivo">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
                  <th className="px-3 py-2">Sector</th><th className="px-3 py-2">Ámbito</th>
                  <th className="px-3 py-2 text-right">Qs</th><th className="px-3 py-2">NRI</th><th className="px-3 py-2">Estado</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {s.filas.map((f, i) => {
                  const st = STATE_META[f.estado] || STATE_META.observaciones;
                  return (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-3 py-1.5 font-sans font-medium">{f.nombre}</td>
                      <td className="px-3 py-1.5 font-sans text-xs">{f.ambito}</td>
                      <td className="px-3 py-1.5 text-right">{num(f.qs_mj, 1)}</td>
                      <td className="px-3 py-1.5 font-sans">{f.nivel} · {f.categoria}</td>
                      <td className="px-3 py-1.5"><span className={`inline-flex rounded-sm border px-2 py-0.5 text-xs font-sans font-medium ${st.cls}`}>{st.label}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {s.depositos?.length > 0 && (
            <div className="mt-3 border border-amber-200 bg-amber-50 p-3" data-testid="report-depositos-just">
              <p className="mb-1.5 text-sm font-semibold text-amber-900">Depósitos de combustible (almacenamiento)</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                {s.depositos.map((d, i) => <li key={i}>{d.justificacion}</li>)}
              </ul>
            </div>
          )}
          </>
        )}

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

        {s.type === "superficies" && (
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
                  <th className="px-3 py-2">Dependencia</th><th className="px-3 py-2">Planta</th><th className="px-3 py-2">Sector</th>
                  <th className="px-3 py-2 text-right">S. útil</th><th className="px-3 py-2 text-right">S. construida</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {(s.data.grupos || [{ planta: null, filas: s.data.filas, sub_util: null, sub_construida: null }]).map((g, gi) => (
                  <Fragment key={gi}>
                    {g.planta && (
                      <tr className="bg-secondary/30"><td colSpan={5} className="px-3 py-1.5 font-sans text-xs font-semibold uppercase tracking-wider">{g.planta}</td></tr>
                    )}
                    {g.filas.map((r, i) => (
                      <tr key={`${gi}-${i}`} className="border-b border-border">
                        <td className="px-3 py-1.5 font-sans">{r.nombre}</td><td className="px-3 py-1.5 font-sans">{r.planta}</td>
                        <td className="px-3 py-1.5 font-sans text-muted-foreground">{r.sector}</td>
                        <td className="px-3 py-1.5 text-right">{num(r.sup_util, 2)}</td><td className="px-3 py-1.5 text-right">{num(r.sup_construida, 2)}</td>
                      </tr>
                    ))}
                    {g.planta && (
                      <tr className="border-b border-border bg-secondary/10">
                        <td colSpan={3} className="px-3 py-1 font-sans text-xs italic text-muted-foreground">Subtotal {g.planta}</td>
                        <td className="px-3 py-1 text-right text-xs font-semibold">{num(g.sub_util, 2)}</td><td className="px-3 py-1 text-right text-xs font-semibold">{num(g.sub_construida, 2)}</td>
                      </tr>
                    )}
                  </Fragment>
                ))}
                <tr className="bg-secondary/40 font-bold">
                  <td className="px-3 py-2 font-sans" colSpan={3}>Total</td>
                  <td className="px-3 py-2 text-right">{num(s.data.total_util, 2)}</td><td className="px-3 py-2 text-right">{num(s.data.total_construida, 2)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {s.type === "ocupacion" && (
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
                  <th className="px-3 py-2">Dependencia</th><th className="px-3 py-2">Sector</th><th className="px-3 py-2">Uso</th>
                  <th className="px-3 py-2 text-right">Sup.</th><th className="px-3 py-2 text-right">Densidad</th><th className="px-3 py-2 text-right">Ocupación</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {s.data.filas.map((r, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="px-3 py-1.5 font-sans">{r.nombre}</td><td className="px-3 py-1.5 font-sans text-muted-foreground">{r.sector}</td>
                    <td className="px-3 py-1.5 font-sans">{r.uso}</td><td className="px-3 py-1.5 text-right">{num(r.superficie, 2)}</td>
                    <td className="px-3 py-1.5 text-right font-sans">{r.densidad}</td><td className="px-3 py-1.5 text-right font-bold">{r.ocupacion}</td>
                  </tr>
                ))}
                <tr className="bg-secondary/40 font-bold">
                  <td className="px-3 py-2 font-sans" colSpan={5}>Ocupación total</td>
                  <td className="px-3 py-2 text-right">{s.data.total} pers.</td>
                </tr>
                {s.data.filas.filter((r) => r.nota).map((r, i) => (
                  <tr key={`nota-${i}`} className="border-t border-border">
                    <td className="px-3 py-1.5 font-sans text-xs italic text-muted-foreground" colSpan={6} data-testid={`report-ocupacion-nota-${i}`}>Ocupación personalizada · {r.nombre}: {r.nota}</td>
                  </tr>
                ))}
                {(s.data.por_planta || []).length > 0 && (
                  <>
                    <tr className="border-t border-border bg-secondary/20"><td colSpan={6} className="px-3 py-1 font-sans text-xs font-semibold uppercase tracking-wider text-muted-foreground">Ocupación por planta</td></tr>
                    {s.data.por_planta.map((p, i) => (
                      <tr key={`pp-${i}`} className="border-b border-border last:border-0">
                        <td colSpan={5} className="px-3 py-1 font-sans">{p.planta}</td>
                        <td className="px-3 py-1 text-right font-bold">{p.ocupacion} pers.</td>
                      </tr>
                    ))}
                  </>
                )}
              </tbody>
            </table>
          </div>
        )}

        {s.type === "resumen" && (
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
                  <th className="px-3 py-2">Sector</th><th className="px-3 py-2">Config.</th><th className="px-3 py-2 text-right">Sup.</th>
                  <th className="px-3 py-2 text-right">Qs</th><th className="px-3 py-2">NRI</th><th className="px-3 py-2">Estab.</th><th className="px-3 py-2 text-right">Ocup.</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {s.filas.map((r, i) => {
                  const risk = RISK_STYLES[r.categoria] || RISK_STYLES.MEDIO;
                  return (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-3 py-1.5 font-sans font-medium">{r.nombre}</td><td className="px-3 py-1.5 font-sans text-xs">{r.config}</td>
                      <td className="px-3 py-1.5 text-right">{num(r.superficie)}</td><td className="px-3 py-1.5 text-right">{num(r.qs_mj, 1)}</td>
                      <td className={`px-3 py-1.5 font-sans font-semibold ${risk.text}`}>{r.nivel} · {r.categoria}</td>
                      <td className="px-3 py-1.5">{r.estabilidad}</td><td className="px-3 py-1.5 text-right font-sans">{r.ocupacion}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {s.type === "sectores" && (
          <div>{s.items.map((sec) => <SectorReport key={sec.id} s={sec} />)}</div>
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
  const [exporting, setExporting] = useState(null);

  const doExport = async (fmt) => {
    setExporting(fmt);
    try {
      await downloadFile(`/studies/${studyId}/export/${fmt}`, `estudio.${fmt}`);
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setExporting(null);
    }
  };

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
          <Button variant="outline" className="rounded-sm" onClick={() => doExport("docx")} disabled={exporting} data-testid="export-docx">
            {exporting === "docx" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />} DOCX
          </Button>
          <Button variant="outline" className="rounded-sm" onClick={() => doExport("xlsx")} disabled={exporting} data-testid="export-xlsx">
            {exporting === "xlsx" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileSpreadsheet className="mr-2 h-4 w-4" />} Excel
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
