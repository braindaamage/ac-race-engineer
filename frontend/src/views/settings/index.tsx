import { useState, useEffect, useRef, useCallback } from "react";
import { Card, Button, Modal } from "../../components/ui";
import { PathInput } from "../../components/onboarding/PathInput";
import { OnboardingWizard } from "../../components/onboarding/OnboardingWizard";
import { useConfig } from "../../hooks/useConfig";
import { useTheme } from "../../hooks/useTheme";
import { useNotificationStore } from "../../store/notificationStore";
import { useUIStore } from "../../store/uiStore";
import { apiPost } from "../../lib/api";
import type { ConnectionTestResult } from "../../lib/validation";
import { CarDataSection } from "./CarDataSection";
import "./Settings.css";

export function SettingsView() {
  const { config, updateConfig, isUpdating } = useConfig();
  const { theme, toggleTheme } = useTheme();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const activeSection = useUIStore((s) => s.activeSection);
  const setActiveSection = useUIStore((s) => s.setActiveSection);

  const [acInstallPath, setAcInstallPath] = useState("");
  const [setupsPath, setSetupsPath] = useState("");
  const [llmProvider, setLlmProvider] = useState("anthropic");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [diagnosticMode, setDiagnosticMode] = useState(false);

  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [showDiscardModal, setShowDiscardModal] = useState(false);
  const pendingSection = useRef<string | null>(null);
  const initialized = useRef(false);

  // Initialize form from config (only once when config first loads)
  useEffect(() => {
    if (config && !initialized.current) {
      initialized.current = true;
      setAcInstallPath(config.ac_install_path);
      setSetupsPath(config.setups_path);
      setLlmProvider(config.llm_provider);
      setApiKey("");
      setDiagnosticMode(config.diagnostic_mode ?? false);
    }
  }, [config]);

  const isDirty = config
    ? acInstallPath !== config.ac_install_path ||
      setupsPath !== config.setups_path ||
      llmProvider !== config.llm_provider ||
      apiKey !== "" ||
      diagnosticMode !== (config.diagnostic_mode ?? false)
    : false;

  // Intercept sidebar navigation when dirty
  const prevSection = useRef(activeSection);
  useEffect(() => {
    if (activeSection !== "settings" && prevSection.current === "settings" && isDirty) {
      pendingSection.current = activeSection;
      setActiveSection("settings");
      setShowDiscardModal(true);
    }
    prevSection.current = activeSection;
  }, [activeSection, isDirty, setActiveSection]);

  const handleDiscard = useCallback(() => {
    setShowDiscardModal(false);
    if (config) {
      setAcInstallPath(config.ac_install_path);
      setSetupsPath(config.setups_path);
      setLlmProvider(config.llm_provider);
      setApiKey("");
      setDiagnosticMode(config.diagnostic_mode ?? false);
    }
    if (pendingSection.current) {
      setActiveSection(pendingSection.current);
      pendingSection.current = null;
    }
  }, [config, setActiveSection]);

  const handleSave = async () => {
    const fields: Record<string, string | boolean> = {};
    if (config) {
      if (acInstallPath !== config.ac_install_path) fields.ac_install_path = acInstallPath;
      if (setupsPath !== config.setups_path) fields.setups_path = setupsPath;
      if (llmProvider !== config.llm_provider) fields.llm_provider = llmProvider;
      if (apiKey) fields.api_key = apiKey;
      if (diagnosticMode !== (config.diagnostic_mode ?? false))
        fields.diagnostic_mode = diagnosticMode;
    }
    try {
      await updateConfig(fields);
      setApiKey("");
      initialized.current = false;
      addNotification("success", "Settings saved successfully.");
    } catch {
      addNotification("error", "Failed to save settings.");
    }
  };

  const handleTestConnection = async () => {
    if (!apiKey.trim()) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await apiPost<ConnectionTestResult>(
        "/config/validate-api-key",
        { provider: llmProvider, api_key: apiKey },
      );
      setTestResult(result);
    } catch {
      setTestResult({ valid: false, message: "Failed to test connection." });
    } finally {
      setIsTesting(false);
    }
  };

  if (showWizard) {
    return (
      <OnboardingWizard
        onComplete={() => setShowWizard(false)}
        initialValues={{
          acInstallPath,
          setupsPath,
          llmProvider,
          apiKey,
        }}
      />
    );
  }

  return (
    <div className="ace-settings">
      <h1 className="ace-settings__title">Settings</h1>

      {/* Section 1: Assetto Corsa */}
      <Card title="Assetto Corsa">
        <div className="ace-settings__field">
          <PathInput
            label="AC Install Path"
            value={acInstallPath}
            onChange={setAcInstallPath}
            pathType="ac_install"
          />
        </div>
        <div className="ace-settings__field">
          <PathInput
            label="Setups Path"
            value={setupsPath}
            onChange={setSetupsPath}
            pathType="setups"
          />
        </div>
      </Card>

      {/* Section 2: AI Provider */}
      <Card title="AI Provider">
        <div className="ace-settings__field">
          <label className="ace-settings__label">Provider</label>
          <select
            className="ace-settings__provider-select"
            value={llmProvider}
            onChange={(e) => {
              setLlmProvider(e.target.value);
              setTestResult(null);
            }}
          >
            <option value="anthropic">Anthropic Claude</option>
            <option value="openai">OpenAI</option>
            <option value="gemini">Google Gemini</option>
          </select>
        </div>
        <div className="ace-settings__field">
          <label className="ace-settings__label">
            API Key{config?.api_key ? ` (current: ${config.api_key})` : ""}
          </label>
          <div className="ace-settings__key-row">
            <input
              className="ace-settings__key-input"
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setTestResult(null);
              }}
              placeholder="Enter new API key"
            />
            <Button variant="ghost" size="sm" onClick={() => setShowKey(!showKey)}>
              {showKey ? "Hide" : "Show"}
            </Button>
          </div>
          <div className="ace-settings__test-row">
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
        </div>
      </Card>

      {/* Section 3: Appearance */}
      <Card title="Appearance">
        <div className="ace-settings__row">
          <span>Theme</span>
          <div className="ace-settings__theme-buttons">
            <Button
              variant={theme === "dark" ? "primary" : "secondary"}
              size="sm"
              onClick={() => {
                if (theme !== "dark") toggleTheme();
              }}
            >
              Night Grid
            </Button>
            <Button
              variant={theme === "light" ? "primary" : "secondary"}
              size="sm"
              onClick={() => {
                if (theme !== "light") toggleTheme();
              }}
            >
              Garage Floor
            </Button>
          </div>
        </div>
      </Card>

      {/* Section: Car Data */}
      <CarDataSection />

      {/* Section 4: Advanced */}
      <Card title="Advanced">
        <div className="ace-settings__row">
          <span>Diagnostic Mode</span>
          <div className="ace-settings__theme-buttons">
            <Button
              variant={diagnosticMode ? "primary" : "secondary"}
              size="sm"
              onClick={() => setDiagnosticMode(true)}
            >
              On
            </Button>
            <Button
              variant={!diagnosticMode ? "primary" : "secondary"}
              size="sm"
              onClick={() => setDiagnosticMode(false)}
            >
              Off
            </Button>
          </div>
        </div>
        <p className="ace-settings__hint">
          When enabled, captures full AI agent conversation traces for debugging.
        </p>
        <button
          className="ace-settings__rerun-btn"
          type="button"
          onClick={() => setShowWizard(true)}
        >
          Re-run onboarding wizard
        </button>
      </Card>

      {/* Save button */}
      <div className="ace-settings__footer">
        <Button onClick={handleSave} disabled={!isDirty || isUpdating}>
          {isUpdating ? "Saving..." : "Save"}
        </Button>
      </div>

      {/* Unsaved changes modal */}
      <Modal
        open={showDiscardModal}
        onClose={() => {
          setShowDiscardModal(false);
          pendingSection.current = null;
        }}
        title="Unsaved Changes"
        actions={{
          cancel: {
            label: "Stay",
            onClick: () => {
              setShowDiscardModal(false);
              pendingSection.current = null;
            },
          },
          confirm: {
            label: "Discard",
            onClick: handleDiscard,
            variant: "secondary",
          },
        }}
      >
        <p>You have unsaved changes. Discard them?</p>
      </Modal>
    </div>
  );
}
