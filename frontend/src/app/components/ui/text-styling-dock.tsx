import * as React from "react";
import type { Style } from "../../../lib/types";

type TextStylingDockProps = {
  value: Style;
  onChange: (patch: Partial<Style>) => void;
  onPresetChange?: (preset: string) => void;
};

const FONT_OPTIONS = ["Inter", "Arial", "Helvetica", "Times New Roman", "Georgia"];

type TabType = "text" | "color" | "stroke" | "rotation" | "preset";

export function TextStylingDock({ value, onChange, onPresetChange }: TextStylingDockProps) {
  const [activeTab, setActiveTab] = React.useState<TabType>("text");

  return (
    <div className="h-full flex flex-col">
      {/* Compact Toolbar */}
      <div className="flex gap-1 mb-2.5 pb-2 border-b border-white/10">
        <button
          type="button"
          onClick={() => setActiveTab("text")}
          className={`flex-1 px-2.5 py-1.5 rounded-md text-[0.7rem] font-medium transition-all ${
            activeTab === "text"
              ? "bg-[var(--accentSoft)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-sm"
              : "text-[var(--muted)]/60 hover:text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)] border border-transparent"
          }`}
          title="Text"
        >
          Aa
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("color")}
          className={`flex-1 px-2.5 py-1.5 rounded-md text-[0.7rem] font-medium transition-all ${
            activeTab === "color"
              ? "bg-[var(--accentSoft)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-sm"
              : "text-[var(--muted)]/60 hover:text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)] border border-transparent"
          }`}
          title="Color"
        >
          ◯
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("stroke")}
          className={`flex-1 px-2.5 py-1.5 rounded-md text-[0.7rem] font-medium transition-all ${
            activeTab === "stroke"
              ? "bg-[var(--accentSoft)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-sm"
              : "text-[var(--muted)]/60 hover:text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)] border border-transparent"
          }`}
          title="Stroke"
        >
          ⬛
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("rotation")}
          className={`flex-1 px-2.5 py-1.5 rounded-md text-[0.7rem] font-medium transition-all border ${
            activeTab === "rotation"
              ? "bg-[var(--accentSoft)] text-[var(--accent)] border-[var(--accent)]/40 shadow-sm"
              : "border-transparent text-[var(--muted)]/60 hover:text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)]"
          }`}
          title="Rotation"
        >
          ↻
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("preset")}
          className={`flex-1 px-2.5 py-1.5 rounded-md text-[0.7rem] font-medium transition-all border ${
            activeTab === "preset"
              ? "bg-[var(--accentSoft)] text-[var(--accent)] border-[var(--accent)]/40 shadow-sm"
              : "border-transparent text-[var(--muted)]/60 hover:text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)]"
          }`}
          title="Preset"
        >
          ★
        </button>
      </div>

      {/* Tab Content - Scrollable */}
      {/* 
        WHY flex-1 + min-h-0: flex-1 makes this take remaining space after tab bar.
        min-h-0 allows it to shrink and enable overflow-auto when content exceeds
        the fixed dock height (240px from parent).
      */}
      <div className="flex-1 min-h-0 overflow-auto">
        <div className="space-y-3 pr-1">
          {/* TEXT Tab */}
          {activeTab === "text" && (
            <>
              <div className="space-y-5.0">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Font Family
                </label>
                <select
                  value={value.fontFamily}
                  onChange={(e) => onChange({ fontFamily: e.target.value })}
                  className="w-full px-2 py-1.5 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-md text-[0.75rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
                >
                  {FONT_OPTIONS.map((font) => (
                    <option key={font} value={font}>
                      {font}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2.5">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Font Size
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={16}
                    max={72}
                    value={value.fontSizePx}
                    onChange={(e) => onChange({ fontSizePx: Number(e.target.value) })}
                    className="flex-1 accent-[var(--accent)]"
                  />
                  <span className="text-[0.7rem] text-[var(--muted)] w-9 text-right font-medium tabular-nums">
                    {value.fontSizePx}px
                  </span>
                </div>
              </div>

              <div className="space-y-2.5">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Style
                </label>
                <div className="pt-2 flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => onChange({ bold: !value.bold })}
                    className={`flex-1 rounded-md border text-[0.7rem] px-2 py-1 transition-colors ${
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
                    className={`flex-1 rounded-md border text-[0.7rem] px-2 py-1 transition-colors ${
                      value.italic
                        ? "border-[var(--accent)] bg-[var(--accentSoft)] text-[var(--text)]/90"
                        : "border-[color:rgba(255,255,255,0.05)] bg-[var(--panel2)] text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)]"
                    }`}
                  >
                    Italic
                  </button>
                </div>
              </div>
            </>
          )}

          {/* COLOR Tab */}
          {activeTab === "color" && (
            <>
              <div className="space-y-2.5">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Text Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={value.color}
                    onChange={(e) => onChange({ color: e.target.value })}
                    className="w-9 h-9 rounded border border-white/10 cursor-pointer bg-[var(--panel2)]"
                  />
                  <input
                    type="text"
                    value={value.color}
                    onChange={(e) => onChange({ color: e.target.value })}
                    className="flex-1 px-2 py-1.5 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-md text-[0.75rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-2.5">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Opacity
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={value.opacity ?? 100}
                    onChange={(e) => onChange({ opacity: Number(e.target.value) })}
                    className="flex-1 accent-[var(--accent)]"
                  />
                  <span className="text-[0.7rem] text-[var(--muted)] w-10 text-right font-medium tabular-nums">
                    {value.opacity ?? 100}%
                  </span>
                </div>
              </div>
            </>
          )}

          {/* STROKE Tab */}
          {activeTab === "stroke" && (
            <>
              <div className="space-y-2.5">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Outline Width
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={0}
                    max={8}
                    value={value.strokePx}
                    onChange={(e) => onChange({ strokePx: Number(e.target.value) })}
                    className="flex-1 accent-[var(--accent)]/70"
                  />
                  <span className="text-[0.7rem] text-[var(--muted)] w-9 text-right font-medium tabular-nums">
                    {value.strokePx}px
                  </span>
                </div>
              </div>

              <div className="space-y-2.5">
                <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                  Outline Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={value.strokeColor}
                    onChange={(e) => onChange({ strokeColor: e.target.value })}
                    className="w-9 h-9 rounded border border-white/10 cursor-pointer bg-[var(--panel2)]"
                  />
                  <input
                    type="text"
                    value={value.strokeColor}
                    onChange={(e) => onChange({ strokeColor: e.target.value })}
                    className="flex-1 px-2 py-1.5 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-md text-[0.75rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
                  />
                </div>
              </div>
            </>
          )}

          {/* ROTATION Tab */}
          {activeTab === "rotation" && (
            <div className="space-y-2.5">
              <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                Rotation Angle
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={0}
                  max={360}
                  value={value.rotation ?? 0}
                  onChange={(e) => onChange({ rotation: Number(e.target.value) })}
                  className="flex-1 accent-[var(--accent)]"
                />
                <span className="text-[0.7rem] text-[var(--muted)] w-12 text-right font-medium tabular-nums">
                  {value.rotation ?? 0}°
                </span>
              </div>
              <button
                type="button"
                onClick={() => onChange({ rotation: 0 })}
                className="w-full px-2 py-1.5 rounded-md border border-[color:rgba(255,255,255,0.05)] bg-[var(--panel2)] text-[0.7rem] text-[var(--muted)] hover:bg-[rgba(255,255,255,0.02)] transition-colors"
              >
                Reset Rotation
              </button>
            </div>
          )}

          {/* PRESET Tab */}
          {activeTab === "preset" && (
            <div className="space-y-2.5">
              <label className="text-[0.7rem] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                Preset
              </label>
              <select
                value={value.preset ?? "default"}
                onChange={(e) => onPresetChange?.(e.target.value)}
                className="w-full px-2 py-1.5 bg-[var(--panel2)] border border-[color:rgba(255,255,255,0.03)] rounded-md text-[0.75rem] text-[var(--text)]/90 focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accentSoft)] transition-colors"
              >
                <option value="default">Default</option>
                <option value="karaoke">Karaoke</option>
                <option value="minimal">Minimal</option>
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

