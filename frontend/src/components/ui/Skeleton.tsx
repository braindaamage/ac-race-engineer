import "./Skeleton.css";

interface SkeletonProps {
  width?: string;
  height?: string;
  variant?: "text" | "circle" | "rect";
}

export function Skeleton({
  width,
  height,
  variant = "text",
}: SkeletonProps) {
  return (
    <span
      className={`ace-skeleton ace-skeleton--${variant}`}
      style={{ width, height }}
    />
  );
}
