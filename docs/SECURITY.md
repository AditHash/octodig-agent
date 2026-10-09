# OctoDig Security and Trust Model

**Status:** required controls for implementation, not a claim that security mechanisms already exist.

OctoDig ingests untrusted public documents and may use paid model/search APIs. A fully agentic workflow must not have unrestricted network, filesystem, data, or billing permissions.

## Threats

- Prompt injection through fetched pages, PDFs, snippets, or tool outputs
- Server-side request forgery (SSRF), DNS rebinding, redirect-based bypasses
- Excessive API/search spending via runaway planning loops
- Cross-tenant access to reports, seller offerings or research traces
- Unsupported sales claims presented as facts
- Secrets leakage in logs, checkpoints, uploaded artifacts or generated output
- Abuse of professional profiles and unauthorized personal data collection

## Minimum protections

**Network tools**
- Allow only justified public HTTP(S) URLs and vetted providers.
- Validate hostname, resolved IPs, and each redirect destination; reject loopback, private, link-local, metadata, and otherwise non-public ranges.
- Enforce byte limits, fetch timeout, redirect limit, content-type handling, concurrency ceilings, and target-domain budgets.
- Revalidate resolved destinations on connection to mitigate DNS rebinding; do not rely solely on string checks.

**Models and agent tools**
- Separate instructions from retrieved web content. Web documents are **data**, not developer/system directives.
- Explicitly allowlist tools per agent; never expose blanket shell/network or direct database credentials to model-controlled code.
- Disable or gate external side effects. No automatic prospect messages, production data deletion or CRM updates.
- Bound run duration, model calls, search actions, token budget, concurrency, and follow-up loops.
- Treat model-generated URLs, snippets, extracted facts, and "verification" labels as untrusted until checked.

**Evidence and privacy**
- Cite primary sources where possible and preserve canonical URLs with time of access.
- Keep "verified", "inferred", and "hypothesis" separate.
- Use only appropriate public professional information for leadership profiles; don't collect private phone numbers, personal email addresses, or sensitive characteristics.
- Honor applicable legal, site, and provider terms for retrieval, rate limits, and retention.
- Do not infer secret technology choices or internal business needs as confirmed facts.

**Applications and storage**
- Validate FastAPI inputs with Pydantic and enforce authorization server-side on every run and stored object.
- Store secrets in environment/managed secret stores; never push .env or credentials into Git.
- Avoid logging authorization headers, API keys, confidential prompts, encrypted reasoning, or raw customer documents.
- Restrict artifact access, redact sensitive fields, define retention and deletion policies.
- Adopt dependency review, tests and vulnerability checks before deployment.

## Testing

Include targeted tests for private-IP and redirect rejections, injected "ignore prior instructions" content, conflicting evidence, runaway tool loops, cross-tenant report access, and leakage of secrets in SSE and logs.

## Reporting a vulnerability

Before publishing a detailed exploit, notify repository maintainers privately using an appropriate GitHub security advisory/reporting channel if available. Do not open a public issue containing credentials, private customer data, or exploitable secrets.
