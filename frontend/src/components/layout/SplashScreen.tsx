import { Button } from "../ui/Button";
import logoSrc from "../../assets/logo.png";
import "./SplashScreen.css";

interface SplashScreenProps {
  status: "polling" | "error";
  onRetry: () => void;
}

export function SplashScreen({ status, onRetry }: SplashScreenProps) {
  return (
    <div className="ace-splash">
      <img src={logoSrc} alt="AC Race Engineer" className="ace-splash__logo" />
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
