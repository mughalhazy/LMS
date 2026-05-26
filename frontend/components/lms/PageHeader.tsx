// PageHeader — design-system.md §3 (A2/A3/A8 slot: PAGE_HEADER)
// R15: subtitle shows insight pills (colored dot + label) — not plain text counts
// R19: exactly one primary CTA — cta prop accepts a single ReactNode, not an array
// Entrance: animate-fade-up

import { cn } from "@/lib/utils"

// ── Insight pill types ─────────────────────────────────────────────────────

export type InsightColor = "green" | "indigo" | "amber" | "red" | "teal"

export type InsightPill = {
  label: string
  color: InsightColor
}

// Pre-built Tailwind class strings — static so JIT includes them all
const PILL_CLS: Record<InsightColor, string> = {
  green:  "bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green)]",
  indigo: "bg-[var(--accent-lt)] border-[rgba(91,91,214,0.2)] text-[var(--lms-accent)]",
  amber:  "bg-[var(--amber-bg)] border-[var(--amber-bd)] text-[var(--amber)]",
  red:    "bg-[var(--red-bg)] border-[var(--red-bd)] text-[var(--red)]",
  teal:   "bg-[var(--teal-bg)] border-[var(--teal-bd)] text-[var(--teal)]",
}

const DOT_CLS: Record<InsightColor, string> = {
  green:  "bg-[var(--green-md)]",
  indigo: "bg-[var(--lms-accent)]",
  amber:  "bg-[var(--amber-md)]",
  red:    "bg-[var(--red-md)]",
  teal:   "bg-[var(--teal-md)]",
}

// ── Component ─────────────────────────────────────────────────────────────

type PageHeaderProps = {
  /** Page title — rendered as h1 */
  title: string
  /**
   * Insight pills — colored dot + label badges shown beneath the title.
   * R15: must be pills, not plain text. Max 3–4 for cognitive load.
   */
  insights?: InsightPill[]
  /**
   * Secondary actions — export, import, etc.
   * Shown desktop-only (hidden on mobile to avoid clutter).
   */
  actions?: React.ReactNode
  /**
   * Primary CTA — single ReactNode (R19: one primary action per page).
   * Always visible (desktop + mobile).
   */
  cta?: React.ReactNode
}

export function PageHeader({ title, insights, actions, cta }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-4 md:mb-5 animate-fade-up">
      {/* Left: title + insight pills */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-[-0.03em] text-[var(--ink)]">
          {title}
        </h1>

        {insights && insights.length > 0 && (
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            {insights.map((pill, i) => (
              <span
                key={i}
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-0.5 rounded-full border",
                  "text-[11px] font-semibold whitespace-nowrap",
                  PILL_CLS[pill.color],
                )}
              >
                <span className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0",
                  DOT_CLS[pill.color],
                )} />
                {pill.label}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Right: secondary actions + primary CTA */}
      {(actions || cta) && (
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Secondary actions — desktop only */}
          {actions && (
            <div className="hidden md:flex items-center gap-1.5">
              {actions}
            </div>
          )}
          {/* Primary CTA — always visible */}
          {cta}
        </div>
      )}
    </div>
  )
}
