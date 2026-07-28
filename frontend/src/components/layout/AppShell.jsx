import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, FolderKanban, Boxes, Users, LogOut, ChevronRight } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/button";

const NAV = [
  { to: "/", label: "Panel", icon: LayoutDashboard, testid: "nav-dashboard", end: true },
  { to: "/expedientes", label: "Expedientes", icon: FolderKanban, testid: "nav-projects" },
  { to: "/modulos", label: "Módulos", icon: Boxes, testid: "nav-modules" },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const nav = user?.role === "admin"
    ? [...NAV, { to: "/equipo", label: "Equipo", icon: Users, testid: "nav-users" }]
    : NAV;

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen bg-secondary/40">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-border bg-background md:flex">
        <div className="flex h-16 items-center gap-3 border-b border-border px-6">
          <Link to="/" className="flex items-center gap-3" data-testid="brand-link">
            <div className="flex h-8 w-8 items-center justify-center bg-orange-500 font-heading text-base font-bold text-white">
              N
            </div>
            <span className="font-heading text-base font-semibold tracking-tight">NormaLab</span>
          </Link>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              data-testid={item.testid}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-sm px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-foreground text-background font-medium"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-3">
          <div className="mb-2 px-3 py-2">
            <p className="truncate text-sm font-medium" data-testid="user-name">{user?.name}</p>
            <p className="truncate text-xs uppercase tracking-wider text-muted-foreground">
              {user?.role === "admin" ? "Administrador" : "Técnico"}
            </p>
          </div>
          <Button
            variant="ghost"
            className="w-full justify-start rounded-sm text-muted-foreground hover:text-foreground"
            onClick={handleLogout}
            data-testid="logout-button"
          >
            <LogOut className="mr-2 h-4 w-4" /> Cerrar sesión
          </Button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 md:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-heading font-medium text-foreground">Despacho técnico</span>
            <ChevronRight className="h-3.5 w-3.5" />
            <span>Estudios normativos</span>
          </div>
          <ThemeToggle />
        </header>
        <main className="px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
