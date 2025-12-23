# models/segment.py
"""
Segment ORM model.

WHY: Represents a single lyric segment (time-aligned text) in the database.
Segments belong to a video and are stored in the DB, not filesystem.
"""
import uuid
from sqlalchemy import Integer, Float, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.session import Base


class SegmentRow(Base):
    """
    Lyric segment model.
    
    WHY: Composite primary key (video_id, id) ensures uniqueness per video.
    The 'id' field matches the Pydantic Segment.id for API consistency.
    """
    __tablename__ = "segments"
    
    # Table-level constraints
    __table_args__ = (
        # Ensure segment IDs are unique per video
        UniqueConstraint("video_id", "id", name="uq_segment_video_id"),
        # Ensure start < end (database-level validation)
        CheckConstraint("start < \"end\"", name="ck_segment_start_lt_end"),
    )

    # Composite primary key: (video_id, id)
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id"),
        primary_key=True
    )
    
    # Segment ID within the video (matches Pydantic Segment.id)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Timing (in seconds)
    start: Mapped[float] = mapped_column(Float, nullable=False)
    end: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Text content
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship back to video
    video = relationship("Video", back_populates="segments")

