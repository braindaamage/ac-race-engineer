import type { ReactNode } from "react";
import "./Badge.css";

interface BadgeProps {
  variant: "info" | "success" | "warning" | "error" | "neutral";
  children: ReactNode;
}

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span className={`ace-badge ace-badge--${variant}`}>{children}</span>
  );
}
