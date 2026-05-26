"use client"

// Drawer — design-system.md §3.21
// Widths: nav=280px · filter=320px · quickview=440px
// Header 48px fixed · body flex-1 overflow-y-auto · footer slot optional
// z-40: below modals (z-50) · shadow: --sh-lg · overlay: rgba(0,0,0,0.40)

import {
  Sheet,
  SheetContent,
  SheetClose,
  SheetHeader,
  SheetFooter,
  SheetTitle,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { XIcon } from "lucide-react"
import { cn } from "@/lib/utils"

const WIDTH_CLS: Record<"nav" | "filter" | "quickview", string> = {
  nav:       "data-[side=left]:!w-[280px] data-[side=right]:!w-[280px]",
  filter:    "data-[side=left]:!w-[320px] data-[side=right]:!w-[320px]",
  quickview: "data-[side=left]:!w-[440px] data-[side=right]:!w-[440px]",
}

type DrawerProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** nav=280px · filter=320px · quickview=440px */
  variant?: "nav" | "filter" | "quickview"
  side?: "left" | "right"
  title: string
  children: React.ReactNode
  /** Optional fixed footer — primary + secondary actions */
  footer?: React.ReactNode
}

export function Drawer({
  open,
  onOpenChange,
  variant = "filter",
  side = "right",
  title,
  children,
  footer,
}: DrawerProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side={side}
        showCloseButton={false}
        className={cn(
          "!z-40 p-0 gap-0 shadow-[var(--sh-lg)]",
          WIDTH_CLS[variant],
        )}
      >
        {/* Header — 48px fixed height */}
        <SheetHeader className="h-12 shrink-0 flex-row items-center justify-between px-4 border-b border-border py-0 gap-0">
          <SheetTitle className="text-[14px] font-bold text-[var(--ink)]">
            {title}
          </SheetTitle>
          <SheetClose
            render={
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Close"
              />
            }
          >
            <XIcon className="size-4" />
          </SheetClose>
        </SheetHeader>

        {/* Body — scrollable */}
        <div className="flex-1 overflow-y-auto p-[var(--pp)]">
          {children}
        </div>

        {/* Footer — optional, fixed bottom */}
        {footer && (
          <SheetFooter className="shrink-0 border-t border-border px-4 py-3 mt-0">
            {footer}
          </SheetFooter>
        )}
      </SheetContent>
    </Sheet>
  )
}
