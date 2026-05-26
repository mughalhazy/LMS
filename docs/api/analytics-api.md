# Analytics API Endpoints

**Type:** API Reference | **Last reviewed:** 2026-05-26

Analytics read endpoints for learner progress, course performance, skills, and compliance reports.

---

| endpoint | method | description |
|---|---|---|
| `/api/v1/analytics/learners/{learnerId}/progress` | GET | Returns learner progress across enrolled courses, including completion percentage, module progress, pacing against schedule, and last activity timestamp. |
| `/api/v1/analytics/courses/{courseId}/performance` | GET | Returns course performance metrics such as enrollment-to-completion funnel, average score, dropout points, time-to-complete, and assessment outcomes. |
| `/api/v1/analytics/skills` | GET | Returns skill analytics aggregated by learner, team, or organization, including proficiency distribution, skill gap trends, and skill acquisition velocity. |
| `/api/v1/analytics/compliance/reports` | POST | Generates compliance reports for required training (e.g., completion status, overdue learners, expiration windows, audit evidence) using filters like policy, region, and date range. |


---

## See also
- `docs/specs/features/learning-analytics-spec.md` � learning analytics spec
- `docs/architecture/AI_04_analytics_pipeline_design.md` � analytics pipeline design
- `docs/designs/analytics-intelligence-layer-design.md` � analytics intelligence layer
