# routes/transcribe.py
"""
POST /api/transcribe endpoint.

WHY: This route handles video upload and transcription.
It's separated from main.py to keep routes organized and testable.

CRITICAL FIXES APPLIED:
1. Generate video_id and owner_key BEFORE any operations (atomicity)
2. Use get_db() dependency (was using undefined 'db' variable)
3. Convert video_id to UUID (was string, DB expects UUID)
4. Save file AFTER generating IDs but BEFORE DB insert
5. Create DB record in transaction, then transcribe
6. If transcription fails, rollback DB transaction (no orphaned records)
7. If DB insert fails, file is already saved (acceptable - can be cleaned up later)
"""
import uuid
import secrets
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.services.storage import save_uploaded_file
from src.services.transcribe_service import create_video_project, transcribe_video

router = APIRouter()


@router.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload video and transcribe it.
    
    FLOW (corrected order):
    1. Generate video_id (UUID) and owner_key FIRST
    2. Save file to filesystem (using video_id)
    3. Create DB record (in transaction, not committed yet)
    4. Run transcription (may take time)
    5. Save segments to DB
    6. Commit transaction (all or nothing)
    7. Return response
    
    WHY THIS ORDER:
    - IDs generated first ensure we can reference the project consistently
    - File saved before DB so we have the file path for DB record
    - DB record created but not committed until transcription succeeds
    - If transcription fails, transaction rolls back (no orphaned DB record)
    - If DB fails, file exists but can be cleaned up (acceptable tradeoff)
    """
    # STEP 1: Generate IDs FIRST (before any side effects)
    # WHY: Ensures we have consistent identifiers for the entire operation
    video_id = uuid.uuid4()  # UUID object, not string
    owner_key = secrets.token_urlsafe(32)

    # STEP 2: Save file to filesystem
    # WHY: We need the file path for the DB record
    # If this fails, we haven't touched the DB yet (clean failure)
    try:
        saved_path = save_uploaded_file(file, str(video_id))
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Unexpected file save error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save upload: {e}"
        )

    # STEP 3: Create DB record (in transaction, not committed yet)
    # WHY: We create the record now so we can reference it
    # But we don't commit until transcription succeeds
    try:
        video = create_video_project(db, saved_path, video_id, owner_key)
    except Exception as e:
        # If DB insert fails, clean up the file
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create video record: {e}"
        )

    # STEP 4: Transcribe and save segments
    # WHY: This is the expensive operation. If it fails, we rollback the transaction.
    try:
        segments = transcribe_video(db, saved_path, video_id, owner_key)
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors from transcription)
        # Transaction will rollback automatically (we haven't committed)
        # Clean up the file
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    except Exception as e:
        # Unexpected transcription error
        # Transaction will rollback automatically
        # Clean up the file
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {e}"
        )

    # STEP 5: Return response
    # WHY: Transaction is committed in transcribe_video() if we reach here
    return JSONResponse(content={
        "video_id": str(video_id),  # Convert UUID to string for JSON
        "owner_key": owner_key,
        "segments": segments
    })

