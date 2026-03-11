import { useState } from "react";
import { Card, Badge, Button } from "../../components/ui";
import { DriverFeedbackCard } from "./DriverFeedbackCard";
import { UsageSummaryBar } from "./UsageSummaryBar";
import { UsageDetailModal } from "./UsageDetailModal";
import { TraceModal } from "./TraceModal";
import { useTrace } from "../../hooks/useTrace";
import type {
  RecommendationDetailResponse,
  RecommendationUsageResponse,
} from "../../lib/types";

interface RecommendationCardProps {
  recommendation: RecommendationDetailResponse;
  sessionId: string | null;
  onApply: (recommendationId: string) => void;
  usage?: RecommendationUsageResponse;
}

const CONFIDENCE_VARIANT: Record<string, "success" | "warning" | "info"> = {
  high: "success",
  medium: "warning",
  low: "info",
};

const STATUS_VARIANT: Record<string, "info" | "success" | "neutral"> = {
  proposed: "info",
  applied: "success",
  rejected: "neutral",
};

export function RecommendationCard({
  recommendation,
  sessionId,
  onApply,
  usage,
}: RecommendationCardProps) {
  const isApplied = recommendation.status === "applied";
  const [showUsageModal, setShowUsageModal] = useState(false);
  const [showTraceModal, setShowTraceModal] = useState(false);
  const [explanationExpanded, setExplanationExpanded] = useState(false);
  const traceQuery = useTrace(sessionId, "recommendation", recommendation.recommendation_id);

  return (
    <div
      className={`ace-recommendation-card ace-recommendation-card--${recommendation.status}`}
    >
      <Card variant="ai">
        <div className="ace-recommendation-card__header">
          <span className="ace-recommendation-card__summary">
            {recommendation.summary}
          </span>
          <Badge
            variant={
              CONFIDENCE_VARIANT[recommendation.confidence] ?? "info"
            }
          >
            {recommendation.confidence}
          </Badge>
          <Badge
            variant={STATUS_VARIANT[recommendation.status] ?? "neutral"}
          >
            {recommendation.status === "proposed"
              ? "Proposed"
              : recommendation.status === "applied"
                ? "Applied"
                : "Rejected"}
          </Badge>
        </div>

        {recommendation.explanation !== "" && (
          <div className="ace-recommendation-card__explanation">
            <button
              type="button"
              className="ace-recommendation-card__explanation-toggle"
              onClick={() => setExplanationExpanded(!explanationExpanded)}
              aria-expanded={explanationExpanded}
            >
              {explanationExpanded ? "Hide details" : "Show details"}
            </button>
            {explanationExpanded && (
              <div className="ace-recommendation-card__explanation-content">
                {recommendation.explanation.split("\n\n").map((paragraph, i) => (
                  <p key={i}>{paragraph}</p>
                ))}
              </div>
            )}
          </div>
        )}

        {recommendation.setup_changes.length > 0 && (
          <div className="ace-recommendation-card__changes">
            {recommendation.setup_changes.map((change, i) => (
              <div key={i} className="ace-setup-change">
                <div className="ace-setup-change__header">
                  <span className="ace-setup-change__param">
                    [{change.section}] {change.parameter}
                  </span>
                  <Badge
                    variant={
                      CONFIDENCE_VARIANT[change.confidence] ?? "info"
                    }
                  >
                    {change.confidence}
                  </Badge>
                </div>
                <div className="ace-setup-change__values">
                  {change.old_value}
                  <span className="ace-setup-change__arrow">&rarr;</span>
                  {change.new_value}
                </div>
                <div className="ace-setup-change__reasoning">
                  {change.reasoning}
                </div>
                <div className="ace-setup-change__effect">
                  {change.expected_effect}
                </div>
              </div>
            ))}
          </div>
        )}

        {recommendation.driver_feedback.length > 0 && (
          <div className="ace-recommendation-card__feedback">
            {recommendation.driver_feedback.map((fb, i) => (
              <DriverFeedbackCard key={i} feedback={fb} />
            ))}
          </div>
        )}

        {usage && (
          <UsageSummaryBar
            totals={usage.totals}
            onViewDetails={() => setShowUsageModal(true)}
          />
        )}

        <div className="ace-recommendation-card__actions">
          {traceQuery.data?.available && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTraceModal(true)}
            >
              Trace
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            disabled={isApplied}
            onClick={() => onApply(recommendation.recommendation_id)}
          >
            {isApplied ? "Applied" : "Apply"}
          </Button>
        </div>
      </Card>

      {usage && (
        <UsageDetailModal
          open={showUsageModal}
          onClose={() => setShowUsageModal(false)}
          usage={usage}
        />
      )}

      <TraceModal
        open={showTraceModal}
        onClose={() => setShowTraceModal(false)}
        traceContent={traceQuery.data?.content ?? null}
      />
    </div>
  );
}
