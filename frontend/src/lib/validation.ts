export interface PathValidationResult {
  status: "valid" | "warning" | "not_found" | "empty";
  message: string;
}

export interface ConnectionTestResult {
  valid: boolean;
  message: string;
}

export interface ConfigResponse {
  ac_install_path: string;
  setups_path: string;
  llm_provider: string;
  llm_model: string;
  ui_theme: string;
  api_key: string;
  onboarding_completed: boolean;
}

export interface ConfigUpdateRequest {
  ac_install_path?: string;
  setups_path?: string;
  llm_provider?: string;
  llm_model?: string;
  ui_theme?: string;
  api_key?: string;
  onboarding_completed?: boolean;
}

export interface ValidatePathRequest {
  path: string;
  path_type: "ac_install" | "setups";
}
