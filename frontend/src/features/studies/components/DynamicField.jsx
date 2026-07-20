import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

export function DynamicField({ field, value, onChange, testidPrefix }) {
  const id = `${testidPrefix}-${field.name}`;
  const label = (
    <Label htmlFor={id} className="text-sm">
      {field.label} {field.required && <span className="text-destructive">*</span>}
    </Label>
  );

  if (field.type === "boolean") {
    return (
      <div className="flex items-center justify-between border border-border bg-background px-4 py-3">
        <div>
          {label}
          {field.help && <p className="mt-0.5 text-xs text-muted-foreground">{field.help}</p>}
        </div>
        <Switch id={id} checked={!!value} onCheckedChange={onChange} data-testid={id} />
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {label}
      {field.type === "select" ? (
        <Select value={value ?? ""} onValueChange={onChange}>
          <SelectTrigger id={id} data-testid={id} className="rounded-sm">
            <SelectValue placeholder={field.placeholder || "Selecciona…"} />
          </SelectTrigger>
          <SelectContent>
            {(field.options || []).map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <Input
          id={id}
          data-testid={id}
          type={field.type === "number" ? "number" : "text"}
          step={field.step}
          min={field.min}
          placeholder={field.placeholder}
          value={value ?? ""}
          onChange={(e) =>
            onChange(field.type === "number" ? (e.target.value === "" ? "" : Number(e.target.value)) : e.target.value)
          }
        />
      )}
      {field.help && <p className="text-xs text-muted-foreground">{field.help}</p>}
    </div>
  );
}
