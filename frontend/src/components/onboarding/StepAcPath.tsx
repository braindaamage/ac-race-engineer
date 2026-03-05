import { PathInput } from "./PathInput";
import { Button } from "../ui";

interface StepAcPathProps {
  value: string;
  onChange: (value: string) => void;
  onNext: () => void;
}

export function StepAcPath({ value, onChange, onNext }: StepAcPathProps) {
  return (
    <div className="ace-onboarding__step">
      <h2 className="ace-onboarding__heading">
        Where is Assetto Corsa installed?
      </h2>
      <p className="ace-onboarding__text">
        We need this to find your car data, track information, and recorded
        sessions.
      </p>
      <PathInput
        label="AC Install Path"
        value={value}
        onChange={onChange}
        pathType="ac_install"
        placeholder="C:\Program Files\Steam\steamapps\common\assettocorsa"
      />
      <div className="ace-onboarding__nav">
        <Button onClick={onNext}>Next</Button>
      </div>
    </div>
  );
}
