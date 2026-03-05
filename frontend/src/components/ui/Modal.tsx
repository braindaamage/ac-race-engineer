import { useEffect, useCallback, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Button } from "./Button";
import "./Modal.css";

interface ModalAction {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "ghost";
}

interface ModalActions {
  confirm?: ModalAction;
  cancel?: { label: string; onClick: () => void };
}

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  actions?: ModalActions;
}

export function Modal({
  open,
  onClose,
  title,
  children,
  actions,
}: ModalProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, handleKeyDown]);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  if (!open) return null;

  return createPortal(
    <div className="ace-modal-backdrop" onClick={handleBackdropClick}>
      <div className="ace-modal">
        <h2 className="ace-modal__title">{title}</h2>
        <div className="ace-modal__body">{children}</div>
        {actions && (
          <div className="ace-modal__actions">
            {actions.cancel && (
              <Button variant="secondary" onClick={actions.cancel.onClick}>
                {actions.cancel.label}
              </Button>
            )}
            {actions.confirm && (
              <Button
                variant={actions.confirm.variant ?? "primary"}
                onClick={actions.confirm.onClick}
              >
                {actions.confirm.label}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}
