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
    # A named preset is still useful for UX
    preset: str = "default"

    # Shared render spec (works for both browser overlay + ASS burn)
    fontFamily: str = "Inter"
    fontSizePx: int = 28              # define in VIDEO PIXELS
    color: str = "#FFFFFF"            # CSS hex
    strokePx: int = 3                 # outline thickness
    strokeColor: str = "rgba(0,0,0,0.85)"
    shadowPx: int = 0                 # keep 0 for now
    align: str = "bottom-center"      # constrain to known set
    marginBottomPx: int = 48
    maxWidthPct: int = 90             # wrapping width in preview


class BurnRequest(BaseModel):
    video_id: str
    segments: List[Segment]
    style: Optional[Style] = None
