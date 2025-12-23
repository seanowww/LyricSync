# services/storage.py
"""
Filesystem storage operations.

WHY: Handles saving/loading video files and burned outputs.
Separated from DB operations to maintain clear boundaries.
"""
from pathlib import Path
from fastapi import HTTPException, UploadFile
from typing import BinaryIO


# Storage directories (relative to src/)
# WHY: Using __file__ to get absolute path ensures it works regardless of working directory
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"
TMP_DIR = STORAGE_DIR / "tmp"

# Ensure directories exist
for d in (UPLOAD_DIR, OUTPUT_DIR, TMP_DIR):
    d.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB for MVP
ALLOWED_EXTS = {".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm"}


def copy_with_limit(src: BinaryIO, dst: BinaryIO, max_bytes: int) -> None:
    """
    Copy file with size limit check.
    
    WHY: Prevents uploading files that are too large.
    Reads in chunks to avoid loading entire file into memory.
    """
    total = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    while True:
        chunk = src.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail="File too large for MVP limit."
            )
        dst.write(chunk)


def save_uploaded_file(
    file: UploadFile,
    video_id: str,
    allowed_exts: set[str] = ALLOWED_EXTS,
    max_bytes: int = MAX_UPLOAD_BYTES
) -> Path:
    """
    Save uploaded file to storage directory.
    
    WHY: Centralized file saving logic with validation.
    Returns the path where the file was saved.
    
    Args:
        file: FastAPI UploadFile
        video_id: UUID string to use as filename base
        allowed_exts: Set of allowed file extensions
        max_bytes: Maximum file size in bytes
    
    Returns:
        Path to saved file
    
    Raises:
        HTTPException: If file type or size is invalid, or save fails
    """
    # Determine extension
    suffix = Path(file.filename or "").suffix.lower() or ".mp4"
    if suffix not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}"
        )

    # Build save path
    saved_path = UPLOAD_DIR / f"{video_id}{suffix}"

    try:
        with open(saved_path, "wb") as out_file:
            copy_with_limit(file.file, out_file, max_bytes)
    except HTTPException:
        # Re-raise size limit errors
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save upload: {e}"
        )
    finally:
        # Ensure file handle is closed
        try:
            file.file.close()
        except Exception:
            pass

    return saved_path


def find_uploaded_video(video_id: str) -> Path:
    """
    Find uploaded video file by video_id (regardless of extension).
    
    WHY: Videos can be uploaded as .mp4, .mov, .webm, etc.
    We search by video_id prefix to find the actual file.
    
    Args:
        video_id: UUID string
    
    Returns:
        Path to video file
    
    Raises:
        HTTPException: If video not found
    """
    matches = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"Video not found for video_id={video_id}"
        )
    return matches[0]  # MVP: assume one match

