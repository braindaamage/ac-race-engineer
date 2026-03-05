import { Button } from "../ui/Button";
import "./SplashScreen.css";

interface SplashScreenProps {
  status: "polling" | "error";
  onRetry: () => void;
}

export function SplashScreen({ status, onRetry }: SplashScreenProps) {
  return (
    <div className="ace-splash">
      <h1 className="ace-splash__title">AC Race Engineer</h1>
      {status === "polling" && (
        <>
          <div className="ace-splash__spinner" />
          <p className="ace-splash__message">Starting backend...</p>
        </>
      )}
      {status === "error" && (
        <>
          <div className="ace-splash__error-icon">!</div>
          <p className="ace-splash__message ace-splash__message--error">
            Backend failed to start
          </p>
          <Button variant="primary" onClick={onRetry}>
            Retry
          </Button>
        </>
      )}
    </div>
  );
}
