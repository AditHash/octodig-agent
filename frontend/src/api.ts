const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type TokenResponse = { access_token: string; token_type: "bearer" };
export type Target = { id: string; name: string; website: string | null; normalized_domain: string | null; notes: string; tags: string[] };
export type ResearchRun = { id: string; status: string; provider: string; mode: string; account_id: string; error_code: string | null; attempts: number };
export type ResearchReport = {
  metadata?: {
    estimated_cost_usd?: string;
    reserved_cost_usd?: string;
    input_tokens?: number;
    output_tokens?: number;
    reasoning_tokens?: number;
    search_calls?: number;
    duration_ms?: number;
  };
  gaps?: string[];
  sources?: { id: string; title?: string; url: string; publisher?: string }[];
  sections?: Record<string, { status: string; gaps: string[]; claim_ids: string[] }>;
};

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

export function startResearch(token: string, targetId: string, input: { provider: "openai" | "gemini"; mode: "standard" | "deep"; max_cost_usd: string }) {
  return request<ResearchRun>(`/api/v1/targets/${targetId}/research`, { method: "POST", body: JSON.stringify(input) }, token);
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
