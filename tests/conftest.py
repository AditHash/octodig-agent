"""Opt-in PostgreSQL checks create and remove only their own random schema."""

import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def disposable_postgres_url(value: str):
    url = make_url(value)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
        raise ValueError("PostgreSQL integration requires a database name ending in _test")
    return url


@pytest.fixture
def postgres_engine():
    value = os.environ.get("OCTODIG_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set OCTODIG_TEST_DATABASE_URL to a disposable PostgreSQL database")
    url = disposable_postgres_url(value)
    schema = f"octodig_test_{uuid.uuid4().hex}"
    admin = create_engine(url, pool_pre_ping=True)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"}, pool_pre_ping=True)
    try:
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
