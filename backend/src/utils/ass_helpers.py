"""
Pure helper functions for ASS subtitle generation.
Extracted from main.py to allow unit testing without importing FastAPI app.
"""


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


def css_hex_to_ass(hex_color: str) -> str:
    """Convert CSS hex color to ASS format: #RRGGBB -> &H00BBGGRR"""
    c = (hex_color or "#FFFFFF").lstrip("#")
    if len(c) != 6:
        c = "FFFFFF"
    rr, gg, bb = c[0:2], c[2:4], c[4:6]
    return f"&H00{bb}{gg}{rr}"


def align_to_ass(align: str) -> int:
    """Convert alignment string to ASS alignment code"""
    # MVP: only bottom-center is supported
    return 2  # bottom-center

