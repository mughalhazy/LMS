# SPEC_12_progress_service

## 1. Service Purpose

`progress_service` is the system of record for learner progress and completion state in Enterprise LMS V2. It owns *progress tracking* and *progress-derived completion outcomes* at lesson, course, and learning-path levels, while remaining strictly aligned with the existing Rails LMS `Progress` model semantics (`progress_id`, `enrollment_id`, `user_id`, `course_id`, optional `lesson_id`, `percent_complete`, `status`, `last_activity_at`).

This service:
- records and updates learner progress events,
- computes completion state transitions,
- exposes operational read APIs for lesson/course/path progression,
- publishes progress and completion events for downstream services.

This service does **not**:
- own enrollment lifecycle (owned by `enrollment_service`),
- own assessment attempts/scores as source-of-truth (owned by `assessment_service`).

## 2. Authoritative Model Alignment (Rails Compatibility)

The canonical Progress entity in V2 maps 1:1 to existing repository semantics:

| Rails LMS Progress semantic | `progress_service` field | Notes |
|---|---|---|
| `progress_id` | `progress_id` (UUID) | Stable identifier for a progress record. |
| `enrollment_id` | `enrollment_id` (UUID) | Required; binds progress to enrollment-owned context. |
| `user_id` | `learner_id` (UUID) | API naming keeps `learner` domain term; event payloads may include `user_id` alias where needed. |
| `course_id` | `course_id` (UUID) | Required for course-scoped progress. |
| `lesson_id` (nullable) | `lesson_id` (UUID, nullable) | Null for course-level aggregate records. |
| `percent_complete` | `progress_percentage` (0..100) | Stored as numeric percentage. |
| `status` | `status` enum | `not_started`, `in_progress`, `completed`, `passed`, `failed` (where assessment policy applies). |
| `last_activity_at` | `last_activity_at` (timestamp) | Updated on any progress mutation. |

Compatibility rules:
1. Every mutable progress state change persists to Progress-owned storage keyed by `progress_id` and `enrollment_id`.
2. Course completion is derived from lesson progression + completion policy, but persisted as progress state (`status=completed`, `progress_percentage=100`).
3. No enrollment or assessment records are denormalized as authoritative data; only foreign-key references and snapshot fields permitted.

## 3. Owned Data

### 3.1 Aggregates and Tables

1. **progress_records** (authoritative)
   - `progress_id` (PK)
   - `tenant_id`
   - `enrollment_id`
   - `learner_id`
   - `course_id`
   - `lesson_id` (nullable)
   - `progress_percentage`
   - `status`
   - `last_activity_at`
   - `completed_at` (nullable)
   - `created_at`, `updated_at`

2. **course_progress_snapshots** (owned projection)
   - `tenant_id`, `learner_id`, `course_id`, `enrollment_id`
   - `completed_lessons`, `total_lessons`
   - `progress_percentage`
   - `completion_status`
   - `started_at`, `completed_at`, `last_activity_at`
   - `final_score` (nullable; copied from assessment completion event)
   - `certificate_id` (nullable link)

3. **learning_path_progress_snapshots** (owned projection)
   - `tenant_id`, `learner_id`, `learning_path_id`
   - `assigned_course_ids`, `completed_course_ids`
   - `progress_percentage`
   - `current_course_id` (nullable)
   - `status`
   - `expected_completion_date` (nullable)
   - `last_activity_at`

4. **completion_metrics_daily** (owned analytics-ready fact table)
   - `tenant_id`, `metric_date`
   - `course_id` (nullable), `learning_path_id` (nullable)
   - `started_count`, `completed_count`, `completion_rate`
   - `avg_time_to_complete_seconds`
   - `avg_progress_percentage`

### 3.2 Explicit Non-Owned Data

- Enrollment status transitions, activation/withdrawal decisions (`enrollment_service` only).
- Assessment attempts, grading policy, and raw attempt events (`assessment_service` only).
- Certificate issuance records and artifacts (`certificate_service` only).

## 4. API Endpoints

Base path: `/api/v1/progress`

### 4.1 Upsert Lesson Progress
**POST** `/api/v1/progress/lessons/{lesson_id}/upsert`

Purpose: idempotently apply learner lesson progression updates.

Request:
```json
{
  "tenant_id": "t-123",
  "learner_id": "u-456",
  "course_id": "c-789",
  "enrollment_id": "e-111",
  "progress_percentage": 75.0,
  "status": "in_progress",
  "time_spent_seconds_delta": 240,
  "attempt_count": 2,
  "occurred_at": "2026-01-20T10:15:00Z",
  "idempotency_key": "evt-lesson-abc"
}
```

Response `200`:
```json
{
  "progress_id": "p-222",
  "tenant_id": "t-123",
  "learner_id": "u-456",
  "course_id": "c-789",
  "lesson_id": "l-333",
  "enrollment_id": "e-111",
  "progress_percentage": 75.0,
  "status": "in_progress",
  "last_activity_at": "2026-01-20T10:15:00Z",
  "completed_at": null
}
```

### 4.2 Mark Lesson Complete
**POST** `/api/v1/progress/lessons/{lesson_id}/complete`

Purpose: transition a lesson progress record to completed (100%).

Request:
```json
{
  "tenant_id": "t-123",
  "learner_id": "u-456",
  "course_id": "c-789",
  "enrollment_id": "e-111",
  "score": 92.5,
  "time_spent_seconds": 1200,
  "attempt_count": 3,
  "completed_at": "2026-01-20T11:00:00Z",
  "idempotency_key": "evt-lesson-complete-01"
}
```

Response `200`:
```json
{
  "lesson_progress": {
    "progress_id": "p-lesson-01",
    "status": "completed",
    "progress_percentage": 100.0,
    "completed_at": "2026-01-20T11:00:00Z"
  },
  "course_progress": {
    "completion_status": "in_progress",
    "progress_percentage": 80.0,
    "completed_lessons": 8,
    "total_lessons": 10
  }
}
```

### 4.3 Get Learner Progress Summary
**GET** `/api/v1/progress/learners/{learner_id}?tenant_id={tenant_id}`

Response `200`:
```json
{
  "tenant_id": "t-123",
  "learner_id": "u-456",
  "courses": [
    {
      "course_id": "c-789",
      "enrollment_id": "e-111",
      "completion_status": "in_progress",
      "progress_percentage": 80.0,
      "started_at": "2026-01-10T08:00:00Z",
      "completed_at": null,
      "last_activity_at": "2026-01-20T11:00:00Z"
    }
  ],
  "lessons": [],
  "learning_paths": []
}
```

### 4.4 Get Course Progress
**GET** `/api/v1/progress/learners/{learner_id}/courses/{course_id}?tenant_id={tenant_id}`

Response `200`:
```json
{
  "tenant_id": "t-123",
  "learner_id": "u-456",
  "course_id": "c-789",
  "enrollment_id": "e-111",
  "completion_status": "completed",
  "progress_percentage": 100.0,
  "final_score": 88.0,
  "started_at": "2026-01-10T08:00:00Z",
  "completed_at": "2026-01-25T09:00:00Z",
  "total_time_spent_seconds": 5400,
  "certificate_id": "cert-444"
}
```

### 4.5 Assign / Update Learning Path Progress Context
**POST** `/api/v1/progress/learning-paths/{learning_path_id}/assignments`

Request:
```json
{
  "tenant_id": "t-123",
  "learner_id": "u-456",
  "assigned_course_ids": ["c-789", "c-790"],
  "expected_completion_date": "2026-02-28",
  "idempotency_key": "evt-path-assign-01"
}
```

Response `202`:
```json
{
  "learning_path_id": "lp-555",
  "status": "in_progress",
  "progress_percentage": 0.0,
  "current_course_id": "c-789"
}
```

## 5. Event Contracts

### 5.1 Events Produced

1. **LessonCompletionTracked**
   - Trigger: lesson progress reaches completed.
   - Payload:
     - `tenant_id`, `learner_id`, `course_id`, `lesson_id`, `enrollment_id`
     - `completion_status` (`completed`)
     - `score`, `time_spent_seconds`, `completed_at`, `attempt_count`

2. **CourseCompletionTracked**
   - Trigger: course progress reaches completed policy threshold.
   - Payload:
     - `tenant_id`, `learner_id`, `course_id`, `enrollment_id`
     - `completion_status`, `final_score`, `started_at`, `completed_at`
     - `total_time_spent_seconds`, `certificate_id` (nullable)

3. **LearningPathProgressUpdated**
   - Trigger: assigned course set changes OR course completion updates path aggregate.
   - Payload:
     - `tenant_id`, `learner_id`, `learning_path_id`
     - `assigned_course_ids`, `completed_course_ids`, `progress_percentage`
     - `current_course_id`, `status`, `last_activity_at`, `expected_completion_date`

4. **ProgressUpdated** (`progress.updated` canonical)
   - Trigger: any Progress record upsert.
   - Payload:
     - `progress_id`, `enrollment_id`, `user_id`, `course_id`, `lesson_id` (nullable)
     - `percent_complete`, `status`, `last_activity_at`

5. **ProgressCompleted** (`progress.completed` canonical)
   - Trigger: course-level record transitions to completed.
   - Payload:
     - `progress_id`, `enrollment_id`, `user_id`, `course_id`, `completed_at`

### 5.2 Events Consumed

1. **`lesson.completed`** (from `lesson_service`)
   - Use: authoritative lesson completion signal to upsert lesson progress.

2. **`enrollment.created` / `enrollment.activated` / `enrollment.withdrawn`** (from `enrollment_service`)
   - Use: initialize progress context, enforce progress mutability guards for inactive enrollments.

3. **`assessment.attempt.submitted` / `assessment.result.finalized`** (from `assessment_service`)
   - Use: update score-linked progress metadata and completion eligibility inputs.

4. **`certificate.issued`** (from `certificate_service`)
   - Use: decorate completed course snapshot with `certificate_id`; no ownership takeover.

## 6. Integration Contracts by Service

### 6.1 `lesson_service`
- `progress_service` consumes lesson completion events and optionally lesson view/progression ticks.
- `lesson_service` remains owner of lesson content state and lesson availability rules.

### 6.2 `enrollment_service`
- Enrollment identity and lifecycle remain external.
- `progress_service` requires valid `enrollment_id` for all write endpoints.
- If enrollment is not active, writes return `409 enrollment_not_active`.

### 6.3 `assessment_service`
- Assessment outcomes are inputs into progress completion policy.
- `progress_service` stores only snapshot values (`final_score`, pass/fail outcome) needed for progress read models.

### 6.4 `certificate_service`
- `progress_service` emits course completion events.
- `certificate_service` issues certificates and emits `certificate.issued`.
- `progress_service` links resulting `certificate_id` into course progress snapshot.

## 7. Constraints and Guardrails

1. Progress remains the authoritative learning progress record for Enterprise LMS V2.
2. Enrollment ownership is external and must not be absorbed.
3. Assessment ownership is external and must not be absorbed.
4. API writes are idempotent via `idempotency_key`.
5. Tenant boundaries are strict (`tenant_id` required and indexed in every owned table).
6. Backward-compatibility adapters provide both `learner_id` and `user_id` aliases in event serialization where needed.
7. **Do not absorb Enrollment ownership.**
8. **Do not absorb Assessment ownership.**

## 8. QC LOOP

### QC Pass 1

| Category | Score (1-10) | Defect |
|---|---:|---|
| alignment with existing Progress model | 9 | Canonical event aliasing (`user_id` vs `learner_id`) was not explicitly required in serialization. |
| progress ownership clarity | 10 | None. |
| API quality | 9 | Idempotency/error semantics not explicit for inactive enrollment writes. |
| integration readiness | 10 | None. |
| analytics readiness | 9 | Completion metrics storage/output cadence not explicit enough. |
| repo compatibility | 10 | None. |

### Revisions Applied

1. Added explicit aliasing rule for `user_id`/`learner_id` compatibility.
2. Added enrollment inactive guard response (`409 enrollment_not_active`).
3. Added `completion_metrics_daily` owned table for analytics-ready metrics.
4. Added API idempotency guardrail requirement.

### QC Pass 2

| Category | Score (1-10) | Defect |
|---|---:|---|
| alignment with existing Progress model | 10 | None. |
| progress ownership clarity | 10 | None. |
| API quality | 10 | None. |
| integration readiness | 10 | None. |
| analytics readiness | 10 | None. |
| repo compatibility | 10 | None. |

**QC Result:** All categories are 10/10.
