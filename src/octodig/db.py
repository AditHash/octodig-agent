"""Database session boundaries. Migrations, not application startup, own schema changes."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .settings import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"connect_timeout": settings.database_connect_timeout_seconds} if make_url(settings.database_url).get_backend_name() == "postgresql" else {}
engine = create_engine(settings.database_url, pool_pre_ping=True,
                       pool_timeout=settings.database_pool_timeout_seconds,
                       connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
