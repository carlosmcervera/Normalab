import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Trash2, ChevronRight, CircuitBoard } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { NumberInput } from "@/components/NumberInput";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const TIPOS = [
  { value: "alumbrado", label: "Alumbrado" }, { value: "tomas", label: "Tomas de corriente" },
  { value: "fuerza", label: "Fuerza" }, { value: "motor", label: "Motor" },
  { value: "clima", label: "Climatización" }, { value: "otros", label: "Otros" },
];
const fieldLabel = "text-[11px] uppercase tracking-wide text-muted-foreground";

const newCarga = () => ({ id: genId(), nombre: "", tipo: "tomas", potencia: "", cosphi: 0.9, factor_uso: 1, longitud: "", estancia: "", diferencial_id: "" });
const newDif = () => ({ id: genId(), nombre: "Diferencial", sensibilidad: 30 });
const newBoard = (raiz) => ({ id: genId(), nombre: raiz ? "Cuadro general" : "Subcuadro", longitud: raiz ? 10 : 5, simultaneidad: 1, cosphi: 0.9, sensibilidad_general: 300, cargas: [newCarga()], diferenciales: [newDif()], subcuadros: [] });

// Recursión SOLO en JS (evita el desbordamiento de Babel con auto-referencia en JSX).
function collect(board, path, depth, raiz, out) {
  out.push({ board, path, depth, raiz });
  (board.subcuadros || []).forEach((sc, i) => collect(sc, [...path, i], depth + 1, false, out));
}
function updateAt(root, path, fn) {
  if (path.length === 0) return fn(root);
  const [i, ...rest] = path;
  return { ...root, subcuadros: (root.subcuadros || []).map((s, idx) => (idx === i ? updateAt(s, rest, fn) : s)) };
}
function removeAt(root, path) {
  const parent = path.slice(0, -1);
  const idx = path[path.length - 1];
  return updateAt(root, parent, (b) => ({ ...b, subcuadros: (b.subcuadros || []).filter((_, i) => i !== idx) }));
}

export function RebtCuadroStep({ data, setData, study }) {
  const projectId = study?.project_id;
  const { data: estancias = [] } = useQuery({
    queryKey: ["estancias", projectId],
    queryFn: () => api.get(`/projects/${projectId}/estancias`).then((r) => r.data.estancias || []),
    enabled: !!projectId,
  });

  useEffect(() => { if (!data.cuadro) setData((d) => ({ ...d, cuadro: newBoard(true) })); }, []); // eslint-disable-line
  if (!data.cuadro) return null;

  const setRoot = (fn) => setData((d) => ({ ...d, cuadro: fn(d.cuadro) }));
  const patchBoard = (path, patch) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, ...patch })));
  const patchCarga = (path, cid, patch) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, cargas: b.cargas.map((c) => (c.id === cid ? { ...c, ...patch } : c)) })));
  const addCarga = (path) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, cargas: [...b.cargas, newCarga()] })));
  const rmCarga = (path, cid) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, cargas: b.cargas.filter((c) => c.id !== cid) })));
  const addDif = (path) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, diferenciales: [...(b.diferenciales || []), newDif()] })));
  const patchDif = (path, did, patch) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, diferenciales: b.diferenciales.map((d) => (d.id === did ? { ...d, ...patch } : d)) })));
  const rmDif = (path, did) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, diferenciales: b.diferenciales.filter((d) => d.id !== did) })));
  const addSub = (path) => setRoot((r) => updateAt(r, path, (b) => ({ ...b, subcuadros: [...(b.subcuadros || []), newBoard(false)] })));
  const rmSub = (path) => setRoot((r) => removeAt(r, path));

  const flat = [];
  collect(data.cuadro, [], 0, true, flat);

  return (
    <div className="space-y-3" data-testid="rebt-cuadro-step">
      <p className="text-sm text-muted-foreground">Define las cargas del cuadro, agrúpalas por diferenciales y añade subcuadros anidados. La potencia de cálculo y todas las líneas se calculan al pulsar «Calcular».</p>
      {flat.map(({ board, path, depth, raiz }) => (
        <div key={board.id} style={{ marginLeft: depth * 16 }} className={`rounded-sm border-2 ${raiz ? "border-orange-300" : "border-blue-300"} bg-background`} data-testid={`board-${board.id}`}>
          <div className="flex flex-wrap items-end gap-2 border-b border-border bg-secondary/40 p-2.5">
            <CircuitBoard className={`h-4 w-4 ${raiz ? "text-orange-500" : "text-blue-500"}`} />
            <div className="min-w-[150px] flex-1"><Label className={fieldLabel}>Nombre del cuadro</Label><Input className="mt-1 h-8 rounded-sm text-sm" value={board.nombre} onChange={(e) => patchBoard(path, { nombre: e.target.value })} data-testid={`board-${board.id}-nombre`} /></div>
            <div className="w-24"><Label className={fieldLabel}>{raiz ? "Long. DI (m)" : "Long. puente"}</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={board.longitud ?? ""} onChange={(v) => patchBoard(path, { longitud: v })} data-testid={`board-${board.id}-longitud`} /></div>
            <div className="w-20"><Label className={fieldLabel}>Simult.</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={board.simultaneidad ?? ""} onChange={(v) => patchBoard(path, { simultaneidad: v })} data-testid={`board-${board.id}-simult`} /></div>
            <div className="w-24"><Label className={fieldLabel}>Dif. gen. mA</Label><NumberInput integer min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={board.sensibilidad_general ?? ""} onChange={(v) => patchBoard(path, { sensibilidad_general: v })} data-testid={`board-${board.id}-difgen`} /></div>
            {!raiz && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => rmSub(path)} data-testid={`rm-sub-${board.id}`}><Trash2 className="h-4 w-4" /></Button>}
          </div>
          <div className="space-y-3 p-2.5">
            <div>
              <div className="mb-1 flex items-center justify-between"><span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Diferenciales</span><Button variant="ghost" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => addDif(path)} data-testid={`board-${board.id}-add-dif`}><Plus className="mr-1 h-3 w-3" />Diferencial</Button></div>
              <div className="flex flex-wrap gap-2">
                {(board.diferenciales || []).map((d) => (
                  <div key={d.id} className="flex items-center gap-1 rounded-sm border border-border bg-secondary/30 px-2 py-1" data-testid={`dif-${d.id}`}>
                    <Input className="h-7 w-24 rounded-sm text-xs" value={d.nombre} onChange={(e) => patchDif(path, d.id, { nombre: e.target.value })} />
                    <Select value={String(d.sensibilidad)} onValueChange={(v) => patchDif(path, d.id, { sensibilidad: Number(v) })}><SelectTrigger className="h-7 w-20 rounded-sm text-xs"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="30">30 mA</SelectItem><SelectItem value="300">300 mA</SelectItem></SelectContent></Select>
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => rmDif(path, d.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between"><span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Cargas / circuitos</span><Button variant="outline" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => addCarga(path)} data-testid={`board-${board.id}-add-carga`}><Plus className="mr-1 h-3 w-3" />Carga</Button></div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs"><thead><tr className="text-left text-[10px] uppercase text-muted-foreground"><th className="px-1 py-1">Circuito</th><th className="px-1">Tipo</th><th className="px-1">P (W)</th><th className="px-1">cosφ</th><th className="px-1">F.u.</th><th className="px-1">L (m)</th><th className="px-1">Estancia</th><th className="px-1">Diferencial</th><th /></tr></thead>
                  <tbody>{board.cargas.map((c) => <CargaRow key={c.id} c={c} board={board} path={path} estancias={estancias} patchCarga={patchCarga} rmCarga={rmCarga} />)}</tbody>
                </table>
              </div>
            </div>
            <Button variant="outline" size="sm" className="rounded-sm text-xs" onClick={() => addSub(path)} data-testid={`board-${board.id}-add-sub`}><Plus className="mr-1 h-3.5 w-3.5" />Añadir subcuadro a «{board.nombre}»</Button>
          </div>
        </div>
      ))}
    </div>
  );
}

function CargaRow({ c, board, path, estancias, patchCarga, rmCarga }) {
  return (
    <tr data-testid={`carga-${c.id}`}>
      <td className="px-1 py-0.5"><Input className="h-7 w-28 rounded-sm text-xs" value={c.nombre} onChange={(e) => patchCarga(path, c.id, { nombre: e.target.value })} data-testid={`carga-${c.id}-nombre`} /></td>
      <td className="px-1"><Select value={c.tipo} onValueChange={(v) => patchCarga(path, c.id, { tipo: v })}><SelectTrigger className="h-7 w-28 rounded-sm text-xs" data-testid={`carga-${c.id}-tipo`}><SelectValue /></SelectTrigger><SelectContent>{TIPOS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></td>
      <td className="px-1"><NumberInput min={0} className="h-7 w-20 rounded-sm font-mono text-xs" value={c.potencia ?? ""} onChange={(v) => patchCarga(path, c.id, { potencia: v })} data-testid={`carga-${c.id}-potencia`} /></td>
      <td className="px-1"><NumberInput min={0} className="h-7 w-14 rounded-sm font-mono text-xs" value={c.cosphi ?? ""} onChange={(v) => patchCarga(path, c.id, { cosphi: v })} /></td>
      <td className="px-1"><NumberInput min={0} className="h-7 w-14 rounded-sm font-mono text-xs" value={c.factor_uso ?? ""} onChange={(v) => patchCarga(path, c.id, { factor_uso: v })} /></td>
      <td className="px-1"><NumberInput min={0} className="h-7 w-16 rounded-sm font-mono text-xs" value={c.longitud ?? ""} onChange={(v) => patchCarga(path, c.id, { longitud: v })} data-testid={`carga-${c.id}-longitud`} /></td>
      <td className="px-1"><Select value={c.estancia || "__none__"} onValueChange={(v) => patchCarga(path, c.id, { estancia: v === "__none__" ? "" : v })}><SelectTrigger className="h-7 w-32 rounded-sm text-xs"><SelectValue placeholder="—" /></SelectTrigger><SelectContent><SelectItem value="__none__">—</SelectItem>{estancias.map((e) => <SelectItem key={e.id} value={e.nombre || e.id}>{e.nombre || "(sin nombre)"}</SelectItem>)}</SelectContent></Select></td>
      <td className="px-1"><Select value={c.diferencial_id || "__none__"} onValueChange={(v) => patchCarga(path, c.id, { diferencial_id: v === "__none__" ? "" : v })}><SelectTrigger className="h-7 w-28 rounded-sm text-xs" data-testid={`carga-${c.id}-dif`}><SelectValue placeholder="—" /></SelectTrigger><SelectContent><SelectItem value="__none__">—</SelectItem>{(board.diferenciales || []).map((d) => <SelectItem key={d.id} value={d.id}>{d.nombre}</SelectItem>)}</SelectContent></Select></td>
      <td className="px-1"><Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => rmCarga(path, c.id)} data-testid={`carga-${c.id}-remove`}><Trash2 className="h-3.5 w-3.5" /></Button></td>
    </tr>
  );
}
