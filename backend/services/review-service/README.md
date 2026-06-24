# Review Service

FastAPI microservice for course reviews and ratings. Manages learner-submitted reviews through a moderation lifecycle (pending → published / rejected) and provides aggregated rating summaries per course.

## REST API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/reviews` | Submit a review (rating 1–5, body text) — created as `pending` |
| `GET` | `/api/v1/reviews` | List reviews (filter: `course_id`, `learner_id`, `status`) |
| `GET` | `/api/v1/reviews/{review_id}` | Get a single review |
| `POST` | `/api/v1/reviews/{review_id}:approve` | Approve review → `published` |
| `POST` | `/api/v1/reviews/{review_id}:reject` | Reject review → `rejected` |
| `DELETE` | `/api/v1/reviews/{review_id}` | Delete a review (admin) |
| `GET` | `/api/v1/ratings?course_id=` | Rating summary — average, total, 1–5 distribution (published reviews only) |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Service metrics |

Tenant via `X-Tenant-Id` header.

## Review lifecycle

```
submit → pending → approve → published
                 → reject  → rejected
```

Only `published` reviews are counted in rating summaries.

## Data model

`Review`: `review_id`, `tenant_id`, `course_id`, `learner_id`, `rating` (1–5), `body`, `status`, `created_at`, `updated_at`

## Structure

- `app/models.py`: `Review` dataclass
- `app/store.py`: `InMemoryReviewStore` — tenant-scoped CRUD + filtering
- `app/service.py`: `ReviewService` — submit, approve, reject, delete, rating summary
- `app/schemas.py`: Pydantic schemas — `SubmitReviewRequest`, `ReviewResponse`, `RatingSummaryResponse`
- `app/main.py`: FastAPI app with all routes

## Run

```bash
cd backend/services/review-service
uvicorn app.main:app --port 8095
```
