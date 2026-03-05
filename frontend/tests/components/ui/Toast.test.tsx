import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Toast } from "../../../src/components/ui/Toast";

describe("Toast", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  const makeNotification = (
    type: "info" | "success" | "warning" | "error",
    message = "Test message",
    id = "toast-1",
  ) => ({
    id,
    type,
    message,
    createdAt: Date.now(),
  });

  it.each(["info", "success", "warning", "error"] as const)(
    "renders with .ace-toast--%s for type '%s'",
    (type) => {
      const { container } = render(
        <Toast notification={makeNotification(type)} onDismiss={vi.fn()} />,
      );

      const el = container.querySelector(`.ace-toast--${type}`);
      expect(el).toBeTruthy();
    },
  );

  it("message content renders", () => {
    render(
      <Toast
        notification={makeNotification("info", "Something happened")}
        onDismiss={vi.fn()}
      />,
    );

    expect(screen.getByText("Something happened")).toBeTruthy();
  });

  it("dismiss button calls onDismiss with notification id", () => {
    const onDismiss = vi.fn();

    render(
      <Toast
        notification={makeNotification("error", "Error!", "err-42")}
        onDismiss={onDismiss}
      />,
    );

    fireEvent.click(screen.getByLabelText("Dismiss"));
    expect(onDismiss).toHaveBeenCalledOnce();
    expect(onDismiss).toHaveBeenCalledWith("err-42");
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";

    render(
      <Toast
        notification={makeNotification("success", "Dark toast")}
        onDismiss={vi.fn()}
      />,
    );

    expect(screen.getByText("Dark toast")).toBeTruthy();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";

    render(
      <Toast
        notification={makeNotification("success", "Light toast")}
        onDismiss={vi.fn()}
      />,
    );

    expect(screen.getByText("Light toast")).toBeTruthy();
  });
});
