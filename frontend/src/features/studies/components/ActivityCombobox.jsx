import { useState } from "react";
import { Check, ChevronsUpDown, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList,
} from "@/components/ui/command";

export function ActivityCombobox({ value, onChange, options = [], testid }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const exists = options.some((o) => o.toLowerCase() === query.trim().toLowerCase());

  const select = (val) => {
    onChange(val);
    setOpen(false);
    setQuery("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          className="w-full justify-between rounded-sm font-normal"
          data-testid={testid}
        >
          <span className={value ? "" : "text-muted-foreground"}>{value || "Selecciona o escribe una actividad"}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0 rounded-sm" align="start">
        <Command>
          <CommandInput placeholder="Buscar actividad…" value={query} onValueChange={setQuery} data-testid="activity-search" />
          <CommandList>
            {query.trim() && !exists && (
              <CommandGroup>
                <CommandItem value={`__create__${query}`} onSelect={() => select(query.trim())} data-testid="activity-create">
                  <Plus className="mr-2 h-4 w-4" /> Crear «{query.trim()}»
                </CommandItem>
              </CommandGroup>
            )}
            <CommandEmpty>Escribe para crear una actividad personalizada.</CommandEmpty>
            <CommandGroup heading="Actividades RSCIEI">
              {options.map((o) => (
                <CommandItem key={o} value={o} onSelect={() => select(o)}>
                  <Check className={`mr-2 h-4 w-4 ${value === o ? "opacity-100" : "opacity-0"}`} />
                  {o}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
