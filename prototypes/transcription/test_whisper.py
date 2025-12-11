import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

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

print(transcript)
