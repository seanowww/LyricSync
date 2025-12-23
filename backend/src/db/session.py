# db/session.py
"""
Database session management.

WHY: Centralizes SQLAlchemy engine and session creation.
This follows FastAPI best practices for dependency injection.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Read DATABASE_URL from environment (defaults to local PostgreSQL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://lyricsync:lyricsync@localhost:5432/lyricsync",
)

# Create engine with connection pooling
# pool_pre_ping: Tests connections before using them (helps avoid stale connections)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Session factory: creates new sessions bound to the engine
# autoflush=False: Don't automatically flush changes (we'll commit explicitly)
# autocommit=False: Use transactions (commit/rollback)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models should inherit from this.
    """
    pass


def get_db():
    """
    Dependency function for FastAPI routes.
    
    WHY: This is a generator function that FastAPI will call to get a DB session.
    FastAPI handles the cleanup (closing the session) after the request completes.
    
    Usage in routes:
        @app.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

