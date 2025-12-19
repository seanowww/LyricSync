# src/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi import HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.schemas import BurnRequest
from pathlib import Path
import shutil
import uuid
import subprocess
import shlex

load_dotenv()

from .timing_pipeline import generate_timing_segments

app = FastAPI()

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # allow POST, GET, etc.
    allow_headers=["*"],    # allow Content-Type, Authorization, etc.
)

UPLOAD_DIR = Path("src/storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = Path("src/storage/tmp")
OUTPUT_DIR = Path("src/storage/outputs")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB for MVP

ALLOWED_EXTS = {".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm"}

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

def _format_srt_timestamp(seconds: float) -> str:
    """
    Converts seconds (float) -> SRT timestamp 'HH:MM:SS,mmm'
    Example: 2.3 -> '00:00:02,300'
    """
    if seconds < 0:
        seconds = 0.0

    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60

    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _segments_to_srt(segments) -> str:
    """
    Convert list of {id,start,end,text} into SRT file content.
    Important: SRT expects entries numbered from 1..N (not necessarily your segment.id).
    """
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_ts = _format_srt_timestamp(seg.start)
        end_ts = _format_srt_timestamp(seg.end)

        # Minimal sanitation: strip whitespace; avoid empty captions
        text = (seg.text or "").strip()
        if not text:
            continue

        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")  # blank line between cues

    if not lines:
        raise HTTPException(status_code=400, detail="No non-empty segments to burn.")

    return "\n".join(lines)


def _find_uploaded_video(video_id: str) -> Path:
    """
    Locate the uploaded file regardless of extension, because uploads may be .mp4/.mov/.webm etc.
    """
    matches = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Video not found for video_id={video_id}")
    return matches[0]


@app.post("/api/burn")
async def burn_video(payload: BurnRequest):

    # 1) Locate the previously uploaded video
    input_path = _find_uploaded_video(payload.video_id)

    # 2) Generate SRT from segments and write it to a temp file
    srt_text = _segments_to_srt(payload.segments)
    srt_path = TMP_DIR / f"{payload.video_id}.srt"
    srt_path.write_text(srt_text, encoding="utf-8")

    # 3) Choose output path
    output_path = OUTPUT_DIR / f"{payload.video_id}_burned.mp4"

    # 4) Run FFmpeg
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",  # overwrite output if exists
        "-i", str(input_path),
        "-vf", f"subtitles={str(srt_path)}",
        "-c:a", "copy",  # keep original audio without re-encoding
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
        # ffmpeg isn't installed / not on PATH
        raise HTTPException(
            status_code=500,
            detail="FFmpeg not found. Install ffmpeg and ensure it is on PATH."
        )

    if result.returncode != 0:
        # Keep stderr short-ish; ffmpeg logs can be huge
        err_tail = result.stderr[-2000:]
        raise HTTPException(
            status_code=500,
            detail=f"FFmpeg failed. stderr tail:\n{err_tail}"
        )

    if not output_path.exists():
        raise HTTPException(status_code=500, detail="Burn succeeded but output file missing.")

    # 5) Return the rendered video to the client
    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=output_path.name
    )
