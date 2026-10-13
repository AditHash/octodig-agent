"""Deterministic, source-linked Markdown rendering for validated reports."""

from ..report_contract import ResearchReport, SECTION_KEYS


def _heading(value: str) -> str:
    return value.replace("_", " ").title()


def render_markdown(report: ResearchReport) -> str:
    claims = {claim.id: claim for claim in report.claims}
    sources = {source.id: source for source in report.sources}
    lines = [
        f"# Account research: {report.target.name}",
        "",
        f"Run: `{report.run_id}`  ",
        f"Identity: {report.target.identity_status}  ",
        f"Mode: {report.mode}",
        "",
    ]
    if report.metadata.model_calls is not None:
        lines.extend([f"Model calls: {report.metadata.model_calls}", ""])
    if report.metadata.delegates_used is not None:
        lines.extend([f"Research specialists: {', '.join(report.metadata.delegates_used) or 'none'}", ""])
    if report.metadata.tool_actions:
        actions = ", ".join(
            f"{action.provider}:{action.name} ({action.calls})" for action in report.metadata.tool_actions
        )
        lines.extend([f"Tool actions: {actions}", ""])
    if report.metadata.estimated_cost_usd is not None:
        lines.extend([f"Estimated provider cost: ${report.metadata.estimated_cost_usd}", ""])
    for key in SECTION_KEYS:
        section = report.sections[key]
        lines.extend([f"## {_heading(key)}", "", f"Status: **{section.status.value}**", ""])
        for claim_id in section.claim_ids:
            claim = claims[claim_id]
            citations = ", ".join(f"[{source_id}]" for source_id in claim.source_ids) or "no source"
            lines.append(f"- **{claim.classification.value}** — {claim.statement} ({citations})")
        for gap in section.gaps:
            lines.append(f"- Gap: {gap}")
        if not section.claim_ids and not section.gaps:
            lines.append("- No recorded findings.")
        lines.append("")
    lines.extend(["## Sources", ""])
    if sources:
        for source in report.sources:
            label = source.title or str(source.url)
            lines.append(f"- [{source.id}] [{label}]({source.url})")
    else:
        lines.append("- No sources recorded.")
    if report.gaps:
        lines.extend(["", "## Run-level gaps", ""])
        lines.extend(f"- {gap}" for gap in report.gaps)
    return "\n".join(lines).rstrip() + "\n"
