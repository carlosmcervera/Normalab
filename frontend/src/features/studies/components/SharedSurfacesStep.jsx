import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Loader2, Layers, Check, Download } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { NumberInput } from "@/components/NumberInput";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { num } from "@/lib/format";
import { SharedTableAlert } from "@/features/studies/components/SharedTableAlert";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const SIN = "__sin__";

const ocupacionDe = (e) => {
  if (e.sin_ocupacion) return 0;
  if (e.ocupacion_custom && e.ocupacion_manual !== "" && e.ocupacion_manual != null) return Math.ceil(Number(e.ocupacion_manual) || 0);
  const dens = Number(e.densidad);
  if (!dens || dens <= 0) return null;
  const sup = Number(e.sup_util) || Number(e.sup_construida) || 0;
  return sup <= 0 ? 0 : Math.ceil(sup / dens);
};

// Cuadro de superficies + ocupación COMPARTIDO por el expediente (project.estancias + project.plantas).
// Fuente única, agrupado por plantas (con sobre/bajo rasante y altura). Autosave + invalidación.
export function SharedSurfacesStep({ projectId, studyId, hideOccupancy = false }) {
  const qc = useQueryClient();
  const [downloading, setDownloading] = useState("");
  const showOcc = !hideOccupancy;
  const descargar = async (fmt) => {
    setDownloading(fmt);
    try {
      const res = await api.get(`/projects/${projectId}/estancias/export/${fmt}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `cuadro_superficies.${fmt === "xlsx" ? "xlsx" : "pdf"}`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setDownloading("");
    }
  };
  const { data, isLoading } = useQuery({
    queryKey: ["estancias", projectId],
    queryFn: () => api.get(`/projects/${projectId}/estancias`).then((r) => r.data),
    enabled: !!projectId,
    staleTime: 0,
  });
  const [estancias, setEstancias] = useState(null);
  const [plantas, setPlantas] = useState(null);
  const [nuevaPlanta, setNuevaPlanta] = useState("");
  const [saved, setSaved] = useState(false);
  const timer = useRef(null);
  const dirty = useRef(false);
  const appliedSig = useRef(null);

  useEffect(() => {
    if (!data) return;
    const sig = JSON.stringify({ e: data.estancias || [], p: data.plantas || [] });
    if (estancias === null || (!dirty.current && sig !== appliedSig.current)) {
      const est = data.estancias || [];
      const srvPl = data.plantas || [];
      const seeded = srvPl.length ? srvPl
        : [...new Set(est.map((e) => e.planta).filter(Boolean))].map((n) => ({ id: genId(), nombre: n, rasante: "sobre", altura: "" }));
      setEstancias(est);
      setPlantas(seeded);
      appliedSig.current = sig;
    }
  }, [data, estancias]);

  useEffect(() => {
    if (!dirty.current || estancias === null) return;
    setSaved(false);
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      await api.put(`/projects/${projectId}/estancias`, { estancias, plantas });
      dirty.current = false;
      appliedSig.current = JSON.stringify({ e: estancias, p: plantas });
      setSaved(true);
      qc.invalidateQueries({ queryKey: ["estancias", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["studies", projectId] });
    }, 700);
    return () => clearTimeout(timer.current);
  }, [estancias, plantas, projectId]); // eslint-disable-line

  const mutE = (fn) => { dirty.current = true; setEstancias((e) => fn(e || [])); };
  const mutP = (fn) => { dirty.current = true; setPlantas((p) => fn(p || [])); };

  const addEstancia = (planta = "") => mutE((e) => [...e, { id: genId(), nombre: "", planta, sup_util: "", sup_construida: "", altura: "", uso_ocupacion: "", densidad: "" }]);
  const upd = (id, patch) => mutE((e) => e.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  const rm = (id) => mutE((e) => e.filter((x) => x.id !== id));

  const addPlanta = () => {
    const nombre = nuevaPlanta.trim();
    if (!nombre || (plantas || []).some((p) => p.nombre === nombre)) return;
    mutP((p) => [...p, { id: genId(), nombre, rasante: "sobre", altura: "" }]);
    setNuevaPlanta("");
  };
  const updPlanta = (id, patch) => {
    if (patch.nombre !== undefined) {
      const old = (plantas || []).find((p) => p.id === id)?.nombre;
      mutE((e) => e.map((x) => (x.planta === old ? { ...x, planta: patch.nombre } : x)));
    }
    mutP((p) => p.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  };
  const rmPlanta = (id) => {
    const target = (plantas || []).find((p) => p.id === id)?.nombre;
    mutE((e) => e.map((x) => (x.planta === target ? { ...x, planta: "" } : x)));
    mutP((p) => p.filter((x) => x.id !== id));
  };

  if (isLoading || estancias === null) return <div className="flex justify-center py-10"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;

  const nombresPlanta = (plantas || []).map((p) => p.nombre);
  const groups = [
    ...(plantas || []).map((p) => ({ key: p.id, planta: p, filas: estancias.filter((x) => x.planta === p.nombre) })),
    { key: SIN, planta: null, filas: estancias.filter((x) => !x.planta || !nombresPlanta.includes(x.planta)) },
  ].filter((g) => g.key !== SIN || g.filas.length > 0);

  const totalU = estancias.reduce((a, x) => a + (Number(x.sup_util) || 0), 0);
  const totalC = estancias.reduce((a, x) => a + (Number(x.sup_construida) || 0), 0);
  const totalO = estancias.reduce((a, x) => a + (ocupacionDe(x) || 0), 0);

  const cols = (
    <thead>
      <tr className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
        <th className="px-2 py-2 font-semibold">Estancia</th>
        <th className="px-2 py-2 text-right font-semibold">S. útil</th>
        <th className="px-2 py-2 text-right font-semibold">S. constr.</th>
        <th className="px-2 py-2 text-right font-semibold">Altura</th>
        {showOcc && <th className="px-2 py-2 font-semibold">Uso</th>}
        {showOcc && <th className="px-2 py-2 text-right font-semibold">m²/pers.</th>}
        {showOcc && <th className="px-2 py-2 text-right font-semibold">Ocup.</th>}
        <th className="px-2 py-2 font-semibold">Planta</th>
        <th className="px-2 py-2" />
      </tr>
    </thead>
  );

  const row = (x, i) => (
    <tr key={x.id} className="border-b border-border" data-testid={`estancia-row-${i}`}>
      <td className="px-2 py-1.5"><Input className="h-8 rounded-sm" value={x.nombre || ""} onChange={(e) => upd(x.id, { nombre: e.target.value })} placeholder="Nombre" data-testid={`estancia-${i}-nombre`} /></td>
      <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-20 rounded-sm text-right font-mono" value={x.sup_util ?? ""} onChange={(v) => upd(x.id, { sup_util: v })} data-testid={`estancia-${i}-util`} /></td>
      <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-20 rounded-sm text-right font-mono" value={x.sup_construida ?? ""} onChange={(v) => upd(x.id, { sup_construida: v })} data-testid={`estancia-${i}-construida`} /></td>
      <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-16 rounded-sm text-right font-mono" value={x.altura ?? ""} onChange={(v) => upd(x.id, { altura: v })} data-testid={`estancia-${i}-altura`} /></td>
      {showOcc && <td className="px-2 py-1.5"><Input className="h-8 w-28 rounded-sm" value={x.uso_ocupacion || ""} onChange={(e) => upd(x.id, { uso_ocupacion: e.target.value })} placeholder="Uso" data-testid={`estancia-${i}-uso`} /></td>}
      {showOcc && <td className="px-2 py-1.5"><NumberInput min={0} className="h-8 w-16 rounded-sm text-right font-mono" value={x.densidad ?? ""} onChange={(v) => upd(x.id, { densidad: v })} data-testid={`estancia-${i}-densidad`} /></td>}
      {showOcc && <td className="px-2 py-1.5 text-right font-mono text-xs" data-testid={`estancia-${i}-ocup`}>{ocupacionDe(x) == null ? "—" : ocupacionDe(x)}</td>}
      <td className="px-2 py-1.5">
        <Select value={x.planta || SIN} onValueChange={(v) => upd(x.id, { planta: v === SIN ? "" : v })}>
          <SelectTrigger className="h-8 w-32 rounded-sm text-xs" data-testid={`estancia-${i}-planta`}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value={SIN}>Sin planta</SelectItem>
            {(plantas || []).map((p) => <SelectItem key={p.id} value={p.nombre}>{p.nombre}</SelectItem>)}
          </SelectContent>
        </Select>
      </td>
      <td className="px-2 py-1.5"><Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => rm(x.id)} data-testid={`remove-estancia-${x.id}`}><Trash2 className="h-4 w-4" /></Button></td>
    </tr>
  );

  let idx = -1;
  return (
    <div className="space-y-4" data-testid="shared-surfaces-step">
      <SharedTableAlert projectId={projectId} currentStudyId={studyId} />

      {/* Gestor de plantas */}
      <div className="border border-border bg-secondary/20 p-4" data-testid="plantas-manager">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold"><Layers className="h-4 w-4" /> Plantas del expediente</div>
        <div className="flex flex-wrap items-end gap-2">
          {(plantas || []).map((p) => (
            <div key={p.id} className="flex items-end gap-1 border border-border bg-background p-2" data-testid={`planta-${p.id}`}>
              <div>
                <label className="text-[10px] uppercase text-muted-foreground">Nombre</label>
                <Input className="h-7 w-24 rounded-sm text-sm" value={p.nombre} onChange={(e) => updPlanta(p.id, { nombre: e.target.value })} data-testid={`planta-${p.id}-nombre`} />
              </div>
              <div>
                <label className="text-[10px] uppercase text-muted-foreground">Rasante</label>
                <Select value={p.rasante || "sobre"} onValueChange={(v) => updPlanta(p.id, { rasante: v })}>
                  <SelectTrigger className="h-7 w-32 rounded-sm text-xs" data-testid={`planta-${p.id}-rasante`}><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="sobre">Sobre rasante</SelectItem><SelectItem value="bajo">Bajo rasante</SelectItem></SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-[10px] uppercase text-muted-foreground">Altura (m)</label>
                <NumberInput min={0} className="h-7 w-16 rounded-sm text-right font-mono text-xs" value={p.altura ?? ""} onChange={(v) => updPlanta(p.id, { altura: v })} data-testid={`planta-${p.id}-altura`} />
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => rmPlanta(p.id)} data-testid={`remove-planta-${p.id}`}><Trash2 className="h-3.5 w-3.5" /></Button>
            </div>
          ))}
          <div className="flex items-center gap-1">
            <Input className="h-8 w-36 rounded-sm" placeholder="Nueva planta (ej. Baja)" value={nuevaPlanta} onChange={(e) => setNuevaPlanta(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addPlanta()} data-testid="new-planta-input" />
            <Button variant="outline" size="sm" className="rounded-sm" onClick={addPlanta} data-testid="add-planta"><Plus className="h-4 w-4" /></Button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Layers className="h-4 w-4" /> Cuadro compartido del expediente, agrupado por planta. Se guarda automáticamente y lo comparten todos los módulos.
          {saved && <span className="inline-flex items-center gap-1 text-emerald-600"><Check className="h-3.5 w-3.5" /> Guardado</span>}
        </p>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="rounded-sm text-xs" onClick={() => descargar("xlsx")} disabled={!!downloading || estancias.length === 0} data-testid="download-master-xlsx">
            {downloading === "xlsx" ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Download className="mr-1.5 h-3.5 w-3.5" />}Excel
          </Button>
          <Button variant="outline" size="sm" className="rounded-sm text-xs" onClick={() => descargar("pdf")} disabled={!!downloading || estancias.length === 0} data-testid="download-master-pdf">
            {downloading === "pdf" ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Download className="mr-1.5 h-3.5 w-3.5" />}PDF
          </Button>
        </div>
      </div>

      {estancias.length === 0 && (plantas || []).length === 0 ? (
        <p className="border border-dashed border-border py-10 text-center text-sm text-muted-foreground" data-testid="estancias-empty">Sin estancias. Crea una planta y añade la primera estancia para construir el cuadro de superficies.</p>
      ) : (
        <div className="space-y-4">
          {groups.map((g) => (
            <div key={g.key} className="overflow-x-auto border border-border">
              <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-3 py-2">
                <span className="text-sm font-semibold">
                  {g.planta ? g.planta.nombre : "Sin planta asignada"}
                  {g.planta && <span className="ml-2 text-xs font-normal text-muted-foreground">{g.planta.rasante === "bajo" ? "Bajo rasante" : "Sobre rasante"}{g.planta.altura ? ` · ${num(g.planta.altura)} m` : ""}</span>}
                </span>
                {g.planta && <Button variant="outline" size="sm" className="h-7 rounded-sm text-xs" onClick={() => addEstancia(g.planta.nombre)} data-testid={`add-estancia-${g.planta.id}`}><Plus className="mr-1 h-3.5 w-3.5" />Estancia</Button>}
              </div>
              <table className="w-full text-sm">
                {cols}
                <tbody>{g.filas.map((x) => { idx += 1; return row(x, idx); })}</tbody>
              </table>
            </div>
          ))}
          <div className="flex items-center justify-between border border-border bg-secondary/40 px-3 py-2 font-mono text-sm font-bold">
            <span className="font-sans">TOTAL ({estancias.length} estancias)</span>
            <span className="flex gap-6">
              <span data-testid="shared-total-util">S. útil {num(totalU, 2)}</span>
              <span data-testid="shared-total-construida">S. constr. {num(totalC, 2)}</span>
              {showOcc && <span data-testid="shared-total-ocup">Ocup. {totalO}</span>}
            </span>
          </div>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={() => addEstancia("")} data-testid="add-estancia"><Plus className="mr-1.5 h-4 w-4" /> Añadir estancia sin planta</Button>
        </div>
      )}
    </div>
  );
}
