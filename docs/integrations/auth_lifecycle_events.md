# Auth Lifecycle Event Definitions

## Event envelope (common)

```json
{
  "event_id": "evt_01J9...",
  "event_type": "auth.login.succeeded",
  "occurred_at": "2026-01-15T10:00:00Z",
  "tenant_id": "tenant-acme",
  "subject_user_id": "usr_321",
  "actor_user_id": "usr_321",
  "correlation_id": "corr-123",
  "trace_id": "trace-789",
  "schema_version": "1.0",
  "payload": {}
}
```

## Published events

### `auth.login.succeeded`
Payload:
- `session_id`
- `auth_method`
- `assurance_level`
- `client_id`

### `auth.login.failed`
Payload:
- `identifier_hash`
- `failure_reason`
- `attempt_count`

### `auth.token.refreshed`
Payload:
- `session_id`
- `new_token_id`
- `previous_token_id`

### `auth.session.revoked`
Payload:
- `session_id`
- `revocation_reason`
- `revoked_by`

### `auth.password.reset.requested`
Payload:
- `challenge_id`
- `delivery_channel`

### `auth.password.reset.completed`
Payload:
- `reset_method`
- `sessions_revoked_count`

### `auth.risk.detected`
Payload:
- `risk_signal`
- `risk_score`
- `mitigation_action`

## Consumed events

- `tenant.status.changed` (disable login/token issue for suspended tenants).
- `user.lifecycle.changed` (disable login for non-active users).

## Delivery guarantees

- At-least-once publish semantics.
- Consumer idempotency keyed by `event_id`.
- Partition strategy by `tenant_id`.
