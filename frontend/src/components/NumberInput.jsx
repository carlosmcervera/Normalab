import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// Campo numérico que acepta coma (,) o punto (.) como separador decimal y valida
// la entrada mostrando el error en línea. Emite un Number (o "" si está vacío).
// Los campos inválidos exponen data-invalid="true" para bloquear el avance del
// asistente hasta corregirlos.
const toText = (v) =>
  v === "" || v === null || v === undefined || Number.isNaN(v) ? "" : String(v).replace(".", ",");

const parse = (t) => {
  const s = (t ?? "").toString().trim().replace(/\s/g, "").replace(",", ".");
  if (s === "") return { empty: true };
  if (!/^-?\d*\.?\d*$/.test(s) || s === "." || s === "-" || s === "-.") return { invalid: true };
  const n = Number(s);
  return Number.isNaN(n) ? { invalid: true } : { value: n };
};

export function NumberInput({
  value, onChange, integer = false, min, className, "data-testid": testid, ...props
}) {
  const [text, setText] = useState(toText(value));
  const [err, setErr] = useState("");

  useEffect(() => {
    const p = parse(text);
    const curr = p.value; // undefined si vacío o inválido
    const ext = value === "" || value === null || value === undefined ? undefined : Number(value);
    if (curr !== ext) setText(toText(value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const handle = (e) => {
    const t = e.target.value;
    setText(t);
    const p = parse(t);
    if (p.empty) { setErr(""); onChange(""); return; }
    if (p.invalid) { setErr("Número no válido (usa coma para decimales)."); return; }
    if (integer && !Number.isInteger(p.value)) { setErr("Debe ser un número entero."); return; }
    if (min !== undefined && min !== null && p.value < min) { setErr(`Debe ser ≥ ${min}.`); return; }
    setErr("");
    onChange(p.value);
  };

  return (
    <div className="w-full">
      <Input
        type="text"
        inputMode="decimal"
        value={text}
        onChange={handle}
        data-testid={testid}
        data-invalid={err ? "true" : undefined}
        aria-invalid={err ? true : undefined}
        className={cn(err && "border-destructive focus-visible:ring-destructive", className)}
        {...props}
      />
      {err && <p className="mt-1 text-xs text-destructive" data-testid={testid ? `${testid}-error` : undefined}>{err}</p>}
    </div>
  );
}
