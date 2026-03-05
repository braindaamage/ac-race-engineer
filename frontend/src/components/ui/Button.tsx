import type { ReactNode, MouseEventHandler, ButtonHTMLAttributes } from "react";
import "./Button.css";

interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  children: ReactNode;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
}

export function Button({
  variant = "primary",
  size = "md",
  disabled,
  onClick,
  children,
  type = "button",
}: ButtonProps) {
  const className = [
    "ace-button",
    `ace-button--${variant}`,
    `ace-button--${size}`,
  ].join(" ");

  return (
    <button
      className={className}
      disabled={disabled}
      onClick={onClick}
      type={type}
    >
      {children}
    </button>
  );
}
