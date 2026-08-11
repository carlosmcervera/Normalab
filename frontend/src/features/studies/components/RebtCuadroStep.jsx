import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Trash2, CircuitBoard, Zap, ShieldPlus, GitBranch } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { NumberInput } from "@/components/NumberInput";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const genId = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2, 10));
const TIPOS = [
  { value: "alumbrado", label: "Alumbrado" }, { value: "tomas", label: "Tomas de corriente" },
  { value: "fuerza", label: "Fuerza" }, { value: "motor", label: "Motor" },
  { value: "clima", label: "Climatización" }, { value: "otros", label: "Otros" },
];
const fieldLabel = "text-[11px] uppercase tracking-wide text-muted-foreground";
const MAGNETOS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250];
const SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240];
const METODOS = [
  { value: "b1", label: "Bajo tubo empotrado (B1)" },
  { value: "b2", label: "Bajo tubo superficie (B2)" },
  { value: "c", label: "Sobre pared / bandeja no perf. (C)" },
  { value: "e", label: "Bandeja perforada (E/F)" },
  { value: "d", label: "Enterrado bajo tubo (D)" },
];
const secTxt = (s) => String(s).replace(".", ",");

const newCarga = (tipo = "tomas") => ({ id: genId(), nombre: "", tipo, potencia: "", cosphi: 0.9, factor_uso: 1, longitud: "", estancia: "" });
const newLinea = () => ({ ...newCarga("tomas"), kind: "linea", dif_propio: false, sensibilidad: 30 });
const newPuente = () => ({ id: genId(), kind: "puente", nombre: "Línea puente", longitud: 5, cosphi: 0.9, simultaneidad: 1, sensibilidad: 30, sublineas: [newCarga("tomas")] });
const newBoard = (raiz) => ({
  id: genId(), nombre: raiz ? "Cuadro general" : "Subcuadro",
  alim: { longitud: raiz ? 10 : 5, caida_max: raiz ? 1.5 : 1, cosphi: 0.9 },
  simultaneidad: 1, diferencial_general: { sensibilidad: 300 },
  spd: { presente: raiz, tipo: "T2" }, lga: { presente: false, longitud: "", caida_max: 0.5 },
  nodos: raiz ? [newLinea()] : [],
});

// Migración del modelo antiguo (cargas/diferenciales/subcuadros) al de nodos.
function migrate(board) {
  if (!board || typeof board !== "object") return newBoard(true);
  if (Array.isArray(board.nodos)) {
    board.nodos.forEach((n) => { if (n.kind === "subcuadro") n.board = migrate(n.board || {}); });
    return board;
  }
  const nodos = [];
  (board.cargas || []).forEach((c) => nodos.push({ ...c, kind: "linea", dif_propio: false, sensibilidad: 30 }));
  (board.subcuadros || []).forEach((sc) => nodos.push({ id: sc.id || genId(), kind: "subcuadro", board: migrate(sc) }));
  return {
    id: board.id || genId(), nombre: board.nombre,
    alim: { longitud: board.longitud, caida_max: board.caida_max, cosphi: board.cosphi ?? 0.9 },
    simultaneidad: board.simultaneidad ?? 1,
    diferencial_general: { sensibilidad: board.sensibilidad_general ?? 300 },
    spd: { presente: false, tipo: "T2" }, lga: { presente: false, longitud: "", caida_max: 0.5 },
    nodos,
  };
}

// Recorre el árbol de cuadros (recursión SOLO en JS) devolviendo una lista plana.
function collect(board, path, depth, raiz, out) {
  out.push({ board, path, depth, raiz });
  (board.nodos || []).forEach((n, i) => { if (n.kind === "subcuadro") collect(n.board, [...path, i], depth + 1, false, out); });
}
function updateBoardAt(root, path, fn) {
  if (path.length === 0) return fn(root);
  const [i, ...rest] = path;
  return { ...root, nodos: (root.nodos || []).map((n, idx) => (idx === i ? { ...n, board: updateBoardAt(n.board, rest, fn) } : n)) };
}

export function RebtCuadroStep({ data, setData, study }) {
  const projectId = study?.project_id;
  const { data: shared = {} } = useQuery({
    queryKey: ["estancias", projectId],
    queryFn: () => api.get(`/projects/${projectId}/estancias`).then((r) => r.data),
    enabled: !!projectId,
    staleTime: 0,
  });
  const estancias = Array.isArray(shared?.estancias) ? shared.estancias : (Array.isArray(shared) ? shared : []);

  useEffect(() => {
    setData((d) => (d.cuadro && Array.isArray(d.cuadro.nodos) ? d : { ...d, cuadro: d.cuadro ? migrate(d.cuadro) : newBoard(true) }));
  }, []); // eslint-disable-line
  if (!data.cuadro || !Array.isArray(data.cuadro.nodos)) return null;

  const setRoot = (fn) => setData((d) => ({ ...d, cuadro: fn(d.cuadro) }));
  const patchBoard = (path, patch) => setRoot((r) => updateBoardAt(r, path, (b) => ({ ...b, ...patch })));
  const patchNode = (path, nid, patch) => setRoot((r) => updateBoardAt(r, path, (b) => ({ ...b, nodos: b.nodos.map((n) => (n.id === nid ? { ...n, ...patch } : n)) })));
  const addNode = (path, node) => setRoot((r) => updateBoardAt(r, path, (b) => ({ ...b, nodos: [...b.nodos, node] })));
  const rmNode = (path, nid) => setRoot((r) => updateBoardAt(r, path, (b) => ({ ...b, nodos: b.nodos.filter((n) => n.id !== nid) })));
  const patchSub = (path, pid, sid, patch) => setRoot((r) => updateBoardAt(r, path, (b) => ({
    ...b, nodos: b.nodos.map((n) => (n.id === pid ? { ...n, sublineas: n.sublineas.map((s) => (s.id === sid ? { ...s, ...patch } : s)) } : n)),
  })));
  const addSub = (path, pid) => setRoot((r) => updateBoardAt(r, path, (b) => ({ ...b, nodos: b.nodos.map((n) => (n.id === pid ? { ...n, sublineas: [...n.sublineas, newCarga()] } : n)) })));
  const rmSub = (path, pid, sid) => setRoot((r) => updateBoardAt(r, path, (b) => ({ ...b, nodos: b.nodos.map((n) => (n.id === pid ? { ...n, sublineas: n.sublineas.filter((s) => s.id !== sid) } : n)) })));
  const rmBoard = (path) => setRoot((r) => {
    const parent = path.slice(0, -1); const idx = path[path.length - 1];
    return updateBoardAt(r, parent, (b) => ({ ...b, nodos: b.nodos.filter((_, i) => i !== idx) }));
  });

  const flat = [];
  collect(data.cuadro, [], 0, true, flat);

  const estOpts = (val, onCh, tid) => (
    <Select value={val || "__none__"} onValueChange={(v) => onCh(v === "__none__" ? "" : v)}>
      <SelectTrigger className="h-7 w-32 rounded-sm text-xs" data-testid={tid}><SelectValue placeholder="—" /></SelectTrigger>
      <SelectContent><SelectItem value="__none__">—</SelectItem>{estancias.map((e) => <SelectItem key={e.id} value={e.nombre || e.id}>{e.nombre || "(sin nombre)"}</SelectItem>)}</SelectContent>
    </Select>
  );

  return (
    <div className="space-y-3" data-testid="rebt-cuadro-step">
      <p className="text-sm text-muted-foreground">Diseña el cuadro: cabecera (IGA + diferencial general + sobretensiones), líneas directas, líneas puente (con sus sublíneas agrupadas) y subcuadros. Todo se dimensiona en cascada al pulsar «Calcular».</p>
      {flat.map(({ board, path, depth, raiz }) => (
        <div key={board.id} style={{ marginLeft: depth * 16 }} className={`rounded-sm border-2 ${raiz ? "border-orange-300" : "border-blue-300"} bg-background`} data-testid={`board-${board.id}`}>
          {/* Cabecera del cuadro */}
          <div className="space-y-2 border-b border-border bg-secondary/40 p-2.5">
            <div className="flex flex-wrap items-end gap-2">
              <CircuitBoard className={`h-4 w-4 ${raiz ? "text-orange-500" : "text-blue-500"}`} />
              <div className="min-w-[150px] flex-1"><Label className={fieldLabel}>Nombre del cuadro</Label><Input className="mt-1 h-8 rounded-sm text-sm" value={board.nombre || ""} onChange={(e) => patchBoard(path, { nombre: e.target.value })} data-testid={`board-${board.id}-nombre`} /></div>
              <div className="w-24"><Label className={fieldLabel}>{raiz ? "Long. DI (m)" : "Long. puente (m)"}</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={board.alim?.longitud ?? ""} onChange={(v) => patchBoard(path, { alim: { ...board.alim, longitud: v } })} data-testid={`board-${board.id}-longitud`} /></div>
              <div className="w-20"><Label className={fieldLabel}>Simult.</Label><NumberInput min={0} className="mt-1 h-8 rounded-sm font-mono text-xs" value={board.simultaneidad ?? ""} onChange={(v) => patchBoard(path, { simultaneidad: v })} data-testid={`board-${board.id}-simult`} /></div>
              <div className="w-24"><Label className={fieldLabel}>Dif. gen. mA</Label>
                <Select value={String(board.diferencial_general?.sensibilidad ?? 300)} onValueChange={(v) => patchBoard(path, { diferencial_general: { sensibilidad: Number(v) } })}>
                  <SelectTrigger className="mt-1 h-8 rounded-sm font-mono text-xs" data-testid={`board-${board.id}-difgen`}><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="30">30 mA</SelectItem><SelectItem value="300">300 mA</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="w-28"><Label className={fieldLabel}>Sección alim.</Label>
                <Select value={board.seccion_manual ? String(board.seccion_manual) : "auto"} onValueChange={(v) => patchBoard(path, { seccion_manual: v === "auto" ? "" : Number(v) })}>
                  <SelectTrigger className="mt-1 h-8 rounded-sm font-mono text-xs" data-testid={`board-${board.id}-seccion`}><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="auto">Auto</SelectItem>{SECCIONES.map((s) => <SelectItem key={s} value={String(s)}>{secTxt(s)} mm²</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="w-44"><Label className={fieldLabel}>Instalación alim.</Label>
                <Select value={board.metodo_instalacion || "b1"} onValueChange={(v) => patchBoard(path, { metodo_instalacion: v })}>
                  <SelectTrigger className="mt-1 h-8 rounded-sm text-xs" data-testid={`board-${board.id}-metodo`}><SelectValue /></SelectTrigger>
                  <SelectContent>{METODOS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              {!raiz && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => rmBoard(path)} data-testid={`rm-sub-${board.id}`}><Trash2 className="h-4 w-4" /></Button>}
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <div className="flex items-center gap-2" data-testid={`board-${board.id}-spd`}>
                <ShieldPlus className="h-3.5 w-3.5 text-emerald-600" />
                <span className="text-xs">Sobretensiones (SPD)</span>
                <Switch checked={!!board.spd?.presente} onCheckedChange={(v) => patchBoard(path, { spd: { ...board.spd, presente: v } })} data-testid={`board-${board.id}-spd-toggle`} />
                {board.spd?.presente && (
                  <Select value={board.spd?.tipo || "T2"} onValueChange={(v) => patchBoard(path, { spd: { ...board.spd, tipo: v } })}>
                    <SelectTrigger className="h-7 w-24 rounded-sm text-xs" data-testid={`board-${board.id}-spd-tipo`}><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="T1">Tipo 1</SelectItem><SelectItem value="T2">Tipo 2</SelectItem><SelectItem value="T1+T2">Tipo 1+2</SelectItem></SelectContent>
                  </Select>
                )}
              </div>
              {raiz && (
                <div className="flex items-center gap-2" data-testid={`board-${board.id}-lga`}>
                  <span className="text-xs">LGA</span>
                  <Switch checked={!!board.lga?.presente} onCheckedChange={(v) => patchBoard(path, { lga: { ...board.lga, presente: v } })} data-testid={`board-${board.id}-lga-toggle`} />
                  {board.lga?.presente && (
                    <div className="flex items-center gap-1"><span className={fieldLabel}>Long. (m)</span><NumberInput min={0} className="h-7 w-20 rounded-sm font-mono text-xs" value={board.lga?.longitud ?? ""} onChange={(v) => patchBoard(path, { lga: { ...board.lga, longitud: v } })} data-testid={`board-${board.id}-lga-long`} /></div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Nodos: líneas directas y líneas puente */}
          <div className="space-y-3 p-2.5">
            <div>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Líneas directas</span>
                <Button variant="outline" size="sm" className="h-6 rounded-sm px-2 text-xs" onClick={() => addNode(path, newLinea())} data-testid={`board-${board.id}-add-linea`}><Plus className="mr-1 h-3 w-3" />Línea</Button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs"><thead><tr className="text-left text-[10px] uppercase text-muted-foreground"><th className="px-1 py-1">Circuito</th><th className="px-1">Tipo</th><th className="px-1">P (W)</th><th className="px-1">cosφ</th><th className="px-1">F.u.</th><th className="px-1">L (m)</th><th className="px-1">Estancia</th><th className="px-1">Dif. propio</th><th className="px-1">Magneto (A)</th><th className="px-1">Sección</th><th className="px-1">Instalación</th><th /></tr></thead>
                  <tbody>{board.nodos.filter((n) => n.kind === "linea").map((n) => (
                    <tr key={n.id} data-testid={`linea-${n.id}`}>
                      <td className="px-1 py-0.5"><Input className="h-7 w-28 rounded-sm text-xs" value={n.nombre || ""} onChange={(e) => patchNode(path, n.id, { nombre: e.target.value })} data-testid={`linea-${n.id}-nombre`} /></td>
                      <td className="px-1"><Select value={n.tipo} onValueChange={(v) => patchNode(path, n.id, { tipo: v })}><SelectTrigger className="h-7 w-28 rounded-sm text-xs" data-testid={`linea-${n.id}-tipo`}><SelectValue /></SelectTrigger><SelectContent>{TIPOS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></td>
                      <td className="px-1"><NumberInput min={0} className="h-7 w-20 rounded-sm font-mono text-xs" value={n.potencia ?? ""} onChange={(v) => patchNode(path, n.id, { potencia: v })} data-testid={`linea-${n.id}-potencia`} /></td>
                      <td className="px-1"><NumberInput min={0} className="h-7 w-14 rounded-sm font-mono text-xs" value={n.cosphi ?? ""} onChange={(v) => patchNode(path, n.id, { cosphi: v })} /></td>
                      <td className="px-1"><NumberInput min={0} className="h-7 w-14 rounded-sm font-mono text-xs" value={n.factor_uso ?? ""} onChange={(v) => patchNode(path, n.id, { factor_uso: v })} /></td>
                      <td className="px-1"><NumberInput min={0} className="h-7 w-16 rounded-sm font-mono text-xs" value={n.longitud ?? ""} onChange={(v) => patchNode(path, n.id, { longitud: v })} data-testid={`linea-${n.id}-longitud`} /></td>
                      <td className="px-1">{estOpts(n.estancia, (v) => patchNode(path, n.id, { estancia: v }), `linea-${n.id}-estancia`)}</td>
                      <td className="px-1"><div className="flex items-center gap-1"><Switch checked={!!n.dif_propio} onCheckedChange={(v) => patchNode(path, n.id, { dif_propio: v })} data-testid={`linea-${n.id}-dif`} />{n.dif_propio && <Select value={String(n.sensibilidad ?? 30)} onValueChange={(v) => patchNode(path, n.id, { sensibilidad: Number(v) })}><SelectTrigger className="h-7 w-16 rounded-sm text-xs"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="30">30</SelectItem><SelectItem value="300">300</SelectItem></SelectContent></Select>}</div></td>
                      <td className="px-1"><Select value={n.magneto_manual ? String(n.magneto_manual) : "auto"} onValueChange={(v) => patchNode(path, n.id, { magneto_manual: v === "auto" ? "" : Number(v) })}><SelectTrigger className="h-7 w-20 rounded-sm text-xs" data-testid={`linea-${n.id}-magneto`}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="auto">Auto</SelectItem>{MAGNETOS.map((m) => <SelectItem key={m} value={String(m)}>{m} A</SelectItem>)}</SelectContent></Select></td>
                      <td className="px-1"><Select value={n.seccion_manual ? String(n.seccion_manual) : "auto"} onValueChange={(v) => patchNode(path, n.id, { seccion_manual: v === "auto" ? "" : Number(v) })}><SelectTrigger className="h-7 w-24 rounded-sm text-xs" data-testid={`linea-${n.id}-seccion`}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="auto">Auto</SelectItem>{SECCIONES.map((s) => <SelectItem key={s} value={String(s)}>{secTxt(s)} mm²</SelectItem>)}</SelectContent></Select></td>
                      <td className="px-1"><Select value={n.metodo_instalacion || "b1"} onValueChange={(v) => patchNode(path, n.id, { metodo_instalacion: v })}><SelectTrigger className="h-7 w-44 rounded-sm text-xs" data-testid={`linea-${n.id}-metodo`}><SelectValue /></SelectTrigger><SelectContent>{METODOS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent></Select></td>
                      <td className="px-1"><Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => rmNode(path, n.id)} data-testid={`linea-${n.id}-remove`}><Trash2 className="h-3.5 w-3.5" /></Button></td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>

            {/* Líneas puente */}
            {board.nodos.filter((n) => n.kind === "puente").map((n) => (
              <div key={n.id} className="rounded-sm border border-purple-300 bg-purple-50/40 p-2" data-testid={`puente-${n.id}`}>
                <div className="mb-2 flex flex-wrap items-end gap-2">
                  <GitBranch className="h-4 w-4 text-purple-600" />
                  <div className="min-w-[130px] flex-1"><Label className={fieldLabel}>Línea puente</Label><Input className="mt-1 h-7 rounded-sm text-xs" value={n.nombre || ""} onChange={(e) => patchNode(path, n.id, { nombre: e.target.value })} data-testid={`puente-${n.id}-nombre`} /></div>
                  <div className="w-20"><Label className={fieldLabel}>Long. (m)</Label><NumberInput min={0} className="mt-1 h-7 rounded-sm font-mono text-xs" value={n.longitud ?? ""} onChange={(v) => patchNode(path, n.id, { longitud: v })} data-testid={`puente-${n.id}-longitud`} /></div>
                  <div className="w-20"><Label className={fieldLabel}>Simult.</Label><NumberInput min={0} className="mt-1 h-7 rounded-sm font-mono text-xs" value={n.simultaneidad ?? ""} onChange={(v) => patchNode(path, n.id, { simultaneidad: v })} /></div>
                  <div className="w-24"><Label className={fieldLabel}>Diferencial mA</Label><Select value={String(n.sensibilidad ?? 30)} onValueChange={(v) => patchNode(path, n.id, { sensibilidad: Number(v) })}><SelectTrigger className="mt-1 h-7 rounded-sm font-mono text-xs" data-testid={`puente-${n.id}-dif`}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="30">30 mA</SelectItem><SelectItem value="300">300 mA</SelectItem></SelectContent></Select></div>
                  <div className="w-28"><Label className={fieldLabel}>Sección</Label><Select value={n.seccion_manual ? String(n.seccion_manual) : "auto"} onValueChange={(v) => patchNode(path, n.id, { seccion_manual: v === "auto" ? "" : Number(v) })}><SelectTrigger className="mt-1 h-7 rounded-sm font-mono text-xs" data-testid={`puente-${n.id}-seccion`}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="auto">Auto</SelectItem>{SECCIONES.map((s) => <SelectItem key={s} value={String(s)}>{secTxt(s)} mm²</SelectItem>)}</SelectContent></Select></div>
                  <div className="w-44"><Label className={fieldLabel}>Instalación</Label><Select value={n.metodo_instalacion || "b1"} onValueChange={(v) => patchNode(path, n.id, { metodo_instalacion: v })}><SelectTrigger className="mt-1 h-7 rounded-sm text-xs" data-testid={`puente-${n.id}-metodo`}><SelectValue /></SelectTrigger><SelectContent>{METODOS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent></Select></div>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => rmNode(path, n.id)} data-testid={`puente-${n.id}-remove`}><Trash2 className="h-4 w-4" /></Button>
                </div>
                <div className="overflow-x-auto rounded-sm border border-border bg-background">
                  <table className="w-full text-xs"><thead><tr className="text-left text-[10px] uppercase text-muted-foreground"><th className="px-1 py-1">Sublínea</th><th className="px-1">Tipo</th><th className="px-1">P (W)</th><th className="px-1">cosφ</th><th className="px-1">F.u.</th><th className="px-1">L (m)</th><th className="px-1">Estancia</th><th /></tr></thead>
                    <tbody>{n.sublineas.map((s) => (
                      <tr key={s.id} data-testid={`subl-${s.id}`}>
                        <td className="px-1 py-0.5"><Input className="h-7 w-28 rounded-sm text-xs" value={s.nombre || ""} onChange={(e) => patchSub(path, n.id, s.id, { nombre: e.target.value })} data-testid={`subl-${s.id}-nombre`} /></td>
                        <td className="px-1"><Select value={s.tipo} onValueChange={(v) => patchSub(path, n.id, s.id, { tipo: v })}><SelectTrigger className="h-7 w-28 rounded-sm text-xs"><SelectValue /></SelectTrigger><SelectContent>{TIPOS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></td>
                        <td className="px-1"><NumberInput min={0} className="h-7 w-20 rounded-sm font-mono text-xs" value={s.potencia ?? ""} onChange={(v) => patchSub(path, n.id, s.id, { potencia: v })} data-testid={`subl-${s.id}-potencia`} /></td>
                        <td className="px-1"><NumberInput min={0} className="h-7 w-14 rounded-sm font-mono text-xs" value={s.cosphi ?? ""} onChange={(v) => patchSub(path, n.id, s.id, { cosphi: v })} /></td>
                        <td className="px-1"><NumberInput min={0} className="h-7 w-14 rounded-sm font-mono text-xs" value={s.factor_uso ?? ""} onChange={(v) => patchSub(path, n.id, s.id, { factor_uso: v })} /></td>
                        <td className="px-1"><NumberInput min={0} className="h-7 w-16 rounded-sm font-mono text-xs" value={s.longitud ?? ""} onChange={(v) => patchSub(path, n.id, s.id, { longitud: v })} data-testid={`subl-${s.id}-longitud`} /></td>
                        <td className="px-1">{estOpts(s.estancia, (v) => patchSub(path, n.id, s.id, { estancia: v }), `subl-${s.id}-estancia`)}</td>
                        <td className="px-1"><Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => rmSub(path, n.id, s.id)} data-testid={`subl-${s.id}-remove`}><Trash2 className="h-3.5 w-3.5" /></Button></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
                <Button variant="ghost" size="sm" className="mt-1 h-6 rounded-sm px-2 text-xs" onClick={() => addSub(path, n.id)} data-testid={`puente-${n.id}-add-subl`}><Plus className="mr-1 h-3 w-3" />Sublínea</Button>
              </div>
            ))}

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" className="rounded-sm text-xs" onClick={() => addNode(path, newPuente())} data-testid={`board-${board.id}-add-puente`}><GitBranch className="mr-1 h-3.5 w-3.5" />Añadir línea puente</Button>
              <Button variant="outline" size="sm" className="rounded-sm text-xs" onClick={() => addNode(path, { id: genId(), kind: "subcuadro", board: newBoard(false) })} data-testid={`board-${board.id}-add-sub`}><Plus className="mr-1 h-3.5 w-3.5" />Añadir subcuadro</Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
