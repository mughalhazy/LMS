"use client"

// ConfirmModal — design-system.md §3.17
// Modal:        general-purpose dialog — title + body slot + footer slot
// ConfirmModal: destructive confirm — entityName mandatory (§3.17), click-outside disabled

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@/components/ui/dialog"
import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

// ── Size map (design-system.md §3.17) ─────────────────────────────────────

const SIZE_CLS: Record<"sm" | "md" | "lg", string> = {
  sm: "sm:max-w-[400px]",
  md: "sm:max-w-[560px]",
  lg: "sm:max-w-[720px]",
}

// ── Shared content shell ───────────────────────────────────────────────────

const CONTENT_CLS = "rounded-[var(--r)] shadow-[var(--sh-xl)] p-0 gap-0"

// ── Modal — general purpose ────────────────────────────────────────────────

type ModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  size?: "sm" | "md" | "lg"
  children: React.ReactNode
  /** Right-aligned footer actions */
  footer?: React.ReactNode
}

export function Modal({
  open,
  onOpenChange,
  title,
  size = "md",
  children,
  footer,
}: ModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton className={cn(CONTENT_CLS, SIZE_CLS[size])}>
        <DialogHeader className="px-6 py-4 border-b border-border">
          <DialogTitle className="text-base font-bold text-[var(--ink)]">
            {title}
          </DialogTitle>
        </DialogHeader>

        <div className="px-6 py-5 text-sm text-[var(--ink-2)]">
          {children}
        </div>

        {footer && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-2">
            {footer}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ── ConfirmModal — destructive confirm ────────────────────────────────────

type ConfirmModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Verb in the confirm question — e.g. "delete", "archive", "remove" */
  action: string
  /** Entity being acted on — mandatory per §3.17: never show a generic confirm */
  entityName: string
  /** Defaults to "This action cannot be undone." — set to null to suppress */
  consequence?: string | null
  onConfirm: () => void
  /** Disables confirm button during async operations */
  loading?: boolean
}

export function ConfirmModal({
  open,
  onOpenChange,
  action,
  entityName,
  consequence = "This action cannot be undone.",
  onConfirm,
  loading = false,
}: ConfirmModalProps) {
  const label = action.charAt(0).toUpperCase() + action.slice(1)

  return (
    // dismissible={false}: explicit cancel required for destructive actions (§3.17)
    <Dialog open={open} onOpenChange={onOpenChange} dismissible={false}>
      <DialogContent
        showCloseButton={false}
        className={cn(CONTENT_CLS, SIZE_CLS["sm"])}
      >
        <DialogHeader className="px-6 py-4 border-b border-border">
          <DialogTitle className="text-base font-bold text-[var(--ink)] flex items-center gap-2">
            <Icon name="warning" size="sm" color="danger" />
            Confirm {label}
          </DialogTitle>
        </DialogHeader>

        <div className="px-6 py-5 flex flex-col gap-1.5">
          <p className="text-sm text-[var(--ink-2)]">
            Are you sure you want to {action}{" "}
            <span className="font-semibold text-[var(--ink)]">{entityName}</span>?
          </p>
          {consequence && (
            <p className="text-[12px] font-medium text-[var(--red)]">
              {consequence}
            </p>
          )}
        </div>

        <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-2">
          <DialogClose render={<Button variant="outline" size="sm" />}>
            Cancel
          </DialogClose>
          <Button
            variant="destructive"
            size="sm"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading && <Icon name="loading" size="xs" color="inverse" animated />}
            {loading ? "Working…" : label}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
