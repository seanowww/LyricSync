# LyricSync — AI-Powered Lyric Video Creator (MVP)

**LyricSync** is a web application that automatically generates time-aligned lyrics from singing videos using AI, then lets you style and position them before burning them directly into your video.

Upload a video → Get AI-transcribed lyrics → Style and position → Export a professional lyric video.

---

## What It Does

- **Automatic transcription** using OpenAI Whisper API
- **Real-time preview** with draggable text overlay synced to video playback
- **Customizable styling**: fonts, colors, sizes, bold/italic, outlines
- **Drag-and-drop positioning** of lyrics on the video
- **Video export** with lyrics burned in using FFmpeg and ASS subtitles

---

## MVP Features

### Core Functionality
- Video/audio file upload (MP4, MOV, etc.)
- Automatic transcription with Whisper API
- Time-aligned lyric segments
- Live preview with synced text overlay
- Editable text and timing
- Drag-to-position lyrics on video
- Text styling panel (font family, size, color, bold, italic, outline)
- Video export with burned-in subtitles (MP4)

### Technical Features
- FastAPI backend with REST API
- React + TypeScript frontend
- ASS subtitle generation
- FFmpeg video processing pipeline
- Comprehensive test suite (unit, integration, golden snapshots)

---

## Stack

### Backend
- **FastAPI** (Python web framework)
- **OpenAI Whisper API** (transcription)
- **FFmpeg** (video processing and subtitle burning)
- **ASS subtitles** (Advanced SubStation Alpha format)
- **Pytest** (testing framework)

### Frontend
- **React 18** + **TypeScript**
- **Vite** (build tool)
- **React Router** (routing)
- **Tailwind CSS** (styling)
- **Radix UI** (component library)

---

## How It Works

1. **Upload**: User uploads a video/audio file
2. **Transcribe**: Backend extracts audio and sends to Whisper API
3. **Generate Segments**: Whisper returns time-aligned text segments
4. **Preview**: Frontend displays video with draggable text overlay
5. **Edit**: User can edit text, timing, styling, and position
6. **Burn**: Backend generates ASS subtitles and burns them into video using FFmpeg
7. **Export**: User downloads the final MP4 with burned-in lyrics

---

## Project Structure

```
LyricSync/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI application
│   │   ├── timing_pipeline.py  # Whisper integration
│   │   ├── schemas.py           # Pydantic models
│   │   ├── utils/
│   │   │   └── ass_helpers.py  # ASS subtitle helpers
│   │   ├── services/
│   │   │   └── segments_store.py  # Segment persistence
│   │   └── assets/
│   │       └── fonts/           # Font files (Inter, Arial, etc.)
│   ├── tests/
│   │   ├── unit/                # Unit tests
│   │   ├── integration/         # Integration tests
│   │   └── assets/
│   │       └── golden/           # Golden snapshot images
│   └── TESTING.md               # Testing documentation
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── App.tsx          # Main app component
    │   │   └── components/
    │   │       ├── UploadScreen.tsx
    │   │       ├── PreviewScreen.tsx
    │   │       └── ui/           # UI components
    │   └── lib/
    │       ├── api.ts            # API client
    │       └── types.ts          # TypeScript types
    └── vite.config.ts           # Vite configuration
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg (for video processing)
- OpenAI API key (for Whisper transcription)

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt  # (if you have one) or:
pip install fastapi uvicorn python-multipart openai python-dotenv pydantic

# Set up environment variables
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the server
uvicorn src.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The app will be available at `http://localhost:5173` (frontend) and `http://localhost:8000` (backend API).

---

## API Endpoints

- `POST /api/transcribe` - Upload video and get transcription
- `GET /api/video/{video_id}` - Get video file
- `GET /api/segments/{video_id}` - Get lyric segments
- `PUT /api/segments/{video_id}` - Update lyric segments
- `POST /api/burn` - Burn subtitles into video and return MP4

---

## Testing

The backend includes a comprehensive test suite:

```bash
cd backend

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests
pytest tests/integration/test_burn_golden.py  # Golden snapshot tests
```

See `backend/TESTING.md` for detailed testing documentation.

---

## Supported Fonts

- Inter (with Bold, Italic, Bold Italic variants)
- Arial (with Bold, Italic, Bold Italic variants)
- Georgia (with Bold, Italic, Bold Italic variants)
- Helvetica (with Bold, Italic, Bold Italic variants)
- Times New Roman (with Bold, Italic, Bold Italic variants)

---

## Example Segment Format

```json
{
  "video_id": "abc123",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "The weather outside is frightful"
    },
    {
      "id": 1,
      "start": 2.5,
      "end": 5.0,
      "text": "But the fire is so delightful"
    }
  ]
}
```

---

## Status

**MVP — Fully Functional**

This MVP includes:
- Complete transcription pipeline
- Interactive preview and editing
- Video export with burned subtitles
- Comprehensive test coverage

Ready for production use with proper API key configuration.

---

## Roadmap (Future Enhancements)

- [ ] Multiple style presets
- [ ] Text animation effects
- [ ] Multi-line text support
- [ ] Project persistence
- [ ] User accounts
- [ ] Batch processing
- [ ] Cloud storage integration

---

## License

MIT

---

## Feedback & Contributions

Issues, feedback, and PRs welcome! This is an active project in development.
