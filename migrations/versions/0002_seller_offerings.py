"""Add workspace-scoped seller offerings.

Revision ID: 0002_seller_offerings
Revises: 0001_initial
Create Date: 2026-10-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_seller_offerings"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seller_offerings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("business_outcomes", sa.JSON(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_offering_slug_workspace"),
    )
    op.create_index("ix_seller_offerings_workspace_id", "seller_offerings", ["workspace_id"])
    op.create_index("ix_seller_offerings_approved", "seller_offerings", ["approved"])


def downgrade() -> None:
    op.drop_table("seller_offerings")
