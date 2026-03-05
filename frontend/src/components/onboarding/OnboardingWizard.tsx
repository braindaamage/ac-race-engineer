import { useState } from "react";
import { StepAcPath } from "./StepAcPath";
import { StepSetupsPath } from "./StepSetupsPath";
import { StepAiProvider } from "./StepAiProvider";
import { StepReview } from "./StepReview";
import { useConfig } from "../../hooks/useConfig";
import "./OnboardingWizard.css";

interface OnboardingWizardProps {
  onComplete: () => void;
  initialValues?: {
    acInstallPath?: string;
    setupsPath?: string;
    llmProvider?: string;
    apiKey?: string;
  };
}

export function OnboardingWizard({ onComplete, initialValues }: OnboardingWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [acInstallPath, setAcInstallPath] = useState(initialValues?.acInstallPath ?? "");
  const [setupsPath, setSetupsPath] = useState(initialValues?.setupsPath ?? "");
  const [llmProvider, setLlmProvider] = useState(initialValues?.llmProvider ?? "anthropic");
  const [apiKey, setApiKey] = useState(initialValues?.apiKey ?? "");
  const [skippedAiStep, setSkippedAiStep] = useState(false);
  const { updateConfig, isUpdating } = useConfig();

  const goToStep = (s: number) => {
    if (s >= 1 && s <= 4) setStep(s as 1 | 2 | 3 | 4);
  };

  const handleFinish = async () => {
    try {
      await updateConfig({
        ac_install_path: acInstallPath || undefined,
        setups_path: setupsPath || undefined,
        llm_provider: llmProvider,
        api_key: apiKey || undefined,
        onboarding_completed: true,
      });
      onComplete();
    } catch {
      // Error handled by TanStack Query
    }
  };

  const totalSteps = 4;

  return (
    <div className="ace-onboarding">
      <div className="ace-onboarding__container">
        <div className="ace-onboarding__progress">
          {Array.from({ length: totalSteps }, (_, i) => (
            <div
              key={i}
              className={`ace-onboarding__progress-dot${
                i + 1 <= step ? " ace-onboarding__progress-dot--active" : ""
              }`}
            />
          ))}
        </div>
        <p className="ace-onboarding__step-label">
          Step {step} of {totalSteps}
        </p>

        {step === 1 && (
          <StepAcPath
            value={acInstallPath}
            onChange={setAcInstallPath}
            onNext={() => setStep(2)}
          />
        )}

        {step === 2 && (
          <StepSetupsPath
            value={setupsPath}
            onChange={setSetupsPath}
            onNext={() => setStep(3)}
            onBack={() => setStep(1)}
            acInstallPath={acInstallPath}
          />
        )}

        {step === 3 && (
          <StepAiProvider
            provider={llmProvider}
            onProviderChange={setLlmProvider}
            apiKey={apiKey}
            onApiKeyChange={setApiKey}
            onNext={() => setStep(4)}
            onBack={() => setStep(2)}
            onSkip={() => {
              setSkippedAiStep(true);
              setStep(4);
            }}
          />
        )}

        {step === 4 && (
          <StepReview
            acInstallPath={acInstallPath}
            setupsPath={setupsPath}
            llmProvider={llmProvider}
            apiKey={apiKey}
            skippedAiStep={skippedAiStep}
            onBack={() => setStep(3)}
            onFinish={handleFinish}
            onGoToStep={goToStep}
            isSaving={isUpdating}
          />
        )}
      </div>
    </div>
  );
}
