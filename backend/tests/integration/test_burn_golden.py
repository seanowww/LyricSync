"""
Golden-image snapshot tests for burned video output.

Current behavior:
- Segments live in the database (not JSON files).
- /api/burn reads segments from DB using video_id + owner_key.
This test mirrors that flow by creating DB rows instead of writing JSON.
"""
import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np
import uuid

from src.main import app
from src.models.segment import SegmentRow


@pytest.fixture
def temp_storage():
    """Create temporary storage directories"""
    temp_dir = tempfile.mkdtemp()
    storage_dir = Path(temp_dir) / "storage"
    for subdir in ["uploads", "tmp", "outputs", "segments"]:
        (storage_dir / subdir).mkdir(parents=True)
    
    # Monkey-patch storage directories
    from src import main as main_module
    
    original_upload = main_module.UPLOAD_DIR
    original_tmp = main_module.TMP_DIR
    original_output = main_module.OUTPUT_DIR
    original_segments = main_module.SEGMENTS_DIR
    original_fonts = main_module.FONTS_DIR
    
    main_module.UPLOAD_DIR = storage_dir / "uploads"
    main_module.TMP_DIR = storage_dir / "tmp"
    main_module.OUTPUT_DIR = storage_dir / "outputs"
    main_module.SEGMENTS_DIR = storage_dir / "segments"
    # Use actual fonts dir for tests
    main_module.FONTS_DIR = Path(__file__).parent.parent.parent / "src" / "assets" / "fonts"
    
    yield temp_dir
    
    # Restore
    main_module.UPLOAD_DIR = original_upload
    main_module.TMP_DIR = original_tmp
    main_module.OUTPUT_DIR = original_output
    main_module.SEGMENTS_DIR = original_segments
    main_module.FONTS_DIR = original_fonts
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_video_path(temp_storage):
    """Generate deterministic test video"""
    video_path = Path(temp_storage) / "test_video.mp4"
    
    # Generate 640x480, 5 seconds, solid color
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=blue:s=640x480:d=5",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(video_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"ffmpeg not available: {result.stderr}")
    
    return video_path


@pytest.fixture
def video_id_with_upload(temp_storage, test_video_path, test_db, test_video_and_owner_key):
    """
    Create video + uploaded video file + DB segments for golden tests.
    
    Returns:
        (video_id_str, owner_key)
    """
    video_id_str, owner_key = test_video_and_owner_key
    video_uuid = uuid.UUID(video_id_str)

    from src.main import UPLOAD_DIR
    upload_path = UPLOAD_DIR / f"{video_id_str}.mp4"
    shutil.copy(test_video_path, upload_path)

    segment_row = SegmentRow(
        video_id=video_uuid,
        id=0,
        start=0.0,
        end=2.5,
        text="Test Subtitle",
    )
    test_db.add(segment_row)
    test_db.commit()

    return video_id_str, owner_key


@pytest.fixture
def client(temp_storage, test_db):
    """
    FastAPI TestClient bound to in-memory test database and temp storage.
    """
    return TestClient(app)


def extract_frame(video_path: Path, timestamp: float, output_path: Path) -> bool:
    """Extract a frame from video at given timestamp"""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-ss", str(timestamp),
        "-vframes", "1",
        "-q:v", "2",  # High quality
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def image_diff_percentage(img1_path: Path, img2_path: Path) -> float:
    """
    Compute pixel difference percentage between two images.
    Returns percentage of pixels that differ (0-100).
    """
    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")
    
    # Resize to same dimensions if needed
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
    
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    
    # Compute absolute difference
    diff = np.abs(arr1.astype(int) - arr2.astype(int))
    
    # Count pixels with any channel difference > threshold (5 for slight compression differences)
    threshold = 5
    different_pixels = np.any(diff > threshold, axis=2)
    diff_percentage = (np.sum(different_pixels) / different_pixels.size) * 100
    
    return diff_percentage


class TestGoldenSnapshots:
    """Golden-image snapshot tests for different style configurations"""

    @pytest.mark.parametrize("style_name,style_config", [
        # Base styles
        ("default", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("large_text", {
            "fontFamily": "Inter",
            "fontSizePx": 48,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("thick_outline", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 6,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        # Bold styles
        ("inter_bold", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": True,
            "italic": False,
        }),
        ("arial_bold", {
            "fontFamily": "Arial",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": True,
            "italic": False,
        }),
        # Italic styles
        ("inter_italic", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": True,
        }),
        ("georgia_italic", {
            "fontFamily": "Georgia",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": True,
        }),
        # Bold + Italic styles
        ("inter_bold_italic", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": True,
            "italic": True,
        }),
        ("helvetica_bold_italic", {
            "fontFamily": "Helvetica",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": True,
            "italic": True,
        }),
        # Different fonts (normal style)
        ("arial", {
            "fontFamily": "Arial",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("georgia", {
            "fontFamily": "Georgia",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("helvetica", {
            "fontFamily": "Helvetica",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("times_new_roman", {
            "fontFamily": "Times New Roman",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        # Different colors
        ("green_color", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#36ce5c",  # Green from user's image
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("red_color", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FF0000",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("blue_color", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#0000FF",
            "strokePx": 3,
            "strokeColor": "#FFFFFF",  # White outline for contrast
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("yellow_color", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFF00",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        # Different positions
        ("top_left", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 100,  # Left side
            "posY": 50,   # Top
            "bold": False,
            "italic": False,
        }),
        ("top_right", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 540,  # Right side (640 - 100)
            "posY": 50,   # Top
            "bold": False,
            "italic": False,
        }),
        ("bottom_left", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 100,   # Left side
            "posY": 430,  # Bottom (480 - 50)
            "bold": False,
            "italic": False,
        }),
        ("center", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#36ce5c",  # Green color
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,  # Center X
            "posY": 240,  # Center Y
            "bold": False,
            "italic": False,
        }),
        # Color + position combinations
        ("green_top_center", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#36ce5c",
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 100,
            "bold": False,
            "italic": False,
        }),
        # Opacity tests
        ("opacity_50", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "opacity": 50,
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("opacity_80", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "opacity": 80,
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        # Rotation tests
        ("rotation_45", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "rotation": 45,
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("rotation_90", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "rotation": 90,
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        ("rotation_180", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "rotation": 180,
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
        # Combined opacity and rotation
        ("opacity_rotation", {
            "fontFamily": "Inter",
            "fontSizePx": 28,
            "color": "#FFFFFF",
            "opacity": 70,
            "rotation": 45,
            "strokePx": 3,
            "strokeColor": "#000000",
            "posX": 320,
            "posY": 400,
            "bold": False,
            "italic": False,
        }),
    ])
    def test_style_golden_snapshot(
        self, client, video_id_with_upload, temp_storage, style_name, style_config
    ):
        """Compare burned video frame to golden snapshot"""
        # Burn video
        video_id, owner_key = video_id_with_upload
        payload = {
            "video_id": video_id,
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "Test Subtitle"},
            ],
            "style": style_config,
        }
        
        # NOTE: /api/burn ignores 'segments' field and loads segments from DB.
        # We still include it for backward compatibility, but DB is source of truth.
        response = client.post(
            "/api/burn",
            json=payload,
            headers={"X-Owner-Key": owner_key},
        )
        assert response.status_code == 200
        
        # Save burned video
        from src.main import OUTPUT_DIR
        burned_path = OUTPUT_DIR / f"{video_id}_burned.mp4"
        burned_path.write_bytes(response.content)
        
        # Extract frame at 1.0s
        actual_frame = Path(temp_storage) / f"actual_{style_name}.png"
        assert extract_frame(burned_path, 1.0, actual_frame), "Failed to extract frame"
        
        # Compare to golden (if exists)
        golden_dir = Path(__file__).parent.parent / "assets" / "golden"
        golden_path = golden_dir / f"{style_name}.png"
        
        if not golden_path.exists():
            # First run: save as golden
            golden_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(actual_frame, golden_path)
            pytest.skip(f"Golden image created at {golden_path}. Re-run test to verify.")
        
        # Compare
        diff_pct = image_diff_percentage(actual_frame, golden_path)
        threshold = 1.0  # Allow 1% difference for compression/rendering variations
        
        assert diff_pct < threshold, (
            f"Image difference {diff_pct:.2f}% exceeds threshold {threshold}%. "
            f"Actual: {actual_frame}, Golden: {golden_path}"
        )

