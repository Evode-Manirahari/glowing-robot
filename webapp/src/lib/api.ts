const BASE = "";

function getToken(): string | null {
  return localStorage.getItem("token");
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json() as T;
}

// Auth
export async function register(email: string, name: string, password: string) {
  return request<{ access_token: string; user_id: string; name: string; email: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, name, password }),
  });
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Login failed");
  }
  return res.json() as Promise<{ access_token: string; user_id: string; name: string; email: string }>;
}

export async function getMe() {
  return request<{ id: string; email: string; name: string }>("/auth/me");
}

// API Keys
export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  key: string; // shown once
}

export async function listApiKeys(): Promise<ApiKey[]> {
  return request<ApiKey[]>("/auth/api-keys");
}

export async function createApiKey(name: string): Promise<ApiKeyCreated> {
  return request<ApiKeyCreated>("/auth/api-keys", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function revokeApiKey(id: string): Promise<void> {
  return request<void>(`/auth/api-keys/${id}`, { method: "DELETE" });
}

// Missions
export interface Mission {
  id: string;
  name: string;
  robot_type: string;
  uploaded_at: string;
  status: string;
  log_filename: string;
  verdict: string | null;
}

export async function listMissions(params?: { verdict?: string; q?: string }): Promise<Mission[]> {
  const search = new URLSearchParams();
  if (params?.verdict) search.set("verdict", params.verdict);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  return request<Mission[]>(`/missions/${qs ? "?" + qs : ""}`);
}

export async function downloadReport(missionId: string): Promise<void> {
  const token = localStorage.getItem("token");
  const res = await fetch(`/missions/${missionId}/report/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = res.headers.get("Content-Disposition")?.match(/filename="(.+)"/)?.[1] ?? "report.json";
  a.click();
  URL.revokeObjectURL(url);
}

export async function getMission(id: string): Promise<Mission> {
  return request<Mission>(`/missions/${id}`);
}

export async function uploadMission(
  name: string,
  robotType: string,
  file: File,
): Promise<{ mission_id: string; job_id: string; message: string }> {
  const form = new FormData();
  form.append("log_file", file);
  const res = await fetch(`/missions/upload?name=${encodeURIComponent(name)}&robot_type=${encodeURIComponent(robotType)}`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Upload failed");
  }
  return res.json();
}

export async function deleteMission(id: string): Promise<void> {
  return request<void>(`/missions/${id}`, { method: "DELETE" });
}

// Jobs
export interface Job {
  id: string;
  mission_id: string;
  type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

export async function getJob(id: string): Promise<Job> {
  return request<Job>(`/jobs/${id}`);
}

// Evals
export interface EvalReport {
  mission_id: string;
  verdict: string;
  collision_count: number;
  max_deviation_m: number;
  completion_rate: number;
  duration_s: number;
  frame_count: number;
  anomalies: string[];
  collision_times: number[];
  ai_summary: string | null;
}

export async function getEvalReport(missionId: string): Promise<EvalReport> {
  return request<EvalReport>(`/evals/${missionId}/report`);
}

export async function requestAiSummary(missionId: string): Promise<void> {
  return request<void>(`/evals/${missionId}/summarize`, { method: "POST" });
}

// Replay frames
export interface ReplayFrame {
  t: number;
  x: number;
  y: number;
  theta: number;
  velocity: number;
}

export async function getReplayData(missionId: string): Promise<{ frames: ReplayFrame[]; waypoints: { x: number; y: number }[]; obstacles: { x: number; y: number; radius: number }[]; collision_times: number[] }> {
  return request(`/missions/${missionId}/replay`);
}

// Policy comparison
export interface CompareResponse {
  report_a: EvalReport;
  report_b: EvalReport;
  mission_a_name: string;
  mission_b_name: string;
  comparison_summary: string;
}

export async function compareMissions(missionA: string, missionB: string): Promise<CompareResponse> {
  return request<CompareResponse>(`/evals/compare?mission_a=${missionA}&mission_b=${missionB}`);
}
