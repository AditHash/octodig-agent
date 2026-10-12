import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { cancelResearchRun, createOffering, createTarget, getResearchReport, getResearchRun, listOfferings, listTargets, login, Offering, register, ResearchReport, ResearchRun, startResearch, Target } from "./api";
import "./styles.css";
import "./forms.css";

const TOKEN_KEY = "octodig.access-token";

function OfferingPanel({ token }: { token: string }) {
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { listOfferings(token).then(setOfferings).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load seller catalog")); }, [token]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const split = (field: string) => String(form.get(field)).split(",").map(value => value.trim()).filter(Boolean);
    try {
      const offering = await createOffering(token, { name: String(form.get("name")), description: String(form.get("description")), capabilities: split("capabilities"), business_outcomes: split("outcomes"), approved: form.get("approved") === "on" });
      setOfferings([...offerings, offering].sort((left, right) => left.name.localeCompare(right.name)));
      setOpen(false);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not create offering"); }
  }
  return <section className="catalog-panel" id="offerings"><div className="section-heading"><div><p className="eyebrow">Seller catalog</p><h2>Approved offerings</h2></div><button className="secondary" onClick={() => setOpen(!open)}>{open ? "Close" : "Add offering"}</button></div>{error && <p className="error" role="alert">{error}</p>}{open && <form className="panel-form" onSubmit={submit}><label>Name<input name="name" required /></label><label>Description<textarea name="description" required /></label><label>Capabilities <input name="capabilities" placeholder="Comma-separated" /></label><label>Business outcomes <input name="outcomes" placeholder="Comma-separated" /></label><label className="check"><input name="approved" type="checkbox" /> Approved for agent matching</label><button>Save offering</button></form>}{offerings.length === 0 ? <p className="helper">No offerings yet. The agent will label ideas as unmatched until you approve catalog entries.</p> : <ul className="offering-list">{offerings.map(offering => <li key={offering.id}><strong>{offering.name}</strong><span>{offering.approved ? "Approved for matching" : "Draft — not used by research"}</span><p>{offering.description}</p></li>)}</ul>}</section>;
}

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
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<Target | null>(null);
  const [notice, setNotice] = useState("");
  const [activeRun, setActiveRun] = useState<ResearchRun | null>(null);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [queueing, setQueueing] = useState(false);
  useEffect(() => { listTargets(token).then(setTargets).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load targets")); }, [token]);
  useEffect(() => {
    if (!activeRun || ["completed", "completed_partial", "failed", "cancelled", "budget_exceeded"].includes(activeRun.status)) return;
    const interval = window.setInterval(() => getResearchRun(token, activeRun.id).then(setActiveRun).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not refresh research status")), 2000);
    return () => window.clearInterval(interval);
  }, [activeRun, token]);
  async function addTarget(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { const item = await createTarget(token, { name: String(form.get("name")), website: String(form.get("website")) || undefined, notes: String(form.get("notes")) || undefined }); setTargets([item, ...targets]); setShowCreate(false); setNotice("Target created."); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not create target"); } }
  async function queue(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!selected || queueing) return; const form = new FormData(event.currentTarget); setQueueing(true); try { const run = await startResearch(token, selected.id, { provider: String(form.get("provider")) as "openai" | "gemini", mode: "standard", max_cost_usd: String(form.get("maxCost")) }, crypto.randomUUID()); setSelected(null); setReport(null); setActiveRun(run); setNotice(`Research ${run.id} queued.`); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not queue research"); } finally { setQueueing(false); } }
  async function cancelActiveRun() { if (!activeRun) return; try { setActiveRun(await cancelResearchRun(token, activeRun.id)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not cancel research"); } }
  async function loadReport() { if (!activeRun) return; try { setReport(await getResearchReport(token, activeRun.id)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Report is not available yet"); } }
  const terminal = activeRun && ["completed", "completed_partial", "failed", "cancelled", "budget_exceeded"].includes(activeRun.status);
  return <main className="app-shell"><aside><div className="brand">octo<span>dig</span></div><nav aria-label="Main navigation"><a className="active" href="#accounts">Accounts</a><a href="#research">Research runs</a><a href="#offerings">Seller catalog</a><a href="#reports">Reports</a><a href="#settings">Settings</a></nav><button className="text-button" onClick={onLogout}>Sign out</button></aside><section className="workspace"><header><div><p className="eyebrow">Workspace</p><h1>Target accounts</h1><p>Research stays traceable from source to claim to sales opportunity.</p></div><button onClick={() => setShowCreate(true)}>New target</button></header>{notice && <p className="notice">{notice}</p>}{error && <p className="error" role="alert">{error}</p>}{activeRun && <section className="run-panel" aria-live="polite"><div><p className="eyebrow">Research run</p><strong>{activeRun.status.replaceAll("_", " ")}</strong><span>{activeRun.provider} · attempt {activeRun.attempts}</span></div>{!terminal && <button className="secondary" onClick={cancelActiveRun}>Cancel research</button>}{terminal && <button onClick={loadReport}>View report</button>}</section>}{showCreate && <form className="panel-form" onSubmit={addTarget}><h2>New target</h2><label>Company name<input name="name" required /></label><label>Official website<input name="website" type="url" /></label><label>Notes<textarea name="notes" /></label><button>Create target</button></form>}{selected && <form className="panel-form" onSubmit={queue}><h2>Research {selected.name}</h2><label>Provider<select name="provider"><option value="openai">OpenAI</option><option value="gemini">Gemini</option></select></label><label>Maximum cost USD<input name="maxCost" type="number" min="0.01" step="0.01" defaultValue="0.05" required /></label><p className="helper">Configured provider worst-case cost must fit this cap.</p><button disabled={queueing}>{queueing ? "Queueing…" : "Queue research"}</button></form>}{report && <section className="report-panel" id="reports"><h2>Evidence report</h2>{report.metadata?.estimated_cost_usd && <p>Estimated provider cost: ${report.metadata.estimated_cost_usd}</p>}{report.metadata?.reserved_cost_usd && <p>Reserved cost ceiling: ${report.metadata.reserved_cost_usd}</p>}{report.metadata && <p>{report.metadata.input_tokens ?? "Unknown"} input tokens · {report.metadata.output_tokens ?? "Unknown"} output tokens · {report.metadata.search_calls ?? "Unknown"} searches{report.metadata.duration_ms !== undefined ? ` · ${(report.metadata.duration_ms / 1000).toFixed(1)}s` : ""}</p>}{report.gaps && report.gaps.length > 0 && <><h3>Gaps and limits</h3><ul>{report.gaps.map(gap => <li key={gap}>{gap}</li>)}</ul></>}{report.sections && <><h3>Required sections</h3><ul>{Object.entries(report.sections).map(([key, section]) => <li key={key}><strong>{key.replaceAll("_", " ")}</strong><span>{section.status}{section.gaps.length > 0 ? `: ${section.gaps.join(" ")}` : ""}</span></li>)}</ul></>}{report.sources && <><h3>Sources</h3><ul>{report.sources.map(source => <li key={source.id}><a href={source.url} target="_blank" rel="noreferrer">{source.title || source.url}</a>{source.publisher && <span>{source.publisher}</span>}</li>)}</ul></>}</section>}<OfferingPanel token={token} />{targets.length === 0 ? <section className="empty"><h2>Start with a target account</h2><p>Add a company, then start a bounded research run. Every report retains sources, gaps, and costs.</p><button onClick={() => setShowCreate(true)}>New target</button></section> : <ul className="target-list">{targets.map(target => <li key={target.id}><div><strong>{target.name}</strong><span>{target.normalized_domain ?? "Website not supplied"}</span></div><button onClick={() => setSelected(target)}>Research</button></li>)}</ul>}</section></main>;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  return token ? <Dashboard token={token} onLogout={() => { localStorage.removeItem(TOKEN_KEY); setToken(null); }} /> : <Auth onAuthenticated={setToken} />;
}

createRoot(document.getElementById("root")!).render(<App />);
