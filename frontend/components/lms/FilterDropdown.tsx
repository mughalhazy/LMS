"use client"

// FilterDropdown — replaces native <select> with styled DropdownMenu popup
// design-system.md §3 (to add) · R22 — no native <select> anywhere
// Active state: indigo border/bg/text when a non-empty value is selected
// noActiveStyle: use for sort/per-page controls that always have a value

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

export type FilterOption = {
  value: string
  label: string
}

type FilterDropdownProps = {
  /** Placeholder label shown when no value is selected */
  label: string
  /** Current selected value — empty string means "no selection / show all" */
  value: string
  onChange: (value: string) => void
  options: FilterOption[]
  /**
   * When true, suppresses the indigo active style even when value is set.
   * Use for controls that always have a value (Sort, Per page) — they are
   * settings, not filters, so the active highlight is misleading.
   */
  noActiveStyle?: boolean
}

export function FilterDropdown({
  label,
  value,
  onChange,
  options,
  noActiveStyle = false,
}: FilterDropdownProps) {
  const active = !noActiveStyle && Boolean(value)
  const currentLabel = value
    ? (options.find(o => o.value === value)?.label ?? label)
    : label

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className={cn(
        "h-8 px-2 rounded-[var(--r-sm)] border text-xs font-medium",
        "inline-flex items-center gap-1.5 outline-none cursor-pointer",
        "whitespace-nowrap transition-colors duration-[120ms]",
        active
          ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold"
          : "border-border bg-[var(--canvas)] text-[var(--ink-2)] hover:border-[var(--border-s)] hover:bg-[var(--subtle)]",
      )}>
        {currentLabel}
        <Icon name="expand" size="xs" color={active ? "primary" : "muted"} />
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        className="min-w-[168px] rounded-[var(--r)] shadow-[var(--sh-md)] p-1.5"
      >
        {options.map(opt => (
          <DropdownMenuItem
            key={opt.value}
            className={cn(
              "text-[12.5px] rounded-[8px] py-2 px-2.5 gap-2 cursor-pointer",
              "transition-colors duration-[120ms]",
              value === opt.value
                ? "bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold"
                : "text-[var(--ink-2)] hover:bg-[var(--subtle)]",
            )}
            onClick={() => onChange(opt.value)}
          >
            <span className={cn(
              "w-[5px] h-[5px] rounded-full shrink-0 mt-[1px]",
              value === opt.value ? "bg-[var(--lms-accent)]" : "bg-transparent",
            )} />
            {opt.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
