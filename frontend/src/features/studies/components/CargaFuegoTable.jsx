import { num } from "@/lib/format";

const MODO = { produccion: "Producción", almacenamiento: "Almacenamiento", deposito: "Depósito" };

// Tabla detallada de cálculo de la carga de fuego ponderada (RSCIEI Anexo I) por sector:
// actividad/zona, modo, Ci, densidad qsi/qvi, hi/volumen, superficie y aporte parcial.
export function CargaFuegoTable({ calculo, categoria }) {
  const zonas = calculo?.zonas || [];
  if (!zonas.length) return null;
  return (
    <div className="border-t border-border px-4 py-3" data-testid="carga-fuego-table">
      <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Cálculo de la carga de fuego (RSCIEI Anexo I)</p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-left text-[10px] uppercase text-muted-foreground">
              <th className="px-2 py-1.5">Actividad / zona</th>
              <th className="px-2 py-1.5">Modo</th>
              <th className="px-2 py-1.5 text-right">Ci</th>
              <th className="px-2 py-1.5 text-right">qsi / qvi</th>
              <th className="px-2 py-1.5 text-right">hi / Vol</th>
              <th className="px-2 py-1.5 text-right">Sup. (m²)</th>
              <th className="px-2 py-1.5 text-right">Parcial (MJ)</th>
            </tr>
          </thead>
          <tbody>
            {zonas.map((z, i) => (
              <tr key={i} className="border-b border-border/60" data-testid={`carga-zona-${i}`}>
                <td className="px-2 py-1.5">{z.descripcion}{z.combustible ? ` · ${z.combustible}` : ""}</td>
                <td className="px-2 py-1.5">{MODO[z.modo] || z.modo}</td>
                <td className="px-2 py-1.5 text-right font-mono">{num(z.ci, 2)}</td>
                <td className="px-2 py-1.5 text-right font-mono">
                  {z.modo === "almacenamiento" ? `${num(z.qvi)} MJ/m³`
                    : z.modo === "deposito" ? `PCI ${num(z.pci)}·ρ ${num(z.dens_comb)}`
                      : `${num(z.qsi)} MJ/m²`}
                </td>
                <td className="px-2 py-1.5 text-right font-mono">
                  {z.modo === "almacenamiento" ? `${num(z.hi)} m`
                    : z.modo === "deposito" ? `${num(z.volumen)} m³` : "—"}
                </td>
                <td className="px-2 py-1.5 text-right font-mono">{num(z.superficie, 2)}</td>
                <td className="px-2 py-1.5 text-right font-mono">{num(z.aporte, 0)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border font-mono text-[11px] font-semibold">
              <td className="px-2 py-1.5" colSpan={5}>Σ(qi·Ci·Si) = {num(calculo.numerador, 0)} MJ · A = {num(calculo.A, 2)} m² · Ra = {num(calculo.ra, 2)}</td>
              <td className="px-2 py-1.5 text-right">Qs =</td>
              <td className="px-2 py-1.5 text-right">{num(calculo.qs_mj, 1)} MJ/m²{categoria ? ` (${categoria})` : ""}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
