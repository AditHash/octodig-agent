import { useState } from "react";
import { downloadMarkdown, ResearchReport } from "./api";

function download(text: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ReportView({ report, token }: { report: ResearchReport; token: string }) {
  const [error, setError] = useState("");
  const metadata = report.metadata;
  async function exportMarkdown() {
    try { download(await downloadMarkdown(token, report.run_id), `octodig-${report.run_id}.md`, "text/markdown"); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Export failed"); }
  }
  return <article className="report-panel">
    <h2>{report.target.name}</h2><p>Identity: {report.target.identity_status}</p>
    <div className="actions"><button onClick={() => download(JSON.stringify(report, null, 2), `octodig-${report.run_id}.json`, "application/json")}>Download JSON</button><button onClick={exportMarkdown}>Download Markdown</button></div>
    {error && <p role="alert" className="error">{error}</p>}
    <p>Estimated spend: {metadata?.estimated_cost_usd ? `$${metadata.estimated_cost_usd}` : "Unknown"} · Reserved: {metadata?.reserved_cost_usd ? `$${metadata.reserved_cost_usd}` : "Unknown"}</p>
    <p>{metadata?.model_calls ?? "Unknown"} model calls · {metadata?.input_tokens ?? "Unknown"} input tokens · {metadata?.output_tokens ?? "Unknown"} output tokens · {metadata?.search_calls ?? "Unknown"} searches{metadata?.duration_ms != null ? ` · ${(metadata.duration_ms / 1000).toFixed(1)} seconds` : ""}</p>
    {metadata?.delegates_used && <p>Research specialists: {metadata.delegates_used.join(", ") || "none"}</p>}
    {!!report.gaps?.length && <section><h3>Gaps and limitations</h3><ul>{report.gaps.map((gap, i) => <li key={i}>{gap}</li>)}</ul></section>}
    <nav className="section-nav" aria-label="Report sections">{Object.keys(report.sections ?? {}).map(key => <a key={key} href={`#section-${key}`}>{key.replaceAll("_", " ")}</a>)}</nav>
    {Object.entries(report.sections ?? {}).map(([key, section]) => <section id={`section-${key}`} key={key}>
      <h3>{key.replaceAll("_", " ")}</h3><p className="badge">{section.status.replaceAll("_", " ")}</p>
      {section.claim_ids.map(id => { const claim = report.claims.find(item => item.id === id); return claim && <div className="claim" key={id}>
        <span className={`badge ${claim.classification}`}>{claim.classification} · {claim.verification_status.replaceAll("_", " ")}</span>
        <p>{claim.statement}</p>{claim.rationale && <p className="helper">{claim.rationale}</p>}
        <ul>{claim.source_ids.map(sourceId => { const source = report.sources?.find(item => item.id === sourceId); return source && <li key={sourceId}><a href={source.url} rel="noreferrer" target="_blank">{source.title || source.url}</a></li>; })}</ul>
      </div>; })}
      {!!section.gaps.length && <ul>{section.gaps.map((gap, i) => <li key={i}>Gap: {gap}</li>)}</ul>}
    </section>)}
    <section><h3>Sales opportunities</h3>{report.opportunities.length ? report.opportunities.map(item => <div className="claim" key={item.id}>
      <h4>{item.title}</h4><p>{item.need_kind} · {item.priority} · {item.offering_id ? "Matched to approved catalog" : "Unmatched suggestion"}</p><p>{item.rationale}</p>
      <p>Supporting findings: {item.supporting_claim_ids.map(id => report.claims.find(claim => claim.id === id)?.statement).filter(Boolean).join("; ") || "None recorded"}</p>
      <ul>{item.gaps.map((gap, i) => <li key={i}>Gap: {gap}</li>)}</ul><h4>Discovery questions</h4><ul>{item.discovery_questions.map((question, i) => <li key={i}>{question}</li>)}</ul>
    </div>) : <p>No qualified opportunities recorded.</p>}</section>
    <section><h3>Source appendix</h3><ul>{report.sources?.map(source => <li key={source.id}><a href={source.url} rel="noreferrer" target="_blank">{source.title || source.url}</a>{source.publisher && <span>{source.publisher}</span>}</li>)}</ul></section>
  </article>;
}
