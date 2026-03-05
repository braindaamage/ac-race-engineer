import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PathInput } from "../../../src/components/onboarding/PathInput";

// Mock the api module
vi.mock("../../../src/lib/api", () => ({
  apiPost: vi.fn(),
}));

import { apiPost } from "../../../src/lib/api";

const mockedApiPost = vi.mocked(apiPost);

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("PathInput", () => {
  beforeEach(() => {
    mockedApiPost.mockResolvedValue({ status: "valid", message: "OK" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders input field", () => {
    renderWithQuery(
      <PathInput label="Test" value="" onChange={() => {}} pathType="ac_install" />,
    );
    expect(screen.getByRole("textbox")).toBeDefined();
  });

  it("renders label", () => {
    renderWithQuery(
      <PathInput label="AC Path" value="" onChange={() => {}} pathType="ac_install" />,
    );
    expect(screen.getByText("AC Path")).toBeDefined();
  });

  it("fires onChange on input", () => {
    const handler = vi.fn();
    renderWithQuery(
      <PathInput label="Test" value="" onChange={handler} pathType="ac_install" />,
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "C:\\Games" },
    });
    expect(handler).toHaveBeenCalled();
  });

  it("calls POST /config/validate-path after debounce", async () => {
    mockedApiPost.mockResolvedValue({ status: "valid", message: "Valid Assetto Corsa installation found." });

    renderWithQuery(
      <PathInput label="Test" value="C:\\Games\\AC" onChange={() => {}} pathType="ac_install" />,
    );

    // Wait for debounce (500ms) + API call to resolve
    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith(
        "/config/validate-path",
        expect.objectContaining({ path_type: "ac_install" }),
      );
    });
  });

  it("displays validation success message", async () => {
    mockedApiPost.mockResolvedValue({ status: "valid", message: "Valid AC found." });

    renderWithQuery(
      <PathInput label="Test" value="C:\\Games\\AC" onChange={() => {}} pathType="ac_install" />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Valid AC found/)).toBeDefined();
    });
  });

  it("displays validation warning message", async () => {
    mockedApiPost.mockResolvedValue({ status: "warning", message: "Missing content folder." });

    renderWithQuery(
      <PathInput label="Test" value="C:\\Games" onChange={() => {}} pathType="ac_install" />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Missing content folder/)).toBeDefined();
    });
  });

  it("displays validation error message", async () => {
    mockedApiPost.mockResolvedValue({ status: "not_found", message: "Folder not found." });

    renderWithQuery(
      <PathInput label="Test" value="C:\\Nope" onChange={() => {}} pathType="setups" />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Folder not found/)).toBeDefined();
    });
  });

  it("fires onValidationChange callback", async () => {
    const validationResult = { status: "valid" as const, message: "OK" };
    mockedApiPost.mockResolvedValue(validationResult);
    const onValidationChange = vi.fn();

    renderWithQuery(
      <PathInput
        label="Test"
        value="C:\\Games"
        onChange={() => {}}
        pathType="ac_install"
        onValidationChange={onValidationChange}
      />,
    );

    await waitFor(() => {
      expect(onValidationChange).toHaveBeenCalled();
    });
  });

  it("does not show browse button outside Tauri", () => {
    renderWithQuery(
      <PathInput label="Test" value="" onChange={() => {}} pathType="ac_install" />,
    );
    expect(screen.queryByText("Browse")).toBeNull();
  });
});
