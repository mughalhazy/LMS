# Event Ingestion Service

The Event Ingestion Service provides high-volume, tenant-scoped ingestion of LMS learning activity events for the analytics pipeline.

## Responsibilities
- Ingest learning activity events through single-event and batch APIs.
- Validate incoming payloads against supported analytics event schemas.
- Persist raw, validated, and rejected events for downstream analytics and replay.
- Keep tenant-scoped streams isolated (`raw`, `validated`, `rejected`).

## API Endpoints
- `POST /api/v1/events/ingest`
- `POST /api/v1/events/ingest/batch`
- `GET /api/v1/events/streams/{tenant_id}`
- `GET /api/v1/events/metrics`

## Event Topics
- `analytics.events.raw`
- `analytics.events.validated`
- `analytics.events.rejected`

## Run
```bash
python -m app.main
```

## Test
```bash
pytest tests/test_event_ingestion_service.py
```
