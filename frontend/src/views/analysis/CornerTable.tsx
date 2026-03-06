import { Badge, DataCell, EmptyState } from "../../components/ui";
import type { CornerMetrics } from "../../lib/types";
import { formatSpeed } from "./utils";

interface CornerTableProps {
  primaryCorners: CornerMetrics[];
  primaryLapNumber: number;
  secondaryCorners?: CornerMetrics[];
  secondaryLapNumber?: number;
}

function getBalanceBadge(understeerRatio: number | null) {
  if (understeerRatio == null) {
    return <Badge variant="neutral">N/A</Badge>;
  }
  if (understeerRatio > 0.05) {
    return <Badge variant="warning">Understeer</Badge>;
  }
  if (understeerRatio < -0.05) {
    return <Badge variant="error">Oversteer</Badge>;
  }
  return <Badge variant="neutral">Neutral</Badge>;
}

export function CornerTable({
  primaryCorners,
  secondaryCorners,
}: CornerTableProps) {
  if (primaryCorners.length === 0) {
    return (
      <EmptyState
        icon={<span>&#128739;</span>}
        title="No corners detected"
        description="Corner detection did not find any corners for this lap."
      />
    );
  }

  const hasSecondary = secondaryCorners && secondaryCorners.length > 0;

  // Build a map for secondary corners by number
  const secondaryMap = new Map<number, CornerMetrics>();
  if (secondaryCorners) {
    for (const c of secondaryCorners) {
      secondaryMap.set(c.corner_number, c);
    }
  }

  return (
    <div data-testid="corner-table">
      <table className="ace-corner-table">
        <thead>
          <tr>
            <th>Corner</th>
            <th>Entry</th>
            <th>Apex</th>
            <th>Exit</th>
            <th>Balance</th>
          </tr>
        </thead>
        <tbody>
          {primaryCorners.map((corner) => {
            const sec = secondaryMap.get(corner.corner_number);
            return (
              <tr key={corner.corner_number}>
                <td>{corner.corner_number}</td>
                <td>
                  <DataCell
                    value={formatSpeed(corner.performance.entry_speed_kmh)}
                    delta={
                      sec
                        ? Math.round(
                            (corner.performance.entry_speed_kmh -
                              sec.performance.entry_speed_kmh) *
                              10,
                          ) / 10
                        : undefined
                    }
                  />
                </td>
                <td>
                  <DataCell
                    value={formatSpeed(corner.performance.apex_speed_kmh)}
                    delta={
                      sec
                        ? Math.round(
                            (corner.performance.apex_speed_kmh -
                              sec.performance.apex_speed_kmh) *
                              10,
                          ) / 10
                        : undefined
                    }
                  />
                </td>
                <td>
                  <DataCell
                    value={formatSpeed(corner.performance.exit_speed_kmh)}
                    delta={
                      sec
                        ? Math.round(
                            (corner.performance.exit_speed_kmh -
                              sec.performance.exit_speed_kmh) *
                              10,
                          ) / 10
                        : undefined
                    }
                  />
                </td>
                <td>
                  {getBalanceBadge(corner.grip.understeer_ratio)}
                  {hasSecondary && sec && (
                    <span style={{ marginLeft: 4, opacity: 0.6 }}>
                      {getBalanceBadge(sec.grip.understeer_ratio)}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
          {/* Show secondary-only corners (mismatched count) */}
          {secondaryCorners
            ?.filter(
              (sc) =>
                !primaryCorners.some(
                  (pc) => pc.corner_number === sc.corner_number,
                ),
            )
            .map((sc) => (
              <tr key={`sec-${sc.corner_number}`} style={{ opacity: 0.5 }}>
                <td>{sc.corner_number}</td>
                <td>{formatSpeed(sc.performance.entry_speed_kmh)}</td>
                <td>{formatSpeed(sc.performance.apex_speed_kmh)}</td>
                <td>{formatSpeed(sc.performance.exit_speed_kmh)}</td>
                <td>{getBalanceBadge(sc.grip.understeer_ratio)}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
