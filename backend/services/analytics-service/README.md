# analytics-service

Platform intelligence layer — learning analytics, performance benchmarking, executive reporting, cost tracking, and profitability insights. All outputs wrapped in BC-ANALYTICS-01 insight envelope. All metrics carry BC-ANALYTICS-02 comparative context. Distinct from learning-analytics-service (learner-specific) and reporting-service (compliance). Spec: `docs/specs/analytics-service-spec.md` (MS§5.16).

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/analytics/insights/learner/{id}` | Learner insights |
| GET | `/api/v1/analytics/learners/{id}/progress` | Learner progress (spec path alias) |
| GET | `/api/v1/analytics/insights/tenant` | Tenant-level insights |
| GET | `/api/v1/analytics/benchmark` | Benchmark comparison |
| GET | `/api/v1/analytics/skills` | Skill analytics stub |
| GET | `/api/v1/analytics/branches` | Cross-branch analytics — HQ aggregate + per-branch (B15-020) |
| GET | `/api/v1/analytics/costs` | Cost tracking — compute/AI/storage/analytics (B15-030) |
| GET | `/api/v1/analytics/profitability` | Profitability — revenue minus cost with BC-ECON-01 action (B15-031/032) |
| POST | `/api/v1/analytics/events` | Ingest analytics events |
| GET | `/health` | Health check |

## B15 fixes (2026-06-02)

- **B15-019**: Branch access enforcement — `X-Scope-Type: branch` requires `X-Branch-Ids` header; `hq_admin` gets full cross-branch access
- **B15-020**: `GET /api/v1/analytics/branches` — cross-branch analytics with aggregate + per-branch breakdown for hq_admin
- **B15-030**: `GET /api/v1/analytics/costs` — CAP-COST-TRACKING; compute/AI/storage costs with suggested_action
- **B15-031**: `GET /api/v1/analytics/profitability` — CAP-PROFITABILITY-INSIGHTS; revenue-minus-cost margin
- **B15-032**: BC-ECON-01 — every economic insight carries embedded `suggested_action`

## Gateway

Route: `/api/v1/analytics` | Rate limit: `public-api-standard`
