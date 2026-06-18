import { ShieldCheckered } from "@phosphor-icons/react";
import type { ReactNode } from "react";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-line/80 bg-white/92 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center gap-3 px-3 py-3 sm:px-4 lg:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 text-action shadow-sm">
              <ShieldCheckered size={22} weight="duotone" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-action">visionguardv2</p>
              <h1 className="truncate text-lg font-semibold text-ink">Claims Risk Assessment</h1>
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1440px] px-3 py-4 sm:px-4 lg:px-5">{children}</main>
    </div>
  );
}
