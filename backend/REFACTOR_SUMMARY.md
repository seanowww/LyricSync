# Backend Refactor Summary

## Overview

This refactor addresses critical bugs in the `POST /api/transcribe` endpoint and reorganizes the codebase into a clean, maintainable structure following FastAPI and SQLAlchemy 2.0 best practices.

## Critical Bugs Fixed

### 1. **Undefined `db` Variable (CRITICAL)**
   - **Problem**: Line 290-291 in `main.py` used `db.add(video)` and `db.commit()` but `db` was never defined
   - **Fix**: Added `db: Session = Depends(get_db)` to route handler
   - **Impact**: This would have caused a runtime error on every transcription request

### 2. **UUID Type Mismatch**
   - **Problem**: `video_id` was generated as `str(uuid.uuid4())` but DB model expects `uuid.UUID`
   - **Fix**: Changed to `uuid.uuid4()` (UUID object) and convert to string only for JSON response
   - **Impact**: Would cause database constraint violations

### 3. **Transaction Boundary Issues**
   - **Problem**: DB record was created and committed BEFORE transcription. If transcription failed, orphaned DB record remained
   - **Fix**: Create DB record in transaction, transcribe, then commit once. If transcription fails, transaction rolls back automatically
   - **Impact**: Prevents orphaned database records

### 4. **Filesystem/DB Coupling**
   - **Problem**: File saved before DB insert. If DB insert failed, orphaned file remained
   - **Fix**: Save file first (acceptable - can be cleaned up), but ensure DB transaction rolls back if transcription fails
   - **Impact**: Better cleanup on failures

### 5. **Broken Code in `segments_store.py`**
   - **Problem**: Lines 55-58 referenced undefined `Segment` and `db` variables
   - **Fix**: Marked file as deprecated (segments now in DB) and removed broken code
   - **Impact**: Would have caused import errors

## New Directory Structure

```
backend/src/
├── main.py                 # App creation + router registration
├── db/
│   ├── __init__.py
│   └── session.py          # Engine + SessionLocal + get_db
├── models/
│   ├── __init__.py
│   ├── video.py            # Video ORM model
│   ├── segment.py          # SegmentRow ORM model
│   └── style.py            # StyleRow ORM model
├── schemas/
│   ├── __init__.py
│   ├── segment.py          # Segment Pydantic schema
│   ├── style.py            # Style Pydantic schema
│   └── requests.py        # Request/response schemas
├── routes/
│   ├── __init__.py
│   ├── transcribe.py       # POST /api/transcribe
│   ├── video.py            # GET /api/video/{video_id}
│   ├── segments.py         # GET/PUT /api/segments/{video_id}
│   └── burn.py             # POST /api/burn
└── services/
    ├── __init__.py
    ├── storage.py          # Filesystem operations
    ├── transcribe_service.py  # Transcription orchestration
    ├── burn_service.py     # Video burning logic
    ├── auth.py             # Owner key validation
    └── mappers.py          # DB ↔ API model mapping
```

## Architectural Changes

### Separation of Concerns

1. **Routes** (`routes/`): Thin HTTP handlers that:
   - Validate input
   - Call services
   - Return responses
   - Handle HTTP-specific concerns

2. **Services** (`services/`): Business logic that:
   - Orchestrates complex operations
   - Manages transactions
   - Handles errors
   - Is testable in isolation

3. **Models** (`models/`): SQLAlchemy ORM models that:
   - Represent database tables
   - Never returned directly to clients
   - Mapped to schemas via mappers

4. **Schemas** (`schemas/`): Pydantic models that:
   - Define API contracts
   - Validate request/response data
   - Separate from DB models

### Transaction Management

**Before**: DB operations scattered, no clear transaction boundaries

**After**: 
- Single transaction per operation
- Commit once after all operations succeed
- Automatic rollback on exceptions
- Clear error handling

### Ownership Checks

**Before**: No ownership validation on endpoints

**After**:
- All modifying endpoints require `X-Owner-Key` header
- Centralized `require_owner_key()` dependency
- `get_video_or_404()` helper for ownership checks

### Segments Storage Migration

**Before**: Segments stored in filesystem JSON files

**After**:
- Segments stored in database (`segments` table)
- Better querying and validation
- Transactional updates
- No file I/O for segment operations

## Key Improvements

1. **Atomicity**: Transcription either fully succeeds or fully fails (no partial state)
2. **Error Handling**: Proper cleanup on failures (file deletion, transaction rollback)
3. **Testability**: Services can be tested independently of routes
4. **Maintainability**: Clear separation of concerns, easy to find and modify code
5. **Type Safety**: Proper UUID types, Pydantic validation
6. **Documentation**: Extensive comments explaining WHY, not just WHAT

## Migration Notes

- Old `segments_store.py` is deprecated but kept for backward compatibility
- All endpoints now require `X-Owner-Key` header (except `/api/transcribe` which generates it)
- Segments are read from/written to database, not filesystem
- Video files still stored in filesystem (as intended)

## Testing Recommendations

1. **Unit Tests**: Test services in isolation (mock DB session)
2. **Integration Tests**: Test full flow with test database
3. **Transaction Tests**: Verify rollback on failures
4. **Ownership Tests**: Verify access control works

## Next Steps

1. Remove deprecated `segments_store.py` after confirming no external dependencies
2. Add database migrations for any schema changes
3. Add comprehensive test coverage
4. Consider adding style storage to database (currently only in burn request)

