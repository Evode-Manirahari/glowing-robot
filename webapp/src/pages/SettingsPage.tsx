import { useEffect, useState, FormEvent } from "react";
import { useAuth } from "../lib/auth";
import { listApiKeys, createApiKey, revokeApiKey, type ApiKey, type ApiKeyCreated } from "../lib/api";

export default function SettingsPage() {
  const { user } = useAuth();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listApiKeys().then(setKeys).catch(() => {});
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const key = await createApiKey(newKeyName.trim());
      setCreatedKey(key);
      setKeys(prev => [key, ...prev]);
      setNewKeyName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create key");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(id: string, name: string) {
    if (!confirm(`Revoke API key "${name}"? Any scripts using it will stop working.`)) return;
    await revokeApiKey(id);
    setKeys(prev => prev.filter(k => k.id !== id));
    if (createdKey?.id === id) setCreatedKey(null);
  }

  function copyKey() {
    if (!createdKey) return;
    navigator.clipboard.writeText(createdKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h1 style={{ marginBottom: 32 }}>Settings</h1>

      {/* Account */}
      <section style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Account</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Field label="Name" value={user?.name ?? ""} />
          <Field label="Email" value={user?.email ?? ""} />
        </div>
      </section>

      <hr style={{ border: "none", borderTop: "1px solid #e5e7eb", marginBottom: 40 }} />

      {/* API Keys */}
      <section>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>API Keys</h2>
        <p style={{ color: "#6b7280", fontSize: 14, marginBottom: 20 }}>
          Use API keys to upload missions and poll results from your CI/CD pipeline.
          Keys inherit your account permissions.
        </p>

        {/* Usage example */}
        <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, padding: "12px 16px", marginBottom: 24, fontFamily: "monospace", fontSize: 13, color: "#374151", overflowX: "auto" }}>
          <div style={{ color: "#9ca3af", marginBottom: 6 }}># Upload from CI</div>
          <div>curl -X POST https://your-host/missions/upload \</div>
          <div style={{ paddingLeft: 16 }}>-H "X-Api-Key: gr_live_..." \</div>
          <div style={{ paddingLeft: 16 }}>-F "name=deploy-v2.1.3" \</div>
          <div style={{ paddingLeft: 16 }}>-F "robot_type=AMR" \</div>
          <div style={{ paddingLeft: 16 }}>-F "log_file=@mission.json"</div>
        </div>

        {/* New key created banner */}
        {createdKey && (
          <div style={{ background: "#f0fdf4", border: "1px solid #86efac", borderRadius: 8, padding: 16, marginBottom: 24 }}>
            <div style={{ fontWeight: 600, fontSize: 14, color: "#15803d", marginBottom: 8 }}>
              API key created — copy it now, it won't be shown again.
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <code style={{ flex: 1, background: "#fff", border: "1px solid #d1d5db", borderRadius: 6, padding: "8px 12px", fontSize: 13, wordBreak: "break-all" }}>
                {createdKey.key}
              </code>
              <button
                onClick={copyKey}
                style={{ padding: "8px 14px", background: "#111", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13, whiteSpace: "nowrap" }}
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        )}

        {/* Create form */}
        <form onSubmit={handleCreate} style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          <input
            value={newKeyName}
            onChange={e => setNewKeyName(e.target.value)}
            placeholder='Key name, e.g. "CI pipeline"'
            required
            style={{ flex: 1, padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14 }}
          />
          <button
            type="submit"
            disabled={creating || !newKeyName.trim()}
            style={{ padding: "8px 16px", background: "#111", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14, opacity: creating || !newKeyName.trim() ? 0.6 : 1 }}
          >
            {creating ? "Creating..." : "Create key"}
          </button>
        </form>

        {error && <p style={{ color: "#dc2626", fontSize: 14, marginBottom: 16 }}>{error}</p>}

        {/* Keys list */}
        {keys.length === 0 ? (
          <p style={{ color: "#9ca3af", fontSize: 14 }}>No API keys yet.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e5e7eb", textAlign: "left", fontSize: 12, color: "#6b7280" }}>
                <th style={{ padding: "6px 0", fontWeight: 500 }}>Name</th>
                <th style={{ fontWeight: 500 }}>Prefix</th>
                <th style={{ fontWeight: 500 }}>Created</th>
                <th style={{ fontWeight: 500 }}>Last used</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {keys.map(k => (
                <tr key={k.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "10px 0", fontSize: 14, fontWeight: 500 }}>{k.name}</td>
                  <td style={{ fontFamily: "monospace", fontSize: 13, color: "#6b7280" }}>{k.key_prefix}...</td>
                  <td style={{ fontSize: 13, color: "#6b7280" }}>{new Date(k.created_at).toLocaleDateString()}</td>
                  <td style={{ fontSize: 13, color: "#6b7280" }}>
                    {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : "Never"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button
                      onClick={() => handleRevoke(k.id, k.name)}
                      style={{ background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: 13 }}
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 12, fontWeight: 500, color: "#6b7280", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 14, padding: "8px 12px", background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 6 }}>{value}</div>
    </div>
  );
}
