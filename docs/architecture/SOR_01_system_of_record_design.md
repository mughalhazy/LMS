# SOR_01 — System of Record Design

**Type:** Architecture design | **Date:** 2026-04-04 | **MS§:** §6 | **Priority:** BATCH-equivalent (SOR layer)

---

## Purpose

Define the System of Record (SoR) architecture for the three authoritative data pillars required by Master Spec §6:

1. Student lifecycle
2. Financial ledger
3. Unified profile

---

## SoR Mandate (from Master Spec §6)

> The system must maintain a SINGLE SOURCE OF TRUTH. No duplication of core state across services.

---

## Pillar 1 — Student Lifecycle SoR

**Owner service:** `services/system-of-record/`
**Shared model:** `shared/models/student_profile.py`

### Authoritative records

| Record | Owned by | Description |
|---|---|---|
| Enrollment state | `services/system-of-record/` | All enrollment transitions — invited → active → completed → withdrawn |
| Progress state | `services/system-of-record/` | Lesson, course, path completion state |
| Attendance record | `services/academy-ops/` → SoR event | Session attendance facts |
| Certificate state | `certificate-service` | Issued, revoked, expired credentials |

### Rule

Only the SoR service writes authoritative lifecycle state. All other services consume lifecycle events — they never write directly to lifecycle records.

---

## Pillar 2 — Financial Ledger SoR

**Owner service:** `services/system-of-record/` (for student-side ledger) + `services/commerce/billing.py` (for platform billing SoR)
**Shared model:** `shared/models/ledger.py`, `shared/models/invoice.py`

### Authoritative records

| Record | Owned by | Description |
|---|---|---|
| Student payment ledger | `services/system-of-record/` | Per-student payment events, balances, fee status |
| Platform invoice | `services/commerce/` | Invoice, line items, payment state |
| Usage ledger | `services/commerce/` | Append-only billable event log |
| Revenue record | `docs/architecture/B3P06` | Read-optimised revenue aggregates (no SoR writes) |

### Rule

Financial ledger is append-only. No updates — only adjustment entries. Deduplication enforced by event key. Cross-service reads via API only.

---

## Pillar 3 — Unified Profile SoR

**Owner service:** `services/system-of-record/`
**Shared model:** `shared/models/student_profile.py`

### Authoritative records

| Record | Owned by | Description |
|---|---|---|
| Core identity | `auth-service` (heritage) | Canonical User — email, credentials, tenant binding |
| Profile attributes | `user-service` / SoR | Name, timezone, locale, department, title |
| Skills profile | `ai/skill-inference-service` → SoR event | Inferred competencies, confidence scores |
| Learning preferences | SoR | Pace, language, accessibility settings |

### Rule

Profile reads serve from the SoR read model. Profile writes route through the SoR service. AI-inferred attributes are written via event — never via direct mutation from AI services.

---

## SoR Access Patterns

### Read
- Services query SoR via stable read APIs
- Read models are pre-projected for performance (no joins at query time)
- `services/system-of-record/read_models.py`

### Write
- Domain services emit events when they produce authoritative state changes
- SoR service consumes events and updates its authoritative records
- Direct cross-service writes to SoR records are prohibited

### Validation
- `services/system-of-record/qc.py` — contract validation for SoR integrity
- `validation/tests/test_system_integration_validation.py`

---

## No-Duplication Rule

| If a service needs | It must | NOT |
|---|---|---|
| Student lifecycle state | Call SoR read API | Cache or replicate lifecycle records |
| Financial balance | Call SoR financial API | Maintain a local payment ledger |
| Profile data | Call SoR profile API | Store profile copies in domain DB |

---

---

## Architectural Contract: MS-SOR-01 — SoR State Authority (MS§6)

**Contract name:** MS-SOR-01
**Source authority:** Master Spec §6
**Enforcement scope:** Applies to ALL services in the platform. No exceptions without an explicit architectural decision record.

**Rule:** No service MAY hold a durable copy of student lifecycle state, financial ledger state, or unified profile state that it did not originate.

**Boundary definitions:**

| State type | Authoritative owner | What ALL other services must do |
|---|---|---|
| Student lifecycle state | `services/system-of-record/` (student pillar) | Read via SoR read API. Never cache, replicate, or maintain a local copy of enrollment, progress, or attendance facts. |
| Financial ledger state | `services/system-of-record/` (financial pillar) + `services/commerce/` (platform billing) | Read via SoR financial API. Never maintain a local payment ledger or balance store. |
| Unified profile state | `services/system-of-record/` (profile pillar) | Read via SoR profile API. Never store profile copies in domain databases. AI-inferred attributes are written to SoR via event — never via direct mutation from AI services. |

**Write rule:** Domain services emit events when they produce authoritative state changes. The SoR service consumes events and updates its authoritative records. Direct cross-service writes to SoR records are prohibited.

**What a violation looks like:**
- A service maintaining its own `student_status` or `balance` table that shadows SoR state.
- A service writing directly to `system-of-record` tables from outside the SoR service.
- An analytics or AI service caching profile state locally beyond a single request scope.

**Why this rule exists:** MS§6 requires a single source of truth with no duplication of core state across services. Without this named enforcement boundary, services accumulate shadow copies of state, leading to consistency violations, reconciliation failures, and undetectable data drift.

---

## References

- Master Spec §6
- `services/system-of-record/service.py` (implementation)
- `shared/models/ledger.py`, `shared/models/student_profile.py`
- `docs/data/DATA_01_global_education_schema.md`
- `docs/architecture/ARCH_04_service_data_ownership_rules.md`
