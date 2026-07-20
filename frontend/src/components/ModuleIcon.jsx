import { Flame, Building2, Zap, Thermometer, Accessibility, FileText } from "lucide-react";

const MAP = {
  flame: Flame,
  "building-2": Building2,
  zap: Zap,
  thermometer: Thermometer,
  accessibility: Accessibility,
  "file-text": FileText,
};

const ACCENT = {
  orange: "text-orange-600 bg-orange-50 border-orange-200",
  blue: "text-blue-600 bg-blue-50 border-blue-200",
  amber: "text-amber-600 bg-amber-50 border-amber-200",
  rose: "text-rose-600 bg-rose-50 border-rose-200",
  emerald: "text-emerald-600 bg-emerald-50 border-emerald-200",
  slate: "text-slate-600 bg-slate-50 border-slate-200",
};

export function ModuleIcon({ icon, accent = "slate", className = "" }) {
  const Icon = MAP[icon] || FileText;
  return (
    <div className={`flex h-11 w-11 items-center justify-center border ${ACCENT[accent] || ACCENT.slate} ${className}`}>
      <Icon className="h-5 w-5" />
    </div>
  );
}
