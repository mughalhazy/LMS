// ActionBar — design-system.md §3 (A4 ResourceEditor, A5 CreationWizard)
// Sticky bottom footer: [status slot ← left] [secondary · primary → right]
// R25: primary action lives here — never floated mid-page
// z-30: above page content, below Drawer (z-40) and Modal (z-50)

import { cn } from "@/lib/utils"

type ActionBarProps = {
  /** Primary action — single button. Save, Publish, Next, Submit. */
  primaryAction: React.ReactNode
  /** Secondary action — Cancel, Back, Save Draft. */
  secondaryAction?: React.ReactNode
  /** Left-aligned status indicator — auto-save state, validation summary, etc. */
  status?: React.ReactNode
  className?: string
}

export function ActionBar({
  primaryAction,
  secondaryAction,
  status,
  className,
}: ActionBarProps) {
  return (
    <footer
      className={cn(
        "sticky bottom-0 z-30",
        "bg-white border-t border-border",
        "px-6 py-3",
        "flex items-center justify-between gap-3",
        className,
      )}
    >
      {/* Left — auto-save / validation status */}
      <div className="flex items-center gap-2 text-[12px] text-[var(--ink-3)]">
        {status}
      </div>

      {/* Right — secondary + primary */}
      <div className="flex items-center gap-2">
        {secondaryAction}
        {primaryAction}
      </div>
    </footer>
  )
}
