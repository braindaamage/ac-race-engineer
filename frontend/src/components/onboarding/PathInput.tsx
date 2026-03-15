import { useState, useEffect, useRef, useCallback } from "react";
import { apiPost } from "../../lib/api";
import type { PathValidationResult, ValidatePathRequest } from "../../lib/validation";
import "./OnboardingWizard.css";

interface PathInputProps {
  label: string;
  value: string;
  onChange: (path: string) => void;
  pathType: "ac_install" | "setups";
  placeholder?: string;
  helpText?: string;
  onValidationChange?: (result: PathValidationResult | null) => void;
}

export function PathInput({
  label,
  value,
  onChange,
  pathType,
  placeholder,
  helpText,
  onValidationChange,
}: PathInputProps) {
  const [validation, setValidation] = useState<PathValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isTauri = typeof window !== "undefined" && "__TAURI__" in window;

  const validate = useCallback(
    async (path: string) => {
      if (!path.trim()) {
        setValidation(null);
        onValidationChange?.(null);
        return;
      }
      setIsValidating(true);
      try {
        const result = await apiPost<PathValidationResult>("/config/validate-path", {
          path,
          path_type: pathType,
        } satisfies ValidatePathRequest);
        setValidation(result);
        onValidationChange?.(result);
      } catch {
        setValidation(null);
        onValidationChange?.(null);
      } finally {
        setIsValidating(false);
      }
    },
    [pathType, onValidationChange],
  );

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      validate(value);
    }, 500);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, validate]);

  const handleBrowse = async () => {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({ directory: true });
      if (selected) {
        onChange(selected);
      }
    } catch {
      // Dialog not available
    }
  };

  const statusClass = validation
    ? `ace-path-input__status--${validation.status}`
    : "";

  return (
    <div className="ace-path-input">
      <label className="ace-path-input__label">{label}</label>
      {helpText && <p className="ace-path-input__help">{helpText}</p>}
      <div className="ace-path-input__row">
        <input
          className="ace-path-input__field"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
        {isTauri && (
          <button
            className="ace-path-input__browse"
            type="button"
            onClick={handleBrowse}
          >
            Browse
          </button>
        )}
      </div>
      {isValidating && (
        <p className="ace-path-input__status ace-path-input__status--validating">
          Validating...
        </p>
      )}
      {!isValidating && validation && (
        <p className={`ace-path-input__status ${statusClass}`}>
          {validation.status === "valid" && "✓ "}
          {validation.status === "warning" && <><i className="fa-solid fa-triangle-exclamation" />{" "}</>}
          {validation.status === "not_found" && "✗ "}
          {validation.message}
        </p>
      )}
    </div>
  );
}
