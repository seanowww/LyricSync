# schemas/requests.py
"""
Request/response Pydantic schemas for API endpoints.

WHY: Defines the shape of data sent to/from endpoints.
Separate from models to allow API evolution independent of DB schema.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.schemas.segment import Segment
from src.schemas.style import Style


class SegmentsUpdateRequest(BaseModel):
    """
    Request body for PUT /api/segments/{video_id}
    
    WHY: Frontend sends a list of segment dicts (flexible format).
    We validate and convert to Segment models in the service layer.
    """
    segments: List[Dict[str, Any]] = Field(
        ...,
        description="List of segment objects with start, end, text, id"
    )


class BurnRequest(BaseModel):
    """
    Request body for POST /api/burn
    
    WHY: Contains video_id, segments, and optional style.
    All data needed to generate ASS subtitles and burn into video.
    """
    video_id: str
    segments: List[Segment]
    style: Optional[Style] = None

