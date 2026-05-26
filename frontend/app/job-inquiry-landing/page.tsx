import {
  Zap,
  UserCheck,
  Target,
  GraduationCap,
  Award,
  Briefcase,
  Laptop,
  Globe,
  BookOpen,
  ArrowRight,
} from "lucide-react"
import { buttonVariants } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

const scope = {
  "--primary": "#5b5bd6",
  "--primary-foreground": "#ffffff",
  "--ring": "#5b5bd6",
  "--background": "#ffffff",
  "--card": "#ffffff",
  "--card-foreground": "#111111",
  "--border": "#e2e2e9",
  "--input": "#e2e2e9",
  "--muted": "#f5f5f8",
  "--muted-foreground": "#6e6e7e",
  "--foreground": "#111111",
  "--radius": "0.75rem",
} as React.CSSProperties

const benefits = [
  {
    icon: Zap,
    title: "Fast Inquiry",
    description: "A simple form — no lengthy applications or account setup required. Submit your details in minutes.",
  },
  {
    icon: UserCheck,
    title: "Profile Review",
    description: "Your skills and background are reviewed carefully by our team, not just an automated filter.",
  },
  {
    icon: Target,
    title: "Opportunity Matching",
    description: "Suitable candidates may be contacted directly for roles that genuinely match their profile.",
  },
]

const steps = [
  {
    number: "01",
    title: "Submit your details",
    description: "Fill in a short form covering your background, skills, and the kind of opportunity you want.",
  },
  {
    number: "02",
    title: "We review your profile",
    description: "Our team reviews each inquiry and matches it against current and upcoming opportunities.",
  },
  {
    number: "03",
    title: "You are contacted if there's a match",
    description: "If a suitable role or project is found, we reach out with the next steps.",
  },
]

const candidates = [
  { icon: GraduationCap, label: "Students" },
  { icon: Award, label: "Fresh Graduates" },
  { icon: Briefcase, label: "Experienced Professionals" },
  { icon: Laptop, label: "Freelancers" },
  { icon: Globe, label: "Remote Workers" },
  { icon: BookOpen, label: "Internship Seekers" },
]

export default function JobInquiryLandingPage() {
  return (
    <div style={scope}>
      <main className="min-h-screen bg-white text-[var(--foreground)]">

        {/* ── HERO ── */}
        <section className="px-6 py-20 md:py-28 text-center">
          <div className="max-w-2xl mx-auto">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-600 border border-indigo-200 mb-6">
              Job Inquiry Platform
            </span>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight">
              Find the Right Opportunity Faster
            </h1>
            <p className="mt-5 text-base md:text-lg text-[var(--muted-foreground)] leading-relaxed">
              Submit your job inquiry and let us review your profile for suitable roles,
              internships, freelance work, or remote opportunities.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href="/job-inquiry"
                className={cn(buttonVariants({ size: "lg" }), "rounded-xl px-7 gap-2")}
              >
                Submit Job Inquiry
                <ArrowRight className="h-4 w-4" />
              </a>
              <a
                href="#how-it-works"
                className={cn(buttonVariants({ variant: "outline", size: "lg" }), "rounded-xl px-7")}
              >
                How It Works
              </a>
            </div>
            <p className="mt-5 text-xs text-[var(--muted-foreground)]">
              Simple inquiry. Clear review. No complicated application process.
            </p>
          </div>
        </section>

        {/* ── BENEFITS ── */}
        <section className="bg-slate-50 px-6 py-16">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Why use this platform?</h2>
              <p className="text-sm text-[var(--muted-foreground)] mt-2">A direct route from inquiry to opportunity.</p>
            </div>
            <div className="grid gap-5 md:grid-cols-3">
              {benefits.map(({ icon: Icon, title, description }) => (
                <Card key={title} className="shadow-sm border border-[var(--border)]">
                  <CardContent className="pt-6 pb-6 px-5 flex flex-col gap-4">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
                      <Icon className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-[var(--foreground)] mb-1.5">{title}</h3>
                      <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">{description}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section id="how-it-works" className="px-6 py-16">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight">How It Works</h2>
              <p className="text-sm text-[var(--muted-foreground)] mt-2">Three steps from inquiry to match.</p>
            </div>
            <div className="flex flex-col gap-8">
              {steps.map(({ number, title, description }) => (
                <div key={number} className="flex gap-5 items-start">
                  <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                    {number}
                  </div>
                  <div>
                    <h3 className="font-bold text-[var(--foreground)] mb-1">{title}</h3>
                    <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── WHO CAN APPLY ── */}
        <section className="bg-slate-50 px-6 py-16">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight mb-2">Who Can Apply</h2>
            <p className="text-sm text-[var(--muted-foreground)] mb-8">Open to anyone seeking work opportunities.</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {candidates.map(({ icon: Icon, label }) => (
                <Card key={label} className="shadow-sm border border-[var(--border)]">
                  <CardContent className="pt-6 pb-5 px-4 flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-indigo-600" />
                    </div>
                    <span className="text-sm font-semibold text-[var(--foreground)]">{label}</span>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* ── BOTTOM CTA ── */}
        <section className="px-6 py-16">
          <div className="max-w-2xl mx-auto rounded-2xl bg-indigo-600 px-8 py-14 text-center">
            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              Ready to share your profile?
            </h2>
            <p className="text-sm text-indigo-100 mt-3 leading-relaxed max-w-sm mx-auto">
              Start with a simple inquiry and tell us what kind of opportunity you&apos;re looking for.
            </p>
            <a
              href="/job-inquiry"
              className="inline-flex items-center justify-center gap-2 mt-8 h-10 px-7 rounded-xl bg-white text-indigo-700 text-sm font-semibold whitespace-nowrap hover:bg-indigo-50 transition-colors"
            >
              Start Inquiry
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </section>

      </main>
    </div>
  )
}
