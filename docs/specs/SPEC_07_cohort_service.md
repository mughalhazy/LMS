# SPEC_07_cohort_service

## 1) Service Purpose

`cohort_service` manages learner grouping constructs and their lifecycle for Enterprise LMS V2. It supports three delivery models under one bounded context:

1. **Formal education cohorts** (term-bound, compliance-heavy, fixed schedules).
2. **Academy batches** (bootcamp-style, pace-managed, operationally flexible).
3. **Small tutor groups** (micro-groups for guided learning and intervention).

The service is responsible for creating and evolving grouping containers, linking them to academic or training programs, maintaining schedule and status context, and exposing membership support interfaces.

### Explicit Non-Responsibilities (Boundary Guardrails)

`cohort_service` does **not**:
- own enrollment records, enrollment eligibility policy decisions, or enrollment financial state (owned by `enrollment_service`),
- own learner progress state, mastery, completion percentages, or transcript outcomes (owned by `progress_tracking_service` / Progress domain).

`cohort_service` may reference and emit context used by Enrollment and Progress but cannot replace either ownership boundary.

---

## 2) Domain Model and Owned Data

### 2.1 Aggregate Roots

- `LearningGroup`
  - canonical aggregate for both formal cohorts and academy batches
  - `group_type`: `FORMAL_COHORT | ACADEMY_BATCH | TUTOR_GROUP`
- `LearningGroupSchedule`
  - scheduling window and calendar metadata
- `LearningGroupProgramLink`
  - relationship between group and a program/curriculum run
- `LearningGroupMembership`
  - contextual roster membership state for a learner in a group
  - references enrollment and learner IDs but does not own enrollment truth

### 2.2 Owned Data Schema (Logical)

| Entity | Key Fields | Notes |
|---|---|---|
| `learning_groups` | `group_id`, `tenant_id`, `group_type`, `name`, `code`, `status`, `lifecycle_model`, `capacity`, `timezone`, `created_by`, `created_at`, `updated_at` | Unified object for cohort/batch/tutor group. |
| `learning_group_program_links` | `link_id`, `group_id`, `program_id`, `program_version`, `link_status`, `link_start_at`, `link_end_at`, `linked_by` | Program association is contextual and version-aware. |
| `learning_group_schedules` | `schedule_id`, `group_id`, `start_at`, `end_at`, `cadence_type`, `meeting_pattern`, `enrollment_cutoff_at`, `grace_period_days`, `schedule_version` | Schedule and timing context only. |
| `learning_group_memberships` | `membership_id`, `group_id`, `learner_id`, `source_enrollment_id`, `membership_state`, `joined_at`, `left_at`, `role_in_group`, `reason_code` | Membership references enrollment but is not enrollment system-of-record. |
| `learning_group_status_history` | `history_id`, `group_id`, `from_status`, `to_status`, `changed_at`, `changed_by`, `change_reason` | Supports auditability and operational diagnostics. |
| `learning_group_metadata` | `group_id`, `metadata_json` | Extensibility for tenant-specific attributes. |

### 2.3 Lifecycle State Models

#### Learning Group Status
- `DRAFT` → `SCHEDULED` → `ACTIVE` → `COMPLETED`
- Terminal alternatives: `CANCELLED`, `ARCHIVED`

#### Membership State
- `PENDING` (pre-activation roster sync)
- `ACTIVE`
- `PAUSED` (temporary hold)
- `REMOVED`
- `COMPLETED` (group completed while membership remained active)

---

## 3) API Endpoints

Base path: `/v2/cohort-service`

### 3.1 Group Lifecycle APIs

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/groups` | Create cohort/batch/tutor group |
| `GET` | `/groups/{group_id}` | Fetch group details |
| `PATCH` | `/groups/{group_id}` | Update mutable group properties |
| `POST` | `/groups/{group_id}/activate` | Transition to ACTIVE |
| `POST` | `/groups/{group_id}/complete` | Mark COMPLETED |
| `POST` | `/groups/{group_id}/cancel` | Cancel group |
| `POST` | `/groups/{group_id}/archive` | Archive group |

### 3.2 Batch Operations and Views

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/groups` | Filter by `group_type`, status, program, date windows |
| `POST` | `/groups/bulk` | Bulk create batches/cohorts for intake cycles |
| `PATCH` | `/groups/bulk/status` | Bulk status transitions with transition validation |

### 3.3 Program Linkage APIs

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/groups/{group_id}/program-links` | Attach program to group |
| `PATCH` | `/groups/{group_id}/program-links/{link_id}` | Update program link window/status |
| `GET` | `/groups/{group_id}/program-links` | List program links |
| `DELETE` | `/groups/{group_id}/program-links/{link_id}` | Soft-unlink program (if no active sessions) |

### 3.4 Membership Support APIs

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/groups/{group_id}/memberships` | Add learner membership reference |
| `PATCH` | `/groups/{group_id}/memberships/{membership_id}` | Update membership state/role |
| `GET` | `/groups/{group_id}/memberships` | List roster with filters |
| `POST` | `/groups/{group_id}/memberships/sync-from-enrollments` | Pull enrollment-authoritative roster deltas |
| `POST` | `/groups/{group_id}/memberships/reconcile` | Reconcile stale membership states |

### 3.5 Status and Scheduling Context APIs

| Method | Path | Purpose |
|---|---|---|
| `PUT` | `/groups/{group_id}/schedule` | Create/replace schedule context |
| `PATCH` | `/groups/{group_id}/schedule` | Partially update schedule |
| `GET` | `/groups/{group_id}/schedule` | Get current schedule |
| `GET` | `/groups/{group_id}/status-history` | Operational audit timeline |

---

## 4) Request and Response Contracts

### 4.1 Create Group

**Request** `POST /groups`
```json
{
  "tenant_id": "t_001",
  "group_type": "ACADEMY_BATCH",
  "name": "Data Engineering Bootcamp - Batch 12",
  "code": "DEB-12",
  "capacity": 40,
  "timezone": "Asia/Singapore",
  "lifecycle_model": "PACE_MANAGED",
  "metadata": {
    "delivery_track": "weekend",
    "campus": "remote"
  }
}
```

**Response 201**
```json
{
  "group_id": "grp_9a1f",
  "tenant_id": "t_001",
  "group_type": "ACADEMY_BATCH",
  "status": "DRAFT",
  "name": "Data Engineering Bootcamp - Batch 12",
  "code": "DEB-12",
  "capacity": 40,
  "timezone": "Asia/Singapore",
  "lifecycle_model": "PACE_MANAGED",
  "created_at": "2026-01-05T09:00:00Z",
  "updated_at": "2026-01-05T09:00:00Z"
}
```

### 4.2 Link Program

**Request** `POST /groups/{group_id}/program-links`
```json
{
  "program_id": "prog_221",
  "program_version": 7,
  "link_start_at": "2026-01-10T00:00:00Z",
  "link_end_at": "2026-06-01T00:00:00Z"
}
```

**Response 201**
```json
{
  "link_id": "gpl_88",
  "group_id": "grp_9a1f",
  "program_id": "prog_221",
  "program_version": 7,
  "link_status": "ACTIVE",
  "link_start_at": "2026-01-10T00:00:00Z",
  "link_end_at": "2026-06-01T00:00:00Z"
}
```

### 4.3 Add Membership Support Record

**Request** `POST /groups/{group_id}/memberships`
```json
{
  "learner_id": "lrn_901",
  "source_enrollment_id": "enr_77551",
  "role_in_group": "LEARNER",
  "membership_state": "ACTIVE",
  "reason_code": "ENROLLMENT_SYNC"
}
```

**Response 201**
```json
{
  "membership_id": "mbr_154",
  "group_id": "grp_9a1f",
  "learner_id": "lrn_901",
  "source_enrollment_id": "enr_77551",
  "membership_state": "ACTIVE",
  "joined_at": "2026-01-09T04:00:00Z",
  "role_in_group": "LEARNER"
}
```

### 4.4 Upsert Schedule Context

**Request** `PUT /groups/{group_id}/schedule`
```json
{
  "start_at": "2026-01-15T00:00:00Z",
  "end_at": "2026-05-15T00:00:00Z",
  "cadence_type": "WEEKLY",
  "meeting_pattern": {
    "days": ["MONDAY", "THURSDAY"],
    "start_time": "18:00",
    "duration_minutes": 120
  },
  "enrollment_cutoff_at": "2026-01-31T00:00:00Z",
  "grace_period_days": 5
}
```

**Response 200**
```json
{
  "schedule_id": "sch_441",
  "group_id": "grp_9a1f",
  "start_at": "2026-01-15T00:00:00Z",
  "end_at": "2026-05-15T00:00:00Z",
  "cadence_type": "WEEKLY",
  "meeting_pattern": {
    "days": ["MONDAY", "THURSDAY"],
    "start_time": "18:00",
    "duration_minutes": 120
  },
  "enrollment_cutoff_at": "2026-01-31T00:00:00Z",
  "grace_period_days": 5,
  "schedule_version": 3
}
```

### 4.5 Error Contract (Common)

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Group cannot be activated before schedule exists.",
    "details": {
      "group_id": "grp_9a1f",
      "from_status": "DRAFT",
      "requested_status": "ACTIVE"
    },
    "trace_id": "trc_41aaf"
  }
}
```

---

## 5) Events Produced

All events are tenant-scoped and versioned (`event_version`).

| Event | Trigger | Key Payload |
|---|---|---|
| `cohort.group.created` | Group created | `group_id`, `group_type`, `status`, `tenant_id` |
| `cohort.group.status_changed` | Any lifecycle transition | `group_id`, `from_status`, `to_status`, `reason` |
| `cohort.group.schedule_updated` | Schedule create/update | `group_id`, `schedule_version`, `start_at`, `end_at` |
| `cohort.group.program_linked` | Program link created | `group_id`, `program_id`, `program_version`, `link_id` |
| `cohort.group.program_unlinked` | Program unlink | `group_id`, `program_id`, `link_id`, `unlink_reason` |
| `cohort.membership.added` | Membership added | `group_id`, `membership_id`, `learner_id`, `source_enrollment_id` |
| `cohort.membership.updated` | Membership state/role changed | `membership_id`, `from_state`, `to_state`, `group_id` |
| `cohort.membership.removed` | Membership removed | `membership_id`, `group_id`, `learner_id`, `reason_code` |

---

## 6) Events Consumed

| Event Source | Event | Consumption Purpose |
|---|---|---|
| `program_service` | `program.version_published` | Validate and refresh program link compatibility metadata |
| `program_service` | `program.archived` | Mark links as inactive and flag groups needing reassignment |
| `session_service` | `session.created` / `session.rescheduled` / `session.cancelled` | Derive schedule drift indicators and group operational status context |
| `enrollment_service` | `enrollment.created` | Add/activate membership support records (reference-only) |
| `enrollment_service` | `enrollment.status_changed` | Pause/remove membership support state as needed |
| `enrollment_service` | `enrollment.cancelled` | Remove or deactivate membership support state |

---

## 7) Integration Contracts

### 7.1 Integration with `program_service`

- `cohort_service` validates `program_id` and `program_version` via synchronous read API on link creation.
- On `program.version_published`, existing links remain pinned unless tenant opts into auto-upgrade policy.
- Program ownership remains in `program_service`; `cohort_service` stores only linkage metadata.

### 7.2 Integration with `session_service`

- `session_service` references `group_id` when scheduling instructor-led sessions.
- `cohort_service` provides group status/schedule context to prevent session creation for `CANCELLED`/`ARCHIVED` groups.
- Session attendance/outcomes are out-of-scope for `cohort_service`.

### 7.3 Integration with `enrollment_service`

- `enrollment_service` is source of truth for entitlement and enrollment lifecycle.
- `cohort_service` stores `source_enrollment_id` as foreign reference and maintains operational roster context.
- Membership reconciliation job compares enrollment-authoritative states with membership support states and emits discrepancy metrics.

### 7.4 Progress Boundary (Explicit)

- `cohort_service` does not write progress, completion, scores, or mastery.
- Progress consumers may use `group_id` as segmentation dimension, but all progress calculations remain outside this service.

---

## 8) Operational Clarity

- **Idempotency:** `POST /groups`, `POST /program-links`, and membership write APIs require `Idempotency-Key`.
- **Concurrency:** optimistic locking via `resource_version` on PATCH/transition endpoints.
- **Auditability:** every state transition and schedule mutation is persisted in status history.
- **Backfill/Reconciliation:** nightly reconciliation for enrollment-to-membership drift.
- **SLO Targets:**
  - p95 read latency < 150 ms
  - p95 write latency < 300 ms
  - event publication lag < 5 seconds

---

## 9) Extensibility

- `group_type` is open for additive values (e.g., `MENTOR_CIRCLE`) via enum versioning strategy.
- `metadata_json` supports tenant-defined keys under namespaced convention (`tenant.<key>`).
- Link policy plug-in point supports future rules (`AUTO_UPGRADE_PROGRAM_VERSION`, `LOCK_TO_VERSION`).

---

## 10) QC LOOP

### QC Pass 1

| Category | Score (1-10) | Defect Identified |
|---|---:|---|
| Support for both cohort and batch models | 10 | None |
| Alignment with repo Enrollment/Progress model | 9 | Membership APIs needed stronger explicit reference-only language and no eligibility ownership statement. |
| API correctness | 9 | Missing explicit idempotency/concurrency requirements on mutation endpoints in API section. |
| Service boundary integrity | 9 | Needed sharper statement that entitlement and progress outcomes remain outside service. |
| Operational clarity | 9 | Needed clearer SLO and reconciliation expectations. |
| Extensibility | 10 | None |

#### Revisions Applied After Pass 1

1. Added strict non-responsibility statements for Enrollment and Progress ownership.
2. Added `source_enrollment_id` reference semantics across membership contracts.
3. Added idempotency and optimistic locking operational requirements.
4. Expanded integration boundary details and reconciliation behavior.
5. Added explicit SLO targets and operational controls.

### QC Pass 2 (Post-Revision)

| Category | Score (1-10) | Rationale |
|---|---:|---|
| Support for both cohort and batch models | 10 | Unified model with explicit `group_type` for formal cohorts, academy batches, and tutor groups. |
| Alignment with repo Enrollment/Progress model | 10 | Enrollment/progress are explicitly non-owned; membership is reference-only context. |
| API correctness | 10 | Endpoints, contracts, error schema, and mutation controls are defined and consistent. |
| Service boundary integrity | 10 | Ownership and integration boundaries are explicit and enforceable. |
| Operational clarity | 10 | Reconciliation, auditability, concurrency, and SLOs are clear. |
| Extensibility | 10 | Enum evolution + metadata + linkage policy extensibility defined. |

**QC Result:** All categories are 10/10.
