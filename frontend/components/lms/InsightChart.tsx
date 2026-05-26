// InsightChart — design-system.md §3.24
// R29: every chart requires insight label + delta row + action link — all three enforced by TypeScript
// R30: absolute number never shown alone — delta must reference a prior period
// Chart library agnostic — children renders the visualisation

import { Icon } from "@/components/ui/icon"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

type DeltaDirection = "up" | "down" | "neutral"

type InsightChartProps = {
  /** Meaning sentence above chart — must state what changed, not just name a metric */
  insight: string
  /** The chart visualisation — bar, line, donut, etc. Chart library agnostic. */
  children: React.ReactNode
  /** Comparative delta — all three fields required (R30) */
  delta: {
    direction: DeltaDirection
    /** Formatted value — "8%", "24", "+12 pts" */
    value: string
    /** Comparison label — "last month", "prior cohort", "target" */
    period: string
  }
  /** Specific verb + entity — "See at-risk learners →", "View full report →" */
  action: {
    label: string
    onClick: () => void
  }
  /** Chart body height in px. Default 160px · expanded 240px */
  chartHeight?: number
  loading?: boolean
  /** Show empty state when no data exists for the selected period */
  empty?: boolean
}

const DELTA_ARROW: Record<DeltaDirection, string> = {
  up:      "↑",
  down:    "↓",
  neutral: "→",
}

const DELTA_COLOR: Record<DeltaDirection, string> = {
  up:      "text-[var(--green-md)]",
  down:    "text-[var(--red-md)]",
  neutral: "text-[var(--ink-4)]",
}

export function InsightChart({
  insight,
  children,
  delta,
  action,
  chartHeight = 160,
  loading = false,
  empty = false,
}: InsightChartProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-3 p-4">
        <Skeleton className="h-4 w-3/4 rounded" />
        <Skeleton className="w-full rounded" style={{ height: chartHeight }} />
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-1/3 rounded" />
          <Skeleton className="h-3 w-1/4 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* INSIGHT_LABEL — meaning sentence, not a metric name (R29) */}
      <p className="text-[13px] font-semibold text-[var(--ink)] leading-snug line-clamp-2">
        {insight}
      </p>

      {/* CHART_BODY */}
      {empty ? (
        <div
          className="flex flex-col items-center justify-center gap-1.5 rounded-[var(--r-sm)] bg-[var(--subtle)] text-center"
          style={{ height: chartHeight }}
        >
          <Icon name="chart" size="lg" color="muted" />
          <p className="text-[12px] text-[var(--ink-4)] font-medium">No data for this period</p>
        </div>
      ) : (
        <div style={{ height: chartHeight }}>{children}</div>
      )}

      {/* DELTA_ROW + ACTION_LINK — both required (R29, R30) */}
      <div className="flex items-center justify-between gap-2">
        {/* Delta */}
        <span className="text-[12px] text-[var(--ink-3)] font-medium">
          <span className={cn("font-bold", DELTA_COLOR[delta.direction])}>
            {DELTA_ARROW[delta.direction]} {delta.value}
          </span>
          {" "}vs {delta.period}
        </span>

        {/* Action link */}
        <button
          type="button"
          onClick={action.onClick}
          className="text-[12px] font-semibold text-[var(--accent)] hover:underline shrink-0"
        >
          {action.label}
        </button>
      </div>
    </div>
  )
}
