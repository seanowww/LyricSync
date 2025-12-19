from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any

# Base storage directory
BASE_STORAGE_DIR = Path("src/storage")
SEGMENTS_DIR = BASE_STORAGE_DIR / "segments"


def _ensure_segments_dir_exists() -> None:
    """
    Ensure that the segments storage directory exists.
    """
    SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)


def _segments_file_path(video_id: str) -> Path:
    """
    Return the path to the segments JSON file for a given video_id.
    """
    _ensure_segments_dir_exists()
    return SEGMENTS_DIR / f"{video_id}.json"


def save_segments(
    video_id: str,
    segments: List[Dict[str, Any]],
    source: str = "unknown"
) -> None:
    """
    Persist segments for a given video_id to disk (atomic write).

    This function is the canonical way to write segment data.
    """
    path = _segments_file_path(video_id)
    tmp_path = path.with_suffix(".json.tmp")

    payload = {
        "video_id": video_id,
        "source": source,
        "updated_at": datetime.utcnow().isoformat(),
        "segments": segments,
    }

    # Preserve created_at if file already exists
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
            payload["created_at"] = existing.get("created_at")
    else:
        payload["created_at"] = payload["updated_at"]

    # Write atomically
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    tmp_path.replace(path)


def load_segments(video_id: str) -> Dict[str, Any]:
    """
    Load and return the full segment payload for a given video_id.

    Raises FileNotFoundError if segments do not exist.
    """
    path = _segments_file_path(video_id)

    if not path.exists():
        raise FileNotFoundError(f"Segments not found for video_id={video_id}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
