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


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database in memory for each test.
    WHY: Isolated database per test, no cleanup needed (in-memory SQLite).
    """
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
    
    # Override get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Monkey-patch get_db in route modules
    import src.routes.transcribe as transcribe_module
    import src.routes.segments as segments_module
    import src.routes.video as video_module
    import src.routes.burn as burn_module
    
    transcribe_module.get_db = override_get_db
    segments_module.get_db = override_get_db
    video_module.get_db = override_get_db
    burn_module.get_db = override_get_db
    
    yield TestingSessionLocal()
    
    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_video_and_owner_key(test_db):
    """
    Create a test video record and return (video_id, owner_key).
    WHY: Helper fixture for tests that need a video in the database.
    """
    video_id = uuid.uuid4()
    owner_key = secrets.token_urlsafe(32)
    
    video = Video(
        id=video_id,
        owner_key=owner_key,
        original_uri=f"{video_id}.mp4",
    )
    test_db.add(video)
    test_db.commit()
    
    return str(video_id), owner_key

