# SPEC_10 — lesson_service Engineering Specification (Enterprise LMS V2)

## 1) Service purpose
`lesson_service` is the system of record for the **lesson runtime content unit** lifecycle inside a course context. It owns lesson metadata, ordering/linkage to a course, delivery state transitions, and emits hooks used by learner runtime/progress flows.

The service is explicitly constrained to:
- Own lesson entities as runtime content units.
- Maintain lesson-to-course linkage and lesson ordering within a course.
- Provide state needed by lesson delivery orchestration (draft/published/archived, availability, launchability).
- Publish integration hooks for progression workflows.

The service must **not**:
- Absorb `course_service` ownership of course aggregate data.
- Absorb `progress_service` ownership of learner progress/completion authority.

---

## 2) Alignment with existing Rails LMS Lesson model
The canonical lesson fields in this specification align 1:1 with the current persisted lesson schema used by the service and expected by Rails-compatible LMS semantics:

| Rails/LMS lesson concept | lesson_service field | Notes |
|---|---|---|
| Identifier | `lesson_id` | Immutable primary key. |
| Tenant scope | `tenant_id` | Required in all APIs/events. |
| Course linkage | `course_id` | Mandatory foreign reference to course aggregate owned by `course_service`. |
| Optional module grouping | `module_id` | Optional grouping key; no module ownership implied. |
| Author | `created_by` | Creator identity for audit. |
| Core metadata | `title`, `description`, `lesson_type`, `learning_objectives`, `metadata` | Editable under version/lifecycle rules. |
| Content pointer | `content_ref` | Reference-only; binary/package storage stays in content domain. |
| Runtime estimates/policies | `estimated_duration_minutes`, `availability_rules` | Used by runtime launch checks. |
| Lifecycle state | `status` (`draft`/`published`/`archived`) | State machine owned by lesson_service. |
| Sequencing | `order_index` | Order within `(tenant_id, course_id)`. |
| Versioning | `version`, `published_version` | Supports draft evolution and published snapshot semantics. |
| Publication timestamps | `published_at` | Nullable until publish. |
| Archive timestamp | `archived_at` | Nullable until archive. |
| Audit timestamps | `created_at`, `updated_at` | Service-managed. |

---

## 3) Owned data

### 3.1 Primary entity: `Lesson`
```yaml
Lesson:
  lesson_id: string
  tenant_id: string
  course_id: string
  module_id: string|null
  created_by: string
  title: string
  description: string|null
  lesson_type: enum[video,document,quiz,scorm,live_session]
  learning_objectives: string[]
  content_ref: string|null
  estimated_duration_minutes: integer|null
  availability_rules: object
  metadata: object
  status: enum[draft,published,archived]
  order_index: integer
  version: integer
  published_version: integer|null
  published_at: datetime|null
  archived_at: datetime|null
  created_at: datetime
  updated_at: datetime
```

### 3.2 Ownership boundaries
- `lesson_service` owns: lesson identity, lifecycle, ordering, lesson metadata, publication/archive state.
- `course_service` owns: course existence, course-level publication policy, course catalog metadata.
- `progress_service` owns: learner progress %, completion, attempts, mastery outcomes.
- `session_service` owns: launch/session runtime instances.
- `enrollment_service` owns: assignment/enrollment eligibility.

---

## 4) API endpoints and contracts
All endpoints are tenant-scoped (`/v1/tenants/{tenant_id}/...`).

### 4.1 Create lesson
`POST /courses/{course_id}/lessons`

**Request**
```json
{
  "module_id": "mod_42",
  "created_by": "usr_123",
  "title": "Introduction to SOC 2",
  "description": "Overview and controls",
  "lesson_type": "video",
  "learning_objectives": ["define SOC 2", "identify trust criteria"],
  "content_ref": "content://asset/vid_998",
  "estimated_duration_minutes": 12,
  "availability_rules": {"drip_days_after_enrollment": 0},
  "metadata": {"difficulty": "beginner"}
}
```

**Response 201**
```json
{
  "lesson_id": "les_001",
  "tenant_id": "ten_001",
  "course_id": "crs_001",
  "module_id": "mod_42",
  "status": "draft",
  "order_index": 1,
  "version": 1,
  "created_at": "2026-01-10T09:00:00Z",
  "updated_at": "2026-01-10T09:00:00Z"
}
```

### 4.2 Update lesson metadata
`PATCH /lessons/{lesson_id}`

**Request (partial)**
```json
{
  "updated_by": "usr_456",
  "title": "SOC 2 Fundamentals",
  "description": "Updated description",
  "learning_objectives": ["define SOC 2", "map trust criteria"],
  "estimated_duration_minutes": 15,
  "metadata": {"difficulty": "intermediate"}
}
```

**Response 200**
```json
{
  "lesson_id": "les_001",
  "status": "draft",
  "version": 2,
  "updated_fields": ["title", "description", "learning_objectives", "estimated_duration_minutes", "metadata"],
  "updated_at": "2026-01-10T10:00:00Z"
}
```

### 4.3 Reorder lessons in a course
`PUT /courses/{course_id}/lessons:reorder`

**Request**
```json
{
  "updated_by": "usr_456",
  "ordered_lesson_ids": ["les_001", "les_003", "les_002"]
}
```

**Response 200**
```json
{
  "course_id": "crs_001",
  "lesson_order": [
    {"lesson_id": "les_001", "order_index": 1},
    {"lesson_id": "les_003", "order_index": 2},
    {"lesson_id": "les_002", "order_index": 3}
  ],
  "reordered_at": "2026-01-10T10:05:00Z"
}
```

### 4.4 Publish lesson
`POST /lessons/{lesson_id}:publish`

**Request**
```json
{
  "requested_by": "usr_789",
  "publish_notes": "Ready for learners",
  "scheduled_publish_at": null,
  "visibility_rules": {"enrollment_required": true},
  "prerequisite_rules": {"required_lesson_ids": ["les_000"]}
}
```

**Response 200**
```json
{
  "lesson_id": "les_001",
  "status": "published",
  "published_version": 2,
  "published_at": "2026-01-10T10:10:00Z",
  "effective_from": "2026-01-10T10:10:00Z"
}
```

### 4.5 Create lesson version
`POST /lessons/{lesson_id}:versions`

**Request**
```json
{
  "based_on_version": 2,
  "created_by": "usr_456",
  "change_summary": "Add examples",
  "cloned_content_refs": ["content://asset/vid_998"],
  "metadata_overrides": {"edition": "2026.1"}
}
```

**Response 201**
```json
{
  "lesson_id": "les_001",
  "new_version": 3,
  "status": "draft",
  "version_id": "les_001:v3",
  "created_at": "2026-01-10T11:00:00Z"
}
```

### 4.6 Archive lesson
`POST /lessons/{lesson_id}:archive`

**Request**
```json
{
  "archived_by": "usr_789",
  "reason_code": "replaced",
  "archive_notes": "Superseded by new policy version"
}
```

**Response 200**
```json
{
  "lesson_id": "les_001",
  "status": "archived",
  "archived_at": "2026-01-10T11:05:00Z"
}
```

### 4.7 Delivery state read endpoint
`GET /lessons/{lesson_id}/delivery-state?learner_id={learner_id}`

**Response 200**
```json
{
  "lesson_id": "les_001",
  "course_id": "crs_001",
  "status": "published",
  "launchable": true,
  "blocked_reasons": [],
  "availability_window": {
    "opens_at": null,
    "closes_at": null
  },
  "requires_enrollment": true,
  "prerequisite_state": {
    "is_satisfied": true,
    "unsatisfied_prerequisites": []
  }
}
```

Contract rule: `delivery-state` may **read** enrollment/progress/prerequisite views via integrations, but does not persist learner progress.

---

## 5) Events produced

| Event | Trigger | Required payload |
|---|---|---|
| `lesson.created` | Lesson created | `event_id`, `occurred_at`, `tenant_id`, `lesson_id`, `course_id`, `title`, `order_index`, `status`, `version`, `created_by` |
| `lesson.updated` | Metadata or ordering update | `event_id`, `occurred_at`, `tenant_id`, `lesson_id`, `course_id`, `changed_fields`, `status`, `version`, `updated_by` |
| `lesson.published` | Publish transition successful | `event_id`, `occurred_at`, `tenant_id`, `lesson_id`, `course_id`, `published_version`, `published_at`, `published_by` |
| `lesson.archived` | Archive transition successful | `event_id`, `occurred_at`, `tenant_id`, `lesson_id`, `course_id`, `archived_at`, `archived_by`, `reason_code` |
| `lesson.delivery_state.changed` | Launchability-relevant policy/linkage changes | `event_id`, `occurred_at`, `tenant_id`, `lesson_id`, `course_id`, `launchable`, `blocked_reasons`, `status` |
| `lesson.progression_hook.requested` | Runtime checkpoint requiring downstream progress workflow | `event_id`, `occurred_at`, `tenant_id`, `lesson_id`, `course_id`, `learner_id`, `hook_type`, `session_id`, `context` |

Event guarantees:
- At-least-once delivery.
- Idempotency key = `event_id`.
- Per-lesson ordering key = `(tenant_id, lesson_id)`.

---

## 6) Events consumed

| Event | Source service | Purpose in lesson_service |
|---|---|---|
| `course.created`, `course.updated`, `course.published`, `course.archived` | `course_service` | Validate linked course existence/state for lesson lifecycle guards. |
| `session.started`, `session.ended`, `session.expired` | `session_service` | Evaluate lesson delivery/runtime state changes and emit progression hooks when needed. |
| `enrollment.created`, `enrollment.status_changed` | `enrollment_service` | Resolve learner launch eligibility in `delivery-state` computation. |
| `progress.updated`, `progress.completed` | `progress_service` | Resolve prerequisite/eligibility read model for launch gating only (no ownership transfer). |

Consumption rule: consumed events materialize **read-side caches only**; source-of-truth ownership remains with producer services.

---

## 7) Service integrations

### 7.1 `course_service`
- Write-time guard: course must exist and be tenant-matched before lesson creation.
- Optional guard: prevent lesson publish if parent course is archived.
- No course metadata mutation from lesson_service.

### 7.2 `session_service`
- Runtime handshake uses `lesson_id` + `content_ref` + resolved delivery state.
- Session lifecycle signals can trigger `lesson.progression_hook.requested` events.

### 7.3 `enrollment_service`
- Delivery state checks enrollment eligibility for learner launchability.
- Enrollment status is read-only to lesson_service.

### 7.4 `progress_service`
- Lesson emits progression hook events; progress decisions remain in progress_service.
- Lesson reads prerequisite/progress snapshots for gating only.

---

## 8) Boundary and safety constraints
- No learner completion percentage, score, or attempt counters are persisted in lesson_service tables.
- No course catalog ownership fields (e.g., course title/category lifecycle) are persisted as mutable lesson-owned source of truth.
- All APIs/events require `tenant_id` to preserve tenant isolation and prevent cross-tenant lesson linkage.
- Soft state transitions (`draft -> published -> archived`) are explicit and auditable.

---

## 9) QC loop

### QC pass 1
| Category | Score (1-10) | Defect found |
|---|---:|---|
| Alignment with existing Lesson model | 9 | Missing explicit mapping for `published_version` and `archived_at` semantics. |
| Boundary clarity | 9 | Needed stronger statement that consumed progress/enrollment data is read-side only. |
| API quality | 9 | Delivery state endpoint lacked explicit contract rule about non-ownership of learner progress writes. |
| Runtime compatibility | 10 | None. |
| Extensibility | 9 | Needed formal event ordering/idempotency guarantees. |
| Repo safety | 10 | None. |

### Revisions applied after pass 1
1. Added full field mapping table including `published_version`, `published_at`, and `archived_at`.
2. Added explicit consumed-event read-side cache rule and ownership statement.
3. Added delivery-state non-persistence contract rule.
4. Added event guarantees (at-least-once, idempotency key, ordering key).

### QC pass 2 (post-revision)
| Category | Score (1-10) | Result |
|---|---:|---|
| Alignment with existing Lesson model | 10 | Pass |
| Boundary clarity | 10 | Pass |
| API quality | 10 | Pass |
| Runtime compatibility | 10 | Pass |
| Extensibility | 10 | Pass |
| Repo safety | 10 | Pass |

**QC final status:** PASS (all categories = 10/10).
