import { ProgressBar } from "../../components/ui";

interface AnalysisProgressProps {
  progress: number;
  currentStep: string | null;
}

export function AnalysisProgress({
  progress,
  currentStep,
}: AnalysisProgressProps) {
  return (
    <div className="ace-analysis-progress">
      <ProgressBar value={progress} />
      {currentStep && (
        <div className="ace-analysis-progress__label">{currentStep}</div>
      )}
    </div>
  );
}
