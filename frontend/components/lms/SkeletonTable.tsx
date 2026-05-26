// SkeletonTable — design-system.md §3.12
// Mirrors loaded table layout exactly — same column count, same row height
// Shimmer from globals.css .shimmer class · 1400ms ease-in-out
// Always shown before spinner — no full-page spinners (R21)

import { Skeleton } from "@/components/ui/skeleton"

type SkeletonTableProps = {
  /** Number of data columns (excluding checkbox column) */
  cols: number
  /** Number of skeleton rows — default 8 */
  rows?: number
  /** Whether to include a checkbox column */
  hasCheckbox?: boolean
}

// Column width hints — skeleton widths cycle through these to feel organic
const COL_WIDTHS = ["w-32", "w-24", "w-16", "w-20", "w-14", "w-28", "w-12"]

export function SkeletonTable({
  cols,
  rows = 8,
  hasCheckbox = true,
}: SkeletonTableProps) {
  return (
    <div className="bg-white border border-border rounded-[var(--r)] overflow-hidden shadow-[var(--sh-xs)]">
      {/* Header row */}
      <div className="flex items-center gap-3 px-4 h-[34px] bg-[var(--subtle)] border-b border-border">
        {hasCheckbox && <Skeleton className="w-3.5 h-3.5 rounded shrink-0" />}
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-2.5 w-16 rounded" />
        ))}
      </div>

      {/* Data rows — height matches --row-h token via h-[var(--row-h)] */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div
          key={rowIdx}
          className="flex items-center gap-3 px-4 h-[var(--row-h)] border-b border-border last:border-0"
        >
          {hasCheckbox && (
            <Skeleton className="w-3.5 h-3.5 rounded shrink-0" />
          )}
          {Array.from({ length: cols }).map((_, colIdx) => {
            const width = COL_WIDTHS[(rowIdx + colIdx) % COL_WIDTHS.length]
            return (
              <Skeleton
                key={colIdx}
                className={`h-3 ${width} rounded`}
              />
            )
          })}
        </div>
      ))}
    </div>
  )
}
