# src/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import tempfile

from .timing_pipeline import generate_timing_segments

app = FastAPI()

#User posts video file
@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    suffix = "." + (file.filename.split(".")[-1] if "." in file.filename else "tmp")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    segments = generate_timing_segments(tmp_path)
    return JSONResponse(content={"segments": segments})