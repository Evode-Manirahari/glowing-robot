import { useEffect, useState } from "react";
import { getJob, getMission, type Job, type Mission } from "../lib/api";

interface Props {
  jobId: string;
  missionId: string;
  onComplete: (mission: Mission) => void;
}

const STATUS_LABEL: Record<string, string> = {
  queued: "Queued...",
  running: "Running replay...",
  completed: "Done",
  failed: "Failed",
};

export default function JobStatus({ jobId, missionId, onComplete }: Props) {
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    let stopped = false;

    async function poll() {
      while (!stopped) {
        try {
          const j = await getJob(jobId);
          setJob(j);
          if (j.status === "completed") {
            const mission = await getMission(missionId);
            onComplete(mission);
            return;
          }
          if (j.status === "failed") return;
        } catch {
          // ignore transient errors
        }
        await new Promise(r => setTimeout(r, 1500));
      }
    }

    poll();
    return () => { stopped = true; };
  }, [jobId, missionId, onComplete]);

  if (!job) return <p style={{ color: "#6b7280" }}>Starting job...</p>;

  const color = job.status === "failed" ? "#dc2626" : job.status === "completed" ? "#16a34a" : "#6b7280";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      {job.status !== "completed" && job.status !== "failed" && (
        <span style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid #6b7280", borderTopColor: "transparent", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
      )}
      <span style={{ color, fontSize: 14 }}>{STATUS_LABEL[job.status] ?? job.status}</span>
      {job.error && <span style={{ color: "#dc2626", fontSize: 12 }}> — {job.error}</span>}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
