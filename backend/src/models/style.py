# models/style.py
"""
Style ORM model.

WHY: Stores rendering configuration (font, color, position) as JSON.
One style per video (one-to-one relationship).
"""
import uuid
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.session import Base


class StyleRow(Base):
    """
    Style configuration model.
    
    WHY: Uses JSON to store flexible style data (fontFamily, fontSizePx, etc.)
    This allows schema evolution without migrations for style fields.
    Uses JSON (not JSONB) for SQLite compatibility in tests.
    """
    __tablename__ = "styles"

    # Primary key and foreign key to videos
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id"),
        primary_key=True
    )
    
    # Style configuration as JSON (matches Pydantic Style model)
    # Uses JSON instead of JSONB for SQLite compatibility
    style_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relationship back to video
    video = relationship("Video", back_populates="style")

