"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

type FormFields = {
  name: string
  email: string
  subject: string
  message: string
}

type SubmitState = "idle" | "submitted"

const scope = {
  "--primary": "#5b5bd6",
  "--primary-foreground": "#ffffff",
  "--ring": "#5b5bd6",
  "--background": "#ffffff",
  "--card": "#ffffff",
  "--card-foreground": "#111",
  "--border": "#e2e2e9",
  "--input": "#e2e2e9",
  "--muted": "#f5f5f8",
  "--muted-foreground": "#6e6e7e",
  "--foreground": "#111111",
  "--radius": "0.75rem",
} as React.CSSProperties

export default function UITestPage() {
  const [form, setForm] = useState<FormFields>({
    name: "",
    email: "",
    subject: "",
    message: "",
  })
  const [submitState, setSubmitState] = useState<SubmitState>("idle")

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitState("submitted")
  }

  if (submitState === "submitted") {
    return (
      <div style={scope} className="min-h-screen bg-white flex items-center justify-center p-6">
        <Card className="w-full max-w-sm shadow-lg">
          <CardContent className="py-10 flex flex-col items-center text-center gap-4">
            <div className="w-12 h-12 rounded-full bg-green-50 border border-green-200 flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M4 10l4 4 8-8" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <p className="text-base font-bold">Message sent</p>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">We&apos;ll be in touch within one business day.</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setForm({ name: "", email: "", subject: "", message: "" })
                setSubmitState("idle")
              }}
            >
              Send another
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div style={scope} className="min-h-screen bg-white flex items-center justify-center p-6">
      <div className="w-full max-w-sm">

        <div className="mb-7 text-center">
          <h1 className="text-2xl font-extrabold tracking-tight text-[var(--foreground)]">
            Get in touch
          </h1>
          <p className="text-sm text-[var(--muted-foreground)] mt-1.5">
            Fill in the form and we&apos;ll respond within one business day.
          </p>
        </div>

        <Card className="shadow-xl border border-[var(--border)]">
          <CardContent className="pt-2 pb-2">
            <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4 py-4">

              <div className="flex flex-col gap-1.5">
                <label htmlFor="name" className="text-xs font-semibold text-[var(--foreground)]">
                  Full name
                </label>
                <Input
                  id="name"
                  name="name"
                  placeholder="Jane Smith"
                  value={form.name}
                  onChange={handleChange}
                  autoComplete="name"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="text-xs font-semibold text-[var(--foreground)]">
                  Email
                </label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="jane@company.com"
                  value={form.email}
                  onChange={handleChange}
                  autoComplete="email"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="subject" className="text-xs font-semibold text-[var(--foreground)]">
                  Subject
                </label>
                <Input
                  id="subject"
                  name="subject"
                  placeholder="What's this about?"
                  value={form.subject}
                  onChange={handleChange}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="message" className="text-xs font-semibold text-[var(--foreground)]">
                  Message
                </label>
                <Textarea
                  id="message"
                  name="message"
                  placeholder="Tell us more…"
                  value={form.message}
                  onChange={handleChange}
                  rows={4}
                />
              </div>

              <Button type="submit" className="w-full mt-1">
                Send message
              </Button>

            </form>
          </CardContent>
        </Card>

      </div>
    </div>
  )
}
