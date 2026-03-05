import "./ProgressBar.css";

interface ProgressBarProps {
  value: number;
  variant?: "default" | "success" | "error";
}

export function ProgressBar({ value, variant = "default" }: ProgressBarProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className="ace-progress" role="progressbar" aria-valuenow={clampedValue} aria-valuemin={0} aria-valuemax={100}>
      <div
        className={`ace-progress__fill ace-progress__fill--${variant}`}
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
}
