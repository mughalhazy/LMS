// KpiCard — design-system.md §3.6
// 3 variants: default · hero (3px left border) · ring (SVG gauge — future)
// Color on number only — never on container (§3.6 rule)
// R11: delta + period + action all required in analytics contexts
// R30: never show absolute number alone — always pair with comparison

import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────────────────────────

type KpiVariant = "default" | "hero"

export type KpiCardProps = {
  /** Short label above the number — e.g. "Active Courses", "Completion Rate" */
  label: string
  /** The primary metric value — string for pre-formatted values, number for raw */
  value: string | number
  /** Unit appended to value — "$", "%", "hrs", etc. */
  unit?: string
  /**
   * Numeric change vs comparison period.
   * Positive = improvement. Negative = decline.
   * Direction is inferred from the metric: for "at-risk" metrics, positive delta = bad.
   * R30: always provide alongside value.
   */
  delta?: number
  /**
   * Comparison period label — "vs last week", "vs last month", "vs target".
   * R30: always provide alongside delta.
   */
  period?: string
  /**
   * Explicit trend direction — overrides delta sign when metric polarity is inverse
   * (e.g. "overdue count": lower is better, so positive delta = bad trend).
   */
  trend?: "up" | "down" | "neutral"
  /**
   * CTA shown when metric is below threshold or declining.
   * R11: required in analytics contexts.
   */
  action?: React.ReactNode
  variant?: KpiVariant
  /** Hero variant: accent color for the 3px left border */
  accentColor?: "indigo" | "green" | "amber" | "red" | "teal"
}

// ── Helpers ────────────────────────────────────────────────────────────────

const ACCENT_BORDER: Record<NonNullable<KpiCardProps["accentColor"]>, string> = {
  indigo: "border-l-[var(--lms-accent)]",
  green:  "border-l-[var(--green-md)]",
  amber:  "border-l-[var(--amber-md)]",
  red:    "border-l-[var(--red-md)]",
  teal:   "border-l-[var(--teal-md)]",
}

// ── Component ─────────────────────────────────────────────────────────────

export function KpiCard({
  label,
  value,
  unit,
  delta,
  period,
  trend,
  action,
  variant = "default",
  accentColor = "indigo",
}: KpiCardProps) {
  // Determine effective trend direction
  const effectiveTrend: "up" | "down" | "neutral" =
    trend ?? (delta == null || delta === 0 ? "neutral" : delta > 0 ? "up" : "down")

  const deltaText = delta != null
    ? `${delta > 0 ? "+" : ""}${delta}${unit === "%" ? "%" : ""}`
    : null

  const trendColor =
    effectiveTrend === "up"   ? "text-[var(--green)]" :
    effectiveTrend === "down" ? "text-[var(--red)]"   : "text-[var(--ink-3)]"

  return (
    <div className={cn(
      "bg-white border border-border rounded-[var(--r)] shadow-[var(--sh-sm)] p-5",
      "flex flex-col gap-3",
      // Hero variant: 3px left accent border (design-system.md §3.6)
      variant === "hero" && cn("border-l-[3px]", ACCENT_BORDER[accentColor]),
    )}>
      {/* Label */}
      <p className="text-[11px] font-bold uppercase tracking-[0.06em] text-[var(--ink-3)]">
        {label}
      </p>

      {/* Value — color on number only (§3.6) */}
      <div className="flex items-baseline gap-1">
        {variant === "hero" ? (
          <span className="text-3xl font-extrabold tracking-[-0.04em] text-[var(--ink)]">
            {value}
          </span>
        ) : (
          <span className="text-2xl font-extrabold tracking-[-0.04em] text-[var(--ink)]">
            {value}
          </span>
        )}
        {unit && (
          <span className="text-sm font-semibold text-[var(--ink-3)]">{unit}</span>
        )}
      </div>

      {/* Delta + period — R30: always alongside value */}
      {(deltaText || period) && (
        <div className="flex items-center gap-1.5 flex-wrap -mt-1">
          {deltaText && (
            <span className={cn("inline-flex items-center gap-0.5 text-[12px] font-semibold", trendColor)}>
              {effectiveTrend === "up"   && <Icon name="trend-up"   size="xs" color="success" />}
              {effectiveTrend === "down" && <Icon name="trend-down" size="xs" color="danger"  />}
              {deltaText}
            </span>
          )}
          {period && (
            <span className="text-[11px] text-[var(--ink-4)] font-medium">{period}</span>
          )}
        </div>
      )}

      {/* Action — R11: shown when metric needs attention */}
      {action && <div className="mt-auto pt-1">{action}</div>}
    </div>
  )
}
