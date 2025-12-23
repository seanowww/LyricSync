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
    
    Usage:
        @app.get("/endpoint")
        def my_endpoint(owner_key: str = Depends(require_owner_key)):
            # owner_key is guaranteed to be present
            pass
    """
    if not x_owner_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Owner-Key header"
        )
    return x_owner_key


def get_video_or_404(
    db: Session,
    video_id: UUID,
    owner_key: str
) -> Video:
    """
    Get video by ID and owner_key, or raise 404.
    
    WHY: Centralizes the "find video + check ownership" pattern.
    Prevents code duplication across endpoints.
    
    Args:
        db: Database session
        video_id: Video UUID
        owner_key: Owner key from header
    
    Returns:
        Video model if found and owned
    
    Raises:
        HTTPException: 404 if video not found or ownership doesn't match
    """
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.owner_key == owner_key)
        .first()
    )
    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )
    return video

