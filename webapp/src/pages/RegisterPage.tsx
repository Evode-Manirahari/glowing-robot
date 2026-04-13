import { useState, FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (password.length < 8) { setError("Password must be at least 8 characters"); return; }
    setLoading(true);
    setError(null);
    try {
      await register(email, name, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto" }}>
      <h1 style={{ marginBottom: 8 }}>Create account</h1>
      <p style={{ color: "#6b7280", marginBottom: 32 }}>glowing-robot — Robot QA platform</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <label>
          <div style={labelStyle}>Name</div>
          <input value={name} onChange={e => setName(e.target.value)} required style={inputStyle} placeholder="Jane Smith" />
        </label>
        <label>
          <div style={labelStyle}>Email</div>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={inputStyle} placeholder="you@company.com" />
        </label>
        <label>
          <div style={labelStyle}>Password</div>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={inputStyle} placeholder="8+ characters" />
        </label>
        {error && <p style={{ color: "#dc2626", margin: 0, fontSize: 14 }}>{error}</p>}
        <button type="submit" disabled={loading} style={btnStyle}>{loading ? "Creating..." : "Create account"}</button>
      </form>

      <p style={{ marginTop: 24, color: "#6b7280", fontSize: 14 }}>
        Already have an account? <Link to="/login" style={{ color: "#111" }}>Sign in</Link>
      </p>
    </div>
  );
}

const labelStyle: React.CSSProperties = { marginBottom: 4, fontWeight: 500, fontSize: 14 };
const inputStyle: React.CSSProperties = { width: "100%", padding: "9px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, boxSizing: "border-box" };
const btnStyle: React.CSSProperties = { background: "#111", color: "#fff", padding: "10px 0", borderRadius: 6, border: "none", fontSize: 14, cursor: "pointer", marginTop: 4 };
