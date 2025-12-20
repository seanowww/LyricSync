// Types matching backend schemas

export interface Segment {
  id?: number;
  start: number;
  end: number;
  text: string;
}

export interface Style {
  preset?: string;
  fontFamily?: string;
  fontSizePx?: number;
  color?: string;
  strokePx?: number;
  strokeColor?: string;
  shadowPx?: number;
  align?: string;
  posX?: number | null;
  posY?: number | null;
  maxWidthPct?: number;
  outlineSamples?: number;
}

export interface TranscribeResponse {
  video_id: string;
  segments: Segment[];
}

export interface SegmentsResponse {
  video_id: string;
  segments: Segment[];
}

export interface SegmentsUpdateRequest {
  segments: Segment[];
}

export interface BurnRequest {
  video_id: string;
  segments: Segment[];
  style?: Style | null;
}

