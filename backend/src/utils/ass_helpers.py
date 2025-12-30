"""
Pure helper functions for ASS subtitle generation.
Extracted from main.py to allow unit testing without importing FastAPI app.
"""
from typing import Optional


def format_ass_timestamp(seconds: float) -> str:
    """Format seconds as ASS timestamp: H:MM:SS.CC"""
    if seconds < 0:
        seconds = 0.0
    cs_total = int(round(seconds * 100))  # centiseconds
    cs = cs_total % 100
    total_s = cs_total // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape_ass_text(text: str) -> str:
    """Escape ASS special characters in text"""
    text = (text or "").replace("\r", "")
    text = text.replace("\n", r"\N")
    text = text.replace("{", r"\{").replace("}", r"\}")
    return text


def css_hex_to_ass(hex_color: str, opacity: Optional[int] = None) -> str:
    """
    Convert CSS hex color to ASS format: #RRGGBB -> &HAABBGGRR
    
    ASS uses BGR (Blue-Green-Red) format, not RGB.
    Format: &HAABBGGRR where:
    - AA = alpha (00 = opaque, FF = transparent)
    - BB = Blue component
    - GG = Green component  
    - RR = Red component
    
    Opacity: 0-100 (0 = transparent, 100 = opaque)
    ASS alpha: 0-255 (0 = opaque, 255 = transparent) - inverted!
    
    Example: #36ce5c (RGB: 54, 206, 92) -> &H005CCE36 (BGR: 92, 206, 54)
    """
    c = (hex_color or "#FFFFFF").lstrip("#").upper()  # Normalize to uppercase
    if len(c) != 6:
        c = "FFFFFF"
    rr, gg, bb = c[0:2], c[2:4], c[4:6]
    
    # Convert opacity (0-100) to ASS alpha (0-255, inverted)
    if opacity is not None:
        # opacity 100 = alpha 00 (opaque), opacity 0 = alpha FF (transparent)
        alpha_hex = format(int((100 - opacity) * 255 / 100), "02X")
    else:
        alpha_hex = "00"  # Default: opaque
    
    # ASS format: &HAABBGGRR (BGR order, not RGB)
    return f"&H{alpha_hex}{bb}{gg}{rr}"


def align_to_ass(align: str) -> int:
    """Convert alignment string to ASS alignment code"""
    # MVP: only bottom-center is supported
    return 2  # bottom-center

