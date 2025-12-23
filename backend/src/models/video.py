# models/video.py
"""
Video ORM model.

WHY: Represents a video project in the database.
Each video has an owner_key for access control and stores file paths.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.session import Base


class Video(Base):
    """
    Video project model.
    
    WHY: This is the anchor table. All segments and styles reference a video.
    The video_id (UUID) is used both in DB and filesystem paths for consistency.
    """
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Owner key for access control (sent in X-Owner-Key header)
    owner_key: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # File paths (relative to storage directory)
    original_uri: Mapped[str] = mapped_column(String, nullable=False)
    burned_uri: Mapped[str | None] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships (cascade delete: if video is deleted, segments/style are too)
    segments = relationship(
        "SegmentRow",
        back_populates="video",
        cascade="all, delete-orphan"
    )
    style = relationship(
        "StyleRow",
        back_populates="video",
        cascade="all, delete-orphan",
        uselist=False  # One-to-one relationship
    )

