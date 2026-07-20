import { Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { useState } from "react";

export function CiTableDialog({ ciTable = [], onSelect, current }) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="h-7 rounded-sm px-2 text-xs" data-testid="open-ci-table">
          <Table2 className="mr-1 h-3 w-3" /> Tabla Ci
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md rounded-sm">
        <DialogHeader>
          <DialogTitle className="font-heading">Coeficiente de combustibilidad (Ci)</DialogTitle>
          <DialogDescription>Selecciona el grado de combustibilidad del producto.</DialogDescription>
        </DialogHeader>
        <div className="border border-border">
          {ciTable.map((row, i) => (
            <button
              key={i}
              type="button"
              onClick={() => { onSelect(row.ci); setOpen(false); }}
              data-testid={`ci-row-${i}`}
              className={`flex w-full items-start gap-3 border-b border-border p-3 text-left transition-colors last:border-0 hover:bg-secondary ${
                current === row.ci ? "bg-secondary" : ""
              }`}
            >
              <span className="flex h-8 w-12 shrink-0 items-center justify-center bg-foreground font-mono text-sm font-bold text-background">
                {row.ci.toFixed(2)}
              </span>
              <span>
                <span className="text-sm font-medium">{row.grado}</span>
                <span className="block text-xs text-muted-foreground">{row.descripcion}</span>
              </span>
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
