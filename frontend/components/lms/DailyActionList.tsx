"use client"

// DailyActionList — design-system.md §3.22
// A1 Dashboard only. Slot: MAIN_GRID.
// R09: system-ranked — never user-sortable. UI renders server order as received.
// R10: surfaces what to do — not just metrics.
// R12: revenue/compliance signals (outstanding fees, overdue counts) appear here.
// Empty: "All clear" message — never blank.

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Skeleton } from "@/components/ui/skeleton"
import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

export type ActionPriority = "critical" | "important" | "optional"

export type ActionItem = {
  priority: ActionPriority
  /** Describes what to do — "Review at-risk learner" */
  action: string
  /** Names the specific entity — "Intro to Python" */
  entity: string
  cta: {
    label: string
    onClick: () => void
  }
}

type DailyActionListProps = {
  items: ActionItem[]
  loading?: boolean
  /** Server total — used for "View all N" link when server has more than MAX_VISIBLE */
  totalCount?: number
  onViewAll?: () => void
}

const PRIORITY_CONFIG: Record<
  ActionPriority,
  { label: string; dotCls: string; defaultOpen: boolean }
> = {
  critical:  { label: "Critical",  dotCls: "bg-[var(--red-md)]",   defaultOpen: true  },
  important: { label: "Important", dotCls: "bg-[var(--amber-md)]", defaultOpen: true  },
  optional:  { label: "Optional",  dotCls: "bg-[var(--ink-4)]",    defaultOpen: false },
}

const MAX_VISIBLE = 10

export function DailyActionList({
  items,
  loading = false,
  totalCount,
  onViewAll,
}: DailyActionListProps) {
  const visibleItems = items.slice(0, MAX_VISIBLE)
  const serverTotal  = totalCount ?? items.length
  const hasMore      = serverTotal > MAX_VISIBLE

  const groups = (["critical", "important", "optional"] as ActionPriority[])
    .map((priority) => ({
      priority,
      config: PRIORITY_CONFIG[priority],
      items:  visibleItems.filter((i) => i.priority === priority),
    }))
    .filter((g) => g.items.length > 0)

  return (
    <div className="bg-white border border-border rounded-[var(--r)] shadow-[var(--sh-xs)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 h-10 border-b border-border">
        <span className="text-[13px] font-bold text-[var(--ink)]">Today's Actions</span>
        {!loading && items.length > 0 && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-[var(--accent-lt)] text-[var(--accent)]">
            {Math.min(items.length, MAX_VISIBLE)}
          </span>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-4 h-11 border-b border-border last:border-0"
            >
              <Skeleton className="w-2 h-2 rounded-full shrink-0" />
              <Skeleton className="h-3 flex-1 rounded" />
              <Skeleton className="h-3 w-20 rounded" />
              <Skeleton className="h-6 w-16 rounded-full" />
            </div>
          ))}
        </div>
      )}

      {/* All clear */}
      {!loading && items.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <Icon name="check-circle" size="lg" color="success" />
          <div>
            <p className="text-[13px] font-semibold text-[var(--ink)]">
              You're on top of everything
            </p>
            <p className="text-[12px] text-[var(--ink-4)] mt-0.5">No actions needed right now</p>
          </div>
        </div>
      )}

      {/* Priority groups */}
      {!loading &&
        groups.map(({ priority, config, items: groupItems }) => (
          <Collapsible key={priority} defaultOpen={config.defaultOpen}>
            <CollapsibleTrigger className="w-full flex items-center gap-2 px-4 h-8 bg-[var(--subtle)] border-b border-border hover:bg-[var(--border)]/40 transition-colors duration-[120ms]">
              <span className={cn("w-2 h-2 rounded-full shrink-0", config.dotCls)} />
              <span className="text-[11px] font-bold uppercase tracking-[0.04em] text-[var(--ink-3)] flex-1 text-left">
                {config.label}
              </span>
              <span className="text-[11px] font-semibold text-[var(--ink-4)]">
                {groupItems.length}
              </span>
            </CollapsibleTrigger>

            <CollapsibleContent>
              {groupItems.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 px-4 h-11 border-b border-border last:border-0"
                >
                  <span className={cn("w-2 h-2 rounded-full shrink-0", config.dotCls)} />
                  <span className="text-[13px] font-medium text-[var(--ink)] flex-1 min-w-0 truncate">
                    {item.action}{" "}
                    <span className="text-[var(--ink-3)]">{item.entity}</span>
                  </span>
                  <button
                    type="button"
                    onClick={item.cta.onClick}
                    className={cn(
                      "shrink-0 px-2.5 py-1 rounded-full",
                      "text-[12px] font-semibold text-[var(--accent)]",
                      "border border-[rgba(91,91,214,0.2)]",
                      "hover:bg-[var(--accent-lt)] transition-colors duration-[120ms]",
                    )}
                  >
                    {item.cta.label}
                  </button>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        ))}

      {/* View all */}
      {!loading && hasMore && (
        <div className="px-4 py-2.5 border-t border-border">
          <button
            type="button"
            onClick={onViewAll}
            className="text-[12px] font-semibold text-[var(--accent)] hover:underline"
          >
            View all {serverTotal} actions →
          </button>
        </div>
      )}
    </div>
  )
}
