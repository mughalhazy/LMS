# LMS PLATFORM — DESIGN SYSTEM
**Product name:** Meridian LMS
**Version:** 2.0 | **Date:** 2026-04-14
**Sources:** Pattern extraction (52 pages) + Design Language v1.4 FINAL

---

## HOW TO USE
- Tokens (§1) are the single source of truth — no hardcoded values anywhere
- Shells (§2) define page-level layout per archetype
- Components (§3) define reusable primitives and composites
- Motion (§4) defines all animation/transition behaviour
- Interaction rules (§5) are laws — not guidelines
- Open issues (§6) must be resolved before any surface ships

---

## §1 TOKENS

### 1.1 Color

**The 4-state rule:** Every semantic color exists in four states — `dk` (text), `md` (fill/accent), `lt` (background tint), `bd` (border, rgba-based). Use only within their designated role.

```css
:root {
  /* Canvas & surfaces */
  --canvas:     #F7F7F5;   /* Page background — warm off-white, not cold grey */
  --white:      #FFFFFF;   /* Cards, panels, tables */
  --subtle:     #F2F2F0;   /* Hover states, table headers */
  --muted:      #EEEEEC;   /* Secondary surface, nested bg */
  --border:     #E8E8E4;   /* Default borders — structure only, never colored */
  --border-s:   #D8D8D2;   /* Strong borders, dividers */
  --border-focus: #5B5BD6; /* Input focus ring */

  /* Ink (text only — never accents or backgrounds) */
  --ink:   #1A1A18;
  --ink-2: #52524E;
  --ink-3: #8C8C84;
  --ink-4: #C0C0B8;

  /* Indigo — primary action · courses · learning */
  --accent:    #5B5BD6;   /* md — fill, active states, focus */
  --accent-lt: #F0F0FF;   /* lt — selected bg, tints */
  --accent-dk: #1E1B4B;   /* dk — text on light bg */
  /* bd = rgba(91,91,214,.14) */

  /* Forest — progress · completion · success */
  --green:    #166534;    /* dk — text */
  --green-md: #16A34A;    /* md — fills, progress bars >= 80% */
  --green-bg: #DCFCE7;    /* lt — backgrounds */
  --green-bd: rgba(22,163,74,.14);

  /* Amber — warning · due soon · attention */
  --amber:    #92400E;    /* dk — text */
  --amber-md: #D97706;    /* md — fills, progress bars < 50% */
  --amber-bg: #FEF3C7;    /* lt — backgrounds */
  --amber-bd: rgba(217,119,6,.14);

  /* Brick — error · critical · destructive · overdue */
  --red:    #991B1B;      /* dk — text */
  --red-md: #DC2626;      /* md — fills, overdue states */
  --red-bg: #FEE2E2;      /* lt — backgrounds */
  --red-bd: rgba(220,38,38,.14);

  /* Gold — achievement · certificates · reward */
  --gold:    #78350F;     /* dk — text */
  --gold-md: #F59E0B;     /* md — fills */
  --gold-bg: #FFFBEB;     /* lt — backgrounds */
  --gold-bd: rgba(245,158,11,.14);

  /* Teal — live · sync · real-time · active session */
  --teal:    #134E4A;     /* dk — text */
  --teal-md: #0D9488;     /* md — fills */
  --teal-bg: #CCFBF1;     /* lt — backgrounds */
  --teal-bd: rgba(13,148,136,.14);

  --font: 'Plus Jakarta Sans', system-ui, sans-serif;

  /* Elevation */
  --sh-xs:     0 1px 2px rgba(0,0,0,.04);
  --sh-sm:     0 1px 4px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --sh-md:     0 4px 16px rgba(0,0,0,.08), 0 2px 6px rgba(0,0,0,.04);
  --sh-lg:     0 12px 40px rgba(0,0,0,.10), 0 4px 12px rgba(0,0,0,.05);
  --sh-xl:     0 24px 64px rgba(0,0,0,.14), 0 8px 24px rgba(0,0,0,.07);
  --sh-indigo: 0 6px 20px rgba(91,91,214,.18);

  /* Radius */
  --r:      14px;
  --r-sm:   7px;
  --r-pill: 999px;
}
```

**The 80/12/8 rule:** 80% neutral · 12% indigo · 8% semantic signals. More than 3 colors simultaneously on one surface = too many.

---

### 1.2 Typography

**Typeface:** Plus Jakarta Sans exclusively.

| Role | Size | Weight | Letter-spacing | Transform | Usage |
|---|---|---|---|---|---|
| Display | 28–32px | 800 | -0.03em | — | Auth, empty states — 1 per page max |
| Page Title | 24px | 800 | -0.03em | — | H1 — one per page |
| Section Title | 16px | 700 | -0.01em | — | Card titles, major headings |
| Panel Title | 13px | 700 | -0.01em | — | Sub-sections, panel headers |
| Body | 14px | 500 | 0 | — | Descriptions, lesson content |
| Meta | 11–12px | 500 | 0 | — | Timestamps, secondary labels |
| Label | 10px | 700 | +0.06em | UPPERCASE | Column headers, nav section labels |

**KPI sizes:** 48px 800 -0.04em (large) · 32px 800 -0.04em (secondary) · 24px 800 -0.04em (admin tertiary)

---

### 1.3 Spacing

**Base unit: 8px.** No deviations.

| Token | Value | Usage |
|---|---|---|
| space-1 | 4px | Micro gap — icon to text, dot to label |
| space-2 | 8px | Tight — within a component |
| space-3 | 12px | Internal breathing room |
| space-4 | 16px | Between related elements |
| space-5 | 24px | Card padding standard, panel gap |
| space-6 | 32px | Between components, page side padding |
| space-7 | 48px | Section separation — the premium signal |
| space-8 | 64px | Hero areas — maximum 1 per page |

**Surface-specific density** (replaces zoom:1.25 hack):

| Surface | Page Pad | Section Gap | Row Height | Tone |
|---|---|---|---|---|
| Learner | 32px | 48px | 56px | Motivational · progress-forward |
| Instructor | 32px | 40px | 52px | Productive · editorial |
| Manager | 32px | 40px | 48px | Analytical · executive |
| Admin | 28px | 20px | 40px | Operational · triage |

---

### 1.4 Elevation

| Token | Value | Usage |
|---|---|---|
| --sh-xs | 0 1px 2px .04 | Flat rows, static elements |
| --sh-sm | 0 1px 4px .06 / 1px 2px .04 | Cards, panels — default resting |
| --sh-md | 0 4px 16px .08 / 2px 6px .04 | Hover, dropdowns |
| --sh-lg | 0 12px 40px .10 / 4px 12px .05 | Drawers, floating panels |
| --sh-xl | 0 24px 64px .14 / 8px 24px .07 | Modals, hero blocks |
| --sh-indigo | 0 6px 20px rgba(91,91,214,.18) | Primary CTA button only |

---

### 1.5 Border Radius

| Token | Value | Usage |
|---|---|---|
| --r | 14px | Cards, panels, modals |
| --r-sm | 7px | Buttons, inputs, small components |
| --r-pill | 999px | Chips, badges, toggles |

---

## §2 SHELLS

Every page maps to exactly one archetype. Same archetype across surfaces renders with different density — same slot structure.

| # | Name | Layout | Flow |
|---|---|---|---|
| A1 | Dashboard | Grid | Scan → Prioritize → Navigate |
| A2 | ResourceList | Stack | Scan → Filter → Select → Act |
| A3 | ResourceDetail | Sidebar | Open → Inspect → Act → Return |
| A4 | ResourceEditor | Stack | Load → Edit → Validate → Save |
| A5 | CreationWizard | Stack | Create → Configure → Validate → Submit |
| A6 | Builder | Canvas | Create → Configure → Validate → Publish |
| A7 | Player | Split | Consume → Interact → Progress → Complete |
| A8 | Insight | Grid | Filter → Analyze → Export |
| A9 | Settings | Sidebar | Configure → Save → Persist |
| A10 | Profile | Sidebar | View → Edit → Save |
| A11 | Library | Sidebar | Search → Browse → Select |
| A12 | SingleFocusForm | Center | Focus → Complete → Exit |

**A2 slot contract:** PAGE_HEADER · KPI_STRIP · FILTER_BAR (sticky) · BULK_TOOLBAR (conditional) · DATA_TABLE · PAGINATION

**A3 slot contract:** BREADCRUMB · PAGE_HEADER · TABS · MAIN (1fr) · SIDEBAR (284px)
Tabs: Overview · Enrolments · Content · Settings

**A7 zones:** Topbar (48px) + Left outline (260px) + Content (flex-1, dark bg #0F0F0F) + Right notes (280px) + Rail (56px fixed)
Responsive: >=1024px all zones · 768px notes hidden · <768px outline as drawer

**A12:** No topbar, no sidebar, no chrome. Auth card 420px max-width centered.

---

## §3 COMPONENTS

### 3.1 Button

4 variants. One primary per page maximum. **Primary = ink fill, not accent.**

| Variant | Background | Text | Border | Notes |
|---|---|---|---|---|
| Primary | --ink | white | none | 1 max · right-aligned in header · hover: --sh-indigo |
| Secondary | --white | --ink-2 | --border | Max 3 per section |
| Ghost | transparent | --accent | none | Inline/contextual — "View all →" |
| Danger | --red-bg | --red | --red-bd | Confirmation modals only |
| Disabled | --white | --ink-4 | --border | opacity 0.5 · cursor not-allowed |

Height: 36px · Padding: 0 18px · Radius: --r-sm · Font: 13px 600

---

### 3.2 Status Chip

Anatomy: `[● dot][LABEL]` — 10px 700 UPPERCASE · border always 1.5px · padding 3px 9px · --r-pill

| State | Text | Background | Border |
|---|---|---|---|
| Published / Active / Completed | --green | --green-bg | --green-bd |
| Draft / Pending | --ink-2 | --subtle | --border |
| Under Review / Due Soon | --amber | --amber-bg | --amber-bd |
| Overdue / Suspended | --red | --red-bg | --red-bd |
| Live / Upcoming | --teal | --teal-bg | --teal-bd |
| Certified | --gold | --gold-bg | --gold-bd |

Domain vocabulary:
- **Course:** Draft · Published · Archived · Under Review
- **User:** Active · Inactive · Pending · Suspended
- **Learning:** Enrolled · Completed · Expired · Waived
- **Session:** Live · Upcoming · Ended · Cancelled

---

### 3.3 Card

Background white · border 1px --border · radius --r · shadow --sh-sm (resting) · --sh-md (hover)
Padding: sm=14px · md=18px · lg=24px
Color on indicators only — never on card containers.

---

### 3.4 Input

Height 38px · padding 0 12px · border 1px --border · radius --r-sm · font 13px 500
Focus: border --border-focus · box-shadow 0 0 0 3px rgba(91,91,214,.08)
Textarea: min-height 80px · resize vertical

---

### 3.5 Table

Header: height 34px · --subtle bg · 10px 700 UPPERCASE +0.06em · --ink-3
Rows: surface-specific height (see §1.3) · white-space nowrap always · truncate with ellipsis
Hover: --subtle bg · Selected: --accent-lt bg
Bulk toolbar (on >=1 selection): --ink bg · white text · height 44px

Column types: entity · tag · text · status_chip · number (right-aligned, tabular) · progress_bar · actions (hover-only, max 2 + overflow)

---

### 3.6 KPI / Stat Card

3 variants: default (label+number+delta) · hero (large, 3px left-border) · ring (SVG gauge)
Color on the number only — never on the container.
Conditional variant (admin): switches color above alert threshold.

---

### 3.7 Progress Bar

Track: height 6px (inline tables: 4px) · --border bg · --r-pill
Always show numeric value alongside the bar.

Threshold coloring:
- >=80% → --green-md
- 50–79% → --accent
- <50% → --amber-md
- Overdue → --red-md (always overrides)

---

### 3.8 Avatar

sm 24px/9px · md 36px/12px · lg 48px/15px
Monochrome bg from name hash · initials first+last · never colored border rings

---

### 3.9 Toggle

Track 36×20px · --r-pill · off=--border bg / on=--accent bg
Thumb 14px white circle · translateX(3px) off / translateX(19px) on · transition 150ms

---

### 3.10 Wizard Stepper

Done: --green-md bg/border · white check
Active: --accent bg/border · white number
Pending: white bg · --border · --ink-3 number
Connector: flex-1 · 1px · done=--green-md / pending=--border

---

### 3.11 Action Bar (Fixed Bottom)

A4/A5 only. Height 64px · fixed bottom · --white bg · border-top 1px --border
Left: unsaved indicator (amber dot + message) · Right: ghost cancel + primary save

---

### 3.12 Skeleton Loader

Shimmer gradient on --subtle/--muted · 1400ms ease-in-out infinite
Mirror the loaded layout exactly — same dimensions and positions.
Skeleton before spinner — always. No full-page spinners.

---

### 3.13 Alert Block

Radius 8px · padding 10px 14px · 12px 600
error=--red/--red-bg/--red-bd · warning=--amber/--amber-bg/--amber-bd
success=--green/--green-bg/--green-bd · info=--teal/--teal-bg/--teal-bd

---

### 3.14 Empty State

Used when any list/table/grid has zero items. Never show 0 rows.

Icon (40px, --ink-4) + specific headline (15px 700) + context description (13px 500 --ink-3) + single CTA
Resource-specific copy always. No generic "No data found."

---

### 3.15 Sidebar Nav

Width: 240px (nav) · 260px (filter panels, profile)
Nav item: height 34px · 12.5px 500 · gap 8px · radius --r-sm · transition 120ms
Active: --accent-lt bg · --accent text · 700wt
Section label: 9px 700 UPPERCASE +0.12em · --ink-4

---

### 3.16 Upload Zone

2px dashed --border-s · --subtle bg · --r · padding 32px
Hover/drag-over: --green-md border · --green-bg bg · transition 150ms

---

## §4 MOTION

Motion is invisible when correct. No bounce. No spring. Enterprise tone is calm.

| Duration | Name | Usage |
|---|---|---|
| 0ms | Instant | Toggle, checkbox — immediate feedback |
| 120ms | Hover | Color/shadow shift on interactive elements |
| 150ms | Micro | Chip, badge, tag state changes |
| 200ms | Panel | Dropdown, accordion expand/collapse |
| 220ms | Modal | Overlay entrance: scale(0.97)+opacity → scale(1)+opacity(1) |
| 240ms | Page | Route change, tab switch — fade only |
| 600ms | Chart | Data viz entrance — fires once on mount only |
| 1400ms | Skeleton | Shimmer — infinite ease-in-out |

Easing: `ease` for all interactive · `ease-out` for chart · `ease-in-out` for skeleton
No animation on hover alone. Motion reserved for state changes.

---

## §5 INTERACTION RULES

**DO:**
1. One primary action per page — ink fill, right-aligned in header
2. Destructive actions always confirm — modal names the specific entity, states if irreversible
3. Row actions on hover only — max 2 icon buttons + ellipsis overflow
4. Skeleton before spinner always — mirror loaded layout exactly
5. Progress bars always show a numeric value alongside
6. Empty states are resource-specific — always offer a single CTA

**DON'T:**
1. Never wrap table cells — truncate with ellipsis
2. Never put color on containers — color lives on dots, fills, numbers
3. Never show 0-row tables — use EmptyState
4. Never use more than 3 colors simultaneously — 80/12/8 rule
5. Never animate on hover alone — motion for state changes only

---

## §6 OPEN ISSUES

### Resolved in v2.0 (from inconsistency list)

| # | Issue | Resolution |
|---|---|---|
| 1 | Border radius inconsistency | --r-sm = 7px (DL wins) |
| 2 | Input height (38/40px) | 38px |
| 3 | Table header height (32/34px) | 34px |
| 4 | Card padding mixed | sm=14 · md=18 · lg=24px |
| 5 | Sidebar widths (200–260px) | 240px nav · 260px filter/profile |
| 6 | Chip border (1px/1.5px) | Always 1.5px |
| 7 | Button padding mixed | height 36px · padding 0 18px |
| 8 | zoom:1.25 hack | Replaced by surface density table |
| 9 | Primary button color | Ink fill confirmed — accent is for focus/ghost only |
| 10 | Green token split | --green (text dk) vs --green-md (fill) — now 4-state |

### Still open (decisions needed before polish pass)

| # | Issue | Notes |
|---|---|---|
| 1 | Icon system | ✅ Resolved in v2.1 — lucide-react via Icon component, ICON_REGISTRY extended to 60 semantic icons, SVG inline pattern defined for HTML pages |
| 2 | Modal / confirmation dialog | Referenced in rules — component not yet specified |
| 3 | Toast / notification pattern | Not in pages or DL — needs spec |
| 4 | Pagination component | Used in all A2 pages — not formally specified |
| 5 | Breadcrumb component | Used in A3/A7 — not specified |
| 6 | Drawer component | Referenced (--sh-lg) — not specified |
| 7 | Body text size | DL specifies 14px · built pages use 13px in many places — resolve on polish pass |
| 8 | DL gap CG-002 | Role display names must come from server, not hardcoded in UI |
| 9 | DL gap BG-014 | No server-side filtering on users endpoint — filter bar operates on local state only |
| 10 | DL gap BG-018 | Completion trend API not available — chart uses synthetic data |
| 11 | Page count | DL references 82 total pages · 52 built · 30 unbuilt — need inventory |
| 12 | DL iframe paths | Preview iframes use relative paths (src="lms-a2-courses-list.html") — need path correction for current folder structure |

---

## §7 ICON SYSTEM

> **Source of truth:** `C:/LMS/UI/-- ICON_SYSTEM_LAYER--v1.md`  
> **Stack:** React/Next.js/Tailwind/shadcn + lucide-react  
> **Rule:** No direct lucide imports outside the icon layer file. All icons via `<Icon />` component only.

---

### 7.1 Design Tokens (locked — mirrors icon layer v1)

#### Size tokens
| Token | Tailwind | px | Usage |
|---|---|---|---|
| xs | w-3 h-3 | 12px | Inline label badges, dense table indicators |
| sm | w-4 h-4 | 16px | Inline body text, chip icons |
| **md** | w-5 h-5 | **20px** | **Default — nav items, buttons, card headers** |
| lg | w-6 h-6 | 24px | Section headings, KPI cards, feature CTAs |
| xl | w-8 h-8 | 32px | Empty state illustrations, hero actions |

#### Color tokens → CSS variable mapping
| Token | Tailwind class | CSS variable | Hex |
|---|---|---|---|
| primary | text-primary | --accent | #5B5BD6 |
| secondary | text-secondary-foreground | --ink-2 | #3D3D3A |
| muted | text-muted-foreground | --ink-3 | #6B6B63 |
| success | text-green-600 | --green-md | #16A34A |
| warning | text-yellow-600 | --amber-md | #D97706 |
| danger | text-red-600 | --red-md | #DC2626 |
| inverse | text-white | white | #FFFFFF |

#### Weight tokens
| Token | Tailwind | Usage |
|---|---|---|
| light | stroke-[1] | Decorative, background icons |
| **regular** | stroke-[1.5] | **Default — all standard usage** |
| bold | stroke-[2.5] | Emphasis, status indicators, CTAs |

---

### 7.2 Icon Component API (React)

```tsx
// Single import — always from the icon layer, never from lucide-react directly
import { Icon, IconName } from "@/components/ui/icon"

// Props
type IconProps = {
  name: IconName         // required — semantic name only
  size?: "xs"|"sm"|"md"|"lg"|"xl"          // default: "md"
  color?: "primary"|"secondary"|"muted"|"success"|"warning"|"danger"|"inverse" // default: "primary"
  weight?: "light"|"regular"|"bold"        // default: "regular"
  state?: "default"|"hover"|"active"|"disabled"  // default: "default"
  className?: string     // escape hatch — use sparingly
  ariaLabel?: string     // required when icon conveys meaning without adjacent text
  animated?: boolean     // true only for name="loading" — triggers animate-spin
}

// Examples
<Icon name="course" />
<Icon name="user" size="lg" />
<Icon name="success" color="success" />
<Icon name="loading" animated />
<Icon name="alert" color="warning" ariaLabel="Warning: incomplete data" />
```

---

### 7.3 Extended ICON_REGISTRY (8 → 60 semantic icons)

> All icons map to lucide-react component names. Add new entries here first, then add the lucide import in the icon layer file.

#### Category 1 — Navigation & Structure
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| course | BookOpen | 📚 | A1 A2 A3 A7 |
| courses | Library | — | A2 sidebar |
| home | Home | 🏠 | A1 nav |
| dashboard | LayoutDashboard | — | A1 |
| settings | Settings | ⚙️ | A10 nav |
| menu | Menu | — | mobile nav |
| sidebar-toggle | PanelLeft | — | A2 A6 |
| breadcrumb-sep | ChevronRight | — | A3 A7 |
| collapse | ChevronUp | — | A6 |
| expand | ChevronDown | ▾ | A6 |
| next | ArrowRight | → | A8 A12 |
| back | ArrowLeft | — | A3 A7 |
| external | ExternalLink | — | A3 |

#### Category 2 — Content & Learning
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| lesson | FileText | 📄 | A3 A6 A7 |
| video | Video | 🎥 | A3 A6 A7 |
| quiz | ClipboardList | 📝 | A3 A6 |
| assignment | ClipboardCheck | — | A3 A6 |
| certificate | Award | 🏆 | A1 A9 |
| resource | Paperclip | 📎 | A3 A6 |
| module | Layers | — | A6 |
| scorm | Package | — | A6 |
| live-session | Radio | 🔴 | A2 A3 |
| category | Tag | — | A2 A11 |
| library | BookMarked | — | A11 |
| path | Route | — | A2 A11 |

#### Category 3 — Actions & Controls
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| add | Plus | ➕ | A2 A4 A6 |
| edit | Pencil | ✏️ | A2 A3 A5 A6 |
| delete | Trash2 | 🗑️ | A2 A5 A6 |
| save | Save | — | A5 A6 |
| publish | Send | — | A5 A6 |
| duplicate | Copy | — | A5 A6 |
| upload | Upload | 📤 | A5 A6 |
| download | Download | 📥 | A3 A9 |
| search | Search | 🔍 | A2 A11 |
| filter | Filter | — | A2 A9 |
| sort | ArrowUpDown | — | A2 A9 |
| more | MoreHorizontal | ⋯ | A2 A3 |
| close | X | ✕ | modals chips |
| drag | GripVertical | ⠿ | A6 |

#### Category 4 — Status & Feedback
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| success | CheckCircle | ✅ | A1 A3 A12 |
| warning | AlertTriangle | ⚠️ | A1 A9 |
| alert | AlertCircle | 🔴 | A1 A9 |
| info | Info | ℹ️ | A3 A10 |
| error | XCircle | — | A12 |
| loading | Loader2 | — | global |
| check | Check | ✓ | A4 A6 |
| lock | Lock | 🔒 | A3 A7 |
| unlock | Unlock | — | A3 |
| required | Asterisk | * | A4 A5 |
| draft | FileEdit | — | A2 |
| archived | Archive | — | A2 A11 |

#### Category 5 — Users & Roles
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| user | User | 👤 | A3 A9 A10 |
| users | Users | 👥 | A1 A9 |
| learner | GraduationCap | 🎓 | A1 A9 |
| instructor | UserCog | — | A9 |
| manager | Briefcase | — | A9 |
| admin | ShieldCheck | — | A10 |
| group | UsersRound | — | A9 |
| profile | CircleUser | — | A10 nav |
| enroll | UserPlus | — | A3 A9 |
| unenroll | UserMinus | — | A9 |

#### Category 6 — Data & Analytics
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| analytics | BarChart3 | 📊 | A8 nav |
| chart-line | LineChart | 📈 | A8 |
| chart-pie | PieChart | — | A8 |
| trend-up | TrendingUp | ↑ | A1 A8 |
| trend-down | TrendingDown | ↓ | A8 |
| kpi | Gauge | — | A8 |
| calendar | Calendar | 📅 | A8 A9 |
| clock | Clock | ⏰ | A1 A3 A7 |
| report | FileBarChart | — | A8 A9 |
| export | FileDown | — | A8 A9 |

#### Category 7 — Utility & System
| Semantic name | lucide-react | Emoji replaced | Used in archetypes |
|---|---|---|---|
| notification | Bell | 🔔 | A1 nav |
| email | Mail | 📧 | A10 |
| link | Link | — | A3 A6 |
| refresh | RefreshCw | — | A8 A9 |
| fullscreen | Maximize2 | — | A7 |
| exit-fullscreen | Minimize2 | — | A7 |
| help | HelpCircle | — | A10 nav |
| star | Star | ⭐ | A11 |
| flag | Flag | — | A9 |

---

### 7.4 SVG Inline Pattern (HTML pages — pre-React)

Until the React migration, HTML built-pages use inline SVG mirroring lucide-react geometry. Apply this wrapper pattern consistently — it ensures visual parity with the Icon component.

```html
<!-- SVG inline pattern — mirrors lucide-react output -->
<!-- Size: use px value from size token (xs=12, sm=16, md=20, lg=24, xl=32) -->
<!-- Color: use CSS var on stroke, not hardcoded hex -->

<!-- Example: course icon, md size, primary color -->
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="20" height="20"
  viewBox="0 0 24 24"
  fill="none"
  stroke="var(--accent)"
  stroke-width="1.5"
  stroke-linecap="round"
  stroke-linejoin="round"
  role="img"
  aria-label="Course"
>
  <!-- lucide BookOpen path data -->
  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
</svg>

<!-- Muted variant (e.g. nav inactive) -->
<svg ... stroke="var(--ink-3)" ...>...</svg>

<!-- Success variant -->
<svg ... stroke="var(--green-md)" ...>...</svg>

<!-- Loading (animated) -->
<svg ... stroke="var(--ink-3)" class="icon-spin">...</svg>
<!-- CSS: .icon-spin { animation: spin 1s linear infinite; } -->
<!-- @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } } -->
```

**Size-to-width table for HTML SVG:**
| Token | width/height attr |
|---|---|
| xs | 12 |
| sm | 16 |
| md | 20 |
| lg | 24 |
| xl | 32 |

**Stroke mapping for HTML SVG:**
| Token | stroke-width value |
|---|---|
| light | 1 |
| regular | 1.5 |
| bold | 2.5 |

---

### 7.5 Hard Rules (from icon layer — enforced)

**NEVER:**
- Import from lucide-react directly in any component file other than the icon layer
- Use raw emoji as icons in new or updated components
- Use raw SVG files (inline SVG per §7.4 pattern only)
- Pass inline styles for size or color — use tokens
- Use arbitrary Tailwind sizing (w-7, h-7, etc.) — only the 5 defined size tokens
- Render icon-only actions without ariaLabel

**ALWAYS:**
- Use `<Icon />` component in React (or inline SVG pattern in HTML)
- Use semantic names from the registry — not shape names (not "chevron-right", use "breadcrumb-sep")
- Use tokenized size / color / weight props
- Provide `ariaLabel` when icon conveys meaning without adjacent text
- Extend the registry here first before adding a new lucide import in the icon layer

---

### 7.6 QC Check

| Check | Rule | Status |
|---|---|---|
| 1 | Zero direct lucide imports outside icon layer | Enforced |
| 2 | All icons use semantic names | 60 registered |
| 3 | No raw emoji in new/updated components | Rule active |
| 4 | Size strictly from 5-token set | Enforced |
| 5 | Color via token → CSS var only | Mapping table in §7.1 |
| 6 | Accessibility: ariaLabel on meaningful icons | Enforced |
| 7 | Loading icon animates | `animated` prop → animate-spin |
| 8 | HTML pages use inline SVG pattern | §7.4 defined |
