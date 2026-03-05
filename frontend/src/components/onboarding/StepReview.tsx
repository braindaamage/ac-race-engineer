import { useState } from "react";
import { PathInput } from "./PathInput";
import { Card } from "../ui";
import { Button } from "../ui";
import type { PathValidationResult } from "../../lib/validation";

interface StepReviewProps {
  acInstallPath: string;
  setupsPath: string;
  llmProvider: string;
  apiKey: string;
  skippedAiStep: boolean;
  onBack: () => void;
  onFinish: () => void;
  onGoToStep: (step: number) => void;
  isSaving: boolean;
}

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: "Anthropic Claude",
  openai: "OpenAI",
  gemini: "Google Gemini",
};

export function StepReview({
  acInstallPath,
  setupsPath,
  llmProvider,
  apiKey,
  skippedAiStep,
  onBack,
  onFinish,
  onGoToStep,
  isSaving,
}: StepReviewProps) {
  const [acValidation, setAcValidation] = useState<PathValidationResult | null>(null);
  const [setupsValidation, setSetupsValidation] = useState<PathValidationResult | null>(null);

  const hasPathWarning =
    (acValidation && acValidation.status !== "valid" && acValidation.status !== "empty") ||
    (setupsValidation && setupsValidation.status !== "valid" && setupsValidation.status !== "empty");

  return (
    <div className="ace-onboarding__step">
      <h2 className="ace-onboarding__heading">Review your configuration</h2>

      <Card title="Assetto Corsa Path">
        <div className="ace-onboarding__review-row">
          <PathInput
            label=""
            value={acInstallPath}
            onChange={() => {}}
            pathType="ac_install"
            onValidationChange={setAcValidation}
          />
          <button
            className="ace-onboarding__edit-link"
            type="button"
            onClick={() => onGoToStep(1)}
          >
            Edit
          </button>
        </div>
      </Card>

      <Card title="Setups Path">
        <div className="ace-onboarding__review-row">
          <PathInput
            label=""
            value={setupsPath}
            onChange={() => {}}
            pathType="setups"
            onValidationChange={setSetupsValidation}
          />
          <button
            className="ace-onboarding__edit-link"
            type="button"
            onClick={() => onGoToStep(2)}
          >
            Edit
          </button>
        </div>
      </Card>

      <Card title="AI Provider">
        <div className="ace-onboarding__review-row">
          <span>
            {skippedAiStep
              ? "Skipped"
              : `${PROVIDER_LABELS[llmProvider] ?? llmProvider}${apiKey ? " (key set)" : ""}`}
          </span>
          <button
            className="ace-onboarding__edit-link"
            type="button"
            onClick={() => onGoToStep(3)}
          >
            Edit
          </button>
        </div>
        {skippedAiStep && (
          <p className="ace-onboarding__warning">
            ⚠ Engineer feature won&apos;t work without AI configuration.
          </p>
        )}
      </Card>

      {hasPathWarning && (
        <p className="ace-onboarding__warning">
          ⚠ One or more paths have warnings. You can still finish, but some
          features may not work correctly.
        </p>
      )}

      <div className="ace-onboarding__nav">
        <Button variant="secondary" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onFinish} disabled={isSaving}>
          {isSaving ? "Saving..." : "Finish"}
        </Button>
      </div>
    </div>
  );
}
