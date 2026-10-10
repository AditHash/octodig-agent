import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { listTargets, login, register, Target } from "./api";
import "./styles.css";

const TOKEN_KEY = "octodig.access-token";

function Auth({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true); setError("");
    try {
      const result = mode === "login"
        ? await login(String(form.get("email")), String(form.get("password")))
        : await register(String(form.get("email")), String(form.get("name")), String(form.get("password")), String(form.get("workspace")));
      localStorage.setItem(TOKEN_KEY, result.access_token);
      onAuthenticated(result.access_token);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not authenticate"); }
    finally { setLoading(false); }
  }

  return <main className="auth-shell"><section className="auth-copy"><p className="eyebrow">Evidence-first account research</p><h1>Know why to reach out.</h1><p>OctoDig turns public evidence into inspectable sales preparation—without hiding uncertainty.</p></section><section className="auth-card"><h2>{mode === "login" ? "Welcome back" : "Create workspace"}</h2><form onSubmit={submit}>{mode === "register" && <><label>Name<input required name="name" autoComplete="name" /></label><label>Workspace<input required name="workspace" /></label></>}<label>Email<input required type="email" name="email" autoComplete="email" /></label><label>Password<input required type="password" name="password" minLength={12} autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>{error && <p className="error" role="alert">{error}</p>}<button disabled={loading}>{loading ? "Working…" : mode === "login" ? "Sign in" : "Create account"}</button></form><button className="text-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Need a workspace? Register" : "Already registered? Sign in"}</button></section></main>;
}

function Dashboard({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [targets, setTargets] = useState<Target[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { listTargets(token).then(setTargets).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load targets")); }, [token]);
  return <main className="app-shell"><aside><div className="brand">octo<span>dig</span></div><nav aria-label="Main navigation"><a className="active" href="#accounts">Accounts</a><a href="#research">Research runs</a><a href="#offerings">Seller catalog</a><a href="#reports">Reports</a><a href="#settings">Settings</a></nav><button className="text-button" onClick={onLogout}>Sign out</button></aside><section className="workspace"><header><div><p className="eyebrow">Workspace</p><h1>Target accounts</h1><p>Research stays traceable from source to claim to sales opportunity.</p></div><button>New target</button></header>{error ? <p className="error" role="alert">{error}</p> : targets.length === 0 ? <section className="empty"><h2>Start with a target account</h2><p>Add a company, then start a bounded research run. Every report retains sources, gaps, and costs.</p><button>New target</button></section> : <ul className="target-list">{targets.map(target => <li key={target.id}><div><strong>{target.name}</strong><span>{target.normalized_domain ?? "Website not supplied"}</span></div><span className="status">Ready for research</span></li>)}</ul>}</section></main>;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  return token ? <Dashboard token={token} onLogout={() => { localStorage.removeItem(TOKEN_KEY); setToken(null); }} /> : <Auth onAuthenticated={setToken} />;
}

createRoot(document.getElementById("root")!).render(<App />);
