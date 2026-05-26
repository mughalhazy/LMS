"use client"

import Image from "next/image"
import { useState, useMemo, useCallback } from "react"
import {
  ChevronUp, ChevronDown, ChevronsUpDown,
  LayoutGrid, List as ListIcon,
  Cog, Shield, Target, Heart, Scale, DollarSign, ShoppingBag, BookOpen as BookOpenLucide,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
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

// ── Data ───────────────────────────────────────────────────────────────────

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

// ── Category config ────────────────────────────────────────────────────────

const CATEGORY_MAP: Record<string, { gradient: string; icon: React.ReactNode }> = {
  Engineering: { gradient: "from-blue-500 to-indigo-600",   icon: <Cog className="w-4 h-4" /> },
  Security:    { gradient: "from-red-500 to-rose-600",      icon: <Shield className="w-4 h-4" /> },
  Product:     { gradient: "from-purple-500 to-violet-600", icon: <Target className="w-4 h-4" /> },
  HR:          { gradient: "from-teal-500 to-cyan-600",     icon: <Heart className="w-4 h-4" /> },
  Compliance:  { gradient: "from-amber-500 to-orange-600",  icon: <Scale className="w-4 h-4" /> },
  Finance:     { gradient: "from-emerald-500 to-green-700", icon: <DollarSign className="w-4 h-4" /> },
  Sales:       { gradient: "from-orange-500 to-amber-600",  icon: <ShoppingBag className="w-4 h-4" /> },
  Operations:  { gradient: "from-slate-500 to-gray-700",    icon: <Cog className="w-4 h-4" /> },
}

function getCat(category: string | null) {
  return CATEGORY_MAP[category ?? ""] ?? {
    gradient: "from-gray-400 to-gray-600",
    icon: <BookOpenLucide className="w-4 h-4" />,
  }
}

// ── Status badge (card overlay variant) ───────────────────────────────────

function CardStatusBadge({ course }: { course: Course }) {
  const { state, label } = getChipState(course)
  return (
    <span className={cn(
      "text-[9.5px] font-bold uppercase tracking-[0.06em] px-2 py-0.5 rounded-full border",
      state === "published"  ? "bg-green-500/25 text-green-50 border-green-400/40" :
      state === "scheduled"  ? "bg-cyan-500/25 text-cyan-50 border-cyan-400/40" :
      state === "archived"   ? "bg-white/10 text-white/50 border-white/20" :
                               "bg-white/20 text-white/80 border-white/30"
    )}>
      {label}
    </span>
  )
}

// ── Completion bar ─────────────────────────────────────────────────────────

function CompletionBar({ pct }: { pct: number | null }) {
  if (pct === null) return <div className="h-1.5 bg-gray-100 rounded-full mt-3 opacity-30" />
  const color = pct >= 75 ? "#22c55e" : pct >= 50 ? "#f59e0b" : "#ef4444"
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Progress</span>
        <span className="text-[11px] font-bold tabular-nums" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

// ── Course grid card ───────────────────────────────────────────────────────

function CourseGridCard({ course }: { course: Course }) {
  const cat = getCat(course.category)
  const { state } = getChipState(course)

  return (
    <div className="group bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.06),0_1px_3px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_32px_rgba(0,0,0,0.1),0_2px_8px_rgba(0,0,0,0.05)] hover:-translate-y-[2px] transition-all duration-200">

      {/* Gradient header */}
      <div className={cn("relative h-[108px] bg-gradient-to-br p-3.5 flex flex-col justify-between", cat.gradient)}>
        <div className="flex items-start justify-between">
          <div className="w-8 h-8 rounded-xl bg-white/25 flex items-center justify-center text-white shrink-0">
            {cat.icon}
          </div>
          <CardStatusBadge course={course} />
        </div>
        <div className="flex items-end justify-between gap-2">
          <span className="text-[9.5px] font-bold uppercase tracking-[0.06em] px-2 py-0.5 rounded-full bg-white/15 border border-white/25 text-white/90">
            {getModeLabel(course.mode)}
          </span>
          {course.category && (
            <span className="text-[10px] font-semibold text-white/70 truncate">{course.category}</span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="p-4">
        <h3 className="text-[14px] font-bold text-gray-900 leading-snug group-hover:text-indigo-600 transition-colors truncate">
          {course.title}
        </h3>
        <p className="text-[11px] text-gray-400 font-mono mt-0.5 mb-3 truncate">
          {course.code ? `#${course.code}` : " "}
        </p>

        {/* Stats row */}
        <div className="flex items-center gap-3 text-[11.5px] text-gray-500">
          <span className="flex items-center gap-1">
            <Icon name="clock" size="xs" color="muted" />
            {fmtDuration(course.duration)}
          </span>
          <span className="flex items-center gap-1">
            <Icon name="users" size="xs" color="muted" />
            {course.enrollments.toLocaleString()}
          </span>
        </div>

        <CompletionBar pct={course.completion} />

        {/* Card footer */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
          <span className="text-[11px] text-gray-400 truncate">{course.updated}</span>
          <DropdownMenu>
            <DropdownMenuTrigger className="w-7 h-7 inline-flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors outline-none shrink-0">
              <Icon name="more" size="sm" color="muted" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-[148px]">
              <DropdownMenuItem className="text-[12.5px]">View Course</DropdownMenuItem>
              <DropdownMenuItem className="text-[12.5px]">
                <Icon name="edit" size="sm" color="muted" className="mr-1.5" />Edit
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {state === "draft" && (
                <DropdownMenuItem className="text-[12.5px]">
                  <Icon name="publish" size="sm" color="muted" className="mr-1.5" />Publish
                </DropdownMenuItem>
              )}
              {state === "published" && (
                <DropdownMenuItem className="text-[12.5px] text-amber-600">
                  <Icon name="archived" size="sm" className="mr-1.5 text-amber-600" />Archive
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-[12.5px] text-red-600">
                <Icon name="delete" size="sm" className="mr-1.5 text-red-600" />Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}

// ── Stat card ──────────────────────────────────────────────────────────────

function StatCard({
  icon, label, value, sub, bg,
}: {
  icon: React.ReactNode; label: string; value: string; sub?: string; bg: string
}) {
  return (
    <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)] flex items-center gap-3">
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center shrink-0", bg)}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[10.5px] font-semibold text-gray-400 uppercase tracking-wider truncate">{label}</p>
        <p className="text-[22px] font-black text-gray-900 leading-none mt-0.5">{value}</p>
        {sub && <p className="text-[10.5px] text-gray-400 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  )
}

// ── Sort header for list view ──────────────────────────────────────────────

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
        "cursor-pointer select-none whitespace-nowrap text-[10.5px] font-bold uppercase tracking-[0.06em] text-gray-400 h-[36px] hover:text-gray-700 transition-colors",
        align === "right" && "text-right",
      )}
      onClick={() => onSort(col)}
    >
      <span className="inline-flex items-center gap-0.5">
        {label}
        {active ? (
          currentDir === "asc"
            ? <ChevronUp className="w-3 h-3 shrink-0" />
            : <ChevronDown className="w-3 h-3 shrink-0" />
        ) : (
          <ChevronsUpDown className="w-3 h-3 shrink-0 opacity-35" />
        )}
      </span>
    </TableHead>
  )
}

// ── Status chip for list view ──────────────────────────────────────────────

function ListStatusChip({ course }: { course: Course }) {
  const { state, label } = getChipState(course)
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-semibold border whitespace-nowrap",
      "before:content-[''] before:w-[5px] before:h-[5px] before:rounded-full before:bg-current",
      state === "published"  ? "bg-green-50 border-green-200 text-green-700" :
      state === "scheduled"  ? "bg-cyan-50 border-cyan-200 text-cyan-700" :
      state === "archived"   ? "bg-gray-100 border-gray-200 text-gray-500 opacity-70" :
                               "bg-gray-100 border-gray-200 text-gray-500"
    )}>
      {label}
    </span>
  )
}

// ── Nav items ──────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { label: "Dashboard",     icon: "dashboard"    as const },
  { label: "Courses",       icon: "courses"      as const, active: true },
  { label: "Users",         icon: "users"        as const },
  { label: "Organizations", icon: "home"         as const },
  { label: "Reports",       icon: "analytics"    as const },
  { label: "Compliance",    icon: "admin"        as const },
  { label: "Settings",      icon: "settings"     as const },
  { label: "Alerts",        icon: "notification" as const, badge: 7 },
]

const BOTTOM_TABS = [
  { label: "Dashboard", icon: "dashboard" as const },
  { label: "Courses",   icon: "courses"   as const, active: true },
  { label: "Users",     icon: "users"     as const },
  { label: "Reports",   icon: "analytics" as const },
  { label: "More",      icon: "menu"      as const },
]

// ── Page scope: override --primary to indigo ───────────────────────────────

const PAGE_SCOPE = {
  "--primary":            "#5b5bd6",
  "--primary-foreground": "#ffffff",
  "--ring":               "rgba(91,91,214,0.4)",
} as React.CSSProperties

// ── Main page ──────────────────────────────────────────────────────────────

export default function CoursesV2Page() {
  const [view, setView]         = useState<"grid" | "list">("grid")
  const [viewState, setViewState] = useState<"loaded" | "skeleton" | "empty" | "error">("loaded")
  const [query, setQuery]       = useState("")
  const [statusFilter, setStatus]   = useState("")
  const [deliveryFilter, setDelivery] = useState("")
  const [sortCol, setSortCol]   = useState("updated")
  const [sortDir, setSortDir]   = useState<"asc" | "desc">("desc")
  const [page, setPage]         = useState(1)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const perPage = view === "grid" ? 12 : 15

  // ── Filter + sort ──
  const filtered = useMemo(() => {
    let rows = COURSES
    if (query)          rows = rows.filter(c => c.title.toLowerCase().includes(query.toLowerCase()) || c.code?.toLowerCase().includes(query.toLowerCase()))
    if (statusFilter)   rows = rows.filter(c => getChipState(c).state === statusFilter)
    if (deliveryFilter) rows = rows.filter(c => c.mode === deliveryFilter)

    rows = [...rows].sort((a, b) => {
      let av: string | number = 0, bv: string | number = 0
      if (sortCol === "title")       { av = a.title;       bv = b.title }
      if (sortCol === "updated")     { av = a.updated;     bv = b.updated }
      if (sortCol === "enrollments") { av = a.enrollments; bv = b.enrollments }
      if (sortCol === "status")      { av = getChipState(a).state; bv = getChipState(b).state }
      return av < bv ? (sortDir === "asc" ? -1 : 1) : av > bv ? (sortDir === "asc" ? 1 : -1) : 0
    })
    return rows
  }, [query, statusFilter, deliveryFilter, sortCol, sortDir])

  const pageRows   = filtered.slice((page - 1) * perPage, page * perPage)
  const totalPages = Math.ceil(filtered.length / perPage)
  const hasFilters = Boolean(query || statusFilter || deliveryFilter)

  // ── Stats ──
  const totalEnrolled  = COURSES.reduce((s, c) => s + c.enrollments, 0)
  const publishedCount = COURSES.filter(c => c.status === "published" && c.pub_status === "published").length
  const draftCount     = COURSES.filter(c => c.status === "draft").length
  const withCompletion = COURSES.filter(c => c.completion !== null)
  const avgCompletion  = withCompletion.length > 0
    ? Math.round(withCompletion.reduce((s, c) => s + (c.completion ?? 0), 0) / withCompletion.length)
    : 0

  const clearFilters = useCallback(() => { setQuery(""); setStatus(""); setDelivery(""); setPage(1) }, [])

  function handleSort(col: string) {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortCol(col); setSortDir("desc") }
    setPage(1)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex" style={PAGE_SCOPE}>

      {/* ── SIDEBAR — desktop ── */}
      <aside className="hidden lg:flex flex-col w-[220px] shrink-0 bg-[#1a1a18] min-h-screen sticky top-0 h-screen overflow-y-auto z-50">
        {/* Logo */}
        <div className="px-5 pt-5 pb-4 border-b border-white/10">
          <Image
            src="/nucleus-logo.png"
            alt="Nucleus LMS"
            width={110} height={36}
            className="h-8 w-auto object-contain brightness-0 invert"
            priority
          />
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2.5 flex flex-col gap-0.5">
          {NAV_ITEMS.map(item => (
            <button
              key={item.label}
              className={cn(
                "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-150 text-left group",
                item.active
                  ? "bg-[#5b5bd6] text-white font-semibold shadow-[0_3px_12px_rgba(91,91,214,0.45)]"
                  : "text-white/55 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon
                name={item.icon}
                size="sm"
                color={item.active ? "inverse" : "muted"}
                className={item.active ? "" : "group-hover:text-white transition-colors"}
              />
              <span className="flex-1 truncate">{item.label}</span>
              {item.badge && (
                <span className="text-[9px] font-bold bg-red-500 text-white px-1.5 py-0.5 rounded-full leading-none">
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* User */}
        <div className="px-2.5 py-3 border-t border-white/10">
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-white/10 transition-colors cursor-pointer">
            <Avatar size="sm">
              <AvatarFallback className="text-[10px] font-bold" style={{ background: "#5b5bd6", color: "#fff" }}>AK</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] font-semibold text-white truncate">Admin User</p>
              <p className="text-[10px] text-white/40 truncate">Acme Corp · Admin</p>
            </div>
            <Icon name="expand" size="xs" className="text-white/30 shrink-0" />
          </div>
        </div>
      </aside>

      {/* ── MOBILE NAV SHEET ── */}
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-[240px] p-0 bg-[#1a1a18] border-r border-white/10">
          <SheetHeader className="px-5 py-4 border-b border-white/10">
            <SheetTitle className="flex items-center">
              <Image src="/nucleus-logo.png" alt="Nucleus LMS" width={100} height={32} className="h-8 w-auto object-contain brightness-0 invert" />
            </SheetTitle>
          </SheetHeader>
          <nav className="py-3 px-2.5 flex flex-col gap-0.5">
            {NAV_ITEMS.map(item => (
              <button
                key={item.label}
                onClick={() => setMobileNavOpen(false)}
                className={cn(
                  "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all text-left",
                  item.active ? "bg-[#5b5bd6] text-white font-semibold" : "text-white/55 hover:bg-white/10 hover:text-white"
                )}
              >
                <Icon name={item.icon} size="sm" color={item.active ? "inverse" : "muted"} />
                <span className="flex-1 truncate">{item.label}</span>
                {item.badge && (
                  <span className="text-[9px] font-bold bg-red-500 text-white px-1.5 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </SheetContent>
      </Sheet>

      {/* ── MAIN AREA ── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* ── TOP HEADER ── */}
        <header className="h-14 bg-white border-b border-gray-100 flex items-center px-4 lg:px-6 gap-3 sticky top-0 z-40 shadow-[0_1px_4px_rgba(0,0,0,0.04)]">
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileNavOpen(true)}
            className="lg:hidden w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
          >
            <Icon name="menu" size="sm" color="muted" />
          </button>

          {/* Mobile logo */}
          <div className="lg:hidden shrink-0">
            <Image src="/nucleus-logo.png" alt="Nucleus" width={80} height={28} className="h-7 w-auto object-contain" />
          </div>

          {/* Desktop search */}
          <div className="hidden lg:flex flex-1 max-w-sm relative">
            <Icon name="search" size="sm" color="muted" className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <Input
              className="pl-9 h-9 text-[13px] bg-gray-50 border-gray-200 rounded-xl"
              placeholder="Search courses, codes…"
              value={query}
              onChange={e => { setQuery(e.target.value); setPage(1) }}
            />
          </div>

          <div className="ml-auto flex items-center gap-2">
            {/* Notification */}
            <button className="relative w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors">
              <Icon name="notification" size="sm" color="muted" />
              <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-red-500 border-2 border-white" />
            </button>
            <Button variant="outline" size="sm" className="hidden md:inline-flex gap-1.5 h-8 text-[12px] rounded-lg border-gray-200">
              <Icon name="upload" size="xs" color="muted" />
              Import
            </Button>
            <Button size="sm" className="gap-1.5 h-8 text-[12px] rounded-lg">
              <Icon name="add" size="xs" color="inverse" />
              <span className="hidden sm:inline">New Course</span>
            </Button>
            <Avatar size="sm" className="cursor-pointer">
              <AvatarFallback className="text-[10px] font-bold" style={{ background: "#5b5bd6", color: "#fff" }}>AK</AvatarFallback>
            </Avatar>
          </div>
        </header>

        {/* ── CANVAS ── */}
        <main className="flex-1 p-4 lg:p-6 pb-28 lg:pb-8 w-full max-w-[1280px] mx-auto">

          {/* Page heading */}
          <div className="flex items-start justify-between mb-5">
            <div>
              <h1 className="text-xl font-black tracking-[-0.03em] text-gray-900">Course Library</h1>
              <p className="text-[12.5px] text-gray-400 mt-0.5">
                {COURSES.length} courses &middot; {publishedCount} published &middot; {draftCount} drafts
              </p>
            </div>
            <Button variant="outline" size="sm" className="hidden md:inline-flex gap-1.5 h-8 text-[12px] rounded-lg border-gray-200">
              <Icon name="export" size="xs" color="muted" />
              Export CSV
            </Button>
          </div>

          {/* ── STATS STRIP ── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <StatCard
              icon={<Icon name="courses" size="sm" color="primary" />}
              label="Total Courses" value={String(COURSES.length)} sub={`${draftCount} drafts`}
              bg="bg-indigo-50"
            />
            <StatCard
              icon={<Icon name="check" size="sm" color="success" />}
              label="Published" value={String(publishedCount)} sub="live now"
              bg="bg-green-50"
            />
            <StatCard
              icon={<Icon name="users" size="sm" color="secondary" />}
              label="Total Enrolled" value={totalEnrolled.toLocaleString()} sub="across all courses"
              bg="bg-blue-50"
            />
            <StatCard
              icon={<Icon name="trend-up" size="sm" color="warning" />}
              label="Avg Completion" value={`${avgCompletion}%`} sub="active courses"
              bg="bg-amber-50"
            />
          </div>

          {/* ── FILTER BAR ── */}
          <div className="bg-white border border-gray-100 rounded-2xl px-4 py-3 flex flex-wrap items-center gap-2 mb-5 shadow-[0_1px_4px_rgba(0,0,0,0.04)]">

            {/* Mobile search */}
            <div className="lg:hidden w-full relative">
              <Icon name="search" size="sm" color="muted" className="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <Input
                className="pl-8 h-8 text-[12.5px] bg-gray-50 border-gray-200 rounded-lg"
                placeholder="Search courses…"
                value={query}
                onChange={e => { setQuery(e.target.value); setPage(1) }}
              />
            </div>

            {/* Status pills */}
            {(["", "published", "draft", "scheduled", "archived"] as const).map(val => (
              <button
                key={val}
                onClick={() => { setStatus(val); setPage(1) }}
                className={cn(
                  "h-7 px-3 rounded-full text-[11.5px] font-semibold whitespace-nowrap transition-all duration-150",
                  statusFilter === val
                    ? "bg-[#5b5bd6] text-white shadow-[0_2px_8px_rgba(91,91,214,0.3)]"
                    : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700"
                )}
              >
                {val === "" ? "All" : val.charAt(0).toUpperCase() + val.slice(1)}
              </button>
            ))}

            <div className="w-px h-5 bg-gray-200 mx-0.5 hidden sm:block shrink-0" />

            {/* Delivery pills */}
            {([
              { val: "self_paced", label: "Self-paced" },
              { val: "instructor_led", label: "Instructor-led" },
              { val: "blended", label: "Blended" },
            ] as const).map(f => (
              <button
                key={f.val}
                onClick={() => { setDelivery(deliveryFilter === f.val ? "" : f.val); setPage(1) }}
                className={cn(
                  "h-7 px-3 rounded-full text-[11.5px] font-semibold whitespace-nowrap transition-all duration-150",
                  deliveryFilter === f.val
                    ? "bg-gray-900 text-white"
                    : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700"
                )}
              >
                {f.label}
              </button>
            ))}

            {/* Right side: count + clear + view toggle */}
            <div className="flex items-center gap-2 ml-auto shrink-0">
              {hasFilters && (
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-1 text-[11px] font-semibold text-red-500 hover:text-red-700 transition-colors"
                >
                  <Icon name="close" size="xs" className="text-red-500" />
                  Clear
                </button>
              )}
              <span className="text-[11.5px] font-bold text-gray-400 whitespace-nowrap">
                {filtered.length} {filtered.length === 1 ? "course" : "courses"}
              </span>

              {/* View toggle */}
              <div className="flex items-center bg-gray-100 rounded-lg p-0.5 gap-0.5 shrink-0">
                <button
                  onClick={() => { setView("grid"); setPage(1) }}
                  className={cn(
                    "w-7 h-7 flex items-center justify-center rounded-md transition-all",
                    view === "grid" ? "bg-white shadow-sm text-gray-800" : "text-gray-400 hover:text-gray-600"
                  )}
                  title="Grid view"
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => { setView("list"); setPage(1) }}
                  className={cn(
                    "w-7 h-7 flex items-center justify-center rounded-md transition-all",
                    view === "list" ? "bg-white shadow-sm text-gray-800" : "text-gray-400 hover:text-gray-600"
                  )}
                  title="List view"
                >
                  <ListIcon className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* ── SKELETON ── */}
          {viewState === "skeleton" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                  <Skeleton className="h-[108px] w-full rounded-none" />
                  <div className="p-4 flex flex-col gap-2.5">
                    <Skeleton className="h-4 w-3/4 rounded-lg" />
                    <Skeleton className="h-3 w-1/3 rounded-lg" />
                    <div className="flex gap-3">
                      <Skeleton className="h-3 w-10 rounded-lg" />
                      <Skeleton className="h-3 w-14 rounded-lg" />
                    </div>
                    <Skeleton className="h-1.5 w-full rounded-full mt-2" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── EMPTY ── */}
          {viewState === "empty" && (
            <div className="bg-white rounded-2xl border border-gray-100 py-20 flex flex-col items-center text-center gap-3 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center">
                <Icon name="courses" size="lg" color="primary" />
              </div>
              <div>
                <p className="text-[15px] font-bold text-gray-900 mb-1">No courses yet</p>
                <p className="text-sm text-gray-400 max-w-xs leading-relaxed">
                  Create your first course to start building your learning catalog.
                </p>
              </div>
              <Button size="sm" className="mt-1 gap-1.5 rounded-xl">
                <Icon name="add" size="sm" color="inverse" />
                Create Course
              </Button>
            </div>
          )}

          {/* ── ERROR ── */}
          {viewState === "error" && (
            <div className="bg-white rounded-2xl border border-gray-100 py-16 flex flex-col items-center text-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center">
                <Icon name="error" size="md" color="danger" />
              </div>
              <div>
                <p className="text-sm font-bold text-gray-900 mb-0.5">Couldn&apos;t load courses.</p>
                <p className="text-xs text-gray-400">course-service may be unavailable.</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => setViewState("loaded")} className="gap-1.5 rounded-xl border-gray-200">
                <Icon name="refresh" size="sm" color="muted" />
                Try Again
              </Button>
            </div>
          )}

          {/* ── LOADED ── */}
          {viewState === "loaded" && (<>

            {pageRows.length === 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 py-14 flex flex-col items-center text-center gap-2 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                <Icon name="search" size="lg" color="muted" />
                <p className="text-sm font-semibold text-gray-700">No courses match your filters.</p>
                <button onClick={clearFilters} className="text-xs text-indigo-600 font-semibold mt-0.5 hover:underline">
                  Clear filters
                </button>
              </div>
            )}

            {/* ── GRID VIEW ── */}
            {view === "grid" && pageRows.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {pageRows.map(course => (
                  <CourseGridCard key={course.id} course={course} />
                ))}
              </div>
            )}

            {/* ── LIST VIEW ── */}
            {view === "list" && pageRows.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader className="bg-gray-50/80">
                      <TableRow className="border-b border-gray-100 hover:bg-transparent">
                        <SortHeader col="title"       label="Course"       currentCol={sortCol} currentDir={sortDir} onSort={handleSort} />
                        <SortHeader col="status"      label="Status"       currentCol={sortCol} currentDir={sortDir} onSort={handleSort} />
                        <TableHead className="text-[10.5px] font-bold uppercase tracking-[0.06em] text-gray-400 h-[36px] whitespace-nowrap">Category</TableHead>
                        <TableHead className="text-[10.5px] font-bold uppercase tracking-[0.06em] text-gray-400 h-[36px] whitespace-nowrap">Mode</TableHead>
                        <SortHeader col="enrollments" label="Enrolled"     currentCol={sortCol} currentDir={sortDir} onSort={handleSort} align="right" />
                        <TableHead className="text-[10.5px] font-bold uppercase tracking-[0.06em] text-gray-400 h-[36px] whitespace-nowrap">Completion</TableHead>
                        <SortHeader col="updated"     label="Updated"      currentCol={sortCol} currentDir={sortDir} onSort={handleSort} />
                        <TableHead className="w-10" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pageRows.map(course => {
                        const cat = getCat(course.category)
                        return (
                          <TableRow
                            key={course.id}
                            className="border-b border-gray-50 h-[52px] hover:bg-indigo-50/40 transition-colors cursor-pointer"
                          >
                            <TableCell>
                              <div className="flex items-center gap-2.5">
                                <div className={cn("w-7 h-7 rounded-lg bg-gradient-to-br flex items-center justify-center text-white shrink-0", cat.gradient)}>
                                  <span className="scale-75">{cat.icon}</span>
                                </div>
                                <div className="min-w-0">
                                  <div className="text-[13px] font-semibold text-gray-900 truncate max-w-[200px]">{course.title}</div>
                                  {course.code && <div className="text-[10.5px] text-gray-400 font-mono">#{course.code}</div>}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell><ListStatusChip course={course} /></TableCell>
                            <TableCell className="text-[12px] text-gray-600">{course.category ?? "—"}</TableCell>
                            <TableCell className="text-[12px] text-gray-500">{getModeLabel(course.mode)}</TableCell>
                            <TableCell className="text-right text-[13px] font-semibold text-gray-700 tabular-nums">{course.enrollments.toLocaleString()}</TableCell>
                            <TableCell>
                              {course.completion !== null ? (
                                <div className="flex items-center gap-1.5">
                                  <div className="w-14 h-1.5 bg-gray-100 rounded-full overflow-hidden shrink-0">
                                    <div
                                      className="h-1.5 rounded-full"
                                      style={{
                                        width: `${course.completion}%`,
                                        backgroundColor: course.completion >= 75 ? "#22c55e" : course.completion >= 50 ? "#f59e0b" : "#ef4444"
                                      }}
                                    />
                                  </div>
                                  <span className="text-[12px] font-semibold text-gray-600 tabular-nums">{course.completion}%</span>
                                </div>
                              ) : (
                                <span className="text-gray-300 text-sm">—</span>
                              )}
                            </TableCell>
                            <TableCell className="text-[12px] text-gray-400 whitespace-nowrap">{course.updated}</TableCell>
                            <TableCell className="w-10" onClick={e => e.stopPropagation()}>
                              <DropdownMenu>
                                <DropdownMenuTrigger className="w-7 h-7 inline-flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors outline-none">
                                  <Icon name="more" size="sm" color="muted" />
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="min-w-[148px]">
                                  <DropdownMenuItem className="text-[12.5px]">View</DropdownMenuItem>
                                  <DropdownMenuItem className="text-[12.5px]">Edit</DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem className="text-[12.5px] text-red-600">Delete</DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}

            {/* ── PAGINATION ── */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-1.5 mt-6">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="w-8 h-8 rounded-lg border border-gray-200 bg-white flex items-center justify-center text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-default transition-all"
                >
                  ‹
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map(p => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={cn(
                      "w-8 h-8 rounded-lg border text-[12px] font-semibold transition-all",
                      p === page
                        ? "bg-[#5b5bd6] text-white border-[#5b5bd6] shadow-[0_2px_8px_rgba(91,91,214,0.35)]"
                        : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
                    )}
                  >
                    {p}
                  </button>
                ))}
                {totalPages > 5 && <span className="text-xs text-gray-400 px-0.5">…</span>}
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                  className="w-8 h-8 rounded-lg border border-gray-200 bg-white flex items-center justify-center text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-default transition-all"
                >
                  ›
                </button>
              </div>
            )}

          </>)}

          {/* Dev state switcher */}
          <div className="fixed bottom-[84px] left-1/2 -translate-x-1/2 bg-gray-900 rounded-full px-1.5 py-1.5 flex gap-0.5 z-50 shadow-xl lg:bottom-5">
            {(["loaded", "skeleton", "empty", "error"] as const).map(s => (
              <button
                key={s}
                onClick={() => setViewState(s)}
                className={cn(
                  "px-3 py-1 rounded-full text-[11px] font-bold transition-all",
                  viewState === s ? "bg-white text-gray-900" : "text-white/40 hover:text-white/70"
                )}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>

        </main>
      </div>

      {/* ── FAB — mobile ── */}
      <button
        className="lg:hidden fixed bottom-[76px] right-4 z-40 w-14 h-14 rounded-full text-white flex items-center justify-center shadow-[0_4px_24px_rgba(91,91,214,0.45)] active:scale-[0.92] transition-all duration-150"
        style={{ background: "#5b5bd6" }}
        aria-label="Create Course"
      >
        <Icon name="add" size="md" color="inverse" />
      </button>

      {/* ── BOTTOM TAB BAR — mobile ── */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-30 h-[64px] bg-white border-t border-gray-100 flex items-stretch">
        {BOTTOM_TABS.map(tab => (
          <button
            key={tab.label}
            onClick={tab.icon === "menu" ? () => setMobileNavOpen(true) : undefined}
            className={cn(
              "flex-1 flex flex-col items-center justify-center gap-[3px] transition-colors relative",
              tab.active ? "text-[#5b5bd6]" : "text-gray-400"
            )}
          >
            <Icon name={tab.icon} size="md" color={tab.active ? "primary" : "muted"} />
            <span className={cn("text-[9.5px] font-semibold tracking-[0.01em]", tab.active && "font-bold")}>
              {tab.label}
            </span>
            {tab.active && (
              <span className="absolute top-1.5 w-1 h-1 rounded-full" style={{ background: "#5b5bd6" }} />
            )}
          </button>
        ))}
      </nav>

    </div>
  )
}
