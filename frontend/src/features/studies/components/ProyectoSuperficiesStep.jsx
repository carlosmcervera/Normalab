import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Layers, Download, Upload } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { NumberInput } from "@/components/NumberInput";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { num } from "@/lib/format";
import { SharedTableAlert } from "@/features/studies/components/SharedTableAlert";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const SIN = "__sin__";

const baseFrom = (d) => ({
  id: d.id, nombre: d.nombre || "", planta: d.planta || "",
  sup_util: d.sup_util ?? "", sup_construida: d.sup_construida ?? "", altura: d.altura ?? "",
  uso_ocupacion: d.uso_ocupacion || "", densidad: d.densidad ?? "",
  sin_ocupacion: !!d.sin_ocupacion, ocupacion_custom: !!d.ocupacion_custom, ocupacion_manual: d.ocupacion_manual ?? "",
});

// Paso 1 · Cuadro de superficies agrupado por planta (plantas como entidad gestionable).
// El cuadro base (superficies/ocupación) es COMPARTIDO por el expediente: se importa
// automáticamente de project.estancias al abrir y se reenvía (debounce) al editarlo.
export function ProyectoSuperficiesStep({ data, setData, study }) {
  const deps = data.dependencias || [];
  const plantas = data.plantas || [];
  const [nuevaPlanta, setNuevaPlanta] = useState("");
  const [syncing, setSyncing] = useState(false);
  const projectId = study?.project_id;
  const queryClient = useQueryClient();

  const { data: shared } = useQuery({
    queryKey: ["estancias", projectId],
    queryFn: () => api.get(`/projects/${projectId}/estancias`).then((r) => r.data),
    enabled: !!projectId,
    staleTime: 0,
  });

  // Fusión inicial (una vez): trae del cuadro compartido las estancias y plantas que falten y
  // actualiza los campos base de las existentes, preservando los campos propios de Incendios.
  const mergedRef = useRef(false);
  useEffect(() => {
    if (!shared || mergedRef.current) return;
    mergedRef.current = true;
    const sharedEst = shared.estancias || [];
    const sharedPla = shared.plantas || [];
    setData((d) => {
      const byId = new Map((d.dependencias || []).map((x) => [x.id, x]));
      const plByName = new Map((d.plantas || []).map((p) => [p.nombre, p]));
      sharedPla.forEach((p) => {
        const prev = plByName.get(p.nombre) || { id: p.id || genId(), nombre: p.nombre };
        plByName.set(p.nombre, { ...prev, nombre: p.nombre, rasante: p.rasante || prev.rasante || "sobre", altura: p.altura ?? prev.altura ?? "" });
      });
      let plantasNext = Array.from(plByName.values());
      const pn = new Set(plantasNext.map((p) => p.nombre));
      sharedEst.forEach((e) => {
        const prev = byId.get(e.id) || { id: e.id, modo: "produccion", ci: 1.44 };
        byId.set(e.id, {
          ...prev,
          nombre: e.nombre ?? prev.nombre ?? "", planta: e.planta ?? prev.planta ?? "",
          sup_util: e.sup_util ?? prev.sup_util ?? "", sup_construida: e.sup_construida ?? prev.sup_construida ?? "",
          altura: e.altura ?? prev.altura, densidad: e.densidad ?? prev.densidad,
          uso_ocupacion: e.uso_ocupacion ?? prev.uso_ocupacion, sin_ocupacion: e.sin_ocupacion ?? prev.sin_ocupacion,
        });
        if (e.planta && !pn.has(e.planta)) { pn.add(e.planta); plantasNext = [...plantasNext, { id: genId(), nombre: e.planta, rasante: "sobre", altura: "" }]; }
      });
      return { ...d, dependencias: Array.from(byId.values()), plantas: plantasNext };
    });
  }, [shared]); // eslint-disable-line

  // Autoguardado del cuadro base al compartido (debounce), sin re-fusionar (evita bucles).
  const pushTimer = useRef(null);
  const lastPushSig = useRef(null);
  useEffect(() => {
    if (!projectId || !mergedRef.current) return;
    const base = (data.dependencias || []).map(baseFrom);
    const pl = (data.plantas || []).map((p) => ({ id: p.id, nombre: p.nombre, rasante: p.rasante || "sobre", altura: p.altura ?? "" }));
    const sig = JSON.stringify({ e: base, p: pl });
    if (sig === lastPushSig.current) return;
    clearTimeout(pushTimer.current);
    pushTimer.current = setTimeout(async () => {
      try {
        lastPushSig.current = sig;
        await api.put(`/projects/${projectId}/estancias`, { estancias: base, plantas: pl });
        queryClient.invalidateQueries({ queryKey: ["estancias", projectId] });
        queryClient.invalidateQueries({ queryKey: ["project", projectId] });
        queryClient.invalidateQueries({ queryKey: ["studies", projectId] });
      } catch (e) { /* silencioso: reintenta en el próximo cambio */ }
    }, 800);
    return () => clearTimeout(pushTimer.current);
  }, [data.dependencias, data.plantas, projectId]); // eslint-disable-line

  const importarCuadro = async () => {
    setSyncing(true);
    try {
      const { data: res } = await api.get(`/projects/${projectId}/estancias`);
      const estancias = res.estancias || [];
      if (!estancias.length) { toast.info("El cuadro del expediente está vacío."); return; }
      setData((d) => {
        const byId = new Map((d.dependencias || []).map((x) => [x.id, x]));
        estancias.forEach((e) => {
          const prev = byId.get(e.id) || { id: e.id, modo: "produccion", ci: 1.44 };
          byId.set(e.id, {
            ...prev, nombre: e.nombre || prev.nombre || "", planta: e.planta || prev.planta || "",
            sup_util: e.sup_util ?? prev.sup_util ?? "", sup_construida: e.sup_construida ?? prev.sup_construida ?? "",
            densidad: e.densidad ?? prev.densidad, uso_ocupacion: e.uso_ocupacion ?? prev.uso_ocupacion,
            sin_ocupacion: e.sin_ocupacion ?? prev.sin_ocupacion,
          });
        });
        const nombres = new Set((d.plantas || []).map((p) => p.nombre));
        const nuevasPlantas = [...(d.plantas || [])];
        estancias.forEach((e) => { if (e.planta && !nombres.has(e.planta)) { nombres.add(e.planta); nuevasPlantas.push({ id: genId(), nombre: e.planta }); } });
        return { ...d, dependencias: Array.from(byId.values()), plantas: nuevasPlantas };
      });
      toast.success(`Importadas ${estancias.length} estancias del cuadro del expediente.`);
    } catch (e) { toast.error(apiError(e)); } finally { setSyncing(false); }
  };

  const enviarCuadro = async () => {
    setSyncing(true);
    try {
      const estancias = (data.dependencias || []).map((d) => ({
        id: d.id, nombre: d.nombre || "", planta: d.planta || "",
        sup_util: d.sup_util ?? "", sup_construida: d.sup_construida ?? "", altura: d.altura ?? "",
        uso_ocupacion: d.uso_ocupacion || "", densidad: d.densidad ?? "",
        sin_ocupacion: !!d.sin_ocupacion, ocupacion_custom: !!d.ocupacion_custom, ocupacion_manual: d.ocupacion_manual ?? "",
      }));
      await api.put(`/projects/${projectId}/estancias`, { estancias });
      toast.success("Cuadro del expediente actualizado con estas estancias.");
    } catch (e) { toast.error(apiError(e)); } finally { setSyncing(false); }
  };

  const addDep = (planta = "") =>
    setData((d) => ({
      ...d,
      dependencias: [...(d.dependencias || []), {
        id: genId(), nombre: "", etiqueta: "", planta, grupo: "",
        sup_util: "", sup_construida: "", modo: "produccion", ci: 1.44,
      }],
    }));
  const updateDep = (id, patch) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === id ? { ...x, ...patch } : x)) }));
  const removeDep = (id) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.filter((x) => x.id !== id) }));

  const addPlanta = () => {
    const nombre = nuevaPlanta.trim();
    if (!nombre || plantas.some((p) => p.nombre === nombre)) return;
    setData((d) => ({ ...d, plantas: [...(d.plantas || []), { id: genId(), nombre, rasante: "sobre", altura: "" }] }));
    setNuevaPlanta("");
  };
  const updatePlanta = (id, patch) =>
    setData((d) => ({ ...d, plantas: (d.plantas || []).map((p) => (p.id === id ? { ...p, ...patch } : p)) }));
  const renamePlanta = (id, nombre) =>
    setData((d) => {
      const old = (d.plantas || []).find((p) => p.id === id)?.nombre;
      return {
        ...d,
        plantas: (d.plantas || []).map((p) => (p.id === id ? { ...p, nombre } : p)),
        dependencias: (d.dependencias || []).map((x) => (x.planta === old ? { ...x, planta: nombre } : x)),
      };
    });
  const removePlanta = (id) =>
    setData((d) => {
      const target = (d.plantas || []).find((p) => p.id === id)?.nombre;
      return {
        ...d,
        plantas: (d.plantas || []).filter((p) => p.id !== id),
        dependencias: (d.dependencias || []).map((x) => (x.planta === target ? { ...x, planta: "" } : x)),
      };
    });

  const nombresPlanta = plantas.map((p) => p.nombre);
  const groups = [
    ...plantas.map((p) => ({ key: p.nombre, label: p.nombre, filas: deps.filter((x) => x.planta === p.nombre) })),
    { key: SIN, label: "Sin planta asignada", filas: deps.filter((x) => !x.planta || !nombresPlanta.includes(x.planta)) },
  ].filter((g) => g.key !== SIN || g.filas.length > 0);

  const totalU = deps.reduce((a, x) => a + (Number(x.sup_util) || 0), 0);
  const totalC = deps.reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);

  return (
    <div className="space-y-5" data-testid="superficies-proyecto-step">
      <SharedTableAlert projectId={projectId} currentStudyId={study?.id} />
      <div className="border border-border bg-secondary/20 p-4" data-testid="plantas-manager">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold"><Layers className="h-4 w-4" /> Plantas del proyecto</div>
        <div className="flex flex-wrap items-center gap-2">
          {plantas.map((p) => (
            <div key={p.id} className="flex items-end gap-1 border border-border bg-background p-2" data-testid={`planta-${p.id}`}>
              <div>
                <label className="text-[10px] uppercase text-muted-foreground">Nombre</label>
                <Input className="h-7 w-24 rounded-sm text-sm" value={p.nombre}
                  onChange={(e) => renamePlanta(p.id, e.target.value)} data-testid={`planta-${p.id}-nombre`} />
              </div>
              <div>
                <label className="text-[10px] uppercase text-muted-foreground">Rasante</label>
                <Select value={p.rasante || "sobre"} onValueChange={(v) => updatePlanta(p.id, { rasante: v })}>
                  <SelectTrigger className="h-7 w-32 rounded-sm text-xs" data-testid={`planta-${p.id}-rasante`}><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="sobre">Sobre rasante</SelectItem><SelectItem value="bajo">Bajo rasante</SelectItem></SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-[10px] uppercase text-muted-foreground">Altura (m)</label>
                <NumberInput min={0} className="h-7 w-16 rounded-sm text-right font-mono text-xs" value={p.altura ?? ""} onChange={(v) => updatePlanta(p.id, { altura: v })} data-testid={`planta-${p.id}-altura`} />
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removePlanta(p.id)} data-testid={`remove-planta-${p.id}`}><Trash2 className="h-3.5 w-3.5" /></Button>
            </div>
          ))}
          <div className="flex items-center gap-1">
            <Input className="h-8 w-36 rounded-sm" placeholder="Nueva planta (ej. Baja)" value={nuevaPlanta}
              onChange={(e) => setNuevaPlanta(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addPlanta()} data-testid="new-planta-input" />
            <Button variant="outline" size="sm" className="rounded-sm" onClick={addPlanta} data-testid="add-planta"><Plus className="h-4 w-4" /></Button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">Estancias agrupadas por planta. Asigna cada estancia a su planta; los sectores se definen en el paso siguiente.</p>
        <div className="flex items-center gap-2">
          {projectId && (
            <>
              <Button variant="outline" size="sm" className="rounded-sm" onClick={importarCuadro} disabled={syncing} data-testid="import-cuadro">
                <Download className="mr-1.5 h-4 w-4" /> Importar del cuadro
              </Button>
              <Button variant="outline" size="sm" className="rounded-sm" onClick={enviarCuadro} disabled={syncing} data-testid="push-cuadro">
                <Upload className="mr-1.5 h-4 w-4" /> Actualizar cuadro
              </Button>
            </>
          )}
          <Button variant="outline" size="sm" className="rounded-sm shrink-0" onClick={() => addDep(plantas[0]?.nombre || "")} data-testid="add-dependencia">
            <Plus className="mr-1.5 h-4 w-4" /> Añadir estancia
          </Button>
        </div>
      </div>

      {deps.length === 0 ? (
        <p className="border border-dashed border-border py-10 text-center text-sm text-muted-foreground">Sin estancias. Añade la primera para empezar el cuadro de superficies.</p>
      ) : (
        <div className="overflow-x-auto border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-3 py-2 font-semibold">Estancia</th>
                <th className="px-3 py-2 font-semibold">Etiqueta</th>
                <th className="px-3 py-2 font-semibold">Planta</th>
                <th className="px-3 py-2 text-right font-semibold">S. útil (m²)</th>
                <th className="px-3 py-2 text-right font-semibold">S. construida (m²)</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => {
                const gu = g.filas.reduce((a, x) => a + (Number(x.sup_util) || 0), 0);
                const gc = g.filas.reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);
                return (
                  <GroupRows key={g.key} label={g.label} filas={g.filas} gu={gu} gc={gc} deps={deps}
                    plantas={plantas} updateDep={updateDep} removeDep={removeDep} addDep={addDep}
                    groupPlanta={g.key === SIN ? "" : g.key} />
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-border bg-secondary/40 font-mono text-sm font-bold">
                <td className="px-3 py-2 font-sans" colSpan={3}>TOTAL ({deps.length} estancias)</td>
                <td className="px-3 py-2 text-right" data-testid="total-util">{num(totalU, 2)}</td>
                <td className="px-3 py-2 text-right" data-testid="total-construida">{num(totalC, 2)}</td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}

function GroupRows({ label, filas, gu, gc, deps, plantas, updateDep, removeDep, addDep, groupPlanta }) {
  const nombres = plantas.map((p) => p.nombre);
  return (
    <>
      <tr className="bg-secondary/25">
        <td colSpan={6} className="px-3 py-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-foreground/80" data-testid={`planta-group-${label}`}>{label} · {filas.length} estancia(s)</span>
            <Button variant="ghost" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => addDep(groupPlanta)} data-testid={`add-dep-planta-${label}`}><Plus className="mr-1 h-3 w-3" /> Añadir aquí</Button>
          </div>
        </td>
      </tr>
      {filas.map((x) => {
        const i = deps.indexOf(x);
        return (
          <tr key={x.id} className="border-b border-border" data-testid={`dep-row-${i}`}>
            <td className="px-3 py-1.5"><Input className="h-8 rounded-sm" value={x.nombre || ""} onChange={(e) => updateDep(x.id, { nombre: e.target.value })} placeholder="Nombre" data-testid={`dep-${i}-nombre`} /></td>
            <td className="px-3 py-1.5"><Input className="h-8 w-32 rounded-sm" value={x.etiqueta || ""} onChange={(e) => updateDep(x.id, { etiqueta: e.target.value })} placeholder="Ref./EN" data-testid={`dep-${i}-etiqueta`} /></td>
            <td className="px-3 py-1.5">
              <Select value={nombres.includes(x.planta) ? x.planta : SIN} onValueChange={(v) => updateDep(x.id, { planta: v === SIN ? "" : v })}>
                <SelectTrigger className="h-8 w-32 rounded-sm" data-testid={`dep-${i}-planta`}><SelectValue /></SelectTrigger>
                <SelectContent>
                  {plantas.map((p) => <SelectItem key={p.id} value={p.nombre}>{p.nombre}</SelectItem>)}
                  <SelectItem value={SIN}>Sin planta</SelectItem>
                </SelectContent>
              </Select>
            </td>
            <td className="px-3 py-1.5"><NumberInput min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.sup_util ?? ""} onChange={(v) => updateDep(x.id, { sup_util: v })} data-testid={`dep-${i}-util`} /></td>
            <td className="px-3 py-1.5"><NumberInput min={0} className="h-8 w-24 rounded-sm text-right font-mono" value={x.sup_construida ?? ""} onChange={(v) => updateDep(x.id, { sup_construida: v })} data-testid={`dep-${i}-construida`} /></td>
            <td className="px-3 py-1.5"><Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => removeDep(x.id)} data-testid={`remove-dep-${i}`}><Trash2 className="h-4 w-4" /></Button></td>
          </tr>
        );
      })}
      {filas.length > 0 && (
        <tr className="border-b border-border bg-secondary/10 font-mono text-xs">
          <td className="px-3 py-1.5 font-sans italic text-muted-foreground" colSpan={3}>Subtotal {label}</td>
          <td className="px-3 py-1.5 text-right font-semibold" data-testid={`subtotal-util-${label}`}>{num(gu, 2)}</td>
          <td className="px-3 py-1.5 text-right font-semibold" data-testid={`subtotal-construida-${label}`}>{num(gc, 2)}</td>
          <td />
        </tr>
      )}
    </>
  );
}
