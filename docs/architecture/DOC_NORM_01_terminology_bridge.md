# DOC_NORM_01 — Terminology Bridge

**Type:** Normalisation anchor | **Date:** 2026-04-04 | **Priority:** Reference (read before any new work)

---

## Purpose

This document maps legacy terminology used throughout the repo to the canonical Master Spec language. It exists because the repo was built using "feature" framing before the Master Spec established "capability" as the required term. Both sets of terms are valid — this bridge ensures they are understood as equivalent.

---

## Canonical Term Map

| Legacy term (in existing docs) | Canonical term (Master Spec) | Notes |
|---|---|---|
| feature | capability | A unit of independently enableable, measurable, reusable platform function |
| feature flag | capability activation gate | Controls whether a capability is active for a tenant context |
| feature inventory | capability domain inventory | A listing of all capability domains and their scope |
| feature-based design | capability-driven design | Prohibited framing — all new work must use capability language |
| feature toggle | capability gate | Same as capability activation gate |
| feature gating | capability entitlement gating | Access controlled via the entitlement service |
| feature set | capability bundle | A group of capabilities enabled together for a use-case profile |
| feature flag system | capability registry + entitlement service | Registry stores definitions; entitlement resolves allow/deny |
| segment | use-case profile | A named capability bundle template (not a product fork) |
| segment-specific | use-case-specific capability domain | See Master Spec §5.19 |
| country-specific | adapter-backed, config-driven | Country variance is isolated in adapters and config layers |
| Enterprise LMS V2 | Heritage runtime layer | The Rails-based runtime engine — valid as implementation context only |
| Global Capability Platform | System identity (Master Spec) | Governs all architectural decisions |

---

## Rules for New Work

1. Always use "capability" not "feature" in new docs, code comments, API names, and event names.
2. If reading a legacy doc that uses "feature", apply this map mentally — do not rewrite legacy docs unless on a dedicated polish pass.
3. If writing a new spec that references a legacy doc, add a cross-reference to this bridge doc.

---

## Reference

- Master Spec §1.4: "Everything must be defined as capabilities"
- `docs/anchors/doc_precedence.md`: Document priority order
