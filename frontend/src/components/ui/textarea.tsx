import type { TextareaHTMLAttributes } from "react";

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`focus-ring min-h-20 w-full resize-y rounded-lg border border-line bg-white px-2.5 py-1.5 text-sm text-ink shadow-sm placeholder:text-muted hover:border-slate-300 ${className}`}
      {...props}
    />
  );
}
