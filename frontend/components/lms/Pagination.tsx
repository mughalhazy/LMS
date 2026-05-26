"use client"

// Pagination — design-system.md §3.19
// A2 slot: below DATA_TABLE · rows-per-page via FilterDropdown (never native select)
// Active page: --lms-accent bg · max 7 page pills with … for large page counts

import { FilterDropdown } from "@/components/lms/FilterDropdown"
import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

// ── Page window algorithm — always produces exactly 7 items when totalPages > 7 ──

function getPageWindow(page: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (page <= 4)        return [1, 2, 3, 4, 5, "…", total]
  if (page >= total - 3) return [1, "…", total - 4, total - 3, total - 2, total - 1, total]
  return [1, "…", page - 1, page, page + 1, "…", total]
}

// ── Component ─────────────────────────────────────────────────────────────

type PaginationProps = {
  /** Current page — 1-indexed */
  page: number
  totalPages: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  pageSizeOptions?: number[]
}

export function Pagination({
  page,
  totalPages,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50, 100],
}: PaginationProps) {
  const pageWindow = getPageWindow(page, totalPages)
  const sizeOptions = pageSizeOptions.map(s => ({ value: String(s), label: `${s} rows` }))

  const NAV_BTN = cn(
    "h-8 w-8 inline-flex items-center justify-center rounded-[var(--r-sm)]",
    "border border-border text-[var(--ink-2)]",
    "hover:bg-[var(--subtle)] transition-colors duration-[120ms]",
    "disabled:opacity-40 disabled:cursor-not-allowed",
  )

  return (
    <div className="flex items-center h-10 gap-1.5">
      {/* Rows per page — noActiveStyle: it's always set, not a filter state */}
      <span className="text-[13px] text-[var(--ink-3)] font-medium mr-1 whitespace-nowrap">
        Rows
      </span>
      <FilterDropdown
        label={String(pageSize)}
        value={String(pageSize)}
        onChange={v => onPageSizeChange(Number(v))}
        options={sizeOptions}
        noActiveStyle
      />

      <div className="flex-1" />

      {/* Prev */}
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className={NAV_BTN}
        aria-label="Previous page"
      >
        <Icon name="back" size="xs" color="secondary" />
      </button>

      {/* Page pills */}
      {pageWindow.map((item, i) =>
        item === "…" ? (
          <span
            key={`ellipsis-${i}`}
            className="w-8 h-8 inline-flex items-center justify-center text-xs text-[var(--ink-4)] select-none"
          >
            …
          </span>
        ) : (
          <button
            key={item}
            onClick={() => onPageChange(item as number)}
            aria-label={`Page ${item}`}
            aria-current={page === item ? "page" : undefined}
            className={cn(
              "h-8 w-8 inline-flex items-center justify-center rounded-[var(--r-sm)]",
              "text-[12px] font-bold transition-colors duration-[120ms]",
              page === item
                ? "bg-[var(--lms-accent)] text-white"
                : "text-[var(--ink-2)] hover:bg-[var(--subtle)]",
            )}
          >
            {item}
          </button>
        )
      )}

      {/* Next */}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className={NAV_BTN}
        aria-label="Next page"
      >
        <Icon name="next" size="xs" color="secondary" />
      </button>
    </div>
  )
}
