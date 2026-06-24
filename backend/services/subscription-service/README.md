# Subscription Service

Subscription lifecycle state machine — manages recurring access products from trial to expiry.

## Design reference

`Repo/docs/designs/subscription-service-design.md` | CGAP-080

## Lifecycle states

```
TRIAL → ACTIVE → GRACE → SUSPENDED → EXPIRED
                        ↘ CANCELLED
```

## Transitions

| Event | From | To |
|---|---|---|
| ACTIVATION | TRIAL | ACTIVE |
| RENEWAL | ACTIVE | ACTIVE |
| GRACE_ENTRY | ACTIVE | GRACE |
| SUSPENSION | GRACE | SUSPENDED |
| EXPIRATION | SUSPENDED | EXPIRED |
| CANCELLATION | any | CANCELLED |

Transitions are defined in `EVENT_TRANSITIONS` in `app/service.py`.

## API routes (port 8098)

Authentication: JWT required (`Authorization: Bearer <token>`). All routes enforce `JWT_SHARED_SECRET`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/subscriptions` | Create subscription (starts in TRIAL state) |
| GET | `/api/v1/subscriptions` | List subscriptions for tenant (`X-Tenant-Id`) |
| GET | `/api/v1/subscriptions/{subscription_id}` | Get subscription by ID |
| POST | `/api/v1/subscriptions/{subscription_id}/activate` | TRIAL → ACTIVE |
| POST | `/api/v1/subscriptions/{subscription_id}/renew` | Renew (extends ACTIVE) |
| POST | `/api/v1/subscriptions/{subscription_id}/expire` | ACTIVE → EXPIRED |
| POST | `/api/v1/subscriptions/{subscription_id}/cancel` | Any → CANCELLED |
| POST | `/api/v1/subscriptions/{subscription_id}/enter-grace` | ACTIVE → GRACE |
| POST | `/api/v1/subscriptions/{subscription_id}/suspend` | GRACE → SUSPENDED |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

Tenant context via `X-Tenant-Id` header or `tenant_id` in request body.

## Status

HTTP entrypoint added 2026-06-01 (B10-006). Not yet registered in the API gateway (pending).
