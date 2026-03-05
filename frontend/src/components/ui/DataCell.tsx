import "./DataCell.css";

interface DataCellProps {
  value: string | number;
  delta?: number;
  unit?: string;
  align?: "left" | "right";
}

function getDeltaClass(delta: number): string {
  if (delta > 0) return "ace-data-cell__delta--positive";
  if (delta < 0) return "ace-data-cell__delta--negative";
  return "ace-data-cell__delta--neutral";
}

function formatDelta(delta: number): string {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta}`;
}

export function DataCell({ value, delta, unit, align = "left" }: DataCellProps) {
  const classNames = ["ace-data-cell"];
  if (align === "right") {
    classNames.push("ace-data-cell--right");
  }

  return (
    <span className={classNames.join(" ")}>
      <span className="ace-data-cell__value">{value}</span>
      {delta != null && (
        <span className={getDeltaClass(delta)}>{formatDelta(delta)}</span>
      )}
      {unit != null && <span className="ace-data-cell__unit">{unit}</span>}
    </span>
  );
}
