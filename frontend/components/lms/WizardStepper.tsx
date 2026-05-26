// WizardStepper — A5 CreationWizard
// R32: each step delivers a visible result — not just config
// States: completed (accent check) · active (accent ring, step number) · upcoming (muted)
// Horizontal layout with connector lines between steps

import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

export type WizardStep = {
  label: string
}

type WizardStepperProps = {
  steps: WizardStep[]
  /** 0-based index of the current active step */
  current: number
  /** Called when user clicks a completed step to navigate back */
  onStepClick?: (index: number) => void
}

export function WizardStepper({ steps, current, onStepClick }: WizardStepperProps) {
  return (
    <nav aria-label="Progress" className="flex items-start">
      {steps.map((step, i) => {
        const isCompleted = i < current
        const isActive    = i === current
        const isUpcoming  = i > current

        return (
          <div key={i} className="flex items-start flex-1 min-w-0">
            {/* Step + label column */}
            <button
              type="button"
              disabled={!isCompleted}
              onClick={() => isCompleted && onStepClick?.(i)}
              className={cn(
                "flex flex-col items-center gap-1.5 w-full",
                isCompleted ? "cursor-pointer" : "cursor-default",
              )}
              aria-current={isActive ? "step" : undefined}
            >
              {/* Circle indicator */}
              <div className={cn(
                "w-7 h-7 rounded-full flex items-center justify-center border-2 transition-colors duration-[120ms]",
                isCompleted && "bg-[var(--accent)] border-[var(--accent)]",
                isActive    && "bg-white border-[var(--accent)]",
                isUpcoming  && "bg-white border-[var(--border)]",
              )}>
                {isCompleted ? (
                  <Icon name="check" size="xs" color="inverse" />
                ) : (
                  <span className={cn(
                    "text-[11px] font-bold leading-none",
                    isActive   ? "text-[var(--accent)]" : "text-[var(--ink-4)]",
                  )}>
                    {i + 1}
                  </span>
                )}
              </div>

              {/* Step label */}
              <span className={cn(
                "text-[11px] font-semibold text-center leading-tight px-1",
                isCompleted && "text-[var(--accent)]",
                isActive    && "text-[var(--ink)]",
                isUpcoming  && "text-[var(--ink-4)]",
              )}>
                {step.label}
              </span>
            </button>

            {/* Connector line — not rendered after the last step */}
            {i < steps.length - 1 && (
              <div className={cn(
                "h-[2px] flex-1 mt-3.5 mx-1 shrink-0",
                i < current ? "bg-[var(--accent)]" : "bg-[var(--border)]",
              )} />
            )}
          </div>
        )
      })}
    </nav>
  )
}
