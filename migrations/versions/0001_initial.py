"""Frozen PostgreSQL schema for the initial hosted application revision."""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

INITIAL_SCHEMA = """
CREATE TYPE workspacerole AS ENUM ('OWNER', 'ADMIN', 'SALES_MANAGER', 'SALES_REP', 'VIEWER');

CREATE TYPE runstatus AS ENUM ('QUEUED', 'RESEARCHING', 'NORMALIZING', 'MATCHING', 'RENDERING', 'COMPLETED', 'COMPLETED_PARTIAL', 'FAILED', 'CANCEL_REQUESTED', 'CANCELLED', 'BUDGET_EXCEEDED');

CREATE TABLE users (
    id VARCHAR(36) NOT NULL,
    email VARCHAR(320) NOT NULL,
    name VARCHAR(160) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE workspaces (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(160) NOT NULL,
    slug VARCHAR(80) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_workspaces_slug ON workspaces (slug);

CREATE TABLE memberships (
    id VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role workspacerole NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_membership_workspace_user UNIQUE (workspace_id, user_id),
    FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_memberships_workspace_id ON memberships (workspace_id);

CREATE INDEX ix_memberships_user_id ON memberships (user_id);

CREATE TABLE target_accounts (
    id VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    normalized_domain VARCHAR(255),
    website VARCHAR(2048),
    owner_user_id VARCHAR(36),
    notes TEXT NOT NULL,
    tags JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_target_domain_workspace UNIQUE (workspace_id, normalized_domain),
    FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
    FOREIGN KEY(owner_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_target_accounts_workspace_id ON target_accounts (workspace_id);

CREATE TABLE research_runs (
    id VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    requested_by_id VARCHAR(36) NOT NULL,
    status runstatus NOT NULL,
    provider VARCHAR(32) NOT NULL,
    mode VARCHAR(16) NOT NULL,
    max_cost_usd VARCHAR(24) NOT NULL,
    input_snapshot JSON NOT NULL,
    attempts INTEGER NOT NULL,
    lease_expires_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    error_code VARCHAR(80),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
    FOREIGN KEY(account_id) REFERENCES target_accounts (id) ON DELETE CASCADE,
    FOREIGN KEY(requested_by_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_research_runs_workspace_id ON research_runs (workspace_id);

CREATE INDEX ix_research_runs_status ON research_runs (status);

CREATE INDEX ix_research_runs_account_id ON research_runs (account_id);

CREATE TABLE research_events (
    id VARCHAR(36) NOT NULL,
    run_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(run_id) REFERENCES research_runs (id) ON DELETE CASCADE
);

CREATE INDEX ix_research_events_run_id ON research_events (run_id);
"""


def upgrade() -> None:
    # Static migration-owned SQL stays independent of runtime models.
    for statement in INITIAL_SCHEMA.split(";"):
        if statement.strip():
            op.execute(statement.strip())


def downgrade() -> None:
    for name in ("research_events", "research_runs", "target_accounts", "memberships", "workspaces", "users"):
        op.drop_table(name)
    op.execute("DROP TYPE runstatus")
    op.execute("DROP TYPE workspacerole")
