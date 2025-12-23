# routes/video.py
"""
GET /api/video/{video_id} endpoint.

WHY: Separated from main.py for organization.
Serves video files from storage.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
from src.db.session import get_db
from src.services.auth import require_owner_key, get_video_or_404
from src.services.storage import find_uploaded_video

router = APIRouter()


@router.get("/api/video/{video_id}")
async def get_video(
    video_id: str,
    owner_key: str = Depends(require_owner_key),
    db: Session = Depends(get_db)
):
    """
    Get video file.
    
    WHY: Requires owner_key for access control.
    Finds the file by video_id (regardless of extension).
    """
    try:
        video_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video_id format")

    # Verify ownership
    video = get_video_or_404(db, video_uuid, owner_key)

    # Find the uploaded file (regardless of extension)
    try:
        video_path = find_uploaded_video(video_id)
    except HTTPException:
        raise

    # Stream the file back to the client
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",  # MVP: assume MP4
        filename=video_path.name
    )

