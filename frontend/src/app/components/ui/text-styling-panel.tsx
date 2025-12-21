import * as React from "react";
import type { Style } from "../../../lib/types";

type TextStylingPanelProps = {
  value: Style;
  onChange: (patch: Partial<Style>) => void;
};

const FONT_OPTIONS = [
  "Inter",
  "Arial",
  "Helvetica",
  "Times New Roman",
  "Courier New",
  "Verdana",
  "Georgia",
];

export function TextStylingPanel({ value, onChange }: TextStylingPanelProps) {
  return (
    <div className="w-80 bg-accent/30 border border-border rounded-lg p-6 space-y-6">
      <h3 className="text-lg font-semibold">Text Styling</h3>

      {/* Font Family */}
      <div className="space-y-2">
        <label className="block text-sm">Font Family</label>
        <select
          value={value.fontFamily}
          onChange={(e) => onChange({ fontFamily: e.target.value })}
          className="w-full px-3 py-2 bg-input-background border border-border rounded-lg"
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
        <label className="block text-sm">Font Size</label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={16}
            max={72}
            value={value.fontSizePx}
            onChange={(e) => onChange({ fontSizePx: Number(e.target.value) })}
            className="flex-1"
          />
          <span className="text-sm text-muted-foreground w-12 text-right">
            {value.fontSizePx}px
          </span>
        </div>
      </div>

      {/* Text Color */}
      <div className="space-y-2">
        <label className="block text-sm">Text Color</label>
        <div className="flex items-center gap-3">
          <input
            type="color"
            value={value.color}
            onChange={(e) => onChange({ color: e.target.value })}
            className="w-12 h-10 rounded border border-border cursor-pointer"
          />
          <input
            type="text"
            value={value.color}
            onChange={(e) => onChange({ color: e.target.value })}
            className="flex-1 px-3 py-2 bg-input-background border border-border rounded-lg"
          />
        </div>
      </div>

      {/* Outline Width */}
      <div className="space-y-2">
        <label className="block text-sm">Outline Width</label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={8}
            value={value.strokePx}
            onChange={(e) => onChange({ strokePx: Number(e.target.value) })}
            className="flex-1"
          />
          <span className="text-sm text-muted-foreground w-12 text-right">
            {value.strokePx}px
          </span>
        </div>
      </div>

      {/* Outline Color */}
      <div className="space-y-2">
        <label className="block text-sm">Outline Color</label>
        <div className="flex items-center gap-3">
          <input
            type="color"
            value={value.outlineColor}
            onChange={(e) => onChange({ outlineColor: e.target.value })}
            className="w-12 h-10 rounded border border-border cursor-pointer"
          />
          <input
            type="text"
            value={value.outlineColor}
            onChange={(e) => onChange({ outlineColor: e.target.value })}
            className="flex-1 px-3 py-2 bg-input-background border border-border rounded-lg"
          />
        </div>
      </div>

      {/* Bold & Italic */}
      <div className="space-y-3">
        <label className="block text-sm">Text Style</label>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => onChange({ bold: !value.bold })}
            className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
              value.bold
                ? "bg-accent border-accent"
                : "bg-card border-border hover:border-primary/20"
            }`}
          >
            Bold
          </button>

          <button
            type="button"
            onClick={() => onChange({ italic: !value.italic })}
            className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
              value.italic
                ? "bg-accent border-accent"
                : "bg-card border-border hover:border-primary/20"
            }`}
          >
            Italic
          </button>
        </div>
      </div>
    </div>
  );
}
