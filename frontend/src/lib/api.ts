// API client for backend endpoints

import type {
  TranscribeResponse,
  SegmentsResponse,
  SegmentsUpdateRequest,
  BurnRequest,
} from "./types";
import { getOwnerKey } from "./auth";

const API_BASE = "/api";

/**
 * Build headers for API requests, including X-Owner-Key if available.
 * 
 * WHY: All endpoints (except /transcribe) require X-Owner-Key header.
 * This centralizes header construction.
 */
function buildHeaders(customHeaders: Record<string, string> = {}): HeadersInit {
  const headers: HeadersInit = {
    ...customHeaders,
  };

  // Add X-Owner-Key header if owner key is available
  // WHY: Backend requires this for authorization
  const ownerKey = getOwnerKey();
  if (ownerKey) {
    headers["X-Owner-Key"] = ownerKey;
  }

  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const msg = await response.text().catch(() => response.statusText);
    throw new Error(`Server error (${response.status}): ${msg}`);
  }
  return response.json();
}

export async function transcribe(file: File): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/transcribe`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<TranscribeResponse>(response);
}

/**
 * Get video URL as a blob URL (required because video element can't send custom headers).
 * 
 * WHY: Backend requires X-Owner-Key header, but HTML <video> elements can't send custom headers.
 * Solution: Fetch video with header, create blob URL, return that.
 * 
 * NOTE: Caller should revoke the URL when done using URL.revokeObjectURL(url)
 */
export async function getVideoUrl(videoId: string): Promise<string> {
  const ownerKey = getOwnerKey();
  if (!ownerKey) {
    throw new Error("Owner key not found. Please upload a video first.");
  }

  const response = await fetch(
    `${API_BASE}/video/${encodeURIComponent(videoId)}`,
    {
      headers: buildHeaders(),
    }
  );

  if (!response.ok) {
    const msg = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to load video (${response.status}): ${msg}`);
  }

  // Create blob URL from response
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export async function getSegments(videoId: string): Promise<SegmentsResponse> {
  const response = await fetch(
    `${API_BASE}/segments/${encodeURIComponent(videoId)}`,
    {
      headers: buildHeaders(),
    }
  );
  return handleResponse<SegmentsResponse>(response);
}

export async function updateSegments(
  videoId: string,
  data: SegmentsUpdateRequest
): Promise<SegmentsResponse> {
  const response = await fetch(
    `${API_BASE}/segments/${encodeURIComponent(videoId)}`,
    {
      method: "PUT",
      headers: buildHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(data),
    }
  );
  return handleResponse<SegmentsResponse>(response);
}

export async function burnVideo(
  data: BurnRequest
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/burn`, {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const msg = await response.text().catch(() => response.statusText);
    throw new Error(`Burn failed (${response.status}): ${msg}`);
  }

  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

