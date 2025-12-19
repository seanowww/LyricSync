from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str

class SegmentsUpdateRequest(BaseModel):
    segments: List[Dict[str, Any]] = Field(..., description="List of segment objects")

class Style(BaseModel):
    preset: Optional[str] = "default"

    # existing fields (future)
    x: Optional[float] = None
    y: Optional[float] = None
    fontSize: Optional[int] = None
    color: Optional[str] = None
    align: Optional[str] = None

class BurnRequest(BaseModel):
    video_id: str
    segments: List[Segment]
    style: Optional[Style] = None
