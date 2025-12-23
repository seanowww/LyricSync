# schemas/style.py
"""
Style Pydantic schema for rendering configuration.

WHY: Defines the structure of style data that can be stored in DB (as JSONB)
and sent to/from the frontend.
"""
from pydantic import BaseModel
from typing import Optional


class Style(BaseModel):
    """
    Style configuration model.
    
    WHY: This matches what the frontend TextStylingPanel sends.
    Stored in DB as JSONB (via StyleRow.style_json).
    """
    # Named preset for UX
    preset: str = "default"

    # Font configuration
    fontFamily: str = "Inter"
    fontSizePx: int = 28  # Video pixels (scaled in frontend overlay)
    bold: bool = False
    italic: bool = False

    # Color configuration
    color: str = "#FFFFFF"  # CSS hex
    strokePx: int = 3  # Outline thickness
    strokeColor: str = "rgba(0,0,0,0.85)"  # CSS color
    shadowPx: int = 0

    # Positioning (in video pixels)
    posX: Optional[float] = None
    posY: Optional[float] = None

    # Layout
    align: str = "bottom-center"
    maxWidthPct: int = 90  # Wrapping width in preview (frontend only)

