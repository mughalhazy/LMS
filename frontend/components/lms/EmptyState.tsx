// EmptyState — design-system.md §3.14
// Used when any list/table/grid has zero items. Never show 0 rows.
// Icon (xl/40px · ink-4) + specific headline + context description + single CTA
// Resource-specific copy always — no generic "No data found." (R20)

import { Icon, IconName } from "@/components/ui/icon"

type EmptyStateProps = {
  /** Semantic icon name — choose one relevant to the resource type */
  icon?: IconName
  /** Specific headline — e.g. "No courses match these filters" not "No results" */
  title: string
  /** Context description — explains the state and hints at resolution */
  description?: string
  /** Single CTA — required per design-system.md §3.14 */
  cta?: React.ReactNode
}

export function EmptyState({
  icon = "search",
  title,
  description,
  cta,
}: EmptyStateProps) {
  return (
    <div className="bg-white border border-border rounded-[var(--r)] shadow-[var(--sh-xs)] py-16 flex flex-col items-center text-center gap-3">
      {/* Icon — xl = 32px, but spec says 40px. Using lg + explicit size override */}
      <div className="w-10 h-10 flex items-center justify-center text-[var(--ink-4)]">
        <Icon name={icon} size="xl" color="muted" />
      </div>

      <div className="flex flex-col gap-1">
        {/* Headline — 15px 700 */}
        <p className="text-[15px] font-bold text-[var(--ink)] leading-snug">{title}</p>

        {/* Description — 13px 500 ink-3 */}
        {description && (
          <p className="text-[13px] font-medium text-[var(--ink-3)] max-w-xs leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {/* Single CTA */}
      {cta && <div className="mt-1">{cta}</div>}
    </div>
  )
}
