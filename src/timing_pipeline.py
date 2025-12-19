import os
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

VIDEO_CONTAINERS = {".mov", ".mp4", ".webm"}

def _extract_audio_to_wav(input_path: str) -> str:
    """
    Extract audio track from a video into a WAV file (mono, 16kHz).
    Whisper accepts wav/mp3/mp4/webm etc. WAV is easiest/reliable.
    """
    in_path = Path(input_path)
    wav_path = in_path.with_suffix(".extracted.wav")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_path),
        "-vn",              # drop video
        "-ac", "1",         # mono
        "-ar", "16000",     # 16kHz
        str(wav_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr[-1500:]}")

    return str(wav_path)


def generate_timing_segments(file_path: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    in_path = Path(file_path)

    audio_path = str(in_path)
    extracted_wav = None

    # If it's a video container (like .mov), extract audio first
    if in_path.suffix.lower() in VIDEO_CONTAINERS:
        extracted_wav = _extract_audio_to_wav(str(in_path))
        audio_path = extracted_wav

    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )

        # Convert transcript.segments into your JSON-ready list
        segments = []
        for seg in transcript.segments:
            segments.append({
                "id": seg["id"] if isinstance(seg, dict) else seg.id,
                "start": seg["start"] if isinstance(seg, dict) else seg.start,
                "end": seg["end"] if isinstance(seg, dict) else seg.end,
                "text": (seg["text"] if isinstance(seg, dict) else seg.text).strip(),
            })

        return segments

    finally:
        # Clean up extracted audio file if we created one
        if extracted_wav:
            try:
                Path(extracted_wav).unlink(missing_ok=True)
            except Exception:
                pass
