# Learning Analytics Service

FastAPI microservice providing aggregated learning, engagement, economics, and AI-signal analytics across tenants, courses, cohorts, and learning paths.

## REST API

Spec: `Repo/docs/specs/learning-analytics-service-spec.md` | Routes: `api_endpoints.yaml`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analytics/events` | Ingest raw learning events |
| `GET` | `/api/v1/analytics/courses/{course_id}/completion` | Course completion analytics |
| `GET` | `/api/v1/analytics/courses/{course_id}/engagement` | Learner engagement metrics |
| `GET` | `/api/v1/analytics/courses/{course_id}/engagement/trends` | Sentiment-aware engagement trends |
| `GET` | `/api/v1/analytics/courses/{course_id}/engagement/dashboard` | Engagement dashboard (widgets) |
| `GET` | `/api/v1/analytics/courses/{course_id}/performance` | Learning and assessment performance |
| `GET` | `/api/v1/analytics/courses/{course_id}/ai-signals` | AI service signals (tutor + recommendation) |
| `GET` | `/api/v1/analytics/courses/{course_id}/risk-insights` | Learner risk insights + automation events |
| `GET` | `/api/v1/analytics/courses/{course_id}/network-effects` | Network effect score and benchmarking |
| `GET` | `/api/v1/analytics/cohorts/{cohort_id}/performance` | Cohort performance metrics |
| `GET` | `/api/v1/analytics/learning-paths/{learning_path_id}/completion` | Learning path completion analysis |
| `GET` | `/api/v1/analytics/economics/revenue` | Revenue metrics by tenant/owner |
| `GET` | `/api/v1/analytics/economics/cashflow` | Cashflow metrics |
| `GET` | `/api/v1/analytics/economics/profitability` | Profitability metrics |
| `GET` | `/api/v1/analytics/economics` | Combined owner economics |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Service metrics |

Query params (all GET routes): `start_at`, `end_at` (ISO datetime), `cohort_id`, `owner_id` where applicable. Tenant via `X-Tenant-Id` header.

## Metric formulas

- **Completion rate**: `completed_learners / enrolled_learners * 100`
- **Engagement score**: `0.35*active_minutes + 0.25*content_interactions + 0.20*assessment_attempts + 0.20*discussion_actions` (normalised per dimension)
- **Sentiment**: per-learner average of event-level sentiment scores → positive (≥ 0.25) / neutral / negative (≤ -0.25)
- **Engagement trends**: daily snapshots with directional delta tracking
- **Network effect score**: weighted combination of completion, engagement, assessment, collaboration ratio, and momentum
- **Learner risk score**: composite of low-engagement, drop-off, and poor-performance signals (0–100)

## Structure

- `app/repository.py`: `AnalyticsRepository` — in-memory event store, ingestion, and query methods
- `app/service.py`: `LearningAnalyticsService` — all metric computations
- `app/main.py`: `LearningAnalyticsAPI` adapter + FastAPI app with all routes
- `app/models.py`: domain dataclasses — enrollments, completions, activities, assessment attempts, path snapshots, revenue/cashflow records
- `app/schemas.py`: query dataclasses — `TimeWindowQuery`, `CourseAnalyticsQuery`, `LearningPathAnalyticsQuery`

## Run

```bash
cd backend/services/learning-analytics-service
uvicorn app.main:app --port 8092
```

## Run tests

```bash
cd backend/services/learning-analytics-service
pytest -q
```
