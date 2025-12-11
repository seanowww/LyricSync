import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import json

# Load .env variables
load_dotenv()

# --- Path handling ---
BASE_DIR = Path(__file__).resolve().parent
audio_path = BASE_DIR / "audio" / "test_cover_1.mp3"

print("Loading file:", audio_path)

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY")
)

with open(audio_path, "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json"
    )

print("Full transcript text:")
print(transcript.text)
print()

# --- Build timing JSON backbone ---
timing = []
for seg in transcript.segments:
    timing.append({
        "id": seg["id"] if isinstance(seg, dict) else seg.id,
        "start": seg["start"] if isinstance(seg, dict) else seg.start,
        "end": seg["end"] if isinstance(seg, dict) else seg.end,
        "text": (seg["text"] if isinstance(seg, dict) else seg.text).strip(),
    })

# Save to file
timing_path = BASE_DIR / "timing.json"
with open(timing_path, "w") as f:
    json.dump(timing, f, indent=2)

print(f"Saved {len(timing)} segments to {timing_path}")
