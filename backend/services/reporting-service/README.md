# Reporting Service

Compliance and training report generation for LMS. Spec: `docs/specs/features/compliance-reporting-spec.md`, `docs/specs/features/reporting-spec.md`.

## Capabilities

- Compliance reports — mandatory training status, escalation, exemptions
- Course completion reports — per-learner completion status and duration
- Certification Validity Report — cert expiry, days-until-expiry, recertification flags (B15-033)
- Analytics dashboards with BC-ANALYTICS-02 comparative context
- CSV and PDF export

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/reports/compliance` | Mandatory training compliance report |
| POST | `/api/v1/reports/course-completion` | Course completion report |
| POST | `/api/v1/reports/certification-validity` | Certification validity report (B15-033) |
| POST | `/api/v1/dashboards/analytics` | Analytics dashboard payload |
| POST | `/api/v1/exports` | Export report as CSV or PDF |
| POST | `/api/v1/analytics/compliance/reports` | Alias for compliance report (analytics-api.md) |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## B15 fixes (2026-06-02)

- **B15-033**: `CertificationValidityReport` added — model (`CertificationValidityRecord`), service method (`generate_certification_validity_report`), schema (`CertificationValidityReportResponse`), route (`POST /api/v1/reports/certification-validity`)

## Run

```bash
uvicorn app.main:app --reload --port 8091
```
