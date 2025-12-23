// ui/message.tsx
/**
 * Standardized message component for error/success/loading states.
 * Uses soft colors for a polished look.
 */
import React from "react";

type MessageType = "error" | "success" | "loading" | "info";

interface MessageProps {
  type?: MessageType;
  children: React.ReactNode;
  className?: string;
}

const typeStyles: Record<MessageType, string> = {
    error: "bg-[var(--panel2)] text-[var(--danger)]",
    success: "bg-[var(--panel2)] text-[var(--success)]",
    loading: "bg-[var(--panel2)] text-[var(--muted)]",
    info: "bg-[var(--panel2)] text-[var(--muted)]",
  };
export function Message({ type = "info", children, className = "" }: MessageProps) {
  return (
    <div
      className={`px-4 py-2.5 rounded-lg text-sm ${typeStyles[type]} ${className}`}
      role="alert"
    >
      <span className="text-sm font-medium">{children}</span>
    </div>
  );
}

