"""
Shared Database Session — Layer 2 Analytical Engine
----------------------------------------------------
Reuses the same `ecogen.db` SQLite file that Layer 1 writes to.
This avoids duplicating database state and allows Layer 2 to read
live ingestion data immediately after Layer 1 writes it.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Resolve DB path relative to the project root (two levels up from this file)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_DB_PATH = os.path.join(_BASE_DIR, "ecogen.db")
_DB_URL = f"sqlite:///{_DB_PATH}"

# Layer 2 uses check_same_thread=False to support FastAPI's async workers
_engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine():
    """Return the SQLAlchemy engine (useful for raw SQL or testing)."""
    return _engine


def get_database() -> Session:
    """
    FastAPI dependency that yields a SQLAlchemy Session.
    Always closes the session after the request completes.
    """
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
