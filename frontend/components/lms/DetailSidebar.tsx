// DetailSidebar — design-system.md §3 (A3 ResourceDetail)
// 284px fixed-width right column. Sticky within content area.
// Persists across tab switches — rendered outside the tab panel.
// Slots: metadata fields + optional quick actions section separated by a border.

import { cn } from "@/lib/utils"

type DetailSidebarProps = {
  /** Entity metadata fields — use SidebarField for each row */
  metadata?: React.ReactNode
  /** Scoped quick actions — archive, publish, duplicate, etc. */
  actions?: React.ReactNode
  className?: string
}

export function DetailSidebar({ metadata, actions, className }: DetailSidebarProps) {
  return (
    <aside
      className={cn(
        "w-[284px] shrink-0 sticky top-0 self-start",
        "bg-white border border-border rounded-[var(--r)] shadow-[var(--sh-xs)]",
        "overflow-hidden",
        className,
      )}
    >
      {metadata && (
        <div className="px-4 py-4 flex flex-col gap-3">
          {metadata}
        </div>
      )}

      {metadata && actions && <div className="border-t border-border" />}

      {actions && (
        <div className="px-4 py-3 flex flex-col gap-1">
          {actions}
        </div>
      )}
    </aside>
  )
}

// ── Metadata field — label + value pair ──────────────────────────────────

type SidebarFieldProps = {
  label: string
  value: React.ReactNode
}

export function SidebarField({ label, value }: SidebarFieldProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)]">
        {label}
      </span>
      <span className="text-[13px] font-medium text-[var(--ink)]">
        {value}
      </span>
    </div>
  )
}
