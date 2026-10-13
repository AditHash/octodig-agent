# SalesDig operational reference

OctoDig uses the separate SalesDig repository's `v1` and `v2` branches as product
references. V1's Workmates UAT history is user-provided context, not validation of
OctoDig. V2 remains an incomplete reference and does not define release readiness.

V1 source provides workspace-scoped authentication, persisted reports, history,
seller settings, report inspection, chat and PDF export. OctoDig's current milestone
implements authentication, account/run history, seller offerings, evidence reports
and authenticated Markdown/JSON exports. Chat, PDF, member administration and
operational monitoring remain separate milestones.

V2 describes durable account research, approved offerings, explicit uncertainty,
versioned seller knowledge and saved sales preparation. OctoDig carries forward
approval filtering and evidence distinctions. Document ingestion, versioned catalog
editing, account chat and saved preparation are not implemented by this milestone.

OctoDig enforces its own twelve-section report contract and security requirements.
No SalesDig customer data, environment files or credentials are copied. Production
release requires the remaining checks in [VERIFICATION.md](VERIFICATION.md).
