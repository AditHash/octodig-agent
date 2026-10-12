"""Add workspace-scoped research run idempotency keys.

Revision ID: 0004_run_idempotency
Revises: 0003_evidence_reports
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_run_idempotency"
down_revision = "0003_evidence_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("research_runs", sa.Column("idempotency_key", sa.String(80), nullable=True))
    op.create_unique_constraint("uq_run_workspace_idempotency", "research_runs", ["workspace_id", "idempotency_key"])


def downgrade() -> None:
    op.drop_constraint("uq_run_workspace_idempotency", "research_runs", type_="unique")
    op.drop_column("research_runs", "idempotency_key")
