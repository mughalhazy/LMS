// BulkToolbar — design-system.md §3.5
// Shown when >= 1 row is selected. --ink bg · white text · height 44px (h-11)
// Slot-based: action buttons passed as children — toolbar is layout only
// R19: actions scoped to selection; R28 (one primary) does not apply inside bulk context

import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

type BulkToolbarProps = {
  /** Number of selected rows */
  count: number
  /** Called when the user clears the selection */
  onClear: () => void
  /** Action buttons — rendered as ghost/outline style on dark bg */
  children?: React.ReactNode
  className?: string
}

export function BulkToolbar({ count, onClear, children, className }: BulkToolbarProps) {
  return (
    <div className={cn(
      "bg-[var(--ink)] rounded-[var(--r)] px-4 h-11",
      "flex items-center gap-2.5 animate-fade-up flex-wrap",
      className,
    )}>
      {/* Count */}
      <span className="text-[13px] font-bold text-white mr-1">
        {count} selected
      </span>

      <div className="w-px h-[18px] bg-white/15 shrink-0" />

      {/* Action buttons slot */}
      {children}

      {/* Clear — always far right */}
      <button
        onClick={onClear}
        className={cn(
          "ml-auto inline-flex items-center gap-1",
          "text-xs font-semibold text-white/40 px-2 py-1 rounded",
          "hover:text-white hover:bg-white/10 transition-all duration-[120ms]",
        )}
      >
        <Icon name="close" size="xs" color="inverse" />
        Clear
      </button>
    </div>
  )
}

// ── Convenience sub-component for action buttons inside BulkToolbar ────────
// Provides the correct ghost-on-dark styling without consumers needing to know it

type BulkActionProps = {
  label: string
  onClick?: () => void
  variant?: "default" | "warning" | "danger"
}

export function BulkAction({ label, onClick, variant = "default" }: BulkActionProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 rounded-[5px] text-xs font-semibold border transition-all duration-[120ms]",
        variant === "default" && "text-white/80 border-white/15 hover:bg-white/10 hover:text-white",
        variant === "warning" && "text-amber-300 border-amber-300/25 hover:bg-white/10",
        variant === "danger"  && "text-red-300 border-red-300/25 hover:bg-white/10",
      )}
    >
      {label}
    </button>
  )
}
