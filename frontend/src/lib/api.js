import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// Refresco transparente del access_token (dura 15 min) usando la cookie de
// refresco (7 días). Evita que las sesiones largas —p. ej. rellenar decenas de
// estancias— fallen en silencio con 401 al guardar/avanzar.
let refreshPromise = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const url = original?.url || "";
    const isAuthCall = url.includes("/auth/login") || url.includes("/auth/refresh") ||
      url.includes("/auth/register") || url.includes("/auth/logout");
    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = api.post("/auth/refresh").finally(() => { refreshPromise = null; });
        }
        await refreshPromise;
        return api(original);
      } catch (e) {
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export async function downloadFile(path, fallbackName) {
  const res = await api.get(path, { responseType: "blob" });
  const cd = res.headers["content-disposition"] || "";
  let name = fallbackName;
  const m = cd.match(/filename\*=UTF-8''([^;]+)/i) || cd.match(/filename="?([^";]+)"?/i);
  if (m) name = decodeURIComponent(m[1]);
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export function apiError(detail) {
  const d = detail?.response?.data?.detail ?? detail;
  if (d == null) return "Se ha producido un error. Inténtalo de nuevo.";
  if (typeof d === "string") return d;
  if (Array.isArray(d))
    return d.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).join(" ");
  if (d && typeof d.msg === "string") return d.msg;
  return String(d);
}
