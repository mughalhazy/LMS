"use client"

// A2 — Courses List (ResourceList archetype)
// Surface: Admin | API: GET /api/v1/courses
// Reference: C:/LMS/built-pages/A2/lms-a2-courses-list-v1.html
// Gaps: BG-026 (no server filter/sort/pagination) · BG-027 (no created_by) · BG-008 (no thumbnail_url)

import Image from "next/image"
import { useState, useMemo, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Sheet, SheetContent, SheetHeader, SheetTitle,
} from "@/components/ui/sheet"
import { Icon } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────────────────────────

type CourseStatus = "draft" | "published" | "archived"
type PublishStatus = "unpublished" | "scheduled" | "published"
type DeliveryMode = "self_paced" | "instructor_led" | "blended"
type ChipState = "draft" | "published" | "scheduled" | "archived"

interface Course {
  id: string
  title: string
  code: string | null
  status: CourseStatus
  pub_status: PublishStatus
  mode: DeliveryMode | null
  category: string | null
  duration: number | null
  published: string | null
  created: string
  updated: string
  instructor: string | null
  enrollments: number
  completion: number | null
}

// ── Static Data (BG-026: no server filter — full set loaded, filtered client-side) ──

const COURSES: Course[] = [
  { id:"c001", title:"Engineering Onboarding",    code:"ENG-ONB-101",  status:"published", pub_status:"published",   mode:"blended",        category:"Engineering", duration:180, published:"Jan 20, 2025", created:"Jan 12, 2025", updated:"Mar 10, 2025", instructor:"u_ins_001", enrollments:284, completion:72  },
  { id:"c002", title:"Security Fundamentals",     code:"SEC-101",      status:"published", pub_status:"published",   mode:"self_paced",     category:"Security",    duration:240, published:"Feb 01, 2025", created:"Jan 18, 2025", updated:"Mar 15, 2025", instructor:"u_ins_002", enrollments:391, completion:61  },
  { id:"c003", title:"Product Management Basics", code:"PM-101",       status:"published", pub_status:"published",   mode:"instructor_led", category:"Product",     duration:360, published:"Feb 15, 2025", created:"Feb 01, 2025", updated:"Apr 01, 2025", instructor:"u_ins_003", enrollments:142, completion:88  },
  { id:"c004", title:"Advanced SQL",              code:"DATA-202",     status:"draft",     pub_status:"unpublished", mode:"self_paced",     category:"Engineering", duration:120, published:null,            created:"Feb 10, 2025", updated:"May 01, 2025", instructor:null,         enrollments:0,   completion:null},
  { id:"c005", title:"Leadership Essentials",     code:"HR-LED-01",    status:"published", pub_status:"published",   mode:"blended",        category:"HR",          duration:480, published:"Mar 01, 2025", created:"Feb 20, 2025", updated:"May 10, 2025", instructor:"u_ins_001", enrollments:517, completion:54  },
  { id:"c006", title:"Data Privacy & Compliance", code:"COMP-DP-01",   status:"published", pub_status:"scheduled",   mode:"self_paced",     category:"Compliance",  duration:90,  published:null,            created:"Feb 28, 2025", updated:"May 20, 2025", instructor:"u_ins_004", enrollments:0,   completion:null},
  { id:"c007", title:"Python for Data Analysis",  code:"DATA-PY-01",   status:"draft",     pub_status:"unpublished", mode:"self_paced",     category:"Engineering", duration:300, published:null,            created:"Mar 05, 2025", updated:"May 25, 2025", instructor:"u_ins_002", enrollments:0,   completion:null},
  { id:"c008", title:"Customer Success Playbook", code:"CS-101",       status:"published", pub_status:"published",   mode:"self_paced",     category:"Sales",       duration:150, published:"Mar 10, 2025", created:"Mar 01, 2025", updated:"Jun 01, 2025", instructor:"u_ins_005", enrollments:209, completion:79  },
  { id:"c009", title:"Financial Reporting",       code:"FIN-REP-01",   status:"archived",  pub_status:"published",   mode:"instructor_led", category:"Finance",     duration:200, published:"Oct 01, 2024", created:"Sep 15, 2024", updated:"Oct 15, 2024", instructor:"u_ins_003", enrollments:88,  completion:95  },
  { id:"c010", title:"Agile Delivery Foundations",code:"PM-AGI-01",    status:"published", pub_status:"published",   mode:"blended",        category:"Product",     duration:270, published:"Mar 20, 2025", created:"Mar 10, 2025", updated:"Jun 10, 2025", instructor:"u_ins_004", enrollments:164, completion:67  },
  { id:"c011", title:"Cloud Architecture 101",    code:"ENG-CLD-01",   status:"draft",     pub_status:"unpublished", mode:"self_paced",     category:"Engineering", duration:360, published:null,            created:"Mar 15, 2025", updated:"Jun 15, 2025", instructor:null,         enrollments:0,   completion:null},
  { id:"c012", title:"Presentation Skills",       code:"HR-PRE-01",    status:"published", pub_status:"published",   mode:"instructor_led", category:"HR",          duration:120, published:"Apr 01, 2025", created:"Mar 20, 2025", updated:"Jun 20, 2025", instructor:"u_ins_001", enrollments:320, completion:83  },
  { id:"c013", title:"GDPR Deep Dive",            code:"COMP-GDPR-01", status:"published", pub_status:"published",   mode:"self_paced",     category:"Compliance",  duration:180, published:"Apr 10, 2025", created:"Mar 25, 2025", updated:"Jul 01, 2025", instructor:"u_ins_005", enrollments:72,  completion:91  },
  { id:"c014", title:"Sales Negotiation",         code:"SLS-NEG-01",   status:"draft",     pub_status:"unpublished", mode:"instructor_led", category:"Sales",       duration:240, published:null,            created:"Apr 01, 2025", updated:"Jul 05, 2025", instructor:"u_ins_002", enrollments:0,   completion:null},
  { id:"c015", title:"Incident Management",       code:"OPS-INC-01",   status:"published", pub_status:"published",   mode:"blended",        category:"Engineering", duration:90,  published:"Apr 15, 2025", created:"Apr 05, 2025", updated:"Jul 10, 2025", instructor:"u_ins_003", enrollments:38,  completion:42  },
  { id:"c016", title:"Diversity & Inclusion",     code:"HR-DEI-01",    status:"published", pub_status:"published",   mode:"self_paced",     category:"HR",          duration:120, published:"May 01, 2025", created:"Apr 20, 2025", updated:"Jul 15, 2025", instructor:"u_ins_004", enrollments:517, completion:76  },
  { id:"c017", title:"Technical Writing",         code:"ENG-TW-01",    status:"archived",  pub_status:"published",   mode:"self_paced",     category:"Engineering", duration:150, published:"Jan 01, 2024", created:"Dec 15, 2023", updated:"Jan 15, 2024", instructor:"u_ins_001", enrollments:45,  completion:100 },
  { id:"c018", title:"Finance for Non-Finance",   code:"FIN-NF-01",    status:"published", pub_status:"published",   mode:"instructor_led", category:"Finance",     duration:300, published:"May 10, 2025", created:"Apr 25, 2025", updated:"Jul 20, 2025", instructor:"u_ins_005", enrollments:142, completion:58  },
  { id:"c019", title:"API Design Principles",     code:"ENG-API-01",   status:"draft",     pub_status:"unpublished", mode:"self_paced",     category:"Engineering", duration:210, published:null,            created:"May 01, 2025", updated:"Jul 25, 2025", instructor:"u_ins_002", enrollments:0,   completion:null},
  { id:"c020", title:"Mental Health at Work",     code:"HR-MH-01",     status:"published", pub_status:"scheduled",   mode:"self_paced",     category:"HR",          duration:60,  published:null,            created:"May 05, 2025", updated:"Aug 01, 2025", instructor:"u_ins_003", enrollments:0,   completion:null},
  { id:"c021", title:"SOC 2 Compliance",          code:"COMP-SOC2-01", status:"published", pub_status:"published",   mode:"self_paced",     category:"Compliance",  duration:270, published:"May 20, 2025", created:"May 10, 2025", updated:"Aug 05, 2025", instructor:"u_ins_004", enrollments:284, completion:69  },
  { id:"c022", title:"Enterprise Sales Strategy", code:"SLS-ENT-01",   status:"draft",     pub_status:"unpublished", mode:"instructor_led", category:"Sales",       duration:480, published:null,            created:"May 15, 2025", updated:"Aug 10, 2025", instructor:null,         enrollments:0,   completion:null},
  { id:"c023", title:"System Design Interviews",  code:"ENG-SDI-01",   status:"published", pub_status:"published",   mode:"self_paced",     category:"Engineering", duration:420, published:"Jun 01, 2025", created:"May 20, 2025", updated:"Aug 15, 2025", instructor:"u_ins_001", enrollments:391, completion:74  },
  { id:"c024", title:"Procurement Essentials",    code:"OPS-PRO-01",   status:"archived",  pub_status:"published",   mode:"blended",        category:"Operations",  duration:180, published:"Jun 01, 2024", created:"May 15, 2024", updated:"Jun 15, 2024", instructor:"u_ins_005", enrollments:64,  completion:88  },
]

// ── Helpers ────────────────────────────────────────────────────────────────

function getChipState(c: Course): { state: ChipState; label: string } {
  if (c.status === "archived") return { state: "archived", label: "Archived" }
  if (c.status === "published" && c.pub_status === "scheduled") return { state: "scheduled", label: "Scheduled" }
  if (c.status === "published") return { state: "published", label: "Published" }
  return { state: "draft", label: "Draft" }
}

function getModeConfig(mode: DeliveryMode | null) {
  switch (mode) {
    case "self_paced":     return { abbr: "SP", cls: "bg-[var(--accent-lt)] border border-[rgba(91,91,214,0.18)] text-[var(--lms-accent)]" }
    case "instructor_led": return { abbr: "IL", cls: "bg-[var(--teal-bg)] border border-[var(--teal-bd)] text-[var(--teal)]" }
    case "blended":        return { abbr: "BL", cls: "bg-[var(--green-bg)] border border-[var(--green-bd)] text-[var(--green)]" }
    default:               return { abbr: "?",  cls: "bg-subtle border border-border text-[var(--ink-4)]" }
  }
}

function getModeLabel(mode: DeliveryMode | null): string {
  switch (mode) {
    case "self_paced":     return "Self-paced"
    case "instructor_led": return "Instructor-led"
    case "blended":        return "Blended"
    default:               return "—"
  }
}

function fmtDuration(mins: number | null): string {
  if (!mins) return "—"
  if (mins < 60) return `${mins}m`
  const h = Math.floor(mins / 60), m = mins % 60
  return m ? `${h}h ${m}m` : `${h}h`
}

// ── Sub-components ─────────────────────────────────────────────────────────

function StatusChip({ course }: { course: Course }) {
  const { state, label } = getChipState(course)
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold border border-[1.5px] uppercase tracking-[0.04em] whitespace-nowrap",
      "before:content-[''] before:w-[5px] before:h-[5px] before:rounded-full before:bg-current",
      state === "draft"      && "bg-[var(--subtle)] border-[var(--border-s)] text-[var(--ink-4)]",
      state === "published"  && "bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green)]",
      state === "scheduled"  && "bg-[var(--teal-bg)] border-[var(--teal-bd)] text-[var(--teal)]",
      state === "archived"   && "bg-[var(--subtle)] border-[var(--border-s)] text-[var(--ink-4)] opacity-70",
    )}>
      {label}
    </span>
  )
}

function ModeAvatar({ mode }: { mode: DeliveryMode | null }) {
  const { abbr, cls } = getModeConfig(mode)
  return (
    <div className={cn(
      "w-7 h-7 rounded-[6px] text-[10px] font-bold flex items-center justify-center shrink-0",
      cls
    )}>
      {abbr}
    </div>
  )
}

function CompletionCell({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-[var(--ink-4)] text-xs">—</span>
  const color = pct >= 75 ? "bg-[var(--green-md)]" : pct >= 50 ? "bg-[var(--amber-md)]" : "bg-[var(--red-md)]"
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-12 h-1 bg-border rounded-full overflow-hidden shrink-0">
        <div className={cn("h-1 rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-[var(--ink-2)]">{pct}%</span>
    </div>
  )
}

function SortHeader({
  col, label, currentCol, currentDir, onSort, align = "left",
}: {
  col: string; label: string; currentCol: string; currentDir: "asc" | "desc"
  onSort: (col: string) => void; align?: "left" | "right"
}) {
  const active = currentCol === col
  return (
    <TableHead
      className={cn(
        "cursor-pointer select-none whitespace-nowrap text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)] h-[34px] hover:text-[var(--ink-2)] transition-colors",
        align === "right" && "text-right",
      )}
      onClick={() => onSort(col)}
    >
      {label}{active ? (currentDir === "asc" ? " ↑" : " ↓") : ""}
    </TableHead>
  )
}

// ── Mobile card (premium native) ──────────────────────────────────────────

function CourseCard({
  course, selected, onToggle,
}: {
  course: Course; selected: boolean; onToggle: () => void
}) {
  const { state } = getChipState(course)
  const completionColor = !course.completion ? "" :
    course.completion >= 75 ? "bg-[var(--green-md)]" :
    course.completion >= 50 ? "bg-[var(--amber-md)]" : "bg-[var(--red-md)]"

  return (
    <div
      className={cn(
        "bg-white rounded-[18px] overflow-hidden transition-all duration-150 active:scale-[0.985] active:shadow-[var(--sh-xs)]",
        "shadow-[0_2px_12px_rgba(0,0,0,0.07),0_1px_3px_rgba(0,0,0,0.04)]",
        selected && "ring-2 ring-[var(--lms-accent)] ring-offset-1 bg-[var(--accent-lt)]"
      )}
      onClick={onToggle}
    >
      <div className="p-4">
        {/* Top row: avatar + title + actions */}
        <div className="flex items-start gap-3">
          {/* Larger mode avatar */}
          <div className={cn(
            "w-9 h-9 rounded-[9px] text-[11px] font-bold flex items-center justify-center shrink-0",
            getModeConfig(course.mode).cls
          )}>
            {getModeConfig(course.mode).abbr}
          </div>

          <div className="flex-1 min-w-0">
            <div className="text-[14px] font-semibold text-[var(--ink)] leading-snug tracking-[-0.01em]">
              {course.title}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              {course.code && (
                <span className="text-[10.5px] text-[var(--ink-4)] font-mono">@{course.code}</span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5 shrink-0 -mt-0.5" onClick={e => e.stopPropagation()}>
            <StatusChip course={course} />
            <DropdownMenu>
              <DropdownMenuTrigger className="w-7 h-7 inline-flex items-center justify-center rounded-full text-[var(--ink-4)] hover:bg-[var(--subtle)] transition-colors outline-none">
                <Icon name="more" size="sm" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="min-w-[160px] rounded-[14px] shadow-[var(--sh-lg)]">
                <DropdownMenuItem className="text-[13px] py-2.5">
                  <Icon name="course" size="sm" color="muted" className="mr-2" />
                  View Course
                </DropdownMenuItem>
                <DropdownMenuItem className="text-[13px] py-2.5">
                  <Icon name="edit" size="sm" color="muted" className="mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {state === "draft" && (
                  <DropdownMenuItem className="text-[13px] py-2.5">
                    <Icon name="publish" size="sm" color="muted" className="mr-2" />
                    Publish
                  </DropdownMenuItem>
                )}
                {state === "published" && (
                  <DropdownMenuItem className="text-[13px] py-2.5 text-[var(--amber)]">
                    <Icon name="archived" size="sm" className="mr-2 text-[var(--amber)]" />
                    Archive
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-[13px] py-2.5 text-[var(--red)]">
                  <Icon name="delete" size="sm" className="mr-2 text-[var(--red)]" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Stats pills */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          {course.category && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[var(--subtle)] rounded-full text-[11px] text-[var(--ink-3)] font-medium">
              {course.category}
            </span>
          )}
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[var(--subtle)] rounded-full text-[11px] text-[var(--ink-3)] font-medium">
            <Icon name="clock" size="xs" color="muted" />
            {fmtDuration(course.duration)}
          </span>
          {course.enrollments > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[var(--subtle)] rounded-full text-[11px] text-[var(--ink-3)] font-medium">
              <Icon name="users" size="xs" color="muted" />
              {course.enrollments.toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Completion strip — flush bottom of card */}
      {course.completion !== null && (
        <div className="px-4 pb-3.5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10.5px] font-semibold text-[var(--ink-4)] uppercase tracking-[0.04em]">Completion</span>
            <span className="text-[11px] font-bold text-[var(--ink-2)]">{course.completion}%</span>
          </div>
          <div className="h-1 bg-[var(--subtle)] rounded-full overflow-hidden">
            <div
              className={cn("h-1 rounded-full transition-all duration-500", completionColor)}
              style={{ width: `${course.completion}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

// ── Mobile bottom tab bar ──────────────────────────────────────────────────

const BOTTOM_TABS = [
  { label: "Dashboard", icon: "dashboard" as const },
  { label: "Courses",   icon: "courses"   as const, active: true },
  { label: "Users",     icon: "users"     as const },
  { label: "Reports",   icon: "analytics" as const },
  { label: "More",      icon: "menu"      as const },
]

// ── Nav items ──────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { label: "Dashboard" }, { label: "Users" }, { label: "Courses", active: true },
  { label: "Organizations" }, { label: "Departments" }, { label: "Compliance" },
  { label: "Reports" }, { label: "Settings" }, { label: "Alerts", badge: 7 },
]

// ── Shared select className ────────────────────────────────────────────────

const SELECT_CLS = [
  "h-9 w-full px-3 pr-8 rounded-[9px] border text-sm font-medium",
  "bg-[var(--canvas)] text-[var(--ink-2)] outline-none cursor-pointer transition-colors appearance-none",
  "bg-[image:url('data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20width=%2210%22%20height=%226%22%20fill=%22none%22%3E%3Cpath%20d=%22M1%201l4%204%204-4%22%20stroke=%22%238C8C84%22%20stroke-width=%221.5%22%20stroke-linecap=%22round%22%20stroke-linejoin=%22round%22/%3E%3C/svg%3E')]",
  "bg-no-repeat bg-[right_10px_center]",
].join(" ")

const SELECT_CLS_DESKTOP = [
  "h-8 px-2 pr-7 rounded-[7px] border text-xs font-medium",
  "bg-[var(--canvas)] text-[var(--ink-2)] outline-none cursor-pointer transition-colors appearance-none",
  "bg-[image:url('data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20width=%2210%22%20height=%226%22%20fill=%22none%22%3E%3Cpath%20d=%22M1%201l4%204%204-4%22%20stroke=%22%238C8C84%22%20stroke-width=%221.5%22%20stroke-linecap=%22round%22%20stroke-linejoin=%22round%22/%3E%3C/svg%3E')]",
  "bg-no-repeat bg-[right_8px_center]",
].join(" ")

// ── Main page ──────────────────────────────────────────────────────────────

export default function CoursesPage() {
  const [viewState, setViewState] = useState<"loaded" | "skeleton" | "empty" | "error">("loaded")
  const [query, setQuery]               = useState("")
  const [statusFilter, setStatus]       = useState("")
  const [deliveryFilter, setDelivery]   = useState("")
  const [instructorFilter, setInstructor] = useState("")
  const [sortCol, setSortCol]           = useState("updated")
  const [sortDir, setSortDir]           = useState<"asc" | "desc">("desc")
  const [selected, setSelected]         = useState<Set<string>>(new Set())
  const [page, setPage]                 = useState(1)
  const [perPage, setPerPage]           = useState(25)
  const [navOpen, setNavOpen]           = useState(false)
  const [filterOpen, setFilterOpen]     = useState(false)
  const [mobileLimit, setMobileLimit]   = useState(10)

  useEffect(() => {
    const handler = () => {}
    document.addEventListener("click", handler)
    return () => document.removeEventListener("click", handler)
  }, [])

  // ── Filter + sort (BG-026: client-side only) ──
  const filtered = useMemo(() => {
    let rows = COURSES
    if (query)          rows = rows.filter(c => c.title.toLowerCase().includes(query.toLowerCase()) || c.code?.toLowerCase().includes(query.toLowerCase()))
    if (statusFilter)   rows = rows.filter(c => getChipState(c).state === statusFilter)
    if (deliveryFilter) rows = rows.filter(c => c.mode === deliveryFilter)
    if (instructorFilter === "assigned")   rows = rows.filter(c => c.instructor !== null)
    if (instructorFilter === "unassigned") rows = rows.filter(c => c.instructor === null)

    rows = [...rows].sort((a, b) => {
      let av: string | number = 0, bv: string | number = 0
      if (sortCol === "title")       { av = a.title;       bv = b.title }
      if (sortCol === "status")      { av = getChipState(a).state; bv = getChipState(b).state }
      if (sortCol === "updated")     { av = a.updated;     bv = b.updated }
      if (sortCol === "enrollments") { av = a.enrollments; bv = b.enrollments }
      if (av < bv) return sortDir === "asc" ? -1 : 1
      if (av > bv) return sortDir === "asc" ? 1 : -1
      return 0
    })
    return rows
  }, [query, statusFilter, deliveryFilter, instructorFilter, sortCol, sortDir])

  // Reset mobile list when filters change
  useEffect(() => { setMobileLimit(10) }, [filtered])

  const hasFilters = query || statusFilter || deliveryFilter || instructorFilter
  const activeFilterCount = [statusFilter, deliveryFilter, instructorFilter].filter(Boolean).length

  // ── Pagination ──
  const totalPages = Math.ceil(filtered.length / perPage)
  const pageRows   = filtered.slice((page - 1) * perPage, page * perPage)

  const clearFilters = useCallback(() => {
    setQuery(""); setStatus(""); setDelivery(""); setInstructor(""); setPage(1)
  }, [])

  // ── Selection ──
  const allOnPageSelected = pageRows.length > 0 && pageRows.every(r => selected.has(r.id))
  const someSelected = selected.size > 0

  function toggleAll() {
    setSelected(prev => {
      const next = new Set(prev)
      if (allOnPageSelected) pageRows.forEach(r => next.delete(r.id))
      else pageRows.forEach(r => next.add(r.id))
      return next
    })
  }

  function toggleRow(id: string) {
    setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  }

  function handleSort(col: string) {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortCol(col); setSortDir("desc") }
    setPage(1)
  }

  // ── Render ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[var(--canvas)]">

      {/* ── MOBILE NAV SHEET ── */}
      <Sheet open={navOpen} onOpenChange={setNavOpen}>
        <SheetContent side="left" className="w-[75vw] max-w-[240px] p-0">
          <SheetHeader className="px-5 py-4 border-b border-border">
            <SheetTitle className="flex items-center">
              <Image src="/nucleus-logo.png" alt="Nucleus LMS" width={120} height={40} className="h-9 w-auto object-contain" />
            </SheetTitle>
          </SheetHeader>
          <nav className="py-2">
            {NAV_ITEMS.map(item => (
              <button
                key={item.label}
                onClick={() => setNavOpen(false)}
                className={cn(
                  "w-full text-left px-5 py-2.5 text-sm font-medium flex items-center justify-between transition-colors",
                  item.active
                    ? "bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold"
                    : "text-[var(--ink-3)] hover:bg-[var(--subtle)] hover:text-[var(--ink-2)]"
                )}
              >
                {item.label}
                {item.badge && (
                  <span className="bg-[var(--red-md)] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            ))}
          </nav>
          {/* Mobile quick-add actions */}
          <div className="px-4 pt-2 pb-4 flex flex-col gap-2 border-t border-border mt-2">
            <Button size="sm" className="w-full gap-1.5 justify-start">
              <Icon name="add" size="sm" color="inverse" />
              Create Course
            </Button>
            <Button variant="outline" size="sm" className="w-full gap-1.5 justify-start">
              <Icon name="enroll" size="sm" color="muted" />
              Add User
            </Button>
          </div>
        </SheetContent>
      </Sheet>

      {/* ── MOBILE FILTER SHEET ── */}
      <Sheet open={filterOpen} onOpenChange={setFilterOpen}>
        <SheetContent side="bottom" className="rounded-t-[18px] px-5 pb-8 pt-5 max-h-[80vh]">
          <SheetHeader className="mb-5">
            <SheetTitle className="text-[15px] font-bold text-[var(--ink)]">Filters &amp; Sort</SheetTitle>
          </SheetHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)]">Status</label>
              <select
                className={cn(SELECT_CLS, statusFilter ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)]" : "border-border")}
                value={statusFilter}
                onChange={e => { setStatus(e.target.value); setPage(1) }}
              >
                <option value="">All statuses</option>
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="scheduled">Scheduled</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)]">Delivery mode</label>
              <select
                className={cn(SELECT_CLS, deliveryFilter ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)]" : "border-border")}
                value={deliveryFilter}
                onChange={e => { setDelivery(e.target.value); setPage(1) }}
              >
                <option value="">All modes</option>
                <option value="self_paced">Self-paced</option>
                <option value="instructor_led">Instructor-led</option>
                <option value="blended">Blended</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)]">Instructor</label>
              <select
                className={cn(SELECT_CLS, instructorFilter ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)]" : "border-border")}
                value={instructorFilter}
                onChange={e => { setInstructor(e.target.value); setPage(1) }}
              >
                <option value="">All courses</option>
                <option value="assigned">Has instructor</option>
                <option value="unassigned">No instructor</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)]">Sort by</label>
              <select
                className={cn(SELECT_CLS, "border-border")}
                value={`${sortCol}_${sortDir}`}
                onChange={e => {
                  const [col, dir] = e.target.value.split("_")
                  setSortCol(col); setSortDir(dir as "asc" | "desc"); setPage(1)
                }}
              >
                <option value="updated_desc">Updated (newest)</option>
                <option value="updated_asc">Updated (oldest)</option>
                <option value="title_asc">Title A–Z</option>
                <option value="title_desc">Title Z–A</option>
                <option value="enrollments_desc">Enrollments ↓</option>
                <option value="status_asc">Status</option>
              </select>
            </div>
            <div className="flex gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => { clearFilters(); setFilterOpen(false) }}
              >
                Clear all
              </Button>
              <Button size="sm" className="flex-1" onClick={() => setFilterOpen(false)}>
                Show {filtered.length} courses
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* ── UTILITY BAR ── */}
      <header className="h-12 bg-white border-b border-border flex items-center px-4 md:px-7 gap-2 sticky top-0 z-40 shadow-[var(--sh-xs)]">
        {/* Logo */}
        <div className="flex items-center mr-2 shrink-0">
          <Image src="/nucleus-logo.png" alt="Nucleus LMS" width={96} height={32} className="h-8 w-auto object-contain" priority />
        </div>

        {/* Quick-add buttons — desktop only */}
        <Button variant="outline" size="sm" className="hidden md:inline-flex h-7 text-[11px] font-semibold">+ User</Button>
        <Button size="sm" className="hidden md:inline-flex h-7 text-[11px] font-semibold">+ Course</Button>
        <Button variant="outline" size="sm" className="hidden md:inline-flex h-7 text-[11px] font-semibold">+ Organization</Button>

        <div className="ml-auto flex items-center gap-1.5">
          {/* Tenant + role — desktop only */}
          <Button variant="ghost" size="sm" className="hidden md:inline-flex h-7 gap-1.5 text-[11px] font-semibold text-[var(--ink-2)]">
            <Icon name="home" size="xs" color="muted" />
            Acme Corp
            <Icon name="expand" size="xs" color="muted" />
          </Button>
          <Button variant="ghost" size="sm" className="hidden md:inline-flex h-7 gap-1.5 text-[11px] font-semibold text-[var(--ink-2)]">
            <span className="w-[5px] h-[5px] rounded-full bg-[var(--ink-3)] inline-block" />
            Admin
            <Icon name="expand" size="xs" color="muted" />
          </Button>

          {/* Notification — always visible */}
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 relative">
            <Icon name="notification" size="sm" color="muted" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[var(--red-md)] border-2 border-white" />
          </Button>

          {/* Avatar — always visible */}
          <div className="w-7 h-7 rounded-full bg-[var(--ink)] text-white text-[10px] font-bold flex items-center justify-center cursor-pointer">
            AK
          </div>
        </div>
      </header>

      {/* ── NAV BAR — desktop only ── */}
      <nav className="hidden md:flex h-10 bg-white border-b border-border items-center px-7 gap-0.5 sticky top-12 z-30">
        {NAV_ITEMS.map(item => (
          <button
            key={item.label}
            className={cn(
              "px-3 py-1.5 rounded-[7px] text-xs font-medium whitespace-nowrap transition-all duration-[120ms]",
              item.active
                ? "bg-[var(--ink)] text-white font-semibold"
                : "text-[var(--ink-3)] hover:bg-[var(--subtle)] hover:text-[var(--ink-2)]"
            )}
          >
            {item.label}
            {item.badge && (
              <span className="ml-1 inline-block bg-[var(--red-md)] text-white text-[9px] font-bold px-1.5 py-0 rounded-full align-middle">
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* ── CANVAS ── */}
      <main className="p-4 pb-28 md:pb-7 md:p-7 md:max-w-[1100px] md:mx-auto">

        {/* Page header */}
        <div className="flex items-start justify-between mb-4 md:mb-5 animate-fade-up">
          <div>
            <h1 className="text-xl md:text-2xl font-extrabold tracking-[-0.03em] text-[var(--ink)] mb-0.5">Courses</h1>
            <p className="text-xs md:text-sm text-[var(--ink-3)]">
              {COURSES.length} courses · {COURSES.filter(c => c.status === "published" && c.pub_status === "published").length} published
            </p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {/* Export/Import — desktop only */}
            <Button variant="outline" size="sm" className="hidden md:inline-flex gap-1.5">
              <Icon name="export" size="sm" color="muted" />
              Export
            </Button>
            <Button variant="outline" size="sm" className="hidden md:inline-flex gap-1.5">
              <Icon name="upload" size="sm" color="muted" />
              Import
            </Button>
            {/* Create — always visible, icon-only on mobile */}
            <Button size="sm" className="gap-1.5">
              <Icon name="add" size="sm" color="inverse" />
              <span className="hidden sm:inline">Create Course</span>
            </Button>
          </div>
        </div>

        {/* ── FILTER BAR — desktop ── */}
        <div className="hidden md:flex bg-white border border-border rounded-[14px] px-3.5 py-2.5 items-center gap-2 mb-2 shadow-[var(--sh-xs)] animate-fade-up flex-wrap">
          <div className="relative flex-1 min-w-40">
            <Icon name="search" size="sm" color="muted"
              className="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none"
            />
            <Input
              className="pl-8 h-8 text-[12.5px] bg-[var(--canvas)] border-border focus-visible:ring-1 focus-visible:ring-[var(--lms-accent)]"
              placeholder="Search by title or course code…"
              value={query}
              onChange={e => { setQuery(e.target.value); setPage(1) }}
            />
          </div>
          <div className="w-px h-[18px] bg-border shrink-0" />
          <select
            className={cn(SELECT_CLS_DESKTOP, statusFilter ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold" : "border-border")}
            value={statusFilter}
            onChange={e => { setStatus(e.target.value); setPage(1) }}
          >
            <option value="">Status</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="scheduled">Scheduled</option>
            <option value="archived">Archived</option>
          </select>
          <select
            className={cn(SELECT_CLS_DESKTOP, deliveryFilter ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold" : "border-border")}
            value={deliveryFilter}
            onChange={e => { setDelivery(e.target.value); setPage(1) }}
          >
            <option value="">Delivery</option>
            <option value="self_paced">Self-paced</option>
            <option value="instructor_led">Instructor-led</option>
            <option value="blended">Blended</option>
          </select>
          <select
            className={cn(SELECT_CLS_DESKTOP, instructorFilter ? "border-[var(--lms-accent)] bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold" : "border-border")}
            value={instructorFilter}
            onChange={e => { setInstructor(e.target.value); setPage(1) }}
          >
            <option value="">Instructor</option>
            <option value="assigned">Assigned</option>
            <option value="unassigned">Unassigned</option>
          </select>
          <div className="w-px h-[18px] bg-border shrink-0" />
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[var(--ink-4)] whitespace-nowrap">
            Sort:
            <select
              className={cn(SELECT_CLS_DESKTOP, "border-border min-w-[100px]")}
              value={`${sortCol}_${sortDir}`}
              onChange={e => {
                const [col, dir] = e.target.value.split("_")
                setSortCol(col); setSortDir(dir as "asc" | "desc"); setPage(1)
              }}
            >
              <option value="updated_desc">Updated ↓</option>
              <option value="updated_asc">Updated ↑</option>
              <option value="title_asc">Title A–Z</option>
              <option value="title_desc">Title Z–A</option>
              <option value="enrollments_desc">Enrollments ↓</option>
              <option value="status_asc">Status</option>
            </select>
          </div>
          <div className="w-px h-[18px] bg-border shrink-0" />
          <span className="text-[11px] font-bold text-[var(--ink-3)] whitespace-nowrap">
            {filtered.length} {filtered.length === 1 ? "course" : "courses"}
          </span>
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="text-xs font-semibold text-[var(--ink-4)] px-1.5 py-0.5 rounded-[5px] hover:text-[var(--ink-2)] hover:bg-[var(--subtle)] transition-all"
            >
              Clear all
            </button>
          )}
        </div>

        {/* ── SEARCH + FILTER CHIPS — mobile ── */}
        <div className="md:hidden mb-3 flex flex-col gap-2">
          {/* Search */}
          <div className="relative">
            <Icon name="search" size="sm" color="muted"
              className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
            />
            <Input
              className="pl-10 h-11 text-[13.5px] bg-white border-0 shadow-[0_2px_12px_rgba(0,0,0,0.07)] rounded-[14px] focus-visible:ring-2 focus-visible:ring-[var(--lms-accent)]"
              placeholder="Search courses…"
              value={query}
              onChange={e => { setQuery(e.target.value); setPage(1) }}
            />
            {query && (
              <button
                onClick={() => { setQuery(""); setPage(1) }}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-[var(--ink-4)] text-white flex items-center justify-center"
              >
                <Icon name="close" size="xs" color="inverse" />
              </button>
            )}
          </div>
          {/* Scrollable filter chips */}
          <div className="flex gap-2 overflow-x-auto pb-0.5 scrollbar-none -mx-4 px-4">
            {[
              { label: "All",            val: "",              field: "status" as const },
              { label: "Published",      val: "published",     field: "status" as const },
              { label: "Draft",          val: "draft",         field: "status" as const },
              { label: "Scheduled",      val: "scheduled",     field: "status" as const },
              { label: "Archived",       val: "archived",      field: "status" as const },
              { label: "Self-paced",     val: "self_paced",    field: "delivery" as const },
              { label: "Instructor-led", val: "instructor_led",field: "delivery" as const },
              { label: "Blended",        val: "blended",       field: "delivery" as const },
            ].map(chip => {
              const isActive = chip.val === ""
                ? !statusFilter && !deliveryFilter
                : chip.field === "status" ? statusFilter === chip.val : deliveryFilter === chip.val
              return (
                <button
                  key={chip.label}
                  onClick={() => {
                    if (chip.val === "") { clearFilters(); return }
                    if (chip.field === "status") { setStatus(isActive ? "" : chip.val); setPage(1) }
                    else { setDelivery(isActive ? "" : chip.val); setPage(1) }
                  }}
                  className={cn(
                    "shrink-0 h-8 px-3.5 rounded-full text-[12px] font-semibold whitespace-nowrap transition-all duration-150",
                    isActive
                      ? "bg-[var(--ink)] text-white shadow-[var(--sh-sm)]"
                      : "bg-white text-[var(--ink-3)] shadow-[0_1px_4px_rgba(0,0,0,0.07)]"
                  )}
                >
                  {chip.label}
                </button>
              )
            })}
            {/* More filters */}
            <button
              onClick={() => setFilterOpen(true)}
              className={cn(
                "shrink-0 h-8 px-3.5 rounded-full text-[12px] font-semibold whitespace-nowrap transition-all duration-150 flex items-center gap-1.5",
                instructorFilter
                  ? "bg-[var(--lms-accent)] text-white shadow-[var(--sh-sm)]"
                  : "bg-white text-[var(--ink-3)] shadow-[0_1px_4px_rgba(0,0,0,0.07)]"
              )}
            >
              <Icon name="filter" size="xs" color={instructorFilter ? "inverse" : "muted"} />
              More
            </button>
          </div>
          {/* Result count */}
          <p className="text-[11.5px] text-[var(--ink-4)] font-medium px-0.5">
            {filtered.length} {filtered.length === 1 ? "course" : "courses"}
            {hasFilters && (
              <button onClick={clearFilters} className="ml-2 text-[var(--lms-accent)] font-semibold">
                Clear
              </button>
            )}
          </p>
        </div>

        {/* Bulk toolbar */}
        {someSelected && (
          <div className="bg-[var(--ink)] rounded-[14px] px-3.5 md:px-4 py-2.5 flex items-center gap-2 md:gap-2.5 mb-3 animate-fade-up flex-wrap">
            <span className="text-[13px] font-bold text-white mr-1">{selected.size} selected</span>
            <div className="w-px h-[18px] bg-white/15 shrink-0" />
            <button className="px-2.5 md:px-3 py-1.5 rounded-[5px] text-xs font-semibold text-white/80 border border-white/15 hover:bg-white/10 hover:text-white transition-all">
              Publish
            </button>
            <button className="px-2.5 md:px-3 py-1.5 rounded-[5px] text-xs font-semibold text-yellow-300 border border-yellow-300/25 hover:bg-white/10 transition-all">
              Archive
            </button>
            <button className="hidden md:block px-3 py-1.5 rounded-[5px] text-xs font-semibold text-white/80 border border-white/15 hover:bg-white/10 hover:text-white transition-all">
              Export
            </button>
            <button
              onClick={() => setSelected(new Set())}
              className="ml-auto text-xs font-semibold text-white/40 px-2 py-1 rounded hover:text-white hover:bg-white/10 transition-all"
            >
              ✕ Clear
            </button>
          </div>
        )}

        {/* ── SKELETON ── */}
        {viewState === "skeleton" && (<>
          {/* Desktop skeleton */}
          <div className="hidden md:block bg-white border border-border rounded-[14px] overflow-hidden shadow-[var(--sh-xs)]">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-4 h-10 border-b border-border last:border-0">
                <Skeleton className="w-3.5 h-3.5 rounded shrink-0" />
                <Skeleton className="w-7 h-7 rounded-[6px] shrink-0" />
                <div className="flex flex-col gap-1 flex-1">
                  <Skeleton className="h-3 w-48" />
                  <Skeleton className="h-2.5 w-24" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-12 ml-auto" />
              </div>
            ))}
          </div>
          {/* Mobile skeleton */}
          <div className="md:hidden flex flex-col gap-2.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="bg-white rounded-[18px] overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.07),0_1px_3px_rgba(0,0,0,0.04)]">
                <div className="p-4 flex flex-col gap-3">
                  <div className="flex items-start gap-3">
                    <Skeleton className="w-9 h-9 rounded-[9px] shrink-0" />
                    <div className="flex-1 flex flex-col gap-1.5">
                      <Skeleton className="h-[14px] w-3/4 rounded-[6px]" />
                      <Skeleton className="h-[11px] w-1/3 rounded-[6px]" />
                    </div>
                    <Skeleton className="h-5 w-16 rounded-full shrink-0" />
                  </div>
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-20 rounded-full" />
                    <Skeleton className="h-6 w-14 rounded-full" />
                    <Skeleton className="h-6 w-16 rounded-full" />
                  </div>
                </div>
                <div className="px-4 pb-3.5">
                  <Skeleton className="h-1 w-full rounded-full" />
                </div>
              </div>
            ))}
          </div>
        </>)}

        {/* ── EMPTY ── */}
        {viewState === "empty" && (
          <div className="bg-white border border-border rounded-[14px] shadow-[var(--sh-xs)] py-16 flex flex-col items-center text-center gap-3">
            <Icon name="courses" size="xl" color="muted" />
            <div>
              <p className="text-base font-extrabold tracking-tight text-[var(--ink)] mb-1">No courses yet.</p>
              <p className="text-sm text-[var(--ink-3)] max-w-xs leading-relaxed">
                Create your first course to start building your learning catalog.
              </p>
            </div>
            <Button size="sm" className="mt-1 gap-1.5">
              <Icon name="add" size="sm" color="inverse" />
              Create Course
            </Button>
          </div>
        )}

        {/* ── ERROR ── */}
        {viewState === "error" && (
          <div className="bg-white border border-border rounded-[14px] shadow-[var(--sh-xs)] py-10 flex flex-col items-center text-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[var(--red-bg)] border border-[var(--red-bd)] flex items-center justify-center">
              <Icon name="error" size="md" color="danger" />
            </div>
            <div>
              <p className="text-sm font-bold text-[var(--ink)] mb-0.5">Couldn&apos;t load courses.</p>
              <p className="text-xs text-[var(--ink-3)]">course-service may be unavailable.</p>
            </div>
            <Button size="sm" variant="outline" onClick={() => setViewState("loaded")} className="gap-1.5">
              <Icon name="refresh" size="sm" color="muted" />
              Try Again
            </Button>
          </div>
        )}

        {/* ── LOADED ── */}
        {viewState === "loaded" && (<>

          {/* ── DESKTOP TABLE ── */}
          <div className="hidden md:block bg-white border border-border rounded-[14px] overflow-hidden shadow-[var(--sh-xs)] animate-fade-up">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-[var(--subtle)]">
                  <TableRow className="border-b border-border hover:bg-transparent">
                    <TableHead className="w-10 pl-3.5">
                      <input
                        type="checkbox"
                        checked={allOnPageSelected}
                        onChange={toggleAll}
                        className="w-3.5 h-3.5 rounded-[4px] border-[1.5px] border-[var(--border-s)] cursor-pointer accent-[var(--ink)]"
                      />
                    </TableHead>
                    <SortHeader col="title"       label="Course"       currentCol={sortCol} currentDir={sortDir} onSort={handleSort} />
                    <TableHead className="text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)] h-[34px] whitespace-nowrap">Instructor</TableHead>
                    <SortHeader col="status"      label="Status"       currentCol={sortCol} currentDir={sortDir} onSort={handleSort} />
                    <TableHead className="text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)] h-[34px] whitespace-nowrap">Category</TableHead>
                    <SortHeader col="duration"    label="Duration"     currentCol={sortCol} currentDir={sortDir} onSort={handleSort} align="right" />
                    <SortHeader col="enrollments" label="Enrollments"  currentCol={sortCol} currentDir={sortDir} onSort={handleSort} align="right" />
                    <TableHead className="text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--ink-4)] h-[34px] whitespace-nowrap">Completion</TableHead>
                    <SortHeader col="updated"     label="Last Updated" currentCol={sortCol} currentDir={sortDir} onSort={handleSort} />
                    <TableHead className="w-11 text-center sticky right-0 bg-[var(--subtle)]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pageRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={10} className="py-10 text-center text-sm text-[var(--ink-3)]">
                        No courses match your filters.{" "}
                        <button onClick={clearFilters} className="text-[var(--lms-accent)] font-semibold hover:underline">
                          Clear filters
                        </button>
                      </TableCell>
                    </TableRow>
                  ) : pageRows.map(course => {
                    const isSel = selected.has(course.id)
                    return (
                      <TableRow
                        key={course.id}
                        className={cn(
                          "border-b border-border h-10 transition-colors cursor-pointer",
                          isSel
                            ? "bg-[var(--accent-lt)] hover:bg-[var(--accent-lt)]"
                            : "hover:bg-[rgba(91,91,214,0.018)]"
                        )}
                        onClick={() => toggleRow(course.id)}
                      >
                        <TableCell className="pl-3.5 w-10" onClick={e => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={isSel}
                            onChange={() => toggleRow(course.id)}
                            className="w-3.5 h-3.5 rounded-[4px] border-[1.5px] border-[var(--border-s)] cursor-pointer accent-[var(--ink)]"
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2.5">
                            <ModeAvatar mode={course.mode} />
                            <div className="min-w-0">
                              <div className="text-[13px] font-semibold text-[var(--ink)] truncate max-w-[200px]">{course.title}</div>
                              {course.code && <div className="text-[11px] text-[var(--ink-4)] font-mono">@{course.code}</div>}
                              <div className="text-[10px] text-[var(--ink-4)] italic">{getModeLabel(course.mode)}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {course.instructor
                            ? <span className="text-[9px] text-[var(--ink-4)] font-mono bg-[var(--subtle)] border border-dashed border-[var(--border-s)] px-1.5 py-0.5 rounded">{course.instructor}</span>
                            : <span className="text-[var(--ink-4)] text-xs">—</span>
                          }
                        </TableCell>
                        <TableCell><StatusChip course={course} /></TableCell>
                        <TableCell className="text-xs text-[var(--ink-2)]">{course.category ?? "—"}</TableCell>
                        <TableCell className="text-right text-xs text-[var(--ink-3)]">{fmtDuration(course.duration)}</TableCell>
                        <TableCell className="text-right text-[13px] font-semibold text-[var(--ink-2)]">{course.enrollments.toLocaleString()}</TableCell>
                        <TableCell><CompletionCell pct={course.completion} /></TableCell>
                        <TableCell className="text-xs text-[var(--ink-3)] whitespace-nowrap">{course.updated}</TableCell>
                        <TableCell
                          className="text-center sticky right-0 bg-white w-11"
                          onClick={e => e.stopPropagation()}
                          style={{ background: isSel ? "var(--accent-lt)" : "white" }}
                        >
                          <DropdownMenu>
                            <DropdownMenuTrigger className="w-7 h-7 p-0 inline-flex items-center justify-center rounded-[7px] text-[var(--ink-4)] hover:text-[var(--ink-2)] hover:bg-[var(--subtle)] transition-colors outline-none">
                              <Icon name="more" size="sm" />
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="min-w-[148px] rounded-[10px] shadow-[var(--sh-md)]">
                              <DropdownMenuItem className="text-[12.5px]">View</DropdownMenuItem>
                              <DropdownMenuItem className="text-[12.5px]">
                                <Icon name="edit" size="sm" color="muted" className="mr-1.5" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              {getChipState(course).state === "draft" && (
                                <DropdownMenuItem className="text-[12.5px]">
                                  <Icon name="publish" size="sm" color="muted" className="mr-1.5" />
                                  Publish
                                </DropdownMenuItem>
                              )}
                              {getChipState(course).state === "published" && (
                                <DropdownMenuItem className="text-[12.5px] text-[var(--amber)]">
                                  <Icon name="archived" size="sm" className="mr-1.5 text-[var(--amber)]" />
                                  Archive
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-[12.5px] text-[var(--red)]">
                                <Icon name="delete" size="sm" className="mr-1.5 text-[var(--red)]" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>

            {/* Pagination — desktop */}
            <div className="flex items-center justify-between px-4 py-[11px] border-t border-border">
              <div className="flex items-center gap-1.5 text-xs text-[var(--ink-3)]">
                Per page:
                <select
                  className="h-7 px-2 pr-5 rounded-[5px] border border-border text-xs font-medium bg-white text-[var(--ink-2)] outline-none cursor-pointer appearance-none bg-[image:url('data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20width=%228%22%20height=%225%22%20fill=%22none%22%3E%3Cpath%20d=%22M1%201l3%203%203-3%22%20stroke=%22%238C8C84%22%20stroke-width=%221.5%22%20stroke-linecap=%22round%22%20stroke-linejoin=%22round%22/%3E%3C/svg%3E')] bg-no-repeat bg-[right_5px_center]"
                  value={perPage}
                  onChange={e => { setPerPage(+e.target.value); setPage(1) }}
                >
                  <option>10</option><option>25</option><option>50</option><option>100</option>
                </select>
              </div>
              <p className="text-xs text-[var(--ink-3)]">
                Showing <strong className="text-[var(--ink-2)] font-semibold">{(page - 1) * perPage + 1}–{Math.min(page * perPage, filtered.length)}</strong> of <strong className="text-[var(--ink-2)] font-semibold">{filtered.length}</strong>
              </p>
              <div className="flex items-center gap-0.5">
                <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                  className="w-[30px] h-7 rounded-[6px] border border-border bg-white flex items-center justify-center text-xs font-semibold text-[var(--ink-2)] hover:bg-[var(--subtle)] hover:border-[var(--border-s)] disabled:opacity-30 disabled:cursor-default transition-all">
                  ‹
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  const p = i + 1
                  return (
                    <button key={p} onClick={() => setPage(p)}
                      className={cn(
                        "w-[30px] h-7 rounded-[6px] border text-xs font-semibold transition-all",
                        p === page
                          ? "bg-[var(--ink)] text-white border-[var(--ink)]"
                          : "bg-white text-[var(--ink-2)] border-border hover:bg-[var(--subtle)] hover:border-[var(--border-s)]"
                      )}>
                      {p}
                    </button>
                  )
                })}
                {totalPages > 5 && <span className="text-xs text-[var(--ink-4)] px-0.5">…</span>}
                <button disabled={page === totalPages || totalPages === 0} onClick={() => setPage(p => p + 1)}
                  className="w-[30px] h-7 rounded-[6px] border border-border bg-white flex items-center justify-center text-xs font-semibold text-[var(--ink-2)] hover:bg-[var(--subtle)] hover:border-[var(--border-s)] disabled:opacity-30 disabled:cursor-default transition-all">
                  ›
                </button>
              </div>
            </div>
          </div>

          {/* ── MOBILE CARD LIST ── */}
          <div className="md:hidden">
            {filtered.length === 0 ? (
              <div className="bg-white rounded-[18px] py-12 flex flex-col items-center text-center gap-2 shadow-[0_2px_12px_rgba(0,0,0,0.07),0_1px_3px_rgba(0,0,0,0.04)]">
                <Icon name="search" size="lg" color="muted" />
                <p className="text-sm font-semibold text-[var(--ink)]">No courses match your filters.</p>
                <button onClick={clearFilters} className="text-xs text-[var(--lms-accent)] font-semibold mt-0.5">Clear filters</button>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5 animate-fade-up">
                {filtered.slice(0, mobileLimit).map(course => (
                  <CourseCard
                    key={course.id}
                    course={course}
                    selected={selected.has(course.id)}
                    onToggle={() => toggleRow(course.id)}
                  />
                ))}
              </div>
            )}

            {/* Load more */}
            {mobileLimit < filtered.length && (
              <button
                onClick={() => setMobileLimit(l => l + 10)}
                className="w-full mt-4 h-11 rounded-[14px] bg-white text-[13px] font-semibold text-[var(--ink-2)] shadow-[0_2px_12px_rgba(0,0,0,0.07),0_1px_3px_rgba(0,0,0,0.04)] active:scale-[0.985] transition-all"
              >
                Load more · {filtered.length - mobileLimit} remaining
              </button>
            )}
            {mobileLimit >= filtered.length && filtered.length > 10 && (
              <p className="text-center text-[11px] text-[var(--ink-4)] mt-4">
                All {filtered.length} courses loaded
              </p>
            )}
          </div>

        </>)}

        {/* Dev state switcher — remove before production */}
        <div className="fixed bottom-[84px] left-1/2 -translate-x-1/2 bg-[var(--ink)] rounded-full px-1.5 py-1.5 flex gap-0.5 z-50 shadow-[var(--sh-lg)] md:bottom-5">
          {(["loaded", "skeleton", "empty", "error"] as const).map(s => (
            <button
              key={s}
              onClick={() => setViewState(s)}
              className={cn(
                "px-3 py-1 rounded-full text-[11px] font-bold transition-all",
                viewState === s ? "bg-white text-[var(--ink)]" : "text-white/40 hover:text-white/70"
              )}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>

      </main>

      {/* ── FAB — mobile only ── */}
      <button
        className="md:hidden fixed bottom-[76px] right-4 z-40 w-14 h-14 rounded-full bg-[var(--ink)] text-white flex items-center justify-center shadow-[0_4px_20px_rgba(0,0,0,0.22),0_2px_6px_rgba(0,0,0,0.14)] active:scale-[0.92] transition-all duration-150"
        aria-label="Create Course"
      >
        <Icon name="add" size="md" color="inverse" />
      </button>

      {/* ── BOTTOM TAB BAR — mobile only ── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 h-[64px] bg-white border-t border-border flex items-stretch">
        {BOTTOM_TABS.map(tab => (
          <button
            key={tab.label}
            onClick={tab.icon === "menu" ? () => setNavOpen(true) : undefined}
            className={cn(
              "flex-1 flex flex-col items-center justify-center gap-[3px] transition-colors relative",
              tab.active ? "text-[var(--ink)]" : "text-[var(--ink-4)]"
            )}
          >
            <Icon name={tab.icon} size="md" color={tab.active ? "default" : "muted"} />
            <span className={cn("text-[9.5px] font-semibold tracking-[0.01em]", tab.active && "font-bold")}>
              {tab.label}
            </span>
            {tab.active && (
              <span className="absolute top-1.5 w-1 h-1 rounded-full bg-[var(--ink)]" />
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}
