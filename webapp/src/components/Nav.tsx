import { Link } from "react-router-dom";

export default function Nav() {
  return (
    <nav style={{ display: "flex", gap: 24, padding: "16px 0", borderBottom: "1px solid #e5e7eb", marginBottom: 32 }}>
      <Link to="/" style={{ fontWeight: 700, fontSize: 18, textDecoration: "none", color: "#111" }}>
        glowing-robot
      </Link>
      <Link to="/" style={{ color: "#6b7280", textDecoration: "none" }}>Missions</Link>
      <Link to="/upload" style={{ color: "#6b7280", textDecoration: "none" }}>Upload</Link>
    </nav>
  );
}
