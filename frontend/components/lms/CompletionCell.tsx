// CompletionCell — design-system.md §3.7
// Progress bar (4px inline) + numeric label — always paired (R18)
// Threshold coloring: >=80% green · 50–79% indigo · <50% amber · overdue red (R17)
// At-risk badge when pct < 50 (R17)

import { cn } from "@/lib/utils"

type CompletionCellProps = {
  pct: number | null
  /** Forces red bar — use when enrollment is overdue regardless of completion % */
  overdue?: boolean
}

export function CompletionCell({ pct, overdue = false }: CompletionCellProps) {
  if (pct === null) {
    return <span className="text-[var(--ink-4)] text-xs">—</span>
  }

  const barColor = overdue
    ? "bg-[var(--red-md)]"
    : pct >= 80
      ? "bg-[var(--green-md)]"
      : pct >= 50
        ? "bg-[var(--lms-accent)]"
        : "bg-[var(--amber-md)]"

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {/* Track (4px — inline table variant per §3.7) */}
      <div className="w-12 h-1 bg-border rounded-full overflow-hidden shrink-0">
        <div
          className={cn("h-full rounded-full transition-all duration-[120ms]", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Numeric label — always alongside bar (R18) */}
      <span className="text-xs font-semibold text-[var(--ink-2)] tabular-nums">{pct}%</span>

      {/* At-risk badge — shown when pct < 50 (R17) */}
      {!overdue && pct < 50 && (
        <span className={cn(
          "text-[9px] font-bold uppercase tracking-[0.05em] leading-none",
          "px-1.5 py-0.5 rounded-full",
          "bg-[var(--red-bg)] border border-[var(--red-bd)] text-[var(--red)]",
        )}>
          At risk
        </span>
      )}

      {/* Overdue badge — shown when overdue prop is true */}
      {overdue && (
        <span className={cn(
          "text-[9px] font-bold uppercase tracking-[0.05em] leading-none",
          "px-1.5 py-0.5 rounded-full",
          "bg-[var(--red-bg)] border border-[var(--red-bd)] text-[var(--red)]",
        )}>
          Overdue
        </span>
      )}
    </div>
  )
}
