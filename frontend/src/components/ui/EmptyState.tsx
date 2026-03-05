import type { ReactNode } from "react";
import { Button } from "./Button";
import "./EmptyState.css";

interface EmptyStateAction {
  label: string;
  onClick: () => void;
}

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: EmptyStateAction;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="ace-empty-state">
      <div className="ace-empty-state__icon">{icon}</div>
      <h3 className="ace-empty-state__title">{title}</h3>
      <p className="ace-empty-state__description">{description}</p>
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
