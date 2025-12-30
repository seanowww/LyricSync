# services/burn_service.py
"""
Video burning service.

WHY: Handles ASS subtitle generation and FFmpeg video burning.
Separated from routes for testability and reusability.
"""
import json
import subprocess
import logging
from pathlib import Path
from fastapi import HTTPException
from src.utils.ass_helpers import (
    format_ass_timestamp,
    escape_ass_text,
    css_hex_to_ass,
)
from src.schemas.style import Style
from src.schemas.segment import Segment

logger = logging.getLogger("lyricsync")

# Storage directories
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
TMP_DIR = STORAGE_DIR / "tmp"
OUTPUT_DIR = STORAGE_DIR / "outputs"
FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

# Ensure directories exist
for d in (TMP_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def probe_video_resolution(path: Path) -> tuple[int, int]:
    """
    Get video resolution using ffprobe.
    
    WHY: We need the video resolution to match PlayRes in ASS subtitles.
    This ensures frontend drag coordinates match burned subtitle positions.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"ffprobe failed: {result.stderr[-500:]}"
        )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])


def segments_to_ass(
    segments: list[Segment],
    style: Style | None,
    play_res_x: int,
    play_res_y: int
) -> str:
    """
    Build an ASS subtitle file.
    
    WHY: Converts segments and style into ASS format for FFmpeg.
    Frontend drags (posX,posY) in VIDEO pixels, so we use \pos(x,y) in ASS.
    """
    # Style defaults
    base_font = style.fontFamily if style and style.fontFamily else "Inter"
    # Build font name with Bold/Italic suffix to match font file names
    font = base_font
    if style and style.bold and style.italic:
        font = f"{base_font} Bold Italic"
    elif style and style.bold:
        font = f"{base_font} Bold"
    elif style and style.italic:
        font = f"{base_font} Italic"
    
    size = style.fontSizePx if style and style.fontSizePx else 28
    opacity = style.opacity if style and style.opacity is not None else 100
    primary = css_hex_to_ass(style.color, opacity) if style and style.color else css_hex_to_ass("#FFFFFF", opacity)

    # Outline color
    outline_color = "&H00000000"  # black
    if style and style.strokeColor and style.strokeColor.startswith("#"):
        outline_color = css_hex_to_ass(style.strokeColor)

    outline = style.strokePx if style and style.strokePx is not None else 3
    shadow = style.shadowPx if style and style.shadowPx is not None else 0

    # Rotation angle (ASS uses degrees, 0 = no rotation)
    rotation = style.rotation if style and style.rotation is not None else 0

    alignment = 2  # bottom-center
    margin_v = 0

    # Position defaults (match frontend defaults)
    if style and style.posX is not None:
        x = int(round(float(style.posX)))
    else:
        x = play_res_x // 2

    if style and style.posY is not None:
        y = int(round(float(style.posY)))
    else:
        y = int(round(play_res_y * 0.88))

    # Clamp to video bounds
    x = max(0, min(play_res_x, x))
    y = max(0, min(play_res_y, y))

    # ASS override tag: \an2 = bottom-center, \pos(x,y) = absolute position, \frz = rotation in degrees
    # \frz rotates around the position point
    if rotation != 0:
        pos_tag = f"{{\\an2\\pos({x},{y})\\frz{rotation}}}"
    else:
        pos_tag = f"{{\\an2\\pos({x},{y})}}"

    # ASS header
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{primary},&H000000FF,{outline_color},&H64000000,0,0,0,0,100,100,0,{rotation},1,{outline},{shadow},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Dialogue lines
    lines = [header]
    any_text = False

    for seg in segments:
        start = format_ass_timestamp(seg.start)
        end = format_ass_timestamp(seg.end)
        text = escape_ass_text(seg.text).strip()
        if not text:
            continue

        any_text = True
        # Include position tag per-line to guarantee sync with drag position
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{pos_tag}{text}\n")

    if not any_text:
        raise HTTPException(status_code=400, detail="No non-empty segments to burn.")

    return "".join(lines)


def burn_video_with_subtitles(
    input_path: Path,
    video_id: str,
    segments: list[Segment],
    style: Style | None
) -> Path:
    """
    Burn subtitles into video using FFmpeg.
    
    WHY: Centralized burning logic. Handles ASS generation and FFmpeg execution.
    Returns path to burned video file.
    """
    # Get video resolution
    play_res_x, play_res_y = probe_video_resolution(input_path)

    # Generate ASS file
    ass_text = segments_to_ass(segments, style, play_res_x, play_res_y)
    ass_path = TMP_DIR / f"{video_id}.ass"
    ass_path.write_text(ass_text, encoding="utf-8")

    logger.info("burn_start video_id=%s", video_id)
    logger.info("burn_style=%s", style.model_dump() if style else None)
    logger.info("burn_res=%sx%s", play_res_x, play_res_y)

    # Output path
    output_path = OUTPUT_DIR / f"{video_id}_burned.mp4"

    # FFmpeg command
    # WHY: Uses subtitles filter with fontsdir to load custom fonts
    # IMPORTANT: Preserve original video resolution by using scale filter
    # The subtitles filter can sometimes change resolution, so we explicitly scale to original
    vf = f"subtitles={str(ass_path)}:fontsdir={str(FONTS_DIR)},scale={play_res_x}:{play_res_y}"
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",  # Re-encode video to ensure resolution is preserved
        "-preset", "medium",  # Balance between speed and quality
        "-crf", "23",  # Good quality (lower = better quality, 18-28 is typical range)
        "-c:a", "copy",  # Copy audio without re-encoding
        str(output_path),
    ]

    try:
        result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="FFmpeg not found. Install ffmpeg and ensure it is on PATH."
        )

    if result.returncode != 0:
        err_tail = result.stderr[-2000:]
        raise HTTPException(
            status_code=500,
            detail=f"FFmpeg failed. stderr tail:\n{err_tail}"
        )

    if not output_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Burn succeeded but output file missing."
        )

    return output_path

