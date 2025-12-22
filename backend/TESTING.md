# Testing Guide for LyricSync Backend

## Overview

The test suite follows a **layered testing approach**:
- **Unit tests**: Fast, isolated tests for pure helper functions
- **Integration tests**: API endpoint tests with file I/O using temp directories
- **Golden snapshot tests**: Visual regression tests for burned video output

## Test Structure

```
backend/tests/
├── unit/              # Unit tests (pure functions, no I/O)
│   └── test_ass_helpers.py
├── integration/       # Integration tests (API endpoints, file I/O)
│   ├── test_segments_api.py
│   ├── test_burn_api.py
│   └── test_burn_golden.py  # Golden snapshot tests
├── assets/            # Test assets
│   └── golden/        # Golden reference images
└── conftest.py        # Shared fixtures
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pillow numpy python-multipart

# Ensure ffmpeg is available (for integration/golden tests)
ffmpeg -version
```

**Note**: `python-multipart` is required because FastAPI needs it for file upload endpoints. 
Even if you don't test the upload endpoint, importing `src.main` (which integration tests do) 
will trigger FastAPI route registration that checks for this dependency.

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Golden snapshot tests (requires ffmpeg)
pytest tests/integration/test_burn_golden.py
```

### Run with Verbose Output

```bash
pytest -v
```

## Test Layers Explained

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test pure helper functions in isolation
- No file I/O
- No network calls
- Fast execution (< 1 second total)
- Deterministic

**Example**: `_format_ass_timestamp()`, `_css_hex_to_ass()`

**Why this layer**: Catches logic errors early, fast feedback during development.

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test API endpoints end-to-end
- Uses FastAPI TestClient
- Creates temporary directories for isolation
- Tests actual file I/O (segments storage, video burning)
- Deterministic with cleanup

**Example**: GET/PUT segments, POST burn endpoint

**Why this layer**: Verifies the full stack works together, catches integration bugs.

### 3. Golden Snapshot Tests (`tests/integration/test_burn_golden.py`)

**Purpose**: Visual regression testing for burned video output
- Extracts frames from burned videos
- Compares to stored "golden" reference images
- Detects rendering regressions (font, position, color changes)

**Example**: Verify default style, large text, thick outline render correctly

**Why this layer**: Catches visual bugs that unit/integration tests miss (e.g., font rendering, positioning).

## Generating Golden Images

On first run, golden images are automatically created. To regenerate:

```bash
# Delete existing goldens
rm -rf tests/assets/golden/*.png

# Run golden tests (they will create new goldens)
pytest tests/integration/test_burn_golden.py -v
```

## Test Isolation

- Each test uses **temporary directories** (created via `tempfile.mkdtemp()`)
- Tests **monkey-patch** storage paths to use temp dirs
- **Cleanup** happens automatically via pytest fixtures
- No tests modify production data

## Continuous Integration

These tests are designed to run in CI:
- No external dependencies (except ffmpeg for integration tests)
- Deterministic (no random data, no network calls)
- Fast unit tests provide quick feedback
- Integration tests verify full pipeline

## Troubleshooting

### Tests fail with "ffmpeg not available"
- Install ffmpeg: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)
- Integration/golden tests will be skipped if ffmpeg is missing

### Golden test fails with high diff percentage
- Check if font file (Inter-Regular.ttf) exists in `src/assets/fonts/`
- Verify ffmpeg version (should support ASS subtitles)
- Regenerate golden if intentional style change: delete golden and re-run

### Tests fail with "python-multipart not installed"
- **Root cause**: Importing `src.main` triggers FastAPI app creation, which requires `python-multipart` for file upload routes
- **Solution**: Install in the same Python environment that pytest uses:
  ```bash
  # Check which Python pytest uses
  python3 -m pytest --version
  
  # Install in that environment
  python3 -m pip install python-multipart
  ```
- **Note**: Unit tests now import helpers directly (no app import), but integration tests still need it

### Import errors
- Ensure you're running from `backend/` directory
- Check that `src/` is in Python path (handled by `conftest.py`)

