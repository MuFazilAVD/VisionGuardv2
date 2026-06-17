import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  icon?: ReactNode;
};

const variants: Record<ButtonVariant, string> = {
  primary: "border-action bg-action text-white shadow-sm hover:bg-blue-700 hover:shadow-soft",
  secondary: "border-line bg-white text-ink shadow-sm hover:border-slate-300 hover:bg-slate-50",
  ghost: "border-transparent bg-transparent text-ink hover:bg-slate-100",
  danger: "border-danger bg-danger text-white shadow-sm hover:bg-red-700"
};

export function Button({ className = "", variant = "primary", icon, children, ...props }: ButtonProps) {
  return (
    <button
      className={`focus-ring inline-flex min-h-9 items-center justify-center gap-2 rounded-lg border px-3.5 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 [&>svg]:shrink-0 ${variants[variant]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}
