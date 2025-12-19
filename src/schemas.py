from pydantic import BaseModel
from typing import List, Optional

class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str

class Style(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    fontSize: Optional[int] = None
    color: Optional[str] = None
    align: Optional[str] = None

class BurnRequest(BaseModel):
    video_id: str
    segments: List[Segment]
    style: Optional[Style] = None
