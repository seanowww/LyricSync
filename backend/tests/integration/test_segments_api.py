"""
Integration tests for segments API endpoints (GET/PUT /api/segments/{video_id}).

Current behavior:
- Segments are stored in the database (not JSON files on disk).
- Access is protected by X-Owner-Key and per-video ownership.
"""
import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app
from src.models.segment import SegmentRow


@pytest.fixture
def client(test_db):
    """
    FastAPI test client using the in-memory test database.
    
    WHY: `test_db` fixture (conftest.py) overrides get_db for all routes so
    segments are read/written via SQLAlchemy instead of the old filesystem store.
    """
    return TestClient(app)


@pytest.fixture
def sample_segments():
    """Sample segment data for testing"""
    return [
        {"id": 0, "start": 0.0, "end": 2.5, "text": "First segment"},
        {"id": 1, "start": 2.5, "end": 5.0, "text": "Second segment"},
    ]


@pytest.fixture
def video_with_segments(test_db, test_video_and_owner_key, sample_segments):
    """
    Create a video with pre-saved segments in the database.
    
    IMPORTANT: Returns UUID object internally. Convert to str only at API boundary.
    
    Returns:
        (video_id, owner_key) where video_id is UUID object
    """
    video_id, owner_key = test_video_and_owner_key  # UUID object

    for seg in sample_segments:
        row = SegmentRow(
            video_id=video_id,  # Use UUID internally
            id=seg["id"],
            start=seg["start"],
            end=seg["end"],
            text=seg["text"],
        )
        test_db.add(row)
    test_db.commit()

    return video_id, owner_key  # Return UUID object


class TestGetSegments:
    """Test GET /api/segments/{video_id}"""

    def test_get_existing_segments(self, client, video_with_segments, sample_segments):
        """Should return segments for existing video_id owned by requester"""
        video_id, owner_key = video_with_segments
        response = client.get(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == str(video_id)  # API returns string
        assert len(data["segments"]) == 2
        assert data["segments"] == sample_segments

    def test_get_nonexistent_video(self, client):
        """Should return 404 for non-existent but well-formed video_id"""
        missing_id = str(uuid.uuid4())
        response = client.get(
            f"/api/segments/{missing_id}",
            headers={"X-Owner-Key": "does-not-matter"},
        )
        assert response.status_code == 404

    def test_get_invalid_video_id_format(self, client):
        """Should return 400 for invalid UUID format"""
        response = client.get(
            "/api/segments/not-a-uuid",
            headers={"X-Owner-Key": "any"},
        )
        assert response.status_code == 400


class TestPutSegments:
    """Test PUT /api/segments/{video_id}"""

    def test_update_existing_segments(self, client, test_db, test_video_and_owner_key):
        """Should replace segments for existing video_id in the database"""
        video_id, owner_key = test_video_and_owner_key  # UUID object
        new_segments = [
            {"id": 0, "start": 0.0, "end": 3.0, "text": "Updated first"},
            {"id": 1, "start": 3.0, "end": 6.0, "text": "Updated second"},
        ]
        
        response = client.put(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            json={"segments": new_segments},
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["segments"] == new_segments

        # Verify persistence in database (use UUID internally)
        rows = (
            test_db.query(SegmentRow)
            .filter(SegmentRow.video_id == video_id)  # Use UUID internally
            .order_by(SegmentRow.id)
            .all()
        )
        assert len(rows) == 2
        assert [(r.id, r.start, r.end, r.text) for r in rows] == [
            (0, 0.0, 3.0, "Updated first"),
            (1, 3.0, 6.0, "Updated second"),
        ]

    def test_update_nonexistent_video(self, client):
        """Should return 404 when updating non-existent but well-formed video_id"""
        new_segments = [{"id": 0, "start": 0.0, "end": 1.0, "text": "Test"}]
        missing_id = str(uuid.uuid4())
        response = client.put(
            f"/api/segments/{missing_id}",
            json={"segments": new_segments},
            headers={"X-Owner-Key": "any"},
        )
        assert response.status_code == 404

    def test_validate_segments_structure(self, client, video_with_segments):
        """Should reject invalid segment structures"""
        video_id, owner_key = video_with_segments
        invalid_segments = [
            {"start": 0.0},  # Missing 'end' and 'text'
        ]
        response = client.put(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            json={"segments": invalid_segments},
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 422

    def test_validate_segments_timing(self, client, video_with_segments):
        """Should reject segments with invalid timing (start >= end)"""
        video_id, owner_key = video_with_segments
        invalid_segments = [
            {"id": 0, "start": 5.0, "end": 2.0, "text": "Invalid timing"},
        ]
        response = client.put(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            json={"segments": invalid_segments},
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 422


class TestSegmentsRoundTrip:
    """Test complete round-trip: save -> get -> update -> get"""

    def test_round_trip(self, client, test_db, test_video_and_owner_key):
        """Full round-trip test of segments persistence via API + database"""
        video_id, owner_key = test_video_and_owner_key  # UUID object
        initial_segments = [
            {"id": 0, "start": 0.0, "end": 1.5, "text": "Initial text"},
        ]
        
        # PUT (create)
        response = client.put(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            json={"segments": initial_segments},
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 200
        assert response.json()["segments"] == initial_segments
        
        # UPDATE
        updated_segments = [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "Updated text"},
        ]
        response = client.put(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            json={"segments": updated_segments},
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 200
        
        # GET again to verify
        response = client.get(
            f"/api/segments/{str(video_id)}",  # Convert UUID → str at API boundary
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 200
        assert response.json()["segments"] == updated_segments

