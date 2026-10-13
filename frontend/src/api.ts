const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type TokenResponse = { access_token: string; token_type: "bearer" };
export type Target = { id: string; name: string; website: string | null; normalized_domain: string | null; notes: string; tags: string[] };
export type Offering = { id: string; name: string; description: string; capabilities: string[]; business_outcomes: string[]; approved: boolean; version: number };
export type ResearchRun = { id: string; status: string; provider: string; mode: string; account_id: string; error_code: string | null; attempts: number };
export type ResearchEvent = { id: string; type: string; data: Record<string, unknown> };
export type ResearchReport = {
  run_id: string;
  target: { name: string; identity_status: string; website: string | null };
  claims: { id: string; section: string; statement: string; classification: string; verification_status: string; source_ids: string[]; rationale: string | null }[];
  opportunities: { id: string; title: string; need_kind: string; offering_id: string | null; priority: string; rationale: string; supporting_claim_ids: string[]; gaps: string[]; discovery_questions: string[] }[];
  metadata?: {
    estimated_cost_usd?: string;
    reserved_cost_usd?: string;
    input_tokens?: number;
    output_tokens?: number;
    reasoning_tokens?: number;
    search_calls?: number;
    model_calls?: number;
    tool_actions?: { name: string; provider: string; calls: number }[];
    delegates_used?: string[];
    duration_ms?: number;
  };
  gaps?: string[];
  sources?: { id: string; title?: string; url: string; publisher?: string }[];
  sections?: Record<string, { status: string; gaps: string[]; claim_ids: string[] }>;
};

export function listResearchRuns(token: string, offset = 0) {
  return request<ResearchRun[]>(`/api/v1/runs?offset=${offset}&limit=50`, {}, token);
}

export function getProfile(token: string) {
  return request<{ name: string; email: string; workspace: string; role: string }>("/api/v1/me", {}, token);
}

export async function downloadMarkdown(token: string, runId: string) {
  const response = await fetch(`${API_URL}/api/v1/runs/${runId}/report.md`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error("Markdown report unavailable");
  return response.text();
}

export async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : "Request failed");
  }
  return response.json() as Promise<T>;
}

export function login(email: string, password: string) {
  return request<TokenResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function register(email: string, name: string, password: string, workspace_name: string) {
  return request<TokenResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify({ email, name, password, workspace_name }) });
}

export function listTargets(token: string) {
  return request<Target[]>("/api/v1/targets", {}, token);
}

export function createTarget(token: string, input: { name: string; website?: string; notes?: string }) {
  return request<Target>("/api/v1/targets", { method: "POST", body: JSON.stringify(input) }, token);
}

export function listOfferings(token: string) {
  return request<Offering[]>("/api/v1/offerings", {}, token);
}

export function createOffering(token: string, input: Omit<Offering, "id" | "version">) {
  return request<Offering>("/api/v1/offerings", { method: "POST", body: JSON.stringify(input) }, token);
}

export function startResearch(token: string, targetId: string, input: { provider: "openai" | "gemini"; mode: "standard" | "deep"; max_cost_usd: string }, idempotencyKey: string) {
  return request<ResearchRun>(`/api/v1/targets/${targetId}/research`, { method: "POST", body: JSON.stringify(input), headers: { "Idempotency-Key": idempotencyKey } }, token);
}

export function getResearchRun(token: string, runId: string) {
  return request<ResearchRun>(`/api/v1/runs/${runId}`, {}, token);
}

export function cancelResearchRun(token: string, runId: string) {
  return request<ResearchRun>(`/api/v1/runs/${runId}/cancel`, { method: "POST" }, token);
}

export function getResearchReport(token: string, runId: string) {
  return request<ResearchReport>(`/api/v1/runs/${runId}/report`, {}, token);
}

export async function streamResearchEvents(
  token: string,
  runId: string,
  after: string | null,
  signal: AbortSignal,
  onEvent: (event: ResearchEvent) => void,
): Promise<string | null> {
  const query = after ? `?after=${encodeURIComponent(after)}` : "";
  const response = await fetch(`${API_URL}/api/v1/runs/${runId}/events${query}`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream" }, signal,
  });
  if (!response.ok || !response.body) throw new Error("Live research updates are unavailable");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let lastEvent = after;
  let id = "";
  let type = "message";
  let data = "";
  function dispatch() {
    if (!data) return;
    try { onEvent({ id, type, data: JSON.parse(data) as Record<string, unknown> }); lastEvent = id || lastEvent; }
    catch { /* Ignore malformed event payloads; the run-status refresh remains authoritative. */ }
    id = ""; type = "message"; data = "";
  }
  while (true) {
    const next = await reader.read();
    buffer += decoder.decode(next.value || new Uint8Array(), { stream: !next.done });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const rawLine of lines) {
      const line = rawLine.endsWith("\r") ? rawLine.slice(0, -1) : rawLine;
      if (!line) { dispatch(); continue; }
      if (line.startsWith("id:")) id = line.slice(3).trim();
      else if (line.startsWith("event:")) type = line.slice(6).trim();
      else if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (next.done) { dispatch(); return lastEvent; }
  }
}
