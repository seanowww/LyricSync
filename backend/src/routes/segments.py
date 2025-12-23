# routes/segments.py
"""
GET /api/segments/{video_id} and PUT /api/segments/{video_id} endpoints.

WHY: Separated from main.py for organization.
These endpoints now use the database instead of filesystem.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.db.session import get_db
from src.services.auth import require_owner_key, get_video_or_404
from src.services.mappers import segments_rows_to_schemas
from src.models.segment import SegmentRow
from src.schemas.requests import SegmentsUpdateRequest

router = APIRouter()


def _validate_segments_mvp(segments: List[Dict[str, Any]]) -> None:
    """
    Validate segment structure.
    
    WHY: Centralized validation logic.
    Ensures segments have required fields and valid values.
    """
    if not isinstance(segments, list):
        raise HTTPException(status_code=422, detail="segments must be a list")

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            raise HTTPException(
                status_code=422,
                detail=f"segments[{i}] must be an object"
            )

        for key in ("start", "end", "text"):
            if key not in seg:
                raise HTTPException(
                    status_code=422,
                    detail=f"segments[{i}] missing '{key}'"
                )

        start = seg["start"]
        end = seg["end"]
        text = seg["text"]

        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise HTTPException(
                status_code=422,
                detail=f"segments[{i}] start/end must be numbers"
            )

        if start < 0 or end < 0 or start >= end:
            raise HTTPException(
                status_code=422,
                detail=f"segments[{i}] must satisfy 0 <= start < end"
            )

        if not isinstance(text, str):
            raise HTTPException(
                status_code=422,
                detail=f"segments[{i}] text must be a string"
            )


@router.get("/api/segments/{video_id}")
async def get_segments(
    video_id: str,
    owner_key: str = Depends(require_owner_key),
    db: Session = Depends(get_db)
):
    """
    Get segments for a video.
    
    WHY: Now reads from database instead of filesystem.
    Requires owner_key for access control.
    """
    try:
        video_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video_id format")

    # Verify ownership
    video = get_video_or_404(db, video_uuid, owner_key)

    # Load segments from database
    segment_rows = (
        db.query(SegmentRow)
        .filter(SegmentRow.video_id == video_uuid)
        .order_by(SegmentRow.start)  # Return in chronological order
        .all()
    )

    # Convert to API schemas
    segments = segments_rows_to_schemas(segment_rows)

    return JSONResponse(content={
        "video_id": video_id,
        "segments": [seg.model_dump() for seg in segments]
    })


@router.put("/api/segments/{video_id}")
async def update_segments(
    video_id: str,
    body: SegmentsUpdateRequest,
    owner_key: str = Depends(require_owner_key),
    db: Session = Depends(get_db)
):
    """
    Update segments for a video.
    
    WHY: Now writes to database instead of filesystem.
    Requires owner_key for access control.
    Uses transaction to ensure atomicity.
    """
    try:
        video_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video_id format")

    # Verify ownership
    video = get_video_or_404(db, video_uuid, owner_key)

    # Validate incoming segments
    try:
        _validate_segments_mvp(body.segments)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected validation error: {e}"
        )

    # Delete existing segments
    # WHY: Simple replace strategy - delete all, then insert new ones
    # This ensures we don't have orphaned segments if the update is partial
    db.query(SegmentRow).filter(SegmentRow.video_id == video_uuid).delete()

    # Insert new segments
    for seg_dict in body.segments:
        # Ensure 'id' field exists (use index if not provided)
        seg_id = seg_dict.get("id", body.segments.index(seg_dict))
        segment_row = SegmentRow(
            video_id=video_uuid,
            id=seg_id,
            start=seg_dict["start"],
            end=seg_dict["end"],
            text=seg_dict["text"]
        )
        db.add(segment_row)

    # Commit transaction
    db.commit()

    return JSONResponse(content={
        "video_id": video_id,
        "segments": body.segments
    })

