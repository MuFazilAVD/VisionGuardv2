import type { HTMLAttributes, ThHTMLAttributes, TdHTMLAttributes } from "react";

export function Table({ className = "", ...props }: HTMLAttributes<HTMLTableElement>) {
  return <table className={`w-full border-collapse text-left text-sm ${className}`} {...props} />;
}

export function THead({ className = "", ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={`bg-slate-900 text-xs uppercase text-white ${className}`} {...props} />;
}

export function TBody({ className = "", ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={`divide-y divide-line ${className}`} {...props} />;
}

export function TR({ className = "", ...props }: HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={`transition hover:bg-blue-50/55 ${className}`} {...props} />;
}

export function TH({ className = "", ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return <th className={`whitespace-nowrap px-3 py-2.5 font-semibold ${className}`} {...props} />;
}

export function TD({ className = "", ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={`px-3 py-2 align-top ${className}`} {...props} />;
}
