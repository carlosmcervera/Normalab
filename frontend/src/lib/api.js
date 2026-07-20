import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

export function apiError(detail) {
  const d = detail?.response?.data?.detail ?? detail;
  if (d == null) return "Se ha producido un error. Inténtalo de nuevo.";
  if (typeof d === "string") return d;
  if (Array.isArray(d))
    return d.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).join(" ");
  if (d && typeof d.msg === "string") return d.msg;
  return String(d);
}
