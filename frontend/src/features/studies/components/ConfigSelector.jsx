import { useState } from "react";
import { Check, Maximize2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export function ConfigSelector({ value, onChange, options = [], testid }) {
  const [zoom, setZoom] = useState(null);

  return (
    <div data-testid={testid}>
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
        {options.map((c) => {
          const active = value === c.value;
          return (
            <button
              key={c.value}
              type="button"
              onClick={() => onChange(c.value)}
              data-testid={`config-option-${c.value}`}
              className={`group relative flex flex-col overflow-hidden border text-left transition-colors ${
                active ? "border-foreground ring-1 ring-foreground" : "border-border hover:border-foreground/50"
              }`}
            >
              <div className="relative h-16 bg-secondary/50 sm:h-20">
                <img src={c.image} alt={c.label} className="h-full w-full object-contain p-1" />
                {active && (
                  <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center bg-foreground text-background">
                    <Check className="h-2.5 w-2.5" />
                  </span>
                )}
                <span
                  onClick={(e) => { e.stopPropagation(); setZoom(c); }}
                  className="absolute bottom-1 right-1 flex h-5 w-5 cursor-pointer items-center justify-center border border-border bg-background/90 opacity-0 transition-opacity group-hover:opacity-100"
                  data-testid={`config-zoom-${c.value}`}
                >
                  <Maximize2 className="h-2.5 w-2.5" />
                </span>
              </div>
              <div className="border-t border-border px-2 py-1.5">
                <p className="text-[11px] font-semibold leading-tight">{c.label}</p>
              </div>
            </button>
          );
        })}
      </div>
      {value && (
        <p className="mt-2 text-xs text-muted-foreground">
          {options.find((c) => c.value === value)?.description}
        </p>
      )}

      <Dialog open={!!zoom} onOpenChange={(o) => !o && setZoom(null)}>
        <DialogContent className="max-w-lg rounded-sm">
          <DialogHeader><DialogTitle className="font-heading">{zoom?.label}</DialogTitle></DialogHeader>
          {zoom && (
            <div>
              <img src={zoom.image} alt={zoom.label} className="w-full border border-border" />
              <p className="mt-3 text-sm text-muted-foreground">{zoom.description}</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
