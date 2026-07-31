import { useEffect, useRef } from "react";
import { DynamicField } from "@/features/studies/components/DynamicField";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Límites de caída de tensión precargados por tipo de instalación (ITC-BT-14/15/19/25).
// El usuario puede editarlos después. DI 1 % con contadores concentrados; 1,5 % un único usuario.
const CDT_PRESETS = {
  vivienda_basica:     { caida_max_di: 1.5, caida_max_circuito: 3, caida_max_total_alumbrado: 3, caida_max_total_otros: 5 },
  vivienda_elevada:    { caida_max_di: 1.5, caida_max_circuito: 3, caida_max_total_alumbrado: 3, caida_max_total_otros: 5 },
  local_comercial:     { caida_max_di: 1.5, caida_max_circuito: 3, caida_max_total_alumbrado: 3, caida_max_total_otros: 5 },
  publica_concurrencia:{ caida_max_di: 1.5, caida_max_circuito: 3, caida_max_total_alumbrado: 3, caida_max_total_otros: 5 },
  garaje:              { caida_max_di: 1.5, caida_max_circuito: 3, caida_max_total_alumbrado: 3, caida_max_total_otros: 5 },
  industrial:          { caida_max_di: 1.5, caida_max_circuito: 4.5, caida_max_total_alumbrado: 4.5, caida_max_total_otros: 6.5 },
  otro:                { caida_max_di: 1.5, caida_max_circuito: 3, caida_max_total_alumbrado: 3, caida_max_total_otros: 5 },
};

// Paso «Datos generales» del REBT: al elegir el tipo de instalación precarga los
// límites normativos de caída de tensión (editables después).
export function RebtGeneralesStep({ step, data, setData }) {
  useEffect(() => {
    const t = data.tipo_instalacion || "otro";
    if (data.caida_max_total_alumbrado == null || data.caida_max_total_alumbrado === "") {
      setData((d) => ({ ...d, ...CDT_PRESETS[t] }));
    }
  }, []); // eslint-disable-line

  const onFieldChange = (f, v) => {
    if (f.name === "tipo_instalacion") {
      const preset = CDT_PRESETS[v] || CDT_PRESETS.otro;
      setData((d) => ({ ...d, tipo_instalacion: v, ...preset }));
      return;
    }
    setData((d) => ({ ...d, [f.name]: v }));
  };

  const cdtFields = new Set(["caida_max_lga", "caida_max_di", "caida_max_circuito", "caida_max_total_alumbrado", "caida_max_total_otros"]);
  const generales = step.fields.filter((f) => !cdtFields.has(f.name));
  const cdt = step.fields.filter((f) => cdtFields.has(f.name));

  return (
    <div className="space-y-5" data-testid="rebt-generales-step">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {generales.map((f) => (
          <div key={f.name} className={f.full ? "sm:col-span-2" : ""}>
            <DynamicField field={f} value={data[f.name]} onChange={(v) => onFieldChange(f, v)} testidPrefix="field" />
          </div>
        ))}
      </div>
      <div className="border border-border bg-secondary/20 p-4">
        <p className="mb-3 text-sm font-semibold">Límites de caída de tensión (ITC-BT-19/25)</p>
        <p className="mb-3 text-xs text-muted-foreground">
          Se precargan según el tipo de instalación (alumbrado 3 % / otros usos 5 % desde el origen; 4,5 % / 6,5 % con
          transformador propio). La DI admite 1 % con contadores concentrados o 1,5 % para un único usuario sin LGA. Edítalos si tu caso lo requiere.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {cdt.map((f) => (
            <div key={f.name}>
              <DynamicField field={f} value={data[f.name]} onChange={(v) => onFieldChange(f, v)} testidPrefix="field" />
            </div>
          ))}
        </div>
      </div>

      <div className="border border-border bg-secondary/20 p-4" data-testid="rebt-cc-config">
        <p className="mb-3 text-sm font-semibold">Cortocircuito (ITC-BT-22)</p>
        <p className="mb-3 text-xs text-muted-foreground">
          Parámetros para la comprobación frente a cortocircuitos (poder de corte, k²·S² ≥ I²t e Icc mín ≥ Im). La Icc se
          estima por el método simplificado de la Guía BT-22 a partir de la Icc presunta en el origen. Valores orientativos.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div>
            <Label className="text-xs">Aislamiento del cable</Label>
            <Select value={data.aislamiento || "PVC"} onValueChange={(v) => setData((d) => ({ ...d, aislamiento: v }))}>
              <SelectTrigger className="mt-1 h-9" data-testid="field-aislamiento"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="PVC">PVC (k: Cu 115 / Al 76)</SelectItem>
                <SelectItem value="XLPE">XLPE/EPR (k: Cu 143 / Al 94)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Curva del magnetotérmico</Label>
            <Select value={data.curva || "C"} onValueChange={(v) => setData((d) => ({ ...d, curva: v }))}>
              <SelectTrigger className="mt-1 h-9" data-testid="field-curva"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="B">B (Im = 5·In)</SelectItem>
                <SelectItem value="C">C (Im = 10·In)</SelectItem>
                <SelectItem value="D">D (Im = 20·In)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Icc presunta en origen (A)</Label>
            <Input type="number" className="mt-1 h-9 font-mono" placeholder="p. ej. 6000" value={data.icc_origen_a ?? ""} onChange={(e) => setData((d) => ({ ...d, icc_origen_a: e.target.value }))} data-testid="field-icc-origen" />
          </div>
          <div>
            <Label className="text-xs">Poder de corte (kA)</Label>
            <Input type="number" className="mt-1 h-9 font-mono" placeholder="6 / 10" value={data.poder_corte_ka ?? ""} onChange={(e) => setData((d) => ({ ...d, poder_corte_ka: e.target.value }))} data-testid="field-poder-corte" />
          </div>
        </div>
      </div>
    </div>
  );
}
