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

## Status

Service exists on disk with full implementation. Not yet registered in the API gateway (pending).
