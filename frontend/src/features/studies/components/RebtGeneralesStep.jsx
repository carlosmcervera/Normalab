import { useEffect, useRef } from "react";
import { DynamicField } from "@/features/studies/components/DynamicField";

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
    </div>
  );
}
