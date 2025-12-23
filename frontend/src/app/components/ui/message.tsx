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
  error: "bg-[#f8d7da] border-[#f5c6cb] text-[#721c24]",
  success: "bg-[#d4edda] border-[#c3e6cb] text-[#155724]",
  loading: "bg-accent/30 border-border text-foreground",
  info: "bg-accent/30 border-border text-foreground",
};

export function Message({ type = "info", children, className = "" }: MessageProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border ${typeStyles[type]} ${className}`}
      role="alert"
    >
      <span className="text-sm font-medium">{children}</span>
    </div>
  );
}

