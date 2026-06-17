import type { InputHTMLAttributes } from "react";

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`focus-ring min-h-9 w-full rounded-lg border border-line bg-white px-2.5 py-1.5 text-sm text-ink shadow-sm placeholder:text-muted hover:border-slate-300 ${className}`}
      {...props}
    />
  );
}
