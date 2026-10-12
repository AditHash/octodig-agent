"""Add missing workspace/account/run indexes for evidence and report reads."""

from alembic import op

revision = "0005_evidence_indexes"
down_revision = "0004_run_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("research_sources", "research_claims", "reports"):
        for column in ("workspace_id", "account_id", "run_id"):
            op.create_index(f"ix_{table}_{column}", table, [column],
                            unique=table == "reports" and column == "run_id")


def downgrade() -> None:
    for table in ("reports", "research_claims", "research_sources"):
        for column in ("run_id", "account_id", "workspace_id"):
            op.drop_index(f"ix_{table}_{column}", table_name=table)
