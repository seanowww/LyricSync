````markdown
# Lyrically — AI-Assisted Lyric Sync Tool (MVP)

**Lyrically** is an early-stage tool for singers and creators that generates time-aligned lyrics from singing videos using AI.  
Upload a video → get an editable, synced **lyric timeline** you can preview and export.

This is the first MVP focusing on:
- **Automatic transcription**
- **Timing extraction**
- **Synced preview UI**
- **Export of timing data**

> Note: Full video rendering with lyrics burned in is planned for future releases.

---

## What It Does

- Accepts audio/video uploads
- Transcribes vocals using Whisper
- Generates a simple **timing JSON**
- Displays synced lyrics with the video
- Lets users edit text and export timing

---

## Why It Matters

Manual lyric syncing for cover videos is tedious and time-consuming.  
Lyrically reduces hours of manual work to seconds.

---

## MVP Features (Current)

- File upload (web)
- Whisper transcription integration
- Timing JSON generation
- Sync preview of video + lyrics
- Export as `.srt` or JSON

---

## Stack

- **Next.js** (frontend + API)
- **TypeScript**  
- **Whisper (local or API)** for transcription
- **HTML5 `<video>`** for playback sync

---

## How It Works (Simplified)

1. Upload video
2. Backend calls Whisper → returns segments
3. Convert segments → timing JSON
4. Frontend displays synced lyrics with video
5. User can edit and export timing

---

## Timing JSON (Example)

```json
[
  { "id": 1, "start": 3.2, "end": 5.4, "text": "I still remember the 3rd of December" },
  { "id": 2, "start": 5.4, "end": 7.2, "text": "You in your sweater" }
]
````

---

## Roadmap (Next)

* `.srt` → FFmpeg render pipeline
* Style presets and templates
* Drag-and-drop positioning
* Full video export (downloadable)
* Project persistence + accounts

---

## Status

**Early MVP — testing phase.**
Designed to validate core transcription + timing accuracy before building the full lyric video renderer.

---

## Feedback & Contributions

Issues, feedback, and PRs welcome — this is a solo project in active development.

---

## License

MIT

```