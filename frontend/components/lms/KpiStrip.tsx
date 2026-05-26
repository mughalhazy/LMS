// KpiStrip — design-system.md §3.6
// Layout wrapper for a responsive row of KpiCards.
// A2 slot KPI_STRIP: 3–5 items · A1 slot KPI_STRIP: 4–6 items
// All items must include delta + period (R11 / R30) — enforced at KpiCard level.
// Gap uses --sg token which AdminShell sets per surface density (design-system.md §1.3).

import { KpiCard } from "@/components/lms/KpiCard"
import type { KpiCardProps } from "@/components/lms/KpiCard"
import { cn } from "@/lib/utils"

// ── Column map — static strings required for Tailwind JIT ─────────────────

const COLS: Record<number, string> = {
  1: "lg:grid-cols-1",
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-4",
  5: "lg:grid-cols-5",
  6: "lg:grid-cols-6",
}

// ── Types ──────────────────────────────────────────────────────────────────

type KpiStripProps = {
  /**
   * KpiCard data objects — 3–5 for A2 pages, 4–6 for A1 dashboards.
   * Every item should supply delta + period (R11/R30).
   */
  items: KpiCardProps[]
  className?: string
}

// ── Component ─────────────────────────────────────────────────────────────

export function KpiStrip({ items, className }: KpiStripProps) {
  // Clamp to supported column range; fall back to 4-col if out of map
  const cols = COLS[Math.min(Math.max(items.length, 1), 6)] ?? "lg:grid-cols-4"

  return (
    <div className={cn(
      "grid grid-cols-1 sm:grid-cols-2",
      cols,
      "gap-[var(--sg)]",
      className,
    )}>
      {items.map((item, i) => (
        <KpiCard key={i} {...item} />
      ))}
    </div>
  )
}
