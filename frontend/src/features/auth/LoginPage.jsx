import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { useAuth, apiError } from "@/features/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const loginSchema = z.object({
  email: z.string().email("Email no válido"),
  password: z.string().min(1, "Introduce la contraseña"),
});
const registerSchema = loginSchema.extend({
  name: z.string().min(1, "Introduce el nombre"),
  password: z.string().min(6, "Mínimo 6 caracteres"),
});

export default function LoginPage() {
  const { login, register: doRegister } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const isLogin = mode === "login";

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({ resolver: zodResolver(isLogin ? loginSchema : registerSchema) });

  const onSubmit = async (values) => {
    try {
      if (isLogin) await login(values.email, values.password);
      else await doRegister({ ...values, role: "tecnico" });
      toast.success(isLogin ? "Sesión iniciada" : "Cuenta creada");
      navigate("/");
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col justify-between bg-[#0A0A0B] p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage:
              "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center bg-orange-500 font-heading text-lg font-bold">
            N
          </div>
          <span className="font-heading text-lg font-semibold tracking-tight">NormaLab</span>
        </div>
        <div className="relative">
          <p className="text-[11px] font-bold uppercase tracking-[0.3em] text-orange-400">
            Plataforma de estudios normativos
          </p>
          <h1 className="mt-4 max-w-md font-heading text-4xl font-light leading-tight tracking-tight">
            Estudios normativos modulares para el despacho técnico.
          </h1>
          <p className="mt-4 max-w-md text-sm text-white/60">
            CTE · RSCIEI · REBT · RITE · Accesibilidad. Asistentes guiados, validaciones
            automáticas e informes no vinculantes con versionado.
          </p>
        </div>
        <div className="relative flex items-center gap-2 text-xs text-white/40">
          <ShieldCheck className="h-4 w-4" /> Aplicación interna · Acceso restringido
        </div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center bg-orange-500 font-heading text-lg font-bold text-white">
              N
            </div>
            <span className="font-heading text-lg font-semibold">NormaLab</span>
          </div>
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
            {isLogin ? "Acceso" : "Registro"}
          </p>
          <h2 className="mt-2 font-heading text-2xl tracking-tight">
            {isLogin ? "Inicia sesión" : "Crea tu cuenta"}
          </h2>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5" data-testid="auth-form">
            {!isLogin && (
              <div className="space-y-1.5">
                <Label htmlFor="name">Nombre</Label>
                <Input id="name" data-testid="name-input" {...register("name")} placeholder="Nombre y apellidos" />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" data-testid="email-input" {...register("email")} placeholder="tecnico@despacho.com" />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Contraseña</Label>
              <Input id="password" type="password" data-testid="password-input" {...register("password")} placeholder="••••••••" />
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>
            <Button type="submit" className="w-full rounded-sm" disabled={isSubmitting} data-testid="submit-auth">
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isLogin ? "Entrar" : "Crear cuenta"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            {isLogin ? "¿No tienes cuenta? " : "¿Ya tienes cuenta? "}
            <button
              type="button"
              className="font-medium text-foreground underline underline-offset-4 hover:text-orange-600"
              onClick={() => {
                setMode(isLogin ? "register" : "login");
                reset();
              }}
              data-testid="toggle-auth-mode"
            >
              {isLogin ? "Regístrate" : "Inicia sesión"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
