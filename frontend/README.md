# LMS Frontend

React/Next.js frontend for the Meridian LMS platform.

## Stack

- **Framework:** Next.js (see `AGENTS.md` — this version has breaking changes from standard Next.js)
- **UI components:** shadcn/ui
- **Design system:** `workspace/design-system/design-system.md`
- **UI framework:** `workspace/page-definitions/ui-framework.md`

## Before writing any code

Read `AGENTS.md` in this directory. It points to the correct Next.js guide for this version. APIs, conventions, and file structure may differ from standard Next.js training data.

## Page inventory

119 pages across 16 archetypes (A1–A16), derived from 23 backend services. Full inventory: `workspace/page-definitions/page-inventory.md`.

- 60 pages in `workspace/pages/working/` — existing prototypes under fix
- 59 pages in `workspace/pages/new/` — built to spec 2026-05-15, zero findings at birth
- No pages are finalised or converted to shadcn yet — HTML prototypes are the current working state

## Development

```bash
npm run dev
```

## Design rules

- Component source of truth: `components/lms/` — 23 components built from spec
- Assembly Contracts (per-archetype binary checklists): `workspace/page-definitions/ui-framework.md §10`
- CSS tokens: `globals.css` — `--primary: #5b5bd6`, no `PAGE_SCOPE` pattern
- Framework changes only via gap register: `workspace/design-system/framework-gap-register.md`
