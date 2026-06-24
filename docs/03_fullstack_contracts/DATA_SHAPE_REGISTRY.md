# DATA_SHAPE_REGISTRY

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Registry of canonical data shapes shared across backend and frontend. Documents field names, types, and semantics for cross-layer consistency. Backend shapes derived from direct code inspection.

---

## Tenant Shape

Used across all services. Source: `docs/anchors/tenant-contract.md` (TIER 1, PROTECTED) and `tenant-service/app/schemas.py`.

```json
{
  "tenant_id": "string (required, immutable)",
  "name": "string",
  "country_code": "string (ISO 3166-1 alpha-2)",
  "segment_type": "string (e.g. university, school, corporate)",
  "plan_type": "string (e.g. free, professional, enterprise)",
  "addon_flags": "object (key-value feature flags, {} if none)"
}
```

**Correction (2026-06-23)**: Prior version listed 4 fields (`tenant_id, name, active, domain`). `active` and `domain` are NOT canonical tenant fields. The canonical 6-field model from the TIER 1 anchor is listed above. `active` and `domain` may appear as mutable operational attributes in tenant lifecycle APIs but are not part of the core tenant identity shape.

Canonical contract: `docs/anchors/tenant-contract.md` (TIER 1, PROTECTED — do not change without owner approval).

---

## Session Shape (auth-service response)

Login response shape — *corrected from code (auth-service/app/service.py:144–152)*:

```json
{
  "session_id": "string",
  "user": {
    "user_id": "string",
    "tenant_id": "string"
  },
  "access_token": "string (JWT)",
  "token_type": "Bearer",
  "expires_in": "integer (seconds, default 900)",
  "refresh_token": "string",
  "refresh_expires_in": "integer (seconds, default 604800)"
}
```

**Frontend notes**: `user_id`/`tenant_id` are nested under `"user"`. `roles` is NOT in the response — read from JWT payload. JWT user identifier is in the `sub` claim (`payload.sub` = user_id string).

Session metadata shape (GET /api/v2/auth/sessions/{session_id}):

```json
{
  "session_id": "string",
  "user_id": "string",
  "tenant_id": "string",
  "issued_at": "ISO 8601 datetime",
  "expires_at": "ISO 8601 datetime",
  "state": "active | revoked | expired"
}
```

---

## Enrollment Shape

Source: `enrollment-service` `EnrollmentResponse` schema.

```json
{
  "enrollment_id": "string",
  "tenant_id": "string",
  "user_id": "string",
  "course_id": "string",
  "source_channel": "string",
  "cohort_id": "string | null",
  "session_id": "string | null",
  "enrollment_status": "string",
  "version": "integer",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime",
  "enrolled_at": "ISO 8601 datetime | null",
  "completed_at": "ISO 8601 datetime | null",
  "dropped_at": "ISO 8601 datetime | null",
  "deferred_at": "ISO 8601 datetime | null",
  "expired_at": "ISO 8601 datetime | null"
}
```

### Enrollment Status Values

Observed from code: active, completed, dropped, deferred, expired, and additional states per the enrollment state machine. Full canonical list: see `docs/specs/enrollment-service-spec.md`.

### Enrollment List Response

```json
{
  "items": [<EnrollmentResponse>],
  "page": "integer",
  "page_size": "integer",
  "total": "integer (stub — not a true DB count)"
}
```

---

## Progress Shapes

Source: `progress-service` schemas.

### Progress Record

```json
{
  "lesson_id": "string",
  "tenant_id": "string",
  "learner_id": "string",
  "completion_status": "not_started | in_progress | completed | passed",
  "progress_percentage": "float (0.0 - 100.0)"
}
```

### Learner Progress Summary

```json
{
  "learner_id": "string",
  "tenant_id": "string"
}
```
(plus course-level aggregates — full shape in progress-service schemas.py)

### Certificate Eligibility

```json
{
  "tenant_id": "string",
  "user_id": "string",
  "course_id": "string",
  "eligible_for_certificate": "boolean",
  "completion_status": "string",
  "progress_percentage": "float"
}
```

---

## RBAC Shapes

Source: `rbac-service` models.py.

### Role Definition

```json
{
  "role_id": "string (UUID)",
  "tenant_id": "string",
  "role_key": "string",
  "display_name": "string",
  "description": "string",
  "is_system": "boolean",
  "status": "active | disabled | deprecated",
  "version": "integer",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime"
}
```

### Permission Definition

```json
{
  "permission_id": "string (UUID)",
  "permission_key": "string (format: resource_type.action)",
  "resource_type": "string",
  "action": "string",
  "risk_tier": "low | moderate | high | critical",
  "is_assignable": "boolean"
}
```

### Subject-Role Assignment

```json
{
  "assignment_id": "string (UUID)",
  "tenant_id": "string",
  "subject_type": "user | group | service_account",
  "subject_id": "string",
  "role_id": "string",
  "scope_type": "tenant | org_unit | course | program | cohort | branch",
  "scope_id": "string",
  "branch_ids": ["string"] | null,
  "starts_at": "ISO 8601 datetime",
  "ends_at": "ISO 8601 datetime | null",
  "source": "direct | group_derived | jit",
  "created_by": "string",
  "created_at": "ISO 8601 datetime",
  "revoked_at": "ISO 8601 datetime | null"
}
```

### Authorization Decision

```json
{
  "decision": "allow | deny",
  "reason_codes": ["string"],
  "policy_trace": ["string"]
}
```

### Effective Permissions Response

```json
{
  "subject": {"type": "string", "id": "string"},
  "tenant_id": "string",
  "effective_permissions": [{"permission_key": "string"}],
  "computed_at": "ISO 8601 datetime"
}
```

---

## Tenant Service Shapes

### Tenant Configuration Response

```json
{
  "tenant_id": "string",
  "configuration": {},
  "effective_settings": {}
}
```

### Lifecycle Status Response

```json
{
  "tenant_id": "string",
  "lifecycle_state": "ACTIVE | SUSPENDED | ARCHIVED | DECOMMISSIONED | PROVISIONING",
  "state_history": [<LifecycleEventResponse>],
  "pending_transitions": ["string"],
  "policy_constraints": ["string"],
  "next_allowed_actions": ["string"]
}
```

---

## Config Resolution Shapes

Source: `shared/models/config.py`.

### ConfigScope

```json
{
  "level": "global | country | segment | tenant",
  "scope_id": "string (non-empty)"
}
```

### ConfigOverride

```json
{
  "scope": <ConfigScope>,
  "capability_enabled": {"capability_key": "boolean"},
  "behavior_tuning": {"key": "value"}
}
```

### ConfigResolutionContext

```json
{
  "tenant_id": "string",
  "country_code": "string",
  "segment_id": "string"
}
```

### EffectiveConfig

```json
{
  "capability_enabled": {"capability_key": "boolean"},
  "behavior_tuning": {"key": "value"}
}
```

### SegmentBehaviorConfig

```json
{
  "attendance_enabled": "boolean",
  "cohort_enabled": "boolean",
  "guardian_notifications_enabled": "boolean"
}
```

---

## Shared Models (root `shared/models/`)

These models are exported by the root `shared/models/` package. Whether they are consumed by `backend/services/` is unconfirmed (OWN-002).

| Model | Purpose |
|---|---|
| `UnifiedStudentProfile` | Cross-system student data shape |
| `Invoice` | Invoice data model |
| `ExamSessionRecord` | Exam session record |
| `AcademyDeliveryMode`, `AcademyEnrollment`, `AcademyPackage` | Academy-specific models |
| `Capability`, `AddOn`, `CapabilityPricing`, `Plan` | Commercial/capability models |
| `Branch`, `BranchStatus` | Multi-branch operator models |
| `TimetableSlot`, `TimetableSlotStatus`, `AttendanceSessionEvent` | Academic scheduling models |
| `Template` | Template model |
| `TeacherPerformanceSnapshot` | Teacher performance |
| `StudentBenchmark`, `TeacherBenchmark`, `InstitutionBenchmark` | Analytics benchmarks |
| `OnboardingMode`, `OnboardingSession`, `OnboardingStatus` | Onboarding state |
| `OwnerEconomicsSnapshot` | Owner economics |
| Various dashboard models | Operations dashboard |

---

## Event Envelope Shape

7-field canonical envelope (PROTECTED — do not modify):

```json
{
  "event_id": "string (UUID)",
  "event_type": "string (e.g., lms.enrollment.created.v1)",
  "tenant_id": "string (required, never null)",
  "producer_service": "string",
  "occurred_at": "ISO 8601 datetime",
  "version": "string (v1)",
  "payload": {}
}
```

Source: `docs/anchors/event-envelope.md`.

---

## Bulk Enrollment Response

```json
{
  "job_id": "string (UUID)",
  "accepted_count": "integer",
  "rejected_count": "integer",
  "submitted_at": "ISO 8601 datetime",
  "results": [
    {
      "user_id": "string",
      "status": "created | skipped | failed",
      "enrollment_id": "string | null",
      "error": "string | null"
    }
  ]
}
```

---

## Learning Path Assignment Response

```json
{
  "learning_path_id": "string",
  "learner_id": "string",
  "tenant_id": "string",
  "status": "string"
}
```
(202 Accepted)

---

## Error Shapes

FastAPI services:
```json
{"detail": "error_code"}
{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}
```

Stdlib services (auth-service, checkout-service):
```json
{"error": "error_code"}
{"error": "error_code", "detail": "message"}
```

Password policy:
```json
{"valid": false, "violations": ["min_length_8", "requires_uppercase", "requires_digit"]}
```

---

## Health Shape (Standard)

```json
{"status": "ok", "service": "<service-name>"}
```

Optionally with version: `{"status": "ok", "service": "...", "version": "v1"}`

---

## Metrics Shape (Standard)

```json
{"service": "<service-name>", "service_up": 1, "<counter_key>": <value>}
```

---

## Related Documents

- `docs/01_backend/API_CONTRACT.md` — endpoint definitions
- `docs/01_backend/ERROR_CONTRACT.md` — error shapes
- `docs/03_fullstack_contracts/VALIDATION_PARITY.md` — validation alignment
- `docs/anchors/event-envelope.md` — event envelope (PROTECTED)
- `docs/anchors/tenant-contract.md` — tenant contract (PROTECTED)
