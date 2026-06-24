# Review Service Spec

**Type:** Feature Specification
**Service:** `review-service` (`Repo/backend/services/review-service/`)
**Version:** 1.0.0
**Anchor:** `doc-catalogue.md` B15a

---

## 1) Service Purpose

`review-service` is the system of record for course reviews and ratings submitted by learners. It manages the full review lifecycle (submit → moderation → publish/reject), provides filtered review queries, and computes aggregated rating summaries per course.

Scope:
- Review submission, retrieval, and soft-lifecycle management.
- Moderation workflow: pending → published | rejected.
- Per-course rating summary aggregation (average, total, star distribution).

Out of scope:
- Course ownership and catalog management (owned by course-service / catalog-service).
- Learner enrollment state or progress (owned by enrollment-service / progress-service).
- Notification dispatch on moderation actions.
- Review appeal or edit-after-submission flows.

---

## 2) Multi-Tenant Context

All routes require `X-Tenant-Id` header. `X-Actor-Id` header is optional (defaults to `"system"`).

Tenant isolation is enforced at service level: all queries and mutations are scoped to the tenant derived from `X-Tenant-Id`. A request for a review ID that exists but belongs to a different tenant returns `404 Not Found` — not `403` — to avoid cross-tenant information leakage.

---

## 3) Domain Model

### 3.1 Review Entity

| Field | Type | Notes |
|---|---|---|
| `review_id` | string (UUID) | Immutable; assigned on creation |
| `tenant_id` | string | Derived from `X-Tenant-Id` header; immutable after creation |
| `course_id` | string | Course being reviewed; opaque reference |
| `learner_id` | string | Learner who submitted the review; opaque reference |
| `rating` | integer | 1–5 inclusive; validated on submission |
| `body` | string | Non-empty; whitespace-trimmed on save |
| `status` | enum | `pending` \| `published` \| `rejected` |
| `created_at` | datetime (UTC) | Set on creation |
| `updated_at` | datetime (UTC) | Updated on status transition |

### 3.2 Status Lifecycle

```
pending  ──:approve──▶  published
pending  ──:reject───▶  rejected
```

Status transitions are one-way. Approve and reject are idempotent if the review is already in the target status (implementation detail — store returns current state). No path back from published/rejected to pending.

Only `published` reviews contribute to rating summary computations.

### 3.3 Rating Summary Shape

Computed on demand from all `published` reviews for a given `(tenant_id, course_id)` pair.

| Field | Type | Notes |
|---|---|---|
| `course_id` | string | |
| `average_rating` | float | Rounded to 2 decimal places; `0.0` when no published reviews |
| `total_reviews` | integer | Count of published reviews only |
| `distribution` | dict[str, int] | Keys `"1"` – `"5"`; count per star rating |

---

## 4) API Endpoints

Base path: `/api/v1`

Required headers on all routes:
- `X-Tenant-Id` (string, required)
- `X-Actor-Id` (string, optional — defaults to `"system"`)

### 4.1 Submit Review

`POST /api/v1/reviews`

Request body:
```json
{
  "course_id": "course_abc",
  "learner_id": "learner_xyz",
  "rating": 4,
  "body": "Clear explanations and well-paced content."
}
```

Response `201 Created`:
```json
{
  "review_id": "r_001",
  "tenant_id": "tenant_a",
  "course_id": "course_abc",
  "learner_id": "learner_xyz",
  "rating": 4,
  "body": "Clear explanations and well-paced content.",
  "status": "pending",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

Validation errors → `422`.

### 4.2 List Reviews

`GET /api/v1/reviews`

Query parameters (all optional, all combinable):

| Param | Type | Notes |
|---|---|---|
| `course_id` | string | Filter to reviews for a specific course |
| `learner_id` | string | Filter to reviews submitted by a specific learner |
| `status` | string | Filter by status: `pending`, `published`, `rejected` |

Response `200`:
```json
{
  "reviews": [ /* ReviewResponse[] */ ],
  "total": 3
}
```

### 4.3 Get Review

`GET /api/v1/reviews/{review_id}`

Response `200`: ReviewResponse object.
Error `404` if review not found or belongs to a different tenant.

### 4.4 Approve Review

`POST /api/v1/reviews/{review_id}:approve`

Transitions review status to `published`. Updates `updated_at`.

Response `200`: updated ReviewResponse.
Error `404` if not found.

### 4.5 Reject Review

`POST /api/v1/reviews/{review_id}:reject`

Transitions review status to `rejected`. Updates `updated_at`.

Response `200`: updated ReviewResponse.
Error `404` if not found.

### 4.6 Delete Review

`DELETE /api/v1/reviews/{review_id}`

Permanently removes the review record from the store.

Response `204 No Content`.
Error `404` if not found.

### 4.7 Rating Summary

`GET /api/v1/ratings?course_id={course_id}`

`course_id` query parameter is required.

Returns aggregated rating data computed from all `published` reviews in the tenant for the specified course.

Response `200`:
```json
{
  "course_id": "course_abc",
  "average_rating": 4.25,
  "total_reviews": 8,
  "distribution": {"1": 0, "2": 1, "3": 1, "4": 3, "5": 3}
}
```

Zero-state response when no published reviews exist:
```json
{
  "course_id": "course_abc",
  "average_rating": 0.0,
  "total_reviews": 0,
  "distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
}
```

---

## 5) Error Contract

| HTTP Status | Detail | Condition |
|---|---|---|
| `400` | `missing_tenant_id` | `X-Tenant-Id` header absent |
| `404` | ReviewNotFoundError message | Review not found or cross-tenant access |
| `422` | ReviewValidationError message | Rating outside 1–5 or body is blank |

---

## 6) Integration Points

### 6.1 course-service / catalog-service

`course_id` is an opaque reference. review-service does not call course-service to validate course existence — that gate belongs upstream (e.g., at API gateway or calling service).

### 6.2 enrollment-service

`learner_id` is opaque. review-service does not enforce enrollment gating — whether a learner must be enrolled before submitting a review is a business rule enforced upstream.

### 6.3 notification-service

Moderation events (approve/reject) do not currently trigger outbound notifications. This is a known gap — future iteration should emit events for downstream notification dispatch.

---

## See also

- `Repo/backend/services/review-service/README.md` — service run and endpoint reference
- `doc-catalogue.md` B15a — spec registration
