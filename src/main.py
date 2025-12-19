# src/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import uuid

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

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#User posts video file
@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # 1) Create a stable id for this uploaded video
    video_id = str(uuid.uuid4())

    # 2) Determine file extension (default to .mp4 if unknown)
    orig_suffix = Path(file.filename).suffix.lower()
    suffix = orig_suffix if orig_suffix else ".mp4"

    # 3) Persist file on backend so we can burn later without re-uploading
    saved_path = UPLOAD_DIR / f"{video_id}{suffix}"

    try:
        with open(saved_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")
    finally:
        # Make sure the temporary upload stream is closed
        try:
            file.file.close()
        except Exception:
            pass

    # 4) Generate timing segments from the saved file
    try:
        segments = generate_timing_segments(str(saved_path))
    except Exception as e:
        # If transcription fails, delete the uploaded file to avoid clutter
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    # 5) Return both video_id + segments so the frontend can edit and later burn
    return JSONResponse(content={
        "video_id": video_id,
        "segments": segments
    })
