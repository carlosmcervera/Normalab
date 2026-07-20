import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/features/auth/AuthContext";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";
import { AppShell } from "@/components/layout/AppShell";
import LoginPage from "@/features/auth/LoginPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import ProjectsPage from "@/features/projects/ProjectsPage";
import ProjectDetailPage from "@/features/projects/ProjectDetailPage";
import ModulesPage from "@/features/modules/ModulesPage";
import StudyWizardPage from "@/features/studies/StudyWizardPage";
import StudyReportPage from "@/features/studies/StudyReportPage";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/expedientes" element={<ProjectsPage />} />
            <Route path="/expedientes/:projectId" element={<ProjectDetailPage />} />
            <Route path="/modulos" element={<ModulesPage />} />
            <Route path="/estudios/:studyId" element={<StudyWizardPage />} />
            <Route path="/estudios/:studyId/informe" element={<StudyReportPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
