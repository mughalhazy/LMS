# PROJECT MEMORY USAGE GUIDE

Status: Active
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: AI

---

## What This Is

The Project Memory Layer is the institutional memory of this LMS platform. It captures every decision, resolution, default, gap, and external dependency that has been classified through governance phases 1 through 3.25.

It exists because:
- Engineering context is costly to re-derive
- Decisions already made should not be re-debated
- Resolved items should not re-appear as new gaps
- Future AI sessions need context that code alone cannot provide

---

## How to Load It

**Every future AI session touching this project must load in this order:**

### Step 1: Load AI_OPERATING_CONTEXT.md
File: `docs/07_governance/AI_OPERATING_CONTEXT.md`
Purpose: Current phase, frozen decisions, known risks, quick reference
Load: Always, before any other action

### Step 2: Load FINAL_CLASSIFIED_REGISTER.md (this layer)
File: `docs/09_project_memory/FINAL_CLASSIFIED_REGISTER.md`
Purpose: Master index of all 83 classified items
Load: Before any audit, gap analysis, or implementation work

### Step 3: Load the relevant authority documents
Files: `docs/00_authority/` (see FEATURE_SCOPE.md, PRODUCT_WORKFLOWS.md, AUTH_AND_TENANCY_CONTRACT.md, FULLSTACK_STITCHING_CONTRACT.md)
Purpose: What the system IS (authority layer)
Load: When the task involves a specific domain

### Step 4: Load the relevant subordinate register
Files: `docs/09_project_memory/` (AUTO_CLOSED, SAFE_DEFAULT, OWNER_DECISION, EXTERNAL_DEPENDENCY, OUT_OF_SCOPE)
Purpose: Full detail on specific items
Load: When FINAL_CLASSIFIED_REGISTER.md references an item you need detail on

---

## When to Use Each Register

| Register | Use When |
|---|---|
| AUTO_CLOSED_REGISTER.md | You found a "gap" and want to verify it wasn't already investigated and closed |
| SAFE_DEFAULT_REGISTER.md | You are about to make an implementation decision already covered by a safe default |
| OWNER_DECISION_REGISTER.md | You are about to ask the owner a question that may already have been decided |
| EXTERNAL_DEPENDENCY_REGISTER.md | You believe a software gap is actually a missing credential or vendor account |
| OUT_OF_SCOPE_REGISTER.md | A feature request or "gap" may be a known deferred feature |

---

## Gap Discovery Workflow

When you find what looks like a new gap:

```
STEP 1: Check FINAL_CLASSIFIED_REGISTER.md
        → Does this item already have a PM-ID?
        → If YES: check the linked subordinate register for full detail
        → If NO: proceed to STEP 2

STEP 2: Classify the item
        → Can it be proven from repository evidence alone?
           YES → AUTO-CLOSED — document in AUTO_CLOSED_REGISTER.md
        → Is there one clear safe default path?
           YES → SAFE-DEFAULT — document in SAFE_DEFAULT_REGISTER.md
        → Does it require a human decision (credential, vendor, anchor)?
           YES → OWNER-DECISION — document in OWNER_DECISION_REGISTER.md
        → Does it require external provisioning (credentials, registration)?
           YES → EXTERNAL-DEPENDENCY — document in EXTERNAL_DEPENDENCY_REGISTER.md
        → Is it a known deferred feature or future phase item?
           YES → OUT-OF-SCOPE — document in OUT_OF_SCOPE_REGISTER.md

STEP 3: Add to FINAL_CLASSIFIED_REGISTER.md with a new PM-ID

STEP 4: Inform the owner if OWNER-DECISION or EXTERNAL-DEPENDENCY
```

---

## The PM-ID Scheme

| Prefix | Register | Meaning |
|---|---|---|
| PM-AC-NNN | AUTO_CLOSED_REGISTER.md | Auto-closed — proven from evidence |
| PM-SD-NNN | SAFE_DEFAULT_REGISTER.md | Safe default applied |
| PM-OD-NNN | OWNER_DECISION_REGISTER.md | Owner decision required |
| PM-ED-NNN | EXTERNAL_DEPENDENCY_REGISTER.md | External dependency |
| PM-OS-NNN | OUT_OF_SCOPE_REGISTER.md | Out of scope |

When adding new items, use the next available number in the sequence.

---

## What the Memory Layer Is NOT

The memory layer does NOT replace:

| This is still authoritative for... | Document |
|---|---|
| Current system design | docs/00_authority/ |
| Service specifications | docs/specs/ |
| Database schema | docs/01_backend/DATABASE_SCHEMA.md |
| Frontend screens and routes | docs/03_frontend_authority/ |
| Governance rules | docs/07_governance/ |
| Risk register | docs/08_reports/BACKEND_RISK_REGISTER.md |

The memory layer supplements these with historical context. If a memory layer entry conflicts with an authority document, the authority document wins (TIER 2 > TIER 5).

---

## Reopen Protocol

Items are closed for reasons. If you believe a closed item needs to be reopened:

1. Check the "Reopen Criteria" field in the item's register entry
2. Verify whether the criteria are met (evidence changed, implementation changed, architecture changed, owner reversal, external dependency available)
3. If criteria ARE met: update the item status, update the evidence, update the resolution, add a reopened date
4. If criteria are NOT met: do NOT reopen — the item is resolved

**The default is: resolved items remain resolved.**

---

## Adding New Items

When a new item needs to be added to the memory layer:

1. Determine the classification
2. Add a full entry (all required fields) to the appropriate subordinate register
3. Add a one-line summary row to FINAL_CLASSIFIED_REGISTER.md with the new PM-ID
4. Check for related items and add cross-references

Required fields for every entry:
- Item ID, Title, Classification, Current Status
- Original Source, Evidence Source, Resolution Source
- Resolution Date, Resolved By
- Decision Summary, Detailed Explanation
- Affected Components, Routes, APIs, Workflows, Roles
- Owner Required, External Dependency, Future Impact
- Reopen Criteria, Related Documents, Related Register Entries

---

## Memory Layer vs. Sprint Planning

The memory layer tracks WHAT was decided. Sprint planning determines WHEN to implement.

Items in SAFE_DEFAULT_REGISTER.md and OUT_OF_SCOPE_REGISTER.md have sprint implications:

| Register | Sprint type |
|---|---|
| SAFE-DEFAULT items | Persistence sprint, Kafka sprint, doc sprint |
| OUT-OF-SCOPE PLANNED-DEFERRED | Dedicated feature sprints (see Out-of-Scope gap sprint priority queue) |
| OWNER-DECISION | No sprint until owner acts; then one-session execution |
| EXTERNAL-DEPENDENCY | No sprint; owner/operator provisioning action |

---

## Versioning

The memory layer is not versioned per file. Instead:
- Each register entry has Resolution Date and Resolved By
- The FINAL_CLASSIFIED_REGISTER.md Phase History table records which phase each batch of items came from
- When updating an existing entry, note the update date and reason at the bottom of the entry

---

## Quick Reference: What NOT to Re-Ask

These questions are already answered. Do not re-derive or re-ask:

| Question | Answer | PM ID |
|---|---|---|
| Does checkout-service have DB persistence? | No — InMemory; SQLite in persistence sprint | PM-SD-001 |
| What cloud is this deployed on? | Docker Compose for dev; cloud at owner discretion | PM-SD-002 |
| Which service owns file uploads? | content-service (metadata) + media-service (binary) | PM-SD-003 |
| How are frontend routes gated? | POST /api/v1/rbac/authorize — no hardcoded role_keys | PM-AC-026 |
| What is the JWT user claim? | sub claim = user_id | PM-AC-036 |
| Does an EventBus exist? | Yes — shared/events/bus.py, thread-safe in-process | PM-AC-037 |
| What is the tenant model? | 6 fields: tenant_id, name, country_code, segment_type, plan_type, addon_flags | PM-AC-039 |
| Are infra env files safe to commit? | Yes — placeholder credentials only | PM-AC-038 |
| Does interaction-service exist? | No — never existed | PM-AC-024 |
| Are class-based services resolved? | Yes — ASGI shims added Phase 2.9 | PM-AC-004 |
| What is the cross-process broker? | Kafka — confirmed in event_bus_config.json | PM-SD-006 |
| Does WF-001 emit Kafka events? | No — synchronous chain only | PM-AC-041 |
| Who owns reconciliation? | PaymentReconciliationEngine in integrations/payments/ | PM-AC-042 |
| Is parent portal in scope? | No — FGAP-001, deferred | PM-OS-001 |
| Is adaptive learning in scope? | No — FGAP-002, deferred (design exists) | PM-OS-002 |
