# Webhook Service

Implements tenant-scoped webhook subscriptions, signed delivery, retry scheduling, and dead-letter handling for LMS domain events.

## Features
- Event subscriptions (`create`, `update`, `delete`) with per-tenant filtering.
- Webhook fan-out delivery for subscribed event types.
- Exponential retry logic with optional jitter and max-attempt enforcement.
- HMAC-SHA256 request signing (`X-LMS-Signature`) + timestamp header (`X-LMS-Timestamp`) + idempotency delivery id (`X-LMS-Delivery-Id`).
- Replay protection and signature verification helper for receiving integrations.
- Endpoint degradation + dead-letter recording after repeated failures.
- Circuit-breaker window for repeated `5xx` on `assessment.graded` deliveries.

## API routes

Authentication: JWT required (`Authorization: Bearer <token>`). Tenant via `X-Tenant-Id` header.

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/webhooks/subscriptions` | Create subscription |
| GET | `/api/v1/webhooks/subscriptions` | List subscriptions for tenant |
| GET | `/api/v1/webhooks/subscriptions/{id}` | Get single subscription |
| PATCH | `/api/v1/webhooks/subscriptions/{id}` | Update endpoint_url or subscribed_events |
| DELETE | `/api/v1/webhooks/subscriptions/{id}` | Delete subscription |
| POST | `/api/v1/webhooks/events` | Publish domain event — fan-out to matching subscriptions |
| POST | `/api/v1/webhooks/deliveries/process` | Run delivery engine |
| GET | `/api/v1/webhooks/deliveries/dead-letter` | List dead-lettered deliveries |
| GET | `/api/v1/webhooks/deliveries/pending` | List pending deliveries |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

Routes added 2026-05-31 (B05-004). JWT added 2026-05-31 (B05-002).

## Module Layout
- `app/main.py`: FastAPI entrypoint — routes, JWT, service wiring.
- `app/service.py`: `WebhookManagementService` — tenant-scoped facade.
- `app/security.py`: JWT validation.
- `src/entities.py`: Domain models.
- `src/webhook_signing.py`: Signing + verification utilities.
- `src/webhook_service.py`: Subscription lifecycle + dispatch + retry orchestration.
- `tests/test_webhook_service.py`: Unit tests for core behavior.
