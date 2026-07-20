import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { CiTableDialog } from "@/features/studies/components/CiTableDialog";
import { num } from "@/lib/format";

const CUSTOM = "__custom__";

function DepFireEditor({ dep, index, catalog, ciTable, onChange }) {
  const cat = catalog.find((c) => c.category === dep.actividad_cat);
  const isCustom = dep.actividad_cat === CUSTOM;
  const almacen = dep.modo === "almacenamiento";
  const patch = (p) => onChange({ ...dep, ...p });

  const selectCategoria = (value) => {
    if (value === CUSTOM) patch({ actividad_cat: CUSTOM, subactividad: "" });
    else patch({ actividad_cat: value, subactividad: "", qsi: undefined, qvi: undefined });
  };
  const selectSub = (idx) => {
    const s = cat.subactivities[Number(idx)];
    patch({
      subactividad: s.name, modo: s.modo,
      qsi: s.modo === "produccion" ? s.qsi : undefined,
      qvi: s.modo === "almacenamiento" ? s.qvi : undefined,
      ci: s.ci, ra: s.ra, rmin: s.rmin ?? (s.ra > 1 ? s.ra : null),
    });
  };

  const s = Number(dep.sup_construida) || 0;
  const aporte = almacen
    ? (Number(dep.qvi) || 0) * (Number(dep.ci) || 0) * (Number(dep.hi) || 0) * s
    : (Number(dep.qsi) || 0) * (Number(dep.ci) || 0) * s;

  return (
    <div className="border border-border" data-testid={`fire-dep-${index}`}>
      <div className="flex items-center justify-between border-b border-border bg-secondary/40 px-3 py-2">
        <span className="text-sm font-medium">{dep.nombre || "Dependencia"}</span>
        <Badge variant="outline" className="rounded-sm font-mono text-xs">{num(s, 2)} m²</Badge>
      </div>
      <div className="space-y-3 p-3">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Actividad principal (Tabla 1.3.5)</Label>
            <Select value={dep.actividad_cat || ""} onValueChange={selectCategoria}>
              <SelectTrigger className="rounded-sm" data-testid={`fire-${index}-cat`}><SelectValue placeholder="Selecciona categoría" /></SelectTrigger>
              <SelectContent>
                {catalog.map((c) => <SelectItem key={c.category} value={c.category}>{c.category}</SelectItem>)}
                <SelectItem value={CUSTOM}>+ Actividad personalizada</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Subactividad</Label>
            {isCustom ? (
              <Input value={dep.subactividad || ""} onChange={(e) => patch({ subactividad: e.target.value })} placeholder="Descripción" data-testid={`fire-${index}-sub`} />
            ) : (
              <Select value={cat ? String(cat.subactivities.findIndex((x) => x.name === dep.subactividad)) : ""} onValueChange={selectSub} disabled={!cat}>
                <SelectTrigger className="rounded-sm" data-testid={`fire-${index}-sub`}><SelectValue placeholder="Selecciona subactividad" /></SelectTrigger>
                <SelectContent>
                  {(cat?.subactivities || []).map((x, i) => <SelectItem key={i} value={String(i)}>{x.name}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="space-y-1.5">
            <Label>Tipo</Label>
            <Select value={dep.modo || "produccion"} onValueChange={(v) => patch({ modo: v })}>
              <SelectTrigger className="rounded-sm" data-testid={`fire-${index}-modo`}><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="produccion">Producción</SelectItem>
                <SelectItem value="almacenamiento">Almacenamiento</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>{almacen ? "qvi (MJ/m³)" : "qsi (MJ/m²)"}</Label>
            <Input type="number" min={0} value={(almacen ? dep.qvi : dep.qsi) ?? ""} data-testid={`fire-${index}-densidad`}
              onChange={(e) => patch(almacen ? { qvi: e.target.value === "" ? "" : Number(e.target.value) } : { qsi: e.target.value === "" ? "" : Number(e.target.value) })} />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Ci</Label>
              <CiTableDialog ciTable={ciTable} current={Number(dep.ci)} onSelect={(ci) => patch({ ci })} />
            </div>
            <Input type="number" min={0} step={0.01} value={dep.ci ?? ""} data-testid={`fire-${index}-ci`}
              onChange={(e) => patch({ ci: e.target.value === "" ? "" : Number(e.target.value) })} />
          </div>
          {almacen && (
            <div className="space-y-1.5">
              <Label>Altura hi (m)</Label>
              <Input type="number" min={0} step={0.1} value={dep.hi ?? ""} data-testid={`fire-${index}-hi`}
                onChange={(e) => patch({ hi: e.target.value === "" ? "" : Number(e.target.value) })} />
            </div>
          )}
        </div>
        <div className="flex items-center justify-between border-t border-border pt-2 text-xs">
          <span className="text-muted-foreground">Ra actividad: <span className="font-mono">{dep.ra ? num(dep.ra, 1) : "—"}</span>{dep.rmin ? <span className="ml-2 text-amber-700">Rmin {num(dep.rmin, 1)}</span> : null}</span>
          <span className="font-mono">Aporte: <span className="font-semibold">{num(aporte)} MJ</span></span>
        </div>
      </div>
    </div>
  );
}

export function CargaFuegoStep({ data, setData, catalog = [], ciTable = [] }) {
  const sectores = data.sectores || [];
  const deps = data.dependencias || [];

  const updateSector = (id, patch) =>
    setData((d) => ({ ...d, sectores: d.sectores.map((s) => (s.id === id ? { ...s, ...patch } : s)) }));
  const updateDep = (nd) =>
    setData((d) => ({ ...d, dependencias: d.dependencias.map((x) => (x.id === nd.id ? nd : x)) }));

  if (sectores.length === 0)
    return <p className="border border-dashed border-border py-8 text-center text-sm text-muted-foreground" data-testid="carga-empty">Primero crea sectores y dependencias.</p>;

  return (
    <div className="space-y-8" data-testid="carga-fuego-step">
      {sectores.map((s, si) => {
        const secDeps = deps.filter((x) => x.sector_id === s.id);
        const exterior = s.tipo === "area_exterior";
        return (
          <div key={s.id} className="border border-border" data-testid={`carga-sector-${si}`}>
            <div className="flex items-center justify-between border-b border-border bg-foreground px-4 py-2.5 text-background">
              <span className="font-heading text-sm">{s.nombre}</span>
              <Badge variant="secondary" className="rounded-sm text-xs">{exterior ? "Área exterior (D)" : `Config ${s.config || data.establecimiento?.config || "C"}`}</Badge>
            </div>

            {/* Sector parameters */}
            <div className="grid grid-cols-2 gap-4 border-b border-border p-4 sm:grid-cols-3">
              {!exterior && (
                <div className="space-y-1.5">
                  <Label>Situación</Label>
                  <Select value={s.situacion || "sobre_rasante"} onValueChange={(v) => updateSector(s.id, { situacion: v })}>
                    <SelectTrigger className="rounded-sm" data-testid={`carga-${si}-situacion`}><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sobre_rasante">Sobre rasante</SelectItem>
                      <SelectItem value="bajo_rasante">Bajo rasante (sótano)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="space-y-1.5">
                <Label>Nº salidas de evacuación</Label>
                <Input type="number" min={1} value={s.num_salidas ?? 2} data-testid={`carga-${si}-salidas`}
                  onChange={(e) => updateSector(s.id, { num_salidas: e.target.value === "" ? "" : Number(e.target.value) })} />
              </div>
              <div className="space-y-1.5">
                <Label>Ra del sector (opcional)</Label>
                <Input type="number" min={0} step={0.1} value={s.ra ?? ""} placeholder="auto (máx.)" data-testid={`carga-${si}-ra`}
                  onChange={(e) => updateSector(s.id, { ra: e.target.value === "" ? "" : Number(e.target.value) })} />
              </div>
              {!exterior && (
                <>
                  <div className="space-y-1.5">
                    <Label>Altura evacuación (m)</Label>
                    <Input type="number" min={0} step={0.5} value={s.altura_evacuacion ?? 0} data-testid={`carga-${si}-altura`}
                      onChange={(e) => updateSector(s.id, { altura_evacuacion: e.target.value === "" ? "" : Number(e.target.value) })} />
                  </div>
                  <label className="flex items-center gap-2 pt-6 text-sm" data-testid={`carga-${si}-fachada`}>
                    <Switch checked={!!s.fachada_accesible} onCheckedChange={(v) => updateSector(s.id, { fachada_accesible: v })} />
                    Fachada accesible ≥ 50%
                  </label>
                  <label className="flex items-center gap-2 pt-6 text-sm" data-testid={`carga-${si}-rociadores`}>
                    <Switch checked={!!s.rociadores} onCheckedChange={(v) => updateSector(s.id, { rociadores: v })} />
                    Rociadores en todo el sector
                  </label>
                </>
              )}
            </div>

            {/* Dependencies fire load */}
            <div className="space-y-3 p-4">
              {secDeps.length === 0 ? (
                <p className="text-sm text-muted-foreground">Sin dependencias asignadas a este sector.</p>
              ) : secDeps.map((d) => {
                const globalIdx = deps.findIndex((x) => x.id === d.id);
                return <DepFireEditor key={d.id} dep={d} index={globalIdx} catalog={catalog} ciTable={ciTable} onChange={updateDep} />;
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
