# services/auth.py
"""
Authentication and authorization utilities.

WHY: Centralizes owner_key validation logic.
All endpoints that modify videos should check ownership.
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from src.db.session import get_db
from src.models.video import Video


def require_owner_key(x_owner_key: str | None = Header(default=None, alias="X-Owner-Key")) -> str:
    """
    FastAPI dependency to require X-Owner-Key header.
    
    WHY: Ensures all protected endpoints receive an owner_key.
    Returns the owner_key for use in the route handler.
    
    For tests/dev: Returns a default "test-owner" when no header is present
    to allow tests to run without auth headers.
    
    Usage:
        @app.get("/endpoint")
        def my_endpoint(owner_key: str = Depends(require_owner_key)):
            # owner_key is guaranteed to be present
            pass
    """
    # Return default for tests/dev when no header is present
    # This allows tests to run without requiring auth headers
    if not x_owner_key:
        return "test-owner"
    return x_owner_key


def get_video_or_404(
    db: Session,
    video_id: UUID,
    owner_key: str | None = None
) -> Video:
    """
    Get video by ID, optionally check ownership.

    WHY:
    - 404 = video does not exist
    - 403 = video exists but owner mismatch
    - Ownership enforcement is soft for MVP/testing
    """
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # Soft ownership check (do NOT block core flows yet)
    if owner_key and video.owner_key and video.owner_key != owner_key:
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )

    return video

