import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { uploadMission } from "../lib/api";

export default function UploadPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [robotType, setRobotType] = useState("AMR");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const { mission_id, job_id } = await uploadMission(name, robotType, file);
      // Store job_id in session so the detail page can poll it
      sessionStorage.setItem(`job_${mission_id}`, job_id);
      navigate(`/missions/${mission_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{ maxWidth: 500 }}>
      <h1 style={{ marginBottom: 8 }}>Upload Mission Log</h1>
      <p style={{ color: "#6b7280", marginBottom: 32 }}>
        Upload a robot trajectory log (.json or .csv) to start a replay and evaluation run.
        Results are ready in seconds.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <label>
          <div style={labelStyle}>Mission name</div>
          <input value={name} onChange={e => setName(e.target.value)} required placeholder="Warehouse run #42" style={inputStyle} />
        </label>

        <label>
          <div style={labelStyle}>Robot type</div>
          <select value={robotType} onChange={e => setRobotType(e.target.value)} style={inputStyle}>
            <option value="AMR">AMR (autonomous mobile robot)</option>
            <option value="arm">Robot arm / manipulator</option>
            <option value="humanoid">Humanoid</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          <div style={labelStyle}>Log file</div>
          <div style={{ border: "2px dashed #d1d5db", borderRadius: 8, padding: "24px", textAlign: "center", background: "#f9fafb" }}>
            <input type="file" accept=".json,.csv,.bag,.mcap,.db3" required onChange={e => setFile(e.target.files?.[0] ?? null)} />
            <p style={{ margin: "8px 0 0", fontSize: 12, color: "#9ca3af" }}>
              Max 50 MB · .bag (ROS1) · .mcap / .db3 (ROS2) · .json · .csv
            </p>
          </div>
        </label>

        {file && (
          <div style={{ background: "#f0fdf4", padding: "10px 14px", borderRadius: 6, fontSize: 13, color: "#16a34a" }}>
            Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}

        {error && <p style={{ color: "#dc2626", margin: 0, fontSize: 14 }}>{error}</p>}

        <button type="submit" disabled={uploading || !file} style={{ ...btnStyle, opacity: uploading || !file ? 0.6 : 1, cursor: uploading || !file ? "not-allowed" : "pointer" }}>
          {uploading ? "Uploading..." : "Upload and run evaluation"}
        </button>
      </form>
    </div>
  );
}

const labelStyle: React.CSSProperties = { marginBottom: 6, fontWeight: 500, fontSize: 14 };
const inputStyle: React.CSSProperties = { width: "100%", padding: "9px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, boxSizing: "border-box" };
const btnStyle: React.CSSProperties = { background: "#111", color: "#fff", padding: "11px 0", borderRadius: 6, border: "none", fontSize: 14, marginTop: 4 };
