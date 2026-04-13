import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listMissions, compareMissions, type Mission, type CompareResponse } from "../lib/api";

const VERDICT_COLOR: Record<string, string> = { pass: "#16a34a", fail: "#dc2626", warning: "#d97706" };

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "12px 14px" }}>
      <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function ReportColumn({ report, name }: { report: CompareResponse["report_a"]; name: string }) {
  const verdictColor = VERDICT_COLOR[report.verdict] ?? "#6b7280";
  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: 16 }}>{name}</h3>
        <span style={{ padding: "2px 10px", borderRadius: 9999, fontSize: 12, fontWeight: 600, background: verdictColor + "20", color: verdictColor }}>
          {report.verdict.toUpperCase()}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
        <MetricCard label="Collisions" value={report.collision_count} />
        <MetricCard label="Max Deviation" value={`${report.max_deviation_m.toFixed(2)} m`} />
        <MetricCard label="Completion" value={`${(report.completion_rate * 100).toFixed(0)}%`} />
        <MetricCard label="Duration" value={`${report.duration_s.toFixed(1)} s`} />
      </div>
      {report.anomalies.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 500, color: "#6b7280", marginBottom: 6 }}>Anomalies</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "#dc2626", lineHeight: 1.8 }}>
            {report.anomalies.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}
      {report.anomalies.length === 0 && (
        <div style={{ fontSize: 13, color: "#16a34a" }}>No anomalies detected</div>
      )}
    </div>
  );
}

export default function ComparePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [missions, setMissions] = useState<Mission[]>([]);
  const [missionA, setMissionA] = useState(searchParams.get("a") ?? "");
  const [missionB, setMissionB] = useState(searchParams.get("b") ?? "");
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMissions().then(ms => {
      // Only compare evaluated missions
      setMissions(ms.filter(m => m.status === "evaluated"));
    });
  }, []);

  // Auto-run if both IDs are pre-filled from URL
  useEffect(() => {
    const a = searchParams.get("a");
    const b = searchParams.get("b");
    if (a && b) {
      setMissionA(a);
      setMissionB(b);
      runCompare(a, b);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runCompare(a = missionA, b = missionB) {
    if (!a || !b || a === b) {
      setError("Select two different evaluated missions to compare.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await compareMissions(a, b);
      setResult(r);
      setSearchParams({ a, b });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  }

  const evaluatedMissions = missions.filter(m => m.status === "evaluated");

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>Policy Comparison</h1>
      <p style={{ color: "#6b7280", marginBottom: 28, fontSize: 14 }}>
        Compare two mission runs side by side to track regressions and improvements.
      </p>

      {/* Mission selectors */}
      <div style={{ display: "flex", gap: 12, alignItems: "flex-end", marginBottom: 32, flexWrap: "wrap" }}>
        <label style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Mission A (baseline)</div>
          <select
            value={missionA}
            onChange={e => setMissionA(e.target.value)}
            style={selectStyle}
          >
            <option value="">Select a mission...</option>
            {evaluatedMissions.map(m => (
              <option key={m.id} value={m.id}>{m.name} — {m.robot_type}</option>
            ))}
          </select>
        </label>

        <label style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Mission B (candidate)</div>
          <select
            value={missionB}
            onChange={e => setMissionB(e.target.value)}
            style={selectStyle}
          >
            <option value="">Select a mission...</option>
            {evaluatedMissions.map(m => (
              <option key={m.id} value={m.id}>{m.name} — {m.robot_type}</option>
            ))}
          </select>
        </label>

        <button
          onClick={() => runCompare()}
          disabled={loading || !missionA || !missionB || missionA === missionB}
          style={{ background: "#111", color: "#fff", padding: "9px 20px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 14, opacity: loading || !missionA || !missionB || missionA === missionB ? 0.5 : 1 }}
        >
          {loading ? "Comparing..." : "Compare"}
        </button>
      </div>

      {error && <p style={{ color: "#dc2626", fontSize: 14, marginBottom: 24 }}>{error}</p>}

      {evaluatedMissions.length < 2 && (
        <p style={{ color: "#6b7280", fontSize: 14 }}>
          You need at least two evaluated missions to compare. <a href="/upload" style={{ color: "#111" }}>Upload another log</a>.
        </p>
      )}

      {/* Results */}
      {result && (
        <>
          {/* AI comparison summary */}
          <div style={{ background: "#f9fafb", borderRadius: 8, padding: 20, marginBottom: 32 }}>
            <h3 style={{ margin: "0 0 10px" }}>AI Comparison</h3>
            <p style={{ margin: 0, lineHeight: 1.7, color: "#374151" }}>{result.comparison_summary}</p>
          </div>

          {/* Side-by-side metrics */}
          <div style={{ display: "flex", gap: 32, alignItems: "flex-start" }}>
            <ReportColumn report={result.report_a} name={result.mission_a_name} />
            <div style={{ width: 1, background: "#e5e7eb", alignSelf: "stretch" }} />
            <ReportColumn report={result.report_b} name={result.mission_b_name} />
          </div>

          {/* Delta summary row */}
          <div style={{ marginTop: 32, padding: "16px 20px", border: "1px solid #e5e7eb", borderRadius: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: "#6b7280", marginBottom: 12 }}>Delta (B vs A)</div>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              <DeltaStat
                label="Collisions"
                delta={result.report_b.collision_count - result.report_a.collision_count}
                lowerIsBetter
                fmt={v => (v > 0 ? `+${v}` : String(v))}
              />
              <DeltaStat
                label="Max Deviation"
                delta={result.report_b.max_deviation_m - result.report_a.max_deviation_m}
                lowerIsBetter
                fmt={v => `${v > 0 ? "+" : ""}${v.toFixed(3)} m`}
              />
              <DeltaStat
                label="Completion"
                delta={(result.report_b.completion_rate - result.report_a.completion_rate) * 100}
                lowerIsBetter={false}
                fmt={v => `${v > 0 ? "+" : ""}${v.toFixed(0)}%`}
              />
              <DeltaStat
                label="Duration"
                delta={result.report_b.duration_s - result.report_a.duration_s}
                lowerIsBetter
                fmt={v => `${v > 0 ? "+" : ""}${v.toFixed(1)} s`}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function DeltaStat({ label, delta, lowerIsBetter, fmt }: { label: string; delta: number; lowerIsBetter: boolean; fmt: (v: number) => string }) {
  const improved = lowerIsBetter ? delta < 0 : delta > 0;
  const neutral = delta === 0;
  const color = neutral ? "#6b7280" : improved ? "#16a34a" : "#dc2626";
  return (
    <div>
      <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color }}>{fmt(delta)}</div>
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  width: "100%",
  padding: "9px 12px",
  border: "1px solid #d1d5db",
  borderRadius: 6,
  fontSize: 14,
  background: "#fff",
};
