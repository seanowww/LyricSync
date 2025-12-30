import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { getVideoUrl, getSegments, updateSegments, burnVideo, downloadBlob } from "../../lib/api";
import type { Segment, Style } from "../../lib/types";
import { TextStylingDock } from "./ui/text-styling-dock";
import { getOwnerKey } from "../../lib/auth";
import { Message } from "./ui/message";

export function PreviewScreen() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const videoId = searchParams.get("video_id");

  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const rafIdRef = useRef<number | null>(null);
  const videoBlobUrlRef = useRef<string | null>(null); // Store blob URL for cleanup

  const [segments, setSegments] = useState<Segment[]>([]);
  const [status, setStatus] = useState<string>("");
  const [isError, setIsError] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isBurning, setIsBurning] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [showToast, setShowToast] = useState(false);

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

  const handleAddLyric = () => {
    setSegments(prev => {
      const lastEnd =
        prev.length === 0
          ? 0
          : Math.max(...prev.map(s => Number(s.end)));
      
      // Calculate next ID: find max existing ID and add 1, or start at 0 if no segments
      // WHY: Database has unique constraint on (video_id, id), so we must ensure IDs are unique
      const existingIds = prev
        .map(s => s.id)
        .filter((id): id is number => typeof id === 'number' && id >= 0);
      const maxId = existingIds.length === 0 ? -1 : Math.max(...existingIds);
      const nextId = maxId + 1;
  
      const sortedSegments = [...prev,
        {
          id: nextId,
          text: "",
          start: lastEnd,
          end: lastEnd + 2,
        },].sort((a,b) => a.start - b.start);

      return sortedSegments;
    });
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

    // Apply font family - use setProperty with important to override any inherited styles
    // This ensures fontFamily changes from TextStylingPanel are immediately visible
    const fontFamily = currentStyle.fontFamily ?? "Inter";
    overlay.style.setProperty("font-family", `${fontFamily}, system-ui, sans-serif`, "important");
    overlay.style.color = currentStyle.color ?? "#FFFFFF";
    overlay.style.fontSize = `${(currentStyle.fontSizePx ?? 28) * scaleX}px`;
    overlay.style.fontWeight = currentStyle.bold ? "700" : "400";
    overlay.style.fontStyle = currentStyle.italic ? "italic" : "normal";

    overlay.style.left = `${posX * scaleX}px`;
    overlay.style.top = `${posY * scaleY}px`;
    overlay.style.transform = "translate(-50%, -100%)";
    overlay.style.textAlign = "center";
    // Remove width constraints to match backend behavior (ASS doesn't wrap)
    // Backend renders text as-is without wrapping, so overlay should match
    overlay.style.width = "auto";
    overlay.style.maxWidth = "none";
    overlay.style.margin = "0 auto";
    overlay.style.whiteSpace = "nowrap";  // Prevent wrapping to match backend ASS behavior
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

  // Load initial data (segments and video)
  useEffect(() => {
    if (!videoId) {
      setStatus("Missing video_id in URL. Go back and upload again.");
      setIsError(true);
      return;
    }

    // Check for owner key
    if (!getOwnerKey()) {
      setStatus("Owner key not found. Please upload a video first.");
      setIsError(true);
      return;
    }

    const loadData = async () => {
      try {
        // Load video URL (async - fetches with X-Owner-Key header and creates blob URL)
        setStatus("Loading video...");
        const videoUrl = await getVideoUrl(videoId);
        videoBlobUrlRef.current = videoUrl; // Store for cleanup
        
        // Update video element src
        if (videoRef.current) {
          videoRef.current.src = videoUrl;
        }

        // Load segments
        setStatus("Loading segments...");
        const data = await getSegments(videoId);
        setSegments(data.segments || []);
        setStatus(`Loaded ${data.segments?.length || 0} segments.`);
      } catch (err) {
        setStatus(`Failed to load: ${err instanceof Error ? err.message : String(err)}`);
        setIsError(true);
      }
    };

    loadData();

    // Cleanup: Revoke blob URL when component unmounts or videoId changes
    return () => {
      if (videoBlobUrlRef.current) {
        URL.revokeObjectURL(videoBlobUrlRef.current);
        videoBlobUrlRef.current = null;
      }
    };
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
  // This ensures fontFamily and other style changes are immediately reflected
  useEffect(() => {
    // Use requestAnimationFrame to ensure DOM is ready
    const rafId = requestAnimationFrame(() => {
      applyOverlayStyle();
      // Double RAF to ensure style is applied after any pending updates
      requestAnimationFrame(applyOverlayStyle);
    });
    return () => cancelAnimationFrame(rafId);
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

  // Toast visibility (non-blocking, overlay)
  useEffect(() => {
    if (!status) {
      setShowToast(false);
      return;
    }
    setShowToast(true);
    const lower = status.toLowerCase();
    const isPersistent =
      isError ||
      lower.includes("loading") ||
      lower.includes("burning") ||
      lower.includes("saving");

    if (!isPersistent) {
      const t = setTimeout(() => setShowToast(false), 2000);
      return () => clearTimeout(t);
    }
  }, [status, isError]);

  // Update segment
  const updateSegment = (index: number, field: keyof Segment, value: string | number) => {
    setSegments((prev) => {
      const newSegs = [...prev];
      newSegs[index] = { ...newSegs[index], [field]: value };
      
      // Auto-sort segments by start time when timing fields are updated
      if (field === "start" || field === "end") {
        newSegs.sort((a, b) => Number(a.start) - Number(b.start));
      }
      
      return newSegs;
    });
  };

  // Delete segment
  const deleteSegment = (index: number) => {
    setSegments((prev) => {
      const newSegs = [...prev];
      newSegs.splice(index, 1);
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
      {/* Header - Back, brand, primary action */}
      <div className="border-b border-[var(--border)] px-8 py-9 flex items-center justify-between bg-[var(--panel2)]">
        <button
          onClick={() => navigate("/")}
          className="text-[var(--muted)] hover:text-[var(--text)] transition-colors px-3 py-1.5 rounded-lg hover:bg-[rgba(255,255,255,0.03)]"
        >
          ← Back
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2 text-[1.8 rem] tracking-[0.18em] uppercase font-semibold text-[var(--text)]">
          <span
            className="relative inline-flex items-center"
            style={{ textShadow: "0 0 22px rgba(109, 90, 230, 0.25)" }}
          >
            <span className="text-[var(--text)]">Lyric</span>
            <span className="text-[var(--text)]/80 ml-0.5">Sync</span>
            <span className="ml-0.5 text-[var(--accent)]">.</span>
          </span>
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={isSaving || isBurning || hasOverlappingSegments}
            className="px-5 py-2 border border-[var(--border)] rounded-full text-sm text-[var(--muted)]
           hover:bg-[rgba(255,255,255,0.03)] hover:border-[var(--border)]
           transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Save
          </button>
          <button
            onClick={handleBurn}
            disabled={isSaving || isBurning || hasOverlappingSegments}
            className="px-6 py-2 rounded-full text-sm font-medium text-white
           bg-[var(--accent)] hover:bg-[#5a4cd4]
           shadow-[var(--shadow)]
           transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Export
          </button>
        </div>
      </div>

      {/* Subtle toast overlay (does not shift layout) */}
      <div className="pointer-events-none fixed top-20 right-10 z-20 flex flex-col items-end gap-2">
        {showToast && status && (
          <div
            className={`flex items-center gap-2 rounded-full border px-3.5 py-2 text-[0.85rem] shadow-sm transition-opacity duration-200
              ${isError ? "border-[var(--danger)] text-[var(--danger)] bg-[var(--panel)]" : "border-[var(--border)] text-[var(--muted)] bg-[var(--panel2)]"}`}
          >
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                isError ? "bg-[var(--danger)]" : "bg-[var(--accent)]/65"
              }`}
            />
            <span className="text-[0.85rem] leading-tight">{status}</span>
          </div>
        )}
      </div>

      {/* Grid Layout: Left video, Right unified sidebar */}
      <div
        className="flex-1 overflow-auto px-8 py-20"
        style={{ minHeight: 0 }}
      >
        <div className="max-w-6xl mx-auto">
          <div className="grid gap-8 items-start" style={{ gridTemplateColumns: "minmax(0, 1fr) 500px" }}>
            {/* Left: Video Container */}
            <div className="min-w-0">
              <div className="relative w-full my-10 flex justify-center">
                <div
                  className="relative rounded-2xl bg-[var(--panel)] p-4 shadow-[var(--shadow)] border border-[var(--border)]"
                  style={{ maxWidth: "420px", width: "100%" }}
                >
                  <video
                    ref={videoRef}
                    controls
                    className="w-full block bg-black rounded-xl"
                  />
                  <div
                    ref={overlayRef}
                    onMouseDown={startDrag}
                    onTouchStart={startDrag}
                    className="absolute left-0 top-0"
                    style={{ padding: "0 16px" }}
                    data-font-family={style.fontFamily ?? "Inter"}
                  />
                </div>
              </div>
            </div>

            {/* Right: Unified Sidebar Panel */}
            {/* 
              WHY min-h-0: In flexbox/grid, flex-1 children can overflow their container.
              min-h-0 allows the flex-1 lyrics container to shrink below its content size,
              enabling overflow-auto to create a scrollbar instead of expanding the parent.
            */}
            <div className = "py-20">
            <aside className="min-w-0 flex flex-col rounded-2xl border border-[var(--border)] bg-[var(--panel)] shadow-[var(--shadow)]">
              {/* Header */}
              <div className="px-6 py-6 border-b border-white/10 flex items-center justify-between flex-shrink-0">
                <h2 className="text-[0.82rem] font-medium uppercase tracking-[0.16em] text-[var(--muted)]">
                  Lyrics
                </h2>
                <span className="text-[0.7rem] text-[var(--muted)]/60 tabular-nums">
                  {segments.length} {segments.length === 1 ? "line" : "lines"}
                </span>
              </div>

              {/* Scrollable Lyrics List */}
              {/* 
                WHY flex-1 + min-h-0: flex-1 makes this take all remaining space.
                min-h-0 ensures it can shrink and trigger overflow-auto scrolling
                when content exceeds available height.
              */}
              <div className="flex-1 min-h-0 overflow-auto px-6 pt-4 pb-1">
                {hasOverlappingSegments && (
                  <div className="mb-3">
                    <Message type="error">
                      Warning: Overlapping segments detected. Please adjust timings before saving or burning.
                    </Message>
                  </div>
                )}
                <div className="space-y-1.5">
                  {segments.map((seg, idx) => {
                    const isActive = currentTime >= Number(seg.start) && currentTime < Number(seg.end);
                    
                    return (
                      <div
                        key={idx}
                        className={`group px-3 py-2 rounded-lg border transition-all cursor-pointer ${
                          isActive
                            ? "bg-[var(--panel2)] border-[var(--accent)]/60 shadow-[0_0_0_1px_rgba(109,90,230,0.2)]"
                            : "bg-transparent border-white/10 hover:border-white/20 hover:bg-[rgba(255,255,255,0.02)]"
                        }`}
                        onClick={() => jumpToSegment(Number(seg.start))}
                      >
                        <div className="flex items-center gap-2.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              jumpToSegment(Number(seg.start));
                            }}
                            className="text-[0.7rem] hover:scale-110 transition-transform flex-shrink-0 text-[var(--muted)]/70 hover:text-[var(--text)]"
                            title="Jump to segment"
                          >
                            ▶
                          </button>
                          <div className="flex-1 min-w-0">
                            <input
                              type="text"
                              value={seg.text ?? ""}
                              onChange={(e) => updateSegment(idx, "text", e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className={`w-full bg-transparent border-none outline-none p-0 text-[0.9rem] tracking-[0.01em] leading-snug transition-colors focus:ring-2 focus:ring-[#4f2d7f2e] rounded ${
                                isActive
                                  ? "text-[var(--text)]/95 font-medium"
                                  : "text-[var(--muted)]/80 font-normal"
                              }`}
                              placeholder="Enter text..."
                            />
                          </div>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <input
                              type="number"
                              step="0.01"
                              value={seg.start === 0 ? "" : (seg.start ?? "")}
                              onChange={(e) => {
                                const val = e.target.value;
                                // If value is empty, set to 0 (will show as placeholder)
                                if (val === "") {
                                  updateSegment(idx, "start", 0);
                                  return;
                                }
                                // Only update if value is valid number
                                const numVal = Number(val);
                                if (!isNaN(numVal) && numVal >= 0) {
                                  updateSegment(idx, "start", numVal);
                                }
                              }}
                              onFocus={(e) => {
                                // When focused and value is 0 (showing as empty), select all so typing replaces it
                                e.target.select();
                              }}
                              onBlur={(e) => {
                                // Format the value when user finishes editing
                                const numVal = Number(e.target.value);
                                if (!isNaN(numVal) && numVal >= 0) {
                                  updateSegment(idx, "start", formatNum(numVal));
                                } else {
                                  // If invalid or empty, reset to 0
                                  updateSegment(idx, "start", 0);
                                }
                              }}
                              onClick={(e) => e.stopPropagation()}
                              className="w-12 px-1.5 py-0.5 text-[0.65rem] tabular-nums text-[var(--muted)]/70 border border-white/10 rounded bg-[var(--panel2)] text-center focus:outline-none focus:ring-1 focus:ring-[#4f2d7f2e] transition-all"
                              placeholder="0"
                            />
                            <span className="text-[0.6rem] text-[var(--muted)]/40">→</span>
                            <input
                              type="number"
                              step="0.01"
                              value={seg.end === 0 ? "" : (seg.end ?? "")}
                              onChange={(e) => {
                                const val = e.target.value;
                                // If value is empty, set to 0 (will show as placeholder)
                                if (val === "") {
                                  updateSegment(idx, "end", 0);
                                  return;
                                }
                                // Only update if value is valid number
                                const numVal = Number(val);
                                if (!isNaN(numVal) && numVal >= 0) {
                                  updateSegment(idx, "end", numVal);
                                }
                              }}
                              onFocus={(e) => {
                                // When focused and value is 0 (showing as empty), select all so typing replaces it
                                e.target.select();
                              }}
                              onBlur={(e) => {
                                // Format the value when user finishes editing
                                const numVal = Number(e.target.value);
                                if (!isNaN(numVal) && numVal >= 0) {
                                  updateSegment(idx, "end", formatNum(numVal));
                                } else {
                                  // If invalid or empty, reset to 0
                                  updateSegment(idx, "end", 0);
                                }
                              }}
                              onClick={(e) => e.stopPropagation()}
                              className="w-12 px-1.5 py-0.5 text-[0.65rem] tabular-nums text-[var(--muted)]/70 border border-white/10 rounded bg-[var(--panel2)] text-center focus:outline-none focus:ring-1 focus:ring-[#4f2d7f2e] transition-all"
                              placeholder="0"
                            />
                          </div>
                          {/* Delete button - appears on hover */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteSegment(idx);
                            }}
                            className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 ml-1 p-1 hover:bg-[rgba(239,68,68,0.1)] rounded transition-colors"
                            title="Delete segment"
                          >
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className="text-[#EF4444]"
                            >
                              <path d="M3 6h18" />
                              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <button
                onClick={handleAddLyric}
                className="
                  flex items-center gap-2
                  px-3 py-2
                  text-sm font-medium
                  text-[var(--muted)]
                  rounded-lg
                  border border-transparent
                  hover:text-[var(--text)]
                  hover:bg-[rgba(255,255,255,0.03)]
                  hover:border-[var(--border)]
                  transition-colors
                  opacity-30
                  disabled:cursor-not-allowed
                "
              >
                <span className="text-base leading-none">+</span>
                <span>Add lyric</span>
              </button>

              {/* Divider - Subtle separator */}
              <div className="border-t border-white/10 flex-shrink-0" />

              {/* Bottom Dock: Fixed height with internal scrolling */}
              {/* 
                WHY fixed height: Dock has a fixed height (200px) so lyrics list
                gets all remaining vertical space. Dock's internal content can scroll
                if controls exceed the fixed height.
              */}
              <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-shrink-0">
                <h2 className="text-[0.82rem] font-medium uppercase tracking-[0.16em] text-[var(--muted)]">
                  Edit
                </h2>
              </div>
              <div className="h-[260px] min-h-[200px] flex-shrink-0 px-6 py-3">
                <TextStylingDock
                  value={style}
                  onChange={(patch) =>
                    setStyle((prev) => ({
                      ...prev,
                      ...patch,
                    }))
                  }
                  onPresetChange={applyPreset}
                />
              </div>
            </aside>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

