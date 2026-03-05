import { useState } from "react";
import { apiPost } from "../../lib/api";
import { Button } from "../ui";
import type { ConnectionTestResult } from "../../lib/validation";

interface StepAiProviderProps {
  provider: string;
  onProviderChange: (provider: string) => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

const PROVIDERS = [
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Google Gemini" },
];

export function StepAiProvider({
  provider,
  onProviderChange,
  apiKey,
  onApiKeyChange,
  onNext,
  onBack,
  onSkip,
}: StepAiProviderProps) {
  const [showKey, setShowKey] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const handleTestConnection = async () => {
    if (!apiKey.trim()) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await apiPost<ConnectionTestResult>(
        "/config/validate-api-key",
        { provider, api_key: apiKey },
      );
      setTestResult(result);
    } catch {
      setTestResult({ valid: false, message: "Failed to test connection." });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="ace-onboarding__step">
      <h2 className="ace-onboarding__heading">Connect an AI provider</h2>
      <p className="ace-onboarding__text">
        The Race Engineer uses AI to analyze your driving and suggest setup
        changes. You&apos;ll need an API key from one of these providers.
      </p>

      <div className="ace-path-input">
        <label className="ace-path-input__label">Provider</label>
        <select
          className="ace-path-input__field"
          value={provider}
          onChange={(e) => {
            onProviderChange(e.target.value);
            setTestResult(null);
          }}
        >
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div className="ace-path-input">
        <label className="ace-path-input__label">API Key</label>
        <div className="ace-path-input__row">
          <input
            className="ace-path-input__field"
            type={showKey ? "text" : "password"}
            value={apiKey}
            onChange={(e) => {
              onApiKeyChange(e.target.value);
              setTestResult(null);
            }}
            placeholder="Enter your API key"
          />
          <button
            className="ace-path-input__browse"
            type="button"
            onClick={() => setShowKey(!showKey)}
          >
            {showKey ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleTestConnection}
          disabled={!apiKey.trim() || isTesting}
        >
          {isTesting ? "Testing..." : "Test Connection"}
        </Button>
        {testResult && (
          <span
            className={
              testResult.valid
                ? "ace-path-input__status ace-path-input__status--valid"
                : "ace-path-input__status ace-path-input__status--not_found"
            }
          >
            {testResult.valid ? "✓ " : "✗ "}
            {testResult.message}
          </span>
        )}
      </div>

      <div className="ace-onboarding__nav">
        <button
          className="ace-onboarding__skip-btn"
          type="button"
          onClick={onSkip}
        >
          Skip for now
        </button>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button variant="secondary" onClick={onBack}>
            Back
          </Button>
          <Button onClick={onNext}>Next</Button>
        </div>
      </div>
    </div>
  );
}
