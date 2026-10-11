"""Authoritative database. SQLite is an explicit, isolated test adapter only."""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


class Base(DeclarativeBase):
    pass


def create_database_engine(url: str):
    if not url:
        raise RuntimeError("DATABASE_URL is required; configure a PostgreSQL psycopg URL")
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        if settings.ENVIRONMENT != "test":
            raise RuntimeError("SQLite is allowed only with ENVIRONMENT=test")
        options = {"connect_args": {"check_same_thread": False}}
        if parsed.database in (None, "", ":memory:"):
            options["poolclass"] = StaticPool
        db_engine = create_engine(url, **options)
        @event.listens_for(db_engine, "connect")
        def foreign_keys(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return db_engine
    if parsed.drivername != "postgresql+psycopg":
        raise RuntimeError("DATABASE_URL must use postgresql+psycopg (SQLite only for tests)")
    return create_engine(url, pool_pre_ping=True, connect_args={"options": "-c timezone=UTC"})


engine = create_database_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.rollback()
