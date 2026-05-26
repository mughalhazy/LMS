"use client"

// Toast — design-system.md §3.18
// Semantic wrapper around sonner with LMS timing rules and design tokens.
// Usage: call toast.success/warning/error/info anywhere in the app.
// Setup: place <LmsToaster /> once in the root layout (replaces ui/sonner Toaster).

import { toast as sonnerToast, Toaster } from "sonner"
import { Icon } from "@/components/ui/icon"

// ── Semantic helpers — enforces LMS timing (§3.18) ────────────────────────
// success / warning / info: auto-dismiss 4000ms
// error: no auto-dismiss (Infinity) — must be manually closed

export const toast = {
  success: (message: string, description?: string) =>
    sonnerToast.success(message, { description, duration: 4000 }),

  warning: (message: string, description?: string) =>
    sonnerToast.warning(message, { description, duration: 4000 }),

  info: (message: string, description?: string) =>
    sonnerToast.info(message, { description, duration: 4000 }),

  error: (message: string, description?: string) =>
    sonnerToast.error(message, { description, duration: Infinity }),
}

// ── LmsToaster — place once in root layout ─────────────────────────────────
// position: top-right · gap: 8px · max 3 visible · semantic border per variant

export function LmsToaster() {
  return (
    <Toaster
      position="top-right"
      gap={8}
      visibleToasts={3}
      icons={{
        success: <Icon name="success" size="sm" color="success" />,
        warning: <Icon name="warning" size="sm" color="warning" />,
        error:   <Icon name="error"   size="sm" color="danger"  />,
        // info uses teal — not in ICON_COLOR map, override via className
        info:    <Icon name="info"    size="sm" className="!text-[var(--teal-md)]" />,
      }}
      toastOptions={{
        classNames: {
          toast: [
            "!bg-white !border !rounded-[var(--r-sm)]",
            "!shadow-[var(--sh-md)] !font-[Plus_Jakarta_Sans,system-ui,sans-serif]",
          ].join(" "),
          title:       "!text-[13px] !font-medium !text-[var(--ink)]",
          description: "!text-[12px] !text-[var(--ink-3)]",
          success:     "!border-[var(--green-bd)]",
          warning:     "!border-[var(--amber-bd)]",
          error:       "!border-[var(--red-bd)]",
          info:        "!border-[var(--teal-bd)]",
          closeButton: "!text-[var(--ink-4)] hover:!text-[var(--ink-2)]",
        },
      }}
    />
  )
}
