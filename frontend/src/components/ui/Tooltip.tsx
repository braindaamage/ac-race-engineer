import { useState, useRef, useCallback, type ReactNode } from "react";
import "./Tooltip.css";

interface TooltipProps {
  content: string;
  position?: "top" | "bottom" | "left" | "right";
  children: ReactNode;
}

export function Tooltip({
  content,
  position = "top",
  children,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = useCallback(() => {
    timerRef.current = setTimeout(() => {
      setVisible(true);
    }, 200);
  }, []);

  const handleMouseLeave = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setVisible(false);
  }, []);

  return (
    <div
      className="ace-tooltip-wrapper"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {visible && (
        <span className={`ace-tooltip ace-tooltip--${position}`}>
          {content}
        </span>
      )}
    </div>
  );
}
