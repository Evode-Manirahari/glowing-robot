import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

interface EvalReport {
  mission_id: string;
  verdict: string;
  collision_count: number;
  max_deviation_m: number;
  completion_rate: number;
  duration_s: number;
  anomalies: string[];
  ai_summary: string | null;
}

export default function MissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<EvalReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    fetch(`/evals/${id}/report`)
      .then((r) => {
        if (r.status === 404) { setNotFound(true); return null; }
        return r.json();
      })
      .then((data) => { if (data) setReport(data); })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p>Loading...</p>;
  if (notFound) return <p>Mission not found.</p>;
  if (!report) return null;

  const verdictColor = report.verdict === "pass" ? "#16a34a" : report.verdict === "fail" ? "#dc2626" : "#d97706";

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>Mission {id?.slice(0, 8)}</h1>
      <span style={{ display: "inline-block", padding: "4px 12px", borderRadius: 9999, background: verdictColor, color: "#fff", fontWeight: 600, marginBottom: 32 }}>
        {report.verdict.toUpperCase()}
      </span>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        {[
          { label: "Collisions", value: report.collision_count },
          { label: "Max Deviation", value: `${report.max_deviation_m.toFixed(2)} m` },
          { label: "Completion", value: `${(report.completion_rate * 100).toFixed(0)}%` },
          { label: "Duration", value: `${report.duration_s.toFixed(1)} s` },
        ].map((m) => (
          <div key={m.label} style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{m.value}</div>
          </div>
        ))}
      </div>

      {report.anomalies.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3>Anomalies</h3>
          <ul>
            {report.anomalies.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      {report.ai_summary && (
        <div style={{ background: "#f9fafb", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>AI Analysis</h3>
          <p style={{ margin: 0, lineHeight: 1.6 }}>{report.ai_summary}</p>
        </div>
      )}
    </div>
  );
}
