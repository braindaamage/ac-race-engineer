import { Button } from "../../components/ui";
import { formatTokenCount } from "../../lib/format";
import type { UsageTotals } from "../../lib/types";

interface UsageSummaryBarProps {
  totals: UsageTotals;
  onViewDetails: () => void;
}

export function UsageSummaryBar({ totals, onViewDetails }: UsageSummaryBarProps) {
  return (
    <div className="ace-usage-summary">
      <span className="ace-usage-summary__item">
        <span className="ace-usage-summary__label">Agents</span>
        <span className="ace-mono">{totals.agent_count}</span>
      </span>
      <span className="ace-usage-summary__item">
        <span className="ace-usage-summary__label">In</span>
        <span className="ace-mono">{formatTokenCount(totals.input_tokens)}</span>
      </span>
      <span className="ace-usage-summary__item">
        <span className="ace-usage-summary__label">Out</span>
        <span className="ace-mono">{formatTokenCount(totals.output_tokens)}</span>
      </span>
      <span className="ace-usage-summary__item">
        <span className="ace-usage-summary__label">Tools</span>
        <span className="ace-mono">{totals.tool_call_count}</span>
      </span>
      <Button variant="ghost" size="sm" onClick={onViewDetails}>
        Details
      </Button>
    </div>
  );
}
