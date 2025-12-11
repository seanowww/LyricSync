# src/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import tempfile

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

#User posts video file
@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    suffix = "." + (file.filename.split(".")[-1] if "." in file.filename else "tmp")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    segments = generate_timing_segments(tmp_path)
    return JSONResponse(content={"segments": segments})