import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { getVideoUrl, getSegments, updateSegments, burnVideo, downloadBlob } from "../../lib/api";
import type { Segment, Style } from "../../lib/types";
import { TextStylingPanel } from "./ui/text-styling-panel";

export function PreviewScreen() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const videoId = searchParams.get("video_id");

  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const rafIdRef = useRef<number | null>(null);

  const [segments, setSegments] = useState<Segment[]>([]);
  const [status, setStatus] = useState<string>("");
  const [isError, setIsError] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isBurning, setIsBurning] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const [style, setStyle] = useState<Style>({
    preset: "default",
    fontFamily: "Inter",
    fontSizePx: 28,
    color: "#FFFFFF",
    strokePx: 3,
    strokeColor: "#000000",
    shadowPx: 0,
    align: "bottom-center",
    posX: null,
    posY: null,
    maxWidthPct: 90,
    outlineSamples: 16,
  });

  const [dragging, setDragging] = useState(false);
  const dragStartRef = useRef<{
    mouseX: number;
    mouseY: number;
    startPosX: number;
    startPosY: number;
    rect: DOMRect;
  } | null>(null);

  // Helper functions
  const formatNum = (n: number): number => {
    return Math.round(n * 100) / 100;
  };

  const clamp = (v: number, min: number, max: number): number => {
    return Math.max(min, Math.min(max, v));
  };

  const hasOverlap = (segs: Segment[]): boolean => {
    const s = [...segs].sort((a, b) => Number(a.start) - Number(b.start));
    for (let i = 1; i < s.length; i++) {
      if (Number(s[i].start) < Number(s[i - 1].end)) return true;
    }
    return false;
  };

  const getActiveCaption = (t: number): string => {
    for (const seg of segments) {
      const start = Number(seg.start);
      const end = Number(seg.end);
      if (t >= start && t < end) return seg.text ?? "";
    }
    return "";
  };

  const hexToRgba = (hex: string, alpha: number = 0.85): string => {
    const c = (hex || "#000000").replace("#", "");
    if (c.length !== 6) return `rgba(0,0,0,${alpha})`;
    const r = parseInt(c.slice(0, 2), 16);
    const g = parseInt(c.slice(2, 4), 16);
    const b = parseInt(c.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  };

  const buildSmoothOutlineShadows = (
    radiusPx: number,
    color: string,
    samples: number = 16
  ): string => {
    const out: string[] = [];
    for (let i = 0; i < samples; i++) {
      const angle = (i / samples) * Math.PI * 2;
      const dx = Math.cos(angle) * radiusPx;
      const dy = Math.sin(angle) * radiusPx;
      out.push(`${dx.toFixed(2)}px ${dy.toFixed(2)}px 0 ${color}`);
    }
    return out.join(", ");
  };

  const ensureDefaultPosition = useCallback(() => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;

    const vw = video.videoWidth;
    const vh = video.videoHeight;

    const defaultX = vw / 2;
    const defaultY = vh * 0.88;

    // Only set if not already set (prevents infinite loop)
    setStyle((prev) => {
      if (prev.posX != null && prev.posY != null) {
        return prev; // Already set, don't update
      }
      return {
        ...prev,
        posX: prev.posX ?? defaultX,
        posY: prev.posY ?? defaultY,
      };
    });
  }, []);

  // Use ref to always read latest style without causing re-renders
  const styleRef = useRef(style);
  useEffect(() => {
    styleRef.current = style;
  }, [style]);

  const applyOverlayStyle = useCallback(() => {
    const video = videoRef.current;
    const overlay = overlayRef.current;
    if (!video || !overlay || !video.videoWidth || !video.videoHeight) return;

    // Read from ref to get latest style without dependency
    const currentStyle = styleRef.current;

    const rect = video.getBoundingClientRect();
    const scaleX = rect.width / video.videoWidth;
    const scaleY = rect.height / video.videoHeight;

    // Use current style position, or fallback to defaults
    const posX = currentStyle.posX ?? video.videoWidth / 2;
    const posY = currentStyle.posY ?? video.videoHeight * 0.88;

    overlay.style.fontFamily = `${currentStyle.fontFamily ?? "Inter"}, system-ui, sans-serif`;
    overlay.style.color = currentStyle.color ?? "#FFFFFF";
    overlay.style.fontSize = `${(currentStyle.fontSizePx ?? 28) * scaleX}px`;
    overlay.style.fontWeight = currentStyle.bold ? "700" : "400";
    overlay.style.fontStyle = currentStyle.italic ? "italic" : "normal";

    overlay.style.left = `${posX * scaleX}px`;
    overlay.style.top = `${posY * scaleY}px`;
    overlay.style.transform = "translate(-50%, -100%)";
    overlay.style.textAlign = "center";
    overlay.style.width = `${currentStyle.maxWidthPct ?? 90}%`;
    overlay.style.maxWidth = `${currentStyle.maxWidthPct ?? 90}%`;
    overlay.style.margin = "0 auto";
    overlay.style.whiteSpace = "pre-wrap";
    overlay.style.lineHeight = "1.15";
    overlay.style.pointerEvents = "auto";
    overlay.style.cursor = dragging ? "grabbing" : "grab";
    overlay.style.userSelect = "none";

    const strokeDisplayPx = Math.max(1, Math.round((currentStyle.strokePx ?? 3) * scaleX));
    const outlineColor = hexToRgba(currentStyle.strokeColor ?? "#000000", 0.90);
    overlay.style.webkitTextStroke = "0px transparent";
    overlay.style.textShadow = buildSmoothOutlineShadows(
      strokeDisplayPx,
      outlineColor,
      currentStyle.outlineSamples ?? 16
    );
  }, [dragging]); // Only depend on dragging, not style

  const applyPreset = (preset: string) => {
    if (preset === "minimal") {
      setStyle((prev) => ({
        ...prev,
        preset: "minimal",
        fontSizePx: 28,
        strokePx: 3,
        shadowPx: 0,
      }));
    } else if (preset === "karaoke") {
      setStyle((prev) => ({
        ...prev,
        preset: "karaoke",
        fontSizePx: 32,
        strokePx: 4,
        shadowPx: 0,
      }));
    } else {
      setStyle((prev) => ({
        ...prev,
        preset: "default",
        fontSizePx: 28,
        strokePx: 3,
        shadowPx: 0,
      }));
    }
  };

  // Dragging handlers
  const startDrag = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;

    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    setDragging(true);

    const rect = video.getBoundingClientRect();

    dragStartRef.current = {
      mouseX: clientX,
      mouseY: clientY,
      startPosX: style.posX ?? video.videoWidth / 2,
      startPosY: style.posY ?? video.videoHeight * 0.88,
      rect,
    };

    if ("preventDefault" in e) {
      e.preventDefault();
    }
  }, [style.posX, style.posY]);

  const onDragMove = useCallback((e: MouseEvent | TouchEvent) => {
    if (!dragging || !dragStartRef.current) return;

    const video = videoRef.current;
    if (!video) return;

    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    const rect = dragStartRef.current.rect;
    const scaleX = rect.width / video.videoWidth;
    const scaleY = rect.height / video.videoHeight;

    const dxDisp = clientX - dragStartRef.current.mouseX;
    const dyDisp = clientY - dragStartRef.current.mouseY;

    const dxVid = dxDisp / scaleX;
    const dyVid = dyDisp / scaleY;

    let nx = dragStartRef.current.startPosX + dxVid;
    let ny = dragStartRef.current.startPosY + dyVid;

    nx = clamp(nx, 0, video.videoWidth);
    ny = clamp(ny, 0, video.videoHeight);

    setStyle((prev) => ({
      ...prev,
      posX: nx,
      posY: ny,
    }));
  }, [dragging]);

  const endDrag = useCallback(() => {
    setDragging(false);
    dragStartRef.current = null;
  }, []);

  // Overlay update loop
  const startOverlayLoop = useCallback(() => {
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
    }

    const tick = () => {
      const video = videoRef.current;
      const overlay = overlayRef.current;
      if (video && overlay) {
        const time = video.currentTime;
        setCurrentTime(time);
        overlay.textContent = getActiveCaption(time);
      }
      rafIdRef.current = requestAnimationFrame(tick);
    };

    rafIdRef.current = requestAnimationFrame(tick);
  }, [segments]);

  // Load initial data
  useEffect(() => {
    if (!videoId) {
      setStatus("Missing video_id in URL. Go back and upload again.");
      setIsError(true);
      return;
    }

    const loadData = async () => {
      try {
        setStatus("Loading segments...");
        const data = await getSegments(videoId);
        setSegments(data.segments || []);
        setStatus(`Loaded ${data.segments?.length || 0} segments.`);
      } catch (err) {
        setStatus(`Failed to load segments: ${err instanceof Error ? err.message : String(err)}`);
        setIsError(true);
      }
    };

    loadData();
  }, [videoId]);

  // Video metadata loaded - set default position once
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedMetadata = () => {
      // Set default position only if not already set
      if (style.posX == null || style.posY == null) {
        const defaultX = video.videoWidth / 2;
        const defaultY = video.videoHeight * 0.88;
        setStyle((prev) => ({
          ...prev,
          posX: prev.posX ?? defaultX,
          posY: prev.posY ?? defaultY,
        }));
      }
      applyOverlayStyle();
      requestAnimationFrame(applyOverlayStyle);
      startOverlayLoop();
    };

    video.addEventListener("loadedmetadata", handleLoadedMetadata);
    return () => {
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
    };
  }, [style.posX, style.posY, applyOverlayStyle, startOverlayLoop]);

  // Restart overlay loop when segments change
  useEffect(() => {
    const video = videoRef.current;
    if (video && video.readyState >= 2) {
      // Video metadata is loaded, restart the loop
      startOverlayLoop();
    }
  }, [segments, startOverlayLoop]);

  // Apply overlay style when style changes (using ref to avoid dependency loop)
  useEffect(() => {
    applyOverlayStyle();
    requestAnimationFrame(applyOverlayStyle);
  }, [style, applyOverlayStyle]);

  // Apply overlay style on window resize
  useEffect(() => {
    const handleResize = () => {
      applyOverlayStyle();
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [applyOverlayStyle]);

  // Global drag handlers
  useEffect(() => {
    if (dragging) {
      const handleMove = (e: MouseEvent | TouchEvent) => onDragMove(e);
      const handleEnd = () => endDrag();

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleEnd);
      window.addEventListener("touchmove", handleMove, { passive: true });
      window.addEventListener("touchend", handleEnd);

      return () => {
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleEnd);
        window.removeEventListener("touchmove", handleMove);
        window.removeEventListener("touchend", handleEnd);
      };
    }
  }, [dragging, onDragMove, endDrag]);

  // Cleanup animation frame
  useEffect(() => {
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  // Save segments
  const handleSave = async (): Promise<boolean> => {
    if (!videoId) return false;

    setStatus("Saving...");
    setIsSaving(true);
    setIsError(false);

    if (hasOverlap(segments)) {
      setStatus("Save failed: overlapping segments not supported yet. Adjust timings so they don't overlap.");
      setIsError(true);
      setIsSaving(false);
      return false;
    }

    try {
      await updateSegments(videoId, { segments });
      setStatus("Saved ✅");
      return true;
    } catch (err) {
      setStatus(`Save failed: ${err instanceof Error ? err.message : String(err)}`);
      setIsError(true);
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  // Burn video
  const handleBurn = async () => {
    if (!videoId) return;

    const ok = await handleSave();
    if (!ok) return;

    setStatus("Burning subtitles (this may take a bit)...");
    setIsBurning(true);

    try {
      const blob = await burnVideo({
        video_id: videoId,
        segments,
        style,
      });

      downloadBlob(blob, `lyricsync_${videoId}.mp4`);
      setStatus("Burn complete ✅ Download started.");
    } catch (err) {
      setStatus(`Burn failed: ${err instanceof Error ? err.message : String(err)}`);
      setIsError(true);
    } finally {
      setIsBurning(false);
    }
  };

  // Update segment
  const updateSegment = (index: number, field: keyof Segment, value: string | number) => {
    setSegments((prev) => {
      const newSegs = [...prev];
      newSegs[index] = { ...newSegs[index], [field]: value };
      return newSegs;
    });
  };

  // Jump to segment
  const jumpToSegment = (start: number) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = Math.max(0, start);
      video.play().catch(() => {});
    }
  };

  if (!videoId) {
    return (
      <div className="size-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Missing video_id in URL. Go back and upload again.</p>
        </div>
      </div>
    );
  }

  const hasOverlappingSegments = hasOverlap(segments);

  return (
    <div className="size-full flex flex-col bg-background">
      {/* Header - Match Figma: Back button left, Title center, Save/Burn buttons right */}
      <div className="border-b border-border px-8 py-6 flex items-center justify-between">
        <button
          onClick={() => navigate("/")}
          className="text-secondary hover:text-primary transition-colors"
        >
          ← Back
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2">LyricSync.</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={isSaving || isBurning || hasOverlappingSegments}
            className="px-6 py-2 border border-border rounded-lg hover:bg-muted/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save
          </button>
          <button
            onClick={handleBurn}
            disabled={isSaving || isBurning || hasOverlappingSegments}
            className="px-6 py-2 bg-accent-purple hover:bg-accent-purple/80 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Burn MP4
          </button>
        </div>
      </div>

      {/* Controls Bar */}
      <div className="px-8 py-4 border-b border-border flex items-center gap-4 flex-wrap">
        <label className="flex items-center gap-2">
          Style:
          <select
            value={style.preset}
            onChange={(e) => {
              applyPreset(e.target.value);
            }}
            className="px-3 py-1 border border-border rounded"
          >
            <option value="default">default</option>
            <option value="karaoke">karaoke</option>
            <option value="minimal">minimal</option>
          </select>
        </label>

        <div className="flex-1" />

        <span className="text-xs text-muted-foreground">
          {style.posX != null && style.posY != null
            ? `pos=(${style.posX.toFixed(0)},${style.posY.toFixed(0)})`
            : ""}
          {videoRef.current?.videoWidth &&
            videoRef.current?.videoHeight &&
            `  video=${videoRef.current.videoWidth}×${videoRef.current.videoHeight}`}
        </span>
      </div>

      {/* Status */}
      {status && (
        <div className={`px-8 py-2 ${isError ? "text-red-600" : "text-foreground"}`}>
          {status}
        </div>
      )}

      {/* Video and Segments */}
      <div className="flex-1 overflow-auto px-8 py-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex gap-8 items-start">
            {/* Left: Video Container */}
            <div className="flex-1">
              <div className="relative w-full mb-8 flex justify-center">
                <div className="relative" style={{ maxWidth: "600px", width: "100%" }}>
                  <video
                    ref={videoRef}
                    src={getVideoUrl(videoId)}
                    controls
                    className="w-full block bg-black rounded-lg"
                  />
                  <div
                    ref={overlayRef}
                    onMouseDown={startDrag}
                    onTouchStart={startDrag}
                    className="absolute left-0 top-0"
                    style={{ padding: "0 16px" }}
                  />
                </div>
              </div>
            </div>

            {/* Right: Text Styling Panel */}
            <div className="flex-shrink-0">
              <TextStylingPanel
                value={style}
                onChange={(patch) =>
                  setStyle((prev) => ({
                    ...prev,
                    ...patch,
                  }))
                }
              />
            </div>
          </div>

          {/* Segments - Card-based display matching Figma */}
          <div className="mt-8">
            <h2 className="mb-4">Segments</h2>
            {hasOverlappingSegments && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-400 rounded text-yellow-800 text-sm">
                Warning: Overlapping segments detected. Please adjust timings before saving or burning.
              </div>
            )}
            <div className="space-y-2">
              {segments.map((seg, idx) => {
                const isActive = currentTime >= Number(seg.start) && currentTime < Number(seg.end);
                
                return (
                  <div
                    key={idx}
                    className={`px-6 py-4 rounded-lg border transition-all ${
                      isActive
                        ? "bg-accent border-accent"
                        : "bg-card border-border hover:border-primary/20"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => jumpToSegment(Number(seg.start))}
                        className="text-sm hover:scale-110 transition-transform flex-shrink-0"
                        title="Jump to segment"
                      >
                        ▶
                      </button>
                      <div className="flex-1 min-w-0">
                        <input
                          type="text"
                          value={seg.text ?? ""}
                          onChange={(e) => updateSegment(idx, "text", e.target.value)}
                          className={`w-full bg-transparent border-none outline-none p-0 text-base ${
                            isActive ? "text-foreground font-medium" : "text-secondary"
                          }`}
                          placeholder="Enter text..."
                        />
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <input
                          type="number"
                          step="0.01"
                          value={formatNum(Number(seg.start))}
                          onChange={(e) => updateSegment(idx, "start", Number(e.target.value))}
                          className="w-16 px-2 py-1 text-xs border border-border rounded bg-background text-center"
                          placeholder="0"
                        />
                        <span className="text-xs text-muted-foreground">→</span>
                        <input
                          type="number"
                          step="0.01"
                          value={formatNum(Number(seg.end))}
                          onChange={(e) => updateSegment(idx, "end", Number(e.target.value))}
                          className="w-16 px-2 py-1 text-xs border border-border rounded bg-background text-center"
                          placeholder="0"
                        />
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

