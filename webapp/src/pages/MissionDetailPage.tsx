import { useParams, Link } from "react-router-dom";
import { useEffect, useState, useCallback, useRef } from "react";
import { getMission, getEvalReport, getReplayData, requestAiSummary, downloadReport, type Mission, type EvalReport, type ReplayFrame } from "../lib/api";
import ReplayViewer from "../components/ReplayViewer";
import JobStatus from "../components/JobStatus";

const VERDICT_COLOR: Record<string, string> = { pass: "#16a34a", fail: "#dc2626", warning: "#d97706" };

export default function MissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [mission, setMission] = useState<Mission | null>(null);
  const [report, setReport] = useState<EvalReport | null>(null);
  const [replayData, setReplayData] = useState<{ frames: ReplayFrame[]; waypoints: { x: number; y: number }[]; obstacles: { x: number; y: number; radius: number }[]; collision_times: number[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async () => {
    if (!id) return;
    const m = await getMission(id);
    setMission(m);

    if (m.status === "evaluated") {
      const [r, rd] = await Promise.all([
        getEvalReport(id).catch(() => null),
        getReplayData(id).catch(() => null),
      ]);
      setReport(r);
      setReplayData(rd);
    }
    return m;
  }, [id]);

  // Auto-poll when mission is still processing (no sessionStorage jobId needed)
  useEffect(() => {
    if (!id) return;
    const pendingJob = sessionStorage.getItem(`job_${id}`);
    if (pendingJob) setJobId(pendingJob);

    loadData().then(m => {
      if (!m) return;
      if (m.status === "pending" || m.status === "replaying") {
        pollRef.current = setInterval(async () => {
          const updated = await getMission(id).catch(() => null);
          if (!updated) return;
          setMission(updated);
          if (updated.status === "evaluated" || updated.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            if (updated.status === "evaluated") {
              const [r, rd] = await Promise.all([
                getEvalReport(id).catch(() => null),
                getReplayData(id).catch(() => null),
              ]);
              setReport(r);
              setReplayData(rd);
            }
          }
        }, 2000);
      }
    }).finally(() => setLoading(false));

    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [id, loadData]);

  function onJobComplete(updatedMission: Mission) {
    setMission(updatedMission);
    if (id) sessionStorage.removeItem(`job_${id}`);
    setJobId(null);
    if (pollRef.current) clearInterval(pollRef.current);
    loadData();
  }

  async function handleRequestSummary() {
    if (!id) return;
    setSummaryLoading(true);
    await requestAiSummary(id);
    let tries = 0;
    while (tries < 20) {
      await new Promise(r => setTimeout(r, 1500));
      const r = await getEvalReport(id).catch(() => null);
      if (r?.ai_summary) { setReport(r); break; }
      tries++;
    }
    setSummaryLoading(false);
  }

  if (loading) return <p style={{ color: "#6b7280" }}>Loading...</p>;
  if (!mission) return <p style={{ color: "#dc2626" }}>Mission not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <span style={{ color: "#6b7280", fontSize: 13 }}>Mission</span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <h1 style={{ margin: 0 }}>{mission.name}</h1>
        {mission.status === "evaluated" && (
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => downloadReport(mission.id)}
              style={{ fontSize: 13, color: "#6b7280", background: "none", border: "1px solid #d1d5db", padding: "5px 12px", borderRadius: 6, cursor: "pointer" }}
            >
              Download report
            </button>
            <Link
              to={`/compare?a=${mission.id}`}
              style={{ fontSize: 13, color: "#6b7280", textDecoration: "none", border: "1px solid #d1d5db", padding: "5px 12px", borderRadius: 6 }}
            >
              Compare with...
            </Link>
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 32 }}>
        <span style={{ fontSize: 13, color: "#6b7280" }}>{mission.robot_type}</span>
        <span style={{ fontSize: 13, color: "#6b7280" }}>·</span>
        <span style={{ fontSize: 13, color: "#6b7280" }}>{new Date(mission.uploaded_at).toLocaleString()}</span>
        {mission.verdict && (
          <span style={{ padding: "3px 12px", borderRadius: 9999, fontWeight: 600, fontSize: 12, background: VERDICT_COLOR[mission.verdict] + "20", color: VERDICT_COLOR[mission.verdict] }}>
            {mission.verdict.toUpperCase()}
          </span>
        )}
      </div>

      {/* Job in progress */}
      {jobId && mission.status !== "evaluated" && (
        <div style={{ marginBottom: 24, padding: 16, background: "#f9fafb", borderRadius: 8 }}>
          <JobStatus jobId={jobId} missionId={mission.id} onComplete={onJobComplete} />
        </div>
      )}

      {/* Auto-polling state */}
      {!jobId && (mission.status === "pending" || mission.status === "replaying") && (
        <div style={{ marginBottom: 24, padding: 16, background: "#f9fafb", borderRadius: 8, display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid #6b7280", borderTopColor: "transparent", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
          <span style={{ color: "#6b7280", fontSize: 14 }}>
            {mission.status === "replaying" ? "Running replay..." : "Queued..."}
          </span>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Failed state */}
      {mission.status === "failed" && (
        <div style={{ marginBottom: 24, padding: 16, background: "#fef2f2", borderRadius: 8, color: "#dc2626", fontSize: 14 }}>
          Replay failed. Check your log file format and try uploading again.
        </div>
      )}

      {/* Eval report */}
      {report && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 32 }}>
            {[
              { label: "Collisions", value: report.collision_count },
              { label: "Max Deviation", value: `${report.max_deviation_m.toFixed(2)} m` },
              { label: "Completion", value: `${(report.completion_rate * 100).toFixed(0)}%` },
              { label: "Duration", value: `${report.duration_s.toFixed(1)} s` },
            ].map(m => (
              <div key={m.label} style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "14px 16px" }}>
                <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 6 }}>{m.label}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>{m.value}</div>
              </div>
            ))}
          </div>

          {report.anomalies.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ marginBottom: 8 }}>Anomalies</h3>
              <ul style={{ margin: 0, paddingLeft: 20, color: "#dc2626", lineHeight: 2 }}>
                {report.anomalies.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}

          {/* AI Summary */}
          <div style={{ background: "#f9fafb", borderRadius: 8, padding: 20, marginBottom: 32 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
              <h3 style={{ margin: 0 }}>AI Analysis</h3>
              {!report.ai_summary && (
                <button onClick={handleRequestSummary} disabled={summaryLoading} style={{ fontSize: 13, padding: "4px 12px", borderRadius: 6, border: "1px solid #d1d5db", cursor: "pointer", background: "#fff" }}>
                  {summaryLoading ? "Generating..." : "Generate summary"}
                </button>
              )}
            </div>
            {report.ai_summary ? (
              <p style={{ margin: 0, lineHeight: 1.7, color: "#374151" }}>{report.ai_summary}</p>
            ) : (
              <p style={{ margin: 0, color: "#9ca3af", fontSize: 14 }}>No AI summary yet. Click "Generate summary" above.</p>
            )}
          </div>
        </>
      )}

      {/* Replay Viewer */}
      {replayData && replayData.frames.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h3 style={{ marginBottom: 16 }}>Trajectory Replay</h3>
          <ReplayViewer
            frames={replayData.frames}
            waypoints={replayData.waypoints}
            obstacles={replayData.obstacles}
            collisionTimes={replayData.collision_times}
          />
        </div>
      )}
    </div>
  );
}
