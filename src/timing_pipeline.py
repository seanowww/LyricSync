import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

def generate_timing_segments(file_path: str):
    
    client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
    )

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

    logging.debug("Full transcript text:")
    logging.debug(transcript.text)

    # --- Build timing JSON backbone ---
    timing = []
    for seg in transcript.segments:
        timing.append({
            "id": seg["id"] if isinstance(seg, dict) else seg.id,
            "start": seg["start"] if isinstance(seg, dict) else seg.start,
            "end": seg["end"] if isinstance(seg, dict) else seg.end,
            "text": (seg["text"] if isinstance(seg, dict) else seg.text).strip(),
        })

    return timing