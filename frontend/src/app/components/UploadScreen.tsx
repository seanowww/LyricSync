import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { transcribe } from "../../lib/api";
import { setOwnerKey } from "../../lib/auth";
import { Message } from "./ui/message";

export function UploadScreen() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [status, setStatus] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string>("");

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      alert("Please choose a video or audio file first.");
      return;
    }

    setStatus("Uploading and processing...");
    setIsUploading(true);

    try {
      const data = await transcribe(file);
      const videoId = data.video_id;
      const ownerKey = data.owner_key;

      if (!videoId) {
        setStatus("Unexpected response: missing video_id");
        setIsUploading(false);
        return;
      }

      if (!ownerKey) {
        setStatus("Unexpected response: missing owner_key");
        setIsUploading(false);
        return;
      }

      // Store owner key in sessionStorage for future API calls
      // WHY: All subsequent API calls (getSegments, updateSegments, burnVideo, getVideo)
      // require X-Owner-Key header. Storing it here ensures it's available.
      setOwnerKey(ownerKey);

      setStatus("Upload complete. Redirecting to preview...");
      navigate(`/preview?video_id=${encodeURIComponent(videoId)}`);
    } catch (err) {
      setStatus(`Request failed: ${err instanceof Error ? err.message : String(err)}`);
      setIsUploading(false);
    }
  };

  const handleFileChange = (e?: React.ChangeEvent<HTMLInputElement>) => {
    const file = e?.target?.files?.[0] || fileInputRef.current?.files?.[0];
    if (file) {
      setSelectedFileName(file.name);
      setStatus("");
    } else {
      setSelectedFileName("");
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files;
        setSelectedFileName(file.name);
        setStatus("");
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="size-full flex items-center justify-center px-8 py-5 bg-background pt-16">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="mb-4 text-[3.5rem] tracking-[0.18em] uppercase font-semibold text-[var(--text)]">
            <span
              className="relative inline-flex items-center"
              style={{ textShadow: "0 0 18px rgba(109, 90, 230, 0.25)" }}
            >
              <span className="text-[var(--text)]">Lyric</span>
              <span className="text-[var(--text)]/80 ml-0.5">Sync</span>
              <span className="ml-0.5 text-[var(--accent)]">.</span>
            </span>
          </h1>
          <p className="text-secondary max-w-2xl mx-auto opacity-50">
            Time your lyrics perfectly. Create stunning lyric videos with precise subtitle timing.
          </p>
        </div>

        {/* Upload Area */}
        <div
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-[var(--border)] rounded-2xl p-16 text-center cursor-pointer
           bg-[var(--panel)] hover:border-[var(--accent)] hover:bg-[var(--panel2)]
           transition-colors mb-8"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*,video/*"
            onChange={handleFileChange}
            className="hidden"
          />
          <div className="space-y-6">
            <div className="flex justify-center">
              <div className="w-16 h-16 rounded-full bg-[var(--panel2)] text-[var(--accent)]
           flex items-center justify-center shadow-[var(--shadow)]">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
            </div>
            <div>
              <p className="mb-2">Drop your video here or click to browse</p>
              <p className="text-sm text-muted-foreground">
                Supports MP4, MOV, and other common video formats
              </p>
            </div>
          </div>
        </div>

        {/* Selected File Name */}
        {selectedFileName && (
          <div className="text-center mb-4">
            <span className="text-sm text-secondary">
              <span className="font-medium">{selectedFileName}</span>
            </span>
          </div>
        )}

        {/* Upload Button */}
        <div className="flex justify-center">
          <button
            onClick={handleUpload}
            disabled={isUploading || !selectedFileName}
            className="px-8 py-3 rounded-full font-medium
           bg-[var(--accent)] text-white
           hover:bg-[#5a4cd4] transition-colors
           disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? "Uploading..." : "Upload & Transcribe"}
          </button>
        </div>

        {/* Status */}
        {status && (
          <div className="mt-4">
            <Message
              type={
                status.includes("failed") || status.includes("Unexpected")
                  ? "error"
                  : status.includes("Uploading") || status.includes("processing")
                  ? "loading"
                  : status.includes("complete")
                  ? "success"
                  : "info"
              }
            >
              {status}
            </Message>
          </div>
        )}
      </div>
    </div>
  );
}
