import { useState } from "react";
import type { SetupParameterDelta } from "../../lib/types";

interface SetupDiffProps {
  changes: SetupParameterDelta[];
  stintAIndex: number;
  stintBIndex: number;
}

function groupBySection(changes: SetupParameterDelta[]): Map<string, SetupParameterDelta[]> {
  const groups = new Map<string, SetupParameterDelta[]>();
  for (const change of changes) {
    const existing = groups.get(change.section);
    if (existing) {
      existing.push(change);
    } else {
      groups.set(change.section, [change]);
    }
  }
  return groups;
}

function getArrow(valueA: number | string, valueB: number | string): string {
  if (typeof valueA === "number" && typeof valueB === "number") {
    if (valueB > valueA) return "\u2191"; // up arrow
    if (valueB < valueA) return "\u2193"; // down arrow
    return "\u2192"; // right arrow (no change)
  }
  return "\u2192"; // right arrow for string changes
}

function formatValue(value: number | string): string {
  if (value === "" || value == null) return "\u2014"; // em dash
  return String(value);
}

export function SetupDiff({ changes, stintAIndex, stintBIndex }: SetupDiffProps) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  if (changes.length === 0) {
    return (
      <div className="ace-metrics-panel">
        <h3>Setup Differences</h3>
        <p className="ace-diff-info">No setup changes between these stints</p>
      </div>
    );
  }

  const grouped = groupBySection(changes);

  const toggleSection = (section: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  return (
    <div className="ace-metrics-panel">
      <h3>Setup Differences</h3>
      <p className="ace-diff-info">Showing changed parameters only</p>
      <div className="ace-diff-row" style={{ fontWeight: 600 }}>
        <span className="ace-diff-row__name">Parameter</span>
        <span className="ace-diff-row__value">Stint {stintAIndex + 1}</span>
        <span className="ace-diff-arrow" />
        <span className="ace-diff-row__value">Stint {stintBIndex + 1}</span>
      </div>
      {Array.from(grouped.entries()).map(([section, params]) => {
        const isSingleValue = params.length === 1 && params[0]!.name === "VALUE";

        if (isSingleValue) {
          const param = params[0]!;
          return (
            <div key={section} className="ace-diff-row">
              <span className="ace-diff-row__name">{section}</span>
              <span className="ace-diff-row__value">
                {formatValue(param.value_a)}
              </span>
              <span className="ace-diff-arrow">
                {getArrow(param.value_a, param.value_b)}
              </span>
              <span className="ace-diff-row__value">
                {formatValue(param.value_b)}
              </span>
            </div>
          );
        }

        return (
          <div key={section} className="ace-diff-section">
            <div
              className="ace-diff-section__header"
              onClick={() => toggleSection(section)}
            >
              <span
                className={`ace-diff-section__toggle${collapsed.has(section) ? " ace-diff-section__toggle--collapsed" : ""}`}
              >
                &#9660;
              </span>
              <span>{section}</span>
            </div>
            {!collapsed.has(section) &&
              params.map((param) => (
                <div key={param.name} className="ace-diff-row">
                  <span className="ace-diff-row__name">{param.name}</span>
                  <span className="ace-diff-row__value">
                    {formatValue(param.value_a)}
                  </span>
                  <span className="ace-diff-arrow">
                    {getArrow(param.value_a, param.value_b)}
                  </span>
                  <span className="ace-diff-row__value">
                    {formatValue(param.value_b)}
                  </span>
                </div>
              ))}
          </div>
        );
      })}
    </div>
  );
}
