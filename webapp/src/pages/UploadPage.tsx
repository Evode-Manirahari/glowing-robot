import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";

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

    const form = new FormData();
    form.append("log_file", file);

    try {
      const res = await fetch(`/missions/upload?name=${encodeURIComponent(name)}&robot_type=${encodeURIComponent(robotType)}`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Upload failed");
      }

      const { mission_id } = await res.json();
      navigate(`/missions/${mission_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{ maxWidth: 480 }}>
      <h1>Upload Mission Log</h1>
      <p style={{ color: "#6b7280", marginBottom: 32 }}>
        Upload a robot trajectory log (.json or .csv) to start a replay and evaluation run.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <label>
          <div style={{ marginBottom: 4, fontWeight: 500 }}>Mission name</div>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="Warehouse run #42"
            style={{ width: "100%", padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, boxSizing: "border-box" }}
          />
        </label>

        <label>
          <div style={{ marginBottom: 4, fontWeight: 500 }}>Robot type</div>
          <select
            value={robotType}
            onChange={(e) => setRobotType(e.target.value)}
            style={{ width: "100%", padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14 }}
          >
            <option value="AMR">AMR (mobile robot)</option>
            <option value="arm">Robot arm / manipulator</option>
            <option value="humanoid">Humanoid</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          <div style={{ marginBottom: 4, fontWeight: 500 }}>Log file (.json or .csv)</div>
          <input
            type="file"
            accept=".json,.csv"
            required
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            style={{ fontSize: 14 }}
          />
        </label>

        {error && <p style={{ color: "#dc2626", margin: 0 }}>{error}</p>}

        <button
          type="submit"
          disabled={uploading}
          style={{ background: "#111", color: "#fff", padding: "10px 20px", borderRadius: 6, border: "none", fontSize: 14, cursor: uploading ? "not-allowed" : "pointer" }}
        >
          {uploading ? "Uploading..." : "Upload and run evaluation"}
        </button>
      </form>
    </div>
  );
}
