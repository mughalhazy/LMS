"use client"

// AdminShell — Universal page wrapper for all admin-surface archetypes
// Source: design-system.md §2 (shells) · §1.3 (surface density) · §3.15 (nav)
// Usage: wrap every admin page with <AdminShell>. Zero page-level scope overrides needed.

import React, { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Sheet, SheetContent, SheetHeader, SheetTitle,
} from "@/components/ui/sheet"
import { Icon, IconName } from "@/components/ui/icon"
import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────────────────────────

export type Surface = "admin" | "manager" | "instructor" | "learner"

export type NavItem = {
  label: string
  href: string
  icon?: IconName
  badge?: number
}

export type MobileTab = {
  label: string
  icon: IconName
  href: string
}

type AdminShellProps = {
  /** Visual surface — controls density (design-system.md §1.3). Defaults to "admin". */
  surface?: Surface
  /** Logo slot — rendered in utility bar and mobile nav header */
  logo?: React.ReactNode
  /** Quick-action buttons shown in utility bar on desktop (e.g. "+ Course") */
  utilityActions?: React.ReactNode
  /** Primary navigation items — rendered in desktop nav bar and mobile sheet */
  navItems?: NavItem[]
  /** Mobile bottom tab bar items — omit to hide the tab bar entirely */
  mobileTabItems?: MobileTab[]
  /** Tenant display name shown in utility bar on desktop */
  tenantName?: string
  /** User initials for avatar fallback */
  userInitials?: string
  /** Unread notification count — shows red dot when > 0 */
  notificationCount?: number
  /** Page content */
  children: React.ReactNode
}

// ── Surface density — design-system.md §1.3 ───────────────────────────────

const SURFACE_VARS: Record<Surface, React.CSSProperties> = {
  admin:      { "--pp": "28px", "--sg": "20px", "--row-h": "40px" } as React.CSSProperties,
  manager:    { "--pp": "32px", "--sg": "40px", "--row-h": "48px" } as React.CSSProperties,
  instructor: { "--pp": "32px", "--sg": "40px", "--row-h": "52px" } as React.CSSProperties,
  learner:    { "--pp": "32px", "--sg": "48px", "--row-h": "56px" } as React.CSSProperties,
}

// ── Component ──────────────────────────────────────────────────────────────

export function AdminShell({
  surface = "admin",
  logo,
  utilityActions,
  navItems = [],
  mobileTabItems,
  tenantName,
  userInitials = "?",
  notificationCount = 0,
  children,
}: AdminShellProps) {
  const [navOpen, setNavOpen] = useState(false)
  const pathname = usePathname()

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href)

  return (
    <div
      className="min-h-screen bg-[var(--canvas)]"
      style={SURFACE_VARS[surface]}
    >
      {/* ── MOBILE NAV SHEET ─────────────────────────────────────── */}
      <Sheet open={navOpen} onOpenChange={setNavOpen}>
        <SheetContent side="left" className="w-[75vw] max-w-[240px] p-0">
          <SheetHeader className="px-5 py-4 border-b border-border">
            <SheetTitle className="flex items-center">
              {logo ?? <span className="text-sm font-bold text-[var(--ink)]">Navigation</span>}
            </SheetTitle>
          </SheetHeader>
          <nav className="py-2">
            {navItems.map(item => {
              const active = isActive(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setNavOpen(false)}
                  className={cn(
                    "w-full flex items-center justify-between px-5 py-2.5 text-sm font-medium transition-colors duration-[120ms]",
                    active
                      ? "bg-[var(--accent-lt)] text-[var(--lms-accent)] font-semibold"
                      : "text-[var(--ink-3)] hover:bg-[var(--subtle)] hover:text-[var(--ink-2)]"
                  )}
                >
                  <span className="flex items-center gap-2.5">
                    {item.icon && (
                      <Icon name={item.icon} size="sm" color={active ? "primary" : "muted"} />
                    )}
                    {item.label}
                  </span>
                  {item.badge != null && item.badge > 0 && (
                    <span className="bg-[var(--red-md)] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>
        </SheetContent>
      </Sheet>

      {/* ── UTILITY BAR ──────────────────────────────────────────── */}
      <header className="h-12 bg-white border-b border-border flex items-center px-4 md:px-7 gap-2 sticky top-0 z-40 shadow-[var(--sh-xs)]">
        {/* Hamburger — mobile only */}
        <button
          onClick={() => setNavOpen(true)}
          className="md:hidden w-8 h-8 inline-flex items-center justify-center rounded-[var(--r-sm)] text-[var(--ink-3)] hover:bg-[var(--subtle)] transition-colors"
          aria-label="Open navigation"
        >
          <Icon name="menu" size="md" color="muted" />
        </button>

        {/* Logo */}
        {logo && (
          <div className="flex items-center mr-2 shrink-0">
            {logo}
          </div>
        )}

        {/* Utility actions — desktop only */}
        {utilityActions && (
          <div className="hidden md:flex items-center gap-1.5">
            {utilityActions}
          </div>
        )}

        {/* Right side */}
        <div className="ml-auto flex items-center gap-1.5">
          {tenantName && (
            <Button
              variant="ghost"
              size="sm"
              className="hidden md:inline-flex h-7 gap-1.5 text-[11px] font-semibold text-[var(--ink-2)]"
            >
              <Icon name="home" size="xs" color="muted" />
              {tenantName}
              <Icon name="expand" size="xs" color="muted" />
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 relative"
            aria-label={notificationCount > 0 ? `${notificationCount} unread notifications` : "Notifications"}
          >
            <Icon name="notification" size="sm" color="muted" />
            {notificationCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[var(--red-md)] border-2 border-white" />
            )}
          </Button>

          <Avatar className="h-7 w-7 cursor-pointer">
            <AvatarFallback className="bg-[var(--ink)] text-white text-[10px] font-bold">
              {userInitials}
            </AvatarFallback>
          </Avatar>
        </div>
      </header>

      {/* ── DESKTOP NAV BAR ──────────────────────────────────────── */}
      {navItems.length > 0 && (
        <nav className="hidden md:flex h-10 bg-white border-b border-border items-center px-7 gap-0.5 sticky top-12 z-30">
          {navItems.map(item => {
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--r-sm)] text-xs font-medium whitespace-nowrap transition-all duration-[120ms]",
                  active
                    ? "bg-[var(--ink)] text-white font-semibold"
                    : "text-[var(--ink-3)] hover:bg-[var(--subtle)] hover:text-[var(--ink-2)]"
                )}
              >
                {item.label}
                {item.badge != null && item.badge > 0 && (
                  <span className="inline-block bg-[var(--red-md)] text-white text-[9px] font-bold px-1.5 py-0 rounded-full leading-none">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>
      )}

      {/* ── CANVAS ───────────────────────────────────────────────── */}
      {/* Padding from --pp token (surface-specific). Max-width set per archetype template, not here. */}
      <main className={cn(
        "p-[var(--pp)]",
        mobileTabItems && mobileTabItems.length > 0 && "pb-28 md:pb-[var(--pp)]"
      )}>
        {children}
      </main>

      {/* ── MOBILE BOTTOM TAB BAR ────────────────────────────────── */}
      {mobileTabItems && mobileTabItems.length > 0 && (
        <nav
          className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-border flex items-stretch h-16"
          aria-label="Mobile navigation"
        >
          {mobileTabItems.map(tab => {
            const active = isActive(tab.href)
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "flex-1 flex flex-col items-center justify-center gap-0.5 text-[10px] font-semibold transition-colors duration-[120ms]",
                  active
                    ? "text-[var(--lms-accent)]"
                    : "text-[var(--ink-4)] hover:text-[var(--ink-2)]"
                )}
              >
                <Icon name={tab.icon} size="sm" color={active ? "primary" : "muted"} />
                {tab.label}
              </Link>
            )
          })}
        </nav>
      )}
    </div>
  )
}
