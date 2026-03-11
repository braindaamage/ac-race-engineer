import { Modal } from "../../components/ui";
import { formatTokenCount } from "../../lib/format";
import type { RecommendationUsageResponse } from "../../lib/types";

interface UsageDetailModalProps {
  open: boolean;
  onClose: () => void;
  usage: RecommendationUsageResponse;
}

export function UsageDetailModal({ open, onClose, usage }: UsageDetailModalProps) {
  const { totals, agents } = usage;

  return (
    <Modal open={open} onClose={onClose} title="Usage Details">
      <div className="ace-usage-modal__totals">
        <div className="ace-usage-modal__total-item">
          <span className="ace-usage-modal__total-label">Input</span>
          <span className="ace-usage-modal__total-value ace-mono">
            {formatTokenCount(totals.input_tokens)}
          </span>
        </div>
        <div className="ace-usage-modal__total-item">
          <span className="ace-usage-modal__total-label">Output</span>
          <span className="ace-usage-modal__total-value ace-mono">
            {formatTokenCount(totals.output_tokens)}
          </span>
        </div>
        <div className="ace-usage-modal__total-item">
          <span className="ace-usage-modal__total-label">Tools</span>
          <span className="ace-usage-modal__total-value ace-mono">
            {totals.tool_call_count}
          </span>
        </div>
        <div className="ace-usage-modal__total-item">
          <span className="ace-usage-modal__total-label">Agents</span>
          <span className="ace-usage-modal__total-value ace-mono">
            {totals.agent_count}
          </span>
        </div>
      </div>

      <div className="ace-usage-modal__agents">
        {agents.map((agent) => (
          <div key={agent.domain} className="ace-usage-modal__agent">
            <div className="ace-usage-modal__agent-header">
              <span className="ace-usage-modal__agent-domain">{agent.domain}</span>
            </div>
            <div className="ace-usage-modal__agent-metrics">
              <span className="ace-usage-modal__agent-metric">
                In <span className="ace-mono">{formatTokenCount(agent.input_tokens)}</span>
              </span>
              <span className="ace-usage-modal__agent-metric">
                Out <span className="ace-mono">{formatTokenCount(agent.output_tokens)}</span>
              </span>
              <span className="ace-usage-modal__agent-metric">
                Turns <span className="ace-mono">{agent.turn_count}</span>
              </span>
              <span className="ace-usage-modal__agent-metric">
                Duration <span className="ace-mono">{(agent.duration_ms / 1000).toFixed(1)}s</span>
              </span>
              <span className="ace-usage-modal__agent-metric">
                Tools <span className="ace-mono">{agent.tool_call_count}</span>
              </span>
            </div>
            {(agent.cache_read_tokens > 0 || agent.cache_write_tokens > 0) && (
              <div className="ace-usage-modal__agent-cache">
                {agent.cache_read_tokens > 0 && (
                  <span className="ace-usage-modal__agent-metric">
                    Cache Read <span className="ace-mono">{formatTokenCount(agent.cache_read_tokens)}</span>
                  </span>
                )}
                {agent.cache_write_tokens > 0 && (
                  <span className="ace-usage-modal__agent-metric">
                    Cache Write <span className="ace-mono">{formatTokenCount(agent.cache_write_tokens)}</span>
                  </span>
                )}
              </div>
            )}
            {agent.tool_calls.length > 0 && (
              <div className="ace-usage-modal__tools">
                {agent.tool_calls.map((tc, i) => (
                  <span key={i} className="ace-usage-modal__tool">
                    {tc.tool_name} (<span className="ace-mono">{formatTokenCount(tc.token_count)}</span>)
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </Modal>
  );
}
