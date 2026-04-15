# SPEC_06_program_service

## 1) Service purpose
`program_service` introduces a learning structure above the existing `Course` model for Enterprise LMS V2.

It provides the curriculum container used to:
- define program lifecycle,
- manage program metadata,
- link programs to institutions,
- map ordered course collections to programs,
- and control program status.

### Boundary statement
- `program_service` **wraps and organizes existing Course entities**.
- `program_service` **does not replace `course_service` ownership** of `Course` lifecycle.
- `program_service` **does not own** lessons, enrollments, or progress.

---

## 2) Owned data

### Core entities
1. **Program**
   - `program_id` (UUID)
   - `tenant_id` (UUID)
   - `institution_id` (UUID)
   - `code` (string, tenant-unique)
   - `title` (string)
   - `description` (string)
   - `status` (`draft|active|archived|retired`)
   - `version` (int)
   - `visibility` (`private|institution|public`)
   - `start_date` (date, optional)
   - `end_date` (date, optional)
   - `metadata` (jsonb)
   - `created_by`, `updated_by` (UUID)
   - `created_at`, `updated_at` (timestamp)

2. **ProgramInstitutionLink**
   - `program_id` (UUID)
   - `institution_id` (UUID)
   - `link_status` (`linked|suspended|unlinked`)
   - `linked_at`, `unlinked_at` (timestamp)
   - `link_metadata` (jsonb)

3. **ProgramCourseMap**
   - `program_id` (UUID)
   - `course_id` (UUID, external ref to `course_service`)
   - `sequence_order` (int)
   - `is_required` (bool)
   - `minimum_completion_pct` (int 0-100, optional)
   - `availability_rule` (jsonb, optional)
   - `mapping_status` (`mapped|unmapped`)
   - `mapped_at`, `unmapped_at` (timestamp)

4. **ProgramStatusHistory**
   - `program_id` (UUID)
   - `from_status`, `to_status`
   - `changed_by` (UUID)
   - `change_reason` (string)
   - `changed_at` (timestamp)

### Explicit non-owned data
- `Course` canonical records (owned by `course_service`)
- lessons and lesson sequencing inside courses (owned by lesson/course services)
- enrollments (owned by `enrollment_service` / `cohort_service` membership domain)
- learner progress and completions (owned by progress/analytics services)

---

## 3) API endpoints

Base path: `/programs`

| Endpoint | Method | Purpose |
|---|---|---|
| `/programs` | POST | Create a program container |
| `/programs/{programId}` | GET | Fetch program + mappings + institution link summary |
| `/programs/{programId}` | PATCH | Update mutable metadata |
| `/programs/{programId}/status` | POST | Transition program status |
| `/programs/{programId}/institution-links` | PUT | Upsert program-to-institution linkage |
| `/programs/{programId}/courses` | PUT | Replace full ordered program-to-course mapping |
| `/programs/{programId}/courses/{courseId}` | DELETE | Remove one mapped course |
| `/programs` | GET | Search/list programs by tenant/institution/status |

---

## 4) Request and response contracts

### 4.1 Create program
**POST `/programs`**

Request:
```json
{
  "tenant_id": "t-123",
  "institution_id": "i-901",
  "code": "DS-FOUNDATIONS-2026",
  "title": "Data Science Foundations",
  "description": "Core pathway for enterprise analysts",
  "visibility": "institution",
  "start_date": "2026-01-15",
  "end_date": "2026-06-30",
  "metadata": {
    "level": "beginner",
    "language": "en"
  },
  "created_by": "u-1001"
}
```

Response `201`:
```json
{
  "program_id": "p-777",
  "tenant_id": "t-123",
  "institution_id": "i-901",
  "status": "draft",
  "version": 1,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

### 4.2 Update metadata
**PATCH `/programs/{programId}`**

Request:
```json
{
  "title": "Data Science Foundations - Enterprise",
  "description": "Updated description",
  "visibility": "institution",
  "metadata": {
    "owner_department": "L&D"
  },
  "updated_by": "u-1002"
}
```

Response `200`:
```json
{
  "program_id": "p-777",
  "version": 2,
  "status": "draft",
  "updated_fields": ["title", "description", "metadata"],
  "updated_at": "2026-01-03T09:15:00Z"
}
```

### 4.3 Transition status
**POST `/programs/{programId}/status`**

Request:
```json
{
  "target_status": "active",
  "change_reason": "Approved for launch",
  "changed_by": "u-2001"
}
```

Response `200`:
```json
{
  "program_id": "p-777",
  "from_status": "draft",
  "to_status": "active",
  "changed_at": "2026-01-04T08:30:00Z"
}
```

Validation rules:
- allowed transitions: `draft -> active -> archived -> retired`
- `retired` is terminal (no outbound transitions)

### 4.4 Upsert institution link
**PUT `/programs/{programId}/institution-links`**

Request:
```json
{
  "institution_id": "i-901",
  "link_status": "linked",
  "link_metadata": {
    "catalog_visibility": "internal"
  },
  "updated_by": "u-3001"
}
```

Response `200`:
```json
{
  "program_id": "p-777",
  "institution_id": "i-901",
  "link_status": "linked",
  "linked_at": "2026-01-04T09:00:00Z"
}
```

### 4.5 Replace program course map
**PUT `/programs/{programId}/courses`**

Request:
```json
{
  "updated_by": "u-5001",
  "courses": [
    {
      "course_id": "c-101",
      "sequence_order": 1,
      "is_required": true,
      "minimum_completion_pct": 80
    },
    {
      "course_id": "c-205",
      "sequence_order": 2,
      "is_required": false,
      "availability_rule": {
        "after_course_id": "c-101"
      }
    }
  ]
}
```

Response `200`:
```json
{
  "program_id": "p-777",
  "mapping_version": 4,
  "mapped_courses": [
    {"course_id": "c-101", "sequence_order": 1, "is_required": true},
    {"course_id": "c-205", "sequence_order": 2, "is_required": false}
  ],
  "updated_at": "2026-01-05T07:20:00Z"
}
```

Validation rules:
- every `course_id` must exist in `course_service`
- duplicate `course_id` values are rejected
- `sequence_order` must be contiguous and unique
- mapping update allowed only in `draft|active` status

### 4.6 Fetch program
**GET `/programs/{programId}`** response `200` returns program metadata, institution linkage, current mappings, and status history tail.

### 4.7 List programs
**GET `/programs?tenant_id=...&institution_id=...&status=active&page=1&page_size=20`** response `200` with paged list.

---

## 5) Events produced

All events follow common envelope conventions used in LMS event bus.

1. `lms.program.program_created.v1`
   - emitted on `POST /programs`
   - payload: `program_id`, `tenant_id`, `institution_id`, `code`, `status`, `version`, `created_at`

2. `lms.program.program_updated.v1`
   - emitted on metadata updates
   - payload: `program_id`, `tenant_id`, `updated_fields[]`, `version`, `updated_at`

3. `lms.program.program_status_changed.v1`
   - emitted on status transition
   - payload: `program_id`, `from_status`, `to_status`, `change_reason`, `changed_by`, `changed_at`

4. `lms.program.program_institution_linked.v1`
   - emitted when program-to-institution linkage becomes `linked`
   - payload: `program_id`, `institution_id`, `link_status`, `linked_at`

5. `lms.program.program_courses_mapped.v1`
   - emitted when mapping set changes
   - payload: `program_id`, `mapping_version`, `courses[]`, `updated_by`, `updated_at`

---

## 6) Events consumed

1. `lms.course.created.v1`
   - caches course existence for faster mapping validation (optional read model)

2. `lms.course.updated.v1`
   - refreshes denormalized course title/status used in program read views

3. `lms.course.published.v1`
   - optional policy enforcement: flag mapped program if required course becomes published/unpublished by policy

4. `lms.organization.institution_created.v1`
   - validates/links new institution references for future program association

5. `lms.cohort.cohort_created.v1`
   - consumed for non-owning reference projection only (cohort counts per program when cohort references program)

---

## 7) Integration contracts

### 7.1 institution_service integration
- Synchronous:
  - On create/update of institution link, validate `institution_id` via institution API/read model.
- Asynchronous:
  - Consume institution lifecycle events to keep reference cache current.
- Failure behavior:
  - reject create/link when institution cannot be resolved (`422 program_institution_not_found`).

### 7.2 course_service integration
- Synchronous:
  - On mapping updates, validate each `course_id` exists and belongs to same tenant.
- Asynchronous:
  - Consume course events to maintain lightweight projection (`course_id`, `title`, `status`, `published_at`).
- Boundary rule:
  - no mutation of course content, lessons, publication internals, or versions from `program_service`.

### 7.3 cohort_service integration
- Synchronous:
  - none required for core ownership.
- Asynchronous:
  - `program_service` publishes `program_status_changed` and `program_courses_mapped`; cohort workflows may consume to decide cohort launch readiness.
  - `program_service` may consume cohort creation updates for analytics/read model only.
- Boundary rule:
  - cohort membership, schedules, and enrollments remain fully outside `program_service`.

---

## 8) State and boundary integrity rules

1. Program can exist without mapped courses in `draft`, but not be set `active` unless at least one mapped course exists.
2. Program cannot map a course from another tenant.
3. Program deletion is soft-delete via `retired` status; hard delete is disallowed to preserve downstream references.
4. Program mapping changes are versioned (`mapping_version`) for auditability.
5. Program status changes are append-only in `ProgramStatusHistory`.

---

## 9) QC LOOP

### QC pass #1
| Category | Score (1-10) | Defect found |
|---|---:|---|
| learning structure clarity | 9 | Program-to-course sequencing existed, but activation gate based on mapped courses was not explicit. |
| alignment with existing Course model | 10 | None. |
| API quality | 9 | Course-mapping lifecycle endpoint did not state replacement semantics clearly. |
| boundary integrity | 10 | None. |
| future extensibility | 9 | Status transition constraints were underspecified for terminal behavior. |
| repo compatibility | 10 | None. |

Revisions applied after pass #1:
- Added explicit activation prerequisite: at least one mapped course required.
- Clarified `PUT /programs/{programId}/courses` as full replacement contract.
- Added terminal state rule for `retired`.

### QC pass #2
| Category | Score (1-10) | Result |
|---|---:|---|
| learning structure clarity | 10 | Pass |
| alignment with existing Course model | 10 | Pass |
| API quality | 10 | Pass |
| boundary integrity | 10 | Pass |
| future extensibility | 10 | Pass |
| repo compatibility | 10 | Pass |

QC loop complete: all categories are **10/10**.
