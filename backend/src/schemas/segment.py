# schemas/segment.py
"""
Segment Pydantic schemas for API requests/responses.

WHY: Separates API contracts from DB models.
Frontend sends/receives these, not raw SQLAlchemy models.
"""
from pydantic import BaseModel


class Segment(BaseModel):
    """
    Segment API model.
    
    WHY: This is what the frontend sends and receives.
    The 'id' field is used for ordering/editing segments within a video.
    """
    id: int
    start: float  # seconds
    end: float    # seconds
    text: str

