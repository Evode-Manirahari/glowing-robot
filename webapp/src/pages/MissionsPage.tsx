import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface Mission {
  id: string;
  name: string;
  robot_type: string;
  uploaded_at: string;
  status: string;
  verdict: string | null;
}

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/missions/")
      .then((r) => r.json())
      .then(setMissions)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading missions...</p>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Missions</h1>
        <Link to="/upload" style={{ background: "#111", color: "#fff", padding: "8px 16px", borderRadius: 6, textDecoration: "none", fontSize: 14 }}>
          + Upload Log
        </Link>
      </div>

      {missions.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 0", color: "#6b7280" }}>
          <p style={{ fontSize: 18 }}>No missions yet.</p>
          <Link to="/upload">Upload your first robot log to get started.</Link>
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #e5e7eb", textAlign: "left" }}>
              <th style={{ padding: "8px 0" }}>Name</th>
              <th>Robot</th>
              <th>Uploaded</th>
              <th>Status</th>
              <th>Verdict</th>
            </tr>
          </thead>
          <tbody>
            {missions.map((m) => (
              <tr key={m.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                <td style={{ padding: "12px 0" }}>
                  <Link to={`/missions/${m.id}`}>{m.name}</Link>
                </td>
                <td>{m.robot_type}</td>
                <td>{new Date(m.uploaded_at).toLocaleDateString()}</td>
                <td>{m.status}</td>
                <td>{m.verdict ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
