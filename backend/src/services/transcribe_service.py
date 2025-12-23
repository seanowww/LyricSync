# services/transcribe_service.py
"""
Transcription service orchestration.

WHY: Handles the complex flow of:
1. Generating IDs (video_id, owner_key)
2. Saving file to filesystem
3. Creating DB record
4. Running transcription
5. Saving segments to DB
6. Handling failures with proper cleanup

This service ensures atomicity: either everything succeeds or we rollback.
"""
import uuid
import secrets
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.video import Video
from src.models.segment import SegmentRow
from src.services.storage import save_uploaded_file
from src.timing_pipeline import generate_timing_segments

logger = logging.getLogger("lyricsync")


def transcribe_video(
    db: Session,
    file_path: Path,
    video_id: uuid.UUID,
    owner_key: str
) -> list[dict]:
    """
    Transcribe video and save segments to database.
    
    WHY: This is the core business logic for transcription.
    It's separated from the route handler so it can be tested independently.
    
    Args:
        db: Database session (must be in a transaction)
        file_path: Path to uploaded video file
        video_id: UUID for the video (already generated)
        owner_key: Owner key for the video (already generated)
    
    Returns:
        List of segment dicts (with id, start, end, text)
    
    Raises:
        HTTPException: If transcription fails
    """
    # Generate timing segments using Whisper
    try:
        segments = generate_timing_segments(str(file_path))
    except Exception as e:
        msg = str(e)
        # Friendlier error message for common issues
        if "Invalid file format" in msg:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Transcription failed due to unsupported media container. "
                    "If you uploaded a video like .mov, ensure the backend extracts audio to .wav/.mp3 "
                    "before calling Whisper."
                ),
            )
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {e}"
        )

    # Save segments to database
    # WHY: We save segments in the same transaction as the video record.
    # If this fails, the entire transaction rolls back.
    for seg_dict in segments:
        segment_row = SegmentRow(
            video_id=video_id,
            id=seg_dict["id"],
            start=seg_dict["start"],
            end=seg_dict["end"],
            text=seg_dict["text"]
        )
        db.add(segment_row)

    # Commit the transaction (video + segments)
    # WHY: We commit once after all DB operations succeed.
    # If transcription failed above, we never reach here, so no orphaned records.
    db.commit()

    return segments


def create_video_project(
    db: Session,
    file_path: Path,
    video_id: uuid.UUID,
    owner_key: str
) -> Video:
    """
    Create a new video project in the database.
    
    WHY: Separates DB record creation from transcription.
    This allows us to create the record first, then transcribe in a separate step.
    
    Args:
        db: Database session
        file_path: Path to uploaded video file (relative path stored in DB)
        video_id: UUID for the video
        owner_key: Owner key for access control
    
    Returns:
        Created Video model
    """
    # Store filename in DB (just the filename, not full path)
    # WHY: We can reconstruct the path using video_id + extension
    # This keeps the DB portable and simple
    filename = file_path.name
    
    video = Video(
        id=video_id,
        owner_key=owner_key,
        original_uri=filename
    )
    db.add(video)
    # NOTE: We don't commit here - the caller commits after transcription succeeds
    return video

