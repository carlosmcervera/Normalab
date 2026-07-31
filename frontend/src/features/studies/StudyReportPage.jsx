import { Fragment, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Printer, History, Loader2, AlertTriangle, FileText, FileSpreadsheet } from "lucide-react";
import { toast } from "sonner";
import { api, apiError, downloadFile } from "@/lib/api";
import { EsquemaUnifilar } from "@/features/studies/components/EsquemaUnifilar";
import { CargaFuegoTable } from "@/features/studies/components/CargaFuegoTable";
import { isSurfacesOutdated, SurfacesOutdatedBanner } from "@/features/studies/components/SurfacesAlert";
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
  const legend = t.legend || [];
  const colorByIdx = {};
  legend.forEach((l) => { colorByIdx[l.idx] = l.color; });
  const cellSectors = t.cell_sectors || {};
  const rowSectors = t.row_sectors || {};
  const bgFor = (idxs) => {
    const cols = idxs.map((i) => colorByIdx[i]).filter(Boolean);
    if (cols.length === 0) return null;
    if (cols.length === 1) return cols[0];
    const step = 100 / cols.length;
    return `linear-gradient(90deg, ${cols.map((c, i) => `${c} ${i * step}%, ${c} ${(i + 1) * step}%`).join(", ")})`;
  };
  return (
    <div data-testid={`ref-table-${t.id}`}>
      <p className="mb-2 text-sm font-semibold">{t.titulo}</p>
      {legend.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1" data-testid={`ref-table-${t.id}-legend`}>
          {legend.map((l) => (
            <span key={l.idx} className="flex items-center gap-1.5 text-[11px] text-slate-600">
              <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: l.color }} />
              {l.nombre}
            </span>
          ))}
        </div>
      )}
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
              const rSec = rowSectors[String(r)];
              const legacyRow = hlRows.has(r);
              return (
                <tr key={r} className={`border-b border-border last:border-0 ${rSec ? "bg-slate-50" : legacyRow ? "bg-orange-100" : ""}`}>
                  {row.map((cell, c) => {
                    const cSec = cellSectors[`${r}-${c}`] || (c === 0 && rSec ? rSec : null);
                    const bg = cSec ? bgFor(cSec) : null;
                    const legacyCell = hlCells.has(`${r}-${c}`);
                    return (
                      <td key={c}
                        className={`px-2.5 py-1.5 ${c === 0 ? "font-sans" : ""} ${bg ? "font-bold text-white" : legacyCell ? "bg-orange-500 font-bold text-white" : ""}`}
                        style={bg ? (bg.startsWith("linear") ? { backgroundImage: bg } : { backgroundColor: bg }) : undefined}>
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
          <tr className="bg-secondary/40">
            <td className="px-4 py-2 font-sans">Actividad: <b>{s.actividad || "—"}</b> · Modo predominante: <b>{s.modo_predominante === "almacenamiento" ? "Almacenamiento" : "Producción"}</b></td>
          </tr>
        </tbody>
      </table>
      <CargaFuegoTable calculo={s.calculo} categoria={s.nivel_riesgo.categoria} />
      <p className="border-t border-border px-4 py-2 text-sm text-slate-700">{sec.mensaje}</p>
      <div className="grid grid-cols-3 gap-3 border-t border-border p-4 text-sm">
        <div><span className="text-xs uppercase text-muted-foreground">Estabilidad</span><p className="font-mono font-semibold">{s.requisitos.estabilidad?.valor}
          {s.requisitos.estabilidad?.reduccion_rociadores && (
            <span className="ml-1 text-[11px] font-normal text-emerald-700" title={s.requisitos.estabilidad?.detalle}>(base {s.requisitos.estabilidad.valor_base}, −1 grado por rociadores)</span>
          )}</p></div>
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
            <div className="flex-1">
              <p className="text-sm font-medium">{it.nombre}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{it.detalle}</p>
              {it.superficie_aerodinamica && (
                <p className="mt-1 inline-block rounded-sm border border-sky-300 bg-sky-50 px-2 py-1 text-xs font-medium text-sky-900">
                  Superficie aerodinámica de evacuación de humos (8.4): ≥ {num(it.superficie_aerodinamica.superficie_aerodinamica, 2)} m²
                  <span className="font-normal text-sky-700"> · 0,5 m² / {num(it.superficie_aerodinamica.ratio_m2, 0)} m² · {it.superficie_aerodinamica.situacion === "bajo_rasante" ? "bajo rasante" : "sobre rasante"}</span>
                </p>
              )}
            </div>
            <span className={`shrink-0 rounded-sm border px-2 py-0.5 text-xs font-medium ${it.obligatorio ? "border-red-300 bg-red-50 text-red-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
              {it.obligatorio ? "Obligatorio" : "No exigible"}
            </span>
          </div>
        ))}
      </div>
      {s.locales_riesgo_especial?.length > 0 && (
        <div className="border-t border-border p-4" data-testid={`report-sector-${s.id}-lre`}>
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Locales de riesgo especial (no computan carga de fuego · clasificados por CTE DB-SI, Tabla 2.1)</p>
          <div className="space-y-2">
            {s.locales_riesgo_especial.map((l, i) => (
              <div key={i} className="text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{l.nombre} · riesgo {l.riesgo?.toLowerCase?.()}</span>
                  <span className="font-mono text-muted-foreground">
                    {l.qs != null ? `Qs ${num(l.qs, 0)} MJ/m² · ` : (l.volumen != null ? `${num(l.volumen, 1)} m³ · ` : (l.potencia != null ? `${num(l.potencia, 1)} · ` : ""))}
                    {num(l.superficie)} m² · {l.resistencia}
                  </span>
                </div>
                {l.uso && <p className="mt-0.5 text-xs text-slate-600">Uso (Tabla 2.1): {l.uso}{l.criterio ? ` — ${l.criterio}` : ""}</p>}
                {l.justificacion && <p className="mt-0.5 text-xs text-muted-foreground">{l.justificacion}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      {s.escaleras_protegidas?.length > 0 && (
        <div className="border-t border-border p-4" data-testid={`report-sector-${s.id}-escaleras`}>
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Escaleras de evacuación (CTE DB-SI · SI 3, Tablas 4.1 y 5.1)</p>
          <div className="space-y-3">
            {s.escaleras_protegidas.map((e, i) => {
              const c = e.calculo || {};
              const estCls = c.estado === "no_cumple" ? "text-red-700" : c.estado === "cumple" ? "text-emerald-700" : "text-slate-500";
              const estTxt = c.estado === "no_cumple" ? "No cumple" : c.estado === "cumple" ? "Cumple" : "Pendiente";
              return (
                <div key={i} className="rounded-sm border border-border p-3 text-sm" data-testid={`report-escalera-${i}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{e.nombre} · {ESC_TIPO_LABEL[e.tipo] || "protegida"}{e.sentido ? ` · evac. ${e.sentido}` : ""} · {e.situacion}</span>
                    <span className={`font-semibold ${estCls}`} data-testid={`report-escalera-${i}-estado`}>{estTxt}</span>
                  </div>
                  {(c.ocupantes || c.altura_evacuacion) && (
                    <p className="mt-1 font-mono text-xs text-slate-600">
                      P = {num(c.ocupantes)} ocupantes · h = {num(c.altura_evacuacion, 2)} m · uso: {c.uso}
                    </p>
                  )}
                  <div className="mt-2 grid gap-2 sm:grid-cols-4 text-xs">
                    <div className="rounded-sm bg-secondary/40 px-2 py-1.5">
                      <span className="uppercase text-muted-foreground">Protección proyectada</span>
                      <p className={`font-semibold ${c.proteccion_estado === "no_cumple" ? "text-red-700" : "text-emerald-700"}`}>{c.proteccion_proyectada_label || (ESC_TIPO_LABEL[e.tipo] || "protegida")}</p>
                    </div>
                    <div className="rounded-sm bg-secondary/40 px-2 py-1.5">
                      <span className="uppercase text-muted-foreground">Exigida mín. (Tabla 5.1)</span>
                      <p className="font-semibold">{c.proteccion_requerida_label || "—"}</p>
                    </div>
                    <div className="rounded-sm bg-secondary/40 px-2 py-1.5">
                      <span className="uppercase text-muted-foreground">RF del recinto</span>
                      <p className="font-mono font-semibold">{c.resistencia || "—"}</p>
                    </div>
                    <div className="rounded-sm bg-secondary/40 px-2 py-1.5">
                      <span className="uppercase text-muted-foreground">Anchura (Tabla 4.1)</span>
                      <p className={`font-mono font-semibold ${c.anchura_estado === "no_cumple" ? "text-red-700" : ""}`}>
                        mín. {c.anchura_min_texto || "—"}{c.anchura_proyectada ? ` · proy. ${num(c.anchura_proyectada, 2)} m` : ""}
                      </p>
                    </div>
                  </div>
                  {c.resistencia_detalle && <p className="mt-2 text-xs text-muted-foreground">{c.resistencia_detalle}</p>}
                  {e.justificacion && <p className="mt-1 text-xs text-muted-foreground">{e.justificacion}</p>}
                </div>
              );
            })}
          </div>
        </div>
      )}
      {s.construccion && (
        <div className="border-t border-border p-4" data-testid={`report-sector-${s.id}-construccion`}>
          <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">
            Construcción y propagación — {s.construccion.normativa || "RSCIEI Anexo II"}
          </p>

          {/* Propagación interior */}
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-600">
            Propagación interior · {s.construccion.interior?.referencia}
          </p>
          <div className="mt-1 overflow-x-auto border border-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-secondary/60 text-left uppercase tracking-wide text-muted-foreground">
                  <th className="px-2.5 py-1.5">Situación del elemento</th>
                  <th className="px-2.5 py-1.5">Techos y paredes</th>
                  <th className="px-2.5 py-1.5">Suelos</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {s.construccion.reaccion.tabla.map((r, i) => {
                  const hi = s.construccion.reaccion.nri_alto && i === 2;
                  return (
                    <tr key={i} className={`border-b border-border last:border-0 ${hi ? "bg-orange-100" : ""}`}>
                      <td className="px-2.5 py-1.5 font-sans">{r.situacion}</td>
                      <td className="px-2.5 py-1.5">{r.techos_paredes}</td>
                      <td className="px-2.5 py-1.5">{r.suelos}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-1.5 text-xs text-slate-700">
            Reacción al fuego de revestimientos:{" "}
            <span className={s.construccion.reaccion.cumple ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
              {s.construccion.reaccion.cumple ? "el proyecto cumple las clases exigidas" : "pendiente de verificar/justificar"}
            </span>
            {s.construccion.reaccion.observaciones ? ` · ${s.construccion.reaccion.observaciones}` : ""}
          </p>
          {s.construccion.interior?.delimitadores && (
            <p className="mt-1 text-xs text-slate-700">
              Elementos delimitadores del sector: exigido <b className="font-mono">{s.construccion.interior.delimitadores.requerido}</b>
              <span className="text-muted-foreground"> · {s.construccion.interior.delimitadores.detalle}</span>
            </p>
          )}

          {/* Propagación exterior */}
          <p className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-slate-600">
            Propagación exterior · {s.construccion.exterior?.referencia}
          </p>
          <div className="mt-1.5 grid gap-2 sm:grid-cols-3 text-sm">
            <div className="rounded-sm border border-border p-2">
              <p className="text-xs uppercase text-muted-foreground">Medianería</p>
              {s.construccion.medianeras ? (
                <p className="mt-0.5">Exigido <b className="font-mono">{s.construccion.medianeras.requerido}</b> · proyectado <b className="font-mono">{s.construccion.medianeras.proyectado || "—"}</b>{" "}
                  <span className={s.construccion.medianeras.estado === "no_cumple" ? "text-red-700 font-semibold" : s.construccion.medianeras.estado === "cumple" ? "text-emerald-700 font-semibold" : "text-slate-500"}>
                    ({s.construccion.medianeras.estado === "no_cumple" ? "No cumple" : s.construccion.medianeras.estado === "cumple" ? "Cumple" : "Pendiente"})</span>
                </p>
              ) : <p className="mt-0.5 text-muted-foreground">No linda con otro establecimiento/edificio.</p>}
            </div>
            <div className="rounded-sm border border-border p-2">
              <p className="text-xs uppercase text-muted-foreground">Fachada</p>
              {s.construccion.fachadas ? (
                <p className="mt-0.5">
                  {s.construccion.fachadas.distancia_d != null ? <>α {s.construccion.fachadas.angulo}° · d ≥ <b className="font-mono">{num(s.construccion.fachadas.distancia_d, 1)} m</b> · </> : null}
                  exigido <b className="font-mono">{s.construccion.fachadas.requerido}</b> / proyectado <b className="font-mono">{s.construccion.fachadas.proyectado || "—"}</b>{" "}
                  <span className={s.construccion.fachadas.estado === "no_cumple" ? "text-red-700 font-semibold" : s.construccion.fachadas.estado === "cumple" ? "text-emerald-700 font-semibold" : "text-slate-500"}>
                    ({s.construccion.fachadas.estado === "no_cumple" ? "No cumple" : s.construccion.fachadas.estado === "cumple" ? "Cumple" : "Pendiente"})</span>
                </p>
              ) : <p className="mt-0.5 text-muted-foreground">Sin encuentro de sector en fachada.</p>}
            </div>
            <div className="rounded-sm border border-border p-2">
              <p className="text-xs uppercase text-muted-foreground">Cubierta</p>
              <p className="mt-0.5">{s.construccion.cubierta.ligera ? "Cubierta ligera" : "Cubierta no ligera"}
                {s.construccion.cubierta.requerido ? <span className="text-muted-foreground"> · {s.construccion.cubierta.requerido}</span> : null}
                {s.construccion.cubierta.observaciones ? ` · ${s.construccion.cubierta.observaciones}` : ""}</p>
            </div>
          </div>
          {s.construccion.fachadas?.huecos && (
            <div className="mt-2 rounded-sm border border-border p-2 text-xs" data-testid={`report-sector-${s.id}-huecos`}>
              <p className="uppercase text-muted-foreground">Separación entre huecos (SI 2, Fig. 1.1)</p>
              <p className="mt-0.5">
                Ángulo {num(s.construccion.fachadas.huecos.angulo, 0)}° · mínima exigida <b className="font-mono">{num(s.construccion.fachadas.huecos.efectivo_m, 2)} m</b>
                {s.construccion.fachadas.huecos.proyectado_m != null ? <> · proyectada <b className="font-mono">{num(s.construccion.fachadas.huecos.proyectado_m, 2)} m</b></> : null}{" "}
                <span className={s.construccion.fachadas.huecos.estado === "no_cumple" ? "text-red-700 font-semibold" : s.construccion.fachadas.huecos.estado === "cumple" ? "text-emerald-700 font-semibold" : "text-slate-500"}>
                  ({s.construccion.fachadas.huecos.estado === "no_cumple" ? "No cumple" : s.construccion.fachadas.huecos.estado === "cumple" ? "Cumple" : "Pendiente"})</span>
                <span className="text-muted-foreground"> · {s.construccion.fachadas.huecos.nota}</span>
              </p>
            </div>
          )}
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

        {s.type === "fundamentos" && (
          <div className="space-y-4" data-testid="report-fundamentos">
            {s.items.map((f, i) => (
              <div key={i} className="border-l-2 border-orange-400 pl-3" data-testid={`report-fundamento-${i}`}>
                <p className="text-sm font-semibold">{f.tema}</p>
                <blockquote className="mt-1 text-sm italic leading-relaxed text-slate-700">{f.cita}</blockquote>
                <p className="mt-1 text-xs text-muted-foreground">— {f.referencia}</p>
              </div>
            ))}
          </div>
        )}

        {s.type === "anexo_propagacion" && (
          <div className="space-y-6" data-testid="report-anexo-propagacion">
            {(s.items || []).length === 0 && <p className="text-sm text-muted-foreground">No hay sectores.</p>}
            {(s.items || []).map((b, bi) => (
              <div key={bi} className="rounded-md border border-border" data-testid={`report-anexo-sector-${bi}`}>
                <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-4 py-2">
                  <span className="font-heading text-sm font-semibold">{b.sector}</span>
                  <span className={`rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase ${b.ambito === "CTE DB-SI" ? "bg-cyan-50 text-cyan-700" : "bg-orange-50 text-orange-700"}`}>{b.normativa}</span>
                </div>
                <div className="grid gap-0 md:grid-cols-2">
                  {[["Propagación interior", b.interior], ["Propagación exterior", b.exterior]].map(([titulo, items], ci) => (
                    <div key={ci} className={`p-4 ${ci === 0 ? "md:border-r border-border" : ""}`}>
                      <p className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-slate-600">{titulo}</p>
                      <div className="space-y-3">
                        {(items || []).map((f, i) => (
                          <div key={i} className="border-l-2 border-slate-300 pl-3">
                            <p className="text-xs font-semibold">{f.tema}</p>
                            <blockquote className="mt-0.5 text-xs italic leading-relaxed text-slate-700">{f.cita}</blockquote>
                            <p className="mt-0.5 text-[11px] text-muted-foreground">— {f.referencia}</p>
                            {f.valor && <p className="mt-1 rounded-sm bg-secondary/60 px-2 py-1 text-[11px] font-medium text-slate-800">{f.valor}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {s.type === "metricas" && (
          <div className="grid grid-cols-2 gap-px border border-border bg-border sm:grid-cols-4" data-testid="report-metricas">
            {(s.items || []).map((m, i) => (
              <div key={i} className="bg-background p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-muted-foreground">{m.label}</p>
                <p className="mt-1 font-mono text-2xl font-light">{m.valor}<span className="text-xs text-muted-foreground"> {m.unidad}</span></p>
              </div>
            ))}
          </div>
        )}

        {s.type === "estancias_resumen" && (
          <div className="overflow-x-auto border border-border" data-testid="report-estancias-resumen">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-secondary/60 text-left uppercase tracking-wide text-muted-foreground">
                  <th className="px-2.5 py-2 font-semibold">Estancia</th><th className="px-2.5 py-2 font-semibold">Planta</th>
                  <th className="px-2.5 py-2 text-right font-semibold">S. útil</th><th className="px-2.5 py-2 text-right font-semibold">S. constr.</th>
                  <th className="px-2.5 py-2 text-right font-semibold">Vol.</th><th className="px-2.5 py-2 font-semibold">Uso</th>
                  <th className="px-2.5 py-2 text-right font-semibold">Ocup.</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {(s.data?.filas || []).map((f, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="px-2.5 py-1.5 font-sans">{f.nombre}</td><td className="px-2.5 py-1.5 font-sans">{f.planta}</td>
                    <td className="px-2.5 py-1.5 text-right">{num(f.sup_util, 2)}</td><td className="px-2.5 py-1.5 text-right">{num(f.sup_construida, 2)}</td>
                    <td className="px-2.5 py-1.5 text-right">{f.volumen ? num(f.volumen, 2) : "—"}</td><td className="px-2.5 py-1.5 font-sans">{f.uso}</td>
                    <td className="px-2.5 py-1.5 text-right">{f.ocupacion}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-border bg-secondary/40 font-mono font-bold">
                  <td className="px-2.5 py-2 font-sans" colSpan={2}>TOTAL</td>
                  <td className="px-2.5 py-2 text-right">{num(s.data?.total_util, 2)}</td>
                  <td className="px-2.5 py-2 text-right">{num(s.data?.total_construida, 2)}</td>
                  <td className="px-2.5 py-2 text-right">{num(s.data?.total_volumen, 2)}</td>
                  <td /><td className="px-2.5 py-2 text-right">{s.data?.total_ocupacion}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        {s.type === "rebt_potencias" && (
          <div className="overflow-x-auto border border-border" data-testid="report-rebt-potencias">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-border bg-secondary/60 text-left uppercase text-muted-foreground">
                <th className="px-2.5 py-2">Cuadro</th><th className="px-2.5">Circuito</th><th className="px-2.5">Tipo</th><th className="px-2.5 text-right">P inst. (W)</th><th className="px-2.5 text-right">F.u.</th><th className="px-2.5 text-right">P cálc. (W)</th>
              </tr></thead>
              <tbody className="font-mono">
                {(s.items || []).map((r, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="px-2.5 py-1.5 font-sans">{r.cuadro}</td><td className="px-2.5 font-sans">{r.circuito}</td><td className="px-2.5 font-sans">{r.tipo}</td>
                    <td className="px-2.5 text-right">{num(r.potencia, 0)}</td><td className="px-2.5 text-right">{r.factor_uso}</td><td className="px-2.5 text-right">{num(r.potencia_calculo, 0)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr className="border-t-2 border-border bg-secondary/40 font-mono font-bold">
                <td className="px-2.5 py-2 font-sans" colSpan={3}>TOTAL</td><td className="px-2.5 text-right">{num(s.total_instalada, 0)}</td><td /><td className="px-2.5 text-right">{num(s.total_calculo, 0)}</td>
              </tr></tfoot>
            </table>
          </div>
        )}

        {s.type === "rebt_esquema" && (
          <div data-testid="report-rebt-esquema"><EsquemaUnifilar arbol={s.arbol} /></div>
        )}

        {s.type === "rebt_lineas" && (
          <div className="overflow-x-auto border border-border" data-testid="report-rebt-lineas">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-border bg-secondary/60 text-left uppercase text-muted-foreground">
                <th className="px-2.5 py-2">Cuadro</th><th className="px-2.5">Línea</th><th className="px-2.5 text-right">Ib</th><th className="px-2.5 text-right">Sección</th><th className="px-2.5 text-right">Iz</th><th className="px-2.5">Protec.</th><th className="px-2.5">Protege cable</th><th className="px-2.5 text-right">Caída ac.</th><th className="px-2.5">Difer.</th><th className="px-2.5 text-right">Tierra</th><th className="px-2.5">Estado</th>
              </tr></thead>
              <tbody className="font-mono">
                {(s.items || []).map((l, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="px-2.5 py-1.5 font-sans">{l.cuadro}</td><td className="px-2.5 font-sans">{l.circuito}</td>
                    <td className="px-2.5 text-right">{l.Ib}</td><td className="px-2.5 text-right">{l.seccion_txt}</td><td className="px-2.5 text-right">{l.iz}</td>
                    <td className="px-2.5 font-sans">{l.proteccion}</td>
                    <td className="px-2.5 font-sans">{l.coordinacion ? (l.protege_cable ? "Sí ✓" : "Revisar") : "—"}</td>
                    <td className="px-2.5 text-right">{l.caida_acum_pct}%</td>
                    <td className="px-2.5 font-sans">{l.diferencial}</td><td className="px-2.5 text-right">{l.tierra}</td>
                    <td className={`px-2.5 font-sans ${l.estado === "no_cumple" ? "font-semibold text-red-700" : l.estado === "observaciones" ? "text-amber-700" : "text-emerald-700"}`}>{l.estado === "no_cumple" ? "No cumple" : l.estado === "observaciones" ? "Revisar" : "Cumple"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="border-t border-border px-2.5 py-2 text-[11px] text-muted-foreground">Coordinación protección↔cable (ITC-BT-22): Ib ≤ In ≤ Iz e I2 ≤ 1,45·Iz.</p>
          </div>
        )}

        {s.type === "rebt_cortocircuito" && (
          <div className="overflow-x-auto border border-border" data-testid="report-rebt-cortocircuito">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-border bg-secondary/60 text-left uppercase text-muted-foreground">
                <th className="px-2.5 py-2">Cuadro</th><th className="px-2.5">Línea</th><th className="px-2.5 text-right">Icc máx (A)</th><th className="px-2.5 text-right">Icc mín (A)</th><th className="px-2.5 text-right">Im (A)</th><th className="px-2.5">P. corte</th><th className="px-2.5">Térmico</th><th className="px-2.5">Disparo</th><th className="px-2.5">Protege CC</th>
              </tr></thead>
              <tbody className="font-mono">
                {(s.items || []).map((l, i) => {
                  const c = l.cortocircuito || {};
                  const yn = (ok) => (ok ? "Sí ✓" : "No ✗");
                  return (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-2.5 py-1.5 font-sans">{l.cuadro}</td><td className="px-2.5 font-sans">{l.circuito}</td>
                      <td className="px-2.5 text-right">{num(c.icc_max_a, 0)}</td><td className="px-2.5 text-right">{num(c.icc_min_a, 0)}</td>
                      <td className="px-2.5 text-right">{num(c.im_a, 0)}</td>
                      <td className={`px-2.5 font-sans ${c.pdc_ok ? "text-emerald-700" : "text-amber-800 font-semibold"}`}>{yn(c.pdc_ok)}</td>
                      <td className={`px-2.5 font-sans ${c.termico_ok ? "text-emerald-700" : "text-amber-800 font-semibold"}`}>{yn(c.termico_ok)}</td>
                      <td className={`px-2.5 font-sans ${c.magnetico_ok ? "text-emerald-700" : "text-amber-800 font-semibold"}`}>{yn(c.magnetico_ok)}</td>
                      <td className={`px-2.5 font-sans ${c.protege_cc ? "text-emerald-700" : "text-amber-800 font-semibold"}`}>{yn(c.protege_cc)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="border-t border-border px-2.5 py-2 text-[11px] text-muted-foreground">Poder de corte ≥ Icc máx · k²·S² ≥ I²t · Icc mín ≥ Im (disparo magnético). Icc por método simplificado (Guía BT-22), orientativo.</p>
          </div>
        )}

        {s.type === "secciones_modulo" && (
          <div className="space-y-4" data-testid="report-secciones-modulo">
            {(s.items || []).map((sec) => {
              const badge = sec.estado === "cumple" ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                : sec.estado === "no_cumple" ? "border-red-300 bg-red-50 text-red-800"
                  : sec.estado === "observaciones" ? "border-amber-300 bg-amber-50 text-amber-800"
                    : "border-slate-300 bg-slate-50 text-slate-600";
              const lbl = sec.estado === "cumple" ? "Cumple" : sec.estado === "no_cumple" ? "No cumple" : sec.estado === "observaciones" ? "Revisar" : "Info";
              return (
                <div key={sec.id} className="border border-border" data-testid={`report-seccion-${sec.id}`}>
                  <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-3 py-2">
                    <span className="font-medium">{sec.titulo}</span>
                    <span className={`rounded-sm border px-2 py-0.5 text-xs font-medium ${badge}`}>{lbl}</span>
                  </div>
                  {sec.descripcion && <p className="px-3 pt-2 text-xs text-muted-foreground">{sec.descripcion}</p>}
                  <div className="p-1.5">
                    {(sec.items || []).map((it, i) => (
                      <div key={i} className="flex items-start justify-between gap-3 px-1.5 py-1">
                        <span>{it.nombre}</span>
                        <span className={`text-right font-mono text-xs ${it.estado === "no_cumple" ? "font-semibold text-red-700" : it.estado === "cumple" ? "font-semibold text-emerald-700" : "text-muted-foreground"}`}>{it.detalle}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
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
  const { data: project } = useQuery({ queryKey: ["project", study?.project_id], enabled: !!study?.project_id, queryFn: () => api.get(`/projects/${study.project_id}`).then((r) => r.data) });
  const qc = useQueryClient();
  const recomputeMut = useMutation({
    mutationFn: () => api.post(`/studies/${studyId}/compute`).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["study", studyId] }); setActiveReport(null); toast.success("Informe recalculado"); },
    onError: (e) => toast.error(apiError(e)),
  });

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

      {isSurfacesOutdated(study, project) && (
        <div className="mb-4 no-print"><SurfacesOutdatedBanner pending={recomputeMut.isPending} onRecompute={() => recomputeMut.mutate()} /></div>
      )}

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
