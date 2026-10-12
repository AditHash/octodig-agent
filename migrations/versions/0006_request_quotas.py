"""Durable, atomic request limits shared by API processes."""

from alembic import op
import sqlalchemy as sa

revision = "0006_request_quotas"
down_revision = "0005_evidence_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("request_quotas",
                    sa.Column("bucket_key", sa.String(64), primary_key=True),
                    sa.Column("attempts", sa.Integer(), nullable=False),
                    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_request_quotas_expires_at", "request_quotas", ["expires_at"])


def downgrade() -> None:
    op.drop_table("request_quotas")
