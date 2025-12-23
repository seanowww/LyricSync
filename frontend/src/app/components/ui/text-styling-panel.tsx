import * as React from "react";
import type { Style } from "../../../lib/types";

type TextStylingPanelProps = {
  value: Style;
  onChange: (patch: Partial<Style>) => void;
  /**
   * Optional handler for style presets (default / karaoke / minimal).
   * The parent owns the actual preset behavior so we don't duplicate logic here.
   */
  onPresetChange?: (preset: string) => void;
};

const FONT_OPTIONS = ["Inter", "Arial", "Helvetica", "Times New Roman", "Georgia"];

export function TextStylingPanel({ value, onChange, onPresetChange }: TextStylingPanelProps) {
  return (
    <div className="w-80 rounded-2xl border border-[var(--border)] bg-[var(--panel)] shadow-[var(--shadow)] p-5 space-y-5 text-[var(--text)]">
      {/* Title */}
      <div className="flex items-center justify-between">
        <h3 className="text-[0.8rem] font-medium tracking-[0.16em] uppercase text-[var(--muted)]">
          Text Styling
        </h3>
      </div>

      {/* Preset */}
      <div className="space-y-2">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Preset
        </label>
        <select
          value={value.preset ?? "default"}
          onChange={(e) => onPresetChange?.(e.target.value)}
          className="w-full px-3 py-2 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-xl text-[0.85rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
        >
          <option value="default">Default</option>
          <option value="karaoke">Karaoke</option>
          <option value="minimal">Minimal</option>
        </select>
      </div>

      {/* Font Family */}
      <div className="space-y-2">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Font Family
        </label>
        <select
          value={value.fontFamily}
          onChange={(e) => onChange({ fontFamily: e.target.value })}
          className="w-full px-3 py-2 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-xl text-[0.85rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
        >
          {FONT_OPTIONS.map((font) => (
            <option key={font} value={font}>
              {font}
            </option>
          ))}
        </select>
      </div>

      {/* Font Size */}
      <div className="space-y-2">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Font Size
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={16}
            max={72}
            value={value.fontSizePx}
            onChange={(e) => onChange({ fontSizePx: Number(e.target.value) })}
            className="flex-1 accent-[var(--accent)]"
          />
          <span className="text-[0.8rem] text-[var(--muted)] w-12 text-right font-medium tabular-nums">
            {value.fontSizePx}px
          </span>
        </div>
      </div>

      {/* Text Color */}
      <div className="space-y-2">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Text Color
        </label>
        <div className="flex items-center gap-3">
          <input
            type="color"
            value={value.color}
            onChange={(e) => onChange({ color: e.target.value })}
            className="w-12 h-10 rounded border border-[var(--border)] cursor-pointer bg-[var(--panel2)]"
          />
          <input
            type="text"
            value={value.color}
            onChange={(e) => onChange({ color: e.target.value })}
            className="flex-1 px-3 py-2 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-xl text-[0.85rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
          />
        </div>
      </div>

      {/* Outline Width */}
      <div className="space-y-2">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Outline Width
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={8}
            value={value.strokePx}
            onChange={(e) => onChange({ strokePx: Number(e.target.value) })}
            className="flex-1 accent-[var(--accent)]/70"
          />
          <span className="text-[0.8rem] text-[var(--muted)] w-12 text-right font-medium tabular-nums">
            {value.strokePx}px
          </span>
        </div>
      </div>

      {/* Outline Color */}
      <div className="space-y-2">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Outline Color
        </label>
        <div className="flex items-center gap-3">
          <input
            type="color"
            value={value.strokeColor}
            onChange={(e) => onChange({ strokeColor: e.target.value })}
            className="w-12 h-10 rounded border border-[var(--border)] cursor-pointer bg-[var(--panel2)]"
          />
          <input
            type="text"
            value={value.strokeColor}
            onChange={(e) => onChange({ strokeColor: e.target.value })}
            className="flex-1 px-3 py-2 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-xl text-[0.85rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
          />
        </div>
      </div>

      {/* Bold & Italic */}
      <div className="space-y-3">
        <label className="text-[0.75rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
          Text Style
        </label>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => onChange({ bold: !value.bold })}
            className={`flex-1 rounded-xl border text-[0.85rem] px-3 py-1.5 transition-colors ${
              value.bold
                ? "border-[var(--accent)] bg-[var(--accentSoft)] text-[var(--text)]/90"
                : "border-[color:rgba(255,255,255,0.05)] bg-[var(--panel2)] text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)]"
            }`}
          >
            Bold
          </button>

          <button
            type="button"
            onClick={() => onChange({ italic: !value.italic })}
            className={`flex-1 rounded-xl border text-[0.85rem] px-3 py-1.5 transition-colors ${
              value.italic
                ? "border-[var(--accent)] bg-[var(--accentSoft)] text-[var(--text)]/90"
                : "border-[color:rgba(255,255,255,0.05)] bg-[var(--panel2)] text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)]"
            }`}
          >
            Italic
          </button>
        </div>
      </div>
    </div>
  );
}