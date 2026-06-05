import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: ReactNode;
  variant?: "primary" | "ghost";
}

export function Button({ children, icon, variant = "primary", type = "button", ...props }: ButtonProps) {
  return (
    <button className={`button button--${variant}`} type={type} {...props}>
      {icon ? <span className="button__icon">{icon}</span> : null}
      <span>{children}</span>
    </button>
  );
}
