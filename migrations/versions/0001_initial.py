"""Initial hosted application schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-10
"""

from alembic import op

from octodig.db import Base
from octodig import models  # noqa: F401 - register all tables

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    table_names = (
        "users",
        "workspaces",
        "memberships",
        "target_accounts",
        "research_runs",
        "research_events",
    )
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in table_names])


def downgrade() -> None:
    table_names = (
        "research_events",
        "research_runs",
        "target_accounts",
        "memberships",
        "workspaces",
        "users",
    )
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in table_names])
