const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type TokenResponse = { access_token: string; token_type: "bearer" };
export type Target = { id: string; name: string; website: string | null; normalized_domain: string | null; notes: string; tags: string[] };

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
