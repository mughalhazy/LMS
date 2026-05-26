// StatusChip — design-system.md §3.2
// Anatomy: [● dot][LABEL] · 10px 700 UPPERCASE · border 1.5px · --r-pill
// R16: optional actionLabel + onAction for inline contextual action on applicable row states

import { Icon, IconName } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

// ── Variant type — covers all LMS domain states (design-system.md §3.2) ────

export type ChipVariant =
  // Course
  | "draft" | "published" | "archived" | "under_review" | "scheduled"
  // User
  | "active" | "inactive" | "pending" | "suspended"
  // Learning
  | "enrolled" | "completed" | "expired" | "waived"
  // Session
  | "live" | "upcoming" | "ended" | "cancelled"
  // Generic
  | "overdue" | "certified"

// ── Color map — design-system.md §3.2 ────────────────────────────────────

const CHIP_STYLES: Record<ChipVariant, string> = {
  // Green — Published / Active / Completed
  published:    "bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green)]",
  active:       "bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green)]",
  completed:    "bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green)]",
  enrolled:     "bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green)]",

  // Neutral — Draft / Pending / Inactive / ended states
  draft:        "bg-[var(--subtle)] border-[var(--border)] text-[var(--ink-2)]",
  pending:      "bg-[var(--subtle)] border-[var(--border)] text-[var(--ink-2)]",
  inactive:     "bg-[var(--subtle)] border-[var(--border)] text-[var(--ink-2)]",
  waived:       "bg-[var(--subtle)] border-[var(--border)] text-[var(--ink-2)]",
  ended:        "bg-[var(--subtle)] border-[var(--border)] text-[var(--ink-2)]",
  archived:     "bg-[var(--subtle)] border-[var(--border)] text-[var(--ink-2)] opacity-60",

  // Amber — Under Review / Due Soon / Upcoming / Scheduled
  under_review: "bg-[var(--amber-bg)] border-[var(--amber-bd)] text-[var(--amber)]",
  upcoming:     "bg-[var(--amber-bg)] border-[var(--amber-bd)] text-[var(--amber)]",
  scheduled:    "bg-[var(--amber-bg)] border-[var(--amber-bd)] text-[var(--amber)]",

  // Red — Overdue / Suspended / Expired / Cancelled
  overdue:      "bg-[var(--red-bg)] border-[var(--red-bd)] text-[var(--red)]",
  suspended:    "bg-[var(--red-bg)] border-[var(--red-bd)] text-[var(--red)]",
  expired:      "bg-[var(--red-bg)] border-[var(--red-bd)] text-[var(--red)]",
  cancelled:    "bg-[var(--red-bg)] border-[var(--red-bd)] text-[var(--red)]",

  // Teal — Live
  live:         "bg-[var(--teal-bg)] border-[var(--teal-bd)] text-[var(--teal)]",

  // Gold — Certified
  certified:    "bg-[var(--gold-bg)] border-[var(--gold-bd)] text-[var(--gold)]",
}

// ── Component ─────────────────────────────────────────────────────────────

export type StatusChipProps = {
  state: ChipVariant
  label: string
  /** Inline contextual action label — R16. Only render when action applies to this state. */
  actionLabel?: string
  actionIcon?: IconName
  onAction?: () => void
}

export function StatusChip({
  state,
  label,
  actionLabel,
  actionIcon,
  onAction,
}: StatusChipProps) {
  const chip = (
    <span className={cn(
      "inline-flex items-center gap-1 px-[9px] py-[3px] rounded-full border-[1.5px]",
      "text-[10px] font-bold uppercase tracking-[0.04em] whitespace-nowrap",
      "before:content-[''] before:w-[5px] before:h-[5px] before:rounded-full before:bg-current before:shrink-0",
      CHIP_STYLES[state],
    )}>
      {label}
    </span>
  )

  if (!actionLabel) return chip

  return (
    <div className="inline-flex items-center gap-1.5">
      {chip}
      <button
        onClick={onAction}
        className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded-full whitespace-nowrap",
          "text-[11px] font-semibold border border-[rgba(91,91,214,0.2)]",
          "bg-[var(--accent-lt)] text-[var(--lms-accent)]",
          "hover:bg-[rgba(91,91,214,0.12)] transition-colors duration-[120ms]",
        )}
      >
        {actionIcon && <Icon name={actionIcon} size="xs" color="primary" />}
        {actionLabel}
      </button>
    </div>
  )
}
