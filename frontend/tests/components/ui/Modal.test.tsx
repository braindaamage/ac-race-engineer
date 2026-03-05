import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Modal } from "../../../src/components/ui/Modal";

describe("Modal", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it("when open is false, nothing renders", () => {
    render(
      <Modal open={false} onClose={vi.fn()} title="Hidden modal">
        <p>Body content</p>
      </Modal>,
    );

    expect(screen.queryByText("Hidden modal")).toBeNull();
    expect(screen.queryByText("Body content")).toBeNull();
  });

  it("when open is true, title and content render", () => {
    render(
      <Modal open={true} onClose={vi.fn()} title="Visible modal">
        <p>Modal body</p>
      </Modal>,
    );

    expect(screen.getByText("Visible modal")).toBeTruthy();
    expect(screen.getByText("Modal body")).toBeTruthy();
  });

  it("confirm and cancel buttons render and fire handlers", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <Modal
        open={true}
        onClose={vi.fn()}
        title="Actions modal"
        actions={{
          confirm: { label: "Save", onClick: onConfirm },
          cancel: { label: "Cancel", onClick: onCancel },
        }}
      >
        <p>Content</p>
      </Modal>,
    );

    fireEvent.click(screen.getByText("Save"));
    expect(onConfirm).toHaveBeenCalledOnce();

    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("backdrop click calls onClose", () => {
    const onClose = vi.fn();

    render(
      <Modal open={true} onClose={onClose} title="Backdrop test">
        <p>Content</p>
      </Modal>,
    );

    const backdrop = document.querySelector(".ace-modal-backdrop")!;
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("escape key calls onClose", () => {
    const onClose = vi.fn();

    render(
      <Modal open={true} onClose={onClose} title="Escape test">
        <p>Content</p>
      </Modal>,
    );

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";

    render(
      <Modal open={true} onClose={vi.fn()} title="Dark modal">
        <p>Dark content</p>
      </Modal>,
    );

    expect(screen.getByText("Dark modal")).toBeTruthy();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";

    render(
      <Modal open={true} onClose={vi.fn()} title="Light modal">
        <p>Light content</p>
      </Modal>,
    );

    expect(screen.getByText("Light modal")).toBeTruthy();
  });
});
