import {
  ArrowsClockwise,
  ChartBar,
  CheckCircle,
  ClipboardText,
  FileMagnifyingGlass,
  Pulse,
  ShieldCheckered
} from "@phosphor-icons/react";
import type { ReactNode } from "react";

export type ViewName = "dashboard" | "retraining" | "review" | "results";

const nav = [
  { id: "dashboard" as const, label: "Dashboard", icon: ChartBar },
  { id: "retraining" as const, label: "Retraining", icon: ArrowsClockwise },
  { id: "review" as const, label: "Claim Review", icon: FileMagnifyingGlass },
  { id: "results" as const, label: "Results", icon: ClipboardText }
];

const viewMeta: Record<ViewName, { eyebrow: string; title: string }> = {
  dashboard: { eyebrow: "Operations", title: "Command Center" },
  retraining: { eyebrow: "Readiness", title: "Engine Refresh" },
  review: { eyebrow: "Intake", title: "Claim Workbench" },
  results: { eyebrow: "Findings", title: "Assessment Output" }
};

export function Layout({
  activeView,
  onChangeView,
  children
}: {
  activeView: ViewName;
  onChangeView: (view: ViewName) => void;
  children: ReactNode;
}) {
  const activeMeta = viewMeta[activeView];

  return (
    <div className="min-h-screen bg-canvas text-ink lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="relative hidden min-h-screen overflow-hidden border-r border-slate-950/20 bg-[#10151f] text-white lg:flex lg:flex-col">
        <div className="absolute inset-y-0 left-0 w-1 bg-[linear-gradient(180deg,#2457d6_0%,#0f766e_38%,#b65f00_68%,#bd1e2c_100%)]" />
        <div className="border-b border-white/10 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-white/10 text-white shadow-soft">
              <ShieldCheckered size={23} weight="duotone" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white">VisionGuard</p>
              <p className="truncate text-xs text-slate-300">Claims Risk Assessment</p>
            </div>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3 py-4" aria-label="Primary">
          {nav.map((item) => {
            const Icon = item.icon;
            const selected = activeView === item.id;
            return (
              <button
                key={item.id}
                className={`focus-ring group flex min-h-11 w-full items-center gap-3 rounded-lg border px-3 text-left text-sm font-semibold transition ${
                  selected
                    ? "border-white/15 bg-white text-ink shadow-lift"
                    : "border-transparent text-slate-300 hover:border-white/10 hover:bg-white/[0.08] hover:text-white"
                }`}
                onClick={() => onChangeView(item.id)}
              >
                <span
                  className={`flex size-8 shrink-0 items-center justify-center rounded-md border ${
                    selected
                      ? "border-blue-200 bg-blue-50 text-action"
                      : "border-white/10 bg-white/5 text-slate-300 group-hover:text-white"
                  }`}
                >
                  <Icon size={17} weight={selected ? "fill" : "regular"} aria-hidden="true" />
                </span>
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-white/10 px-4 py-4">
          <div className="rounded-lg border border-white/10 bg-white/[0.06] p-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Pulse size={16} weight="duotone" aria-hidden="true" />
              Live Workspace
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-300">
              <CheckCircle size={14} weight="fill" className="text-green-300" aria-hidden="true" />
              Analyst ready
            </div>
          </div>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-20 border-b border-line/80 bg-white/90 backdrop-blur">
          <div className="flex flex-col gap-3 px-4 py-3 lg:px-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3 lg:hidden">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 text-action shadow-sm">
                  <ShieldCheckered size={22} weight="duotone" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-action">VisionGuard</p>
                  <h1 className="truncate text-lg font-semibold text-ink">Claims Risk Assessment</h1>
                </div>
              </div>
              <div className="hidden min-w-0 lg:block">
                <p className="text-xs font-semibold uppercase text-muted">{activeMeta.eyebrow}</p>
                <h1 className="truncate text-xl font-semibold text-ink">{activeMeta.title}</h1>
              </div>
              <div className="hidden items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm font-semibold text-success sm:flex">
                <CheckCircle size={16} weight="fill" aria-hidden="true" />
                Workspace Ready
              </div>
            </div>

            <nav className="flex gap-2 overflow-x-auto pb-1 lg:hidden" aria-label="Primary">
              {nav.map((item) => {
                const Icon = item.icon;
                const selected = activeView === item.id;
                return (
                  <button
                    key={item.id}
                    className={`focus-ring inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                      selected
                        ? "border-action bg-blue-50 text-action shadow-sm"
                        : "border-line bg-white text-ink hover:border-slate-300 hover:bg-slate-50"
                    }`}
                    onClick={() => onChangeView(item.id)}
                  >
                    <Icon size={17} weight={selected ? "fill" : "regular"} aria-hidden="true" />
                    {item.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-[1680px] px-3 py-4 sm:px-4 lg:px-5">{children}</main>
      </div>
    </div>
  );
}
