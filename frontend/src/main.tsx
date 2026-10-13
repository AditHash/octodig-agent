import { FormEvent, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { cancelResearchRun, createOffering, createTarget, getResearchReport, getResearchRun, listOfferings, listTargets, login, Offering, register, ResearchReport, ResearchRun, startResearch, streamResearchEvents, Target } from "./api";
import "./styles.css";
import "./forms.css";
import { getProfile, listResearchRuns } from "./api";
import { ReportView } from "./ReportView";

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
  const [tab, setTab] = useState<"accounts" | "runs" | "catalog" | "reports" | "settings">("accounts");
  const [targets, setTargets] = useState<Target[]>([]);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [profile, setProfile] = useState<{ name: string; email: string; workspace: string; role: string } | null>(null);
  const [selected, setSelected] = useState<Target | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [activeRun, setActiveRun] = useState<ResearchRun | null>(null);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [runActivity, setRunActivity] = useState("");
  const pending = useRef<{ signature: string; key: string } | null>(null);
  const terminal = (status: string) => ["completed", "completed_partial", "failed", "cancelled", "budget_exceeded"].includes(status);
  const reportAvailable = (status: string) => ["completed", "completed_partial", "budget_exceeded"].includes(status);
  function showError(cause: unknown) { setError(cause instanceof Error ? cause.message : "Request failed"); }
  useEffect(() => {
    let disposed = false;
    Promise.all([listTargets(token), listResearchRuns(token), getProfile(token)]).then(([accounts, history, identity]) => {
      if (!disposed) { setTargets(accounts); setRuns(history); setProfile(identity); }
    }).catch(cause => { if (!disposed) showError(cause); });
    return () => { disposed = true; };
  }, [token]);
  useEffect(() => {
    if (!activeRun || terminal(activeRun.status)) return;
    const runId = activeRun.id;
    let disposed = false;
    let lastEvent: string | null = null;
    let retryTimer: number | undefined;
    const controller = new AbortController();
    const refresh = async () => {
      const run = await getResearchRun(token, runId);
      if (disposed) return true;
      setActiveRun(run); setRuns(items => items.map(item => item.id === run.id ? run : item));
      if (reportAvailable(run.status)) setRunActivity("Report is ready.");
      else if (run.status === "cancelled") setRunActivity("Research cancelled.");
      else if (run.status === "failed") setRunActivity("Research stopped with an error.");
      return terminal(run.status);
    };
    const describe = (type: string) => {
      const messages: Record<string, string> = {
      "run.queued": "Research is queued.",
      "run.started": "Research worker started.",
      "run.reclaimed": "Research resumed after worker recovery.",
      "budget.reserved": "Research budget reserved.",
      "research.provider_call_started": "Gathering provider research.",
      "research.evidence_verification_started": "Verifying source support.",
      "report.ready": "Report is ready.",
      "run.partial": "Research completed with documented gaps.",
      "run.failed": "Research stopped with an error.",
      "run.cancel_requested": "Cancellation requested.",
      "run.cancelled": "Research cancelled.",
      };
      return messages[type] || "Research progress updated.";
    };
    const follow = async () => {
      try {
        lastEvent = await streamResearchEvents(token, runId, lastEvent, controller.signal, event => {
          if (!disposed) { setRunActivity(describe(event.type)); void refresh().catch(showError); }
        });
        if (await refresh()) return;
      } catch (cause) {
        if (disposed || controller.signal.aborted) return;
        setRunActivity("Live updates reconnecting.");
        showError(cause);
      }
      if (!disposed) retryTimer = window.setTimeout(() => { void follow(); }, 300);
    };
    setRunActivity("Waiting for research updates.");
    void follow();
    return () => { disposed = true; controller.abort(); if (retryTimer !== undefined) window.clearTimeout(retryTimer); };
  }, [activeRun?.id, token]);
  async function addTarget(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return;
    const form = new FormData(event.currentTarget); setBusy(true); setError("");
    try { const item = await createTarget(token, { name: String(form.get("name")), website: String(form.get("website")) || undefined, notes: String(form.get("notes")) || undefined }); setTargets(items => [item, ...items]); setShowCreate(false); }
    catch (cause) { showError(cause); } finally { setBusy(false); }
  }
  async function queue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected || busy) return;
    const form = new FormData(event.currentTarget);
    const input = { provider: String(form.get("provider")) as "openai" | "gemini", mode: String(form.get("mode")) as "standard" | "deep", max_cost_usd: String(form.get("maxCost")) };
    const signature = JSON.stringify({ target: selected.id, ...input });
    if (pending.current?.signature !== signature) pending.current = { signature, key: crypto.randomUUID() };
    setBusy(true); setError("");
    try { const run = await startResearch(token, selected.id, input, pending.current.key); pending.current = null; setSelected(null); setReport(null); setRunActivity("Research is queued."); setActiveRun(run); setRuns(items => [run, ...items.filter(item => item.id !== run.id)]); setTab("runs"); }
    catch (cause) { showError(cause); } finally { setBusy(false); }
  }
  async function openRun(run: ResearchRun) {
    setActiveRun(run); setReport(null); setError("");
    if (reportAvailable(run.status)) { try { setReport(await getResearchReport(token, run.id)); setTab("reports"); } catch (cause) { showError(cause); } }
    else setTab("runs");
  }
  async function cancel() { if (!activeRun) return; setBusy(true); try { const run = await cancelResearchRun(token, activeRun.id); setActiveRun(run); setRuns(items => items.map(item => item.id === run.id ? run : item)); } catch (cause) { showError(cause); } finally { setBusy(false); } }
  async function moreRuns() { try { const next = await listResearchRuns(token, runs.length); setRuns(items => [...items, ...next]); } catch (cause) { showError(cause); } }
  return <main className="app-shell"><aside><div className="brand">octo<span>dig</span></div><nav aria-label="Main navigation">{(["accounts", "runs", "catalog", "reports", "settings"] as const).map(item => <button className={tab === item ? "active" : ""} key={item} onClick={() => setTab(item)} aria-current={tab === item ? "page" : undefined}>{({ accounts: "Accounts", runs: "Research runs", catalog: "Seller catalog", reports: "Reports", settings: "Settings" })[item]}</button>)}</nav><button className="text-button" onClick={onLogout}>Sign out</button></aside>
    <section className="workspace"><header><div><p className="eyebrow">{profile?.workspace || "Workspace"}</p><h1>{({ accounts: "Target accounts", runs: "Research history", catalog: "Seller catalog", reports: "Evidence reports", settings: "Workspace settings" })[tab]}</h1><p>Inspect findings, sources, uncertainty, and seller fit.</p></div>{tab === "accounts" && <button onClick={() => setShowCreate(!showCreate)}>{showCreate ? "Close form" : "New target"}</button>}</header>
    {error && <p className="error" role="alert">{error}</p>}
    {activeRun && <section className="run-panel" aria-live="polite"><div><strong>{activeRun.status.replaceAll("_", " ")}</strong><span>{targets.find(item => item.id === activeRun.account_id)?.name || activeRun.account_id} · {activeRun.provider} · Attempt {activeRun.attempts}</span>{runActivity && <span>{runActivity}</span>}{activeRun.error_code && <span>{activeRun.error_code}</span>}</div>{!terminal(activeRun.status) && <button disabled={busy || activeRun.status === "cancel_requested"} onClick={cancel}>{activeRun.status === "cancel_requested" ? "Cancellation requested" : "Cancel research"}</button>}{reportAvailable(activeRun.status) && <button onClick={() => openRun(activeRun)}>View report</button>}</section>}
    {tab === "accounts" && <>{showCreate && <form className="panel-form" onSubmit={addTarget}><h2>New target</h2><label>Company name<input name="name" required maxLength={200} /></label><label>Official website<input name="website" type="url" /></label><label>Notes<textarea name="notes" maxLength={5000} /></label><button disabled={busy}>Create target</button></form>}
    {selected && <form className="panel-form" onSubmit={queue}><h2>Research {selected.name}</h2><label>Provider<select name="provider"><option value="openai">OpenAI</option><option value="gemini">Gemini</option></select></label><label>Depth<select name="mode"><option value="standard">Standard</option><option value="deep">Deep</option></select></label><label>Maximum cost USD<input name="maxCost" type="number" min="0.01" step="0.01" defaultValue="0.05" required /></label><button disabled={busy}>{busy ? "Queueing…" : "Queue research"}</button><button type="button" className="secondary" onClick={() => setSelected(null)}>Close</button></form>}
    {targets.length ? <ul className="target-list">{targets.map(target => <li key={target.id}><div><strong>{target.name}</strong><span>{target.normalized_domain || "No website supplied"}</span></div><button onClick={() => setSelected(target)}>Research</button></li>)}</ul> : <p>No target accounts yet. Add a company to begin research.</p>}</>}
    {tab === "catalog" && <OfferingPanel token={token} />}
    {(tab === "runs" || (tab === "reports" && !report)) && <><ul className="target-list">{runs.filter(run => tab === "runs" || reportAvailable(run.status)).map(run => <li key={run.id}><div><strong>{targets.find(item => item.id === run.account_id)?.name || run.account_id}</strong><span>{run.status.replaceAll("_", " ")} · {run.provider} · {run.mode}</span></div><button onClick={() => openRun(run)}>{reportAvailable(run.status) ? "Read report" : "View status"}</button></li>)}</ul>{!runs.length && <p>No research runs yet.</p>}{runs.length >= 50 && <button className="secondary" onClick={moreRuns}>Load older runs</button>}</>}
    {tab === "reports" && report && <><button className="secondary" onClick={() => setReport(null)}>Back to reports</button><ReportView report={report} token={token} /></>}
    {tab === "settings" && profile && <section className="report-panel"><h2>{profile.workspace}</h2><p>Name: {profile.name}</p><p>Email: {profile.email}</p><p>Workspace role: {profile.role.replaceAll("_", " ")}</p><p>Only approved seller offerings are available to research. Provider configuration and pricing are managed by your application operator.</p></section>}
    </section></main>;
}
function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  return token ? <Dashboard token={token} onLogout={() => { localStorage.removeItem(TOKEN_KEY); setToken(null); }} /> : <Auth onAuthenticated={setToken} />;
}

createRoot(document.getElementById("root")!).render(<App />);
