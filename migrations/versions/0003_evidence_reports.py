"""Persist normalized research evidence and report envelopes.

Revision ID: 0003_evidence_reports
Revises: 0002_seller_offerings
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_evidence_reports"
down_revision = "0002_seller_offerings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("research_sources", sa.Column("id", sa.String(80), primary_key=True), sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("account_id", sa.String(36), sa.ForeignKey("target_accounts.id", ondelete="CASCADE"), nullable=False), sa.Column("run_id", sa.String(36), sa.ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("canonical_url", sa.String(2048), nullable=False), sa.Column("title", sa.String(500)), sa.Column("publisher", sa.String(300)), sa.Column("published_at", sa.DateTime(timezone=True)), sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False), sa.Column("provider", sa.String(64), nullable=False), sa.Column("locator", sa.Text()), sa.UniqueConstraint("run_id", "canonical_url", name="uq_source_run_url"))
    op.create_table("research_claims", sa.Column("id", sa.String(80), primary_key=True), sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("account_id", sa.String(36), sa.ForeignKey("target_accounts.id", ondelete="CASCADE"), nullable=False), sa.Column("run_id", sa.String(36), sa.ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("section", sa.String(80), nullable=False), sa.Column("statement", sa.Text(), nullable=False), sa.Column("classification", sa.String(32), nullable=False), sa.Column("verification_status", sa.String(32), nullable=False), sa.Column("rationale", sa.Text()))
    op.create_table("claim_evidence", sa.Column("claim_id", sa.String(80), sa.ForeignKey("research_claims.id", ondelete="CASCADE"), primary_key=True), sa.Column("source_id", sa.String(80), sa.ForeignKey("research_sources.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("reports", sa.Column("id", sa.String(36), primary_key=True), sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("account_id", sa.String(36), sa.ForeignKey("target_accounts.id", ondelete="CASCADE"), nullable=False), sa.Column("run_id", sa.String(36), sa.ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("schema_version", sa.String(20), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("markdown", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("claim_evidence")
    op.drop_table("research_claims")
    op.drop_table("research_sources")
