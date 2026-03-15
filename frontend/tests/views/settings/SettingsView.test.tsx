import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, fireEvent, waitFor, act } from "@testing-library/react";
import { SettingsView } from "../../../src/views/settings";
import { renderWithRouter } from "../../helpers/renderWithRouter";

// Mock api
vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
  apiPost: vi.fn(),
}));

// Mock useTheme
vi.mock("../../../src/hooks/useTheme", () => ({
  useTheme: () => ({ theme: "dark", toggleTheme: vi.fn() }),
}));

import { apiGet, apiPatch, apiPost } from "../../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPatch = vi.mocked(apiPatch);
const mockedApiPost = vi.mocked(apiPost);

const defaultConfig = {
  ac_install_path: "C:\\Games\\AC",
  setups_path: "C:\\Games\\AC\\setups",
  llm_provider: "anthropic",
  llm_model: "",
  ui_theme: "dark",
  api_key: "sk-a****7890",
  onboarding_completed: true,
  diagnostic_mode: false,
};

function renderSettings() {
  return renderWithRouter(<SettingsView />, {
    path: "/settings",
    route: "/settings",
  });
}

describe("SettingsView", () => {
  beforeEach(() => {
    mockedApiGet.mockResolvedValue(defaultConfig);
    mockedApiPatch.mockResolvedValue(defaultConfig);
    mockedApiPost.mockResolvedValue({ status: "valid", message: "OK" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders all 4 sections", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Settings")).toBeDefined();
      expect(screen.getByText("Assetto Corsa")).toBeDefined();
      expect(screen.getByText("AI Provider")).toBeDefined();
      expect(screen.getByText("Appearance")).toBeDefined();
      expect(screen.getByText("Advanced")).toBeDefined();
    });
  });

  it("populates form with config values", async () => {
    renderSettings();

    await waitFor(() => {
      const inputs = screen.getAllByRole("textbox");
      // AC path and setups path should be present
      const acInput = inputs.find(
        (i) => (i as HTMLInputElement).value === "C:\\Games\\AC",
      );
      expect(acInput).toBeDefined();
    });
  });

  it("Save button is disabled when not dirty", async () => {
    renderSettings();

    await waitFor(() => {
      const saveBtn = screen.getByText("Save");
      expect(saveBtn).toBeDisabled();
    });
  });

  it("Save calls PATCH /config when path is changed", async () => {
    mockedApiPatch.mockResolvedValue({
      ...defaultConfig,
      ac_install_path: "C:\\NewPath",
    });

    renderSettings();

    // Wait for form to populate (AC path appears)
    await waitFor(() => {
      const inputs = screen.getAllByRole("textbox");
      const acInput = inputs.find(
        (i) => (i as HTMLInputElement).value === "C:\\Games\\AC",
      );
      expect(acInput).toBeDefined();
    });

    // Change the AC path to make form dirty
    const inputs = screen.getAllByRole("textbox");
    const acInput = inputs.find(
      (i) => (i as HTMLInputElement).value === "C:\\Games\\AC",
    )!;
    fireEvent.change(acInput, { target: { value: "C:\\NewPath" } });

    // Save button should now be enabled
    await waitFor(() => {
      expect(screen.getByText("Save")).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockedApiPatch).toHaveBeenCalledWith(
        "/config",
        expect.objectContaining({ ac_install_path: "C:\\NewPath" }),
      );
    });
  });

  it("theme toggle buttons render", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Night Grid")).toBeDefined();
      expect(screen.getByText("Garage Floor")).toBeDefined();
    });
  });

  it("Re-run onboarding button shows wizard", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Re-run onboarding wizard")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Re-run onboarding wizard"));

    await waitFor(() => {
      expect(
        screen.getByText("Where is Assetto Corsa installed?"),
      ).toBeDefined();
    });
  });

  it("Test Connection button is disabled without api key", async () => {
    renderSettings();

    await waitFor(() => {
      const testBtn = screen.getByText("Test Connection");
      expect(testBtn).toBeDisabled();
    });
  });

  it("diagnostic mode toggle renders in Advanced section", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Diagnostic Mode")).toBeDefined();
      expect(screen.getByText("On")).toBeDefined();
      expect(screen.getByText("Off")).toBeDefined();
    });
  });

  it("diagnostic mode toggle makes form dirty", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Diagnostic Mode")).toBeDefined();
      expect(screen.getByText("Save")).toBeDisabled();
    });

    // Wait for all pending async effects to settle
    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    await act(async () => {
      fireEvent.click(screen.getByText("On"));
    });

    await waitFor(() => {
      expect(screen.getByText("Save")).not.toBeDisabled();
    });
  });

  it("handleSave includes diagnostic_mode when toggled", async () => {
    mockedApiPatch.mockResolvedValue({
      ...defaultConfig,
      diagnostic_mode: true,
    });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Diagnostic Mode")).toBeDefined();
      expect(screen.getByText("Save")).toBeDisabled();
    });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    await act(async () => {
      fireEvent.click(screen.getByText("On"));
    });

    await waitFor(() => {
      expect(screen.getByText("Save")).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockedApiPatch).toHaveBeenCalledWith(
        "/config",
        expect.objectContaining({ diagnostic_mode: true }),
      );
    });
  });
});
