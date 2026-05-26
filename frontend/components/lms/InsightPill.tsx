// InsightPill — design-system.md §3.23
// Inline pill: [● dot] [label] [count]
// R15: PageHeader subtitle shows insight pills — not plain text counts
// Returns null when count === 0 — never render "Published 0"
// Caller enforces max 4 pills per subtitle

import { cn } from "@/lib/utils"

export type InsightType =
  | "published"
  | "draft"
  | "archived"
  | "live"
  | "at-risk"
  | "default"

type InsightPillProps = {
  label: string
  count: number
  type?: InsightType
}

const PILL_STYLES: Record<InsightType, { pill: string; dot: string; count: string }> = {
  published: {
    pill:  "bg-[var(--green-bg)] border-[var(--green-bd)]",
    dot:   "bg-[var(--green-md)]",
    count: "text-[var(--green)]",
  },
  draft: {
    pill:  "bg-[var(--amber-bg)] border-[var(--amber-bd)]",
    dot:   "bg-[var(--amber-md)]",
    count: "text-[var(--amber)]",
  },
  archived: {
    pill:  "bg-[var(--subtle)] border-[var(--border)]",
    dot:   "bg-[var(--ink-4)]",
    count: "text-[var(--ink-3)]",
  },
  live: {
    pill:  "bg-[var(--teal-bg)] border-[var(--teal-bd)]",
    dot:   "bg-[var(--teal-md)]",
    count: "text-[var(--teal)]",
  },
  "at-risk": {
    pill:  "bg-[var(--red-bg)] border-[var(--red-bd)]",
    dot:   "bg-[var(--red-md)]",
    count: "text-[var(--red)]",
  },
  default: {
    pill:  "bg-[var(--accent-lt)] border-[rgba(91,91,214,0.14)]",
    dot:   "bg-[var(--accent)]",
    count: "text-[var(--accent)]",
  },
}

export function InsightPill({ label, count, type = "default" }: InsightPillProps) {
  if (count === 0) return null

  const { pill, dot, count: countCls } = PILL_STYLES[type]

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 h-5 px-2 rounded-full border-[1.5px] whitespace-nowrap",
        pill,
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", dot)} />
      <span className="text-[11px] font-medium text-[var(--ink-2)]">{label}</span>
      <span className={cn("text-[11px] font-bold", countCls)}>{count}</span>
    </span>
  )
}
