# routes/burn.py
"""
POST /api/burn endpoint.

WHY: Separated from main.py for organization.
Handles video burning with subtitles.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.services.auth import require_owner_key, get_video_or_404
from src.services.storage import find_uploaded_video
from src.services.burn_service import burn_video_with_subtitles
from src.services.mappers import segments_rows_to_schemas
from src.models.segment import SegmentRow
from src.schemas.requests import BurnRequest

router = APIRouter()


@router.post("/api/burn")
async def burn_video(
    payload: BurnRequest,
    owner_key: str = Depends(require_owner_key),
    db: Session = Depends(get_db)
):
    """
    Burn subtitles into video.
    
    WHY: Requires owner_key for access control.
    Loads segments from database (not request payload) to ensure consistency.
    """
    try:
        video_uuid = uuid.UUID(payload.video_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video_id format")

    # Validate segments are not empty
    if len(payload.segments) == 0:
        raise HTTPException(
            status_code=400,
            detail="No segments provided"
        )

    # Verify ownership and video exists
    video = get_video_or_404(db, video_uuid, owner_key)

    # Find uploaded video file
    input_path = find_uploaded_video(payload.video_id)

    # Query segments from database
    segment_rows = (
        db.query(SegmentRow)
        .filter(SegmentRow.video_id == video_uuid)
        .order_by(SegmentRow.start)
        .all()
    )

    if segment_rows:
        # Use segments from database (source of truth)
        segments = segments_rows_to_schemas(segment_rows)
    else:
        # Fallback: use segments from payload if no DB segments exist
        segments = payload.segments

    # Burn video
    output_path = burn_video_with_subtitles(
        input_path,
        payload.video_id,
        segments,
        payload.style
    )

    return FileResponse(
        path=str(output_path),
        media_type="video/*",
        filename=output_path.name
    )

