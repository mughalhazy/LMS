// ICON SYSTEM LAYER — v1.1
// Source: C:/LMS/UI/-- ICON_SYSTEM_LAYER--v1.md + design-system.md §7
// RULE: NO direct lucide-react imports outside this file.
// All icons via <Icon /> component only.

import {
  // Navigation & Structure
  BookOpen, Library, Home, LayoutDashboard, Settings, Menu, PanelLeft,
  ChevronRight, ChevronUp, ChevronDown, ArrowRight, ArrowLeft, ExternalLink,
  // Content & Learning
  FileText, Video, ClipboardList, ClipboardCheck, Award, Paperclip,
  Layers, Package, Radio, Tag, BookMarked, Route,
  // Actions & Controls
  Plus, Pencil, Trash2, Save, Send, Copy, Upload, Download,
  Search, Filter, ArrowUpDown, MoreHorizontal, X, GripVertical,
  // Status & Feedback
  CheckCircle, AlertTriangle, AlertCircle, Info, XCircle, Loader2,
  Check, Lock, Unlock, Asterisk, FileEdit, Archive,
  // Users & Roles
  User, Users, GraduationCap, UserCog, Briefcase, ShieldCheck,
  UsersRound, CircleUser, UserPlus, UserMinus,
  // Data & Analytics
  BarChart3, LineChart, PieChart, TrendingUp, TrendingDown, Gauge,
  Calendar, Clock, FileBarChart, FileDown,
  // Utility & System
  Bell, Mail, Link, RefreshCw, Maximize2, Minimize2,
  HelpCircle, Star, Flag,
} from "lucide-react"

import { cn } from "@/lib/utils"

// ── Design Tokens (locked) ──────────────────────────────────

const ICON_SIZE = {
  xs: "w-3 h-3",    // 12px — inline badges, dense indicators
  sm: "w-4 h-4",    // 16px — inline body text, chip icons
  md: "w-5 h-5",    // 20px — default: nav, buttons, card headers
  lg: "w-6 h-6",    // 24px — section headings, KPI cards
  xl: "w-8 h-8",    // 32px — empty states, hero actions
} as const

const ICON_COLOR = {
  primary:   "text-[var(--lms-accent)]",        // #5B5BD6
  secondary: "text-[var(--ink-2)]",              // #3D3D3A
  muted:     "text-[var(--ink-3)]",              // #6B6B63
  success:   "text-[var(--green-md)]",           // #16A34A
  warning:   "text-[var(--amber-md)]",           // #D97706
  danger:    "text-[var(--red-md)]",             // #DC2626
  inverse:   "text-white",
  ink:       "text-[var(--ink)]",               // #1A1A18
} as const

const ICON_WEIGHT = {
  light:   "stroke-[1]",
  regular: "stroke-[1.5]",
  bold:    "stroke-[2.5]",
} as const

const ICON_STATE = {
  default:  "",
  hover:    "group-hover:opacity-80",
  active:   "opacity-100",
  disabled: "opacity-40 pointer-events-none",
} as const

// ── Semantic Registry (60 icons) ────────────────────────────

const ICON_REGISTRY = {
  // Navigation & Structure
  course:          BookOpen,
  courses:         Library,
  home:            Home,
  dashboard:       LayoutDashboard,
  settings:        Settings,
  menu:            Menu,
  "sidebar-toggle": PanelLeft,
  "breadcrumb-sep": ChevronRight,
  collapse:        ChevronUp,
  expand:          ChevronDown,
  next:            ArrowRight,
  back:            ArrowLeft,
  external:        ExternalLink,
  // Content & Learning
  lesson:          FileText,
  video:           Video,
  quiz:            ClipboardList,
  assignment:      ClipboardCheck,
  certificate:     Award,
  resource:        Paperclip,
  module:          Layers,
  scorm:           Package,
  "live-session":  Radio,
  category:        Tag,
  library:         BookMarked,
  path:            Route,
  // Actions & Controls
  add:             Plus,
  edit:            Pencil,
  delete:          Trash2,
  save:            Save,
  publish:         Send,
  duplicate:       Copy,
  upload:          Upload,
  download:        Download,
  search:          Search,
  filter:          Filter,
  sort:            ArrowUpDown,
  more:            MoreHorizontal,
  close:           X,
  drag:            GripVertical,
  // Status & Feedback
  success:         CheckCircle,
  warning:         AlertTriangle,
  alert:           AlertCircle,
  info:            Info,
  error:           XCircle,
  loading:         Loader2,
  check:           Check,
  lock:            Lock,
  unlock:          Unlock,
  required:        Asterisk,
  draft:           FileEdit,
  archived:        Archive,
  // Users & Roles
  user:            User,
  users:           Users,
  learner:         GraduationCap,
  instructor:      UserCog,
  manager:         Briefcase,
  admin:           ShieldCheck,
  group:           UsersRound,
  profile:         CircleUser,
  enroll:          UserPlus,
  unenroll:        UserMinus,
  // Data & Analytics
  analytics:       BarChart3,
  "chart-line":    LineChart,
  "chart-pie":     PieChart,
  "trend-up":      TrendingUp,
  "trend-down":    TrendingDown,
  kpi:             Gauge,
  calendar:        Calendar,
  clock:           Clock,
  report:          FileBarChart,
  export:          FileDown,
  // Utility & System
  notification:    Bell,
  email:           Mail,
  link:            Link,
  refresh:         RefreshCw,
  fullscreen:      Maximize2,
  "exit-fullscreen": Minimize2,
  help:            HelpCircle,
  star:            Star,
  flag:            Flag,
} as const

export type IconName = keyof typeof ICON_REGISTRY

// ── Component API ────────────────────────────────────────────

type IconProps = {
  name: IconName
  size?:     keyof typeof ICON_SIZE
  color?:    keyof typeof ICON_COLOR
  weight?:   keyof typeof ICON_WEIGHT
  state?:    keyof typeof ICON_STATE
  className?: string
  ariaLabel?: string
  animated?:  boolean
}

export function Icon({
  name,
  size     = "md",
  color    = "primary",
  weight   = "regular",
  state    = "default",
  className,
  ariaLabel,
  animated = false,
}: IconProps) {
  const IconComponent = ICON_REGISTRY[name]

  return (
    <IconComponent
      className={cn(
        ICON_SIZE[size],
        ICON_COLOR[color],
        ICON_WEIGHT[weight],
        ICON_STATE[state],
        animated && name === "loading" && "animate-spin",
        className
      )}
      aria-label={ariaLabel}
      role={ariaLabel ? "img" : "presentation"}
    />
  )
}
