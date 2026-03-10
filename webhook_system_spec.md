event
webhook_payload
delivery_rules

subscription.created
{"subscription_id":"sub_12345","tenant_id":"tenant_abc","endpoint_url":"https://client.example.com/webhooks/lms","subscribed_events":["course.published","enrollment.completed"],"status":"active","created_at":"2026-01-18T10:12:33Z"}
Delivered immediately after subscription creation. Retries on non-2xx/timeouts with exponential backoff (30s, 2m, 10m, 1h, 6h; max 8 attempts). Every request includes HMAC-SHA256 signature in `X-LMS-Signature`, timestamp in `X-LMS-Timestamp`, and unique `X-LMS-Delivery-Id`; receivers must verify signature with shared secret and reject timestamps older than 5 minutes.

subscription.updated
{"subscription_id":"sub_12345","tenant_id":"tenant_abc","endpoint_url":"https://client.example.com/webhooks/lms-v2","subscribed_events":["course.published","enrollment.completed","assessment.graded"],"status":"active","updated_at":"2026-01-20T08:04:10Z"}
Delivered in-order per subscription using per-endpoint queue. Retries use same backoff policy with jitter to avoid thundering herd. If all retries fail, event is dead-lettered and visible in webhook delivery logs. Signature and timestamp verification required on every retry; payload is immutable across attempts.

course.published
{"event_id":"evt_90001","event_type":"course.published","occurred_at":"2026-01-22T14:20:00Z","tenant_id":"tenant_abc","data":{"course_id":"course_778","title":"Data Literacy 101","version":"1.0","published_by":"user_55"}}
Fan-out only to active subscriptions that include `course.published`. Delivery target must return 2xx within 10 seconds; otherwise retry schedule starts. Duplicate deliveries are possible across retries, so consumers must use `event_id` or `X-LMS-Delivery-Id` for idempotency. Signature verification is mandatory before processing payload data.

enrollment.completed
{"event_id":"evt_90002","event_type":"enrollment.completed","occurred_at":"2026-01-22T15:05:11Z","tenant_id":"tenant_abc","data":{"enrollment_id":"enr_4421","user_id":"user_99","course_id":"course_778","completion_score":92}}
Delivered at-least-once to matching subscriptions. Retries stop early on first 2xx response. After max retries, endpoint is marked `degraded`; alert emitted to tenant admins. Security checks: verify HMAC signature, enforce TLS 1.2+, optionally validate source IP allowlist, and reject replayed `X-LMS-Delivery-Id` values seen within 24 hours.

assessment.graded
{"event_id":"evt_90003","event_type":"assessment.graded","occurred_at":"2026-01-22T16:40:44Z","tenant_id":"tenant_abc","data":{"assessment_id":"asm_883","submission_id":"subm_1201","user_id":"user_99","score":88,"passed":true}}
Delivered only to subscriptions explicitly opted into `assessment.graded` (fine-grained event subscription). Retries follow exponential backoff and are paused during endpoint circuit-breaker windows after repeated 5xx responses. Resume attempts after health-check success. Receiver must verify signature against raw body and compare timestamp tolerance to prevent tampering/replay.

subscription.deleted
{"subscription_id":"sub_12345","tenant_id":"tenant_abc","status":"deleted","deleted_at":"2026-01-24T09:00:00Z"}
Best-effort notification sent once before deactivation; if delivery fails, one retry after 5 minutes. No further business events are delivered after deletion effective time. Signed like all webhook events; client should verify signature and remove local endpoint bindings.
