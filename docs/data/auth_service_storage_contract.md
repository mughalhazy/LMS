# Auth Service Storage Contract

## Ownership

`auth_service` exclusively owns auth persistence objects and does not write to `user_service`, `rbac_service`, or `tenant_service` databases.

## Tables

### `auth_sessions`
- `session_id` (pk)
- `tenant_id` (not null)
- `user_id` (not null)
- `state` (`active|revoked|expired`)
- `auth_method`
- `assurance_level`
- `issued_at`
- `expires_at`
- `last_seen_at`
- `revoked_at`
- `revoked_reason`

### `auth_refresh_tokens`
- `token_id` (pk)
- `tenant_id`
- `user_id`
- `session_id` (fk -> auth_sessions)
- `parent_token_id` (nullable)
- `replaced_by_token_id` (nullable)
- `token_fingerprint` (unique)
- `hashed_secret`
- `issued_at`
- `expires_at`
- `used_at`
- `revoked_at`

### `auth_password_reset_challenges`
- `challenge_id` (pk)
- `tenant_id`
- `user_id`
- `challenge_hash`
- `delivery_channel`
- `requested_at`
- `expires_at`
- `consumed_at`
- `attempt_count`
- `max_attempts`

### `auth_audit_log`
- `event_id` (pk)
- `tenant_id`
- `event_type`
- `severity`
- `actor_user_id`
- `subject_user_id`
- `session_id`
- `result`
- `reason_code`
- `correlation_id`
- `trace_id`
- `metadata` (jsonb)
- `occurred_at`

### `auth_outbox_events`
- `outbox_id` (pk)
- `event_id` (unique)
- `event_type`
- `tenant_id`
- `payload` (jsonb)
- `published_at` (nullable)
- `attempts`

## Data access constraints

- Every repository method requires `tenant_id` argument.
- All selects and updates include tenant predicate.
- No cross-tenant bulk operations without explicit partition key.
