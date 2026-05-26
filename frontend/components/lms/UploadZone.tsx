"use client"

// UploadZone — A5 CreationWizard, A6 Builder
// Drag-and-drop with click-to-browse fallback
// Drag-over: accent border + tinted background · 120ms transition
// Loading: skeleton rows — no spinner

import { useRef, useState } from "react"
import { Icon } from "@/components/ui/icon"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

type UploadZoneProps = {
  /** MIME type filter — e.g. "video/*,image/*,.pdf" */
  accept?: string
  multiple?: boolean
  /** Called with the selected or dropped files */
  onFiles: (files: File[]) => void
  loading?: boolean
  /** Descriptive prompt shown inside the zone */
  label?: string
  className?: string
}

export function UploadZone({
  accept,
  multiple = false,
  onFiles,
  loading = false,
  label = "Drop files here or click to browse",
  className,
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length) onFiles(files)
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (files.length) onFiles(files)
    e.target.value = ""
  }

  if (loading) {
    return (
      <div className={cn("flex flex-col gap-2 p-4 rounded-[var(--r)] border border-border", className)}>
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-[var(--r-sm)]" />
        ))}
      </div>
    )
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={label}
      onDragEnter={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click()
      }}
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-[var(--r)]",
        "border-2 border-dashed p-10 text-center cursor-pointer",
        "transition-colors duration-[120ms]",
        isDragging
          ? "border-[var(--accent)] bg-[var(--accent-lt)]"
          : "border-[var(--border)] bg-[var(--subtle)] hover:border-[var(--accent)]/60 hover:bg-[var(--accent-lt)]/40",
        className,
      )}
    >
      <Icon
        name="upload"
        size="lg"
        color={isDragging ? "primary" : "muted"}
      />

      <div className="flex flex-col gap-1">
        <p className="text-[13px] font-semibold text-[var(--ink)]">{label}</p>
        {accept && (
          <p className="text-[11px] text-[var(--ink-4)]">
            {accept.split(",").map((t) => t.trim()).join(" · ")}
          </p>
        )}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
      >
        Browse files
      </Button>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="sr-only"
        onChange={handleChange}
      />
    </div>
  )
}
