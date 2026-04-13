import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./lib/auth";
import MissionsPage from "./pages/MissionsPage";
import MissionDetailPage from "./pages/MissionDetailPage";
import UploadPage from "./pages/UploadPage";
import ComparePage from "./pages/ComparePage";
import SettingsPage from "./pages/SettingsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import Nav from "./components/Nav";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", maxWidth: 1100, margin: "0 auto", padding: "0 24px" }}>
      <Nav />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<RequireAuth><MissionsPage /></RequireAuth>} />
        <Route path="/missions/:id" element={<RequireAuth><MissionDetailPage /></RequireAuth>} />
        <Route path="/upload" element={<RequireAuth><UploadPage /></RequireAuth>} />
        <Route path="/compare" element={<RequireAuth><ComparePage /></RequireAuth>} />
        <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
      </Routes>
    </div>
  );
}
