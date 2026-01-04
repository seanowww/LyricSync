---
layout: default
---

# LyricSync.

**AI-assisted lyric timing and subtitle rendering for singing videos**

- Upload a singing video and get automatic, time-aligned lyrics
- Edit lyrics and timing with real-time preview
- Render professional subtitle videos with customizable styling

[GitHub Repository](https://github.com/seanowww/LyricSync)

---

## Demo

### Upload Interface

![Upload Screen](./assets/UploadScreen.png)

**Drag-and-drop video upload with progress tracking.** Supports multiple formats (MP4, MOV, WebM) and provides immediate feedback during upload. The interface validates file types and handles errors gracefully.

### Editor & Preview

![Editor Screen](./assets/EditorScreen.png)

**Real-time synchronized preview with styling controls.** The preview matches the final burned output pixel-perfectly through PlayRes probing via ffprobe—no calibration constants needed. Edit lyrics, adjust timing, and see changes instantly before rendering.

### Styling System

**Full typographic control with deterministic rendering.** Fonts are bundled and referenced via `fontsdir` in FFmpeg, ensuring consistent output across environments. Supports Arial, Georgia, Helvetica, Inter, and Times New Roman with bold/italic variants.

### Export & Rendering

**FFmpeg-based subtitle burning with ASS format.** Segments are converted from JSON to ASS subtitles, then burned into video with precise positioning, opacity, rotation, and stroke controls. Golden snapshot tests ensure style regression safety.

---

## Architecture

<div class="architecture-diagram">
![System Architecture](./assets/architecture.png)
</div>

### Backend Components

- **FastAPI Routes**: RESTful endpoints for transcription, segment management, and video rendering
- **PostgreSQL + SQLAlchemy**: Videos, segments, and styles stored as relational data
- **JSON → ASS Conversion**: Segment data transformed to Advanced SubStation Alpha format
- **FFmpeg Pipeline**: Subtitle burning with font bundling and PlayRes matching

### Frontend Components

- **React + TypeScript**: Type-safe editor-like preview interface
- **Real-time Sync**: Video playback synchronized with lyric timeline
- **Styling Controls**: Live preview of font, color, position, opacity, rotation changes

### Testing Infrastructure

- **Integration Tests**: Full API endpoint coverage with in-memory SQLite
- **Golden Snapshot Tests**: Visual regression testing for rendered video frames
- **Test Isolation**: Per-test database instances for parallel execution

---

## Key Engineering Decisions

**Database as source of truth for segments/styles**  
Segments and styles are stored in PostgreSQL, not filesystem JSON. This ensures consistency, enables concurrent editing, and provides a foundation for future multi-user features.

**UUID identity consistency across API/DB/storage**  
A single UUID is generated per video and used consistently for database records, file paths, and API calls. This eliminates lookup mismatches and ensures data integrity.

**Font bundling + fontsdir with FFmpeg for deterministic renders**  
Fonts are packaged with the application and referenced via `-fontsdir` in FFmpeg commands. This guarantees identical rendering across development, CI, and production environments.

**PlayRes probing via ffprobe to match preview/burn scaling**  
The preview calculates scaling using the same PlayRes values that FFmpeg uses for rendering. This eliminates the need for calibration constants and ensures pixel-perfect preview accuracy.

**Snapshot testing for style regression safety**  
Golden image tests compare rendered video frames against expected outputs. This catches visual regressions in font rendering, positioning, and styling across 28+ style combinations.

**Dependency injection for test database isolation**  
`get_db` is patched at pytest configuration time (before route imports) to use in-memory SQLite. Each test gets a fresh database instance, enabling parallel execution and eliminating test interdependencies.

---

## Local Run

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with DATABASE_URL and OPENAI_API_KEY

# Initialize database
alembic upgrade head

# Run server
uvicorn src.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
pytest  # All tests
pytest tests/integration/test_burn_api.py -v  # Specific suite
```

For detailed setup instructions, see the [main README](https://github.com/seanowww/LyricSync/blob/main/README.md).

---

## What I'd Build Next

**User authentication and multi-user support**  
Replace owner-key system with proper JWT-based auth. Enable users to manage multiple projects and share videos.

**Aspect ratio presets and templates**  
Pre-configured styling templates for common video formats (16:9, 9:16, 1:1) with optimized font sizes and positions.

**Enhanced segment CRUD UX**  
Drag-to-resize timing, bulk edit operations, and keyboard shortcuts for faster lyric editing workflows.

**Render job queue for async processing**  
Move video rendering to background jobs with progress tracking. Support batch rendering of multiple videos.

**Cloud storage integration**  
Replace local filesystem storage with S3/GCS for scalable file handling and CDN delivery of rendered videos.

---

*This documentation site is static; the backend is not deployed. For local development, follow the setup instructions above.*

