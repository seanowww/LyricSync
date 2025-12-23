# main.py
"""
FastAPI application entry point.

WHY: This file creates the app and registers routers.
All route logic is in routes/ modules for organization.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lyricsync")

# Create FastAPI app
app = FastAPI()

# CORS configuration
# WHY: Allows frontend (Vite dev server) to make API calls
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
# WHY: Routes are organized in separate modules for maintainability
from src.routes import transcribe, video, segments, burn

app.include_router(transcribe.router)
app.include_router(video.router)
app.include_router(segments.router)
app.include_router(burn.router)

# Debug endpoint (can be removed in production)
from src.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from src.models.video import Video

@app.get("/debug/db")
def debug_db(db: Session = Depends(get_db)):
    """Debug endpoint to check database connection."""
    count = db.query(Video).count()
    return {"videos_count": count}
