import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function Nav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  if (!user) return null;

  return (
    <nav style={{ display: "flex", gap: 24, padding: "16px 0", borderBottom: "1px solid #e5e7eb", marginBottom: 32, alignItems: "center" }}>
      <Link to="/" style={{ fontWeight: 700, fontSize: 18, textDecoration: "none", color: "#111", marginRight: 8 }}>
        glowing-robot
      </Link>
      <Link to="/" style={{ color: "#6b7280", textDecoration: "none", fontSize: 14 }}>Missions</Link>
      <Link to="/upload" style={{ color: "#6b7280", textDecoration: "none", fontSize: 14 }}>Upload</Link>
      <Link to="/compare" style={{ color: "#6b7280", textDecoration: "none", fontSize: 14 }}>Compare</Link>
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 16 }}>
        <Link to="/settings" style={{ fontSize: 13, color: "#6b7280", textDecoration: "none" }}>{user.name}</Link>
        <button onClick={handleLogout} style={{ fontSize: 13, color: "#6b7280", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
          Sign out
        </button>
      </div>
    </nav>
  );
}
