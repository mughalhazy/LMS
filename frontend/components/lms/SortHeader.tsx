// SortHeader — design-system.md §3.5
// Sortable TableHead — 34px height · 10.5px 700 UPPERCASE · +0.06em tracking · --ink-4
// Uses Icon component only — zero direct lucide imports (per §7 icon rules)
// align prop supports left / right / center (R: Status column is center-aligned)

import { TableHead } from "@/components/ui/table"
import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

type SortHeaderProps = {
  col: string
  label: string
  currentCol: string
  currentDir: "asc" | "desc"
  onSort: (col: string) => void
  align?: "left" | "right" | "center"
}

export function SortHeader({
  col,
  label,
  currentCol,
  currentDir,
  onSort,
  align = "left",
}: SortHeaderProps) {
  const active = currentCol === col

  return (
    <TableHead
      className={cn(
        "cursor-pointer select-none whitespace-nowrap h-[34px]",
        "text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)]",
        "hover:text-[var(--ink-2)] transition-colors duration-[120ms]",
        align === "right"  && "text-right",
        align === "center" && "text-center",
      )}
      onClick={() => onSort(col)}
    >
      <span className={cn(
        "inline-flex items-center gap-0.5",
        align === "center" && "justify-center w-full",
        align === "right"  && "justify-end w-full",
      )}>
        {label}
        {active ? (
          currentDir === "asc"
            ? <Icon name="collapse" size="xs" color="muted" />
            : <Icon name="expand"  size="xs" color="muted" />
        ) : (
          <Icon name="sort" size="xs" className="opacity-35" />
        )}
      </span>
    </TableHead>
  )
}
