import { Navigate } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import { Loader2 } from "lucide-react";

export function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (user === null) {
    return (
      <div className="flex h-screen items-center justify-center" data-testid="auth-loading">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (user === false) return <Navigate to="/login" replace />;
  return children;
}
