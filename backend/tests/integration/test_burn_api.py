"""
Integration tests for POST /api/burn endpoint.
Tests video burning with ASS subtitles and verifies MP4 output.
"""
import pytest
import tempfile
import shutil
import subprocess
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys

# Imports work via conftest.py
from src.main import app
from src.models.video import Video
from src.models.segment import SegmentRow


@pytest.fixture
def temp_storage():
    """Create temporary storage directories"""
    temp_dir = tempfile.mkdtemp()
    storage_dir = Path(temp_dir) / "storage"
    for subdir in ["uploads", "tmp", "outputs", "segments"]:
        (storage_dir / subdir).mkdir(parents=True)
    
    # Monkey-patch storage directories in storage module
    from src.services import storage as storage_module
    from src.services import segments_store as store_module
    
    original_upload = storage_module.UPLOAD_DIR
    original_tmp = storage_module.TMP_DIR
    original_output = storage_module.OUTPUT_DIR
    original_segments = store_module.SEGMENTS_DIR
    
    # Patch the module variables
    storage_module.UPLOAD_DIR = storage_dir / "uploads"
    storage_module.TMP_DIR = storage_dir / "tmp"
    storage_module.OUTPUT_DIR = storage_dir / "outputs"
    store_module.SEGMENTS_DIR = storage_dir / "segments"
    
    # Also patch in burn_service which has its own TMP_DIR and OUTPUT_DIR
    from src.services import burn_service
    original_burn_tmp = burn_service.TMP_DIR
    original_burn_output = burn_service.OUTPUT_DIR
    burn_service.TMP_DIR = storage_dir / "tmp"
    burn_service.OUTPUT_DIR = storage_dir / "outputs"
    
    yield temp_dir
    
    # Restore
    storage_module.UPLOAD_DIR = original_upload
    storage_module.TMP_DIR = original_tmp
    storage_module.OUTPUT_DIR = original_output
    store_module.SEGMENTS_DIR = original_segments
    burn_service.TMP_DIR = original_burn_tmp
    burn_service.OUTPUT_DIR = original_burn_output
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_video_path(temp_storage):
    """Generate a simple test video using ffmpeg (5 seconds, solid color)"""
    video_path = Path(temp_storage) / "test_video.mp4"
    
    # Generate a simple test video: 5 seconds, 640x480, solid red
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=red:s=640x480:d=5",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(video_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"ffmpeg not available or failed: {result.stderr}")
    
    return video_path


@pytest.fixture
def video_id_with_upload(temp_storage, test_video_path, test_db, test_video_and_owner_key):
    """
    Create a video_id with uploaded video file and database records.
    
    IMPORTANT: Returns UUID object internally. Convert to str only at API boundary.
    """
    video_id, owner_key = test_video_and_owner_key
    
    # Verify video exists in database (from test_video_and_owner_key)
    # Video is already imported at module level (line 17)
    video = test_db.query(Video).filter(Video.id == video_id).first()
    assert video is not None, f"Video {video_id} not found in database"
    assert video.owner_key == owner_key, f"Video owner_key mismatch: expected {owner_key}, got {video.owner_key}"
    
    # Copy test video to uploads directory
    # Import after temp_storage has patched it
    from src.services import storage as storage_module
    from src.services.storage import find_uploaded_video
    # Convert UUID to str for file path (storage uses string paths)
    upload_path = storage_module.UPLOAD_DIR / f"{video_id}.mp4"
    shutil.copy(test_video_path, upload_path)
    
    # Verify file was created
    assert upload_path.exists(), f"Video file not created at {upload_path}"
    
    # Verify find_uploaded_video can find it (confirms patching worked)
    # find_uploaded_video expects string, so convert UUID → str at boundary
    found_path = find_uploaded_video(str(video_id))
    assert found_path == upload_path, f"find_uploaded_video found {found_path} but expected {upload_path}"
    
    # Create segments in database (use UUID internally)
    segments = [
        {"id": 0, "start": 0.0, "end": 2.5, "text": "First subtitle"},
        {"id": 1, "start": 2.5, "end": 5.0, "text": "Second subtitle"},
    ]
    
    for seg in segments:
        segment_row = SegmentRow(
            video_id=video_id,  # Use UUID internally
            id=seg["id"],
            start=seg["start"],
            end=seg["end"],
            text=seg["text"]
        )
        test_db.add(segment_row)
    test_db.commit()
    
    # Verify segments were created
    segment_count = test_db.query(SegmentRow).filter(SegmentRow.video_id == video_id).count()
    assert segment_count == len(segments), f"Expected {len(segments)} segments, found {segment_count}"
    
    # Return UUID object (not string) - convert to str only at API boundary
    return video_id, owner_key


@pytest.fixture
def client(temp_storage, test_db):
    """
    FastAPI test client.
    
    WHY: Depends on test_db to ensure the database override is set up
    before the client is created. This ensures get_db uses the test database.
    """
    return TestClient(app)


class TestBurnVideo:
    """Test POST /api/burn"""

    def test_burn_returns_mp4(self, client, video_id_with_upload):
        """Should return an MP4 file with correct content-type"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Test subtitle"},
            ],
            "style": {
                "fontFamily": "Inter",
                "fontSizePx": 28,
                "color": "#FFFFFF",
                "strokePx": 3,
                "strokeColor": "#000000",
                "posX": 320,
                "posY": 400,
                "bold": False,
                "italic": False,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        
        assert response.status_code == 200
        # Backend returns "video/*" as content-type (see main.py line ~399)
        assert response.headers["content-type"] == "video/*"
        
        # Verify it's actually an MP4 (check file signature)
        content = response.content
        assert len(content) > 1000  # Non-trivial size
        # MP4 files start with ftyp box (bytes 4-8 contain "ftyp")
        assert b"ftyp" in content[:20]  # MP4 signature

    def test_burn_with_default_style(self, client, video_id_with_upload):
        """Should work with minimal style (defaults applied)"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Default style"},
            ],
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        
        assert response.status_code == 200
        # Backend returns "video/*" as content-type
        assert response.headers["content-type"] == "video/*"

    def test_burn_with_bold_style(self, client, video_id_with_upload):
        """Should work with bold font style"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Bold text"},
            ],
            "style": {
                "fontFamily": "Arial",
                "bold": True,
                "italic": False,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000

    def test_burn_with_italic_style(self, client, video_id_with_upload):
        """Should work with italic font style"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Italic text"},
            ],
            "style": {
                "fontFamily": "Georgia",
                "bold": False,
                "italic": True,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000

    def test_burn_with_bold_italic_style(self, client, video_id_with_upload):
        """Should work with bold+italic font style"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Bold Italic text"},
            ],
            "style": {
                "fontFamily": "Helvetica",
                "bold": True,
                "italic": True,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000

    def test_burn_with_different_fonts(self, client, video_id_with_upload):
        """Should work with different font families"""
        video_id, owner_key = video_id_with_upload
        fonts = ["Inter", "Arial", "Georgia", "Helvetica", "Times New Roman"]
        
        for font in fonts:
            payload = {
                "video_id": str(video_id),  # Convert UUID → str at API boundary
                "segments": [
                    {"id": 0, "start": 0.0, "end": 2.5, "text": f"Text in {font}"},
                ],
                "style": {
                    "fontFamily": font,
                    "bold": False,
                    "italic": False,
                },
            }
            
            response = client.post(
                "/api/burn",
                json=payload,
                headers={"X-Owner-Key": owner_key}
            )
            assert response.status_code == 200, f"Failed for font {font}"
            assert response.headers["content-type"] == "video/*"
            assert len(response.content) > 1000

    def test_burn_nonexistent_video(self, client):
        """Should return 404 for non-existent video_id"""
        # Use a valid UUID format that doesn't exist in the database
        nonexistent_uuid = str(uuid.uuid4())
        payload = {
            "video_id": nonexistent_uuid,
            "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "Test"}],
        }
        response = client.post("/api/burn", json=payload)
        assert response.status_code == 404

    def test_burn_empty_segments(self, client, video_id_with_upload):
        """Should return 400 for empty segments"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [],
        }
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 400

    def test_burn_large_video_size(self, client, temp_storage, test_db, test_video_and_owner_key):
        """Should handle large video sizes (1920x1080)"""
        video_id, owner_key = test_video_and_owner_key  # UUID object
        
        # Generate large test video (1920x1080, 5 seconds)
        # Import after temp_storage has patched it
        from src.services import storage as storage_module
        # Convert UUID → str for file path (storage uses string paths)
        large_video_path = storage_module.UPLOAD_DIR / f"{video_id}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=blue:s=1920x1080:d=5",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(large_video_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            pytest.skip(f"ffmpeg not available or failed: {result.stderr}")
        
        # Create segments (use UUID internally)
        segment_row = SegmentRow(
            video_id=video_id,  # Use UUID internally
            id=0,
            start=0.0,
            end=2.5,
            text="Large video test"
        )
        test_db.add(segment_row)
        test_db.commit()
        
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Large video test"},
            ],
            "style": {
                "fontSizePx": 48,  # Large font for large video
                "posX": 960,  # Center of 1920px width
                "posY": 950,  # Near bottom of 1080px height
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000
        
        # Verify output resolution is preserved (check with ffprobe if available)
        # This is a basic test - full verification would require extracting frame

    def test_burn_with_opacity(self, client, video_id_with_upload):
        """Should work with text opacity"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Semi-transparent text"},
            ],
            "style": {
                "fontFamily": "Inter",
                "color": "#FFFFFF",
                "opacity": 70,  # 70% opacity
                "bold": False,
                "italic": False,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000

    def test_burn_with_rotation(self, client, video_id_with_upload):
        """Should work with text rotation"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Rotated text"},
            ],
            "style": {
                "fontFamily": "Inter",
                "color": "#FFFFFF",
                "rotation": 45,  # 45 degrees rotation
                "bold": False,
                "italic": False,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000

    def test_burn_with_opacity_and_rotation(self, client, video_id_with_upload):
        """Should work with both opacity and rotation"""
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": str(video_id),  # Convert UUID → str at API boundary
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Rotated transparent text"},
            ],
            "style": {
                "fontFamily": "Inter",
                "color": "#FFFFFF",
                "opacity": 80,
                "rotation": 90,  # 90 degrees rotation
                "bold": False,
                "italic": False,
            },
        }
        
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/*"
        assert len(response.content) > 1000

