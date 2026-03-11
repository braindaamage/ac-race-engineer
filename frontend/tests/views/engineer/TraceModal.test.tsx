import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TraceModal } from "../../../src/views/engineer/TraceModal";

describe("TraceModal", () => {
  it("renders trace content as preformatted text", () => {
    const content = "# Diagnostic Trace: test content";
    render(
      <TraceModal open={true} onClose={vi.fn()} traceContent={content} />,
    );

    const pre = screen.getByText(content);
    expect(pre.tagName).toBe("PRE");
  });

  it("handles null content gracefully", () => {
    render(
      <TraceModal open={true} onClose={vi.fn()} traceContent={null} />,
    );

    expect(screen.getByText("No trace content available.")).toBeDefined();
  });

  it("backdrop click triggers onClose callback", () => {
    const onClose = vi.fn();
    render(
      <TraceModal open={true} onClose={onClose} traceContent="test" />,
    );

    // The Modal closes via backdrop click
    const backdrop = document.querySelector(".ace-modal-backdrop");
    if (backdrop) {
      fireEvent.click(backdrop);
    }

    expect(onClose).toHaveBeenCalled();
  });

  it("does not render when open is false", () => {
    render(
      <TraceModal open={false} onClose={vi.fn()} traceContent="test" />,
    );

    expect(screen.queryByText("Diagnostic Trace")).toBeNull();
  });
});
