"""Add per-account report versions and generation timestamps."""

from alembic import op
import sqlalchemy as sa


revision = "0007_report_history"
down_revision = "0006_request_quotas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("report_version", sa.Integer(), nullable=True))
    op.add_column("reports", sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("""
        UPDATE reports AS report
        SET report_version = ranked.report_version, generated_at = report.created_at
        FROM (
            SELECT id, row_number() OVER (PARTITION BY account_id ORDER BY created_at, id) AS report_version
            FROM reports
        ) AS ranked
        WHERE report.id = ranked.id
    """)
    op.alter_column("reports", "report_version", nullable=False)
    op.alter_column("reports", "generated_at", nullable=False)
    op.create_unique_constraint("uq_report_account_version", "reports", ["account_id", "report_version"])


def downgrade() -> None:
    op.drop_constraint("uq_report_account_version", "reports", type_="unique")
    op.drop_column("reports", "generated_at")
    op.drop_column("reports", "report_version")
