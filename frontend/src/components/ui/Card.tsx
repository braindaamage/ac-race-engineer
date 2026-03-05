import type { ReactNode } from "react";
import "./Card.css";

interface CardProps {
  variant?: "default" | "ai";
  children: ReactNode;
  title?: string;
  padding?: "sm" | "md" | "lg";
}

export function Card({
  variant = "default",
  children,
  title,
  padding = "md",
}: CardProps) {
  const classNames = ["ace-card", `ace-card--padding-${padding}`];

  if (variant === "ai") {
    classNames.push("ace-card--ai");
  }

  return (
    <div className={classNames.join(" ")}>
      {title != null && <h3 className="ace-card__title">{title}</h3>}
      {children}
    </div>
  );
}
