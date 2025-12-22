"""
Integration tests for segments API endpoints (GET/PUT /api/segments/{video_id}).
Uses FastAPI TestClient and temp directories for deterministic testing.
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
import sys

# Imports work via conftest.py which adds backend/ to path
from src.main import app
from src.services.segments_store import save_segments, load_segments


@pytest.fixture
def temp_storage():
    """Create temporary storage directories for test isolation"""
    temp_dir = tempfile.mkdtemp()
    storage_dir = Path(temp_dir) / "storage"
    segments_dir = storage_dir / "segments"
    segments_dir.mkdir(parents=True)
    
    # Monkey-patch the segments_store to use temp directory
    from src.services import segments_store as store_module
    original_dir = store_module.SEGMENTS_DIR
    store_module.SEGMENTS_DIR = segments_dir
    
    yield temp_dir
    
    # Restore and cleanup
    store_module.SEGMENTS_DIR = original_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def client(temp_storage):
    """FastAPI test client with temp storage"""
    return TestClient(app)


@pytest.fixture
def sample_segments():
    """Sample segment data for testing"""
    return [
        {"id": 0, "start": 0.0, "end": 2.5, "text": "First segment"},
        {"id": 1, "start": 2.5, "end": 5.0, "text": "Second segment"},
    ]


@pytest.fixture
def video_id_with_segments(temp_storage, sample_segments):
    """Create a video_id with pre-saved segments"""
    video_id = "test-video-123"
    save_segments(video_id, sample_segments, source="test")
    return video_id


class TestGetSegments:
    """Test GET /api/segments/{video_id}"""

    def test_get_existing_segments(self, client, video_id_with_segments, sample_segments):
        """Should return segments for existing video_id"""
        response = client.get(f"/api/segments/{video_id_with_segments}")
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id_with_segments
        assert len(data["segments"]) == 2
        assert data["segments"] == sample_segments

    def test_get_nonexistent_segments(self, client):
        """Should return 404 for non-existent video_id"""
        response = client.get("/api/segments/nonexistent-id")
        assert response.status_code == 404


class TestPutSegments:
    """Test PUT /api/segments/{video_id}"""

    def test_update_existing_segments(self, client, video_id_with_segments):
        """Should update segments for existing video_id"""
        new_segments = [
            {"id": 0, "start": 0.0, "end": 3.0, "text": "Updated first"},
            {"id": 1, "start": 3.0, "end": 6.0, "text": "Updated second"},
        ]
        
        response = client.put(
            f"/api/segments/{video_id_with_segments}",
            json={"segments": new_segments}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["segments"] == new_segments
        
        # Verify persistence
        loaded = load_segments(video_id_with_segments)
        assert loaded["segments"] == new_segments

    def test_update_nonexistent_segments(self, client):
        """Should return 404 when updating non-existent video_id"""
        new_segments = [{"id": 0, "start": 0.0, "end": 1.0, "text": "Test"}]
        response = client.put(
            "/api/segments/nonexistent-id",
            json={"segments": new_segments}
        )
        assert response.status_code == 404

    def test_validate_segments_structure(self, client, video_id_with_segments):
        """Should reject invalid segment structures"""
        invalid_segments = [
            {"start": 0.0},  # Missing 'end' and 'text'
        ]
        response = client.put(
            f"/api/segments/{video_id_with_segments}",
            json={"segments": invalid_segments}
        )
        assert response.status_code == 422

    def test_validate_segments_timing(self, client, video_id_with_segments):
        """Should reject segments with invalid timing (start >= end)"""
        invalid_segments = [
            {"id": 0, "start": 5.0, "end": 2.0, "text": "Invalid timing"},
        ]
        response = client.put(
            f"/api/segments/{video_id_with_segments}",
            json={"segments": invalid_segments}
        )
        assert response.status_code == 422


class TestSegmentsRoundTrip:
    """Test complete round-trip: save -> get -> update -> get"""

    def test_round_trip(self, client, temp_storage):
        """Full round-trip test of segments persistence"""
        video_id = "round-trip-test"
        initial_segments = [
            {"id": 0, "start": 0.0, "end": 1.5, "text": "Initial text"},
        ]
        
        # Save via PUT (requires existing video_id, so we create it first)
        save_segments(video_id, initial_segments, source="test")
        
        # GET
        response = client.get(f"/api/segments/{video_id}")
        assert response.status_code == 200
        assert response.json()["segments"] == initial_segments
        
        # UPDATE
        updated_segments = [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "Updated text"},
        ]
        response = client.put(
            f"/api/segments/{video_id}",
            json={"segments": updated_segments}
        )
        assert response.status_code == 200
        
        # GET again to verify
        response = client.get(f"/api/segments/{video_id}")
        assert response.status_code == 200
        assert response.json()["segments"] == updated_segments

