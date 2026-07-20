export function formatDate(iso) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleString("es-ES", {
      day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function num(v, digits = 0) {
  if (v == null || isNaN(v)) return "-";
  return Number(v).toLocaleString("es-ES", {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  });
}

export const RISK_STYLES = {
  BAJO: { bg: "bg-emerald-500", text: "text-emerald-700", soft: "bg-emerald-50 border-emerald-200 text-emerald-800" },
  MEDIO: { bg: "bg-amber-500", text: "text-amber-700", soft: "bg-amber-50 border-amber-200 text-amber-800" },
  ALTO: { bg: "bg-red-500", text: "text-red-700", soft: "bg-red-50 border-red-200 text-red-800" },
};

export const STATE_META = {
  cumple: { label: "Cumple", cls: "bg-emerald-50 border-emerald-300 text-emerald-800" },
  observaciones: { label: "Con observaciones", cls: "bg-amber-50 border-amber-300 text-amber-800" },
  no_cumple: { label: "No cumple", cls: "bg-red-50 border-red-300 text-red-800" },
};
