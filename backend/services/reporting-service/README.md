# Reporting Service

Reporting service for LMS analytics and compliance reporting.

## Capabilities
- Generate compliance reports.
- Generate course completion reports.
- Produce analytics dashboard payloads with sentiment tracking and engagement trends.
- Export reports as CSV and PDF payloads.

## API Endpoints
- `POST /reports/compliance`
- `POST /reports/course-completion`
- `POST /dashboards/analytics`
- `POST /exports`

## Local Run
```bash
uvicorn app.main:app --reload --port 8091
```

## Tests
```bash
pytest
```
