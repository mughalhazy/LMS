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

## Module Layout
- `src/entities.py`: Domain models.
- `src/webhook_signing.py`: Signing + verification utilities.
- `src/webhook_service.py`: Subscription lifecycle + dispatch + retry orchestration.
- `tests/test_webhook_service.py`: Unit tests for core behavior.
