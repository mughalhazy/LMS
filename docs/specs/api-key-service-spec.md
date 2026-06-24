# API Key Service — Spec

**Service:** `api-key-service` | **Gateway:** `/api/v1/api-key` | **Port:** 8086

## Purpose

Manages integration API keys for tenant-scoped external callers. Provides key creation, rotation, revocation, scope-based authorization, and usage reporting.

## Responsibilities

- API key lifecycle: create, rotate, revoke
- Scope-based authorization check (validate key + required scope)
- Per-key usage counters by scope
- Hashed secret storage — plaintext returned once on creation only

## Out of scope

- OAuth2 / JWT token management (owned by `auth-service`)
- User session management (owned by `session-service`)

## Data model

| Entity | Fields |
|---|---|
| `ApiKeyRecord` | key_id, tenant_id, name, hashed_secret, key_prefix, scopes[], created_by, created_at, rotated_from_key_id, revoked, revoked_at |
| `UsageCounter` | key_id, tenant_id, total_requests, per_scope{}, last_used_at |

## Allowed scopes

```
integrations:hris.sync
integrations:crm.upsert
integrations:lti.launch
integrations:webhooks.publish
integrations:*
```

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/integrations/api-keys` | Create API key — returns plaintext secret once |
| POST | `/api/v1/integrations/api-keys/rotate` | Rotate key — creates new key, revokes old |
| POST | `/api/v1/integrations/api-keys/authorize` | Validate key + scope — used by gateway/services |
| POST | `/api/v1/integrations/api-keys/usage` | Per-key usage report |

## Behavioral rules

- Plaintext secret is never stored — only SHA-256 hash is persisted
- Rotation atomically creates new key and revokes old key in same operation
- Authorization increments per-scope usage counter on success
- Revoked keys are rejected at authorization time
- Scopes must be from the allowed set; unknown scopes rejected at creation

## Integration

- Consumed by: API gateway (authorization middleware), integration services
- Emits: no events
