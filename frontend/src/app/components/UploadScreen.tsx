import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { transcribe } from "../../lib/api";

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

      if (!videoId) {
        setStatus("Unexpected response: missing video_id");
        setIsUploading(false);
        return;
      }

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
    <div className="size-full flex items-center justify-center px-8 bg-background pt-16">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="mb-4">LyricSync.</h1>
          <p className="text-secondary max-w-md mx-auto">
            Time your lyrics perfectly. Create stunning lyric videos with precise subtitle timing.
          </p>
        </div>

        {/* Upload Area */}
        <div
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-border rounded-lg p-20 text-center cursor-pointer hover:border-primary/20 transition-colors mb-8"
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
              <div className="w-16 h-16 rounded-full bg-accent flex items-center justify-center">
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
            className="px-8 py-3 bg-accent hover:bg-accent/80 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? "Uploading..." : "Upload & Transcribe"}
          </button>
        </div>

        {/* Status */}
        {status && (
          <div className="text-center text-sm text-muted-foreground mt-4">
            {status}
          </div>
        )}
      </div>
    </div>
  );
}
