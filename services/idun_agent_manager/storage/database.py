from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_engine = None
SessionLocal: sessionmaker | None = None


class Base(DeclarativeBase):
    pass


def init_engine_and_session(database_url: str) -> None:
    global _engine, SessionLocal
    _engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_session() -> Generator:
    if SessionLocal is None:
        raise RuntimeError("Database session not initialized. Call init_engine_and_session() first.")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_engine():
    if _engine is None:
        raise RuntimeError("Database engine not initialized.")
    return _engine


def create_all_tables() -> None:
    from services.idun_agent_manager.storage.models import Base as ModelsBase

    engine = get_engine()
    ModelsBase.metadata.create_all(bind=engine)
