// API client for backend endpoints

import type {
  TranscribeResponse,
  SegmentsResponse,
  SegmentsUpdateRequest,
  BurnRequest,
} from "./types";

const API_BASE = "/api";

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

export function getVideoUrl(videoId: string): string {
  return `${API_BASE}/video/${encodeURIComponent(videoId)}`;
}

export async function getSegments(videoId: string): Promise<SegmentsResponse> {
  const response = await fetch(
    `${API_BASE}/segments/${encodeURIComponent(videoId)}`
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
      headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
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

