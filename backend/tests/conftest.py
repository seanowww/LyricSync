"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
import uuid
import secrets
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to Python path so 'src' can be imported as a package
# This matches how the app runs normally (from backend/ directory)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.db.session import Base, get_db
from src.models.video import Video
from src.models.segment import SegmentRow

# Global variable to hold the current test database session factory
# This allows per-test databases while patching get_db at module level
_current_test_session_factory = None
_original_get_db = None


def pytest_configure(config):
    """
    Pytest hook called before test collection.
    Patches get_db BEFORE any routes are imported.
    """
    # Patch get_db to use a factory that returns the current test session
    from src.db import session as session_module
    
    def test_get_db():
        """Test version of get_db that uses the current test database."""
        global _current_test_session_factory, _original_get_db
        
        if _current_test_session_factory is None:
            # Fallback to original if no test database is set up
            # This shouldn't happen in normal test flow, but provides safety
            if _original_get_db is None:
                raise RuntimeError("Test database not initialized")
            for db in _original_get_db():
                yield db
            return
        
        db = _current_test_session_factory()
        try:
            yield db
        finally:
            db.close()
    
    # Store original BEFORE patching (important!)
    global _original_get_db
    _original_get_db = session_module.get_db
    session_module.get_db = test_get_db


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database in memory for each test.
    WHY: Isolated database per test, no cleanup needed (in-memory SQLite).
    """
    global _current_test_session_factory
    
    # Use in-memory SQLite for tests (fast, isolated)
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Set the global session factory so get_db (patched in pytest_configure) uses it
    _current_test_session_factory = TestingSessionLocal
    
    # Create a session for fixtures to use
    db_session = TestingSessionLocal()
    
    yield db_session
    
    # Cleanup: close session, clear factory, drop tables
    db_session.close()
    _current_test_session_factory = None
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_video_and_owner_key(test_db):
    """
    Create a test video record and return (video_id, owner_key).
    WHY: Helper fixture for tests that need a video in the database.
    
    IMPORTANT:
    Use a single canonical UUID for DB, storage, and API calls.
    Multiple UUIDs for the same logical video causes 404s during lookup.
    The video_id must be the same UUID object used in:
    - Video.id in the database
    - the filename / storage path
    - the value returned to the test
    """
    # Generate a single UUID that will be used consistently everywhere
    video_id = uuid.uuid4()
    owner_key = secrets.token_urlsafe(32)
    
    # Use the SAME video_id for the database record
    video = Video(
        id=video_id,  # Explicitly set to avoid default uuid.uuid4() being called
        owner_key=owner_key,
        original_uri=f"{video_id}.mp4",  # Use SAME video_id for filename
    )
    test_db.add(video)
    test_db.commit()
    
    # Return the SAME video_id for use in API calls
    return video_id, owner_key

