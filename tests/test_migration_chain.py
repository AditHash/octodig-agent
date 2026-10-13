import subprocess


def test_fresh_postgresql_migration_chain_adds_idempotency_once():
    result = subprocess.run(
        ["alembic", "upgrade", "head", "--sql"],
        check=True, capture_output=True, text=True,
    )
    initial_run_table = result.stdout.split("CREATE TABLE research_runs (")[1].split(");")[0]
    assert "idempotency_key" not in initial_run_table
    assert result.stdout.count("ADD COLUMN idempotency_key") == 1
