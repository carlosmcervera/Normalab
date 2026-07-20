import { useState } from "react";
import { Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger,
} from "@/components/ui/dialog";

export function RaSelector({ value, onChange, raTable = [], testid }) {
  const [open, setOpen] = useState(false);
  const current = raTable.find((r) => Math.abs(Number(r.ra) - Number(value)) < 1e-6);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <Input
          type="number"
          min={0.1}
          step={0.1}
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
          data-testid={testid}
          className="max-w-[120px]"
        />
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button type="button" variant="outline" size="sm" className="rounded-sm" data-testid="open-ra-table">
              <Table2 className="mr-1.5 h-3.5 w-3.5" /> Tabla 1.3.4
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl rounded-sm">
            <DialogHeader>
              <DialogTitle className="font-heading">Coeficiente de activación Ra (Tabla 1.3.4)</DialogTitle>
              <DialogDescription>Selecciona el grado de peligrosidad por activación del sector.</DialogDescription>
            </DialogHeader>
            <div className="border border-border">
              {raTable.map((row, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => { onChange(row.ra); setOpen(false); }}
                  data-testid={`ra-row-${i}`}
                  className={`flex w-full items-start gap-3 border-b border-border p-3 text-left transition-colors last:border-0 hover:bg-secondary ${
                    Math.abs(Number(value) - row.ra) < 1e-6 ? "bg-secondary" : ""
                  }`}
                >
                  <span className="flex h-9 w-12 shrink-0 items-center justify-center bg-foreground font-mono text-sm font-bold text-background">
                    {row.ra.toFixed(1).replace(".", ",")}
                  </span>
                  <span>
                    <span className="text-sm font-medium">{row.grado}</span>
                    <span className="mt-0.5 block text-xs text-muted-foreground">{row.criterio}</span>
                  </span>
                </button>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </div>
      {current && <p className="text-xs text-muted-foreground">Ra = {current.ra.toFixed(1).replace(".", ",")} · {current.grado}</p>}
    </div>
  );
}
