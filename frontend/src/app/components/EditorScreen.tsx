import { useState, useRef, useEffect } from "react";
import { LyricSegment } from "../App";

interface EditorScreenProps {
  videoFile: File | null;
  onBack: () => void;
}

export function EditorScreen({ videoFile, onBack }: EditorScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [lyricPosition, setLyricPosition] = useState({ x: 50, y: 80 }); // percentage based
  const [isDragging, setIsDragging] = useState(false);
  const [videoAspectRatio, setVideoAspectRatio] = useState<number | null>(null);

  // Sample lyric segments
  const [segments] = useState<LyricSegment[]>([
    { id: "1", text: "Welcome to the show", startTime: 0, endTime: 2.5 },
    { id: "2", text: "Where dreams come alive", startTime: 2.5, endTime: 5.0 },
    { id: "3", text: "Dancing in the moonlight", startTime: 5.0, endTime: 7.5 },
    { id: "4", text: "Everything feels right", startTime: 7.5, endTime: 10.0 },
    { id: "5", text: "Hearts beating as one", startTime: 10.0, endTime: 12.5 },
    { id: "6", text: "Under the midnight sun", startTime: 12.5, endTime: 15.0 },
  ]);

  useEffect(() => {
    if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      setVideoUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [videoFile]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => setCurrentTime(video.currentTime);
    const handleLoadedMetadata = () => {
      const aspectRatio = video.videoWidth / video.videoHeight;
      setVideoAspectRatio(aspectRatio);
    };

    video.addEventListener("timeupdate", updateTime);
    video.addEventListener("loadedmetadata", handleLoadedMetadata);

    return () => {
      video.removeEventListener("timeupdate", updateTime);
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
    };
  }, []);

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSegmentClick = (segment: LyricSegment) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = segment.startTime;
    }
  };

  const getCurrentSegment = () => {
    return segments.find(
      (seg) => currentTime >= seg.startTime && currentTime < seg.endTime
    );
  };

  const currentSegment = getCurrentSegment();

  const handleMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;

    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    // Clamp values between 0 and 100
    const clampedX = Math.max(0, Math.min(100, x));
    const clampedY = Math.max(0, Math.min(100, y));

    setLyricPosition({ x: clampedX, y: clampedY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      const handleGlobalMouseUp = () => setIsDragging(false);
      window.addEventListener("mouseup", handleGlobalMouseUp);
      return () => window.removeEventListener("mouseup", handleGlobalMouseUp);
    }
  }, [isDragging]);

  // Determine if the video is vertical (9:16 aspect ratio like 1080x1920)
  const isVerticalVideo = videoAspectRatio !== null && videoAspectRatio < 1;

  return (
    <div className="size-full flex flex-col">
      {/* Header */}
      <div className="border-b border-border px-8 py-6 flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-secondary hover:text-primary transition-colors"
        >
          ← Back
        </button>
        <h2 className="absolute left-1/2 -translate-x-1/2">LyricSync.</h2>
        <div className="flex items-center gap-3">
          <button className="px-6 py-2 border border-border rounded-lg hover:bg-muted/50 transition-colors">
            Save
          </button>
          <button className="px-6 py-2 bg-accent-purple hover:bg-accent-purple/80 rounded-lg transition-colors">
            Burn MP4
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-8 py-12">
          {/* Video Preview */}
          <div className="mb-12">
            <div className="flex justify-center">
              <div
                ref={containerRef}
                className="relative bg-card rounded-lg overflow-hidden shadow-sm border border-border"
                style={{
                  width: isVerticalVideo ? "auto" : "100%",
                  maxWidth: isVerticalVideo ? "400px" : "100%",
                  aspectRatio: videoAspectRatio || undefined,
                }}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
              >
                <video
                  ref={videoRef}
                  src={videoUrl}
                  className="w-full h-full object-contain"
                  onClick={handlePlayPause}
                  style={{ display: "block" }}
                />
                {/* Draggable Lyric Overlay */}
                {currentSegment && (
                  <div
                    onMouseDown={handleMouseDown}
                    className="absolute cursor-move pointer-events-auto"
                    style={{
                      left: `${lyricPosition.x}%`,
                      top: `${lyricPosition.y}%`,
                      transform: "translate(-50%, -50%)",
                    }}
                  >
                    <div className="bg-primary/80 px-6 py-3 rounded-lg select-none">
                      <p
                        className="text-white text-center whitespace-nowrap"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {currentSegment.text}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Video Controls */}
            <div className="mt-6 flex items-center justify-center gap-4">
              <button
                onClick={handlePlayPause}
                className="w-12 h-12 rounded-full bg-accent hover:bg-accent/80 flex items-center justify-center transition-colors"
              >
                {isPlaying ? (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <rect x="6" y="4" width="4" height="16" />
                    <rect x="14" y="4" width="4" height="16" />
                  </svg>
                ) : (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                )}
              </button>
            </div>

            {/* Position Info */}
            <div className="mt-4 text-center text-sm text-muted-foreground">
              Drag the lyric text to position it on the video
            </div>
          </div>

          {/* Segment List */}
          <div className="space-y-2">
            <h3 className="mb-6">Lyric Segments</h3>
            <div className="space-y-2">
              {segments.map((segment) => {
                const isActive =
                  currentTime >= segment.startTime &&
                  currentTime < segment.endTime;
                return (
                  <div
                    key={segment.id}
                    onClick={() => handleSegmentClick(segment)}
                    className={`px-6 py-4 rounded-lg border cursor-pointer transition-all ${
                      isActive
                        ? "bg-accent border-accent"
                        : "bg-card border-border hover:border-primary/20"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className={isActive ? "" : "text-secondary"}>
                        {segment.text}
                      </p>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground">
                          {segment.startTime.toFixed(1)}s
                        </span>
                        <span className="text-sm text-muted-foreground">→</span>
                        <span className="text-sm text-muted-foreground">
                          {segment.endTime.toFixed(1)}s
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
