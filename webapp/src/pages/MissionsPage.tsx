import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { listMissions, deleteMission, type Mission } from "../lib/api";

const VERDICT_COLOR: Record<string, string> = { pass: "#16a34a", fail: "#dc2626", warning: "#d97706" };
const STATUS_LABEL: Record<string, string> = { pending: "Pending", replaying: "Replaying...", evaluated: "Done", failed: "Failed" };

const SAMPLE_LOG_URL = "https://raw.githubusercontent.com/Evode-Manirahari/glowing-robot/main/sim/scenarios/warehouse_collision.json";

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verdictFilter, setVerdictFilter] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const fetchMissions = useCallback(() => {
    setLoading(true);
    listMissions({ verdict: verdictFilter || undefined, q: search || undefined })
      .then(setMissions)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [verdictFilter, search]);

  useEffect(() => { fetchMissions(); }, [fetchMissions]);

  // Debounce search input
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete mission "${name}"?`)) return;
    await deleteMission(id);
    setMissions(ms => ms.filter(m => m.id !== id));
  }

  const hasFilters = verdictFilter || search;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Missions</h1>
        <Link to="/upload" style={{ background: "#111", color: "#fff", padding: "8px 16px", borderRadius: 6, textDecoration: "none", fontSize: 14 }}>
          + Upload Log
        </Link>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20, alignItems: "center" }}>
        <input
          placeholder="Search missions..."
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          style={{ padding: "7px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, width: 220 }}
        />
        <select
          value={verdictFilter}
          onChange={e => setVerdictFilter(e.target.value)}
          style={{ padding: "7px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, background: "#fff" }}
        >
          <option value="">All verdicts</option>
          <option value="pass">Pass</option>
          <option value="fail">Fail</option>
          <option value="warning">Warning</option>
        </select>
        {hasFilters && (
          <button
            onClick={() => { setSearchInput(""); setVerdictFilter(""); }}
            style={{ fontSize: 13, color: "#6b7280", background: "none", border: "none", cursor: "pointer", padding: "4px 8px" }}
          >
            Clear
          </button>
        )}
        {!loading && (
          <span style={{ marginLeft: "auto", fontSize: 13, color: "#9ca3af" }}>
            {missions.length} {missions.length === 1 ? "mission" : "missions"}
          </span>
        )}
      </div>

      {error && <p style={{ color: "#dc2626" }}>Error: {error}</p>}
      {loading && <p style={{ color: "#6b7280" }}>Loading...</p>}

      {!loading && missions.length === 0 && !hasFilters && (
        <EmptyState />
      )}

      {!loading && missions.length === 0 && hasFilters && (
        <div style={{ textAlign: "center", padding: "60px 0", color: "#6b7280" }}>
          <p>No missions match your filters.</p>
          <button onClick={() => { setSearchInput(""); setVerdictFilter(""); }} style={{ color: "#111", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontSize: 14 }}>
            Clear filters
          </button>
        </div>
      )}

      {!loading && missions.length > 0 && (
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

function EmptyState() {
  function downloadSample() {
    const a = document.createElement("a");
    a.href = SAMPLE_LOG_URL;
    a.download = "warehouse_collision.json";
    a.click();
  }

  return (
    <div style={{ textAlign: "center", padding: "80px 0" }}>
      <div style={{ fontSize: 40, marginBottom: 16 }}>🤖</div>
      <h2 style={{ margin: "0 0 8px", fontWeight: 600 }}>No missions yet</h2>
      <p style={{ color: "#6b7280", marginBottom: 32, maxWidth: 400, margin: "0 auto 32px" }}>
        Upload a robot trajectory log to run your first evaluation. Get a pass/fail verdict, anomaly report, and AI analysis in seconds.
      </p>
      <div style={{ display: "flex", gap: 12, justifyContent: "center", alignItems: "center" }}>
        <Link
          to="/upload"
          style={{ background: "#111", color: "#fff", padding: "10px 20px", borderRadius: 6, textDecoration: "none", fontSize: 14, fontWeight: 500 }}
        >
          Upload a log
        </Link>
        <span style={{ color: "#d1d5db", fontSize: 13 }}>or</span>
        <button
          onClick={downloadSample}
          style={{ fontSize: 14, color: "#6b7280", background: "none", border: "1px solid #d1d5db", borderRadius: 6, padding: "9px 16px", cursor: "pointer" }}
        >
          Download sample log
        </button>
      </div>
    </div>
  );
}
