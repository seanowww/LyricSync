# src/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi import HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.schemas import BurnRequest, SegmentsUpdateRequest
from pathlib import Path
from src.services.segments_store import load_segments, save_segments
from typing import Any, Dict, List
from fastapi.staticfiles import StaticFiles

import logging
import uuid
import subprocess
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lyricsync")

load_dotenv()

from .timing_pipeline import generate_timing_segments

app = FastAPI()

STATIC_DIR = Path("src/static")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/preview")
async def serve_preview():
    return FileResponse(str(STATIC_DIR / "preview.html"))

origins = ["http://localhost:8000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # allow POST, GET, etc.
    allow_headers=["*"],    # allow Content-Type, Authorization, etc.
)

BASE_DIR = Path(__file__).resolve().parent  # src/

FONTS_DIR = BASE_DIR / "assets" / "fonts"  # src/assets/fonts

SERVICES_DIR = BASE_DIR / "services"

STORAGE_DIR = BASE_DIR / "storage"

SEGMENTS_DIR = STORAGE_DIR / "segments"
UPLOAD_DIR = STORAGE_DIR / "uploads"
TMP_DIR = STORAGE_DIR / "tmp"
OUTPUT_DIR = STORAGE_DIR / "outputs"

for d in (UPLOAD_DIR, TMP_DIR, OUTPUT_DIR, FONTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB for MVP

ALLOWED_EXTS = {".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm"}

# Helpers

def copy_with_limit(src, dst, max_bytes: int):
    total = 0
    chunk_size = 1024 * 1024  # 1 MB
    while True:
        chunk = src.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="File too large for MVP limit.")
        dst.write(chunk)

def _find_uploaded_video(video_id: str) -> Path:
    """
    Locate the uploaded file regardless of extension, because uploads may be .mp4/.mov/.webm etc.
    """
    matches = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Video not found for video_id={video_id}")
    return matches[0]

def _probe_video_resolution(path: Path) -> tuple[int, int]:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"ffprobe failed: {result.stderr[-500:]}")
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])


def _format_ass_timestamp(seconds: float) -> str:
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


def _escape_ass_text(text: str) -> str:
    text = (text or "").replace("\r", "")
    text = text.replace("\n", r"\N")
    text = text.replace("{", r"\{").replace("}", r"\}")
    return text


def _css_hex_to_ass(hex_color: str) -> str:
    # "#RRGGBB" -> "&H00BBGGRR" (alpha 00 = opaque)
    c = (hex_color or "#FFFFFF").lstrip("#")
    if len(c) != 6:
        c = "FFFFFF"
    rr, gg, bb = c[0:2], c[2:4], c[4:6]
    return f"&H00{bb}{gg}{rr}"


def _align_to_ass(align: str) -> int:
    # MVP: only bottom-center is supported
    return 2  # bottom-center


def _segments_to_ass(segments, style, play_res_x: int, play_res_y: int) -> str:
    """
    Build an .ass subtitle file.
    MVP sync rules:
    - Frontend drags (posX,posY) in VIDEO pixels.
    - Backend must burn at the same absolute position using ASS override tags:
        {\an2\pos(x,y)}  # bottom-center anchored at (x,y)
    - We no longer rely on MarginV (marginBottomPx removed).
    """

    # ---- 1) Style defaults ----
    font = style.fontFamily if style and style.fontFamily else "Inter"
    size = style.fontSizePx if style and style.fontSizePx else 28
    primary = _css_hex_to_ass(style.color) if style and style.color else "&H00FFFFFF"

    # Outline color: only accept hex (your frontend now sends hex like "#000000")
    outline_color = "&H00000000"  # black
    if style and style.strokeColor and style.strokeColor.startswith("#"):
        outline_color = _css_hex_to_ass(style.strokeColor)

    outline = style.strokePx if style and style.strokePx is not None else 3
    shadow = style.shadowPx if style and style.shadowPx is not None else 0

    # We still keep alignment=2 in the style as a default (bottom-center),
    # BUT the real placement is done by \an2 + \pos(...) per Dialogue line.
    alignment = 2
    margin_v = 0  # not used if we always apply \pos()

    # ---- 2) Position defaults (match your frontend defaults) ----
    # Frontend: defaultX = vw/2, defaultY = vh*0.88
    if style and style.posX is not None:
        x = int(round(float(style.posX)))
    else:
        x = play_res_x // 2

    if style and style.posY is not None:
        y = int(round(float(style.posY)))
    else:
        y = int(round(play_res_y * 0.88))

    # Clamp just in case user drags outside bounds
    x = max(0, min(play_res_x, x))
    y = max(0, min(play_res_y, y))

    # ASS override tag:
    # \an2 = bottom-center anchor (matches frontend translate(-50%,-100%))
    # \pos(x,y) = absolute position in PlayRes coordinates
    pos_tag = f"{{\\an2\\pos({x},{y})}}"

    # ---- 3) Header ----
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{primary},&H000000FF,{outline_color},&H64000000,0,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # ---- 4) Dialogue lines ----
    lines = [header]
    any_text = False

    for seg in segments:
        start = _format_ass_timestamp(seg.start)
        end = _format_ass_timestamp(seg.end)
        text = _escape_ass_text(seg.text).strip()
        if not text:
            continue

        any_text = True

        # Inject the position tag at the start of the line text.
        # IMPORTANT: we include the tag per-line to guarantee sync with drag position.
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{pos_tag}{text}\n")

    if not any_text:
        raise HTTPException(status_code=400, detail="No non-empty segments to burn.")

    return "".join(lines)


def _validate_segments_mvp(segments: List[Dict[str, Any]]) -> None:
    """
    MVP validation:
    - must be a list
    - each segment must have: start, end, text
    - start/end must be numbers, start < end
    - text must be a string
    """
    if not isinstance(segments, list):
        raise HTTPException(status_code=422, detail="segments must be a list")

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            raise HTTPException(status_code=422, detail=f"segments[{i}] must be an object")

        for key in ("start", "end", "text"):
            if key not in seg:
                raise HTTPException(status_code=422, detail=f"segments[{i}] missing '{key}'")

        start = seg["start"]
        end = seg["end"]
        text = seg["text"]

        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise HTTPException(status_code=422, detail=f"segments[{i}] start/end must be numbers")

        if start < 0 or end < 0 or start >= end:
            raise HTTPException(status_code=422, detail=f"segments[{i}] must satisfy 0 <= start < end")

        if not isinstance(text, str):
            raise HTTPException(status_code=422, detail=f"segments[{i}] text must be a string")
        
# Routing

# User posts video file
@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())

    # Determine extension
    suffix = Path(file.filename).suffix.lower() or ".mp4"
    if suffix not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    # Persist upload
    saved_path = UPLOAD_DIR / f"{video_id}{suffix}"

    try:
        with open(saved_path, "wb") as out_file:
            copy_with_limit(file.file, out_file, MAX_UPLOAD_BYTES)
    except HTTPException:
        # re-raise size limit error cleanly
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")
    finally:
        try:
            file.file.close()
        except Exception:
            pass

    # Generate timing segments (this function must handle video -> audio extraction internally)
    try:
        segments = generate_timing_segments(str(saved_path))
        save_segments(video_id, segments, source="whisper_verbose_json")
    except Exception as e:
        # Clean up the saved upload if transcription fails
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass

        msg = str(e)
        # Friendlier hint for the most common cause
        if "Invalid file format" in msg:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Transcription failed due to unsupported media container. "
                    "If you uploaded a video like .mov, ensure the backend extracts audio to .wav/.mp3 "
                    "before calling Whisper."
                ),
            )

        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    return JSONResponse(content={
        "video_id": video_id,
        "segments": segments
    })

@app.get("/api/video/{video_id}")
async def get_video(video_id: str):
    # Find the uploaded file regardless of extension (mp4/mov/webm/etc.)
    matches = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    video_path = matches[0]  # MVP: assume one match

    # Stream the file back to the client
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",   # MVP: okay; optional improvement below
        filename=video_path.name
    )

@app.get("/api/segments/{video_id}")
async def get_segments(video_id: str):
    try:
        payload = load_segments(video_id)  # returns dict with video_id, segments, etc.
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Segments not found: {video_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load segments: {e}")

    # Return only what the frontend needs
    return JSONResponse(content={
        "video_id": payload["video_id"],
        "segments": payload["segments"],
    })

@app.post("/api/burn")
async def burn_video(payload: BurnRequest):
    input_path = _find_uploaded_video(payload.video_id)

    # PlayRes must match the video resolution to sync with frontend “video px”
    play_res_x, play_res_y = _probe_video_resolution(input_path)

    ass_text = _segments_to_ass(payload.segments, payload.style, play_res_x, play_res_y)
    ass_path = TMP_DIR / f"{payload.video_id}.ass"
    ass_path.write_text(ass_text, encoding="utf-8")

    logger.info("burn_start video_id=%s", payload.video_id)
    logger.info("burn_style=%s", payload.style.model_dump() if payload.style else None)
    logger.info("burn_res=%sx%s", play_res_x, play_res_y)
    logger.info("burn_ass_path=%s", str(ass_path))

    output_path = OUTPUT_DIR / f"{payload.video_id}_burned.mp4"

    vf = f"subtitles={str(ass_path)}:fontsdir={str(FONTS_DIR)}"

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:a", "copy",
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
        raise HTTPException(status_code=500, detail="FFmpeg not found. Install ffmpeg and ensure it is on PATH.")

    if result.returncode != 0:
        err_tail = result.stderr[-2000:]
        raise HTTPException(status_code=500, detail=f"FFmpeg failed. stderr tail:\n{err_tail}")

    if not output_path.exists():
        raise HTTPException(status_code=500, detail="Burn succeeded but output file missing.")

    return FileResponse(
        path=str(output_path),
        media_type="video/*",
        filename=output_path.name
    )

@app.put("/api/segments/{video_id}")
async def update_segments(video_id: str, body: SegmentsUpdateRequest):
    # 1) Ensure this video_id exists (segments were generated before)
    try:
        _ = load_segments(video_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Segments not found: {video_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load existing segments: {e}")

    # 2) Validate incoming segments
    try:
        _validate_segments_mvp(body.segments)
    except HTTPException:
        # Pass through our validation messages
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected validation error: {e}")

    # 3) Save
    try:
        save_segments(video_id, body.segments, source="manual_edit")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save segments: {e}")

    # 4) Respond (return latest)
    return JSONResponse(content={
        "video_id": video_id,
        "segments": body.segments
    })