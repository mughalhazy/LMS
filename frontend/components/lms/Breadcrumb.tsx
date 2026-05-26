// Breadcrumb — design-system.md §3.20
// Embedded in AdminShell topbar (A3 ResourceDetail, A7 Player). Max 3 levels — flatten middle if deeper.
// Current crumb is never a link. Home icon links to surface root.

import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

export type BreadcrumbItem = {
  label: string
  /** Omit for the current (last) crumb — it is never interactive */
  href?: string
}

type BreadcrumbProps = {
  items: BreadcrumbItem[]
  /** Surface root href — /admin, /instructor, /learner, etc. */
  homeHref?: string
  className?: string
}

export function Breadcrumb({ items, homeHref = "/", className }: BreadcrumbProps) {
  const visible: BreadcrumbItem[] =
    items.length > 3
      ? [items[0], { label: "…" }, items[items.length - 1]]
      : items

  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1", className)}>
      <a
        href={homeHref}
        aria-label="Home"
        className="flex items-center text-[var(--ink-4)] hover:text-[var(--ink-2)] transition-colors duration-[120ms]"
      >
        <Icon name="home" size="xs" color="muted" />
      </a>

      {visible.map((item, i) => {
        const isLast = i === visible.length - 1
        return (
          <span key={i} className="flex items-center gap-1">
            <span className="text-[12px] text-[var(--ink-4)]" aria-hidden>/</span>
            {isLast || !item.href ? (
              <span
                className={cn(
                  "text-[12px]",
                  isLast
                    ? "font-semibold text-[var(--ink)]"
                    : "font-medium text-[var(--ink-3)]",
                )}
                aria-current={isLast ? "page" : undefined}
              >
                {item.label}
              </span>
            ) : (
              <a
                href={item.href}
                className="text-[12px] font-medium text-[var(--ink-3)] hover:text-[var(--ink-2)] transition-colors duration-[120ms]"
              >
                {item.label}
              </a>
            )}
          </span>
        )
      })}
    </nav>
  )
}
