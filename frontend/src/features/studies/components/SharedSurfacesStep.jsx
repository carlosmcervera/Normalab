import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Loader2, Layers, Check } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { NumberInput } from "@/components/NumberInput";
import { num } from "@/lib/format";
import { SharedTableAlert } from "@/features/studies/components/SharedTableAlert";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));

const ocupacionDe = (e) => {
  if (e.sin_ocupacion) return 0;
  if (e.ocupacion_custom && e.ocupacion_manual !== "" && e.ocupacion_manual != null) return Math.ceil(Number(e.ocupacion_manual) || 0);
  const dens = Number(e.densidad);
  if (!dens || dens <= 0) return null;
  const sup = Number(e.sup_util) || Number(e.sup_construida) || 0;
  return sup <= 0 ? 0 : Math.ceil(sup / dens);
};

// Cuadro de superficies + ocupación COMPARTIDO por el expediente (project.estancias).
// Fuente única, editable desde cualquier módulo o desde el expediente. Autosave con debounce
// + invalidación para que los cambios se reflejen en el resto de módulos al instante.
export function SharedSurfacesStep({ projectId, studyId }) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["estancias", projectId],
    queryFn: () => api.get(`/projects/${projectId}/estancias`).then((r) => r.data.estancias || []),
    enabled: !!projectId,
    staleTime: 0,
  });
  const [estancias, setEstancias] = useState(null);
  const [saved, setSaved] = useState(false);
  const timer = useRef(null);
  const dirty = useRef(false);
  const appliedSig = useRef(null);

  // Adopta los datos del servidor al montar y cuando cambian externamente (si no hay edición pendiente).
  useEffect(() => {
    if (!data) return;
    const sig = JSON.stringify(data);
    if (estancias === null || (!dirty.current && sig !== appliedSig.current)) {
      setEstancias(data);
      appliedSig.current = sig;
    }
  }, [data, estancias]);

  useEffect(() => {
    if (!dirty.current || estancias === null) return;
    setSaved(false);
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      await api.put(`/projects/${projectId}/estancias`, { estancias });
      dirty.current = false;
      appliedSig.current = JSON.stringify(estancias);
      setSaved(true);
      qc.invalidateQueries({ queryKey: ["estancias", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["studies", projectId] });
    }, 700);
    return () => clearTimeout(timer.current);
  }, [estancias, projectId]); // eslint-disable-line

  const mutate = (fn) => { dirty.current = true; setEstancias((e) => fn(e || [])); };
  const add = () => mutate((e) => [...e, { id: genId(), nombre: "", planta: "", sup_util: "", sup_construida: "", altura: "", uso_ocupacion: "", densidad: "" }]);
  const upd = (id, patch) => mutate((e) => e.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  const rm = (id) => mutate((e) => e.filter((x) => x.id !== id));

  if (isLoading || estancias === null) return <div className="flex justify-center py-10"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;

  const totalU = estancias.reduce((a, x) => a + (Number(x.sup_util) || 0), 0);
  const totalC = estancias.reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);
  const totalO = estancias.reduce((a, x) => a + (ocupacionDe(x) || 0), 0);

  return (
    <div className="space-y-4" data-testid="shared-surfaces-step">
      <SharedTableAlert projectId={projectId} currentStudyId={studyId} />
      <div className="flex items-center justify-between">
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Layers className="h-4 w-4" /> Cuadro compartido del expediente. Los cambios se guardan automáticamente y los comparten todos los módulos.
          {saved && <span className="inline-flex items-center gap-1 text-emerald-600"><Check className="h-3.5 w-3.5" /> Guardado</span>}
        </p>
        <Button variant="outline" size="sm" className="rounded-sm shrink-0" onClick={add} data-testid="add-estancia">
          <Plus className="mr-1.5 h-4 w-4" /> Añadir estancia
        </Button>
      </div>

      {estancias.length === 0 ? (
        <p className="border border-dashed border-border py-10 text-center text-sm text-muted-foreground" data-testid="estancias-empty">Sin estancias. Añade la primera para crear el cuadro de superficies del expediente.</p>
      ) : (
        <div className="overflow-x-auto border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-2 py-2 font-semibold">Estancia</th>
                <th className="px-2 py-2 font-semibold">Planta</th>
                <th className="px-2 py-2 text-right font-semibold">S. útil</th>
                <th className="px-2 py-2 text-right font-semibold">S. constr.</th>
                <th className="px-2 py-2 text-right font-semibold">Altura</th>
                <th className="px-2 py-2 font-semibold">Uso</th>
                <th className="px-2 py-2 text-right font-semibold">m²/pers.</th>
                <th className="px-2 py-2 text-right font-semibold">Ocup.</th>
                <th className="px-2 py-2" />
              </tr>
            </thead>
            <tbody>
              {estancias.map((x, i) => (
                <tr key={x.id} className="border-b border-border" data-testid={`estancia-row-${i}`}>
                  <td className="px-2 py-1.5"><Input className="h-8 rounded-sm" value={x.nombre || ""} onChange={(e) => upd(x.id, { nombre: e.target.value })} placeholder="Nombre" data-testid={`estancia-${i}-nombre`} /></td>
                  <td className="px-2 py-1.5"><Input className="h-8 w-24 rounded-sm" value={x.planta || ""} onChange={(e) => upd(x.id, { planta: e.target.value })} placeholder="Planta" data-testid={`estancia-${i}-planta`} /></td>
                  <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-20 rounded-sm text-right font-mono" value={x.sup_util ?? ""} onChange={(v) => upd(x.id, { sup_util: v })} data-testid={`estancia-${i}-util`} /></td>
                  <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-20 rounded-sm text-right font-mono" value={x.sup_construida ?? ""} onChange={(v) => upd(x.id, { sup_construida: v })} data-testid={`estancia-${i}-construida`} /></td>
                  <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-16 rounded-sm text-right font-mono" value={x.altura ?? ""} onChange={(v) => upd(x.id, { altura: v })} data-testid={`estancia-${i}-altura`} /></td>
                  <td className="px-2 py-1.5"><Input className="h-8 w-28 rounded-sm" value={x.uso_ocupacion || ""} onChange={(e) => upd(x.id, { uso_ocupacion: e.target.value })} placeholder="Uso" data-testid={`estancia-${i}-uso`} /></td>
                  <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-16 rounded-sm text-right font-mono" value={x.densidad ?? ""} onChange={(v) => upd(x.id, { densidad: v })} data-testid={`estancia-${i}-densidad`} /></td>
                  <td className="px-2 py-1.5 text-right font-mono text-xs" data-testid={`estancia-${i}-ocup`}>{ocupacionDe(x) == null ? "—" : ocupacionDe(x)}</td>
                  <td className="px-2 py-1.5"><Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => rm(x.id)} data-testid={`remove-estancia-${i}`}><Trash2 className="h-4 w-4" /></Button></td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-border bg-secondary/40 font-mono text-sm font-bold">
                <td className="px-2 py-2 font-sans" colSpan={2}>TOTAL ({estancias.length})</td>
                <td className="px-2 py-2 text-right" data-testid="shared-total-util">{num(totalU, 2)}</td>
                <td className="px-2 py-2 text-right" data-testid="shared-total-construida">{num(totalC, 2)}</td>
                <td colSpan={3} />
                <td className="px-2 py-2 text-right" data-testid="shared-total-ocup">{totalO}</td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
