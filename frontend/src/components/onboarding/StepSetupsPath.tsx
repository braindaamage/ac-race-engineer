import { useEffect, useRef } from "react";
import { PathInput } from "./PathInput";
import { Button } from "../ui";

interface StepSetupsPathProps {
  value: string;
  onChange: (value: string) => void;
  onNext: () => void;
  onBack: () => void;
  acInstallPath: string;
}

export function StepSetupsPath({
  value,
  onChange,
  onNext,
  onBack,
  acInstallPath,
}: StepSetupsPathProps) {
  const prefilled = useRef(false);

  useEffect(() => {
    if (!prefilled.current && !value && acInstallPath) {
      onChange(`${acInstallPath}\\setups`);
      prefilled.current = true;
    }
  }, [acInstallPath, value, onChange]);

  return (
    <div className="ace-onboarding__step">
      <h2 className="ace-onboarding__heading">
        Where are your setup files?
      </h2>
      <p className="ace-onboarding__text">
        This is where your car setup .ini files are stored. We&apos;ll read and
        modify setups here.
      </p>
      <PathInput
        label="Setups Path"
        value={value}
        onChange={onChange}
        pathType="setups"
        placeholder="C:\Program Files\Steam\steamapps\common\assettocorsa\setups"
      />
      <div className="ace-onboarding__nav">
        <Button variant="secondary" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onNext}>Next</Button>
      </div>
    </div>
  );
}
