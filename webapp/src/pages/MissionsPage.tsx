import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMissions, deleteMission, type Mission } from "../lib/api";

const VERDICT_COLOR: Record<string, string> = { pass: "#16a34a", fail: "#dc2626", warning: "#d97706" };
const STATUS_LABEL: Record<string, string> = { pending: "Pending", replaying: "Replaying...", evaluated: "Done", failed: "Failed" };

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMissions()
      .then(setMissions)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete mission "${name}"?`)) return;
    await deleteMission(id);
    setMissions(ms => ms.filter(m => m.id !== id));
  }

  if (loading) return <p style={{ color: "#6b7280" }}>Loading missions...</p>;
  if (error) return <p style={{ color: "#dc2626" }}>Error: {error}</p>;

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
            <tr style={{ borderBottom: "2px solid #e5e7eb", textAlign: "left", fontSize: 13, color: "#6b7280" }}>
              <th style={{ padding: "8px 0", fontWeight: 500 }}>Name</th>
              <th style={{ fontWeight: 500 }}>Robot</th>
              <th style={{ fontWeight: 500 }}>Uploaded</th>
              <th style={{ fontWeight: 500 }}>Status</th>
              <th style={{ fontWeight: 500 }}>Verdict</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {missions.map(m => (
              <tr key={m.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                <td style={{ padding: "12px 0" }}>
                  <Link to={`/missions/${m.id}`} style={{ fontWeight: 500, color: "#111", textDecoration: "none" }}>
                    {m.name}
                  </Link>
                  <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 2 }}>{m.log_filename}</div>
                </td>
                <td style={{ color: "#374151", fontSize: 14 }}>{m.robot_type}</td>
                <td style={{ color: "#6b7280", fontSize: 13 }}>{new Date(m.uploaded_at).toLocaleDateString()}</td>
                <td style={{ fontSize: 13 }}>{STATUS_LABEL[m.status] ?? m.status}</td>
                <td>
                  {m.verdict ? (
                    <span style={{ padding: "2px 10px", borderRadius: 9999, fontSize: 12, fontWeight: 600, background: VERDICT_COLOR[m.verdict] + "20", color: VERDICT_COLOR[m.verdict] }}>
                      {m.verdict.toUpperCase()}
                    </span>
                  ) : "—"}
                </td>
                <td style={{ textAlign: "right" }}>
                  <button onClick={() => handleDelete(m.id, m.name)} style={{ background: "none", border: "none", color: "#9ca3af", cursor: "pointer", fontSize: 13 }}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
